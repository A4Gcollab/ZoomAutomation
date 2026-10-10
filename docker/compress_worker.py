#!/usr/bin/env python3
"""
ytz HEVC night-time compression worker.

HIBERNATING: not an always-on process. A systemd timer on the host starts the container at night
(see docker/systemd/); the worker drains the queue, retries failures, then EXITS once there is
nothing eligible left or the window closes. With `restart: "no"` the container then stays stopped
all day -> 0 RAM until the next night. (HEVC_IGNORE_WINDOW=1 runs once on demand, e.g. to test.)

Per video (one at a time): download the raw mp4 from DRIVE -> HEVC-encode (libx265, 1 nice'd core,
container-capped) -> upload the compressed mp4 to the SAME Drive folder -> verify (size matches,
and smaller) -> ONLY THEN delete the old raw Drive file, repoint recordings.drive_url, compressed=1.
Zoom and YouTube are never touched; the live pipeline is unchanged. End state = Drive holds only the
compressed file; the raw just lived there until night.

RETRY (round-robin, same night): always take the eligible video (compressed=0, attempts<MAX) with
the FEWEST attempts that is not within its cooldown. So it tries A; if A fails it moves to B, C...
and comes back to A later. A failure bumps compress_attempts and leaves the video eligible until it
hits HEVC_MAX_ATTEMPTS (default 3) lifetime attempts, each at least HEVC_COOLDOWN_MIN (default 15)
minutes apart -- so a transient blip gets a real retry, a sole failing video is not hammered, and
unfinished retries spill to the next night if the window closes. After MAX attempts it is parked
(reset with: UPDATE recordings SET compress_attempts=0, compress_error=NULL WHERE zoom_id='...').

A failure NEVER touches Zoom (the Zoom-deletion gate is independent). Errors are logged to the
recording's row (compress_error) AND to the app's `system_logs` table, so they appear in the
dashboard's "System Logs" tab, e.g. "[hevc] FAILED <topic> (attempt 2/3): <error>".

Verified against live code (2026-10): SQLite config.DATA_DIR/"vong_v2.db", table `recordings`, done
status 'COMPLETED', key `zoom_id`, Drive link in `drive_url`; DriveClient has no download/delete ->
use its raw googleapiclient `.service`; app logs via INSERT INTO system_logs(level, message).
"""
import os, re, time, subprocess, datetime, sqlite3, sys
sys.path.insert(0, ".")                       # cwd = /app, so `from src import ...` resolves
from src import config
from src.drive_client import DriveClient
from googleapiclient.http import MediaIoBaseDownload

DB      = str(config.DATA_DIR / "vong_v2.db")
CRF     = os.getenv("HEVC_CRF", "28")
WINDOW  = os.getenv("HEVC_WINDOW_UTC", "16:30-01:30")        # start-end, UTC (22:00-07:00 IST)
SCRATCH = os.getenv("HEVC_SCRATCH", "/app/downloads")
MAX_ATTEMPTS = int(os.getenv("HEVC_MAX_ATTEMPTS", "3"))
COOLDOWN_MIN = int(os.getenv("HEVC_COOLDOWN_MIN", "15"))
IGNORE_WINDOW = os.getenv("HEVC_IGNORE_WINDOW", "0") == "1"  # run once regardless of time (testing)


def in_window():
    if IGNORE_WINDOW:
        return True
    s, e = WINDOW.split("-")
    t = lambda x: datetime.time(int(x[:2]), int(x[3:5]))
    now, a, b = datetime.datetime.utcnow().time(), t(s), t(e)
    return (a <= now or now <= b) if a > b else (a <= now <= b)   # handles midnight wrap


def db():
    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=60000")
    return c


def add_log(c, level, message):
    # same table/shape the app's db.add_log() uses -> shows in the dashboard "System Logs" tab
    try:
        c.execute("INSERT INTO system_logs (level, message) VALUES (?, ?)", (level, message))
        c.commit()
    except Exception:
        pass
    print(f"[hevc] {level}: {message}", flush=True)


def ensure_schema(c):
    cols = {r[1] for r in c.execute("PRAGMA table_info(recordings)")}
    adds = {
        "compressed":            "INTEGER NOT NULL DEFAULT 0",
        "compressed_at":         "TEXT",
        "compress_attempts":     "INTEGER NOT NULL DEFAULT 0",
        "compress_error":        "TEXT",
        "compress_last_attempt": "TEXT",
    }
    for col, decl in adds.items():
        if col not in cols:
            c.execute(f"ALTER TABLE recordings ADD COLUMN {col} {decl}")
    c.commit()


def drive_id(url):
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def candidate_count(c):
    """Videos still needing compression and not yet out of attempts (ignores cooldown)."""
    return c.execute(
        "SELECT COUNT(*) FROM recordings WHERE status='COMPLETED' AND COALESCE(compressed,0)=0 "
        "AND COALESCE(compress_attempts,0) < ? AND drive_url IS NOT NULL AND drive_url!=''",
        (MAX_ATTEMPTS,)).fetchone()[0]


