import sqlite3
import json

def check_db():
    conn = sqlite3.connect('data/vong_v2.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT zoom_id, status, error_message, youtube_url FROM recordings WHERE date_str LIKE '%08%' AND date_str LIKE '%2026%' AND team='Tech'")
    rows = [dict(row) for row in c.fetchall()]
    print(json.dumps(rows, indent=2))

if __name__ == '__main__':
    check_db()
