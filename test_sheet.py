import logging
import gspread
from src import config
from src.drive_client import DriveClient

def test_sheet_write():
    print("Testing Sheet Write Access...")
    
    # Auth
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        # Defaults use env vars now
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
        token_path=config.DRIVE_TOKEN_PATH
    )
    
    gc = gspread.authorize(drive.credentials)
    sh = gc.open_by_key(config.GOOGLE_SHEET_ID)
    ws = sh.sheet1
    
    # Append a test row
    test_row = ["TEST_DATE", "TEST_ID", "TEST_WRITE", "TEST_TEAM", "", "", "", "", "TEST_STATUS", "", ""]
    ws.append_row(test_row)
    print("✅ Appended Test Row.")
    
    # Verify and Delete
    rows = ws.get_all_values()
    last_row = rows[-1]
    if last_row[1] == "TEST_ID":
        # Delete the last row
        ws.delete_rows(len(rows))
        print("✅ Deleted Test Row.")
    else:
        print("❌ Could not find the test row to delete.")

if __name__ == "__main__":
    test_sheet_write()
