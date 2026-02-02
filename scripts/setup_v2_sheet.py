
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from src import config
from src.drive_client import DriveClient
from src.sheet_schema_v2 import SheetSchemaV2

def setup_v2_sheet():
    print("Initializing Google Sheets V2 Setup...")
    
    # Authenticate
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
        token_path=config.DRIVE_TOKEN_PATH
    )
    gc = gspread.authorize(drive.credentials)
    
    try:
        sh = gc.open_by_key(config.GOOGLE_SHEET_ID)
        print(f"Connected to Sheet: {sh.title}")
    except Exception as e:
        print(f"Error accessing sheet: {e}")
        return

    # 1. Setup Settings Tab
    try:
        ws_settings = sh.worksheet(SheetSchemaV2.TAB_SETTINGS)
    except gspread.WorksheetNotFound:
        ws_settings = sh.add_worksheet(title=SheetSchemaV2.TAB_SETTINGS, rows=10, cols=2)
    
    # Default State
    ws_settings.update(range_name='A1:B2', values=[
        [SheetSchemaV2.KEY_COMMAND, SheetSchemaV2.CMD_IDLE],
        [SheetSchemaV2.KEY_LAST_RUN, "Never"]
    ])
    print("✅ Settings Tab Configured")

    # 2. Setup System Logs Tab
    try:
        ws_logs = sh.worksheet(SheetSchemaV2.TAB_LOGS)
    except gspread.WorksheetNotFound:
        ws_logs = sh.add_worksheet(title=SheetSchemaV2.TAB_LOGS, rows=50, cols=2)
    ws_logs.update(range_name='A1:B1', values=[["Timestamp", "Message"]])
    print("✅ System Logs Tab Configured")

    # 3. Setup Dashboard Tab
    try:
        ws_dash = sh.worksheet(SheetSchemaV2.TAB_DASHBOARD)
    except gspread.WorksheetNotFound:
        ws_dash = sh.add_worksheet(title=SheetSchemaV2.TAB_DASHBOARD, rows=10, cols=2)
    ws_dash.update(range_name='A1:B4', values=[
        ["Metric", "Value"],
        ["Total Processed", 0],
        ["Storage Saved (Est)", "0 GB"],
        ["Last Sync", "-"]
    ])
    print("✅ Dashboard Tab Configured")

    # 4. Setup Main Tab (Rename old one if exists or create new)
    try:
        ws_main = sh.worksheet(SheetSchemaV2.TAB_MAIN)
        print("Main tab exists. Updating headers if needed...")
        current_headers = ws_main.row_values(1)
        if current_headers != SheetSchemaV2.HEADERS_MAIN:
            print("⚠️ Headers Update Required. Appending new columns...")
            ws_main.update(range_name='A1:I1', values=[SheetSchemaV2.HEADERS_MAIN])
            
    except gspread.WorksheetNotFound:
        print("Creating Main Tab...")
        ws_main = sh.add_worksheet(title=SheetSchemaV2.TAB_MAIN, rows=100, cols=10)
        ws_main.update(range_name='A1:I1', values=[SheetSchemaV2.HEADERS_MAIN])

    # Validation & Formatting (Basic)
    # Skipped programmatic validation to avoid dependency issues. 
    # Please set Dropdown for Column F (Status) manually in Sheets:
    # Data > Data Validation > Criteria: Dropdown (PENDING, PROCESSING, COMPLETED, ERROR)
    
    print("✅ Main Tab Configured")
    print("\nSetup Complete! The Sheet is ready for V2 Automation.")

if __name__ == "__main__":
    setup_v2_sheet()
