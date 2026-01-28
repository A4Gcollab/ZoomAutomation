import logging
import gspread
from src.sheets_integration import SheetManager
from src.drive_client import DriveClient
from src import config

logging.basicConfig(level=logging.INFO)

def test_integration():
    print("Testing SheetManager Integration...")
    
    # Auth
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
        token_path=config.DRIVE_TOKEN_PATH
    )
    
    # Init Manager
    print(f"Using Sheet ID: {config.GOOGLE_SHEET_ID}")
    sm = SheetManager(drive.credentials)
    
    # Test 1: Sync (Append)
    dummy_rec = [{
        'id': '999999',
        'start_time': '2025-01-01T10:00:00Z',
        'topic': 'Integration Test',
        'play_url': 'http://test.com'
    }]
    
    print("Running sync_recordings...")
    sm.sync_recordings(dummy_rec)
    
    # Test 2: Read
    print("Running get_existing_ids...")
    ids = sm.get_existing_ids()
    if '999999' in ids:
        print("✅ Found Sync'd Recording ID")
    else:
        print("❌ ID Not Found")
        
    # Test 3: Mark Completed (this tests batch_update)
    # Find the row index
    row_idx = ids.index('999999') + 2 # +1 header, +1 1-based index ?? No.
    # ids is values[1:]. So index 0 in ids is Row 2.
    # So row_idx = 0 + 2 = 2. Correct.
    
    print(f"Marking Row {row_idx} as Completed...")
    sm.mark_completed(row_idx, "http://drive", "http://yt")
    print("✅ Mark Completed Finished")
    
    # Clean up (Optional, but good manners)
    print("Cleaning up test row...")
    sm.sheet.delete_rows(row_idx)
    print("✅ Cleanup Done")

if __name__ == "__main__":
    test_integration()
