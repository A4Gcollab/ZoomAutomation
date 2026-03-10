
import sys
import os
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)

try:
    from src.db_sql import db
    print("DB initialized successfully.")
    
    stats = db.get_stats()
    print(f"Stats: {stats}")
    
    pending = db.get_pending()
    print(f"Pending: {len(pending)}")
    
    # Check if table exists
    cur = db.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")

except Exception as e:
    print(f"DB Error: {e}")
    import traceback
    traceback.print_exc()

# Test Auth Config
from src.config import GOOGLE_WEB_CLIENT_ID
print(f"Auth Client ID: {GOOGLE_WEB_CLIENT_ID}")
