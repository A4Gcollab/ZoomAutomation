"""
Upload to Drive for VERIFICATION_FAILED recordings where YouTube is verified (YT:True)
but Drive is missing. After upload, reset them to PENDING for deletion.
"""
import sys, os, urllib.parse, datetime, json, traceback
sys.path.insert(0, ".")

from src.db_sql import db
from src.config import (ZOOM_ACCOUNTS, DOWNLOAD_DIR, PLAYLIST_CONFIG_PATH)
from src.drive_client import DriveClient
from src.zoom_client import ZoomClient
from src.utils import generate_names
from src import config

drive = DriveClient(
    auth_mode=config.DRIVE_AUTH_MODE,
    token_path=config.DRIVE_TOKEN_PATH,
    client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
    service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE
)

zoom_clients = {}
for i, creds in enumerate(ZOOM_ACCOUNTS, 1):
    zoom_clients["Zoom Account " + str(i)] = ZoomClient(creds)

with open(PLAYLIST_CONFIG_PATH) as f:
    playlist_cfg = json.load(f)

def get_drive_folders(playlist_name):
    for pl in playlist_cfg.get("playlists", []):
        if pl.get("playlist_name") == playlist_name:
            return pl.get("drive_folder_id"), pl.get("transcript_folder_id")
    return playlist_cfg.get("drive_folder_id"), playlist_cfg.get("transcript_folder_id")

# VERIFICATION_FAILED where YouTube is verified (YT:True in error) but no drive_url
cur = db._get_cursor()
cur.execute("""
    SELECT zoom_id, meeting_id, topic, youtube_url, account_name, start_time, playlist
    FROM recordings
    WHERE zoom_deletion_status='VERIFICATION_FAILED'
      AND youtube_url IS NOT NULL AND youtube_url != ''
      AND (drive_url IS NULL OR drive_url = '')
      AND zoom_deletion_error LIKE '%YT:True%'
""")
rows = [dict(r) for r in cur.fetchall()]
print("Recordings needing Drive upload (VERIFICATION_FAILED, YT verified):", len(rows))

success = 0
skipped = 0
failed = 0

for rec in rows:
    uuid = rec["zoom_id"]
    meeting_id = rec["meeting_id"]
    topic = rec["topic"]
    account = rec["account_name"] or "Zoom Account 1"
    start_time = rec["start_time"]
    playlist_name = rec["playlist"] or "Miscellaneous"

    print("\n" + "-"*50)
    print("Topic:", topic[:55])

    zoom_client = zoom_clients.get(account)
    if not zoom_client:
        print("  SKIP: no zoom client for", account)
        skipped += 1
        continue

    if uuid.startswith("/") or "//" in uuid:
        encoded = urllib.parse.quote(urllib.parse.quote(uuid, safe=""), safe="")
    else:
        encoded = urllib.parse.quote(uuid, safe="")

    recording_data = zoom_client.get_recording_details(encoded)
    if not recording_data and meeting_id:
        recording_data = zoom_client.get_recording_details(meeting_id)

    if not recording_data:
        print("  SKIP: not found on Zoom (expired or deleted)")
        skipped += 1
        continue

    expected_date = start_time[:10] if start_time else None
    video_url = None
    for f in recording_data.get("recording_files", []):
        file_date = f.get("recording_start", "")[:10]
        if expected_date and file_date and file_date != expected_date:
            continue
        if f.get("file_type") == "MP4" and not video_url:
            video_url = f.get("download_url")

    if not video_url:
        for f in recording_data.get("recording_files", []):
            if f.get("file_type") == "MP4" and not video_url:
                video_url = f.get("download_url")

    if not video_url:
        print("  SKIP: no MP4 found")
        skipped += 1
        continue

    names = generate_names(topic, start_time)
    video_filename = names["video_filename"]
    video_path = os.path.join(DOWNLOAD_DIR, video_filename)

    try:
        print("  Downloading from Zoom...")
        zoom_client.download_file(video_url, video_path)

        drive_folder_id, _ = get_drive_folders(playlist_name)
        if not drive_folder_id:
            print("  SKIP: no drive folder for playlist:", playlist_name)
            skipped += 1
            continue

        print("  Uploading to Drive folder:", drive_folder_id)
        drive_file_id = drive.upload_file(video_path, video_filename, drive_folder_id)
        drive_url = "https://drive.google.com/file/d/" + drive_file_id + "/view"
        print("  Drive URL:", drive_url)

        db.update_recording(uuid, {
            "drive_url": drive_url,
            "drive_uploaded_at": datetime.datetime.now().isoformat(),
            "zoom_deletion_status": "PENDING",
            "zoom_deletion_error": None,
        })
        db.add_log("INFO", "Drive upload + reset to PENDING: " + uuid + " -> " + drive_url)
        print("  DB updated: drive_url set, reset to PENDING. SUCCESS.")
        success += 1

    except Exception as e:
        print("  ERROR:", str(e)[:100])
        print(traceback.format_exc()[:300])
        failed += 1
    finally:
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except Exception:
            pass

print("\n\n=== DONE ===")
print("Success:", success)
print("Skipped:", skipped)
print("Failed:", failed)
print("\nSuccessful recordings reset to PENDING — will auto-delete from Zoom in next cycle.")
