import sys, json
sys.path.insert(0, ".")
from src.config import (YOUTUBE_CLIENT_SECRET_PATH, YOUTUBE_TOKEN_PATH,
                        PLAYLIST_CONFIG_PATH)
from src.youtube_client import YouTubeClient
from src.drive_client import DriveClient
from src import config

# Init clients
yt = YouTubeClient(YOUTUBE_CLIENT_SECRET_PATH, YOUTUBE_TOKEN_PATH)
drive = DriveClient(
    auth_mode=config.DRIVE_AUTH_MODE,
    token_path=config.DRIVE_TOKEN_PATH,
    client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
    service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE
)

PLAYLIST_NAME = "WORK HUB MEET"
PLAYLIST_DESC = "Recordings from THE WORK HUB meetings - auto-uploaded by YTZ Automation"

# ── 1. Create YouTube playlist ──────────────────────────────────────────────
print("Creating YouTube playlist:", PLAYLIST_NAME)
request = yt.youtube.playlists().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": PLAYLIST_NAME,
            "description": PLAYLIST_DESC
        },
        "status": {
            "privacyStatus": "unlisted"
        }
    }
)
response = request.execute()
yt_playlist_id = response["id"]
print("  YouTube Playlist ID:", yt_playlist_id)

# ── 2. Create Drive folder for videos ────────────────────────────────────────
# Find the parent folder (same parent as other team folders)
# Load config to get an existing drive folder id to find parent
with open(PLAYLIST_CONFIG_PATH, 'r') as f:
    cfg = json.load(f)

# Get parent folder of an existing playlist's drive folder to use as parent
existing_folder = cfg["playlists"][0].get("drive_folder_id")
print("Finding parent folder from existing folder:", existing_folder)

parent_folder_meta = drive.service.files().get(
    fileId=existing_folder,
    fields="id, name, parents"
).execute()
parent_ids = parent_folder_meta.get("parents", [])
parent_id = parent_ids[0] if parent_ids else None
print("  Parent folder ID:", parent_id)

# Create video folder
print("Creating Drive video folder:", PLAYLIST_NAME)
video_folder_meta = {
    "name": PLAYLIST_NAME,
    "mimeType": "application/vnd.google-apps.folder",
    "parents": [parent_id] if parent_id else []
}
video_folder = drive.service.files().create(body=video_folder_meta, fields="id, name").execute()
drive_folder_id = video_folder["id"]
print("  Drive Video Folder ID:", drive_folder_id)

# Create transcript subfolder inside it
print("Creating Drive transcript folder: Transcripts")
transcript_folder_meta = {
    "name": "Transcripts",
    "mimeType": "application/vnd.google-apps.folder",
    "parents": [drive_folder_id]
}
transcript_folder = drive.service.files().create(body=transcript_folder_meta, fields="id, name").execute()
transcript_folder_id = transcript_folder["id"]
print("  Drive Transcript Folder ID:", transcript_folder_id)

# ── 3. Update playlists.json ─────────────────────────────────────────────────
new_entry = {
    "playlist_id": yt_playlist_id,
    "playlist_name": PLAYLIST_NAME,
    "category": "Work Hub",
    "drive_folder_id": drive_folder_id,
    "transcript_folder_id": transcript_folder_id,
    "meeting_ids": [],
    "keywords": [
        "the work hub",
        "work hub",
        "work hub meet",
        "workhub"
    ]
}

cfg["playlists"].append(new_entry)

with open(PLAYLIST_CONFIG_PATH, 'w') as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

print("\nplaylists.json updated.")
print("\n=== SUCCESS ===")
print("YouTube Playlist:", PLAYLIST_NAME, "->", yt_playlist_id)
print("Drive Video Folder:     ", drive_folder_id)
print("Drive Transcript Folder:", transcript_folder_id)
print("Keywords:", new_entry["keywords"])
