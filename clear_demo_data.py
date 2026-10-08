#!/usr/bin/env python3
"""
Clear Demo Data Script
Removes all test/demo recordings from the database and Google Sheets
while preserving system configuration and credentials.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src import config
from src.drive_client import DriveClient
from src.sheets_integration import SheetManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ClearDemoData")

def clear_database():
    """Clear demo data from SQLite database"""
    try:
        db_path = config.DATA_DIR / "vong_v2.db"
        if not db_path.exists():
            logger.info("No database file found. Skipping database cleanup.")
            return
        
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM recordings")
        before_count = cursor.fetchone()[0]
        
        # Clear all recordings
        cursor.execute("DELETE FROM recordings")
        conn.commit()
        
        logger.info(f"✓ Cleared {before_count} recordings from database")
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")

def clear_google_sheets():
    """Clear all data rows from Google Sheets (keep headers)"""
    try:
        # Initialize Drive client
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH,
            service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE
        )
        
        # Initialize Sheet Manager
        sheet_manager = SheetManager(drive.credentials)
        
        # Get all values to count rows
        all_values = sheet_manager.main_tab.get_all_values()
        if len(all_values) <= 1:
            logger.info("Google Sheets already clean (only headers present)")
            return
        
        row_count = len(all_values) - 1  # Exclude header
        
        # Clear all rows except header
        if row_count > 0:
            sheet_manager.main_tab.delete_rows(2, len(all_values))
            logger.info(f"✓ Cleared {row_count} rows from Google Sheets")
        
        # Clear system logs tab if it exists
        try:
            if sheet_manager.logs_tab:
                logs_values = sheet_manager.logs_tab.get_all_values()
                if len(logs_values) > 1:
                    sheet_manager.logs_tab.delete_rows(2, len(logs_values))
                    logger.info(f"✓ Cleared {len(logs_values) - 1} log entries")
        except:
            pass
            
    except Exception as e:
        logger.error(f"Failed to clear Google Sheets: {e}")
        import traceback
        traceback.print_exc()

def clear_local_downloads():
    """Clear downloaded files from downloads directory"""
    try:
        download_dir = config.DOWNLOAD_DIR
        if not download_dir.exists():
            logger.info("Downloads directory doesn't exist. Skipping.")
            return
        
        files = list(download_dir.glob("*"))
        count = 0
        for file in files:
            if file.is_file():
                file.unlink()
                count += 1
        
        if count > 0:
            logger.info(f"✓ Cleared {count} files from downloads directory")
        else:
            logger.info("Downloads directory already clean")
            
    except Exception as e:
        logger.error(f"Failed to clear downloads: {e}")

def main():
    logger.info("=" * 60)
    logger.info("YTZ Automation - Clear Demo Data")
    logger.info("=" * 60)
    logger.info("")
    
    # Confirmation
    print("\n⚠️  WARNING: This will delete all recordings and logs!")
    print("   - Database: All recording entries")
    print("   - Google Sheets: All data rows (keeps headers)")
    print("   - Downloads: All temporary files")
    print("")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm != "YES":
        logger.info("Cancelled by user")
        return
    
    logger.info("")
    logger.info("Starting cleanup...")
    logger.info("")
    
    # Create backup timestamp
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Backup timestamp: {backup_time}")
    
    # Execute cleanup
    clear_database()
    clear_google_sheets()
    clear_local_downloads()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Cleanup Complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("System is now ready for fresh data.")
    logger.info("Run the main automation to start processing new recordings.")

if __name__ == "__main__":
    main()
