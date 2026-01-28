import json
import logging
import gspread
import time
from src.drive_client import DriveClient
from datetime import datetime
from src import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SheetSetup")

def setup_sheet():
    logger.info("Initializing Google Sheet Setup (CLEAN RESET)...")
    
    try:
        # 1. Auth via Drive Client (Service Account or User, based on config)
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH,
            service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE
        )
        
        # 2. Connect
        gc = gspread.authorize(drive.credentials)
        sheet_id = config.GOOGLE_SHEET_ID
        logger.info(f"Opening Sheet ID: {sheet_id}")
        
        sh = gc.open_by_key(sheet_id)
        ws = sh.sheet1
        
        # 3. WIPE SHEET
        logger.warning("Clearing entire worksheet...")
        ws.clear()
        time.sleep(1)
        
        # 4. Set Headers
        headers = [
            "Date", "Meeting ID", "Title", "Team", "Playlist", 
            "Drive Link", "Upload Date", "Deletion Date", "Status", 
            "Approved By", "Zoom Preview", "YouTube Link"
        ]
        
        logger.info("Setting Headers...")
        ws.update(range_name='A1:L1', values=[headers])
        
        # 5. Format Headers
        logger.info("Formatting Headers (Bold, Frozen)...")
        ws.format('A1:L1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        ws.freeze(rows=1)
        
        # 6. Add Data Validation (Status)
        logger.info("Adding Status Validation Rules...")
        
        # Status Rule (Col I / Index 8)
        status_rule = {
            "setDataValidation": {
                "range": {
                    "sheetId": ws.id,
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": 8,
                    "endColumnIndex": 9
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [
                            {"userEnteredValue": "PENDING"},
                            {"userEnteredValue": "APPROVED"},
                            {"userEnteredValue": "REJECTED"},
                            {"userEnteredValue": "COMPLETED"},
                            {"userEnteredValue": "ERROR"}
                        ]
                    },
                    "showCustomUi": True,
                    "strict": False
                }
            }
        }
        
        sh.batch_update({"requests": [status_rule]})
        
        # 7. Add Data Validation (Playlist)
        logger.info("Adding Playlist Validation Rules...")
        playlist_names = ["General", "Internal"]
        try:
            with open(config.PLAYLIST_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                playlist_names = [p['playlist_name'] for p in data.get('playlists', [])]
        except:
             logger.warning("Could not load playlists.json for validation.")

        playlist_rule = {
            "setDataValidation": {
                "range": {
                    "sheetId": ws.id,
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": n} for n in playlist_names]
                    },
                    "showCustomUi": True,
                    "strict": False
                }
            }
        }
        
        sh.batch_update({"requests": [playlist_rule]})
        
        # 8. Reset Settings Tab
        logger.info("Resetting Settings Tab...")
        try:
            try:
                settings_ws = sh.worksheet("Settings")
                settings_ws.clear()
            except gspread.WorksheetNotFound:
                settings_ws = sh.add_worksheet(title="Settings", rows=10, cols=3)
            
            settings_ws.update('A1:C2', [['Key', 'Value', 'Description'], ['CHECK_INTERVAL', '60', 'Seconds execution loop']])
            settings_ws.format('A1:C1', {'textFormat': {'bold': True}})
            logger.info("Settings Tab Reset (Interval=60s).")
        except Exception as set_e:
            logger.warning(f"Failed to reset Settings tab: {set_e}")
        
        logger.info("✅ Sheet Reset Complete! Ready for fresh data.")
        print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}")

    except Exception as e:
        logger.error(f"Setup Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_sheet()
