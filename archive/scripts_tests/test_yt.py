import os
import sys

# Add src to the path so we can import yt_downloader
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from yt_downloader import YouTubeDownloader

def test():
    print("Testing YouTube Downloader...")
    
    # Initialize the downloader
    # This will use the cookies.txt file if it exists in the root directory
    downloader = YouTubeDownloader()
    
    # Replace this with a valid YouTube URL (unlisted or public)
    test_url = "https://www.youtube.com/watch?v=yWbA1hYy7i4"  # Change to a real unlisted video URL
    
    print(f"\nAttempting to download: {test_url}")
    print("This will test if yt-dlp can access the video using your cookies.")
    
    try:
        # Download the video
        # It will be saved to the 'downloads' folder by default
        video_path = downloader.download_video(test_url)
        
        if video_path:
            print(f"\n✅ SUCCESS! Video downloaded to: {video_path}")
            
            # Print file size to confirm it actually downloaded data
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"File size: {size_mb:.2f} MB")
        else:
            print("\n❌ FAILED! Video path was None.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nIf you see a 'Sign in to confirm you're not a bot' error:")
        print("1. Make sure you exported cookies for youtube.com")
        print("2. Ensure cookies.txt is in the ZoomAutomation folder")
        print("3. Try updating yt-dlp: pip install -U yt-dlp")

if __name__ == "__main__":
    test()
