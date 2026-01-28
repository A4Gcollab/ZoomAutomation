import gspread
from src.drive_client import DriveClient
from src import config

def clean_rules():
    print("Initializing Rule Cleanup...")
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
        token_path=config.DRIVE_TOKEN_PATH
    )
    gc = gspread.authorize(drive.credentials)
    sh = gc.open_by_key(config.GOOGLE_SHEET_ID)
    ws = sh.sheet1
    
    print(f"Target Sheet: {ws.title}")
    
    # Construct Request to Clear Validation for Col J (Index 9)
    # Actually, let's clear validation for the WHOLE sheet just to be safe, 
    # then re-apply Status/Playlist validation via setup_sheet.py
    # But user might want to keep Status/Playlist.
    # Let's target Col J specifically.
    
    requests = [{
        "setDataValidation": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": 1, # Skip header
                "startColumnIndex": 9, # Col J
                "endColumnIndex": 10
            },
            "rule": None # Removing rule
        }
    }]
    
    try:
        sh.batch_update({"requests": requests})
        print(" [OK] Removed Data Validation from Column J (Approved By).")
    except Exception as e:
        print(f" [!] Failed to remove rules: {e}")

if __name__ == "__main__":
    clean_rules()
