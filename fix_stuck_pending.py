import sys
sys.path.insert(0, '.')
import sqlite3
import json
from src.config import PLAYLIST_CONFIG_PATH
from src.db_sql import db

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
        print(f"Error resolving playlist: {e}")
    return None, None

def fix_stuck_pending():
    print("Scanning database for videos stuck in PENDING queue that should be auto-approved...")
    conn = sqlite3.connect('C:/Users/HP/ZoomAutomation/data/vong_v2.db' if sys.platform == 'win32' else 'data/vong_v2.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT zoom_id, meeting_id, topic FROM recordings WHERE status IN ('PENDING', 'PENDING_PLAYLIST')")
    rows = cur.fetchall()
    
    updated = 0
    for row in rows:
        team, playlist = resolve_team_playlist(row['meeting_id'], row['topic'])
        if team and playlist:
            cur.execute("""
                UPDATE recordings 
                SET status = 'APPROVED', team = ?, playlist = ? 
                WHERE zoom_id = ?
            """, (team, playlist, row['zoom_id']))
            print(f"✅ Auto-Approved: {row['topic']} -> {playlist}")
            updated += 1
            
    conn.commit()
    conn.close()
    print(f"\nSuccessfully forced {updated} videos out of the Pending queue and into the Approved pipeline!")

if __name__ == "__main__":
    fix_stuck_pending()
