import sqlite3
import json
try:
    conn = sqlite3.connect('data/vong_v2.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT zoom_id, status, error_message FROM recordings WHERE team='HR' ORDER BY start_time DESC LIMIT 5")
    rows = [dict(row) for row in c.fetchall()]
    with open("hr_result.json", "w") as f:
        json.dump(rows, f, indent=2)
except Exception as e:
    with open("hr_result.json", "w") as f:
        f.write(str(e))
