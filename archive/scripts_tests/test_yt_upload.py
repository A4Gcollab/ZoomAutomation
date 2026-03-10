"""
==========================================================================
  STANDALONE YouTube Quota Test Script
  ------------------------------------
  Purpose: Test how many videos the vong.meetings2 account can upload
           before hitting YouTube API quota limits.

  SAFETY: This script is 100% standalone.  It does NOT import from src/,
          does NOT touch the database, does NOT modify playlists.json,
          and does NOT affect the main automation pipeline in any way.

  Usage:
    Step 1 (one-time):  python test_yt_upload.py --setup
                        This opens a browser for Google login.
                        Log in with vong.meetings2@gmail.com

    Step 2 (the test):  python test_yt_upload.py --test
                        This uploads small test videos and counts how
                        many succeed before quota is hit.

    Step 3 (cleanup):   python test_yt_upload.py --cleanup
                        This deletes all test videos from YouTube.
==========================================================================
"""

import os
import sys
import pickle
import time
import struct
import argparse
import logging
from datetime import datetime
from pathlib import Path

# --------------- CONFIGURATION ---------------
# All test files go in this isolated folder
TEST_DIR = Path(__file__).parent / "test_quota_workspace"
TEST_TOKEN_PATH = TEST_DIR / "test_token.json"
TEST_VIDEO_DIR = TEST_DIR / "test_videos"
TEST_LOG_FILE = TEST_DIR / "quota_test_results.log"
UPLOADED_IDS_FILE = TEST_DIR / "uploaded_video_ids.txt"

# How many uploads to attempt (set higher than 6 to test the limit)
MAX_UPLOAD_ATTEMPTS = 10

# YouTube API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("QuotaTest")


def ensure_dirs():
    """Create test workspace directories."""
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    TEST_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def find_client_secret():
    """
    Look for the client_secret.json in common locations.
    The user may need to provide this.
    """
    search_paths = [
        TEST_DIR / "client_secret.json",
        Path(__file__).parent / "secrets" / "client_secret.json",
        Path(__file__).parent / "client_secret.json",
    ]
    for p in search_paths:
        if p.exists():
            return str(p)
    return None


def create_minimal_mp4(filepath, duration_seconds=1):
    """
    Create a minimal valid MP4 file (~1KB) that YouTube will accept.
    This creates a proper MP4 container with a tiny video track.
    """
    # We'll create a minimal MP4 with ftyp + moov boxes
    # This is the smallest valid MP4 YouTube will process
    import tempfile

    # Actually, the simplest approach: create a very small file
    # YouTube requires a real video, so let's make one with raw bytes
    # that form a valid (if empty/tiny) MP4 container.

    # For reliability, let's just create a small AVI-like file
    # Actually, let's just write raw bytes for a minimal valid MP4

    # Simplest: use a 1-second solid color video via ffmpeg if available
    # Fallback: create a minimal binary MP4

    try:
        import subprocess
        # Try ffmpeg first (most reliable)
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            # ffmpeg is available - create a tiny 1-second black video
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=black:s=160x120:d={duration_seconds}",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "51",  # Lowest quality = smallest file
                "-pix_fmt", "yuv420p",
                filepath
            ], capture_output=True, text=True, check=True)
            logger.info(f"Created test video: {filepath} ({os.path.getsize(filepath)} bytes)")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback: try with imageio/moviepy if installed
    try:
        import numpy as np
        import imageio

        # Create a 1-second video with a single black frame
        writer = imageio.get_writer(filepath, fps=1)
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        for _ in range(duration_seconds):
            writer.append_data(frame)
        writer.close()
        logger.info(f"Created test video (imageio): {filepath} ({os.path.getsize(filepath)} bytes)")
        return True
    except ImportError:
        pass

    logger.error("Cannot create test video. Please install ffmpeg or run: pip install imageio imageio-ffmpeg numpy")
    logger.error("  Windows: winget install ffmpeg")
    logger.error("  Or download from: https://ffmpeg.org/download.html")
    return False


