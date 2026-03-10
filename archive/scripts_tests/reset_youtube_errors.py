"""
Reset videos that failed due to "YouTube client not initialized".

Now that the YouTube token is fixed, these videos can be reprocessed.
This script resets them back to APPROVED with retry_count = 0.

Usage:
    python reset_youtube_errors.py          # Preview what will be reset (dry run)
    python reset_youtube_errors.py --apply  # Actually reset the records
"""
import sqlite3
import sys

DB_PATH = "data/vong_v2.db"

def main():
    apply = "--apply" in sys.argv
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Find all ERROR records caused by YouTube client issues
    cur = conn.cursor()
    cur.execute("""
        SELECT zoom_id, topic, error_message, retry_count
        FROM recordings
        WHERE status = 'ERROR'
        AND (
            error_message LIKE '%YouTube client not initialized%'
            OR error_message LIKE '%Service Accounts do not have storage quo%'
        )
    """)
    rows = cur.fetchall()

    print(f"Found {len(rows)} videos with YouTube-related errors:\n")
    for r in rows:
        print(f"  - {r['topic']}")
        print(f"    Error: {r['error_message'][:80]}")
        print(f"    Retries: {r['retry_count']}")
        print()

    if not rows:
        print("Nothing to reset!")
        return

    if not apply:
        print("=" * 60)
        print("DRY RUN — no changes made.")
        print("Run with --apply to reset these videos:")
        print(f"  python reset_youtube_errors.py --apply")
        return

    # Reset to APPROVED so the pipeline picks them up
    cur.execute("""
        UPDATE recordings
        SET status = 'APPROVED',
            retry_count = 0,
            error_message = NULL
        WHERE status = 'ERROR'
        AND (
            error_message LIKE '%YouTube client not initialized%'
            OR error_message LIKE '%Service Accounts do not have storage quo%'
        )
    """)
    count = cur.rowcount
    conn.commit()
    conn.close()

    print(f"✅ Reset {count} videos back to APPROVED. They will be processed in the next cycle.")


if __name__ == "__main__":
    main()
