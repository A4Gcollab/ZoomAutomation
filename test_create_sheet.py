import logging
import gspread
from src.drive_client import DriveClient
from src import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SheetTest")

def test_create():
    logger.info("Attempting to CREATE a new sheet...")
    try:
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH
        )
        gc = gspread.authorize(drive.credentials)
        
        sh = gc.create("API_TEST_SHEET")
        print(f"SUCCESS: Created sheet with ID {sh.id}")
        
    except Exception as e:
        logger.error(f"FAILURE: {e}")

if __name__ == "__main__":
    test_create()
