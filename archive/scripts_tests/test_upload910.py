"""Upload 2 more real videos as #9 and #10 to find the hard quota limit."""
import pickle, os, sys, time

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

for i in [9, 10]:
    print(f'\n{"=" * 60}')
    print(f'Upload #{i} - Real video ({size_mb:.1f} MB)')
    print(f'{"=" * 60}')
    
    try:
        body = {
            'snippet': {
                'title': f'[QUOTA TEST {i}] Real Video - Delete Me',
                'description': 'Quota limit test. Safe to delete.',
                'categoryId': '22'
            },
            'status': {'privacyStatus': 'private'}
        }
        media = MediaFileUpload(video_path, chunksize=5*1024*1024, resumable=True)
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
        
        print('Uploading...')
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f'  Progress: {int(status.progress() * 100)}%')
        
        video_id = response.get('id', 'unknown')
        print(f'SUCCESS! Video ID: {video_id}')
        
        with open('test_quota_workspace/uploaded_video_ids.txt', 'a') as f:
            f.write(video_id + '\n')
        
        if i == 9:
            print('Waiting 10 seconds before next upload...')
            time.sleep(10)

    except Exception as e:
        error_str = str(e)
        print(f'FAILED at upload #{i}!')
        print(f'Error: {error_str[:400]}')
        if 'quota' in error_str.lower():
            print(f'\n>>> QUOTA HIT at upload #{i}!')
            print(f'>>> Hard limit reached after {i-1} successful uploads.')
        else:
            print(f'>>> Non-quota error.')
        sys.exit(1)

print(f'\n{"=" * 60}')
print(f'BOTH uploads #9 and #10 SUCCEEDED!')
print(f'Total today: 10 uploads = 16,000 units used on a 10,000 limit!')
print(f'{"=" * 60}')
