import os
import sys
sys.path.insert(0, '.')
from src.drive_client import DriveClient

def main():
    print("This script will open your browser to log into Google and grant Google Drive access.")
    print("It will save a User OAuth token to 'secrets/token_drive.json' to fix the 15GB Quota Error.")
    print("=" * 80)
    
    # This automatically triggers the OAuth flow and saves the token
    drive = DriveClient(
        auth_mode='user',
        token_path='secrets/token_drive.json',
        client_secret_path='secrets/client_secret.json'
    )
    
    print("\n" + "=" * 80)
    print("SUCCESS! The 'secrets/token_drive.json' file has been created successfully!")
    print("Now simply SCP this file to your production server using the following command:")
    print("scp secrets/token_drive.json root@139.84.133.1:/root/ytz-automation/secrets/token_drive.json")

if __name__ == '__main__':
    main()
