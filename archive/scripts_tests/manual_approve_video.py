from src.db_sql import db

zoom_id = "81992981065"
db.update_recording(zoom_id, {
    "team": "Tech",
    "playlist": "2.2.4 Tech Systems and Products",
    "status": "APPROVED",
    "approved_by": "System Test"
})
print("Video successfully approved in DB!")
