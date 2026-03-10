
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
    and deletes them from Zoom.
    """
    logger.info(f"Running Safety Deletion Check (Retention: {retention_days} days)...")
    
    try:
        if not sheet_manager.main_tab: return
        
        # Get all data
        rows = sheet_manager.main_tab.get_all_values()
        headers = rows[0]
        data = rows[1:]
        
        # Column Indexes (0-based) based on V2 Schema
        # 0: Date, 1: ID, 5: Status
        
        now = datetime.now()
        
        for idx, row in enumerate(data):
            if len(row) < 9: continue
            
            status = row[5].strip().upper()
            zoom_id = row[1].strip()
            date_str = row[0].strip()
            
            # Logic: If Status is COMPLETED (and not already marked deleted)
            if "COMPLETED" in status and "ZOOM_DELETED" not in status:
                try:
                    # Use Meeting Date as proxy for age
                    meeting_date = datetime.strptime(date_str, "%Y-%m-%d")
                    age_days = (now - meeting_date).days
                    
                    if age_days >= retention_days:
                        logger.info(f"Found expired recording: {zoom_id} (Age: {age_days} days). Deleting...")
                        
                        deleted = False
                        # Try all clients (since we don't know exact ownership from sheet)
                        for acc_name, client in zoom_clients_map.items():
                            try:
                                if client.delete_recording(zoom_id):
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
