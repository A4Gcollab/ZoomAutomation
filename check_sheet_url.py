import gspread
from src.drive_client import DriveClient
from src import config

def get_url():
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
        token_path=config.DRIVE_TOKEN_PATH
    )
    gc = gspread.authorize(drive.credentials)
    
    # ID from .env
    sheet_id = config.GOOGLE_SHEET_ID
    print(f"ID from Config: {sheet_id}")
    
    try:
        sh = gc.open_by_key(sheet_id)
        print(f"ACTUAL URL: {sh.url}")
        print(f"Is Public? {sh.share}") # Just prints method
    except Exception as e:
        print(f"Error accessing sheet: {e}")

if __name__ == "__main__":
    get_url()
