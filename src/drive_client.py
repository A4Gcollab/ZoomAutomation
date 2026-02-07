import logging
import os
import pickle
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class DriveClient:
    def __init__(self, auth_mode='user', **kwargs):
        self.logger = logging.getLogger("DriveClient")
        # Add Spreadsheets scope
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        self.mode = auth_mode
        self.config = kwargs
        self.credentials = None  # Store credentials for reuse
        self.service = self._authenticate()

    def _authenticate(self):
        credentials = None
        
        if self.mode == 'service_account':
            self.logger.info("Using Service Account Authentication")
            sa_file = self.config.get('service_account_file')
            if not sa_file or not os.path.exists(sa_file):
                raise ValueError(f"Service account file not found: {sa_file}")
            
            creds = service_account.Credentials.from_service_account_file(
                sa_file, scopes=self.SCOPES)
            self.credentials = creds
            return build('drive', 'v3', credentials=creds)
        
        else: # user mode
            self.logger.info("Using User OAuth Authentication")
            token_path = self.config.get('token_path')
            client_secret_path = self.config.get('client_secret_path')
            
            # Load token if exists
            if os.path.exists(token_path):
                try:
                    with open(token_path, 'rb') as token:
                        credentials = pickle.load(token)
                except Exception:
                    self.logger.warning("Token file invalid, forcing re-auth")
                    credentials = None

            # Refresh or Create new
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    self.logger.info("Refreshing Drive Access Token...")
                    try:
                        credentials.refresh(Request())
                    except Exception:
                        self.logger.warning("Refresh failed, forcing new auth")
                        credentials = None
                
                if not credentials:
                    self.logger.info("Fetching new Drive Access Token (User Interaction Required)...")
                    # Should verify if we need to delete old token file first?
                    # Flow handles it.
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        client_secret_path, self.SCOPES)
                    credentials = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(token_path, 'wb') as token:
                    pickle.dump(credentials, token)

            self.credentials = credentials
            return build('drive', 'v3', credentials=credentials)

    def find_folder(self, folder_name, parent_id=None):
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
            
        results = self.service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']
        return None

    def create_folder(self, folder_name, parent_id):
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        file = self.service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
        return file.get('id')

    def ensure_folder(self, folder_name, parent_id):
        folder_id = self.find_folder(folder_name, parent_id)
        if not folder_id:
            folder_id = self.create_folder(folder_name, parent_id)
        return folder_id

    def upload_file(self, file_path, filename, parent_id):
        """
        Uploads a file to a specific folder in Drive.
        """
        file_metadata = {
            'name': filename,
            'parents': [parent_id]
        }
        media = MediaFileUpload(file_path, resumable=True)
        
        self.logger.info(f"Uploading {filename} to Drive folder {parent_id}...")
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        self.logger.info(f"Drive Upload Complete. ID: {file.get('id')}")
        return file.get('id')

    def check_file_integrity(self, file_id, local_file_path):
        """
        Verifies that the file exists on Drive and matches the local file size.
        """
        try:
            # Get Remote Metadata
            remote_file = self.service.files().get(
                fileId=file_id,
                fields="id, size, trashed",
                supportsAllDrives=True
            ).execute()

            if remote_file.get('trashed'):
                self.logger.error("Verification Failed: Remote file is in trash.")
                return False

            remote_size = int(remote_file.get('size', 0))
            local_size = os.path.getsize(local_file_path)

            # Allow slight variance? No, exact match for binary identical,
            # but Drive might report different size? Usually exact for binary.
            if remote_size == local_size:
                self.logger.info(f"Integrity Verified: Remote Size {remote_size} == Local Size {local_size}")
                return True
            else:
                self.logger.error(f"Integrity Mismatch: Remote {remote_size} != Local {local_size}")
                return False

        except Exception as e:
            self.logger.error(f"Verification Check Failed: {e}")
            return False

    def verify_file_exists(self, file_id):
        """
        Verify that a file exists on Drive and is accessible.

        Args:
            file_id: The Drive file ID to verify

        Returns:
            dict with 'exists', 'name', 'size' or error info
        """
        try:
            if not file_id:
                return {'exists': False, 'error': 'No file ID provided'}

            remote_file = self.service.files().get(
                fileId=file_id,
                fields="id, name, size, trashed, mimeType",
                supportsAllDrives=True
            ).execute()

            if remote_file.get('trashed'):
                return {'exists': False, 'error': 'File is in trash'}

            return {
                'exists': True,
                'name': remote_file.get('name'),
                'size': int(remote_file.get('size', 0)),
                'mimeType': remote_file.get('mimeType')
            }

        except Exception as e:
            self.logger.error(f"Failed to verify file {file_id}: {e}")
            return {'exists': False, 'error': str(e)}
