"""
Fix VERIFICATION_FAILED recordings:
1. Still on Zoom + YouTube deleted + Drive exists  -> Download from Zoom, re-upload YouTube, delete from Zoom
2. NOT on Zoom + YouTube deleted + Drive exists    -> Download from Drive, re-upload YouTube (mark DELETED since not on Zoom)
3. NOT on Zoom + YouTube exists + Drive missing   -> Download from YouTube (yt-dlp), upload to Drive (mark DELETED)
4. Completely unrecoverable (both deleted, not on Zoom) -> Mark UNRECOVERABLE, log it
"""
import sys, os, urllib.parse, datetime, json, traceback, io
sys.path.insert(0, ".")

from src.db_sql import db
from src.config import (ZOOM_ACCOUNTS, DOWNLOAD_DIR, PLAYLIST_CONFIG_PATH)
from src.drive_client import DriveClient
from src.youtube_client import YouTubeClient
from src.zoom_client import ZoomClient
from src.utils import generate_names
from src import config

# ── clients ──────────────────────────────────────────────────────────────────
drive = DriveClient(
    auth_mode=config.DRIVE_AUTH_MODE,
    token_path=config.DRIVE_TOKEN_PATH,
    client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
    service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE
)

youtube = YouTubeClient(
    client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
    token_path=config.YOUTUBE_TOKEN_PATH
)

zoom_clients = {}
for i, creds in enumerate(ZOOM_ACCOUNTS, 1):
    zoom_clients["Zoom Account " + str(i)] = ZoomClient(creds)

with open(PLAYLIST_CONFIG_PATH) as f:
    playlist_cfg = json.load(f)

# ── helpers ───────────────────────────────────────────────────────────────────
def get_drive_folders(playlist_name):
    for pl in playlist_cfg.get("playlists", []):
        if pl.get("playlist_name") == playlist_name:
            return pl.get("drive_folder_id"), pl.get("transcript_folder_id")
    return playlist_cfg.get("drive_folder_id"), playlist_cfg.get("transcript_folder_id")

def get_yt_playlist_id(playlist_name):
    for pl in playlist_cfg.get("playlists", []):
        if pl.get("playlist_name") == playlist_name:
            return pl.get("playlist_id")
    return playlist_cfg.get("default_playlist_id")

def zoom_encoded(uuid):
    if uuid.startswith("/") or "//" in uuid:
        return urllib.parse.quote(urllib.parse.quote(uuid, safe=""), safe="")
    return urllib.parse.quote(uuid, safe="")

def get_zoom_mp4(zoom_client, uuid, meeting_id, start_time):
    data = zoom_client.get_recording_details(zoom_encoded(uuid))
    if not data and meeting_id:
        data = zoom_client.get_recording_details(meeting_id)
    if not data:
        return None, None
    expected_date = start_time[:10] if start_time else None
    video_url = None
    for f in data.get("recording_files", []):
        if f.get("file_type") == "MP4":
            file_date = f.get("recording_start", "")[:10]
            if expected_date and file_date and file_date != expected_date:
                continue
            video_url = f.get("download_url")
            break
    if not video_url:
        for f in data.get("recording_files", []):
            if f.get("file_type") == "MP4":
                video_url = f.get("download_url")
                break
    return video_url, data

