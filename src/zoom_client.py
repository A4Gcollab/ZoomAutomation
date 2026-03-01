import requests
import base64
import time
import logging
import os
from src.utils import retry_with_backoff

class ZoomClient:
    def __init__(self, credentials):
        """
        credentials: {
            'account_id': ...,
            'client_id': ...,
            'client_secret': ...
        }
        """
        self.account_id = credentials['account_id'].strip().strip('"').strip("'")
        self.client_id = credentials['client_id'].strip().strip('"').strip("'")
        self.client_secret = credentials['client_secret'].strip().strip('"').strip("'")
        self.base_url = "https://api.zoom.us/v2"
        self.token = None
        self.token_expiry = 0
        self.logger = logging.getLogger(f"ZoomClient-{credentials.get('name', 'Auth')}")

    @retry_with_backoff(retries=2, initial_delay=1)
    def _get_access_token(self):
        """Retrieve Server-to-Server OAuth token."""
        if self.token and time.time() < self.token_expiry - 60:
            return self.token

        url = "https://zoom.us/oauth/token"
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {b64_auth}"
            # Content-Type is not strictly needed if body is empty, but can stay
        }
        query_params = {
            "grant_type": "account_credentials",
            "account_id": self.account_id
        }
        
        resp = requests.post(url, headers=headers, params=query_params)
        if resp.status_code != 200:
            try:
                error_data = resp.json()
                self.logger.error(f"Zoom OAuth Error: {error_data.get('reason')} - {error_data.get('error')}")
            except:
                self.logger.error(f"Zoom OAuth Error: {resp.text}")
            resp.raise_for_status()

        data = resp.json()
        self.token = data['access_token']
        self.token_expiry = time.time() + data['expires_in']
        self.logger.info("Successfully refreshed Access Token")
        return self.token

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }

    @retry_with_backoff(retries=3)
    def get_all_users(self):
        """
        Yields all active users in the account.
        Handles pagination automatically.
        """
        url = f"{self.base_url}/users"
        params = {
            "page_size": 30,
            "status": "active"
        }
        
        while True:
            resp = requests.get(url, headers=self.get_headers(), params=params)
            if resp.status_code != 200:
                self.logger.error(f"Zoom API Error (get_all_users): {resp.status_code} - {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            
            for user in data.get('users', []):
                yield user
            
            # Check for next page
            if data.get('next_page_token'):
                params['next_page_token'] = data['next_page_token']
            else:
                break

    @retry_with_backoff(retries=3)
    def get_user_recordings(self, user_id, from_date, to_date):
        """
        Fetch cloud recordings for a specific user.
        dates should be YYYY-MM-DD strings.
        """
        url = f"{self.base_url}/users/{user_id}/recordings"
        params = {
            "from": from_date,
            "to": to_date,
            "page_size": 30
        }
        
        recordings = []
        while True:
            resp = requests.get(url, headers=self.get_headers(), params=params)
            if resp.status_code == 404:
                self.logger.warning(f"User {user_id} not found or no recordings.")
                break
            if resp.status_code != 200:
                self.logger.error(f"Zoom API Error (get_user_recordings): {resp.status_code} - {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            
            recordings.extend(data.get('meetings', []))
            
            if data.get('next_page_token'):
                params['next_page_token'] = data['next_page_token']
            else:
                break
        
        return recordings

    @retry_with_backoff(retries=3)
    def get_user_meetings(self, user_id):
        """
        Fetch scheduled meetings for a specific user.
        """
        url = f"{self.base_url}/users/{user_id}/meetings"
        params = {
            "page_size": 100,
            "type": "scheduled"
        }
        
        meetings = []
        while True:
            resp = requests.get(url, headers=self.get_headers(), params=params)
            if resp.status_code == 404:
                break
            if resp.status_code != 200:
                self.logger.error(f"Zoom API Error (get_user_meetings): {resp.status_code} - {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            
            meetings.extend(data.get('meetings', []))
            
            if data.get('next_page_token'):
                params['next_page_token'] = data['next_page_token']
            else:
                break
        
        return meetings

    @retry_with_backoff(retries=3)
    def download_file(self, download_url, dest_path):
        """
        Download a file from Zoom.
        Appends access token to the request for authentication.
        """
        # Append access token if not already present
        # For S2S OAuth, we just need the Bearer header usually, but for download_url 
        # specifically, sometimes query param is needed: ?access_token=...
        # actually for standard download_url, it redirects. Bearer token in header is safest.
        
        # However, getting 'download_url' from recording object directly often requires
        # the user's ZAK token or just the account level OAuth token.
        # Let's try standard Bearer header.
        
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}"
        }

        with requests.get(download_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    
    @retry_with_backoff(retries=2)
    def delete_recording(self, meeting_id, action="delete"):
        """
        Delete a recording from Zoom cloud.
        
        Args:
            meeting_id: The meeting ID or UUID
            action: 'trash' to move to trash, 'delete' to permanently delete
            
        Returns:
            bool: True if successful
        """
        url = f"{self.base_url}/meetings/{meeting_id}/recordings"
        params = {"action": action}
        
        self.logger.info(f"Deleting recording for meeting {meeting_id} (action: {action})")
        
        resp = requests.delete(url, headers=self.get_headers(), params=params)
        
        if resp.status_code == 204:
            self.logger.info(f"Successfully deleted recording for meeting {meeting_id}")
            return True
        elif resp.status_code == 404:
            self.logger.warning(f"Recording not found for meeting {meeting_id} (may already be deleted)")
            return True  # Consider this success since it's already gone
        else:
            self.logger.error(f"Failed to delete recording: {resp.status_code} - {resp.text}")
            resp.raise_for_status()
            return False

    @retry_with_backoff(retries=3)
    def get_meeting_recordings(self, meeting_id):
        """
        Fetch all recordings for a specific meeting ID.
        Useful for refreshing metadata before download.
        """
        url = f"{self.base_url}/meetings/{meeting_id}/recordings"

        resp = requests.get(url, headers=self.get_headers())
        if resp.status_code == 404:
            self.logger.warning(f"Meeting {meeting_id} recordings not found (404).")
            return None
        if resp.status_code != 200:
            self.logger.error(f"Zoom API Error (get_meeting_recordings): {resp.status_code} - {resp.text}")

        resp.raise_for_status()
        return resp.json()

    # Alias for backward compatibility
    def get_recording_details(self, meeting_id):
        """Alias for get_meeting_recordings."""
        return self.get_meeting_recordings(meeting_id)
