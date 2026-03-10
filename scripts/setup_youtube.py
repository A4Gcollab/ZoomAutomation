import os
import sys
import pickle
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import google_auth_oauthlib.flow
from src import config

# Clean and Init Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SetupYouTube")

def setup_youtube_auth(headless=False):
    """
    Interactive Setup for YouTube OAuth.
    Generates token file for use by the main application.
    
    Args:
        headless: If True, uses console-based flow (no browser needed).
                  Prints a URL to visit and asks for the authorization code.
    """
    client_secrets_file = config.YOUTUBE_CLIENT_SECRET_PATH
    token_file = config.YOUTUBE_TOKEN_PATH
    
    if not os.path.exists(client_secrets_file):
        logger.error(f"Client Secret file not found at: {client_secrets_file}")
        logger.info("Please download it from Google Cloud Console and place it there.")
        return

    scopes = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl"
    ]
    
    logger.info("Starting YouTube Authentication Flow...")
    
    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        
        if headless:
            # Console flow — works on headless servers
            logger.info("Running in HEADLESS mode.")
            logger.info("A URL will be printed below. Open it in any browser,")
            logger.info("approve access, and paste the authorization code back here.")
            credentials = flow.run_console()
        else:
            # Browser flow — requires local display
            logger.info("A browser window will open. Please log in and approve access.")
            credentials = flow.run_local_server(port=0)
        
        # Save credentials
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
            
        logger.info("Authentication Successful!")
        logger.info(f"Token saved to: {token_file}")
        logger.info("You can now run 'python main.py' without interaction.")
        
    except Exception as e:
        logger.error(f"Authentication Failed: {e}")

if __name__ == "__main__":
    headless = "--headless" in sys.argv
    setup_youtube_auth(headless=headless)