def next_ready(c):
    """Eligible video with fewest attempts whose cooldown has elapsed; None if all are cooling down."""
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(minutes=COOLDOWN_MIN)).isoformat()
    return c.execute(
        "SELECT zoom_id, topic, drive_url, COALESCE(compress_attempts,0) FROM recordings "
        "WHERE status='COMPLETED' AND COALESCE(compressed,0)=0 "
        "AND COALESCE(compress_attempts,0) < ? "
        "AND drive_url IS NOT NULL AND drive_url!='' "
        "AND (compress_last_attempt IS NULL OR compress_last_attempt < ?) "
        "ORDER BY COALESCE(compress_attempts,0) ASC, date_str ASC LIMIT 1",
        (MAX_ATTEMPTS, cutoff)).fetchone()


def download(svc, fid, path):
    req = svc.files().get_media(fileId=fid, supportsAllDrives=True)
    with open(path, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=32 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk()


def process(dr, svc, zid, topic, durl, attempts):
    attempt_no = attempts + 1
    now = datetime.datetime.utcnow().isoformat()
    c = db()
    c.execute("UPDATE recordings SET compress_attempts=COALESCE(compress_attempts,0)+1, "
              "compress_last_attempt=? WHERE zoom_id=?", (now, zid))
    c.commit(); c.close()

    fid = drive_id(durl)
    raw = os.path.join(SCRATCH, f"raw_{fid or zid}.mp4")
    out = os.path.join(SCRATCH, f"hevc_{fid or zid}.mp4")
    try:
        if not fid:
            raise RuntimeError(f"cannot parse Drive id from {durl!r}")
        meta = svc.files().get(fileId=fid, fields="name,parents,size",
                               supportsAllDrives=True).execute()
        name, parent, rawsize = meta["name"], meta["parents"][0], int(meta.get("size", 0))

        download(svc, fid, raw)
        subprocess.run(
            ["nice", "-n", "19", "ionice", "-c3",
             "ffmpeg", "-y", "-i", raw,
             "-c:v", "libx265", "-preset", "medium", "-crf", str(CRF),
             "-x265-params", "pools=1:frame-threads=1",
             "-tag:v", "hvc1", "-c:a", "copy", "-movflags", "+faststart", out],
            check=True)

        newsize = os.path.getsize(out)
        if newsize < 1_000_000 or newsize >= rawsize:
            raise RuntimeError(f"bad output size {newsize} vs raw {rawsize}")

        new_id = dr.upload_file(out, name, parent)
        if not dr.check_file_integrity(new_id, out):
            raise RuntimeError("drive upload size mismatch")

        svc.files().delete(fileId=fid, supportsAllDrives=True).execute()   # raw removed ONLY now
        c = db()
        c.execute("UPDATE recordings SET drive_url=?, compressed=1, compressed_at=?, "
                  "compress_error=NULL WHERE zoom_id=?",
                  (f"https://drive.google.com/file/d/{new_id}/view", now, zid))
        add_log(c, "INFO", f"[hevc] OK {topic}: {rawsize//1048576}->{newsize//1048576} MiB")
        c.commit(); c.close()
        return True
    except Exception as e:
        err = str(e)[:500]
        c = db()
        c.execute("UPDATE recordings SET compress_error=? WHERE zoom_id=?", (err, zid))
        if attempt_no >= MAX_ATTEMPTS:
            add_log(c, "ERROR", f"[hevc] GIVING UP on {topic} after {attempt_no}/{MAX_ATTEMPTS} "
                                f"(manual reset needed): {err}")
        else:
            add_log(c, "ERROR", f"[hevc] FAILED {topic} (attempt {attempt_no}/{MAX_ATTEMPTS}): {err}")
        c.commit(); c.close()
        return False
    finally:
        for f in (raw, out):
            try: os.remove(f)
            except OSError: pass


def main():
    c0 = db(); ensure_schema(c0); add_log(c0, "INFO", "HEVC worker started"); c0.close()
    dr = DriveClient(auth_mode=config.DRIVE_AUTH_MODE,
                     token_path=config.DRIVE_TOKEN_PATH,
                     client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
                     service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE)
    svc = dr.service
    os.makedirs(SCRATCH, exist_ok=True)
    ok = fail = 0

    while in_window():
        c = db(); n = candidate_count(c); job = next_ready(c) if n else None; c.close()
        if n == 0:
            break                             # nothing left to compress -> exit (frees RAM)
        if job is None:
            time.sleep(90); continue          # all remaining are within cooldown -> wait, then recheck
        zid, topic, durl, attempts = job
        if process(dr, svc, zid, topic, durl, attempts):
            ok += 1
        else:
            fail += 1
        time.sleep(5)

    c = db(); add_log(c, "INFO", f"HEVC worker exiting (ok={ok}, failed={fail})"); c.close()


if __name__ == "__main__":
    main()
