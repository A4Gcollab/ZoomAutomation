
import shutil
import os
import time
import logging
from datetime import datetime, timedelta
from src.notifications import notify_error
from src.sheet_schema_v2 import SheetSchemaV2, SheetSchemaV2 as Schema

logger = logging.getLogger("Monitor")

def check_disk_space(path, min_gb=5):
    """
    Check if disk space is below threshold.
    Alerts if critical.
    """
    try:
        total, used, free = shutil.disk_usage(path)
        free_gb = free // (2**30)
        
        if free_gb < min_gb:
            msg = f"Low Disk Space Warning! Only {free_gb}GB remaining on {path}."
            logger.warning(msg)
            # notify_error("System Monitor", msg) # Reduce spam
    except Exception:
        pass

def cleanup_old_files(folder, max_age_hours=24):
    """
    Deletes files in a folder older than max_age_hours.
    """
    logger.info(f"Running cleanup on {folder}...")
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    
    count = 0
    for root, dirs, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            try:
                if os.stat(path).st_mtime < cutoff:
                    os.remove(path)
                    count += 1
            except Exception as e:
                logger.error(f"Error deleting {path}: {e}")

    if count > 0:
        logger.info(f"Cleaned up {count} old temporary files.")

def cleanup_zoom_recordings(sheet_manager, zoom_clients_map, retention_days=7):
    """
    Scans the V2 sheet for COMPLETED items older than retention_days
    and deletes them from Zoom ONLY if both YouTube and Drive links exist.
    """
    logger.info(f"Running Safety Deletion Check (Retention: {retention_days} days)...")
    
    try:
        if not sheet_manager.main_tab: return
        
        # Get all data
        rows = sheet_manager.main_tab.get_all_values()
        headers = rows[0]
        data = rows[1:]
        
        # Column Indexes (0-based) based on V2 Schema:
        # 0: Date, 1: ID, 2: Title, 3: Team, 4: Playlist,
        # 5: Status, 6: Approved By, 7: YouTube URL, 8: Drive Folder
        
        now = datetime.now()
        
        for idx, row in enumerate(data):
            if len(row) < 9: continue
            
            status = row[5].strip().upper()
            zoom_id = row[1].strip()
            date_str = row[0].strip()
            youtube_url = row[7].strip() if len(row) > 7 else ""
            drive_url = row[8].strip() if len(row) > 8 else ""
            
            # SAFETY: Only delete if COMPLETED AND both YouTube AND Drive links exist and are valid
            if "COMPLETED" in status and "ZOOM_DELETED" not in status:
                # Check both links are present and valid (not error placeholders)
                if not youtube_url or not drive_url or "FAILED" in drive_url.upper():
                    logger.info(f"Skipping {zoom_id}: missing or invalid links (YT: {'✓' if youtube_url else '✗'}, Drive: {'✓' if (drive_url and 'FAILED' not in drive_url.upper()) else '✗'})")
                    continue
                
                try:
                    # Use Meeting Date as proxy for age
                    meeting_date = datetime.strptime(date_str, "%Y-%m-%d")
                    age_days = (now - meeting_date).days
                    
                    if age_days >= retention_days:
                        logger.info(f"Found expired recording: {zoom_id} (Age: {age_days} days, YT: ✓, Drive: ✓). Deleting...")
                        
                        deleted = False
                        # Try all clients using UUID-safe deletion
                        import urllib.parse
                        for acc_name, client in zoom_clients_map.items():
                            try:
                                # URL-encode UUID for Zoom API (double-encode if starts with / or has //)
                                if zoom_id.startswith('/') or '//' in zoom_id:
                                    encoded_id = urllib.parse.quote(urllib.parse.quote(zoom_id, safe=''), safe='')
                                else:
                                    encoded_id = urllib.parse.quote(zoom_id, safe='')
                                if client.delete_recording(encoded_id):
                                    deleted = True
                                    break
                            except:
                                continue
                        
                        if deleted:
                            # Update Status
                            # Row Index is idx + 2
                            new_status = status + " (ZOOM_DELETED)"
                            sheet_manager.main_tab.update_cell(idx + 2, 6, new_status) # Col 6 is Status
                            sheet_manager.log_system_status(f"Deleted expired recording {zoom_id}", "CLEANUP")
                        else:
                            logger.warning(f"Failed to delete {zoom_id} from Zoom (or already deleted).")
                            
                except ValueError:
                    continue
                    
    except Exception as e:
        logger.error(f"Error during Zoom Cleanup: {e}")

