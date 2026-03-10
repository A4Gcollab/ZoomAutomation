import sqlite3
import json

def check_db():
    conn = sqlite3.connect('data/vong_v2.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT zoom_id, topic, status, error_message, youtube_url FROM recordings WHERE team='HR' ORDER BY start_time DESC LIMIT 5")
    rows = [dict(row) for row in c.fetchall()]
    print("Database rows:", json.dumps(rows, indent=2))
    
    c.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 15")
    logs = [dict(row) for row in c.fetchall()]
    print("Recent system logs:", json.dumps(logs, indent=2))

if __name__ == '__main__':
    check_db()
