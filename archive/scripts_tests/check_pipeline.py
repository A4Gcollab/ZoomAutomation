"""
Diagnostic script: Check exactly what's happening with the processing pipeline.
Run this on the Vultr server: python check_pipeline.py
"""
import sys, os
sys.path.insert(0, '.')
import sqlite3

DB_PATH = 'data/vong_v2.db'

def check():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=" * 70)
    print("PIPELINE DIAGNOSTIC REPORT")
    print("=" * 70)
    
    # 1. Status counts
    cur.execute("SELECT status, COUNT(*) as cnt FROM recordings GROUP BY status ORDER BY cnt DESC")
    rows = cur.fetchall()
    print("\n📊 VIDEO STATUS COUNTS:")
    for r in rows:
        print(f"   {r['status']}: {r['cnt']}")
    
    # 2. Check APPROVED videos (should be processing)
    cur.execute("SELECT zoom_id, topic, team, playlist FROM recordings WHERE status = 'APPROVED' LIMIT 10")
    approved = cur.fetchall()
    print(f"\n🟡 APPROVED (waiting to be processed): {len(approved)} shown (of total)")
    for r in approved:
        print(f"   - {r['topic'][:50]} | team={r['team']} | playlist={r['playlist']}")
    
    # 3. Check PROCESSING videos (actively being handled)
    cur.execute("SELECT zoom_id, topic, processed_at FROM recordings WHERE status = 'PROCESSING'")
    processing = cur.fetchall()
    print(f"\n🔄 PROCESSING (actively downloading/uploading): {len(processing)}")
    for r in processing:
        print(f"   - {r['topic'][:50]} | started: {r['processed_at']}")
    
    # 4. Check YOUTUBE_COMPRESSING videos
    cur.execute("SELECT zoom_id, topic, youtube_url FROM recordings WHERE status = 'YOUTUBE_COMPRESSING'")
    compressing = cur.fetchall()
    print(f"\n⏳ YOUTUBE_COMPRESSING (waiting for YT to finish): {len(compressing)}")
    for r in compressing:
        print(f"   - {r['topic'][:50]} | {r['youtube_url']}")
    
    # 5. Check COMPLETED videos
    cur.execute("SELECT topic, youtube_url, drive_url FROM recordings WHERE status = 'COMPLETED' LIMIT 10")
    completed = cur.fetchall()
    print(f"\n✅ COMPLETED: {len(completed)} shown")
    for r in completed:
        print(f"   - {r['topic'][:50]}")
        print(f"     YT: {r['youtube_url']}")
        print(f"     Drive: {r['drive_url']}")
    
    # 6. Check ERROR videos
    cur.execute("SELECT topic, error_message, retry_count FROM recordings WHERE status = 'ERROR' LIMIT 10")
    errors = cur.fetchall()
    print(f"\n❌ ERRORS: {len(errors)} shown")
    for r in errors:
        print(f"   - {r['topic'][:50]}")
        print(f"     Error: {r['error_message'][:100] if r['error_message'] else 'None'}")
        print(f"     Retries: {r['retry_count']}")
    
    # 7. Check recent logs
    cur.execute("SELECT timestamp, level, message FROM logs ORDER BY id DESC LIMIT 20")
    logs = cur.fetchall()
    print(f"\n📋 RECENT SYSTEM LOGS (last 20):")
    for r in logs:
        print(f"   [{r['level']}] {r['timestamp']} - {r['message'][:80]}")
    
    # 8. Check if secrets exist
    print(f"\n🔑 SECRETS/CREDENTIALS CHECK:")
    secrets_files = [
        'secrets/token_youtube.json',
        'secrets/token_drive.json', 
        'secrets/service_account.json',
        'secrets/youtube_cookies.txt',
        'secrets/client_secret.json'
    ]
    for f in secrets_files:
        exists = os.path.exists(f)
        size = os.path.getsize(f) if exists else 0
        print(f"   {'✅' if exists else '❌'} {f} {'(' + str(size) + ' bytes)' if exists else '(MISSING!)'}")
    
    conn.close()
    print("\n" + "=" * 70)

if __name__ == "__main__":
    check()
