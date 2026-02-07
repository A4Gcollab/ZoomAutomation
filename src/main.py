
import logging
import time
import threading
import traceback
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
                    auth_mode='user',
                    token_path=config.DRIVE_TOKEN_PATH,
                    client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH
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

    def _resolve_team_playlist(self, meeting_id):
        """Match Meeting ID to Config."""
        import json
        from src.config import PLAYLIST_CONFIG_PATH

        if not PLAYLIST_CONFIG_PATH.exists():
            return None, None

        try:
            with open(PLAYLIST_CONFIG_PATH, 'r') as f:
                data = json.load(f)
                meeting_id = str(meeting_id)
                for pl in data.get('playlists', []):
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

                            team, playlist = self._resolve_team_playlist(r['id'])
                            if team:
                                r['team'] = team
                            if playlist:
                                r['playlist'] = playlist

                            if db.add_recording(str(r['id']), r):
                                count += 1
                                if team:
                                    logger.info(f"Auto-Matched {r['id']} -> {team} / {playlist}")

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

    def _process_queue(self):
        tasks = db.get_approved()
        logger.info(f"Found {len(tasks)} approved tasks to process")

        for task in tasks:
            zoom_id = task['zoom_id']
            topic = task['topic']
            start_time = task['start_time']
            team = task.get('team', 'Unknown')
            playlist = task.get('playlist', 'General')
            account_name = task.get('account_name', 'Zoom Account 1')

            logger.info(f"Processing: {zoom_id} - {topic}")

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

                # 1. DOWNLOAD from Zoom
                logger.info(f"   Downloading from Zoom...")
                video_path = os.path.join(DOWNLOAD_DIR, video_filename)
                transcript_path = os.path.join(DOWNLOAD_DIR, transcript_filename)

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

                zoom_client.download_file(video_url, video_path)
                logger.info(f"   Video downloaded: {video_filename}")

                if transcript_url:
                    try:
                        zoom_client.download_file(transcript_url, transcript_path)
                        logger.info(f"   Transcript downloaded")
                    except Exception as e:
                        logger.warning(f"   Transcript download failed (non-critical): {e}")

                # 2. UPLOAD to YouTube
                youtube_url = None
                video_id = None

                if self._is_youtube_quota_paused():
                    # Put back to APPROVED - will retry next time quota resets
                    db.update_recording(zoom_id, {"status": "APPROVED", "error_message": "YouTube quota paused"})
                    self._safe_cleanup_files(video_path, transcript_path)
                    logger.warning(f"   Skipping {zoom_id}: YouTube quota paused")
                    continue

                if not self.youtube:
                    raise Exception("YouTube client not initialized")

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
                except Exception as yt_err:
                    error_str = str(yt_err)
                    # Detect quota exceeded
                    if 'quotaExceeded' in error_str or 'dailyLimitExceeded' in error_str:
                        self._pause_youtube_for_quota()
                        db.update_recording(zoom_id, {"status": "APPROVED", "error_message": "YouTube quota exceeded, will retry"})
                        self._safe_cleanup_files(video_path, transcript_path)
                        continue
                    raise  # Re-raise non-quota errors

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

                # Add to playlist (non-critical)
                if video_id:
                    try:
                        self.youtube.add_to_playlist(video_id, playlist)
                        logger.info(f"   Added to playlist: {playlist}")
                    except Exception as e:
                        logger.warning(f"   Playlist add failed (non-critical): {e}")

                # 3. UPLOAD to Drive (Backup)
                drive_url = None
                drive_video_id = None

                if not self.drive:
                    logger.warning("   Drive client not initialized, skipping Drive upload")
                else:
                    try:
                        logger.info(f"   Uploading to Drive...")
                        drive_folder_id, transcript_folder_id = self._get_drive_folders(playlist)

                        if not drive_folder_id:
                            logger.warning(f"   No Drive folder for playlist '{playlist}'. Skipping Drive upload.")
                        else:
                            drive_video_id = self.drive.upload_file(video_path, video_filename, drive_folder_id)
                            drive_url = f"https://drive.google.com/file/d/{drive_video_id}/view"
                            logger.info(f"   Drive Video: {drive_url}")

                            # Upload transcript to transcript folder (non-critical)
                            if os.path.exists(transcript_path) and transcript_folder_id:
                                try:
                                    self.drive.upload_file(transcript_path, transcript_filename, transcript_folder_id)
                                    logger.info(f"   Transcript backed up to Drive")
                                except Exception as e:
                                    logger.warning(f"   Transcript Drive upload failed (non-critical): {e}")

                            # Update sheets with Drive URL (non-critical)
                            if self.sheets and sheet_row:
                                try:
                                    self.sheets.update_row_status(sheet_row, "PROCESSING", youtube_url=youtube_url, drive_url=drive_url)
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.error(f"   Drive upload failed: {e}")
                        # Continue - YouTube upload succeeded, Drive is secondary

                # 4. VERIFY UPLOADS
                logger.info(f"   Verifying uploads...")
                youtube_verified = False
                drive_verified = False

                if video_id and self.youtube:
                    try:
                        yt_status = self.youtube.get_video_status(video_id)
                        if yt_status in ['uploaded', 'processed']:
                            youtube_verified = True
                            logger.info(f"   YouTube verified: {yt_status}")
                        else:
                            logger.warning(f"   YouTube status: {yt_status}")
                    except Exception as e:
                        logger.warning(f"   YouTube verification failed (non-critical): {e}")

                if drive_video_id:
                    drive_verified = True
                    logger.info(f"   Drive verified")

                # 5. SCHEDULE DELAYED DELETION
                if youtube_verified and drive_verified:
                    deletion_ready_time = datetime.now() + timedelta(hours=config.DELETE_DELAY_HOURS)
                    logger.info(f"   Zoom deletion scheduled for: {deletion_ready_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    db.update_recording(zoom_id, {
                        "deletion_ready_at": deletion_ready_time.isoformat(),
                        "zoom_deletion_status": "PENDING"
                    })
                else:
                    logger.warning(f"   Uploads not fully verified - Zoom deletion NOT scheduled")
                    logger.warning(f"      YouTube: {youtube_verified}, Drive: {drive_verified}")

                # 6. CLEANUP local files
                self._safe_cleanup_files(video_path, transcript_path)

                # 7. UPDATE status
                update_data = {
                    "status": "COMPLETED",
                    "processed_at": datetime.now().isoformat()
                }
                if youtube_url:
                    update_data["youtube_url"] = youtube_url
                if drive_url:
                    update_data["drive_url"] = drive_url

                db.update_recording(zoom_id, update_data)
                db.add_log("INFO", f"Completed: {zoom_id} - {youtube_title}")
                logger.info(f"   COMPLETED: {zoom_id}")

                # Final sheets update (non-critical)
                if self.sheets and sheet_row:
                    try:
                        self.sheets.update_row_status(sheet_row, "COMPLETED", youtube_url=youtube_url or "", drive_url=drive_url or "")
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f"   Processing Failed {zoom_id}: {e}")
                logger.error(f"   Traceback:\n{traceback.format_exc()}")

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
                video_path_check = os.path.join(DOWNLOAD_DIR, f"*{zoom_id}*")
                self._safe_cleanup_files(
                    os.path.join(DOWNLOAD_DIR, task.get('video_filename', '')),
                    os.path.join(DOWNLOAD_DIR, task.get('transcript_filename', ''))
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
            ready_for_deletion = db.get_ready_for_deletion()

            if not ready_for_deletion:
                logger.info("   No recordings ready for Zoom deletion")
                return

            logger.info(f"   Found {len(ready_for_deletion)} recording(s) ready for Zoom deletion")

            for task in ready_for_deletion:
                zoom_id = task['zoom_id']
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
                        if zoom_client.delete_recording(zoom_id, action="delete"):
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
