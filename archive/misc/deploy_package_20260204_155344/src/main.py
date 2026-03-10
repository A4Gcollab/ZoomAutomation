
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
        self.sheets = None  # Google Sheets manager for status updates
        
    def run(self):
        logger.info("=" * 60)
        logger.info("🚀 Background Service Thread RUNNING")
        logger.info("=" * 60)
        self._init_clients()
        
        cycle_count = 0
        while self.running:
            try:
                # 0. ENSURE CLIENTS ARE ACTIVE (Self-Healing)
                self._init_clients()
                
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"📊 Service Cycle #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # 1. SCAN (Ingestion)
                logger.info("Phase 1: Scanning Zoom for new recordings...")
                self._scan_zoom()
                
                # 2. PROCESS (Approvals)
                logger.info("Phase 2: Processing approved tasks...")
                self._process_queue()
                
                # 3. SLEEP
                # 3. SLEEP
                logger.info(f"✅ Cycle #{cycle_count} complete. Sleeping 60s...")
                # Responsive sleep: check self.running every 1s
                for _ in range(60):
                    if not self.running:
                        logger.info("🛑 Stop signal received during sleep. Exiting...")
                        break
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Service Loop Error in Cycle #{cycle_count}: {e}")
                import traceback
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                db.add_log("ERROR", f"Service Loop Error: {e}")
                time.sleep(60)
        
        logger.info("Background Service Loop Ended (running=False)")

    def _init_clients(self):
        """Initialize API clients. Non-blocking - failures are logged but don't stop the service."""
        logger.info("Initializing API clients...")
        
        # YouTube
        if not self.youtube:
            try:
                logger.info("  Initializing YouTube client...")
                self.youtube = YouTubeClient(config.YOUTUBE_CLIENT_SECRET_PATH, config.YOUTUBE_TOKEN_PATH)
                logger.info("  ✅ YouTube client ready")
            except Exception as e:
                logger.error(f"  ❌ YouTube client failed: {e}")
                self.youtube = None
        
        # Drive
        if not self.drive:
            try:
                logger.info("  Initializing Drive client...")
                self.drive = DriveClient(
                    auth_mode='user', 
                    token_path=config.DRIVE_TOKEN_PATH, 
                    client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH
                )
                logger.info("  ✅ Drive client ready")
            except Exception as e:
                logger.error(f"  ❌ Drive client failed: {e}")
                self.drive = None
        
        # Zoom Clients
        try:
            logger.info("  Initializing Zoom clients...")
            for i, creds in enumerate(config.ZOOM_ACCOUNTS, 1):
                name = f"Zoom Account {i}"
                # Pass the whole credentials dict
                self.zoom_clients[name] = ZoomClient(creds)
            logger.info(f"  ✅ {len(self.zoom_clients)} Zoom client(s) ready")
        except Exception as e:
            logger.error(f"  ❌ Zoom clients failed: {e}")
            logger.warning("  Service will continue but Zoom scanning will fail")
        
        # Google Sheets
        if not self.sheets:
            try:
                logger.info("  Initializing Google Sheets client...")
                from src.sheets_integration import SheetManager
                import gspread
                from google.oauth2.service_account import Credentials
                
                scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_file(config.DRIVE_SERVICE_ACCOUNT_FILE, scopes=scopes)
                self.sheets = SheetManager(creds, config.GOOGLE_SHEET_ID)
                logger.info("  ✅ Google Sheets client ready")
            except Exception as e:
                logger.error(f"  ❌ Google Sheets client failed: {e}")
                self.sheets = None

    def _find_sheet_row(self, zoom_id):
        """Find the row index in Google Sheets for a given zoom_id."""
        try:
            if not self.sheets or not self.sheets.main_tab:
                return None
            
            # Get all values from column B (Meeting ID column)
            cell = self.sheets.main_tab.find(zoom_id)
            if cell:
                return cell.row
            return None
        except Exception as e:
            logger.warning(f"Failed to find sheet row for {zoom_id}: {e}")
            return None

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

    def _get_drive_folders(self, playlist_name):
        """Get Drive folder IDs for a given playlist name."""
        import json
        from src.config import PLAYLIST_CONFIG_PATH
        
        if not PLAYLIST_CONFIG_PATH.exists():
            return None, None
            
        try:
            with open(PLAYLIST_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                
                for pl in data.get('playlists', []):
                    if pl.get('playlist_name') == playlist_name:
                        return pl.get('drive_folder_id'), pl.get('transcript_folder_id')
        except Exception as e:
            logger.error(f"Failed to get drive folders: {e}")
        return None, None

    def _scan_zoom(self):
        logger.info("Scanning Zoom...")
        now = datetime.now()
        # Scan last 90 days to ensure we don't miss anything
        start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        today = now.strftime("%Y-%m-%d")
        
        count = 0
        for name, client in self.zoom_clients.items():
            try:
                user_count = 0
                for user in client.get_all_users():
                    user_count += 1
                    recs = client.get_user_recordings(user['id'], start_date, today)
                    logger.info(f"   Scan {name}: User {user.get('email')} -> {len(recs)} recordings found")
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
                            
                            # Add to Google Sheets
                            if self.sheets:
                                try:
                                    self.sheets.add_recording(r)
                                    logger.info(f"Added {r['id']} to Sheets")
                                except Exception as e:
                                    logger.error(f"Failed to add to sheets: {e}")
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
        
        logger.info(f"Found {len(tasks)} approved tasks to process")
        
        for task in tasks:
            task = dict(task)  # Convert Row to dict
            zoom_id = task['zoom_id']
            topic = task['topic']
            start_time = task['start_time']
            team = task.get('team', 'Unknown')
            playlist = task.get('playlist', 'General')
            account_name = task.get('account_name', 'Zoom Account 1')
            
            logger.info(f"▶️  Processing: {zoom_id} - {topic}")
            db.update_recording(zoom_id, {"status": "PROCESSING"})
            
            # Update sheets status to PROCESSING
            sheet_row = None # Initialize sheet_row here
            if self.sheets:
                try:
                    # Find the row for this zoom_id
                    sheet_row = self._find_sheet_row(zoom_id)
                    if sheet_row:
                        self.sheets.update_row_status(sheet_row, "PROCESSING")
                        logger.info(f"   📊 Sheets updated: PROCESSING")
                except Exception as e:
                    logger.warning(f"   ⚠️  Sheets update failed: {e}")
            
            try:
                # Generate proper names with date format
                names = generate_names(topic, start_time)
                video_filename = names['video_filename']
                youtube_title = names['youtube_title']  # Format: "20260108 Topic Name"
                transcript_filename = names['transcript_filename']
                
                logger.info(f"   Generated title: {youtube_title}")
                
                # Get the Zoom client for this account
                zoom_client = self.zoom_clients.get(account_name)
                if not zoom_client:
                    raise Exception(f"Zoom client not found for account: {account_name}")
                
                # 1. DOWNLOAD from Zoom
                logger.info(f"   📥 Downloading from Zoom...")
                video_path = os.path.join(DOWNLOAD_DIR, video_filename)
                transcript_path = os.path.join(DOWNLOAD_DIR, transcript_filename)
                
                # Download video and transcript
                recording_data = zoom_client.get_recording_details(zoom_id)
                video_url = None
                transcript_url = None
                
                for file in recording_data.get('recording_files', []):
                    if file.get('file_type') == 'MP4':
                        video_url = file.get('download_url')
                    elif file.get('file_type') == 'TRANSCRIPT':
                        transcript_url = file.get('download_url')
                
                if not video_url:
                    raise Exception("No video file found in recording")
                
                # Download video
                zoom_client.download_file(video_url, video_path)
                logger.info(f"   ✅ Video downloaded: {video_filename}")
                
                # Download transcript if available
                if transcript_url:
                    zoom_client.download_file(transcript_url, transcript_path)
                    logger.info(f"   ✅ Transcript downloaded")
                
                # 2. UPLOAD to YouTube
                logger.info(f"   📤 Uploading to YouTube...")
                description = f"{topic}\n\nRecorded: {start_time}\nTeam: {team}\nPlaylist: {playlist}"
                
                video_id = self.youtube.upload_video(
                    file_path=video_path,
                    title=youtube_title,  # Uses date-formatted title
                    description=description,
                    privacy_status="unlisted"
                )
                youtube_url = f"https://youtu.be/{video_id}"
                logger.info(f"   ✅ YouTube: {youtube_url}")
                
                # Update sheets with YouTube URL
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "PROCESSING", youtube_url=youtube_url)
                        logger.info(f"   📊 Sheets updated: YouTube URL")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Sheets update failed: {e}")
                
                # Upload captions if transcript exists
                if transcript_url and os.path.exists(transcript_path):
                    try:
                        # Read transcript content
                        with open(transcript_path, 'r', encoding='utf-8') as f:
                            transcript_text = f.read()
                        
                        # Upload as caption/subtitle
                        self.youtube.upload_caption(video_id, transcript_path, language='en')
                        logger.info(f"   ✅ Captions/transcript uploaded to YouTube")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Caption upload failed: {e}")
                
                # Add to playlist
                try:
                    self.youtube.add_to_playlist(video_id, playlist)
                    logger.info(f"   ✅ Added to playlist: {playlist}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Playlist add failed: {e}")
                
                # 3. UPLOAD to Drive (Backup)
                logger.info(f"   📤 Uploading to Drive...")
                
                # Get exact Drive folder IDs from playlist configuration
                drive_folder_id, transcript_folder_id = self._get_drive_folders(playlist)
                
                if not drive_folder_id or not transcript_folder_id:
                    raise Exception(f"Drive folder IDs not found for playlist: {playlist}. Check config/playlists.json")
                
                logger.info(f"   Using Drive folders - Video: {drive_folder_id}, Transcript: {transcript_folder_id}")
                
                # Upload video to recording folder
                drive_video_id = self.drive.upload_file(video_path, video_filename, drive_folder_id)
                drive_url = f"https://drive.google.com/file/d/{drive_video_id}/view"
                logger.info(f"   ✅ Drive Video: {drive_url}")
                
                # Update sheets with Drive URL
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "PROCESSING", youtube_url=youtube_url, drive_url=drive_url)
                        logger.info(f"   📊 Sheets updated: Drive URL")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Sheets update failed: {e}")
                
                # Upload transcript to transcript folder
                if os.path.exists(transcript_path):
                    drive_transcript_id = self.drive.upload_file(transcript_path, transcript_filename, transcript_folder_id)
                    logger.info(f"   ✅ Transcript backed up to Drive: https://drive.google.com/file/d/{drive_transcript_id}/view")
                
                # 4. VERIFY UPLOADS (Critical Safety Check)
                logger.info(f"   🔍 Verifying uploads...")
                youtube_verified = False
                drive_verified = False
                
                try:
                    # Verify YouTube
                    yt_status = self.youtube.get_video_status(video_id)
                    if yt_status in ['uploaded', 'processed']:
                        youtube_verified = True
                        logger.info(f"   ✅ YouTube upload verified: {yt_status}")
                    else:
                        raise Exception(f"YouTube video status: {yt_status}")
                except Exception as e:
                    logger.error(f"   ❌ YouTube verification failed: {e}")
                
                try:
                    # Verify Drive (check if file exists)
                    if drive_video_id:
                        drive_verified = True
                        logger.info(f"   ✅ Drive upload verified")
                except Exception as e:
                    logger.error(f"   ❌ Drive verification failed: {e}")
                
                # 5. DELETE FROM ZOOM (Only if both uploads verified)
                if youtube_verified and drive_verified:
                    try:
                        logger.info(f"   🗑️  Deleting from Zoom...")
                        if zoom_client.delete_recording(zoom_id, action="delete"):
                            logger.info(f"   ✅ Zoom recording deleted permanently")
                        else:
                            logger.warning(f"   ⚠️  Zoom deletion returned False")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Zoom deletion failed (non-critical): {e}")
                        # Don't fail the entire process if Zoom deletion fails
                else:
                    logger.warning(f"   ⚠️  Skipping Zoom deletion - uploads not verified (YT: {youtube_verified}, Drive: {drive_verified})")
                
                # 6. CLEANUP local files
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(transcript_path):
                    os.remove(transcript_path)
                logger.info(f"   🗑️  Local files cleaned up")
                
                # 7. UPDATE status
                db.update_recording(zoom_id, {
                    "status": "COMPLETED",
                    "youtube_url": youtube_url,
                    "drive_url": drive_url,
                    "processed_at": datetime.now().isoformat()
                })
                db.add_log("INFO", f"✅ Completed: {zoom_id} - {youtube_title}")
                logger.info(f"   ✅ COMPLETED: {zoom_id}")
                
                # Final sheets update: COMPLETED
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "COMPLETED", youtube_url=youtube_url, drive_url=drive_url)
                        logger.info(f"   📊 Sheets updated: COMPLETED")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Sheets update failed: {e}")
                
            except Exception as e:
                logger.error(f"   ❌ Processing Failed {zoom_id}: {e}")
                import traceback
                logger.error(f"   Traceback:\n{traceback.format_exc()}")
                db.update_recording(zoom_id, {"status": "ERROR", "error_message": str(e)})
                db.add_log("ERROR", f"Failed {zoom_id}: {e}")
                
                # Update sheets: ERROR
                if self.sheets and 'sheet_row' in locals():
                    try:
                        self.sheets.update_row_status(sheet_row, "ERROR")
                        logger.info(f"   📊 Sheets updated: ERROR")
                    except Exception as sheet_err:
                        logger.warning(f"   ⚠️  Sheets error update failed: {sheet_err}")

# Initializer for fastAPI to call
service = BackgroundService()
def start_service():
    if not service.is_alive():
        service.start()
