"""Test script to verify the production YouTubeClient can upload 13 videos.
This uses the EXACT same YouTubeClient as main.py but skips Zoom/Drive to focus purely on the YouTube API limits.
"""
import os
import sys
import time
from src.youtube_client import YouTubeClient

client_secret_path = 'secrets/client_secret.json'
token_path = 'secrets/token.json'

print("Initializing production YouTubeClient...")
youtube = YouTubeClient(client_secret_path, token_path)

# Use our real video file
video_path = r'c:\Users\HP\ZoomAutomation\src\REVIEW MEET RECORDING.mp4'

print("\nCreating a test playlist on vong.meetings2...")
try:
    playlist_id = youtube.create_playlist(
        title="Production Pipeline Quota Test",
        description="Testing 13 uploads using the production youtube_client.py",
        privacy_status="private"
    )
    print(f"Playlist created! ID: {playlist_id}")
except Exception as e:
    print(f"Failed to create playlist. Error: {e}")
    sys.exit(1)

success_count = 0
target = 13

with open('test_quota_workspace/uploaded_video_ids.txt', 'a') as f:
    for i in range(1, target + 1):
        print(f"\n============================================================")
        print(f"Upload #{i}/{target} using production pipeline")
        print(f"============================================================")
        
        try:
            # 1. UPLOAD
            title = f"[QUOTA TEST PROD] Video {i} - Delete Me"
            desc = "Testing production code flow for quota limits."
            
            video_id = youtube.upload_video(
                file_path=video_path,
                title=title,
                description=desc,
                privacy_status="private"
            )
            
            f.write(f"{video_id}\n")
            
            # 2. STATUS CHECK
            status = youtube.get_video_status(video_id)
            print(f"   Video Status: {status}")
            
            # 3. PLAYLIST ADD
            print(f"   Adding to playlist {playlist_id}...")
            youtube.add_to_playlist(video_id, playlist_id)
            
            # (Skipping captions since we don't have a VTT file handy, but upload + playlist is the bulk of the quota)
            
            success_count += 1
            print(f"   Upload #{i} PIPELINE COMPLETE!")
            
            if i < target:
                print("Waiting 10 seconds...")
                time.sleep(10)
                
        except Exception as e:
            error_str = str(e)
            print(f"\nFAILED at upload #{i}!")
            print(f"Error: {error_str[:500]}")
            if 'quota' in error_str.lower():
                print("\n>>> QUOTA HIT! Our test failed when using production calls.")
            break

print(f"\n============================================================")
print(f"PIPELINE TEST FINISHED")
print(f"Successful uploads using production code: {success_count}/{target}")
print(f"============================================================")

if success_count == target:
    print("\n✅ VONG.MEETINGS2 CHANNEL SUCCESSFULLY BYPASSES THE 6-VIDEO LIMIT EVEN WITH PRODUCTION OVERHEAD!")
