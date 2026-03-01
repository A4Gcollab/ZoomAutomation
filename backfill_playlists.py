"""
Backfill: Add existing YouTube videos to their correct playlists.
Run this AFTER YouTube API quota resets (~1:30 PM IST / midnight PT).

This script:
1. Gets all COMPLETED + YOUTUBE_COMPRESSING recordings with YouTube URLs
2. Checks if each video is already in its assigned playlist
3. Adds missing videos to their correct playlist
"""
import sys, time
sys.path.insert(0, '.')

import sqlite3
from src.youtube_client import YouTubeClient
from src.config import YOUTUBE_CLIENT_SECRET_PATH, YOUTUBE_TOKEN_PATH, PLAYLIST_CONFIG_PATH
import json

DB = r'c:\Users\HP\ZoomAutomation\data\vong_v2.db'

# Init YouTube client
yt = YouTubeClient(str(YOUTUBE_CLIENT_SECRET_PATH), str(YOUTUBE_TOKEN_PATH))

# Load playlist config
with open(str(PLAYLIST_CONFIG_PATH), 'r') as f:
    config = json.load(f)

def get_playlist_id(playlist_name):
    for pl in config.get('playlists', []):
        if pl.get('playlist_name') == playlist_name:
            return pl.get('playlist_id')
    return config.get('default_playlist_id')

# Get recordings
conn = sqlite3.connect(DB, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("""SELECT zoom_id, topic, youtube_url, playlist FROM recordings 
    WHERE status IN ('COMPLETED','YOUTUBE_COMPRESSING') AND youtube_url IS NOT NULL""")
rows = [dict(r) for r in cur.fetchall()]
conn.close()

print(f"Found {len(rows)} videos to check/add to playlists\n")

success = 0
skipped = 0
failed = 0

for i, d in enumerate(rows, 1):
    topic = d['topic']
    yt_url = d['youtube_url']
    playlist = d.get('playlist', '')
    
    # Extract video ID
    if 'youtu.be' in yt_url:
        vid_id = yt_url.split('/')[-1]
    elif 'watch' in yt_url:
        vid_id = yt_url.split('v=')[-1].split('&')[0]
    else:
        print(f"[{i}/{len(rows)}] SKIP {topic[:40]} - bad URL: {yt_url}")
        skipped += 1
        continue
    
    yt_pl_id = get_playlist_id(playlist)
    if not yt_pl_id or yt_pl_id == 'PENDING_CREATION':
        print(f"[{i}/{len(rows)}] SKIP {topic[:40]} - no playlist ID for: {playlist}")
        skipped += 1
        continue
    
    try:
        yt.add_to_playlist(vid_id, yt_pl_id)
        print(f"[{i}/{len(rows)}] ADDED {topic[:40]} -> {playlist}")
        success += 1
        time.sleep(1)  # Rate limit safety
    except Exception as e:
        error_str = str(e)
        if 'duplicate' in error_str.lower() or 'already' in error_str.lower() or 'conflict' in error_str.lower():
            print(f"[{i}/{len(rows)}] ALREADY IN PLAYLIST: {topic[:40]}")
            skipped += 1
        elif 'quota' in error_str.lower():
            print(f"\n⚠️  QUOTA EXCEEDED at video {i}. Run again later.")
            break
        else:
            print(f"[{i}/{len(rows)}] FAILED {topic[:40]}: {e}")
            failed += 1

print(f"\n=== Results: {success} added, {skipped} skipped, {failed} failed ===")
