import sys
import json
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

sys.path.insert(0, '.')
from src.zoom_client import ZoomClient
from src.config import ZOOM_ACCOUNTS, PLAYLIST_CONFIG_PATH
from src.db_sql import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("HistoricQueue")

def resolve_team_playlist(meeting_id, topic=''):
    if not PLAYLIST_CONFIG_PATH.exists():
        return None, None
    try:
        with open(PLAYLIST_CONFIG_PATH, 'r') as f:
            data = json.load(f)
            meeting_id = str(meeting_id)
            
            for pl in data.get('playlists', []):
                if meeting_id in pl.get('meeting_ids', []):
                    return pl.get('category'), pl.get('playlist_name')
            
            topic_lower = topic.lower()
            for pl in data.get('playlists', []):
                for keyword in pl.get('keywords', []):
                    if keyword.lower() in topic_lower:
                        return pl.get('category'), pl.get('playlist_name')
    except Exception as e:
        logger.error(f"Error resolving playlist: {e}")
    return None, None

def queue_historical_recordings(start_year=2021, start_month=1):
    logger.info("Starting historical scan for Zoom Account 1...")
    
    # Use Zoom Account 1
    if not ZOOM_ACCOUNTS:
        logger.error("No Zoom accounts configured.")
        return
        
    creds = ZOOM_ACCOUNTS[0]
    client = ZoomClient(creds)
    account_name = creds['name']
    
    try:
        users = client.get_all_users()
    except Exception as e:
        logger.error(f"Failed to get Zoom users: {e}")
        return
        
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime.now()
    
    total_queued = 0
    total_scanned = 0

    for user in users:
        user_id = user['id']
        email = user.get('email', 'unknown')
        logger.info(f"Scanning user: {email} ({user_id})")
        
        current_start = start_date
        while current_start < end_date:
            current_end = current_start + relativedelta(months=1)
            if current_end > end_date:
                current_end = end_date
                
            sd_str = current_start.strftime('%Y-%m-%d')
            ed_str = current_end.strftime('%Y-%m-%d')
            
            logger.info(f"  Scanning range: {sd_str} to {ed_str}")
            try:
                recordings = client.get_user_recordings(user_id, sd_str, ed_str)
            except Exception as e:
                logger.error(f"  Failed to get recordings for range {sd_str}-{ed_str}: {e}")
                recordings = []
                
            for r in recordings:
                total_scanned += 1
                r['account_name'] = account_name
                uuid = r.get('uuid', str(r['id']))
                meeting_id = str(r['id'])
                topic = r.get('topic', '')
                
                team, playlist = resolve_team_playlist(meeting_id, topic)
                if team:
                    r['team'] = team
                if playlist:
                    r['playlist'] = playlist
                    
                # The db.add_recording handles INSERT OR IGNORE, meaning it won't duplicate existing ones.
                if db.add_recording(uuid, r, meeting_id=meeting_id):
                    total_queued += 1
                    status_log = f"{team} / {playlist}" if team else "PENDING_PLAYLIST"
                    logger.info(f"    Added strictly older recording: {topic[:40]} -> {status_log}")
            
            current_start = current_end + relativedelta(days=1)
            
    logger.info(f"Final Count! Scanned {total_scanned} historic videos, successfully injected {total_queued} strictly new videos into the local database queue.")
    if total_queued > 0:
        logger.info("The standard 'main.py' production pipeline will automatically detect these queued videos and begin aggressively downloading them to YouTube and Drive immediately!")

if __name__ == "__main__":
    queue_historical_recordings(start_year=2021)
