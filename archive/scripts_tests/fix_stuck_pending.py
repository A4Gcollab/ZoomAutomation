"""
Force-approve ALL remaining PENDING/PENDING_PLAYLIST videos.
- First tries to match by keywords in playlists.json
- If no match, assigns to the default Miscellaneous playlist
This ensures ZERO videos remain in the Pending Queue.
"""
import sys
sys.path.insert(0, '.')
import sqlite3
import json
from src.config import PLAYLIST_CONFIG_PATH

DB_PATH = 'data/vong_v2.db'

def load_config():
    with open(str(PLAYLIST_CONFIG_PATH), 'r') as f:
        return json.load(f)

def resolve_team_playlist(config, meeting_id, topic=''):
    meeting_id = str(meeting_id)
    
    # Priority 1: Match by meeting ID
    for pl in config.get('playlists', []):
        if meeting_id in pl.get('meeting_ids', []):
            return pl.get('category'), pl.get('playlist_name')
    
    # Priority 2: Match by topic keywords
    topic_lower = topic.lower()
    for pl in config.get('playlists', []):
        for keyword in pl.get('keywords', []):
            if keyword.lower() in topic_lower:
                return pl.get('category'), pl.get('playlist_name')
    
    # No match -> use default
    return None, None

def fix_all_pending():
    config = load_config()
    default_category = config.get('default_category', 'Miscellaneous')
    default_playlist = config.get('default_playlist_name', 'Miscellaneous')
    
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT zoom_id, meeting_id, topic, status FROM recordings WHERE status IN ('PENDING', 'PENDING_PLAYLIST')")
    rows = cur.fetchall()
    
    print(f"Found {len(rows)} videos still in Pending Queue\n")
    
    matched = 0
    defaulted = 0
    
    for row in rows:
        team, playlist = resolve_team_playlist(config, row['meeting_id'], row['topic'])
        
        if team and playlist:
            cur.execute("""
                UPDATE recordings 
                SET status = 'APPROVED', team = ?, playlist = ? 
                WHERE zoom_id = ?
            """, (team, playlist, row['zoom_id']))
            print(f"  ✅ MATCHED: {row['topic'][:50]} -> {playlist}")
            matched += 1
        else:
            # Force-assign to default Miscellaneous playlist
            cur.execute("""
                UPDATE recordings 
                SET status = 'APPROVED', team = ?, playlist = ? 
                WHERE zoom_id = ?
            """, (default_category, default_playlist, row['zoom_id']))
            print(f"  📦 DEFAULT: {row['topic'][:50]} -> {default_playlist}")
            defaulted += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Results: {matched} matched by keywords, {defaulted} assigned to '{default_playlist}'")
    print(f"Total: {matched + defaulted} videos moved from PENDING -> APPROVED")
    print(f"Pending Queue should now be: 0")
    print(f"{'='*60}")

if __name__ == "__main__":
    fix_all_pending()
