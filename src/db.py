from tinydb import TinyDB, Query
from datetime import datetime
from . import config

class StateManager:
    def __init__(self, db_path=config.DB_PATH):
        self.db = TinyDB(db_path)
        self.recordings = self.db.table('recordings')
        self.Recording = Query()

    def exists(self, zoom_meeting_id):
        """Check if a recording has already been completely processed."""
        # This might need to be more granular (e.g., check if 'upload_status' is 'completed')
        result = self.recordings.get(self.Recording.zoom_id == zoom_meeting_id)
        if result and result.get('status') == 'completed':
            return True
        return False
    
    def get_recording_state(self, zoom_meeting_id):
        """Get the full state object for a recording."""
        return self.recordings.get(self.Recording.zoom_id == zoom_meeting_id)

    def mark_detected(self, zoom_id, metadata):
        """Mark a recording as detected but not yet processed."""
        if not self.recordings.contains(self.Recording.zoom_id == zoom_id):
            self.recordings.insert({
                'zoom_id': zoom_id,
                'metadata': metadata,
                'status': 'detected',
                'created_at': datetime.now().isoformat(),
                'download_timestamp': None,
                'youtube_upload_timestamp': None,
                'drive_upload_timestamp': None,
                'scheduled_deletion_at': None,
                'deleted_at': None,
                'steps': {
                    'downloaded': False,
                    'youtube_upload': False,
                    'youtube_id': None,
                    'playlist_id': None,
                    'playlist_name': None,
                    'category': None,
                    'drive_upload': False,
                    'drive_video_id': None,
                    'drive_transcript_id': None
                }
            })

    def update_step(self, zoom_id, step_name, value=True):
        """Update a specific step status."""
        # Get current record
        record = self.recordings.get(self.Recording.zoom_id == zoom_id)
        if record:
            # Update the nested steps field properly
            steps = record.get('steps', {})
            steps[step_name] = value
            self.recordings.update(
                {'steps': steps},
                self.Recording.zoom_id == zoom_id
            )

    def mark_completed(self, zoom_id):
        """Mark the entire pipeline as completed for this recording."""
        self.recordings.update(
            {'status': 'completed', 'completed_at': datetime.now().isoformat()},
            self.Recording.zoom_id == zoom_id
        )

    def mark_error(self, zoom_id, error_msg):
        """Log an error for a recording."""
        self.recordings.update(
            {'status': 'error', 'last_error': error_msg, 'error_at': datetime.now().isoformat()},
            self.Recording.zoom_id == zoom_id
        )
    
    def schedule_deletion(self, zoom_id, hours_delay=24):
        """Schedule a recording for deletion after specified hours."""
        from datetime import timedelta
        deletion_time = datetime.now() + timedelta(hours=hours_delay)
        self.recordings.update(
            {'scheduled_deletion_at': deletion_time.isoformat()},
            self.Recording.zoom_id == zoom_id
        )
    
    def get_recordings_for_deletion(self):
        """Get recordings that are ready for deletion."""
        now = datetime.now().isoformat()
        all_recordings = self.recordings.all()
        ready_for_deletion = []
        
        for rec in all_recordings:
            scheduled_at = rec.get('scheduled_deletion_at')
            if scheduled_at and scheduled_at <= now and not rec.get('deleted_at'):
                ready_for_deletion.append(rec)
        
        return ready_for_deletion
    
    def mark_deleted(self, zoom_id):
        """Mark a recording as deleted from Zoom."""
        self.recordings.update(
            {'deleted_at': datetime.now().isoformat()},
            self.Recording.zoom_id == zoom_id
        )
    
    def update_timestamp(self, zoom_id, timestamp_field):
        """Update a specific timestamp field (download_timestamp, youtube_upload_timestamp, etc.)."""
        self.recordings.update(
            {timestamp_field: datetime.now().isoformat()},
            self.Recording.zoom_id == zoom_id
        )
