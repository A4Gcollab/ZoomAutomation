
import sqlite3
import json
import logging
import threading
from datetime import datetime, timedelta
from src.config import DATA_DIR

DB_PATH = DATA_DIR / "vong_v2.db"
logger = logging.getLogger("DB")


class Database:
    def __init__(self):
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_cursor(self):
        """Get a cursor with automatic reconnection if the connection is dead."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1")  # Test connection
            return cur
        except Exception:
            logger.warning("Database connection lost, reconnecting...")
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            return self.conn.cursor()

    def _init_db(self):
        with self._lock:
            cur = self.conn.cursor()

            # Recordings Table
            # zoom_id = UUID (unique per recording instance)
            # meeting_id = numeric Zoom meeting ID (same for recurring meetings)
            cur.execute('''
            CREATE TABLE IF NOT EXISTS recordings (
                zoom_id TEXT PRIMARY KEY,
                meeting_id TEXT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                processed_at TEXT,
                deletion_ready_at TEXT,
                zoom_deletion_status TEXT,
                zoom_deleted_at TEXT,
                zoom_deletion_error TEXT
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

            # Auto-migrate: add columns that might be missing from older schemas
            self._migrate_columns(cur)

    def _migrate_columns(self, cur):
        """Add any missing columns to existing tables."""
        new_columns = [
            ("meeting_id", "TEXT"),
            ("error_message", "TEXT"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("processed_at", "TEXT"),
            ("deletion_ready_at", "TEXT"),
            ("zoom_deletion_status", "TEXT"),
            ("zoom_deleted_at", "TEXT"),
            ("zoom_deletion_error", "TEXT"),
            ("drive_uploaded_at", "TEXT"),
        ]

        for col_name, col_type in new_columns:
            try:
                cur.execute(f"ALTER TABLE recordings ADD COLUMN {col_name} {col_type}")
                self.conn.commit()
                logger.info(f"Migrated: added column '{col_name}' to recordings")
            except sqlite3.OperationalError:
                pass  # Column already exists

    def add_recording(self, zoom_id, data, meeting_id=None):
        """Insert or Ignore new recording.

        Args:
            zoom_id: UUID (unique per recording instance) - used as primary key
            data: Full recording data dict from Zoom
            meeting_id: Numeric meeting ID (same for recurring meetings) - used for playlist matching
        """
        with self._lock:
            try:
                cur = self._get_cursor()
                topic = data.get('topic', '')
                start_time = data.get('start_time', '')
                date_str = start_time[:10] if start_time else ''
                acc_name = data.get('account_name', '')
                mid = meeting_id or str(data.get('id', ''))
                team = data.get('team', None)
                playlist = data.get('playlist', None)
                status = 'APPROVED' if (team and playlist) else 'PENDING_PLAYLIST'

                cur.execute('''
                    INSERT OR IGNORE INTO recordings
                    (zoom_id, meeting_id, account_name, topic, start_time, date_str, team, playlist, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (zoom_id, mid, acc_name, topic, start_time, date_str, team, playlist, status, json.dumps(data)))
                self.conn.commit()
                return cur.rowcount > 0
            except Exception as e:
                logger.error(f"DB Error add_recording: {e}")
                return False

    def get_pending(self):
        """Get pending recordings, grouped by meeting_id.

        For recurring meetings (same meeting_id), only returns the LATEST instance
        with a count of how many total instances exist. This prevents the queue
        from showing 15 rows for the same recurring meeting.
        """
        with self._lock:
            cur = self._get_cursor()
            # Get the latest recording per meeting_id (or per zoom_id if no meeting_id)
            cur.execute("""
                SELECT r.*, sub.instance_count
                FROM recordings r
                INNER JOIN (
                    SELECT
                        COALESCE(meeting_id, zoom_id) as group_key,
                        MAX(start_time) as max_start,
                        COUNT(*) as instance_count
                    FROM recordings
                    WHERE status IN ('PENDING', 'PENDING_PLAYLIST')
                    GROUP BY COALESCE(meeting_id, zoom_id)
                ) sub ON COALESCE(r.meeting_id, r.zoom_id) = sub.group_key
                    AND r.start_time = sub.max_start
                WHERE r.status IN ('PENDING', 'PENDING_PLAYLIST')
                ORDER BY r.start_time DESC
            """)
            return [dict(row) for row in cur.fetchall()]

    def get_pending_all(self):
        """Get ALL pending recordings without grouping (for internal processing)."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT * FROM recordings WHERE status = 'PENDING' ORDER BY start_time DESC")
            return [dict(row) for row in cur.fetchall()]

    def get_approved(self):
        """Get recordings that have been approved and are ready for processing."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT * FROM recordings WHERE status = 'APPROVED' ORDER BY start_time DESC")
            return [dict(row) for row in cur.fetchall()]

    def get_history(self, limit=50):
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT * FROM recordings WHERE status != 'PENDING' ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]

    def get_compressing(self):
        """Get recordings that are waiting for YouTube compression to finish."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT * FROM recordings WHERE status = 'YOUTUBE_COMPRESSING' ORDER BY start_time DESC")
            return [dict(row) for row in cur.fetchall()]

    def get_pending_playlist(self):
        """Get recordings awaiting admin playlist assignment."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT * FROM recordings WHERE status = 'PENDING_PLAYLIST' ORDER BY start_time DESC")
            return [dict(row) for row in cur.fetchall()]

    def get_ready_for_zoom_deletion(self, delay_hours=6):
        """Get COMPLETED recordings where Drive upload happened >delay_hours ago."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("""
                SELECT * FROM recordings 
                WHERE status = 'COMPLETED' 
                AND drive_uploaded_at IS NOT NULL
                AND (zoom_deletion_status IS NULL OR zoom_deletion_status = 'PENDING' OR zoom_deletion_status = '')
                AND datetime(drive_uploaded_at) <= datetime('now', ? || ' hours')
                ORDER BY drive_uploaded_at ASC
            """, (str(-delay_hours),))
            return [dict(row) for row in cur.fetchall()]

    def get_options(self):
        """Fetch distinct teams and playlists from DB + Config."""
        with self._lock:
            cur = self._get_cursor()

            cur.execute("SELECT DISTINCT team FROM recordings WHERE team IS NOT NULL AND team != ''")
            db_teams = set(row[0] for row in cur.fetchall())

            cur.execute("SELECT DISTINCT playlist FROM recordings WHERE playlist IS NOT NULL AND playlist != ''")
            db_playlists = set(row[0] for row in cur.fetchall())

        # Config Options (playlists.json) - outside lock since it's file I/O
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
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT COUNT(*) FROM recordings WHERE status='COMPLETED'")
            completed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM recordings WHERE status IN ('PENDING', 'PENDING_PLAYLIST')")
            pending = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM recordings WHERE status='ERROR'")
            errors = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM recordings WHERE status='PROCESSING'")
            processing = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM recordings WHERE status='APPROVED'")
            approved = cur.fetchone()[0]
            return {
                "completed": completed,
                "pending": pending,
                "errors": errors,
                "processing": processing,
                "approved": approved,
            }

    def update_recording(self, zoom_id, updates):
        """updates is a dict of col: val"""
        with self._lock:
            try:
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values())
                values.append(zoom_id)

                cur = self._get_cursor()
                cur.execute(f"UPDATE recordings SET {set_clause} WHERE zoom_id = ?", values)
                self.conn.commit()
            except Exception as e:
                logger.error(f"DB Error update_recording({zoom_id}): {e}")

    def bulk_approve_by_meeting_id(self, meeting_id, team, playlist, approved_by):
        """Approve ALL pending recordings with the same meeting_id.

        When a user approves one instance of a recurring meeting,
        this approves all other pending instances too.
        Returns the number of recordings approved.
        """
        with self._lock:
            try:
                cur = self._get_cursor()
                cur.execute("""
                    UPDATE recordings
                    SET status = 'APPROVED', team = ?, playlist = ?, approved_by = ?
                    WHERE status IN ('PENDING', 'PENDING_PLAYLIST')
                    AND meeting_id = ?
                """, (team, playlist, approved_by, meeting_id))
                count = cur.rowcount
                self.conn.commit()
                if count > 0:
                    logger.info(f"Bulk approved {count} recording(s) for meeting_id {meeting_id}")
                return count
            except Exception as e:
                logger.error(f"DB Error bulk_approve_by_meeting_id: {e}")
                return 0

    def get_meeting_id_for_zoom_id(self, zoom_id):
        """Get the meeting_id associated with a zoom_id (UUID)."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT meeting_id FROM recordings WHERE zoom_id = ?", (zoom_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def add_log(self, level, message):
        with self._lock:
            try:
                cur = self._get_cursor()
                cur.execute("INSERT INTO system_logs (level, message) VALUES (?, ?)", (level, message))
                self.conn.commit()
            except Exception as e:
                logger.error(f"DB Error add_log: {e}")

    def get_recent_logs(self, limit=100):
        with self._lock:
            cur = self._get_cursor()
            cur.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]

    # === AUTO-RECOVERY METHODS ===

    def recover_stuck_processing(self, max_age_minutes=60):
        """Reset PROCESSING records that have been stuck for too long back to APPROVED."""
        with self._lock:
            try:
                cur = self._get_cursor()
                # Find PROCESSING records older than max_age_minutes
                # We use created_at as a proxy since we don't track processing_started_at
                cutoff = (datetime.now() - timedelta(minutes=max_age_minutes)).isoformat()
                cur.execute("""
                    UPDATE recordings
                    SET status = 'APPROVED', error_message = 'Auto-recovered: stuck in PROCESSING'
                    WHERE status = 'PROCESSING'
                    AND (processed_at IS NULL OR processed_at < ?)
                """, (cutoff,))
                count = cur.rowcount
                self.conn.commit()
                if count > 0:
                    logger.info(f"Auto-recovered {count} stuck PROCESSING record(s)")
                return count
            except Exception as e:
                logger.error(f"DB Error recover_stuck_processing: {e}")
                return 0

    def recover_error_records(self, max_retries=3):
        """Reset ERROR records back to APPROVED (if matched) or PENDING for retry."""
        with self._lock:
            try:
                cur = self._get_cursor()
                cur.execute("""
                    UPDATE recordings
                    SET status = CASE
                            WHEN team IS NOT NULL AND playlist IS NOT NULL THEN 'APPROVED'
                            ELSE 'PENDING_PLAYLIST'
                        END,
                        retry_count = COALESCE(retry_count, 0) + 1,
                        error_message = NULL
                    WHERE status = 'ERROR'
                    AND COALESCE(retry_count, 0) < ?
                """, (max_retries,))
                count = cur.rowcount
                self.conn.commit()
                if count > 0:
                    logger.info(f"Auto-recovered {count} ERROR record(s) for retry")
                return count
            except Exception as e:
                logger.error(f"DB Error recover_error_records: {e}")
                return 0

    def get_permanently_failed(self):
        """Get records that have exceeded max retries."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("""
                SELECT * FROM recordings
                WHERE status = 'ERROR' AND COALESCE(retry_count, 0) >= 3
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cur.fetchall()]

    def get_ready_for_deletion(self):
        """Get COMPLETED recordings ready for Zoom deletion after safety period."""
        with self._lock:
            cur = self._get_cursor()
            cur.execute("""
                SELECT * FROM recordings
                WHERE status = 'COMPLETED'
                AND deletion_ready_at IS NOT NULL
                AND deletion_ready_at <= ?
                AND (zoom_deletion_status IS NULL OR zoom_deletion_status = 'PENDING')
            """, (datetime.now().isoformat(),))
            return [dict(row) for row in cur.fetchall()]


# Singleton
db = Database()
