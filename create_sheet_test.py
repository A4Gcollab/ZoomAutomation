import logging
import gspread
from src.drive_client import DriveClient
from src import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CreateSheet")

def create_new_sheet():
    logger.info("Tentative: Creating NEW Google Sheet...")
    
    try:
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH
        )
        
        gc = gspread.authorize(drive.credentials)
        
        # Create
        sh = gc.create("VONG Automation Dashboard")
        sh.share(config.DRIVE_AUTH_MODE, perm_type='user', role='writer') # Share with self, or just rely on ownership
        
        logger.info(f"SUCCESS! Created new sheet.")
        logger.info(f"URL: {sh.url}")
        logger.info(f"ID: {sh.id}")
        
    except Exception as e:
        logger.error(f"Creation Failed: {e}")

if __name__ == "__main__":
    create_new_sheet()
