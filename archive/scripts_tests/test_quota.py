import traceback
from src.youtube_client import YouTubeClient
import googleapiclient.errors

def test():
    print("Testing upload to check exact error...")
    try:
        yt = YouTubeClient('secrets/client_secret.json', 'secrets/token.json')
        # We need an actual video to test - let's find the review meet recording
        video_path = r'c:\Users\HP\ZoomAutomation\src\REVIEW MEET RECORDING.mp4'
        import os
        if not os.path.exists(video_path):
            print(f"File not found: {video_path}")
            return
            
        print("Uploading test video...")
        yt.upload_video(video_path, "Diagnostic Test", "Diagnostic Description")
        print("Upload succeeded! No quota issue.")
    except googleapiclient.errors.HttpError as e:
        print("--- HTTP ERROR CAUGHT ---")
        print("STATUS:", e.resp.status)
        print("REASON:", e.reason)
        print("ERROR DETAILS:", e.error_details)
        print("CONTENT:", e.content.decode('utf-8') if hasattr(e, 'content') else repr(e))
    except Exception as e:
        print("OTHER ERROR:", traceback.format_exc())

if __name__ == '__main__':
    test()
