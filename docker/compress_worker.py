#!/usr/bin/env python3
"""
ytz HEVC night-time compression worker.

Two kinds of work, NEW FIRST then the old backlog as fill-in:

  PLAN A (priority) -- new recordings still in Zoom with no Drive copy yet:
      re-fetch the raw MP4 from ZOOM -> HEVC-encode -> upload ONLY the compressed file to Drive
      -> set recordings.drive_url + compressed=1. (No raw-to-Drive double upload. drive_url is what
      lets the main pipeline's Zoom-deletion gate later trash the recording from Zoom.)

  BACKLOG (only when no Plan A work is left) -- old recordings that already have a big RAW Drive copy
  (from the old flow; their Zoom copy is usually gone):
      download that raw FROM DRIVE -> HEVC-encode -> upload the compressed file to the SAME folder
      -> verify -> delete the old raw Drive file -> repoint drive_url + compressed=1. (In-place shrink.)

The worker always clears NEW recordings first; it only touches the backlog when nothing new is pending,
so recent videos are never delayed behind the archive.

HIBERNATING: a systemd timer starts the container at night; the worker drains the queue + retries,
then EXITS when nothing eligible is left or the window closes. restart:"no" keeps it stopped (0 RAM)
until the next night. HEVC_IGNORE_WINDOW=1 runs once on demand (testing).

RETRY: persistent compress_attempts; round-robin (fewest first), >= HEVC_COOLDOWN_MIN apart, up to
HEVC_MAX_ATTEMPTS lifetime. A failure never deletes anything (Plan A leaves drive_url empty; backlog
deletes the old raw ONLY after the compressed copy is verified) and is logged to the recording's row
(compress_error) AND the app's system_logs (dashboard "System Logs" tab). Reset a parked video:
    UPDATE recordings SET compress_attempts=0, compress_error=NULL WHERE zoom_id='...';

Reuses the live pipeline's machinery (BackgroundService._init_clients + its zoom_clients,
_encode_uuid_for_zoom, _get_drive_folders, drive) so Zoom/Drive logic is never duplicated.
"""
import os, re, time, subprocess, datetime, sqlite3, sys
sys.path.insert(0, ".")
from src import config
from src.utils import generate_names
from src.main import BackgroundService
from googleapiclient.http import MediaIoBaseDownload

DB      = str(config.DATA_DIR / "vong_v2.db")
CRF     = os.getenv("HEVC_CRF", "28")
WINDOW  = os.getenv("HEVC_WINDOW_UTC", "16:30-01:30")        # start-end, UTC (22:00-07:00 IST)
SCRATCH = os.getenv("HEVC_SCRATCH", "/app/downloads")
MAX_ATTEMPTS = int(os.getenv("HEVC_MAX_ATTEMPTS", "3"))
COOLDOWN_MIN = int(os.getenv("HEVC_COOLDOWN_MIN", "15"))
IGNORE_WINDOW = os.getenv("HEVC_IGNORE_WINDOW", "0") == "1"


def in_window():
    if IGNORE_WINDOW:
        return True
    s, e = WINDOW.split("-")
    t = lambda x: datetime.time(int(x[:2]), int(x[3:5]))
    now, a, b = datetime.datetime.utcnow().time(), t(s), t(e)
    return (a <= now or now <= b) if a > b else (a <= now <= b)   # midnight wrap


def db():
    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=60000")
    return c


def add_log(c, level, message):
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


# columns every job needs (superset for both kinds)
_COLS = ("zoom_id, meeting_id, topic, start_time, playlist, account_name, drive_url, "
         "COALESCE(compress_attempts,0)")


# "new" = on YouTube, no Drive copy yet (Plan A, from Zoom).  "backlog" = already has a raw Drive copy.
_WHERE_NEW     = ("AND youtube_url IS NOT NULL AND youtube_url!='' "
                  "AND (drive_url IS NULL OR drive_url='')")
_WHERE_BACKLOG = "AND drive_url IS NOT NULL AND drive_url!=''"


def _count(c, where):
    """How many of this kind still need compressing (ignores cooldown)."""
    return c.execute(
        "SELECT COUNT(*) FROM recordings WHERE status='COMPLETED' AND COALESCE(compressed,0)=0 "
        "AND COALESCE(compress_attempts,0) < ? " + where, (MAX_ATTEMPTS,)).fetchone()[0]


