import os
import sys
import logging
import gspread
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import config

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SetupSheet")

def setup_sheet_structure():
    """
    Initialize the Google Sheet with new tabs for the Sheet-Driven Architecture.
    Tabs: Settings, System_Logs, Dashboard
    """
    if not os.path.exists(config.DRIVE_SERVICE_ACCOUNT_FILE):
        logger.error("Service Account file missing. Cannot connect to Sheets.")
        return

    try:
        # Connect to Sheet
        gc = gspread.service_account(filename=config.DRIVE_SERVICE_ACCOUNT_FILE)
        sh = gc.open_by_key(config.GOOGLE_SHEET_ID)
        
        logger.info(f"Connected to Sheet: {sh.title}")
        
        existing_titles = [ws.title for ws in sh.worksheets()]
        
        # --- 1. SETTINGS TAB ---
        if "Settings" not in existing_titles:
            logger.info("Creating 'Settings' tab...")
            ws = sh.add_worksheet(title="Settings", rows=50, cols=4)
            ws.append_row(["Key", "Value", "Description"])
            ws.format("A1:C1", {"textFormat": {"bold": True}})
            
            # Default Settings
            defaults = [
                ["CHECK_INTERVAL", "3600", "Seconds to wait between checks"],
                ["YOUTUBE_PRIVACY", "unlisted", "public, private, or unlisted"],
                ["ENABLE_AUTO_DELETE", "TRUE", "Auto-delete from Zoom after safety check"],
                ["DELETE_DELAY_DAYS", "7", "Days to keep in Zoom after upload"],
                ["DRIVE_DEFAULT_CATEGORY", "General", "Default drive folder name"],
                ["ENABLE_DRIVE_UPLOAD", "TRUE", "Upload to Google Drive"],
                ["ENABLE_SHEETS_LOGGING", "TRUE", "Write logs to System_Logs tab"]
            ]
            ws.append_rows(defaults)
            logger.info("'Settings' tab populated.")
        else:
            logger.info("'Settings' tab already exists.")

        # --- 2. SYSTEM_LOGS TAB ---
        if "System_Logs" not in existing_titles:
            logger.info("Creating 'System_Logs' tab...")
            ws = sh.add_worksheet(title="System_Logs", rows=1000, cols=3)
            ws.append_row(["Timestamp", "Level", "Message"])
            ws.format("A1:C1", {"textFormat": {"bold": True}})
            # Freeze header
            ws.freeze(rows=1)
            logger.info("'System_Logs' tab created.")
        else:
            logger.info("'System_Logs' tab already exists.")

        # --- 3. DASHBOARD TAB ---
        if "Dashboard" not in existing_titles:
            logger.info("Creating 'Dashboard' tab...")
            ws = sh.add_worksheet(title="Dashboard", rows=20, cols=5)
            ws.append_row(["Metric", "Count", "Last Updated"])
            ws.format("A1:C1", {"textFormat": {"bold": True}})
            
            # Initial Metrics
            metrics = [
                ["Total Processed", "=COUNTIF('Sheet1'!I:I, \"COMPLETED\")", ""],
                ["Pending Approval", "=COUNTIF('Sheet1'!I:I, \"PENDING\")", ""],
                ["Errors", "=COUNTIF('Sheet1'!I:I, \"ERROR\")", ""],
                ["Last Run", "Waiting...", ""]
            ]
            ws.append_rows(metrics)
            logger.info("'Dashboard' tab created.")
        else:
            logger.info("'Dashboard' tab already exists.")

        logger.info("Sheet Structure Setup Complete!")
        print("\n\nSUCCESS! Your Google Sheet is now ready for the new architecture.")
        print("Go check the 'Settings' tab in your sheet.")

    except Exception as e:
        logger.error(f"Setup Failed: {e}")

if __name__ == "__main__":
    setup_sheet_structure()
