

import logging
import time
import os
import sys
import json
import signal
from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# Env and Path Setup
from src.config import check_config, CHECK_INTERVAL, DATA_DIR, DOWNLOAD_DIR
import src.config as config

# Modules
from src.db import StateManager
from src.utils import generate_names
from src.history_logger import HistoryLogger
from src.lock import acquire_lock, release_lock
from src.notifications import notify_error, notify_success
from src.zoom_client import ZoomClient
from src.youtube_client import YouTubeClient
from src.drive_client import DriveClient
from src.sheets_integration import SheetManager
from src.sheet_schema_v2 import SheetSchemaV2
from src.monitor import check_disk_space, cleanup_old_files, cleanup_zoom_recordings

# Logging Setup
log_file = DATA_DIR / "app.log"
logger = logging.getLogger("Main")
logger.setLevel(logging.INFO)

# File Handler
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))
logger.addHandler(console_handler)

# Health monitoring
def update_health(status="running", last_cycle=None, error_count=0):
    """Update health status file for service manager"""
    try:
        import json
        from datetime import datetime
        health_data = {
            "status": status,
            "last_heartbeat": datetime.now().isoformat(),
            "last_cycle": last_cycle,
            "error_count": error_count
        }
        Path(".health").write_text(json.dumps(health_data))
    except:
        pass

# PID file management
def write_pid():
    """Write process ID to file"""
    try:
        Path(".service.pid").write_text(str(os.getpid()))
    except:
        pass

def remove_pid():
    """Remove PID file on shutdown"""
    try:
        Path(".service.pid").unlink(missing_ok=True)
        Path(".health").unlink(missing_ok=True)
    except:
        pass

