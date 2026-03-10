"""Upload a real video as the 8th upload to test quota enforcement."""
import pickle, os, sys

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load credentials
with open('test_quota_workspace/test_token.json', 'rb') as f:
    creds = pickle.load(f)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())

youtube = build('youtube', 'v3', credentials=creds)

video_path = r'c:\Users\HP\ZoomAutomation\src\REVIEW MEET RECORDING.mp4'
size_mb = os.path.getsize(video_path) / 1024 / 1024
print(f'Uploading REAL video: {size_mb:.1f} MB')
print(f'This is upload #8 today - testing quota enforcement')
print('=' * 60)

try:
    body = {
        'snippet': {
            'title': '[QUOTA TEST 8] Real Video - Delete Me',
            'description': 'Real video quota test. Safe to delete.',
            'categoryId': '22'
        },
        'status': {'privacyStatus': 'private'}
    }
    media = MediaFileUpload(video_path, chunksize=5*1024*1024, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    
    print('Starting upload...')
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f'  Progress: {int(status.progress() * 100)}%')
    
    video_id = response.get('id', 'unknown')
    print()
    print('RESULT: SUCCESS')
    print(f'Video ID: {video_id}')
    print('Upload #8 SUCCEEDED - quota was NOT enforced at 10,000 units!')
    
    with open('test_quota_workspace/uploaded_video_ids.txt', 'a') as f:
        f.write(video_id + '\n')

except Exception as e:
    error_str = str(e)
    print()
    print('RESULT: FAILED')
    print(f'Error: {error_str[:300]}')
    if 'quota' in error_str.lower():
        print()
        print('>>> QUOTA HIT! The 10,000 unit limit IS enforced.')
        print('>>> Max reliable uploads per project per day = 6')
    else:
        print('>>> Failed for a NON-QUOTA reason.')
    sys.exit(1)
