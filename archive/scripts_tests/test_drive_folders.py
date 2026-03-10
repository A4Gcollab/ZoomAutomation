import sys
sys.path.insert(0, '.')
from src.drive_client import DriveClient
drive = DriveClient(auth_mode='user', token_path='secrets/token_drive.json', client_secret_path='secrets/client_secret.json')

about = drive.service.about().get(fields="user").execute()
print(about)
