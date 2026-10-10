#!/usr/bin/env python3
"""
ytz HEVC night-time compression worker  (runs in its own resource-capped container).

BASELINE = in-place shrink of the Drive copy ("Plan C"): ZERO changes to the live pipeline,
never touches Zoom or YouTube. The live pipeline keeps doing Zoom -> YouTube + Drive(raw) -> trash
exactly as today; this worker only shrinks the Drive copy that already exists. The END STATE is
identical to "Plan A" (Drive ends up holding only the compressed file) — the raw just lives on
Drive for a few hours until the night window instead of never.

Each night-window pass picks ONE COMPLETED recording whose Drive copy is still raw (compressed=0):
   1. download the raw MP4 from DRIVE            -> /app/downloads
   2. HEVC-encode with libx265 (nice'd, 1 core; the container also caps CPU/RAM)
   3. upload the compressed MP4 to the SAME Drive folder (same filename)
   4. verify the upload (size matches local, and < raw)  -- only then:
   5. delete the OLD raw Drive file, repoint recordings.drive_url, set compressed=1
   6. clean scratch; repeat until the window closes or the queue is empty.

SAFETY: the raw Drive file is deleted ONLY after the compressed copy is verified uploaded, so there
is never a moment with zero Drive backup, and YouTube stays as the second backup throughout.

Verified against the live code (2026-10):
  - DB: SQLite at config.DATA_DIR/"vong_v2.db", table `recordings`, done status = 'COMPLETED',
    key col `zoom_id`, Drive link in `drive_url` (https://drive.google.com/file/d/<id>/view).
  - DriveClient has NO download/delete methods -> we use its raw googleapiclient `.service`.
  - The `compressed` / `compressed_at` columns don't exist yet -> this worker adds them (idempotent).
"""
import os, re, time, subprocess, datetime, sqlite3, sys
sys.path.insert(0, ".")                       # cwd = /app, so `from src import ...` resolves
from src import config
from src.drive_client import DriveClient
from googleapiclient.http import MediaIoBaseDownload

DB      = str(config.DATA_DIR / "vong_v2.db")
CRF     = os.getenv("HEVC_CRF", "28")
WINDOW  = os.getenv("HEVC_WINDOW_UTC", "18:00-00:30")      # start-end, UTC (23:30-06:00 IST)
SCRATCH = os.getenv("HEVC_SCRATCH", "/app/downloads")


def in_window():
    s, e = WINDOW.split("-")
    t = lambda x: datetime.time(int(x[:2]), int(x[3:5]))
    now, a, b = datetime.datetime.utcnow().time(), t(s), t(e)
    return (a <= now or now <= b) if a > b else (a <= now <= b)   # handles midnight wrap


def db():
    c = sqlite3.connect(DB, timeout=60)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=60000")
    return c


def ensure_schema():
    c = db()
    cols = {r[1] for r in c.execute("PRAGMA table_info(recordings)")}
    if "compressed" not in cols:
        c.execute("ALTER TABLE recordings ADD COLUMN compressed INTEGER NOT NULL DEFAULT 0")
    if "compressed_at" not in cols:
        c.execute("ALTER TABLE recordings ADD COLUMN compressed_at TEXT")
    c.commit(); c.close()


def drive_id(url):
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def next_job(c, skip):
    rows = c.execute(
        "SELECT zoom_id, topic, drive_url FROM recordings "
        "WHERE status='COMPLETED' AND COALESCE(compressed,0)=0 "
        "AND drive_url IS NOT NULL AND drive_url!='' "
        "ORDER BY date_str").fetchall()
    for r in rows:
        if r[0] not in skip:
            return r
    return None


def download(svc, fid, path):
    req = svc.files().get_media(fileId=fid, supportsAllDrives=True)
    with open(path, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=32 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk()


def main():
    ensure_schema()
    dr = DriveClient(auth_mode=config.DRIVE_AUTH_MODE,
                     token_path=config.DRIVE_TOKEN_PATH,
                     client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
                     service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE)
    svc = dr.service
    os.makedirs(SCRATCH, exist_ok=True)
    skip = set()                              # zoom_ids that failed this run -> don't hot-loop on them
    print(f"[hevc] worker up. DB={DB} CRF={CRF} window(UTC)={WINDOW}", flush=True)

    while True:
        if not in_window():
            time.sleep(300); continue
        c = db(); job = next_job(c, skip); c.close()
        if not job:
            time.sleep(600); continue         # nothing left (or all skipped) — recheck later
        zid, topic, durl = job
        fid = drive_id(durl)
        if not fid:
            print(f"[hevc] SKIP {topic}: cannot parse Drive id from {durl!r}", flush=True)
            skip.add(zid); continue
        raw = os.path.join(SCRATCH, f"raw_{fid}.mp4")
        out = os.path.join(SCRATCH, f"hevc_{fid}.mp4")
        try:
            meta = svc.files().get(fileId=fid, fields="name,parents,size",
                                   supportsAllDrives=True).execute()
            name    = meta["name"]
            parent  = meta["parents"][0]
            rawsize = int(meta.get("size", 0))

            download(svc, fid, raw)

            # 1 core, nice'd + ionice'd; hvc1 tag + faststart so the Drive preview plays the HEVC file.
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

            new_id = dr.upload_file(out, name, parent)            # upload compressed to same folder
            if not dr.check_file_integrity(new_id, out):          # verify remote size == local
                raise RuntimeError("drive upload size mismatch")

            svc.files().delete(fileId=fid, supportsAllDrives=True).execute()   # remove raw ONLY now
            c = db()
            c.execute("UPDATE recordings SET drive_url=?, compressed=1, compressed_at=? WHERE zoom_id=?",
                      (f"https://drive.google.com/file/d/{new_id}/view",
                       datetime.datetime.utcnow().isoformat(), zid))
            c.commit(); c.close()
            print(f"[hevc] OK {topic}: {rawsize // 1048576} -> {newsize // 1048576} MiB", flush=True)
        except Exception as e:
            print(f"[hevc] SKIP {topic}: {e}", flush=True)
            skip.add(zid)                      # retry on next container restart, not in a tight loop
        finally:
            for f in (raw, out):
                try: os.remove(f)
                except OSError: pass
        time.sleep(10)


if __name__ == "__main__":
    main()