def _next(c, where):
    """Next job of this kind whose cooldown has elapsed; fewest attempts, then oldest. None if all cooling."""
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(minutes=COOLDOWN_MIN)).isoformat()
    return c.execute(
        f"SELECT {_COLS} FROM recordings WHERE status='COMPLETED' AND COALESCE(compressed,0)=0 "
        "AND COALESCE(compress_attempts,0) < ? "
        "AND (compress_last_attempt IS NULL OR compress_last_attempt < ?) " + where +
        " ORDER BY COALESCE(compress_attempts,0) ASC, date_str ASC LIMIT 1",
        (MAX_ATTEMPTS, cutoff)).fetchone()


def _encode(out, raw):
    subprocess.run(
        ["nice", "-n", "19", "ionice", "-c3",
         "ffmpeg", "-y", "-i", raw,
         "-c:v", "libx265", "-preset", "medium", "-crf", str(CRF),
         "-x265-params", "pools=1:frame-threads=1",
         "-tag:v", "hvc1", "-c:a", "copy", "-movflags", "+faststart", out],
        check=True)


def fetch_zoom_mp4(svc, account_name, zoom_id, meeting_id, start_time):
    zc = svc.zoom_clients.get(account_name)
    if zc is None and svc.zoom_clients:
        zc = next(iter(svc.zoom_clients.values()))
    if zc is None:
        raise RuntimeError(f"no Zoom client available (account={account_name!r})")
    data = zc.get_recording_details(svc._encode_uuid_for_zoom(zoom_id))
    if not data and str(zoom_id) == str(meeting_id):
        data = zc.get_recording_details(meeting_id)
    if not data:
        raise RuntimeError(f"recording not found on Zoom (uuid={zoom_id}, mtg={meeting_id}) "
                           f"- it may have aged out of Zoom cloud")
    expected = start_time[:10] if start_time else None
    url = None
    for f in data.get("recording_files", []):
        fd = (f.get("recording_start") or "")[:10] or None
        if expected and fd and fd != expected:
            continue
        if f.get("file_type") == "MP4" and not url:
            url = f.get("download_url")
    if not url:
        for f in data.get("recording_files", []):
            if f.get("file_type") == "MP4":
                url = f.get("download_url"); break
    if not url:
        raise RuntimeError("no MP4 file on the Zoom recording")
    return zc, url


