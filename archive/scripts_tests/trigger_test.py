from src.db_sql import db

pending = db.get_pending()
if not pending:
    print("No pending videos found to test.")
    exit(0)

# Pick the first pending video
video = pending[0]
zoom_id = video['zoom_id']
topic = video['topic']
meeting_id = video.get('meeting_id', zoom_id)

print(f"Triggering pipeline for test video: {topic} ({zoom_id})")

# Set it to APPROVED and assign a test playlist temporarily if it doesn't have one
updates = {
    'status': 'APPROVED',
    'team': video.get('team') or 'Tech',
    'playlist': video.get('playlist') or '2.2.4 Tech Systems and Products',
    'approved_by': 'Auto Test Script'
}

db.update_recording(zoom_id, updates)

print("Video successfully APPROVED!")
print("The background service will pick this up automatically within the next 60 seconds.")
print("Watch the logs: sudo journalctl -u ytz-backend -f")
