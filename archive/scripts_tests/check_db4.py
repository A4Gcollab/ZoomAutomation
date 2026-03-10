import sqlite3
import json
import os

def check_db():
    try:
        conn = sqlite3.connect('data/vong_v2.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT zoom_id, status, error_message FROM recordings WHERE team='HR' ORDER BY start_time DESC LIMIT 5")
        rows = [dict(row) for row in c.fetchall()]
        print("HR videos:", json.dumps(rows, indent=2))
        
        c.execute("SELECT message FROM system_logs ORDER BY id DESC LIMIT 5")
        logs = [r[0] for r in c.fetchall()]
        print("Logs:", json.dumps(logs, indent=2))
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    check_db()
    
    # Check env for sheets
    from dotenv import load_dotenv
    load_dotenv()
    print("SHEETS_URL / SPREADSHEET_ID:", os.getenv("SPREADSHEET_ID") or os.getenv("SHEETS_URL") or "Not found")

