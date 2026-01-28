import logging
import gspread
import re
from datetime import datetime
from src.drive_client import DriveClient
from src import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("FreshSheet")

def create_fresh_dashboard():
    print("\n" + "="*50)
    print("CREATING FRESH AUTOMATION DASHBOARD")
    print("="*50)
    
    try:
        # 1. Auth
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH
        )
        gc = gspread.authorize(drive.credentials)
        
        # 2. Create New Sheet
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        sheet_name = f"VONG Automation Dashboard - {timestamp}"
        
        logger.info(f"Creating Sheet: '{sheet_name}'...")
        sh = gc.create(sheet_name)
        
        # 3. Share (Make it accessible to anyone with link as editor for ease, or just user)
        # User requested flexible access.
        try:
            sh.share(None, perm_type='anyone', role='writer')
            logger.info("Sheet shared as 'Anyone with Link can Edit'")
        except Exception as share_e:
            logger.warning(f"Could not share publicly: {share_e}. Proceeding as private.")

        # 4. Setup Headers
        ws = sh.sheet1
        headers = [
            "Date", "Meeting ID", "Title", "Team", "Playlist", 
            "Drive Link", "Upload Date", "Deletion Date", "Status", 
            "Approved By", "Zoom Preview", "YouTube Link"
        ]
        
        ws.update(range_name='A1:L1', values=[headers])
        ws.format('A1:L1', {'textFormat': {'bold': True}})
        
        # Freeze header row
        ws.freeze(rows=1)
        
        # 5. Update .env
        new_id = sh.id
        env_path = config.BASE_DIR / ".env"
        
        with open(env_path, 'r') as f:
            content = f.read()
            
        if "GOOGLE_SHEET_ID=" in content:
            content = re.sub(r"GOOGLE_SHEET_ID=.*", f"GOOGLE_SHEET_ID={new_id}", content)
        else:
            content += f"\nGOOGLE_SHEET_ID={new_id}"
            
        with open(env_path, 'w') as f:
            f.write(content)
            
        print("\n" + "="*50)
        print("✅ SUCCESS! NEW SHEET READY.")
        print(f"🔗 URL: {sh.url}")
        print(f"🆔 ID:  {sh.id}")
        print("="*50)
        print("NOTE: To enable 'Auto Name Grabbing', you must still add the Apps Script manually.")
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_fresh_dashboard()