def download_from_drive(drive_url, dest_path):
    """Download a file from Google Drive using the Drive API."""
    # Extract file ID from URL
    file_id = None
    if "/file/d/" in drive_url:
        file_id = drive_url.split("/file/d/")[1].split("/")[0]
    if not file_id:
        raise ValueError("Cannot extract file_id from: " + drive_url)

    import io
    request = drive.service.files().get_media(fileId=file_id)
    from googleapiclient.http import MediaIoBaseDownload
    with open(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                if pct % 20 == 0:
                    print(f"    Drive download {pct}%...")
    return dest_path

def download_from_youtube(youtube_url, dest_path):
    """Download from YouTube using yt-dlp."""
    import yt_dlp
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": dest_path,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    # yt-dlp may add extension
    if not os.path.exists(dest_path):
        # try with .mp4
        if os.path.exists(dest_path + ".mp4"):
            os.rename(dest_path + ".mp4", dest_path)

def upload_to_youtube(video_path, rec):
    """Upload a video to YouTube and add to playlist. Returns (video_id, youtube_url)."""
    names = generate_names(rec["topic"], rec["start_time"])
    youtube_title = names["youtube_title"]
    description = f"{rec['topic']}\n\nRecorded: {rec['start_time']}\nPlaylist: {rec['playlist']}"
    video_id = youtube.upload_video(
        file_path=video_path,
        title=youtube_title,
        description=description,
        privacy_status="unlisted"
    )
    new_url = "https://youtu.be/" + video_id
    # Add to playlist
    yt_pl_id = get_yt_playlist_id(rec["playlist"])
    if yt_pl_id:
        try:
            youtube.add_to_playlist(video_id, yt_pl_id)
            print(f"    Added to playlist: {rec['playlist']}")
        except Exception as e:
            print(f"    Warning: playlist add failed: {e}")
    return video_id, new_url

# ── load all VERIFICATION_FAILED ─────────────────────────────────────────────
cur = db._get_cursor()
cur.execute("""
    SELECT zoom_id, meeting_id, topic, youtube_url, drive_url, account_name,
           start_time, playlist, zoom_deletion_error
    FROM recordings
    WHERE zoom_deletion_status = 'VERIFICATION_FAILED'
""")
rows = [dict(r) for r in cur.fetchall()]
print(f"Total VERIFICATION_FAILED: {len(rows)}")

counts = {"yt_reuploaded": 0, "drive_reuploaded": 0, "deleted_zoom": 0,
          "already_off_zoom": 0, "unrecoverable": 0, "failed": 0}

for rec in rows:
    uuid = rec["zoom_id"]
    meeting_id = rec["meeting_id"]
    topic = rec["topic"]
    account = rec["account_name"] or "Zoom Account 1"
    start_time = rec["start_time"]
    playlist_name = rec["playlist"] or "Miscellaneous"
    err = rec["zoom_deletion_error"] or ""
    yt_live = "YT:True" in err
    dr_live = "Drive:True" in err
    has_yt_url = bool(rec["youtube_url"])
    has_dr_url = bool(rec["drive_url"])

    print(f"\n{'─'*55}")
    print(f"Topic: {topic[:55]}")
    print(f"  OnZoom_err: {err}  DB_YT:{has_yt_url} DB_DR:{has_dr_url}")

    zoom_client = zoom_clients.get(account)
    names = generate_names(topic, start_time)
    video_filename = names["video_filename"]
    video_path = os.path.join(DOWNLOAD_DIR, video_filename)

    try:
        # ── Check if still on Zoom ────────────────────────────────────────
        on_zoom = False
        zoom_mp4_url = None
        if zoom_client:
            zoom_mp4_url, _ = get_zoom_mp4(zoom_client, uuid, meeting_id, start_time)
            on_zoom = bool(zoom_mp4_url)

        # ── Case: both YouTube & Drive exist → just reset to PENDING ──────
        if yt_live and dr_live:
            print("  Both YT and Drive verified live — resetting to PENDING for deletion")
            db.update_recording(uuid, {
                "zoom_deletion_status": "PENDING",
                "zoom_deletion_error": None
            })
            counts["deleted_zoom"] += 1
            continue

        # ── Case: NOT on Zoom at all ──────────────────────────────────────
        if not on_zoom:
            print("  Not on Zoom (expired/already deleted)")
            if not yt_live and not dr_live and not has_yt_url and not has_dr_url:
                print("  UNRECOVERABLE: no copy anywhere")
                db.update_recording(uuid, {
                    "zoom_deletion_status": "UNRECOVERABLE",
                    "zoom_deletion_error": "Expired from Zoom, YouTube deleted, no Drive"
                })
                counts["unrecoverable"] += 1
                continue

            if not yt_live and has_dr_url:
                # YouTube deleted, Drive exists, Zoom expired → download from Drive, re-upload to YouTube
                print("  YouTube deleted, Drive exists — downloading from Drive to re-upload to YouTube")
                download_from_drive(rec["drive_url"], video_path)
                print(f"  Downloaded from Drive ({os.path.getsize(video_path)//1024//1024} MB)")
                _, new_yt_url = upload_to_youtube(video_path, rec)
                print(f"  Re-uploaded to YouTube: {new_yt_url}")
                db.update_recording(uuid, {
                    "youtube_url": new_yt_url,
                    "zoom_deletion_status": "DELETED",  # already off Zoom
                    "zoom_deleted_at": datetime.datetime.now().isoformat(),
                    "zoom_deletion_error": "Was off Zoom; YouTube re-uploaded from Drive"
                })
                db.add_log("INFO", f"YT re-upload from Drive (off Zoom): {uuid} -> {new_yt_url}")
                counts["yt_reuploaded"] += 1
                counts["already_off_zoom"] += 1
                continue

            if yt_live and not has_dr_url:
                # YouTube exists, no Drive, Zoom expired → download from YouTube, upload to Drive
                print("  Drive missing, YouTube exists — downloading from YouTube via yt-dlp")
                download_from_youtube(rec["youtube_url"], video_path)
                if not os.path.exists(video_path):
                    print("  ERROR: yt-dlp download failed — file not found")
                    counts["failed"] += 1
                    continue
                print(f"  Downloaded from YouTube ({os.path.getsize(video_path)//1024//1024} MB)")
                drive_folder_id, _ = get_drive_folders(playlist_name)
                if not drive_folder_id:
                    print("  SKIP: no drive folder for playlist:", playlist_name)
                    counts["failed"] += 1
                    continue
                drive_file_id = drive.upload_file(video_path, video_filename, drive_folder_id)
                new_dr_url = "https://drive.google.com/file/d/" + drive_file_id + "/view"
                print(f"  Uploaded to Drive: {new_dr_url}")
                db.update_recording(uuid, {
                    "drive_url": new_dr_url,
                    "drive_uploaded_at": datetime.datetime.now().isoformat(),
                    "zoom_deletion_status": "DELETED",  # already off Zoom
                    "zoom_deleted_at": datetime.datetime.now().isoformat(),
                    "zoom_deletion_error": "Was off Zoom; Drive uploaded from YouTube"
                })
                db.add_log("INFO", f"Drive upload from YouTube (off Zoom): {uuid} -> {new_dr_url}")
                counts["drive_reuploaded"] += 1
                counts["already_off_zoom"] += 1
                continue

            if not yt_live and not has_dr_url:
                print("  UNRECOVERABLE: YouTube deleted, no Drive, not on Zoom")
                db.update_recording(uuid, {
                    "zoom_deletion_status": "UNRECOVERABLE",
                    "zoom_deletion_error": "Off Zoom, YouTube deleted, no Drive URL"
                })
                counts["unrecoverable"] += 1
                continue

            # Other off-Zoom edge cases — mark as DELETED since it's not on Zoom anyway
            print("  Off Zoom, no clear recovery path — marking DELETED")
            db.update_recording(uuid, {
                "zoom_deletion_status": "DELETED",
                "zoom_deleted_at": datetime.datetime.now().isoformat(),
                "zoom_deletion_error": "Off Zoom — marked clean"
            })
            counts["already_off_zoom"] += 1
            continue

        # ── Still on Zoom ─────────────────────────────────────────────────
        print("  Still on Zoom ✓")

        if not yt_live and has_dr_url:
            # Download from Zoom, re-upload to YouTube, then reset to PENDING (bg service will delete)
            print("  YouTube deleted but Drive OK — downloading from Zoom to re-upload YouTube")
            zoom_client.download_file(zoom_mp4_url, video_path)
            print(f"  Downloaded from Zoom ({os.path.getsize(video_path)//1024//1024} MB)")
            _, new_yt_url = upload_to_youtube(video_path, rec)
            print(f"  Re-uploaded to YouTube: {new_yt_url}")
            db.update_recording(uuid, {
                "youtube_url": new_yt_url,
                "zoom_deletion_status": "PENDING",
                "zoom_deletion_error": None
            })
            db.add_log("INFO", f"YT re-upload + reset to PENDING: {uuid} -> {new_yt_url}")
            print("  Reset to PENDING — background service will verify both and delete from Zoom")
            counts["yt_reuploaded"] += 1
            counts["deleted_zoom"] += 1
            continue

        if yt_live and not has_dr_url:
            # YouTube exists, no Drive → download from Zoom, upload to Drive, reset PENDING
            print("  Drive missing but YouTube OK — downloading from Zoom to upload Drive")
            zoom_client.download_file(zoom_mp4_url, video_path)
            print(f"  Downloaded from Zoom ({os.path.getsize(video_path)//1024//1024} MB)")
            drive_folder_id, _ = get_drive_folders(playlist_name)
            if not drive_folder_id:
                print("  SKIP: no drive folder for playlist:", playlist_name)
                counts["failed"] += 1
                continue
            drive_file_id = drive.upload_file(video_path, video_filename, drive_folder_id)
            new_dr_url = "https://drive.google.com/file/d/" + drive_file_id + "/view"
            print(f"  Uploaded to Drive: {new_dr_url}")
            db.update_recording(uuid, {
                "drive_url": new_dr_url,
                "drive_uploaded_at": datetime.datetime.now().isoformat(),
                "zoom_deletion_status": "PENDING",
                "zoom_deletion_error": None
            })
            db.add_log("INFO", f"Drive upload + reset to PENDING: {uuid} -> {new_dr_url}")
            print("  Reset to PENDING — background service will verify and delete from Zoom")
            counts["drive_reuploaded"] += 1
            counts["deleted_zoom"] += 1
            continue

        if not yt_live and not has_dr_url:
            # Nothing backed up, download from Zoom, upload both
            print("  Both missing — downloading from Zoom to upload both YouTube and Drive")
            zoom_client.download_file(zoom_mp4_url, video_path)
            print(f"  Downloaded ({os.path.getsize(video_path)//1024//1024} MB)")
            _, new_yt_url = upload_to_youtube(video_path, rec)
            print(f"  Re-uploaded to YouTube: {new_yt_url}")
            drive_folder_id, _ = get_drive_folders(playlist_name)
            new_dr_url = None
            if drive_folder_id:
                drive_file_id = drive.upload_file(video_path, video_filename, drive_folder_id)
                new_dr_url = "https://drive.google.com/file/d/" + drive_file_id + "/view"
                print(f"  Uploaded to Drive: {new_dr_url}")
            db.update_recording(uuid, {
                "youtube_url": new_yt_url,
                "drive_url": new_dr_url,
                "drive_uploaded_at": datetime.datetime.now().isoformat() if new_dr_url else None,
                "zoom_deletion_status": "PENDING",
                "zoom_deletion_error": None
            })
            counts["yt_reuploaded"] += 1
            if new_dr_url:
                counts["drive_reuploaded"] += 1
            counts["deleted_zoom"] += 1
            continue

    except Exception as e:
        print(f"  ERROR: {str(e)[:120]}")
        print(traceback.format_exc()[:400])
        counts["failed"] += 1
    finally:
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except Exception:
            pass

print("\n\n=== DONE ===")
print(f"YouTube re-uploaded:         {counts['yt_reuploaded']}")
print(f"Drive re-uploaded:           {counts['drive_reuploaded']}")
print(f"Reset to PENDING (will delete from Zoom): {counts['deleted_zoom']}")
print(f"Already off Zoom (cleaned up): {counts['already_off_zoom']}")
print(f"Unrecoverable (marked):      {counts['unrecoverable']}")
print(f"Failed (errors):             {counts['failed']}")
