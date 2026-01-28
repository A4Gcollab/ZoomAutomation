
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# Env and Path Setup
from src.config import check_config, CHECK_INTERVAL, DATA_DIR, DOWNLOAD_DIR
import src.config as config

# Modules
from src.db import StateManager
from src.utils import generate_names
from src.lock import acquire_lock, release_lock
from src.notifications import notify_error, notify_success
from src.zoom_client import ZoomClient
from src.youtube_client import YouTubeClient
from src.drive_client import DriveClient
from src.sheets_integration import SheetManager
from src.sheet_schema_v2 import SheetSchemaV2
from src.monitor import check_disk_space, cleanup_old_files, cleanup_zoom_recordings

# Setup Logging
log_file = DATA_DIR / "app.log"
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler, logging.StreamHandler()]
)
logger = logging.getLogger("Main")

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
        
        # 1. Drive & Sheet (Core)
        drive = DriveClient(
            auth_mode=config.DRIVE_AUTH_MODE,
            service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE,
            client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
            token_path=config.DRIVE_TOKEN_PATH
        )
        sheet_manager = SheetManager(drive.credentials)
        sheet_manager.log_system_status("System Booted. Waiting for Command...", "INIT")

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

        # --- MAIN LOOP ---
        while True:
            # 1. Poll Command State
            cmd_state = sheet_manager.check_command_state()
            
            if cmd_state == SheetSchemaV2.CMD_IDLE:
                if run_once: break
                logger.info("State: IDLE. Sleeping 60s...")
                time.sleep(60)
                continue
            
            # If we are here, State is START or REFRESH
            logger.info(f"State: {cmd_state} -> Executing Cycle...")
            sheet_manager.log_system_status("Cycle Started...", "RUNNING")
            sheet_manager.update_dashboard("Running...", "Calculating...")
            
            try:
                # --- PHASE 1: INGESTION (Zoom -> Sheet) ---
                logger.info("--- Phase 1: Ingestion ---")
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
                
                added_count = sheet_manager.log_new_recordings(new_recs)
                if added_count > 0:
                    notify_success(f"Found {added_count} new Zoom recordings.")

                # --- PHASE 2: PROCESSING (Sheet -> YT/Drive) ---
                logger.info("--- Phase 2: Processing Approvals ---")
                tasks = sheet_manager.get_pending_approvals()
                logger.info(f"Found {len(tasks)} approved tasks.")
                
                for task in tasks:
                    try:
                        zoom_id = task['meeting_id']
                        logger.info(f"Processing: {task['topic']} (approved by {task['approved_by']})")
                        
                        sheet_manager.update_row_status(task['row_idx'], "PROCESSING")
                        
                        # A. Get Zoom Client
                        # For simplicity, try all or map if we stored it? We didn't store account in Sheet V2.
                        # So we rely on DB or try-all.
                        client = list(zoom_clients_map.values())[0] # Fallback
                        
                        # B. Refresh Metadata & Files
                        meta = client.get_meeting_recordings(zoom_id)
                        if not meta: raise Exception("Meeting not found in Zoom (expired?)")
                        
                        # Find Files
                        mp4_url = next((f['download_url'] for f in meta['recording_files'] if f['file_type'] == 'MP4'), None)
                        vtt_url = next((f['download_url'] for f in meta['recording_files'] if f['file_type'] == 'TRANSCRIPT'), None)
                        
                        if not mp4_url: raise Exception("No MP4 file found.")
                        
                        # Download
                        names = generate_names(task['topic'], meta.get('start_time'))
                        vid_path = DOWNLOAD_DIR / names['video_filename']
                        ts_path = DOWNLOAD_DIR / names['transcript_filename']
                        
                        logger.info("Downloading from Zoom...")
                        client.download_file(mp4_url, vid_path)
                        if vtt_url: client.download_file(vtt_url, ts_path)
                        
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
                        
                        # C. Upload to YouTube
                        logger.info("Uploading to YouTube...")
                        yt_id = youtube.upload_video(
                            str(vid_path), 
                            task['topic'], 
                            f"Approved by {task['approved_by']}", 
                            privacy_status="unlisted"
                        )
                        
                        if pl_id: youtube.add_to_playlist(yt_id, pl_id)
                        if os.path.exists(ts_path): youtube.upload_caption(yt_id, str(ts_path))
                        
                        yt_link = f"https://youtu.be/{yt_id}"
                        
                        # D. Upload to Drive (Original Quality)
                        # Structure: Year / Playlist / Meeting
                        year_str = datetime.now().strftime("%Y")
                        
                        # 1. Ensure Year Folder
                        year_fid = drive.ensure_folder(year_str, config.DRIVE_ROOT_FOLDER_ID)
                        # 2. Ensure Playlist Folder
                        pl_fid = drive.ensure_folder(pl_name, year_fid)
                        # 3. Ensure Meeting Folder
                        meeting_fid = drive.ensure_folder(names['folder_name'], pl_fid)
                        
                        logger.info(f"Uploading to Drive Folder: {year_str}/{pl_name}/{names['folder_name']}")
                        drive.upload_file(str(vid_path), names['video_name_clean'], meeting_fid)
                        if os.path.exists(ts_path):
                            drive.upload_file(str(ts_path), names['transcript_filename'], meeting_fid)
                            
                        drive_link = f"https://drive.google.com/drive/folders/{meeting_fid}"
                        
                        # Cleanup
                        if os.path.exists(vid_path): os.remove(vid_path)
                        if os.path.exists(ts_path): os.remove(ts_path)
                        
                        # Mark Complete
                        sheet_manager.update_row_status(task['row_idx'], "COMPLETED", yt_link, drive_link)
                        db.mark_completed(zoom_id)
                        notify_success(f"Completed: {task['topic']}")
                        
                    except Exception as e:
                        logger.error(f"Failed task {task['topic']}: {e}")
                        sheet_manager.update_row_status(task['row_idx'], "ERROR")
                        sheet_manager.log_system_status(f"Error processing {task['topic']}: {e}", "ERROR")

                # --- PHASE 3: MONITOR & CLEANUP ---
                check_disk_space(DOWNLOAD_DIR)
                cleanup_old_files(DOWNLOAD_DIR)
                
                # Zoom Retention Check (7 Days)
                cleanup_zoom_recordings(sheet_manager, zoom_clients_map, retention_days=7)
                
                sheet_manager.log_system_status("Cycle Finished.", "IDLE")
                
            except Exception as e:
                logger.error(f"Cycle Error: {e}")
                sheet_manager.log_system_status(f"Cycle Error: {e}", "FATAL")
            
            # Reset State?
            # User wants it to "proceed until approved". 
            # If we set it to IDLE, it stops.
            # If we keep it START, it loops every minute.
            # "refresh the sheet... keep running... especially after start... proceed until approved"
            # It sounds like START -> Loop Mode.
            # We ONLY set to IDLE if it was a "REFRESH" (Single Run).
            if cmd_state == SheetSchemaV2.CMD_REFRESH:
                 sheet_manager.set_command_state(SheetSchemaV2.CMD_IDLE)
            
            if run_once: break
            
            # Sleep a bit between active cycles
            time.sleep(30)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        release_lock()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once")
    args = parser.parse_args()
    main(run_once=args.once)
