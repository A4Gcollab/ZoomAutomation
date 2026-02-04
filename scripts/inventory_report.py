
import sqlite3
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vong_v2.db"

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def check_status():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("="*60)
    print("📊 SYSTEM INVENTORY REPORT")
    print("="*60)
    
    # 1. Status Counts
    print("\n[1] Overall Status Breakdown:")
    cur.execute("SELECT status, COUNT(*) FROM recordings GROUP BY status;")
    rows = cur.fetchall()
    for status, count in rows:
        print(f"    - {status:12}: {count} videos")

    # 2. Approved but not processed
    cur.execute("SELECT COUNT(*) FROM recordings WHERE status = 'APPROVED';")
    approved = cur.fetchone()[0]
    print(f"\n[2] Waiting for Action:")
    print(f"    - Approved (Ready to Upload): {approved} videos")

    # 3. Recent Processing
    cur.execute("SELECT topic, status, created_at FROM recordings ORDER BY created_at DESC LIMIT 10;")
    recent = cur.fetchall()
    print("\n[3] Latest Discoveries:")
    for topic, status, created in recent:
        print(f"    - [{status}] {topic[:40]}")

    print("\n" + "="*60)
    conn.close()

if __name__ == "__main__":
    check_status()
