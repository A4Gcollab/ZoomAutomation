import os
import shutil
import gspread
from src.drive_client import DriveClient
from src import config
from pathlib import Path

def reset_system():
    print("WARNING: This will clear the Google Sheet data and local DB.")
    
    # 1. Clear Google Sheet
    try:
        print("Connecting to Google Sheets...")
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH
        )
        gc = gspread.authorize(drive.credentials)
        sh = gc.open_by_key(config.GOOGLE_SHEET_ID)
        ws = sh.sheet1
        
        # Clear Data (Keep Headers A1:L1)
        print("Clearing Sheet rows 2-500...")
        ws.batch_clear(["A2:L500"])
        print(" [OK] Sheet Cleared.")
        
    except Exception as e:
        print(f" [!] Failed to clear sheet: {e}")

    # 2. Reset DB
    db_path = config.DATA_DIR / config.DB_PATH
    if db_path.exists():
        try:
            os.remove(db_path)
            print(f" [OK] Deleted local DB: {db_path}")
        except Exception as e:
            print(f" [!] Failed to delete DB: {e}")
    else:
        print(" [OK] No DB file found (Clean start).")

    # 3. Clear Downloads (Optional)
    downloads = config.DOWNLOAD_DIR
    if downloads.exists():
        print("Clearing downloads folder...")
        for item in downloads.iterdir():
            try:
                if item.is_file() and item.name != '.gitkeep':
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                pass
        print(" [OK] Downloads cleared.")

    # 4. Remove Lock File
    lock_file = config.DATA_DIR / "app.lock"
    if lock_file.exists():
         try:
            lock_file.unlink()
            print(" [OK] Lock file removed.")
         except: pass

    print("\nSYSTEM RESET COMPLETE. Ready for fresh test.")

if __name__ == "__main__":
    reset_system()
