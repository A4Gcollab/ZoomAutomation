
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

# Constants for resilience
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30
YOUTUBE_QUOTA_RESET_HOURS = 24
ERROR_RECOVERY_INTERVAL_MINUTES = 30


class BackgroundService(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        self.zoom_clients = {}
        self.youtube = None
        self.drive = None
        self.sheets = None
        self.last_error_recovery = None
        self.youtube_quota_exceeded_at = None  # Track when quota was hit

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

                # 1. AUTO-RECOVERY: Reset ERROR/PROCESSING records periodically
                self._auto_recover_stuck_records()

                # 2. SCAN (Ingestion)
                logger.info("Phase 1: Scanning Zoom for new recordings...")
                self._scan_zoom()

                # 3. PROCESS (Approvals) - Skip if YouTube quota exceeded
                if self._can_use_youtube():
                    logger.info("Phase 2: Processing approved tasks...")
                    self._process_queue()
                else:
                    logger.warning("Phase 2: SKIPPED - YouTube quota exceeded, waiting for reset...")

                # 4. CLEANUP (Delayed Zoom Deletions)
                logger.info("Phase 3: Checking for recordings ready for Zoom deletion...")
                self._cleanup_zoom_recordings()

                # 5. SLEEP
                logger.info(f"✅ Cycle #{cycle_count} complete. Sleeping 60s...")
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

    def _can_use_youtube(self):
        """Check if YouTube API is available (not quota exceeded)."""
        if not self.youtube_quota_exceeded_at:
            return True

        # Check if 24 hours have passed since quota was exceeded
        hours_since = (datetime.now() - self.youtube_quota_exceeded_at).total_seconds() / 3600
        if hours_since >= YOUTUBE_QUOTA_RESET_HOURS:
            logger.info("YouTube quota reset period passed. Resuming YouTube operations.")
            self.youtube_quota_exceeded_at = None
            return True

        remaining = YOUTUBE_QUOTA_RESET_HOURS - hours_since
        logger.info(f"YouTube quota exceeded. {remaining:.1f} hours until reset.")
        return False

    def _auto_recover_stuck_records(self):
        """Automatically recover records stuck in ERROR or PROCESSING status."""
        try:
            now = datetime.now()

            # Only run recovery every 30 minutes
            if self.last_error_recovery:
                minutes_since = (now - self.last_error_recovery).total_seconds() / 60
                if minutes_since < ERROR_RECOVERY_INTERVAL_MINUTES:
                    return

            self.last_error_recovery = now
            cur = db.conn.cursor()

            # 1. Reset ERROR records back to PENDING (so they can be re-approved)
            cur.execute("""
                UPDATE recordings
                SET status = 'PENDING', error_message = NULL
                WHERE status = 'ERROR'
            """)
            error_count = cur.rowcount

            # 2. Reset PROCESSING records that have been stuck for > 1 hour
            one_hour_ago = (now - timedelta(hours=1)).isoformat()
            cur.execute("""
                UPDATE recordings
                SET status = 'PENDING'
                WHERE status = 'PROCESSING'
                AND (processed_at IS NULL OR processed_at < ?)
            """, (one_hour_ago,))
            stuck_count = cur.rowcount

            db.conn.commit()

            if error_count > 0 or stuck_count > 0:
                logger.info(f"🔄 Auto-Recovery: Reset {error_count} ERROR and {stuck_count} stuck PROCESSING records to PENDING")
                db.add_log("INFO", f"Auto-Recovery: Reset {error_count} ERROR, {stuck_count} stuck records")

        except Exception as e:
            logger.error(f"Auto-recovery failed: {e}")

    def _init_clients(self):
        """Initialize API clients with retry logic. Non-blocking - failures are logged but don't stop the service."""
        logger.info("Initializing API clients...")

        # YouTube
        if not self.youtube:
            for attempt in range(MAX_RETRIES):
                try:
                    logger.info("  Initializing YouTube client...")
                    self.youtube = YouTubeClient(config.YOUTUBE_CLIENT_SECRET_PATH, config.YOUTUBE_TOKEN_PATH)
                    logger.info("  ✅ YouTube client ready")
                    break
                except Exception as e:
                    logger.error(f"  ❌ YouTube client failed (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
                    self.youtube = None

        # Drive
        if not self.drive:
            for attempt in range(MAX_RETRIES):
                try:
                    logger.info("  Initializing Drive client...")
                    self.drive = DriveClient(
                        auth_mode='user',
                        token_path=config.DRIVE_TOKEN_PATH,
                        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH
                    )
                    logger.info("  ✅ Drive client ready")
                    break
                except Exception as e:
                    logger.error(f"  ❌ Drive client failed (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(5)
                    self.drive = None

        # Zoom Clients
        if not self.zoom_clients:
            try:
                logger.info("  Initializing Zoom clients...")
                for i, creds in enumerate(config.ZOOM_ACCOUNTS, 1):
                    name = f"Zoom Account {i}"
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
                from google.oauth2.service_account import Credentials

                scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_file(config.DRIVE_SERVICE_ACCOUNT_FILE, scopes=scopes)
                self.sheets = SheetManager(creds, config.GOOGLE_SHEET_ID)
                logger.info("  ✅ Google Sheets client ready")
            except Exception as e:
                logger.error(f"  ❌ Google Sheets client failed: {e}")
                self.sheets = None

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

    def _get_playlist_id(self, playlist_name):
        """Get YouTube playlist ID from playlist name."""
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
        except Exception as e:
            logger.error(f"Failed to get playlist ID: {e}")
        return None

    def _scan_zoom(self):
        """Scan Zoom for new recordings with error handling."""
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
                            try:
                                r['account_name'] = name
                                uuid = r.get('uuid', str(r['id']))

                                team, playlist = self._resolve_team_playlist(r['id'])
                                if team: r['team'] = team
                                if playlist: r['playlist'] = playlist

                                if db.add_recording(uuid, r):
                                    count += 1
                                    logger.info(f"   ✅ New: {r.get('topic', '?')[:40]}")
                                    if team:
                                        logger.info(f"      Auto-Matched -> {team} / {playlist}")

                                    if self.sheets:
                                        try:
                                            self.sheets.add_recording(r)
                                        except Exception:
                                            pass  # Non-critical
                            except Exception as rec_err:
                                logger.warning(f"   ⚠️ Error processing recording: {rec_err}")
                    except Exception as user_err:
                        logger.warning(f"   ⚠️ Error scanning user {user.get('email')}: {user_err}")
            except Exception as e:
                logger.error(f"Zoom Scan Error ({name}): {e}")

        if count > 0:
            logger.info(f"   📥 Added {count} new recordings to queue")

    def _process_queue(self):
        """Process approved recordings with comprehensive error handling."""
        cur = db.conn.cursor()
        cur.execute("SELECT * FROM recordings WHERE status = 'APPROVED'")
        tasks = cur.fetchall()

        logger.info(f"Found {len(tasks)} approved tasks to process")

        for task in tasks:
            task = dict(task)
            zoom_id = task['zoom_id']
            meeting_id = task.get('meeting_id', zoom_id)
            topic = task['topic']
            start_time = task['start_time']
            team = task.get('team', 'Unknown')
            playlist = task.get('playlist', 'General')
            account_name = task.get('account_name', 'Zoom Account 1')

            display_id = zoom_id[:20] + '...' if len(zoom_id) > 20 else zoom_id
            logger.info(f"▶️  Processing: {topic} ({display_id})")

            # Mark as processing with timestamp
            db.update_recording(zoom_id, {
                "status": "PROCESSING",
                "processed_at": datetime.now().isoformat()
            })

            try:
                self._process_single_recording(task, zoom_id, topic, start_time, team, playlist, account_name)

            except Exception as e:
                error_msg = str(e)
                logger.error(f"   ❌ Processing Failed: {error_msg}")

                # Check if it's a YouTube quota error
                if 'quota' in error_msg.lower():
                    logger.error("   🚫 YouTube quota exceeded! Pausing YouTube operations for 24 hours.")
                    self.youtube_quota_exceeded_at = datetime.now()
                    # Reset to APPROVED so it can be retried after quota reset
                    db.update_recording(zoom_id, {
                        "status": "APPROVED",
                        "error_message": "YouTube quota exceeded - will retry after reset"
                    })
                else:
                    # For other errors, mark as ERROR (will be auto-recovered)
                    db.update_recording(zoom_id, {
                        "status": "ERROR",
                        "error_message": error_msg[:500]  # Truncate long errors
                    })
                    db.add_log("ERROR", f"Failed {zoom_id}: {error_msg[:200]}")

    def _process_single_recording(self, task, zoom_id, topic, start_time, team, playlist, account_name):
        """Process a single recording with retry logic."""
        import json
        import urllib.parse

        # Generate names
        names = generate_names(topic, start_time)
        video_filename = names['video_filename']
        youtube_title = names['youtube_title']
        transcript_filename = names['transcript_filename']

        logger.info(f"   Generated title: {youtube_title}")

        # Get Zoom client
        zoom_client = self.zoom_clients.get(account_name)
        if not zoom_client:
            raise Exception(f"Zoom client not found: {account_name}")

        # 1. DOWNLOAD from Zoom (with retry)
        logger.info(f"   📥 Downloading from Zoom...")
        video_path = os.path.join(DOWNLOAD_DIR, video_filename)
        transcript_path = os.path.join(DOWNLOAD_DIR, transcript_filename)

        recording_data = None
        stored_metadata = task.get('metadata')
        if stored_metadata:
            try:
                recording_data = json.loads(stored_metadata) if isinstance(stored_metadata, str) else stored_metadata
            except:
                pass

        if not recording_data or 'recording_files' not in recording_data:
            encoded_uuid = urllib.parse.quote(urllib.parse.quote(zoom_id, safe=''), safe='')
            recording_data = zoom_client.get_meeting_recordings(encoded_uuid)

        if not recording_data:
            raise Exception("Could not fetch recording data from Zoom")

        video_url = None
        transcript_url = None
        for file in recording_data.get('recording_files', []):
            if file.get('file_type') == 'MP4':
                video_url = file.get('download_url')
            elif file.get('file_type') == 'TRANSCRIPT':
                transcript_url = file.get('download_url')

        if not video_url:
            raise Exception("No video file found in recording")

        # Download with retry
        for attempt in range(MAX_RETRIES):
            try:
                zoom_client.download_file(video_url, video_path)
                logger.info(f"   ✅ Video downloaded")
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"   ⚠️ Download retry {attempt+1}: {e}")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise

        if transcript_url:
            try:
                zoom_client.download_file(transcript_url, transcript_path)
                logger.info(f"   ✅ Transcript downloaded")
            except Exception:
                pass  # Transcript is optional

        # 2. UPLOAD to YouTube (with retry)
        logger.info(f"   📤 Uploading to YouTube...")
        description = f"{topic}\n\nRecorded: {start_time}\nTeam: {team}\nPlaylist: {playlist}"

        video_id = None
        for attempt in range(MAX_RETRIES):
            try:
                video_id = self.youtube.upload_video(
                    file_path=video_path,
                    title=youtube_title,
                    description=description,
                    privacy_status="unlisted"
                )
                break
            except Exception as e:
                if 'quota' in str(e).lower():
                    raise  # Don't retry quota errors
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"   ⚠️ YouTube upload retry {attempt+1}: {e}")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise

        youtube_url = f"https://youtu.be/{video_id}"
        logger.info(f"   ✅ YouTube: {youtube_url}")

        # Add to playlist (non-critical)
        try:
            playlist_id = self._get_playlist_id(playlist)
            if playlist_id:
                self.youtube.add_to_playlist(video_id, playlist_id)
                logger.info(f"   ✅ Added to playlist: {playlist}")
        except Exception as e:
            logger.warning(f"   ⚠️ Playlist add failed (non-critical): {e}")

        # Upload captions (non-critical)
        if transcript_url and os.path.exists(transcript_path):
            try:
                self.youtube.upload_caption(video_id, transcript_path, language='en')
                logger.info(f"   ✅ Captions uploaded")
            except Exception:
                pass

        # 3. UPLOAD to Drive (with retry)
        logger.info(f"   📤 Uploading to Drive...")
        drive_folder_id, transcript_folder_id = self._get_drive_folders(playlist)

        if not drive_folder_id:
            logger.warning(f"   ⚠️ No Drive folder configured for {playlist}, using default")
            drive_folder_id = config.DRIVE_ROOT_FOLDER_ID
            transcript_folder_id = config.DRIVE_ROOT_FOLDER_ID

        drive_video_id = None
        for attempt in range(MAX_RETRIES):
            try:
                drive_video_id = self.drive.upload_file(video_path, video_filename, drive_folder_id)
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"   ⚠️ Drive upload retry {attempt+1}: {e}")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    raise

        drive_url = f"https://drive.google.com/file/d/{drive_video_id}/view"
        logger.info(f"   ✅ Drive: {drive_url}")

        # Upload transcript to Drive (non-critical)
        if os.path.exists(transcript_path) and transcript_folder_id:
            try:
                self.drive.upload_file(transcript_path, transcript_filename, transcript_folder_id)
                logger.info(f"   ✅ Transcript backed up to Drive")
            except Exception:
                pass

        # 4. Schedule Zoom deletion
        deletion_ready_time = datetime.now() + timedelta(hours=config.DELETE_DELAY_HOURS)
        logger.info(f"   ⏰ Zoom deletion scheduled for: {deletion_ready_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 5. Cleanup local files
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(transcript_path):
                os.remove(transcript_path)
            logger.info(f"   🗑️ Local files cleaned up")
        except Exception:
            pass

        # 6. Mark as COMPLETED
        db.update_recording(zoom_id, {
            "status": "COMPLETED",
            "youtube_url": youtube_url,
            "drive_url": drive_url,
            "processed_at": datetime.now().isoformat(),
            "deletion_ready_at": deletion_ready_time.isoformat(),
            "zoom_deletion_status": "PENDING"
        })
        db.add_log("INFO", f"✅ Completed: {youtube_title}")
        logger.info(f"   ✅ COMPLETED")

        # Update sheets (non-critical)
        if self.sheets:
            try:
                self.sheets.log_completion(zoom_id, topic, youtube_url, drive_url)
            except Exception:
                pass

    def _cleanup_zoom_recordings(self):
        """Check for completed recordings that are ready for Zoom deletion.

        IMPORTANT: Only deletes from Zoom after verifying:
        1. At least 24 hours have passed since completion
        2. YouTube video exists and is accessible
        3. Drive file exists and is not in trash
        """
        try:
            cur = db.conn.cursor()
            cur.execute("""
                SELECT * FROM recordings
                WHERE status = 'COMPLETED'
                AND deletion_ready_at IS NOT NULL
                AND deletion_ready_at <= ?
                AND (zoom_deletion_status IS NULL OR zoom_deletion_status = 'PENDING')
            """, (datetime.now().isoformat(),))

            ready_for_deletion = cur.fetchall()

            if not ready_for_deletion:
                logger.info("   No recordings ready for Zoom deletion")
                return

            logger.info(f"   Found {len(ready_for_deletion)} recording(s) ready for Zoom deletion verification")

            for task in ready_for_deletion:
                task = dict(task)
                zoom_id = task['zoom_id']
                topic = task['topic'][:40]
                youtube_url = task.get('youtube_url')
                drive_url = task.get('drive_url')
                account_name = task.get('account_name', 'Zoom Account 1')

                # Skip if no backups exist
                if not youtube_url or not drive_url:
                    logger.warning(f"   ⚠️ Skipping {topic} - missing backup URLs")
                    db.update_recording(zoom_id, {
                        "zoom_deletion_status": "SKIPPED",
                        "zoom_deletion_error": "Missing backup URLs"
                    })
                    continue

                # 1. VERIFY YOUTUBE VIDEO EXISTS
                youtube_verified = False
                try:
                    # Extract video ID from URL (youtu.be/ID or youtube.com/watch?v=ID)
                    video_id = None
                    if 'youtu.be/' in youtube_url:
                        video_id = youtube_url.split('youtu.be/')[-1].split('?')[0]
                    elif 'v=' in youtube_url:
                        video_id = youtube_url.split('v=')[-1].split('&')[0]

                    if video_id and self.youtube:
                        result = self.youtube.verify_video_exists(video_id)
                        if result.get('exists'):
                            logger.info(f"   ✅ YouTube verified: {result.get('title', 'N/A')[:30]}")
                            youtube_verified = True
                        else:
                            logger.warning(f"   ⚠️ YouTube verification failed: {result.get('error')}")
                    else:
                        logger.warning(f"   ⚠️ Could not extract video ID from {youtube_url}")
                except Exception as e:
                    logger.error(f"   ❌ YouTube verification error: {e}")

                # 2. VERIFY DRIVE FILE EXISTS
                drive_verified = False
                try:
                    # Extract file ID from URL (drive.google.com/file/d/ID/view)
                    file_id = None
                    if '/file/d/' in drive_url:
                        file_id = drive_url.split('/file/d/')[-1].split('/')[0]
                    elif 'id=' in drive_url:
                        file_id = drive_url.split('id=')[-1].split('&')[0]

                    if file_id and self.drive:
                        result = self.drive.verify_file_exists(file_id)
                        if result.get('exists'):
                            logger.info(f"   ✅ Drive verified: {result.get('name', 'N/A')[:30]}")
                            drive_verified = True
                        else:
                            logger.warning(f"   ⚠️ Drive verification failed: {result.get('error')}")
                    else:
                        logger.warning(f"   ⚠️ Could not extract file ID from {drive_url}")
                except Exception as e:
                    logger.error(f"   ❌ Drive verification error: {e}")

                # 3. ONLY DELETE IF BOTH VERIFIED
                if not youtube_verified or not drive_verified:
                    logger.warning(f"   ⚠️ Skipping Zoom deletion for {topic} - verification failed")
                    logger.warning(f"      YouTube: {'✅' if youtube_verified else '❌'}, Drive: {'✅' if drive_verified else '❌'}")
                    db.update_recording(zoom_id, {
                        "zoom_deletion_status": "VERIFICATION_FAILED",
                        "zoom_deletion_error": f"YT:{youtube_verified}, Drive:{drive_verified}"
                    })
                    continue

                # Both verified - proceed with Zoom deletion
                zoom_client = self.zoom_clients.get(account_name)
                if not zoom_client:
                    logger.warning(f"   ⚠️ Zoom client not found: {account_name}")
                    continue

                try:
                    logger.info(f"   🗑️ Deleting from Zoom: {topic}...")
                    if zoom_client.delete_recording(zoom_id, action="delete"):
                        db.update_recording(zoom_id, {
                            "zoom_deletion_status": "DELETED",
                            "zoom_deleted_at": datetime.now().isoformat(),
                            "youtube_verified": True,
                            "drive_verified": True
                        })
                        logger.info(f"   ✅ Successfully deleted from Zoom (backups verified)")
                        db.add_log("INFO", f"Deleted from Zoom: {topic} (verified)")
                except Exception as e:
                    logger.error(f"   ❌ Zoom deletion failed: {e}")
                    db.update_recording(zoom_id, {
                        "zoom_deletion_status": "FAILED",
                        "zoom_deletion_error": str(e)[:200]
                    })

        except Exception as e:
            logger.error(f"   ❌ Cleanup phase error: {e}")


# Singleton service instance
service = BackgroundService()

def start_service():
    if not service.is_alive():
        service.start()
