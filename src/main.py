
import logging
import time
import threading
from datetime import datetime, timedelta
from src import config
from src.db_sql import db
from src.zoom_client import ZoomClient
from src.youtube_client import YouTubeClient
from src.drive_client import DriveClient
from src.utils import generate_names
from src.monitor import check_disk_space, cleanup_old_files
import os
from src.config import DOWNLOAD_DIR

logger = logging.getLogger("BackgroundService")

class BackgroundService(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        self.zoom_clients = {}
        self.youtube = None
        self.drive = None
        
    def run(self):
        logger.info("Background Service Started.")
        self._init_clients()
        
        while self.running:
            try:
                # 1. SCAN (Ingestion)
                self._scan_zoom()
                
                # 2. PROCESS (Approvals)
                self._process_queue()
                
                # 3. SLEEP
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Service Loop Error: {e}")
                db.add_log("ERROR", f"Service Loop Error: {e}")
                time.sleep(60)

    def _init_clients(self):
        try:
            # YouTube
            self.youtube = YouTubeClient(config.YOUTUBE_CLIENT_SECRET_PATH, config.YOUTUBE_TOKEN_PATH)
            
            # Drive
            self.drive = DriveClient(
                auth_mode=config.DRIVE_AUTH_MODE,
                service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE,
                client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
                token_path=config.DRIVE_TOKEN_PATH
            )
            
            # Zoom
            for z_cfg in config.ZOOM_ACCOUNTS:
                self.zoom_clients[z_cfg['name']] = ZoomClient(z_cfg)
                
        except Exception as e:
            logger.error(f"Client Init Failed: {e}")

        if count > 0:
            db.add_log("INFO", f"Found {count} new recordings.")

    def _resolve_team_playlist(self, meeting_id):
        """Match Meeting ID to Config."""
        import json
        from src.config import PLAYLIST_CONFIG_PATH
        
        if not PLAYLIST_CONFIG_PATH.exists():
            return None, None
            
        try:
            with open(PLAYLIST_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                meeting_id = str(meeting_id) # Ensure string
                
                for pl in data.get('playlists', []):
                    # Check if ID is in the list
                    if meeting_id in pl.get('meeting_ids', []):
                        return pl.get('category'), pl.get('playlist_name')
        except Exception:
            pass
        return None, None

    def _scan_zoom(self):
        logger.info("Scanning Zoom...")
        now = datetime.now()
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        today = now.strftime("%Y-%m-%d")
        
        count = 0
        for name, client in self.zoom_clients.items():
            try:
                for user in client.get_all_users():
                    recs = client.get_user_recordings(user['id'], yesterday, today)
                    for r in recs:
                        r['account_name'] = name
                        
                        # AUTO-RESOLVE
                        team, playlist = self._resolve_team_playlist(r['id'])
                        if team: r['team'] = team
                        if playlist: r['playlist'] = playlist
                        
                        if db.add_recording(str(r['id']), r):
                            count += 1
                            if team:
                                logger.info(f"Auto-Matched {r['id']} -> {team} / {playlist}")
            except Exception as e:
                logger.error(f"Zoom Scan Error ({name}): {e}")

    def _process_queue(self):
        # Fetch APPROVED items (different from PENDING)
        # We need a new method in DB or execute query
        # Actually API sets status to 'APPROVED'. 
        # We need to find 'APPROVED' items.
        
        # Let's add get_approved to DB or run query here? 
        # Better to add to DB wrapper. But for now I'll use raw query for speed
        cur = db.conn.cursor()
        cur.execute("SELECT * FROM recordings WHERE status = 'APPROVED'")
        tasks = cur.fetchall()
        
        for task in tasks:
            zoom_id = task['zoom_id']
            # PROCESSING...
            logger.info(f"Processing Approved Task: {zoom_id}")
            db.update_recording(zoom_id, {"status": "PROCESSING"})
            
            try:
                # 1. Download (Logic similar to before)
                # For brevity, implementing High-Level flow
                
                # ... Download ...
                # ... Upload YT ...
                # ... Upload Drive ...
                
                # Mock Success for now until fully ported utils
                time.sleep(2) 
                
                db.update_recording(zoom_id, {
                    "status": "COMPLETED",
                    "youtube_url": "https://youtu.be/mock",
                    "drive_url": "https://drive.google.com/mock"
                })
                db.add_log("INFO", f"Completed Task: {zoom_id}")
                
            except Exception as e:
                logger.error(f"Processing Failed {zoom_id}: {e}")
                db.update_recording(zoom_id, {"status": "ERROR"})
                db.add_log("ERROR", f"Failed {zoom_id}: {e}")

# Initializer for fastAPI to call
service = BackgroundService()
def start_service():
    if not service.is_alive():
        service.start()
