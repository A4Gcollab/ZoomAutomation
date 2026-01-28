import logging
import os
import sys
import json
from dotenv import load_dotenv
from src.drive_client import DriveClient
from src import config
from googleapiclient.errors import HttpError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("DriveVerify")

def verify_drive_access():
    load_dotenv()
    
    # 1. Load Config
    # Hardcode path to match config.py logic
    service_acc = "secrets/service_account.json"
    root_id = os.getenv("DRIVE_ROOT_FOLDER_ID")
    transcripts_id = os.getenv("TRANSCRIPTS_FOLDER_ID")
    
    # Load Playlists
    with open("config/playlists.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n" + "="*60)
    print("GOOGLE DRIVE VERIFICATION")
    print("="*60)
    
    if not os.path.exists(config.SECRETS_DIR / "client_secret.json") and config.DRIVE_AUTH_MODE == 'user':
         logger.error(f"Missing Client Secret File for User Auth")
         return
         
    try:
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE,
            token_path=config.DRIVE_TOKEN_PATH,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH
        )
    except Exception as e:
        logger.error(f"Failed to auth with Drive: {e}")
        return

    # 2. Check Root Folder
    print(f"\nChecking Video Root Folder (ID: {root_id})...")
    if check_folder(drive, root_id, "Video Root"):
        print(" [OK] Video Root is ACCESSIBLE and WRITABLE.")
    else:
        print(" [FAIL] Video Root Failed Checks.")
        
    # 3. Check Transcripts Folder
    if transcripts_id:
        print(f"\nChecking Transcripts Folder (ID: {transcripts_id})...")
        if check_folder(drive, transcripts_id, "Transcripts"):
             print(" [OK] Transcripts Folder is ACCESSIBLE and WRITABLE.")
        else:
             print(" [FAIL] Transcripts Folder Failed Checks.")
    else:
        print("\nChecking Transcripts Folder...")
        print(" [WARN] No explicit TRANSCRIPTS_FOLDER_ID set. System will look for 'Transcripts' inside Root.")

    # 4. Deep Check: Verify Subfolders based on Config
    print(f"\nScanning for {len(data.get('playlists', []))} expected subfolders...")
    
    found_vid = 0
    found_ts = 0
    
    for pl in data.get('playlists', []):
        name = pl.get('playlist_name')
        if not name: continue
        
        print(f"\n  Category: '{name}'")
        
        # Check in Video Root
        vid_sub = drive.find_folder(name, root_id)
        if vid_sub:
            print(f"    - Video Subfolder: FOUND [OK]")
            if verify_write(drive, vid_sub, f"Vid-{name}"):
                print(f"      -> Writable: YES")
                found_vid += 1
            else:
                print(f"      -> Writable: NO [FAIL]")
        else:
            print(f"    - Video Subfolder: MISSING (Will be auto-created)")

        # Check in Transcripts Root
        if transcripts_id:
            ts_sub = drive.find_folder(name, transcripts_id)
            if ts_sub:
                print(f"    - Transcript Subfolder: FOUND [OK]")
                if verify_write(drive, ts_sub, f"Ts-{name}"):
                    print(f"      -> Writable: YES")
                    found_ts += 1
                else:
                    print(f"      -> Writable: NO [FAIL]")
            else:
                print(f"    - Transcript Subfolder: MISSING (Will be auto-created)")

    print("\n" + "="*60)

def verify_write(drive, folder_id, label):
    try:
        test_folder = drive.create_folder(f"_test_{label}", folder_id)
        drive.service.files().delete(fileId=test_folder).execute()
        return True
    except Exception:
        return False

def check_folder(drive, folder_id, label):
    if not folder_id:
        logger.error(f"{label}: No ID provided in configuration.")
        return False
        
    # A. Check Existence
    try:
        f = drive.service.files().get(fileId=folder_id, fields="id, name, capabilities").execute()
        print(f"   Found Folder: '{f.get('name')}'")
        
        # B. Check Permissions
        caps = f.get('capabilities', {})
        can_edit = caps.get('canAddChildren') or caps.get('canEdit')
        
        if not can_edit:
            logger.error(f"   [FAIL] Service Account cannot write to this folder. Please share as 'Editor'.")
            return False
            
        # C. Write Test
        return verify_write(drive, folder_id, label)
            
    except HttpError as e:
        if e.resp.status == 404:
            logger.error(f"   [FAIL] Folder ID not found (404). Check if ID is correct and shared.")
        else:
            logger.error(f"   [FAIL] API Error: {e}")
        return False
    except Exception as e:
        logger.error(f"   [FAIL] Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    verify_drive_access()
