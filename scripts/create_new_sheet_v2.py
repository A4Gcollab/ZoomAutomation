
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from src import config
from src.drive_client import DriveClient

def create_new_sheet():
    print("Creating NEW Google Sheet for V2 Automation...")
    
    # Authenticate
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
        token_path=config.DRIVE_TOKEN_PATH
    )
    gc = gspread.authorize(drive.credentials)
    
    # Create Sheet
    title = "VONG Automation V2 Command Center"
    try:
        sh = gc.create(title)
        new_id = sh.id
        print(f"✅ Created New Sheet: '{title}'")
        print(f"🆔 ID: {new_id}")
        print(f"🔗 Link: {sh.url}")
        
        # Update .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        with open(env_path, 'r') as f:
            content = f.read()
            
        # Replace ID
        new_content = re.sub(
            r'GOOGLE_SHEET_ID=.*', 
            f'GOOGLE_SHEET_ID={new_id}', 
            content
        )
        
        with open(env_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Updated .env with new Sheet ID.")
        return sh.url
        
    except Exception as e:
        print(f"❌ Failed to create sheet: {e}")
        return None

if __name__ == "__main__":
    create_new_sheet()
