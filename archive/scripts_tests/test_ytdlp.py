import yt_dlp
import sys
import os

def test_download(video_url):
    ydl_opts = {
        'format': 'best[ext=mp4][height<=720]/best',
        'outtmpl': 'test_download.%(ext)s',
        'quiet': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Fetching info...")
            info = ydl.extract_info(video_url, download=True)
            print(f"Success! Downloaded {info['title']}")
            print(f"File size: {os.path.getsize('test_download.mp4') / (1024*1024):.2f} MB")
    except Exception as e:
        print("ERROR:", e)

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://youtu.be/OeiNITZwUUzo'
    test_download(url)
