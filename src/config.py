import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Standardized Directory Structure
SECRETS_DIR = BASE_DIR / "secrets"
DATA_DIR = BASE_DIR / "data"
DOWNLOAD_DIR = BASE_DIR / "downloads"

# Ensure directories exist
SECRETS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "db.json"

# Zoom Settings - Dynamic Load
ZOOM_ACCOUNTS = []
_i = 1
while True:
    acc_id = os.getenv(f"ZOOM_{_i}_ACCOUNT_ID")
    client_id = os.getenv(f"ZOOM_{_i}_CLIENT_ID")
    client_secret = os.getenv(f"ZOOM_{_i}_CLIENT_SECRET")
    
    if not (acc_id and client_id and client_secret):
        break # Stop checking when a sequence breaks
    
    ZOOM_ACCOUNTS.append({
        "account_id": acc_id,
        "client_id": client_id,
        "client_secret": client_secret,
        "name": f"Zoom Account {_i}"
    })
    _i += 1

# YouTube Settings
# Looks for 'client_secret.json' and 'token.json' in 'secrets/' folder
YOUTUBE_CLIENT_SECRET_PATH = SECRETS_DIR / "client_secret.json"
YOUTUBE_TOKEN_PATH = SECRETS_DIR / "token.json"

# Drive Settings
# Looks for 'service_account.json' in 'secrets/' folder
DRIVE_SERVICE_ACCOUNT_FILE = SECRETS_DIR / "service_account.json"
DRIVE_TOKEN_PATH = SECRETS_DIR / "token_drive.json"
DRIVE_ROOT_FOLDER_ID = os.getenv("DRIVE_ROOT_FOLDER_ID")

# Operational Settings
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 3600))

# Playlist Configuration
CONFIG_DIR = BASE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PLAYLIST_CONFIG_PATH = CONFIG_DIR / "playlists.json"

# Drive Configuration
ENABLE_DRIVE_UPLOAD = os.getenv("ENABLE_DRIVE_UPLOAD", "false").lower() == "true"
DRIVE_AUTH_MODE = os.getenv("DRIVE_AUTH_MODE", "service_account").lower() # 'user' or 'service_account'

# Google Docs Logging
GOOGLE_DOCS_LOG_ID = os.getenv("GOOGLE_DOCS_LOG_ID")
ENABLE_GOOGLE_DOCS_LOGGING = os.getenv("ENABLE_GOOGLE_DOCS_LOGGING", "false").lower() == "true"

# Drive Organization
DRIVE_USE_CATEGORY_FOLDERS = os.getenv("DRIVE_USE_CATEGORY_FOLDERS", "true").lower() == "true"
DRIVE_DEFAULT_CATEGORY = os.getenv("DRIVE_DEFAULT_CATEGORY", "General")
TRANSCRIPTS_FOLDER_NAME = os.getenv("TRANSCRIPTS_FOLDER_NAME", "Transcripts")
TRANSCRIPTS_FOLDER_ID = os.getenv("TRANSCRIPTS_FOLDER_ID")

# Deletion Settings
ENABLE_AUTO_DELETE = os.getenv("ENABLE_AUTO_DELETE", "true").lower() == "true"
DELETE_DELAY_HOURS = int(os.getenv("DELETE_DELAY_HOURS", 24))

# Upload Settings
UPLOAD_DELAY_SECONDS = int(os.getenv("UPLOAD_DELAY_SECONDS", 30))
YOUTUBE_PRIVACY_STATUS = os.getenv("YOUTUBE_PRIVACY_STATUS", "unlisted")

# Processing Settings
ENABLE_ADAPTIVE_WAIT = os.getenv("ENABLE_ADAPTIVE_WAIT", "true").lower() == "true"
MAX_YOUTUBE_PROCESSING_WAIT = int(os.getenv("MAX_YOUTUBE_PROCESSING_WAIT", 300))

# Zoho Integration
ZOHO_CLIQ_WEBHOOK_URL = os.getenv("ZOHO_CLIQ_WEBHOOK_URL")
ENABLE_ZOHO_INTEGRATION = os.getenv("ENABLE_ZOHO_INTEGRATION", "false").lower() == "true"

# Google Sheets Integration
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "17XhkOS7YW0AC7fOC51tXRoLbIOX2MkY2YxN1nJFVlwE")
ENABLE_SHEETS_INTEGRATION = os.getenv("ENABLE_SHEETS_INTEGRATION", "true").lower() == "true"

# Validation
REQUIRED_VARS = ["DRIVE_ROOT_FOLDER_ID"]

def check_config():
    missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    if not ZOOM_ACCOUNTS:
        raise ValueError("No Zoom accounts configured. Please set ZOOM_1_ACCOUNT_ID, etc.")

# --- DYNAMIC CONFIGURATION ---
class DynamicConfig:
    def __init__(self):
        self.CHECK_INTERVAL = CHECK_INTERVAL
        self.YOUTUBE_PRIVACY = YOUTUBE_PRIVACY_STATUS
        self.ENABLE_AUTO_DELETE = ENABLE_AUTO_DELETE
        self.DELETE_DELAY_DAYS = 7 # Default
        self.DRIVE_DEFAULT_CATEGORY = DRIVE_DEFAULT_CATEGORY
        self.ENABLE_DRIVE_UPLOAD = ENABLE_DRIVE_UPLOAD
        self.ENABLE_SHEETS_LOGGING = True
        
    def update(self, settings_dict):
        """Update config from a dictionary (e.g., from Sheet)."""
        if not settings_dict:
            return

        # Helper to safely cast types
        def safe_cast(key, val, type_func, default):
            try:
                return type_func(val)
            except:
                return default

        if 'CHECK_INTERVAL' in settings_dict:
            self.CHECK_INTERVAL = safe_cast('CHECK_INTERVAL', settings_dict['CHECK_INTERVAL'], int, 3600)
            
        if 'YOUTUBE_PRIVACY' in settings_dict:
            self.YOUTUBE_PRIVACY = settings_dict['YOUTUBE_PRIVACY'].strip().lower()
            
        if 'ENABLE_AUTO_DELETE' in settings_dict:
            val = settings_dict['ENABLE_AUTO_DELETE'].upper()
            self.ENABLE_AUTO_DELETE = (val == 'TRUE')
            
        if 'DELETE_DELAY_DAYS' in settings_dict:
            self.DELETE_DELAY_DAYS = safe_cast('DELETE_DELAY_DAYS', settings_dict['DELETE_DELAY_DAYS'], int, 7)
            
        if 'DRIVE_DEFAULT_CATEGORY' in settings_dict:
            self.DRIVE_DEFAULT_CATEGORY = settings_dict['DRIVE_DEFAULT_CATEGORY']
            
        if 'ENABLE_DRIVE_UPLOAD' in settings_dict:
            val = settings_dict['ENABLE_DRIVE_UPLOAD'].upper()
            self.ENABLE_DRIVE_UPLOAD = (val == 'TRUE')

        if 'ENABLE_SHEETS_LOGGING' in settings_dict:
            val = settings_dict['ENABLE_SHEETS_LOGGING'].upper()
            self.ENABLE_SHEETS_LOGGING = (val == 'TRUE')

# Global Instance
DYNAMIC_CONFIG = DynamicConfig()
