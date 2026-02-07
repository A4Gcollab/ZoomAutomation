import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import logging
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from src.utils import retry_with_backoff

# Scopes for YouTube Data API
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",  # Full access for playlist management
    "https://www.googleapis.com/auth/youtube.force-ssl" # Required for Captions
]

class YouTubeClient:
    def __init__(self, client_secret_path, token_path):
        self.logger = logging.getLogger("YouTubeClient")
        self.client_secret_path = client_secret_path
        self.token_path = token_path
        self.youtube = self._authenticate()

    def _authenticate(self):
        credentials = None
        # Load token if exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                credentials = pickle.load(token)

        # Refresh or Create new
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                self.logger.info("Refreshing Access Token...")
                credentials.refresh(Request())
                # Save the refreshed credentials
                with open(self.token_path, 'wb') as token:
                    pickle.dump(credentials, token)
            except Exception as e:
                self.logger.error(f"Token refresh failed: {e}")
                raise Exception("Authentication Token expired and refresh failed. Please run scripts/setup_youtube.py")

        if not credentials or not credentials.valid:
            self.logger.error("No valid credentials found.")
            raise Exception("Authentication required. Please run 'python scripts/setup_youtube.py' to login.")

        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    @retry_with_backoff(retries=3, initial_delay=5)
    def upload_video(self, file_path, title, description, privacy_status="unlisted", category_id="22"):
        """
        Uploads a video to YouTube.
        Returns the Video ID.
        """
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["Zoom", "Meeting", "Recording", "Omysha"],
                "categoryId": category_id,
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en"
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        
        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        self.logger.info(f"Uploading {file_path} to YouTube...")
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                self.logger.info(f"Uploaded {int(status.progress() * 100)}%")

        video_id = response.get("id")
        self.logger.info(f"Upload Complete! Video ID: {video_id}")
        return video_id

    def get_video_status(self, video_id):
        """Check processing status."""
        request = self.youtube.videos().list(
            part="status,processingDetails",
            id=video_id
        )
        response = request.execute()
        if not response['items']:
            return None
        return response['items'][0]['status']['uploadStatus']

    def verify_video_exists(self, video_id):
        """
        Verify that a video exists and is accessible on YouTube.

        Returns:
            dict with 'exists', 'status', 'title' or None if error
        """
        try:
            if not video_id:
                return {'exists': False, 'error': 'No video ID provided'}

            request = self.youtube.videos().list(
                part="snippet,status",
                id=video_id
            )
            response = request.execute()

            if not response.get('items'):
                return {'exists': False, 'error': 'Video not found'}

            item = response['items'][0]
            return {
                'exists': True,
                'status': item['status']['uploadStatus'],
                'privacy': item['status'].get('privacyStatus', 'unknown'),
                'title': item['snippet']['title']
            }
        except Exception as e:
            self.logger.error(f"Failed to verify video {video_id}: {e}")
            return {'exists': False, 'error': str(e)}
    
    @retry_with_backoff(retries=3, initial_delay=2)
    def add_to_playlist(self, video_id, playlist_id):
        """
        Add a video to a specific playlist.
        
        Args:
            video_id: YouTube video ID
            playlist_id: YouTube playlist ID
            
        Returns:
            str: Playlist item ID
        """
        try:
            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            response = request.execute()
            self.logger.info(f"Added video {video_id} to playlist {playlist_id}")
            return response.get("id")
        except Exception as e:
            self.logger.error(f"Failed to add video to playlist: {e}")
            raise
    
    def get_playlists(self):
        """
        Retrieve all playlists for the authenticated user.
        
        Returns:
            list: List of playlist dictionaries with id, title, and itemCount
        """
        try:
            playlists = []
            request = self.youtube.playlists().list(
                part="snippet,contentDetails",
                mine=True,
                maxResults=50
            )
            
            while request:
                response = request.execute()
                for item in response.get('items', []):
                    playlists.append({
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'itemCount': item['contentDetails']['itemCount']
                    })
                
                request = self.youtube.playlists().list_next(request, response)
            
            return playlists
        except Exception as e:
            self.logger.error(f"Failed to retrieve playlists: {e}")
            return []
    
    @retry_with_backoff(retries=2, initial_delay=3)
    def create_playlist(self, title, description="", privacy_status="unlisted"):
        """
        Create a new playlist.
        
        Args:
            title: Playlist title
            description: Playlist description
            privacy_status: public, private, or unlisted
            
        Returns:
            str: Playlist ID
        """
        try:
            request = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description
                    },
                    "status": {
                        "privacyStatus": privacy_status
                    }
                }
            )
            response = request.execute()
            playlist_id = response.get("id")
            self.logger.info(f"Created new playlist: {title} (ID: {playlist_id})")
            return playlist_id
        except Exception as e:
            self.logger.error(f"Failed to create playlist: {e}")
            raise

    def get_recent_uploads(self, limit=50):
        """
        Fetch recent uploads to check for duplicates.
        Uses 'uploads' playlist to be quota efficient (1 unit).
        
        Returns:
            dict: {title: video_id} mapping of recent videos
        """
        try:
            # 1. Get Uploads Playlist ID
            request = self.youtube.channels().list(
                part="contentDetails",
                mine=True
            )
            response = request.execute()
            
            if not response.get('items'):
                return {}
                
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 2. Get Videos from Uploads Playlist
            videos = {}
            request = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=limit
            )
            
            while request and len(videos) < limit:
                response = request.execute()
                for item in response.get('items', []):
                    title = item['snippet']['title']
                    vid = item['snippet']['resourceId']['videoId']
                    videos[title] = vid
                
                # We only need the first page usually (~50 items)
                # If specifically requested more, we page
                break 
                
            return videos
            
        except Exception as e:
            self.logger.error(f"Failed to fetch recent uploads: {e}")
            return {}

    @retry_with_backoff(retries=3, initial_delay=5)
    def upload_caption(self, video_id, file_path, name="Transcript", language="en"):
        """
        Uploads a caption track to a YouTube video.
        """
        try:
            body = {
                "snippet": {
                    "videoId": video_id,
                    "language": language,
                    "name": name,
                    "isDraft": False
                }
            }

            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

            request = self.youtube.captions().insert(
                part="snippet",
                body=body,
                media_body=media
            )
            
            self.logger.info(f"Uploading caption {file_path} to video {video_id}...")
            response = request.execute()
            self.logger.info(f"Caption Upload Complete! ID: {response.get('id')}")
            return response.get("id")

        except Exception as e:
            self.logger.error(f"Failed to upload caption: {e}")
            # Non-critical, so we don't re-raise to crash the flow, but we assume re-try wrapper handles transient errors.
            # If wrapper raises, it crashes. We want that behavior if retries fail.
            raise

    def delete_video(self, video_id):
        """
        Deletes a video from YouTube.
        """
        try:
            self.youtube.videos().delete(id=video_id).execute()
            self.logger.info(f"Deleted video {video_id} from YouTube")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete video {video_id}: {e}")
            return False
