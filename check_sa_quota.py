from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KEY_FILE = BASE_DIR / 'secrets/service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def check_quota():
    if not KEY_FILE.exists():
        print(f"Error: {KEY_FILE} not found!")
        return

    try:
        creds = service_account.Credentials.from_service_account_file(str(KEY_FILE), scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        about = service.about().get(fields="storageQuota,user").execute()
        
        email = about['user']['emailAddress']
        quota = about['storageQuota']
        limit = int(quota.get('limit', 0))
        usage = int(quota.get('usage', 0))
        
        print(f"Service Account Email: {email}")
        if limit > 0:
            print(f"Storage: {usage / (1024**3):.2f} GB / {limit / (1024**3):.2f} GB")
            print(f"Percent Used: {usage/limit*100:.1f}%")
        else:
            print("Storage: No Limit (or 0GB quota if hitting errors).")
            print("Note: 'limit' key might be missing for unlimited or 0.")
            print(f"Usage: {usage / (1024**3):.2f} GB")
            
        print(f"Quota Details: {quota}")

    except Exception as e:
        print(f"Error checking quota: {e}")

if __name__ == "__main__":
    check_quota()
