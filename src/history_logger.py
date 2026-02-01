"""
Historical Logging System
Tracks all upload operations with comprehensive metadata including:
- Upload date/time
- Recording metadata (title, date, meeting ID)
- Playlist assignment
- YouTube and Google Drive links
- Processing status and errors
- Approver information
- Processing duration
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger("HistoryLogger")

class HistoryLogger:
    """Comprehensive logging system for tracking all automation operations"""
    
    def __init__(self, sheet_manager=None):
        """
        Initialize history logger
        
        Args:
            sheet_manager: Optional SheetManager instance for Google Sheets logging
        """
        self.sheet_manager = sheet_manager
        self.current_operation = {}
    
    def start_operation(self, zoom_id: str, metadata: Dict[str, Any]):
        """
        Start tracking a new operation
        
        Args:
            zoom_id: Zoom meeting ID
            metadata: Recording metadata (title, date, etc.)
        """
        self.current_operation[zoom_id] = {
            'zoom_id': zoom_id,
            'title': metadata.get('topic', 'Untitled'),
            'recording_date': metadata.get('start_time', ''),
            'start_time': datetime.now(),
            'status': 'PROCESSING',
            'errors': [],
            'metadata': metadata
        }
        logger.info(f"Started operation for: {metadata.get('topic', zoom_id)}")
    
    def log_step(self, zoom_id: str, step: str, details: Optional[str] = None):
        """
        Log a processing step
        
        Args:
            zoom_id: Zoom meeting ID
            step: Step name (e.g., 'download', 'youtube_upload', 'drive_upload')
            details: Optional details about the step
        """
        if zoom_id not in self.current_operation:
            logger.warning(f"No operation found for {zoom_id}")
            return
        
        if 'steps' not in self.current_operation[zoom_id]:
            self.current_operation[zoom_id]['steps'] = []
        
        self.current_operation[zoom_id]['steps'].append({
            'step': step,
            'timestamp': datetime.now().isoformat(),
            'details': details
        })
        
        log_msg = f"[{zoom_id}] {step}"
        if details:
            log_msg += f": {details}"
        logger.info(log_msg)
    
    def log_youtube_upload(self, zoom_id: str, video_id: str, playlist: str):
        """
        Log successful YouTube upload
        
        Args:
            zoom_id: Zoom meeting ID
            video_id: YouTube video ID
            playlist: Playlist name
        """
        if zoom_id in self.current_operation:
            self.current_operation[zoom_id]['youtube_id'] = video_id
            self.current_operation[zoom_id]['youtube_url'] = f"https://youtu.be/{video_id}"
            self.current_operation[zoom_id]['playlist'] = playlist
            self.log_step(zoom_id, 'youtube_upload', f"Video ID: {video_id}, Playlist: {playlist}")
    
    def log_drive_upload(self, zoom_id: str, folder_id: str, folder_path: str):
        """
        Log successful Google Drive upload
        
        Args:
            zoom_id: Zoom meeting ID
            folder_id: Drive folder ID
            folder_path: Human-readable folder path
        """
        if zoom_id in self.current_operation:
            self.current_operation[zoom_id]['drive_folder_id'] = folder_id
            self.current_operation[zoom_id]['drive_url'] = f"https://drive.google.com/drive/folders/{folder_id}"
            self.current_operation[zoom_id]['drive_path'] = folder_path
            self.log_step(zoom_id, 'drive_upload', f"Path: {folder_path}")
    
    def log_error(self, zoom_id: str, error: str, step: Optional[str] = None):
        """
        Log an error during processing
        
        Args:
            zoom_id: Zoom meeting ID
            error: Error message
            step: Optional step where error occurred
        """
        if zoom_id not in self.current_operation:
            self.current_operation[zoom_id] = {
                'zoom_id': zoom_id,
                'start_time': datetime.now(),
                'status': 'ERROR',
                'errors': []
            }
        
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': error,
            'step': step
        }
        
        self.current_operation[zoom_id]['errors'].append(error_entry)
        self.current_operation[zoom_id]['status'] = 'ERROR'
        
        logger.error(f"[{zoom_id}] Error in {step or 'unknown step'}: {error}")
    
    def complete_operation(self, zoom_id: str, approved_by: str, team: str, playlist: str):
        """
        Mark operation as complete and log to history
        
        Args:
            zoom_id: Zoom meeting ID
            approved_by: Email of approver
            team: Team name
            playlist: Playlist name
        """
        if zoom_id not in self.current_operation:
            logger.warning(f"No operation found for {zoom_id}")
            return
        
        operation = self.current_operation[zoom_id]
        operation['end_time'] = datetime.now()
        operation['duration'] = (operation['end_time'] - operation['start_time']).total_seconds()
        operation['approved_by'] = approved_by
        operation['team'] = team
        operation['playlist'] = playlist
        
        if not operation.get('errors'):
            operation['status'] = 'COMPLETED'
        
        # Log to Google Sheets if available
        if self.sheet_manager:
            self._log_to_sheets(operation)
        
        # Log summary
        status = operation['status']
        duration = operation['duration']
        logger.info(f"[{zoom_id}] Operation {status} in {duration:.1f}s")
        
        # Clean up
        del self.current_operation[zoom_id]
    
    def _log_to_sheets(self, operation: Dict[str, Any]):
        """
        Log operation to Google Sheets history tab
        
        Args:
            operation: Operation data dictionary
        """
        try:
            # Check if Upload History tab exists, create if not
            try:
                history_tab = self.sheet_manager.doc.worksheet("Upload History")
            except:
                # Create Upload History tab
                history_tab = self.sheet_manager.doc.add_worksheet(
                    title="Upload History",
                    rows=1000,
                    cols=12
                )
                # Add headers
                headers = [
                    "Upload Date", "Recording Date", "Meeting ID", "Title",
                    "Team", "Playlist", "YouTube Link", "Drive Link",
                    "Status", "Errors", "Approved By", "Duration (s)"
                ]
                history_tab.update('A1:L1', [headers])
                history_tab.format('A1:L1', {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                })
            
            # Prepare row data
            row = [
                operation.get('end_time', datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
                operation.get('recording_date', '')[:10],
                operation.get('zoom_id', ''),
                operation.get('title', ''),
                operation.get('team', ''),
                operation.get('playlist', ''),
                operation.get('youtube_url', ''),
                operation.get('drive_url', ''),
                operation.get('status', ''),
                '; '.join([e['message'] for e in operation.get('errors', [])]),
                operation.get('approved_by', ''),
                f"{operation.get('duration', 0):.1f}"
            ]
            
            # Append to sheet
            history_tab.append_row(row)
            logger.info(f"Logged to Upload History sheet: {operation.get('title', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to log to Google Sheets: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics
        
        Returns:
            Dictionary with statistics
        """
        # This would query the history tab or database
        # For now, return basic info
        return {
            'active_operations': len(self.current_operation),
            'operations': list(self.current_operation.keys())
        }
