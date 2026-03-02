import yt_dlp
import logging
import os

logger = logging.getLogger("Downloader")

def download_youtube_video(video_url, output_path):
    """
    Download the best MP4 format from YouTube using yt-dlp.
    This retrieves the YouTube-processed version (compressed).
    """
    ydl_opts = {
        'outtmpl': str(output_path), 
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4'
    }
    if os.path.exists('secrets/youtube_cookies.txt'):
        ydl_opts['cookiefile'] = 'secrets/youtube_cookies.txt'
    
    # If output_path exists, yt-dlp might skip or overwrite.
    # Note: 'outtmpl' in yt-dlp corresponds to the template. 
    # If we pass a full exact path "C:/foo/bar.mp4", it works.
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading from YouTube: {video_url}")
            ydl.download([video_url])
        
        # Verify file exists
        # yt-dlp might append .mp4 if not in path, but simple test usually honors outtmpl
        final_path = output_path
        if not os.path.exists(final_path):
            # Check if it added extension
            if os.path.exists(final_path + ".mp4"):
                final_path = final_path + ".mp4"
                
        if os.path.exists(final_path):
            return final_path
        else:
            raise FileNotFoundError("File not found after yt-dlp download")
            
    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}")
        raise
