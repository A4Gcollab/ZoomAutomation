
import logging
import googleapiclient.errors
import time
import threading
import traceback
import urllib.parse
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

# How often (in cycles) to run auto-recovery. Every 10 cycles = ~10 minutes.
RECOVERY_EVERY_N_CYCLES = 10
MAX_RETRIES = 3


class BackgroundService(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        self.zoom_clients = {}
        self.youtube = None
        self.drive = None
        self.sheets = None
        self._youtube_quota_paused_until = None  # Track YouTube quota exhaustion

    def run(self):
        logger.info("=" * 60)
        logger.info("Background Service Thread RUNNING")
        logger.info("=" * 60)
        self._init_clients()

        cycle_count = 0
        while self.running:
            try:
                # Re-initialize any dead clients each cycle
                self._init_clients()

                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"Service Cycle #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")

                # AUTO-RECOVERY: run every N cycles
                if cycle_count % RECOVERY_EVERY_N_CYCLES == 0:
                    self._auto_recover()

                # 1. SCAN
                logger.info("Phase 1: Scanning Zoom for new recordings...")
                self._scan_zoom()

                # 2. PROCESS
                logger.info("Phase 2: Processing approved tasks...")
                self._process_queue()

                # 2.5 PROCESS COMPRESSION QUEUE
                logger.info("Phase 2.5: Processing compression queue...")
                self._process_compressing_queue()

                # 3. CLEANUP (Delayed Zoom Deletions)
                logger.info("Phase 3: Checking for recordings ready for Zoom deletion...")
                self._cleanup_zoom_recordings()

                # 4. SLEEP (responsive - check self.running every 1s)
                logger.info(f"Cycle #{cycle_count} complete. Sleeping 60s...")
                for _ in range(60):
                    if not self.running:
                        logger.info("Stop signal received during sleep. Exiting...")
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Service Loop Error in Cycle #{cycle_count}: {e}")
                logger.error(f"Traceback:\n{traceback.format_exc()}")
                db.add_log("ERROR", f"Service Loop Error: {e}")
                # Sleep a bit longer after errors to avoid tight error loops
                time.sleep(60)

        logger.info("Background Service Loop Ended (running=False)")

    def _init_clients(self):
        """Initialize API clients. Non-blocking - failures are logged but don't stop the service."""
        # YouTube
        if not self.youtube:
            try:
                self.youtube = YouTubeClient(config.YOUTUBE_CLIENT_SECRET_PATH, config.YOUTUBE_TOKEN_PATH)
                logger.info("  YouTube client ready")
            except Exception as e:
                logger.error(f"  YouTube client failed: {e}")
                self.youtube = None

        # Drive
        if not self.drive:
            try:
                self.drive = DriveClient(
                    auth_mode=config.DRIVE_AUTH_MODE,
                    token_path=config.DRIVE_TOKEN_PATH,
                    client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
                    service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE
                )
                logger.info("  Drive client ready")
            except Exception as e:
                logger.error(f"  Drive client failed: {e}")
                self.drive = None

        # Zoom Clients
        if not self.zoom_clients:
            try:
                for i, creds in enumerate(config.ZOOM_ACCOUNTS, 1):
                    name = f"Zoom Account {i}"
                    self.zoom_clients[name] = ZoomClient(creds)
                logger.info(f"  {len(self.zoom_clients)} Zoom client(s) ready")
            except Exception as e:
                logger.error(f"  Zoom clients failed: {e}")

        # Google Sheets
        if not self.sheets:
            try:
                from src.sheets_integration import SheetManager
                from google.oauth2.service_account import Credentials

                scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_file(config.DRIVE_SERVICE_ACCOUNT_FILE, scopes=scopes)
                self.sheets = SheetManager(creds, config.GOOGLE_SHEET_ID)
                logger.info("  Google Sheets client ready")
            except Exception as e:
                logger.error(f"  Google Sheets client failed: {e}")
                self.sheets = None

    def _auto_recover(self):
        """Auto-recover stuck and errored records."""
        logger.info("Running auto-recovery...")
        try:
            stuck = db.recover_stuck_processing(max_age_minutes=60)
            errors = db.recover_error_records(max_retries=MAX_RETRIES)
            if stuck or errors:
                db.add_log("INFO", f"Auto-recovery: {stuck} stuck, {errors} errors recovered")
        except Exception as e:
            logger.error(f"Auto-recovery failed: {e}")

    def _is_youtube_quota_paused(self):
        """Check if YouTube operations are paused due to quota exhaustion."""
        if self._youtube_quota_paused_until is None:
            return False
        if datetime.now() >= self._youtube_quota_paused_until:
            logger.info("YouTube quota pause period ended. Resuming operations.")
            self._youtube_quota_paused_until = None
            return False
        remaining = (self._youtube_quota_paused_until - datetime.now()).total_seconds() / 3600
        logger.info(f"YouTube quota paused. Resuming in {remaining:.1f} hours.")
        return True

    def _pause_youtube_for_quota(self):
        """Pause YouTube operations for 24 hours after quota exhaustion."""
        self._youtube_quota_paused_until = datetime.now() + timedelta(hours=24)
        logger.warning(f"YouTube quota exceeded. Pausing until {self._youtube_quota_paused_until}")
        db.add_log("WARNING", "YouTube daily quota exceeded. Auto-resuming in 24 hours.")

    def _find_sheet_row(self, zoom_id):
        """Find the row index in Google Sheets for a given zoom_id."""
        try:
            if not self.sheets or not self.sheets.main_tab:
                return None
            cell = self.sheets.main_tab.find(zoom_id)
            if cell:
                return cell.row
            return None
        except Exception as e:
            logger.warning(f"Failed to find sheet row for {zoom_id}: {e}")
            return None

    def _resolve_team_playlist(self, meeting_id, topic=''):
        """Match recording to playlist by meeting ID first, then topic keywords.
        
        Matched videos -> auto-APPROVED (zero approval).
        Unmatched videos -> PENDING_PLAYLIST (admin picks playlist).
        """
        import json
        from src.config import PLAYLIST_CONFIG_PATH

        if not PLAYLIST_CONFIG_PATH.exists():
            return None, None

        try:
            with open(PLAYLIST_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                meeting_id = str(meeting_id)
                
                # Priority 1: Match by meeting ID (exact)
                for pl in data.get('playlists', []):
                    if meeting_id in pl.get('meeting_ids', []):
                        return pl.get('category'), pl.get('playlist_name')
                
                # Priority 2: Match by topic keywords (case-insensitive)
                topic_lower = topic.lower()
                for pl in data.get('playlists', []):
                    for keyword in pl.get('keywords', []):
                        if keyword.lower() in topic_lower:
                            return pl.get('category'), pl.get('playlist_name')
                
                # No match -> admin picks (PENDING_PLAYLIST)
                logger.info(f"No keyword match for '{topic}' -> PENDING_PLAYLIST for admin")
        except Exception as e:
            logger.error(f"Error resolving playlist: {e}")
        return None, None

    def _get_playlist_id(self, playlist_name):
        """Look up YouTube playlist ID from playlist name in config."""
        import json
        from src.config import PLAYLIST_CONFIG_PATH

        if not PLAYLIST_CONFIG_PATH.exists():
            return None

        try:
            with open(PLAYLIST_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                for pl in data.get('playlists', []):
                    if pl.get('playlist_name') == playlist_name:
                        return pl.get('playlist_id')
                # Fallback: return default (Miscellaneous) playlist ID
                return data.get('default_playlist_id')
        except Exception as e:
            logger.error(f"Error getting playlist ID: {e}")
        return None

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
        start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        today = now.strftime("%Y-%m-%d")

        count = 0
        for name, client in self.zoom_clients.items():
            try:
                for user in client.get_all_users():
                    try:
                        recs = client.get_user_recordings(user['id'], start_date, today)
                        logger.info(f"   Scan {name}: User {user.get('email')} -> {len(recs)} recordings found")
                        for r in recs:
                            r['account_name'] = name

                            # Use UUID as unique identifier (different for each recurring instance)
                            # Fall back to meeting ID if UUID not available
                            uuid = r.get('uuid', str(r['id']))
                            meeting_id = str(r['id'])

                            topic = r.get('topic', '')
                            team, playlist = self._resolve_team_playlist(meeting_id, topic)
                            if team:
                                r['team'] = team
                            if playlist:
                                r['playlist'] = playlist

                            if db.add_recording(uuid, r, meeting_id=meeting_id):
                                count += 1
                                if team:
                                    logger.info(f"Auto-Matched {uuid} (meeting {meeting_id}) -> {team} / {playlist}")
                                else:
                                    logger.info(f"No match for '{topic}' ({uuid}) -> PENDING_PLAYLIST")
                            elif team and playlist:
                                # Auto-upgrade existing PENDING records when keywords now match
                                try:
                                    with db._lock:
                                        cur = db._get_cursor()
                                        cur.execute("""
                                            UPDATE recordings 
                                            SET status = 'APPROVED', team = ?, playlist = ?
                                            WHERE zoom_id = ? AND status IN ('PENDING', 'PENDING_PLAYLIST')
                                        """, (team, playlist, uuid))
                                        db.conn.commit()
                                        if cur.rowcount > 0:
                                            logger.info(f"Auto-Upgraded {uuid} from PENDING -> APPROVED ({team} / {playlist})")
                                except Exception as e:
                                    logger.warning(f"Auto-upgrade failed for {uuid}: {e}")

                                # Add to Google Sheets (non-critical)
                                if self.sheets:
                                    try:
                                        self.sheets.add_recording(r)
                                    except Exception as e:
                                        logger.warning(f"Sheets add failed (non-critical): {e}")
                    except Exception as e:
                        logger.error(f"Error scanning user {user.get('email', 'unknown')}: {e}")
            except Exception as e:
                logger.error(f"Zoom Scan Error ({name}): {e}")

        if count > 0:
            logger.info(f"Added {count} new recording(s) to database")

    def _encode_uuid_for_zoom(self, uuid_str):
        """URL-encode a UUID for use with the Zoom API.

        Zoom requires double encoding ONLY if the UUID starts with '/' or contains '//'.
        For all other UUIDs, SINGLE URL encoding is strictly required.
        """
        if not uuid_str:
            return uuid_str
            
        if uuid_str.startswith('/') or '//' in uuid_str:
            return urllib.parse.quote(urllib.parse.quote(uuid_str, safe=''), safe='')
            
        return urllib.parse.quote(uuid_str, safe='')

    def _process_queue(self):
        tasks = db.get_approved()
        logger.info(f"Found {len(tasks)} approved tasks to process")

        for task in tasks:
            zoom_id = task['zoom_id']  # This is now the UUID
            meeting_id = task.get('meeting_id') or zoom_id  # Fallback for old records
            topic = task['topic']
            start_time = task['start_time']
            team = task.get('team', 'Unknown')
            playlist = task.get('playlist', 'General')
            account_name = task.get('account_name', 'Zoom Account 1')

            logger.info(f"Processing: {zoom_id} (meeting {meeting_id}) - {topic}")

            # Mark as PROCESSING with timestamp
            db.update_recording(zoom_id, {
                "status": "PROCESSING",
                "processed_at": datetime.now().isoformat()
            })

            # Update sheets status (non-critical)
            sheet_row = None
            if self.sheets:
                try:
                    sheet_row = self._find_sheet_row(zoom_id)
                    if sheet_row:
                        self.sheets.update_row_status(sheet_row, "PROCESSING")
                except Exception as e:
                    logger.warning(f"   Sheets update failed (non-critical): {e}")

            try:
                names = generate_names(topic, start_time)
                video_filename = names['video_filename']
                youtube_title = names['youtube_title']
                transcript_filename = names['transcript_filename']

                logger.info(f"   Generated title: {youtube_title}")

                # Get the Zoom client for this account
                zoom_client = self.zoom_clients.get(account_name)
                if not zoom_client:
                    raise Exception(f"Zoom client not found for account: {account_name}")

                # 1. CHECK QUOTA before downloading (avoid wasting bandwidth)
                if self._is_youtube_quota_paused():
                    logger.warning(f"   Skipping {zoom_id}: YouTube quota paused (not downloading)")
                    continue

                if not self.youtube:
                    raise Exception("YouTube client not initialized")

                # 2. DOWNLOAD from Zoom
                logger.info(f"   Downloading from Zoom...")
                video_path = os.path.join(DOWNLOAD_DIR, video_filename)
                transcript_path = os.path.join(DOWNLOAD_DIR, transcript_filename)

                # Use URL-encoded UUID for Zoom API calls (required for recurring meetings)
                encoded_id = self._encode_uuid_for_zoom(zoom_id)
                recording_data = zoom_client.get_recording_details(encoded_id)

                # If UUID lookup fails, try meeting_id fallback ONLY for non-recurring meetings
                if not recording_data and str(zoom_id) == str(meeting_id):
                    logger.warning(f"   UUID lookup failed, trying meeting ID fallback: {meeting_id}")
                    recording_data = zoom_client.get_recording_details(meeting_id)

                if not recording_data:
                    raise Exception(f"Recording not found on Zoom (UUID: {zoom_id}, Meeting ID: {meeting_id})")

                # Extract the expected date from start_time for verification
                expected_date = start_time[:10] if start_time else None

                video_url = None
                transcript_url = None

                # When multiple recording_files exist (recurring meetings fetched by meeting_id),
                # match by recording_start date to avoid downloading the wrong instance
                for file in recording_data.get('recording_files', []):
                    file_start = file.get('recording_start', '')
                    file_date = file_start[:10] if file_start else None

                    # If we have date info, only accept files matching our expected date
                    if expected_date and file_date and file_date != expected_date:
                        logger.warning(f"   Skipping file with mismatched date: expected {expected_date}, got {file_date}")
                        continue

                    if file.get('file_type') == 'MP4' and not video_url:
                        video_url = file.get('download_url')
                    elif file.get('file_type') == 'TRANSCRIPT' and not transcript_url:
                        transcript_url = file.get('download_url')

                if not video_url:
                    # Fallback: if strict date matching found nothing, log clearly and try without date filter
                    logger.warning(f"   No MP4 found matching date {expected_date}. Available files:")
                    for file in recording_data.get('recording_files', []):
                        logger.warning(f"     - {file.get('file_type')} | start: {file.get('recording_start', 'unknown')} | status: {file.get('status', 'unknown')}")
                    raise Exception(f"No video file found matching expected date {expected_date} (UUID: {zoom_id})")

                zoom_client.download_file(video_url, video_path)
                logger.info(f"   Video downloaded: {video_filename}")

                if transcript_url:
                    try:
                        zoom_client.download_file(transcript_url, transcript_path)
                        logger.info(f"   Transcript downloaded")
                    except Exception as e:
                        logger.warning(f"   Transcript download failed (non-critical): {e}")

                # 3. UPLOAD to YouTube
                youtube_url = None
                video_id = None

                try:
                    logger.info(f"   Uploading to YouTube...")
                    description = f"{topic}\n\nRecorded: {start_time}\nTeam: {team}\nPlaylist: {playlist}"

                    video_id = self.youtube.upload_video(
                        file_path=video_path,
                        title=youtube_title,
                        description=description,
                        privacy_status="unlisted"
                    )
                    youtube_url = f"https://youtu.be/{video_id}"
                    logger.info(f"   YouTube: {youtube_url}")
                except googleapiclient.errors.HttpError as e:
                    raw_error = e.content.decode('utf-8') if hasattr(e, 'content') else str(e)
                    logger.error(f"YOUTUBE UPLOAD HTTP ERROR: {e.resp.status} - {e.reason} - {raw_error}")
                    # Detect quota exceeded
                    if 'quotaExceeded' in raw_error or 'dailyLimitExceeded' in raw_error:
                        self._pause_youtube_for_quota()
                        db.update_recording(zoom_id, {"status": "APPROVED", "error_message": "YouTube quota exceeded, will retry"})
                    else:
                        db.update_recording(zoom_id, {"status": "ERROR", "error_message": f"YouTube API Error: {e.reason} - {raw_error}"})
                    self._safe_cleanup_files(video_path, transcript_path)
                    continue
                except Exception as e:
                    logger.error(f"YOUTUBE UPLOAD UNKNOWN ERROR: {e}")
                    db.update_recording(zoom_id, {"status": "ERROR", "error_message": str(e)})
                    self._safe_cleanup_files(video_path, transcript_path)
                    continue

                # Update sheets with YouTube URL (non-critical)
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "PROCESSING", youtube_url=youtube_url)
                    except Exception:
                        pass

                # Upload captions (non-critical)
                if transcript_url and os.path.exists(transcript_path) and video_id:
                    try:
                        self.youtube.upload_caption(video_id, transcript_path, language='en')
                        logger.info(f"   Captions uploaded to YouTube")
                    except Exception as e:
                        logger.warning(f"   Caption upload failed (non-critical): {e}")

                # Add to playlist (CRITICAL - must succeed)
                playlist_added = False
                if video_id:
                    yt_playlist_id = self._get_playlist_id(playlist)
                    if yt_playlist_id:
                        for attempt in range(3):
                            try:
                                self.youtube.add_to_playlist(video_id, yt_playlist_id)
                                logger.info(f"   ✅ Added to playlist: {playlist} ({yt_playlist_id})")
                                playlist_added = True
                                break
                            except Exception as e:
                                logger.error(f"   ❌ Playlist add attempt {attempt+1}/3 failed: {e}")
                                if attempt < 2:
                                    import time
                                    time.sleep(5)  # Wait before retry
                        if not playlist_added:
                            logger.error(f"   ❌ PLAYLIST ADD FAILED after 3 attempts for {video_id} -> {playlist}")
                            db.add_log("ERROR", f"Playlist add failed: {zoom_id} -> {playlist} ({yt_playlist_id})")
                    else:
                        logger.error(f"   ❌ No YouTube playlist ID found for: {playlist}")

                # 3. UPLOAD video + transcript directly to Drive from local file
                drive_url = None
                drive_video_id = None
                drive_folder_id, transcript_folder_id = self._get_drive_folders(playlist)

                if self.drive:
                    # Upload video to Drive
                    if drive_folder_id and os.path.exists(video_path):
                        logger.info(f"   Uploading video to Drive...")
                        try:
                            drive_video_id = self.drive.upload_file(video_path, video_filename, drive_folder_id)
                            drive_url = f"https://drive.google.com/file/d/{drive_video_id}/view"
                            logger.info(f"   Drive Video: {drive_url}")
                        except Exception as e:
                            logger.warning(f"   Drive video upload failed (non-critical): {e}")
                    else:
                        logger.warning(f"   No Drive folder for playlist '{playlist}' or video not found.")

                    # Upload transcript to Drive
                    if transcript_folder_id and transcript_url and os.path.exists(transcript_path):
                        try:
                            self.drive.upload_file(transcript_path, transcript_filename, transcript_folder_id)
                            logger.info(f"   Transcript uploaded to Drive")
                        except Exception as e:
                            logger.warning(f"   Transcript Drive upload failed (non-critical): {e}")

                # 4. CLEANUP local files
                self._safe_cleanup_files(video_path, transcript_path)

                # 5. UPDATE status to COMPLETED immediately
                deletion_ready_time = datetime.now() + timedelta(hours=config.DELETE_DELAY_HOURS)
                update_data = {
                    "status": "COMPLETED",
                    "processed_at": datetime.now().isoformat(),
                    "youtube_url": youtube_url,
                    "drive_url": drive_url,
                    "deletion_ready_at": deletion_ready_time.isoformat(),
                    "zoom_deletion_status": "PENDING"
                }
                if drive_video_id:
                    update_data["drive_uploaded_at"] = datetime.now().isoformat()

                db.update_recording(zoom_id, update_data)
                db.add_log("INFO", f"COMPLETED: {zoom_id} - {youtube_title} | YT: {youtube_url} | Drive: {drive_url or 'N/A'}")
                logger.info(f"   COMPLETED: {zoom_id} (YT: {'✅' if youtube_url else '❌'}, Drive: {'✅' if drive_url else '❌'})")

                # Update sheets to COMPLETED
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "COMPLETED", youtube_url=youtube_url, drive_url=drive_url)
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f"   Processing Failed {zoom_id}: {e}")
                logger.error(f"   Traceback:\n{traceback.format_exc()}")
                with open("traceback_error.txt", "w") as f:
                    f.write(traceback.format_exc())

                retry_count = task.get('retry_count') or 0
                db.update_recording(zoom_id, {
                    "status": "ERROR",
                    "error_message": str(e)[:500],
                    "retry_count": retry_count
                })
                db.add_log("ERROR", f"Failed {zoom_id}: {e}")

                # Update sheets (non-critical)
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "ERROR")
                    except Exception:
                        pass

                # Clean up any leftover files
                video_path_check = os.path.join(config.DOWNLOAD_DIR, f"*{zoom_id}*")
                self._safe_cleanup_files(
                    os.path.join(config.DOWNLOAD_DIR, task.get('video_filename', '')),
                    os.path.join(config.DOWNLOAD_DIR, task.get('transcript_filename', ''))
                )

        if tasks:
            logger.info("Done processing approved tasks")

    def _process_compressing_queue(self):
        """Handle videos stuck in YOUTUBE_COMPRESSING - re-download from Zoom and upload to Drive."""
        tasks = db.get_compressing()
        if not tasks:
            return

        logger.info(f"Found {len(tasks)} tasks in YOUTUBE_COMPRESSING - uploading to Drive via Zoom re-download")

        for task in tasks:
            zoom_id = task['zoom_id']
            meeting_id = task.get('meeting_id') or zoom_id
            youtube_url = task.get('youtube_url')
            topic = task['topic']
            start_time = task['start_time']
            playlist = task.get('playlist', 'General')
            account_name = task.get('account_name', 'Zoom Account 1')

            if not youtube_url:
                db.update_recording(zoom_id, {"status": "ERROR", "error_message": "Missing YouTube URL"})
                continue

            logger.info(f"Processing compressing task: {zoom_id} - {topic}")

            zoom_client = self.zoom_clients.get(account_name)
            if not zoom_client:
                logger.error(f"   Zoom client not found for {account_name}")
                continue

            try:
                names = generate_names(topic, start_time)
                video_filename = names['video_filename']
                transcript_filename = names['transcript_filename']
                video_path = os.path.join(DOWNLOAD_DIR, video_filename)
                transcript_path = os.path.join(DOWNLOAD_DIR, transcript_filename)

                # Re-fetch Zoom recording details for download URLs
                encoded_id = self._encode_uuid_for_zoom(zoom_id)
                recording_data = zoom_client.get_recording_details(encoded_id)
                if not recording_data and str(zoom_id) == str(meeting_id):
                    logger.warning(f"   UUID lookup failed, trying meeting ID fallback: {meeting_id}")
                    recording_data = zoom_client.get_recording_details(meeting_id)

                if not recording_data:
                    # Zoom recording expired - can't get Drive copy, mark COMPLETED without Drive
                    logger.warning(f"   Zoom recording not found (expired?) - marking COMPLETED without Drive")
                    deletion_ready_time = datetime.now() + timedelta(hours=config.DELETE_DELAY_HOURS)
                    db.update_recording(zoom_id, {
                        "status": "COMPLETED",
                        "deletion_ready_at": deletion_ready_time.isoformat(),
                        "zoom_deletion_status": "PENDING"
                    })
                    continue

                # Extract expected date for verification
                expected_date = start_time[:10] if start_time else None

                video_url = None
                transcript_url = None
                for file in recording_data.get('recording_files', []):
                    file_start = file.get('recording_start', '')
                    file_date = file_start[:10] if file_start else None

                    if expected_date and file_date and file_date != expected_date:
                        logger.warning(f"   Skipping file with mismatched date: expected {expected_date}, got {file_date}")
                        continue

                    if file.get('file_type') == 'MP4' and not video_url:
                        video_url = file.get('download_url')
                    elif file.get('file_type') == 'TRANSCRIPT':
                        transcript_url = file.get('download_url')

                if not video_url:
                    logger.error(f"   No MP4 found in Zoom recording: {zoom_id}")
                    continue

                # Re-download video from Zoom
                logger.info(f"   Re-downloading from Zoom for Drive upload...")
                zoom_client.download_file(video_url, video_path)
                logger.info(f"   Downloaded: {video_filename}")

                if transcript_url:
                    try:
                        zoom_client.download_file(transcript_url, transcript_path)
                    except Exception:
                        pass

                # Upload to Drive
                drive_url = None
                drive_video_id = None
                drive_folder_id, transcript_folder_id = self._get_drive_folders(playlist)

                if self.drive and drive_folder_id:
                    try:
                        logger.info(f"   Uploading video to Drive...")
                        drive_video_id = self.drive.upload_file(video_path, video_filename, drive_folder_id)
                        drive_url = f"https://drive.google.com/file/d/{drive_video_id}/view"
                        logger.info(f"   Drive: {drive_url}")
                    except Exception as e:
                        logger.warning(f"   Drive video upload failed: {e}")

                if transcript_url and os.path.exists(transcript_path) and transcript_folder_id and self.drive:
                    try:
                        self.drive.upload_file(transcript_path, transcript_filename, transcript_folder_id)
                    except Exception:
                        pass

                # Cleanup local files
                self._safe_cleanup_files(video_path, transcript_path)

                # Mark COMPLETED
                deletion_ready_time = datetime.now() + timedelta(hours=config.DELETE_DELAY_HOURS)
                update_data = {
                    "status": "COMPLETED",
                    "drive_url": drive_url,
                    "deletion_ready_at": deletion_ready_time.isoformat(),
                    "zoom_deletion_status": "PENDING"
                }
                if drive_video_id:
                    update_data["drive_uploaded_at"] = datetime.now().isoformat()
                db.update_recording(zoom_id, update_data)
                db.add_log("INFO", f"COMPLETED (compressing queue): {zoom_id} | Drive: {drive_url or 'N/A'}")
                logger.info(f"   COMPLETED: {zoom_id} (Drive: {'✅' if drive_url else '❌'})")

                # Update Sheets
                sheet_row = self._find_sheet_row(zoom_id)
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "COMPLETED", youtube_url=youtube_url, drive_url=drive_url)
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f"   Compressing queue error for {zoom_id}: {e}")
                logger.error(traceback.format_exc())
                retry_count = task.get('retry_count', 0)
                if retry_count < 3:
                    db.update_recording(zoom_id, {"retry_count": retry_count + 1})
                else:
                    db.update_recording(zoom_id, {
                        "status": "ERROR",
                        "error_message": f"Drive upload failed after retries: {str(e)[:200]}"
                    })
                self._safe_cleanup_files(
                    os.path.join(DOWNLOAD_DIR, task.get('video_filename', '') or ''),
                    os.path.join(DOWNLOAD_DIR, task.get('transcript_filename', '') or '')
                )

    def _safe_cleanup_files(self, *paths):
        """Safely remove files, ignoring errors."""
        for path in paths:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

    def _cleanup_zoom_recordings(self):
        """Check for completed recordings that are ready for Zoom deletion after safety period."""
        try:
            ready_for_deletion = db.get_ready_for_zoom_deletion(delay_hours=6)

            if not ready_for_deletion:
                logger.info("   No recordings ready for Zoom deletion")
                return

            logger.info(f"   Found {len(ready_for_deletion)} recording(s) ready for Zoom deletion")

            for task in ready_for_deletion:
                zoom_id = task['zoom_id']  # UUID
                meeting_id = task.get('meeting_id') or zoom_id
                topic = task['topic']
                youtube_url = task.get('youtube_url')
                drive_url = task.get('drive_url')
                account_name = task.get('account_name', 'Zoom Account 1')

                logger.info(f"   Verifying {zoom_id} - {topic}")

                zoom_client = self.zoom_clients.get(account_name)
                if not zoom_client:
                    logger.error(f"      Zoom client not found for account: {account_name}")
                    continue

                # RE-VERIFY uploads before deletion
                youtube_still_exists = False
                drive_still_exists = False

                if youtube_url and self.youtube:
                    try:
                        video_id = youtube_url.split('/')[-1]
                        yt_status = self.youtube.get_video_status(video_id)
                        if yt_status in ['uploaded', 'processed']:
                            youtube_still_exists = True
                            logger.info(f"      YouTube verified: {yt_status}")
                        else:
                            logger.warning(f"      YouTube status unexpected: {yt_status}")
                    except Exception as e:
                        logger.error(f"      YouTube re-verification failed: {e}")

                if drive_url:
                    drive_still_exists = True
                    logger.info(f"      Drive URL present: {drive_url}")

                # Only delete if BOTH uploads are verified
                if youtube_still_exists and drive_still_exists:
                    try:
                        logger.info(f"      Deleting from Zoom...")
                        encoded_id = self._encode_uuid_for_zoom(zoom_id)
                        if zoom_client.delete_recording(encoded_id, action="trash"):
                            logger.info(f"      Zoom recording deleted successfully")
                            db.update_recording(zoom_id, {
                                "zoom_deletion_status": "DELETED",
                                "zoom_deleted_at": datetime.now().isoformat()
                            })
                            db.add_log("INFO", f"Deleted from Zoom: {zoom_id} - {topic}")
                        else:
                            logger.warning(f"      Zoom deletion returned False")
                            db.update_recording(zoom_id, {"zoom_deletion_status": "FAILED"})
                    except Exception as e:
                        logger.error(f"      Zoom deletion failed: {e}")
                        db.update_recording(zoom_id, {
                            "zoom_deletion_status": "FAILED",
                            "zoom_deletion_error": str(e)[:500]
                        })
                else:
                    logger.error(f"      SAFETY CHECK FAILED - Not deleting from Zoom")
                    logger.error(f"         YouTube: {youtube_still_exists}, Drive: {drive_still_exists}")
                    db.update_recording(zoom_id, {
                        "zoom_deletion_status": "VERIFICATION_FAILED",
                        "zoom_deletion_error": f"YT:{youtube_still_exists}, Drive:{drive_still_exists}"
                    })

        except Exception as e:
            logger.error(f"   Cleanup phase error: {e}")
            logger.error(f"   Traceback:\n{traceback.format_exc()}")


# Initializer for fastAPI to call
service = BackgroundService()


def start_service():
    if not service.is_alive():
        service.start()
