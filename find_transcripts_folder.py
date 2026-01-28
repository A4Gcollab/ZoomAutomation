from src.drive_client import DriveClient
from src import config
import os
from dotenv import load_dotenv

load_dotenv()

def find_transcripts():
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE,
        token_path=config.DRIVE_TOKEN_PATH,
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH
    )
    
    FOLDER_NAME = "Zoom Meeting Transcripts"
    print(f"Searching for folder: '{FOLDER_NAME}'...")
    
    # Search without parent restriction first to find it anywhere
    query = f"mimeType='application/vnd.google-apps.folder' and name='{FOLDER_NAME}' and trashed=false"
    results = drive.service.files().list(q=query, fields="files(id, name, parents)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = results.get('files', [])
    
    if not files:
        print("❌ Folder NOT FOUND.")
    else:
        for f in files:
            print(f"✅ FOUND: ID={f['id']}, Name='{f['name']}', Parents={f.get('parents')}")
            
if __name__ == "__main__":
    find_transcripts()
