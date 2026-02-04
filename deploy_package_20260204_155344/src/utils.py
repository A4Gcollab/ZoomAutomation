import re
from datetime import datetime

def sanitize_filename(name):
    """Sanitize string to be safe for filenames."""
    # Replace invalid chars with SPACE instead of underscore per user request
    # Also collapse multiple spaces
    cleaned = re.sub(r'[<>:"/\\|?*]', ' ', name)
    return re.sub(r'\s+', ' ', cleaned).strip()

def parse_zoom_start_time(start_time_str):
    """
    Parse Zoom start_time string.
    Expected format ex: '2026-01-08T10:00:00Z'
    Returns datetime object.
    """
    try:
        return datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        # Handle cases where Z might be missing or different format
        return datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))

def generate_names(topic, start_time_str):
    """
    Generate deterministic file names and titles based on rules.
    
    Input:
        topic: "Tech Project Meeting"
        start_time_str: "2026-01-08T10:00:00Z"
        
    Output keys:
        video_filename: "20260108_Tech_Project_Meeting.mp4"
        transcript_filename: "20260108_Tech_Project_Meeting_transcript.txt"
        youtube_title: "Tech Project Meeting | 08 Jan 2026"
        folder_date: "2026-01-08"
    """
    dt = parse_zoom_start_time(start_time_str)
    date_str = dt.strftime("%Y%m%d")      # 20260108
    readable_date = dt.strftime("%d %b %Y") # 08 Jan 2026
    
    # Clean topic for usage in filename
    # User requested: "just the name with spaces", no underscores
    # Sanitize keeps spaces, but removes invalid chars
    safe_topic = sanitize_filename(topic)
    
    # Format: "20260115 Meeting Name.mp4"
    video_filename = f"{date_str} {safe_topic}.mp4"
    video_name_clean = f"{date_str} {safe_topic}"
    transcript_filename = f"{date_str} {safe_topic}_transcript.txt"
    youtube_title = video_name_clean  # User requested: "20260114 tech systems..." format
    
    return {
        "video_filename": video_filename,
        "video_name_clean": video_name_clean,
        "transcript_filename": transcript_filename,
        "youtube_title": youtube_title,
        "date_obj": dt
    }

import time
import functools
import logging
import random

def retry_with_backoff(retries=3, initial_delay=2, backoff_factor=2):
    """
    Retry Decorator with Exponential Backoff.
    Waits: 2s, 4s, 8s...
    """
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            delay = initial_delay
            last_exception = None
            
            for i in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if i == retries:
                        break
                    
                    wait = delay + random.uniform(0, 1) # Add jitter
                    logger.warning(f"Error in {func.__name__}: {e}. Retrying in {wait:.1f}s...")
                    time.sleep(wait)
                    delay *= backoff_factor
            
            logger.error(f"Failed {func.__name__} after {retries} retries.")
            raise last_exception
        return wrapper_retry
    return decorator_retry