def setup_auth():
    """
    Step 1: Authenticate with the vong.meetings2 YouTube account.
    Uses run_local_server with browser auto-open disabled so user can paste URL into Chrome.
    """
    ensure_dirs()

    client_secret = find_client_secret()
    if not client_secret:
        logger.error("client_secret.json NOT FOUND!")
        logger.error("Place it in: " + str(TEST_DIR / "client_secret.json"))
        return False

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        logger.info("=" * 60)
        logger.info("YOUTUBE AUTH SETUP")
        logger.info("=" * 60)
        logger.info(f"Using client secret: {client_secret}")
        logger.info("")
        logger.info("A URL will appear below.")
        logger.info("COPY it and paste into CHROME (where vong.meetings2 is logged in).")
        logger.info("After approving, you'll see 'Auth complete' in the browser.")
        logger.info("=" * 60)

        flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
        credentials = flow.run_local_server(
            port=8090,
            open_browser=True,
            prompt='consent',
            success_message='Auth complete! You can close this tab and return to terminal.'
        )

        _save_token(credentials)
        return True

    except Exception as e:
        logger.error(f"Auth failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _save_token(credentials):
    """Save credentials to the test token file."""
    with open(TEST_TOKEN_PATH, 'wb') as f:
        pickle.dump(credentials, f)
    logger.info("")
    logger.info("AUTH SUCCESS!")
    logger.info(f"Token saved to: {TEST_TOKEN_PATH}")
    logger.info("")
    logger.info("Now run:  python test_yt_upload.py --test --count 7")


def get_youtube_service():
    """Load saved credentials and build YouTube API service."""
    if not TEST_TOKEN_PATH.exists():
        logger.error("No token found. Run --setup first.")
        return None

    with open(TEST_TOKEN_PATH, 'rb') as f:
        credentials = pickle.load(f)

    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        from google.auth.transport.requests import Request
        credentials.refresh(Request())
        with open(TEST_TOKEN_PATH, 'wb') as f:
            pickle.dump(credentials, f)

    import googleapiclient.discovery
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


def run_quota_test(upload_count=MAX_UPLOAD_ATTEMPTS):
    """
    Step 2: Upload test videos one by one and count successes.
    This is the main test to verify the CEO's claim.
    """
    ensure_dirs()

    youtube = get_youtube_service()
    if not youtube:
        return

    # Add file handler for logging results
    file_handler = logging.FileHandler(TEST_LOG_FILE, mode='w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    logger.info("=" * 70)
    logger.info("  YOUTUBE QUOTA TEST")
    logger.info(f"  Account: vong.meetings2@gmail.com")
    logger.info(f"  Testing: {upload_count} video uploads")
    logger.info(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    # First, check which channel we're authenticated as
    try:
        ch_request = youtube.channels().list(part="snippet", mine=True)
        ch_response = ch_request.execute()
        if ch_response.get('items'):
            channel = ch_response['items'][0]
            logger.info(f"  Channel: {channel['snippet']['title']}")
            logger.info(f"  Channel ID: {channel['id']}")
        else:
            logger.warning("  Could not determine channel info")
    except Exception as e:
        logger.warning(f"  Channel info check failed: {e}")

    logger.info("")

    # Create test videos
    logger.info("Creating test videos...")
    video_paths = []
    for i in range(1, upload_count + 1):
        video_path = str(TEST_VIDEO_DIR / f"quota_test_{i}.mp4")
        if not os.path.exists(video_path):
            if not create_minimal_mp4(video_path, duration_seconds=2):
                logger.error(f"Failed to create test video {i}. Aborting.")
                return
        video_paths.append(video_path)

    logger.info(f"  {len(video_paths)} test videos ready")
    logger.info("")

    # Upload one by one
    successful = 0
    failed = 0
    quota_hit = False
    uploaded_ids = []

    from googleapiclient.http import MediaFileUpload

    for i, video_path in enumerate(video_paths, 1):
        logger.info(f"--- Upload {i}/{upload_count} ---")

        try:
            body = {
                "snippet": {
                    "title": f"[QUOTA TEST {i}] Delete Me - {datetime.now().strftime('%H:%M:%S')}",
                    "description": "Automated quota test. Safe to delete.",
                    "tags": ["test", "quota-test", "delete-me"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "private"  # PRIVATE so nobody sees these
                }
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"  Progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            successful += 1
            uploaded_ids.append(video_id)

            logger.info(f"  SUCCESS! Video ID: {video_id}")
            logger.info(f"  Score: {successful} uploaded, {failed} failed")

            # Small delay between uploads to be respectful
            if i < MAX_UPLOAD_ATTEMPTS:
                logger.info(f"  Waiting 5 seconds before next upload...")
                time.sleep(5)

        except Exception as e:
            error_str = str(e)
            failed += 1

            if 'quotaExceeded' in error_str or 'dailyLimitExceeded' in error_str:
                quota_hit = True
                logger.error(f"  QUOTA HIT after {successful} successful uploads!")
                logger.error(f"  Error: {error_str[:200]}")
                break
            else:
                logger.error(f"  FAILED (non-quota error): {error_str[:200]}")
                # Continue trying - might be a transient error

    # Save uploaded video IDs for cleanup
    with open(UPLOADED_IDS_FILE, 'w') as f:
        for vid in uploaded_ids:
            f.write(f"{vid}\n")

    # Print results
    logger.info("")
    logger.info("=" * 70)
    logger.info("  RESULTS")
    logger.info("=" * 70)
    logger.info(f"  Total Attempted:  {successful + failed}")
    logger.info(f"  Successful:       {successful}")
    logger.info(f"  Failed:           {failed}")
    logger.info(f"  Quota Hit:        {'YES' if quota_hit else 'NO'}")
    logger.info("")

    if quota_hit:
        logger.info("  CONCLUSION: This account has the STANDARD quota (10,000 units/day).")
        logger.info(f"              Maximum ~{successful} video uploads before quota is exhausted.")
        logger.info("              The CEO's claim of 'no limits' is INCORRECT for this account.")
    elif successful >= 7:
        logger.info("  CONCLUSION: This account uploaded MORE than 6 videos successfully!")
        logger.info("              The CEO may be correct - this project might have elevated quota.")
        logger.info("              Check: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas")
    else:
        logger.info("  CONCLUSION: Could not determine quota limit (errors were not quota-related).")

    logger.info("")
    logger.info(f"  Full log saved to: {TEST_LOG_FILE}")
    logger.info(f"  Uploaded video IDs: {UPLOADED_IDS_FILE}")
    logger.info("")
    logger.info("  To clean up test videos from YouTube, run:")
    logger.info("    python test_yt_upload.py --cleanup")
    logger.info("=" * 70)


def cleanup_test_videos():
    """
    Step 3: Delete all uploaded test videos from YouTube.
    """
    youtube = get_youtube_service()
    if not youtube:
        return

    if not UPLOADED_IDS_FILE.exists():
        logger.info("No uploaded video IDs found. Nothing to clean up.")
        return

    with open(UPLOADED_IDS_FILE, 'r') as f:
        video_ids = [line.strip() for line in f if line.strip()]

    if not video_ids:
        logger.info("No video IDs to delete.")
        return

    logger.info(f"Deleting {len(video_ids)} test videos from YouTube...")

    deleted = 0
    for vid in video_ids:
        try:
            youtube.videos().delete(id=vid).execute()
            logger.info(f"  Deleted: {vid}")
            deleted += 1
        except Exception as e:
            logger.warning(f"  Failed to delete {vid}: {e}")

    logger.info(f"Deleted {deleted}/{len(video_ids)} videos.")

    # Clean up local files
    logger.info("Cleaning up local test files...")
    import shutil
    if TEST_VIDEO_DIR.exists():
        shutil.rmtree(TEST_VIDEO_DIR)
        logger.info(f"  Removed {TEST_VIDEO_DIR}")

    # Clear the IDs file
    UPLOADED_IDS_FILE.unlink(missing_ok=True)
    logger.info("Cleanup complete!")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Quota Test - Test how many videos can be uploaded",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Steps:
  1. python test_yt_upload.py --setup     (login with vong.meetings2@gmail.com)
  2. python test_yt_upload.py --test      (upload test videos, count successes)
  3. python test_yt_upload.py --cleanup   (delete test videos from YouTube)
        """
    )
    parser.add_argument('--setup', action='store_true', help='Authenticate with YouTube')
    parser.add_argument('--test', action='store_true', help='Run the upload quota test')
    parser.add_argument('--cleanup', action='store_true', help='Delete test videos from YouTube')
    parser.add_argument('--count', type=int, default=MAX_UPLOAD_ATTEMPTS,
                        help=f'Number of uploads to attempt (default: {MAX_UPLOAD_ATTEMPTS})')

    args = parser.parse_args()

    if args.setup:
        setup_auth()
    elif args.test:
        run_quota_test(upload_count=args.count)
    elif args.cleanup:
        cleanup_test_videos()
    else:
        parser.print_help()
        print("\nStart with: python test_yt_upload.py --setup")


if __name__ == "__main__":
    main()

