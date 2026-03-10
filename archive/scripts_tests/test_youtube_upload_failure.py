from src.main import BackgroundService
import traceback

def test():
    print("Testing upload...")
    try:
        s = BackgroundService()
        s._init_clients()
        # Find the video file
        import os
        videos = [f for f in os.listdir('downloads') if f.endswith('.mp4')]
        if not videos:
            print("No videos found to test with.")
            return
            
        print(f"Uploading {videos[0]}...")
        s.youtube.upload_video(f'downloads/{videos[0]}', 'Test Video', 'Test Description')
        print("Upload succeeded!")
    except Exception as e:
        print("Upload failed!")
        print(traceback.format_exc())

if __name__ == '__main__':
    test()