# Global shutdown flag
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main(run_once=False):
    logger.info("Starting VONG Automation System (V2 Passive Mode)...")
    
    try:
        check_config()
    except ValueError as e:
        logger.error(str(e))
        return

    acquire_lock()
    
    try:
        # --- INITIALIZATION ---
        db = StateManager()
        
        # 1. Drive (user OAuth for 2TB personal Drive)
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH
        )
        # Sheets always uses service account (separate from Drive OAuth)
        sheets_drive = DriveClient(
            auth_mode='service_account',
            service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE
        )
        sheet_manager = SheetManager(sheets_drive.credentials)
        sheet_manager.log_system_status("System Booted. Waiting for Command...", "INIT")
        
        # Initialize History Logger
        history_logger = HistoryLogger(sheet_manager)
        logger.info("History logger initialized")

        # 2. YouTube
        try:
            youtube = YouTubeClient(config.YOUTUBE_CLIENT_SECRET_PATH, config.YOUTUBE_TOKEN_PATH)
        except Exception as e:
            logger.error(f"YouTube Auth Failed: {e}")
            sheet_manager.log_system_status("YouTube Auth Failed - Check Logs", "ERROR")
            return

        # 3. Zoom Clients
        zoom_clients_map = {}
        for z_cfg in config.ZOOM_ACCOUNTS:
            try:
                zoom_clients_map[z_cfg['name']] = ZoomClient(z_cfg)
            except Exception as e:
                logger.error(f"Zoom Client Init Failed ({z_cfg['name']}): {e}")

        # --- MAIN LOOP (ACTIVE MODE) ---
        logger.info("Starting active auto-processing mode...")
        sheet_manager.log_system_status("Active Mode - Auto-processing enabled", "RUNNING")
        
        # Write PID file for service manager
        write_pid()
        update_health("starting")
        
        error_count = 0
        
        while True:
            try:
                logger.info("--- Cycle Start ---")
                cycle_start = datetime.now()
                update_health("running", cycle_start.isoformat(), error_count)
                sheet_manager.update_dashboard("Running...", "Calculating...")
            
                # --- PHASE 1: INGESTION (Zoom -> Sheet) ---
                logger.info("--- Phase 1: Ingestion ---")
                try:
                    now = datetime.now()
                    # Scan last 2 days to be safe
                    yesterday = (now - timedelta(days=2)).strftime("%Y-%m-%d")
                    today = now.strftime("%Y-%m-%d")
                    
                    new_recs = []
                    for name, client in zoom_clients_map.items():
                        for user in client.get_all_users():
                            try:
                                recs = client.get_user_recordings(user['id'], yesterday, today)
                                for r in recs:
                                    r['account_name'] = name
                                    db.mark_detected(r['id'], r)
                                    new_recs.append(r)
                            except: pass

                    # Add to sheets (for logging)
                    added_count = sheet_manager.log_new_recordings(new_recs)

                    # Also add to SQL database (for frontend API)
                    # Use UUID as primary key (unique per recording instance)
                    from src.db_sql import db as sql_db
                    for rec in new_recs:
                        uuid = rec.get('uuid', str(rec['id']))
                        meeting_id = str(rec['id'])
                        sql_db.add_recording(uuid, rec, meeting_id=meeting_id)
                    
                    if added_count > 0:
                        notify_success(f"Found {added_count} new Zoom recordings.")
                        logger.info(f"Added {added_count} recordings to sheets and SQL database")
                except Exception as e:
                    logger.warning(f"Zoom ingestion failed (non-fatal): {e}")
                    logger.info("Continuing to process existing approvals...")


                # --- PHASE 2: PROCESSING (Sheet -> YT/Drive) ---
                logger.info("--- Phase 2: Processing Approvals ---")
                
                # Get approvals from BOTH sources:
                # 1. Google Sheets (legacy/manual approvals)
                sheet_tasks = sheet_manager.get_pending_approvals()
                
                # 2. SQL Database (frontend approvals)
                from src.db_sql import db as sql_db
                sql_approvals = sql_db.get_approved()
                
                # Convert SQL approvals to expected format
                tasks = list(sheet_tasks)  # Start with sheet tasks
                for sql_rec in sql_approvals:
                    metadata = json.loads(sql_rec['metadata']) if sql_rec.get('metadata') else {}
                    tasks.append({
                        'meeting_id': sql_rec.get('meeting_id') or sql_rec['zoom_id'],
                        'zoom_id': sql_rec['zoom_id'],  # This is the UUID (unique per instance)
                        'topic': sql_rec['topic'],
                        'team': sql_rec['team'],
                        'playlist': sql_rec['playlist'],
                        'approved_by': sql_rec['approved_by'],
                        'start_time': sql_rec.get('start_time', ''),
                        'metadata': metadata,
                        'source': 'frontend'  # Mark source for tracking
                    })
                
                logger.info(f"Found {len(tasks)} approved tasks ({len(sheet_tasks)} from sheets, {len(sql_approvals)} from frontend).")
                
                for task in tasks:
                    try:
                        # Use UUID (zoom_id) for all Zoom API calls — NOT meeting_id
                        # meeting_id is the same for ALL recurring instances and fetches wrong recordings
                        zoom_id = task.get('zoom_id') or task['meeting_id']
                        meeting_id = task.get('meeting_id', zoom_id)
                        logger.info(f"Processing: {task['topic']} (approved by {task['approved_by']}, UUID: {zoom_id})")

                        # Start history tracking
                        history_logger.start_operation(zoom_id, {
                            'topic': task['topic'],
                            'start_time': task.get('start_time', ''),
                            'approved_by': task['approved_by'],
                            'team': task['team'],
                            'playlist': task['playlist']
                        })

                        # Update sheet status (only for sheet approvals)
                        if task.get('row_idx'):
                            sheet_manager.update_row_status(task['row_idx'], "PROCESSING")

                        # A. Get Zoom Client
                        client = list(zoom_clients_map.values())[0]  # Fallback

                        # B. Refresh Metadata & Files using UUID (safe for recurring meetings)
                        task_start_time = task.get('start_time', '')
                        expected_date = task_start_time[:10] if task_start_time else None

                        try:
                            # Always use UUID-based lookup first (returns only this specific instance)
                            meta = client.get_recording_by_uuid(zoom_id)
                        except Exception as e:
                            if "404" in str(e) or "Not Found" in str(e):
                                # UUID lookup failed — only fall back to meeting_id if NOT recurring
                                if str(zoom_id) == str(meeting_id):
                                    logger.warning(f"UUID lookup failed, trying meeting_id fallback: {meeting_id}")
                                    try:
                                        meta = client.get_meeting_recordings(meeting_id)
                                    except:
                                        raise Exception("EXPIRED: Meeting not found in Zoom")
                                else:
                                    raise Exception(f"EXPIRED: Recording UUID {zoom_id} not found in Zoom (recurring meeting, no fallback)")
                            else:
                                raise e

                        if not meta: raise Exception("EXPIRED: Meeting not found in Zoom")

                        # Find Files - match by date for recurring meetings to avoid wrong instance
                        mp4_url = None
                        vtt_url = None
                        for f in meta.get('recording_files', []):
                            file_start = f.get('recording_start', '')
                            file_date = file_start[:10] if file_start else None

                            # Skip files that don't match the expected recording date
                            if expected_date and file_date and file_date != expected_date:
                                logger.warning(f"Skipping recording file with wrong date: expected {expected_date}, got {file_date}")
                                continue

                            if f.get('file_type') == 'MP4' and not mp4_url:
                                mp4_url = f.get('download_url')
                            elif f.get('file_type') == 'TRANSCRIPT' and not vtt_url:
                                vtt_url = f.get('download_url')

                        if not mp4_url:
                            # Log all available files for debugging
                            logger.error(f"No MP4 found matching date {expected_date}. Available files:")
                            for f in meta.get('recording_files', []):
                                logger.error(f"  - {f.get('file_type')} | start: {f.get('recording_start', 'unknown')}")
                            raise Exception(f"No MP4 file found matching expected date {expected_date}")

                        # Download - use meta's start_time for naming (from actual Zoom data)
                        recording_start = meta.get('start_time', task_start_time)
                        names = generate_names(task['topic'], recording_start)
                        vid_path = DOWNLOAD_DIR / names['video_filename']
                        ts_path = DOWNLOAD_DIR / names['transcript_filename']
                        
                        logger.info("Downloading from Zoom...")
                        history_logger.log_step(zoom_id, 'download_start', f"Downloading {names['video_filename']}")
                        client.download_file(mp4_url, vid_path)
                        if vtt_url: client.download_file(vtt_url, ts_path)
                        history_logger.log_step(zoom_id, 'download_complete', f"Downloaded {os.path.getsize(vid_path) / 1024 / 1024:.1f} MB")
                        
                        # --- DYNAMIC PLAYLIST ---
                        pl_name = task['playlist']
                        pl_id = None
                        
                        # Search YT Playlists
                        user_playlists = youtube.get_playlists()
                        # Simple name match (case insensitive?)
                        for pl in user_playlists:
                            if pl['title'].lower() == pl_name.lower():
                                pl_id = pl['id']
                                break
                        
                        if not pl_id:
                            logger.info(f"Playlist '{pl_name}' not found. Creating new...")
                            pl_id = youtube.create_playlist(pl_name, "Auto-created by VONG", "unlisted")
                        
                        # C. Upload to YouTube (use date-prefixed title e.g. "20260312 Daily meeting")
                        youtube_title = names.get('youtube_title', task['topic'])
                        logger.info(f"Uploading to YouTube as: {youtube_title}")
                        history_logger.log_step(zoom_id, 'youtube_upload_start', f"Uploading to playlist: {pl_name}")
                        try:
                            yt_id = youtube.upload_video(
                                str(vid_path),
                                youtube_title,
                                f"Approved by {task['approved_by']}",
                                privacy_status="unlisted"
                            )
                        except Exception as yt_err:
                            if 'quotaExceeded' in str(yt_err):
                                logger.warning("YouTube daily quota exceeded. Stopping cycle until quota resets (1:30 AM IST).")
                                raise Exception("YOUTUBE_QUOTA_EXCEEDED")
                            raise yt_err
                        
                        if pl_id: youtube.add_to_playlist(yt_id, pl_id)
                        if os.path.exists(ts_path): youtube.upload_caption(yt_id, str(ts_path))
                        
                        yt_link = f"https://youtu.be/{yt_id}"
                        history_logger.log_youtube_upload(zoom_id, yt_id, pl_name)
                        
                        # D. Upload to Drive (Original Quality)
                        # Use existing playlist folders - NO auto-creation
                        from src.playlist_folders import get_drive_folder_id
                        
                        # Get the existing folder IDs for this playlist
                        video_folder_id = get_drive_folder_id(pl_name, for_transcript=False)
                        transcript_folder_id = get_drive_folder_id(pl_name, for_transcript=True)
                        
                        drive_link = ""
                        try:
                            if not video_folder_id:
                                raise Exception(f"No Drive folder found for playlist '{pl_name}'. Please add it to playlist_folders.py")
                            
                            logger.info(f"Uploading to Drive Playlist Folder: {pl_name}")
                            history_logger.log_step(zoom_id, 'drive_upload_start', f"Playlist: {pl_name}")
                            
                            # Upload video to playlist video folder
                            drive.upload_file(str(vid_path), names['video_name_clean'], video_folder_id)
                            
                            # Upload transcript to playlist transcript folder (if exists)
                            if os.path.exists(ts_path) and transcript_folder_id:
                                drive.upload_file(str(ts_path), names['transcript_filename'], transcript_folder_id)
                            elif os.path.exists(ts_path):
                                # Fallback: upload to video folder if no transcript folder
                                logger.warning(f"No transcript folder for '{pl_name}', uploading to video folder")
                                drive.upload_file(str(ts_path), names['transcript_filename'], video_folder_id)
                                
                            drive_link = f"https://drive.google.com/drive/folders/{video_folder_id}"
                            history_logger.log_drive_upload(zoom_id, video_folder_id, pl_name)
                        except Exception as drive_err:
                            logger.error(f"Drive upload failed (skipping): {drive_err}")
                            history_logger.log_step(zoom_id, 'drive_upload_failed', str(drive_err))
                            drive_link = "FAILED_QUOTA_ERROR"
                        
                        # Cleanup (moved to finally block)

                        # E. Delete from Zoom Cloud — ONLY if BOTH YouTube AND Drive succeeded
                        if yt_link and drive_link and drive_link != "FAILED_QUOTA_ERROR":
                            try:
                                # Use UUID-based deletion (safe for recurring meetings)
                                logger.info(f"Deleting recording from Zoom cloud (UUID: {zoom_id})")
                                client.get_recording_by_uuid(zoom_id)  # Verify it exists first
                                import urllib.parse
                                if zoom_id.startswith('/') or '//' in zoom_id:
                                    encoded_id = urllib.parse.quote(urllib.parse.quote(zoom_id, safe=''), safe='')
                                else:
                                    encoded_id = urllib.parse.quote(zoom_id, safe='')
                                client.delete_recording(encoded_id)
                                logger.info(f"Zoom recording deleted: {zoom_id}")
                                history_logger.log_step(zoom_id, 'zoom_deleted', 'Deleted from Zoom cloud')
                            except Exception as del_err:
                                logger.warning(f"Could not delete Zoom recording (may already be gone): {del_err}")
                        else:
                            logger.warning(f"NOT deleting from Zoom - safety check: YT={bool(yt_link)}, Drive={drive_link}")
                            history_logger.log_step(zoom_id, 'zoom_delete_skipped', f'Safety: YT={bool(yt_link)}, Drive={drive_link}')
                        
                        # Mark Complete in TinyDB
                        db.mark_completed(zoom_id)
                        
                        # Update SQL database if this was a frontend approval
                        if task.get('source') == 'frontend':
                            from src.db_sql import db as sql_db
                            sql_db.update_recording(zoom_id, {
                                'status': 'COMPLETED',
                                'youtube_url': yt_link,
                                'drive_url': drive_link
                            })
                        
                        # Mark Complete in Sheets (only if this came from sheets)
                        if 'row_idx' in task:
                            sheet_manager.update_row_status(task['row_idx'], "COMPLETED", yt_link, drive_link)
                        
                        # Complete history logging
                        history_logger.complete_operation(
                            zoom_id,
                            approved_by=task['approved_by'],
                            team=task['team'],
                            playlist=pl_name
                        )
                        
                        notify_success(f"Completed: {task['topic']}")
                        
                    except Exception as e:
                        error_msg = str(e)
                        is_expired = "EXPIRED" in error_msg
                        is_quota = "YOUTUBE_QUOTA_EXCEEDED" in error_msg
                        status_to_set = "EXPIRED" if is_expired else "ERROR"
                        
                        # YouTube quota hit: stop processing for the day, don't mark as ERROR
                        if is_quota:
                            logger.warning("YouTube quota exhausted for today. Pipeline will resume after 1:30 AM IST.")
                            sheet_manager.log_system_status("YouTube quota exhausted. Resuming after reset.", "QUOTA")
                            break  # Stop processing remaining tasks this cycle
                        
                        logger.error(f"Failed task {task.get('topic', 'Unknown')}: {e}")
                        
                        # Log error to history
                        zoom_id = task.get('meeting_id', 'unknown')
                        history_logger.log_error(zoom_id, error_msg, 'processing')
                        
                        # Try to complete operation with error status
                        try:
                            history_logger.complete_operation(
                                zoom_id,
                                approved_by=task.get('approved_by', 'Unknown'),
                                team=task.get('team', 'Unknown'),
                                playlist=task.get('playlist', 'Unknown')
                            )
                        except:
                            pass
                        
                        # Update sheet status (only for sheet approvals)
                        if 'row_idx' in task:
                            sheet_manager.update_row_status(task['row_idx'], status_to_set)
                        
                        # Update SQL database if this was a frontend approval
                        if task.get('source') == 'frontend':
                            from src.db_sql import db as sql_db
                            sql_db.update_recording(zoom_id, {'status': status_to_set, 'error_message': error_msg})
                        
                        sheet_manager.log_system_status(f"Error processing {task.get('topic', 'Unknown')}: {error_msg}", status_to_set)
                    
                    finally:
                        # Guaranteed Cleanup to prevent disk space exhaustion
                        try:
                            if 'vid_path' in locals() and os.path.exists(vid_path):
                                os.remove(vid_path)
                                logger.info(f"Cleaned up {vid_path}")
                            if 'ts_path' in locals() and os.path.exists(ts_path):
                                os.remove(ts_path)
                        except Exception as cleanup_err:
                            logger.error(f"Cleanup failed for {zoom_id}: {cleanup_err}")

                # --- PHASE 3: MONITOR & CLEANUP ---
                check_disk_space(DOWNLOAD_DIR)
                cleanup_old_files(DOWNLOAD_DIR)
                
                # Zoom Cloud Cleanup: Delete recordings that are COMPLETED and older than 1 day
                try:
                    cleanup_zoom_recordings(sheet_manager, zoom_clients_map, retention_days=1)
                except Exception as cleanup_err:
                    logger.warning(f"Zoom cloud cleanup failed (non-fatal): {cleanup_err}")
                
                # Update dashboard with stats
                sheet_manager.update_dashboard("Idle", "Waiting for next cycle...")
                
            except Exception as e:
                error_count += 1
                update_health("error", datetime.now().isoformat(), error_count)
                logger.error(f"Cycle Error: {e}")
                sheet_manager.log_system_status(f"Cycle error: {e}", "ERROR")
            
            
            if run_once or shutdown_requested:
                break
            
            # Active mode: Check for new approvals every 30 seconds
            logger.info("Sleeping 30s before next cycle...")
            for _ in range(30):
                if shutdown_requested:
                    break
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping...")
        update_health("stopped")
    finally:
        remove_pid()
        release_lock()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once")
    args = parser.parse_args()
    main(run_once=args.once)
