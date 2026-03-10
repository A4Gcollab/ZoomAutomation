
import sqlite3
import json
import logging
from datetime import datetime
from src.config import DATA_DIR

DB_PATH = DATA_DIR / "vong_v2.db"
logger = logging.getLogger("DB")

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        
        # Recordings Table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            zoom_id TEXT PRIMARY KEY,
            account_name TEXT,
            topic TEXT,
            start_time TEXT,
            date_str TEXT,
            status TEXT DEFAULT 'PENDING',
            team TEXT,
            playlist TEXT,
            approved_by TEXT,
            video_url TEXT,
            transcript_url TEXT,
            youtube_url TEXT,
            drive_url TEXT,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Logs Table (for persistent history)
        cur.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()

    def add_recording(self, zoom_id, data):
        """Insert or Ignore new recording."""
        try:
            cur = self.conn.cursor()
            # extract basic fields
            topic = data.get('topic', '')
            start_time = data.get('start_time', '')
            date_str = start_time[:10] if start_time else ''
            acc_name = data.get('account_name', '')
            
            cur.execute('''
                INSERT OR IGNORE INTO recordings 
                (zoom_id, account_name, topic, start_time, date_str, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (zoom_id, acc_name, topic, start_time, date_str, json.dumps(data)))
            self.conn.commit()
            return cur.rowcount > 0 # True if inserted
        except Exception as e:
            logger.error(f"DB Error add_recording: {e}")
            return False

    def get_pending(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM recordings WHERE status = 'PENDING' ORDER BY start_time DESC")
        return [dict(row) for row in cur.fetchall()]
    
    def get_approved(self):
        """Get recordings that have been approved and are ready for processing."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM recordings WHERE status = 'APPROVED' ORDER BY start_time DESC")
        return [dict(row) for row in cur.fetchall()]

    def get_history(self, limit=50):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM recordings WHERE status != 'PENDING' ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

    def get_options(self):
        """Fetch distinct teams and playlists from DB + Config."""
        cur = self.conn.cursor()
        
        # 1. DB Options
        cur.execute("SELECT DISTINCT team FROM recordings WHERE team IS NOT NULL AND team != ''")
        db_teams = set(row[0] for row in cur.fetchall())
        
        cur.execute("SELECT DISTINCT playlist FROM recordings WHERE playlist IS NOT NULL AND playlist != ''")
        db_playlists = set(row[0] for row in cur.fetchall())
        
        # 2. Config Options (playlists.json)
        import json
        from src.config import PLAYLIST_CONFIG_PATH
        
        if PLAYLIST_CONFIG_PATH.exists():
            try:
                with open(PLAYLIST_CONFIG_PATH, 'r') as f:
                    data = json.load(f)
                    for pl in data.get('playlists', []):
                        if pl.get('category'):
                            db_teams.add(pl['category'])
                        if pl.get('playlist_name'):
                            db_playlists.add(pl['playlist_name'])
            except Exception as e:
                logger.error(f"Failed to load playlist config: {e}")
        
        return {"teams": sorted(list(db_teams)), "playlists": sorted(list(db_playlists))}
    
    def get_stats(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM recordings WHERE status='COMPLETED'")
        completed = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM recordings WHERE status='PENDING'")
        pending = cur.fetchone()[0]
        return {"completed": completed, "pending": pending}

    def update_recording(self, zoom_id, updates):
        """updates is a dict of col: val"""
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(zoom_id)
        
        cur = self.conn.cursor()
        cur.execute(f"UPDATE recordings SET {set_clause} WHERE zoom_id = ?", values)
        self.conn.commit()

    def add_log(self, level, message):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO system_logs (level, message) VALUES (?, ?)", (level, message))
        self.conn.commit()

    def get_recent_logs(self, limit=100):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cur.fetchall()]

# Singleton
db = Database()
