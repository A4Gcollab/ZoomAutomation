"""
Backfill: Upload existing YouTube videos to Google Drive.
Run this on the PRODUCTION server (needs disk space for temp downloads).

This script:
1. Gets all COMPLETED + YOUTUBE_COMPRESSING recordings with YouTube URLs but no Drive URL
2. Downloads compressed video from YouTube using yt-dlp
3. Uploads to the correct Google Drive folder
4. Updates the DB with the Drive URL
5. Cleans up the local file after each upload
"""
import sys, os, time, traceback
sys.path.insert(0, '.')

import sqlite3
import json
from pathlib import Path

DB = 'data/vong_v2.db'
CFG = 'config/playlists.json'
DOWNLOADS = 'downloads'

def main():
    # Init Drive client
    from src.drive_client import DriveClient
    from src import config

    sa_path = str(config.DRIVE_SERVICE_ACCOUNT_FILE) if hasattr(config, 'DRIVE_SERVICE_ACCOUNT_FILE') and config.DRIVE_SERVICE_ACCOUNT_FILE else 'secrets/service_account.json'
    root_folder = config.DRIVE_ROOT_FOLDER_ID if hasattr(config, 'DRIVE_ROOT_FOLDER_ID') else None

    drive = DriveClient(
        auth_mode='service_account',
        service_account_file=sa_path
    )

    # Load playlist config for Drive folder mapping
    with open(CFG, 'r') as f:
        config = json.load(f)

    def get_drive_folder(playlist_name):
        for pl in config.get('playlists', []):
            if pl.get('playlist_name') == playlist_name:
                return pl.get('drive_folder_id'), pl.get('transcript_folder_id')
        return None, None

    # Get recordings that need Drive upload
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT zoom_id, topic, youtube_url, playlist, transcript_url
        FROM recordings 
        WHERE status IN ('COMPLETED', 'YOUTUBE_COMPRESSING') 
        AND youtube_url IS NOT NULL
        AND (drive_url IS NULL OR drive_url = '')
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    print(f"Found {len(rows)} videos needing Drive upload\n")
    os.makedirs(DOWNLOADS, exist_ok=True)

    success = 0
    failed = 0

    for i, d in enumerate(rows, 1):
        topic = d['topic']
        youtube_url = d['youtube_url']
        playlist = d.get('playlist', 'Miscellaneous')
        zoom_id = d['zoom_id']

        print(f"[{i}/{len(rows)}] {topic[:50]}")

        drive_folder_id, transcript_folder_id = get_drive_folder(playlist)
        if not drive_folder_id:
            # Use root folder as fallback
            drive_folder_id = root_folder
            print(f"  No Drive folder for '{playlist}', using root folder")

        zoom_url = d.get('video_url')
        account_name = d.get('account_name', 'Zoom Account 1')
        
        # Try YouTube first
        compressed_path = os.path.join(DOWNLOADS, f"{zoom_id}_video.mp4")
        dl_success = False
        
        try:
            import yt_dlp
            ydl_opts = {
                'format': 'best[ext=mp4][height<=720]/best',
                'outtmpl': compressed_path,
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(youtube_url, download=True)
            dl_success = True
            print("  Downloaded from YouTube (compressed)")
        except Exception as e:
            print(f"  YouTube download failed ({str(e)[:100]}). Trying Zoom fallback...")
            
            # Fallback to Zoom
            if zoom_url:
                try:
                    from src.config import get_zoom_clients
                    z_clients = get_zoom_clients()
                    z_client = z_clients.get(account_name)
                    if z_client:
                        print(f"  Downloading original from Zoom...")
                        if z_client.download_file(zoom_url, compressed_path):
                            dl_success = True
                            print("  Downloaded from Zoom successfully")
                        else:
                            print("  Zoom download returned False")
                    else:
                        print(f"  Zoom client not found for {account_name}")
                except Exception as ze:
                    print(f"  Zoom fallback failed: {ze}")
            else:
                print("  No Zoom URL available for fallback")

        if not dl_success:
            print("  Could not download video from anywhere. Skipping.")
            failed += 1
            continue

        try:
            file_size_mb = os.path.getsize(compressed_path) / (1024*1024)
            print(f"  Final File Size: {file_size_mb:.1f} MB")

            # Upload to Drive
            safe_title = "".join(c for c in topic if c.isalnum() or c in " ._-")[:100]
            filename = f"{safe_title}.mp4"
            drive_file_id = drive.upload_file(compressed_path, filename, drive_folder_id)
            drive_url = f"https://drive.google.com/file/d/{drive_file_id}/view"
            print(f"  Uploaded to Drive: {drive_url}")

            # Update DB
            conn2 = sqlite3.connect(DB, timeout=30)
            conn2.execute("UPDATE recordings SET drive_url=? WHERE zoom_id=?", (drive_url, zoom_id))
            conn2.commit()
            conn2.close()

            success += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
        finally:
            # Always cleanup
            if os.path.exists(compressed_path):
                os.remove(compressed_path)

        time.sleep(1)  # Rate limit safety

    print(f"\n=== Results: {success} uploaded, {failed} failed ===")

if __name__ == '__main__':
    main()