def drive_download(svc, fid, path):
    req = svc.drive.service.files().get_media(fileId=fid, supportsAllDrives=True)
    with open(path, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=32 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk()


def process(svc, kind, job):
    (zid, meeting_id, topic, start_time, playlist, account_name, drive_url, attempts) = job
    attempt_no = attempts + 1
    now = datetime.datetime.utcnow().isoformat()
    c = db()
    c.execute("UPDATE recordings SET compress_attempts=COALESCE(compress_attempts,0)+1, "
              "compress_last_attempt=? WHERE zoom_id=?", (now, zid)); c.commit(); c.close()

    tag = abs(hash(zid)) % 10**8
    raw = os.path.join(SCRATCH, f"raw_{tag}.mp4")
    out = os.path.join(SCRATCH, f"hevc_{tag}.mp4")
    try:
        if kind == "zoom":
            # PLAN A: pull raw from Zoom, compress, upload compressed to the playlist's Drive folder
            zc, url = fetch_zoom_mp4(svc, account_name, zid, meeting_id, start_time)
            zc.download_file(url, raw)
            rawsize = os.path.getsize(raw)
            _encode(out, raw)
            newsize = os.path.getsize(out)
            if newsize < 1_000_000 or newsize >= rawsize:
                raise RuntimeError(f"bad output size {newsize} vs raw {rawsize}")
            drive_folder_id, _ = svc._get_drive_folders(playlist)
            if not svc.drive or not drive_folder_id:
                raise RuntimeError(f"no Drive client/folder for playlist {playlist!r}")
            name = generate_names(topic, start_time)["video_filename"]
            new_id = svc.drive.upload_file(out, name, drive_folder_id)
            if not svc.drive.check_file_integrity(new_id, out):
                raise RuntimeError("drive upload size mismatch")
            c = db()
            c.execute("UPDATE recordings SET drive_url=?, compressed=1, compressed_at=?, "
                      "drive_uploaded_at=?, compress_error=NULL WHERE zoom_id=?",
                      (f"https://drive.google.com/file/d/{new_id}/view", now, now, zid))
            add_log(c, "INFO", f"[hevc] OK (new) {topic}: {rawsize//1048576}->{newsize//1048576} MiB -> Drive")
            c.commit(); c.close()
        else:
            # BACKLOG: shrink the existing raw Drive copy in place
            fid = drive_id(drive_url)
            if not fid:
                raise RuntimeError(f"cannot parse Drive id from {drive_url!r}")
            meta = svc.drive.service.files().get(fileId=fid, fields="name,parents,size",
                                                 supportsAllDrives=True).execute()
            name, parent, rawsize = meta["name"], meta["parents"][0], int(meta.get("size", 0))
            drive_download(svc, fid, raw)
            _encode(out, raw)
            newsize = os.path.getsize(out)
            if newsize < 1_000_000 or newsize >= rawsize:
                raise RuntimeError(f"bad output size {newsize} vs raw {rawsize}")
            new_id = svc.drive.upload_file(out, name, parent)
            if not svc.drive.check_file_integrity(new_id, out):
                raise RuntimeError("drive upload size mismatch")
            svc.drive.service.files().delete(fileId=fid, supportsAllDrives=True).execute()   # raw removed ONLY now
            c = db()
            c.execute("UPDATE recordings SET drive_url=?, compressed=1, compressed_at=?, "
                      "compress_error=NULL WHERE zoom_id=?",
                      (f"https://drive.google.com/file/d/{new_id}/view", now, zid))
            add_log(c, "INFO", f"[hevc] OK (backlog) {topic}: {rawsize//1048576}->{newsize//1048576} MiB")
            c.commit(); c.close()
        return True
    except Exception as e:
        err = str(e)[:500]
        # Zoom 404 = the source recording has aged out of the Zoom cloud: PERMANENT, never
        # recoverable by retrying. Mirror src/main.py's original handling ("Zoom recording not
        # found (expired?) - marking COMPLETED without Drive"): give up at once instead of burning
        # MAX_ATTEMPTS. Parking it (compress_attempts := MAX_ATTEMPTS) stops it from being picked
        # as a "new" job, so it no longer blocks the new-videos-first queue or the backlog.
        permanent = ("recording not found on Zoom" in err) or ("aged out of Zoom" in err)
        c = db()
        if permanent:
            c.execute("UPDATE recordings SET compress_error=?, compress_attempts=? WHERE zoom_id=?",
                      (err, MAX_ATTEMPTS, zid))
            add_log(c, "WARNING", f"[hevc] SKIP (Zoom source gone, not retrying) {topic}: {err}")
        else:
            c.execute("UPDATE recordings SET compress_error=? WHERE zoom_id=?", (err, zid))
            if attempt_no >= MAX_ATTEMPTS:
                add_log(c, "ERROR", f"[hevc] GIVING UP on {topic} after {attempt_no}/{MAX_ATTEMPTS} "
                                    f"(reset compress_attempts to retry): {err}")
            else:
                add_log(c, "ERROR", f"[hevc] FAILED {topic} (attempt {attempt_no}/{MAX_ATTEMPTS}): {err}")
        c.commit(); c.close()
        return False
    finally:
        for f in (raw, out):
            try: os.remove(f)
            except OSError: pass


def main():
    c0 = db(); ensure_schema(c0)
    add_log(c0, "INFO", "HEVC worker started (new-from-Zoom first, then backlog)"); c0.close()
    svc = BackgroundService()
    svc._init_clients()            # builds svc.zoom_clients, svc.drive (+ youtube/sheets); no thread
    os.makedirs(SCRATCH, exist_ok=True)
    ok = fail = 0

    while in_window():
        c = db()
        if _count(c, _WHERE_NEW) > 0:
            # NEW videos (including ones waiting out a retry cooldown) take ABSOLUTE priority.
            # If they're all cooling down, WAIT for them -- never start a long backlog encode ahead
            # of a pending new-video retry.
            job = _next(c, _WHERE_NEW); c.close()
            if job:
                if process(svc, "zoom", job): ok += 1
                else: fail += 1
                time.sleep(5)
            else:
                time.sleep(90)     # new videos pending but cooling -> wait, recheck
            continue
        # No new videos left anywhere -> fill spare time with the backlog
        back_total = _count(c, _WHERE_BACKLOG)
        job = _next(c, _WHERE_BACKLOG) if back_total else None
        c.close()
        if back_total == 0:
            break                  # nothing left anywhere -> exit (frees RAM)
        if job:
            if process(svc, "drive", job): ok += 1
            else: fail += 1
            time.sleep(5)
        else:
            time.sleep(90)         # backlog pending but cooling -> wait, recheck

    c = db(); add_log(c, "INFO", f"HEVC worker exiting (ok={ok}, failed={fail})"); c.close()


if __name__ == "__main__":
    main()
