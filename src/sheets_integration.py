"""
Google Sheets integration for YTZ Automation.
- Main sheet: Tracks all recordings with status
- Logs sheet: Activity logs
"""

import gspread
import logging
from datetime import datetime
from src import config

logger = logging.getLogger("SheetManager")

class SheetManager:
    """Sheet Manager for recording tracking and activity logs."""

    # Main sheet columns (0-indexed)
    COL_DATE = 0
    COL_MEETING_ID = 1
    COL_TITLE = 2
    COL_TEAM = 3
    COL_PLAYLIST = 4
    COL_STATUS = 5
    COL_APPROVED_BY = 6
    COL_YOUTUBE_URL = 7
    COL_DRIVE_URL = 8

    def __init__(self, credentials, sheet_id=None):
        self.sheet_id = sheet_id or config.GOOGLE_SHEET_ID
        self.client = gspread.authorize(credentials)
        self.main_tab = None
        self.logs_tab = None

        try:
            self.doc = self.client.open_by_key(self.sheet_id)
            logger.info(f"Connected to Google Sheet: {self.doc.title}")
            self._setup_sheets()
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheet: {e}")
            raise

    def _setup_sheets(self):
        """Setup Main and Logs tabs."""
        # Main tab for recording tracking
        try:
            self.main_tab = self.doc.worksheet("Main")
            logger.info("Found Main tab")
        except gspread.exceptions.WorksheetNotFound:
            logger.info("Creating Main tab")
            self.main_tab = self.doc.add_worksheet(title="Main", rows="1000", cols="10")
            self.main_tab.append_row([
                "Date", "Meeting ID", "Title", "Team", "Playlist",
                "Status", "Approved By", "YouTube URL", "Drive Folder"
            ])
            self.main_tab.freeze(rows=1)

        # Logs tab for activity logs
        try:
            self.logs_tab = self.doc.worksheet("Logs")
            logger.info("Found Logs tab")
        except gspread.exceptions.WorksheetNotFound:
            logger.info("Creating Logs tab")
            self.logs_tab = self.doc.add_worksheet(title="Logs", rows="5000", cols="5")
            self.logs_tab.append_row(["Timestamp", "Level", "Action", "Details", "Status"])
            self.logs_tab.freeze(rows=1)

    # ==================== MAIN SHEET METHODS ====================

    def get_existing_ids(self):
        """Get all Meeting IDs currently in the Main Sheet."""
        try:
            if not self.main_tab:
                return []
            vals = self.main_tab.col_values(2)  # Column B = Meeting ID
            return vals[1:] if vals else []  # Skip header
        except Exception as e:
            logger.error(f"Failed to get existing IDs: {e}")
            return []

    def add_recording(self, rec):
        """Add a new recording to the Main sheet.

        Uses UUID as the unique identifier (truncated to 20 chars for readability).
        """
        if not self.main_tab:
            return False

        # Use UUID as the unique ID, truncated for readability
        uuid = str(rec.get('uuid', rec.get('id', '')))
        display_id = uuid[:20] if len(uuid) > 20 else uuid

        existing_ids = self.get_existing_ids()
        if display_id in existing_ids:
            logger.debug(f"Recording {display_id} already exists in sheet")
            return False

        try:
            date_str = rec.get('start_time', '')[:10] if rec.get('start_time') else ''
            row = [
                date_str,                      # Date
                display_id,                    # UUID (truncated)
                rec.get('topic', ''),          # Title
                rec.get('team', ''),           # Team
                rec.get('playlist', ''),       # Playlist
                "PENDING",                     # Status
                "",                            # Approved By
                "",                            # YouTube URL
                ""                             # Drive Folder
            ]
            self.main_tab.append_row(row)
            logger.info(f"Added recording {display_id} to Main sheet")
            return True
        except Exception as e:
            logger.error(f"Failed to add recording to sheet: {e}")
            return False

    def find_row_by_id(self, zoom_id):
        """Find the row number for a given zoom_id."""
        try:
            if not self.main_tab:
                return None
            cell = self.main_tab.find(str(zoom_id), in_column=2)
            return cell.row if cell else None
        except Exception as e:
            logger.warning(f"Failed to find row for {zoom_id}: {e}")
            return None

    def update_recording_status(self, zoom_id, status, youtube_url="", drive_url="", approved_by=""):
        """Update a recording's status and URLs in the Main sheet."""
        if not self.main_tab:
            return False

        try:
            row = self.find_row_by_id(zoom_id)
            if not row:
                logger.warning(f"Recording {zoom_id} not found in sheet")
                return False

            updates = []

            # Status (Column F)
            if status:
                updates.append({'range': f'F{row}', 'values': [[status]]})

            # Approved By (Column G)
            if approved_by:
                updates.append({'range': f'G{row}', 'values': [[approved_by]]})

            # YouTube URL (Column H)
            if youtube_url:
                updates.append({'range': f'H{row}', 'values': [[youtube_url]]})

            # Drive URL (Column I)
            if drive_url:
                updates.append({'range': f'I{row}', 'values': [[drive_url]]})

            if updates:
                self.main_tab.batch_update(updates)
                logger.info(f"Updated recording {zoom_id} in sheet: status={status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update recording {zoom_id}: {e}")
            return False

    def update_row_status(self, row_idx, status, youtube_url="", drive_url=""):
        """Update a row by index (legacy compatibility)."""
        try:
            if not self.main_tab:
                return

            updates = [{'range': f'F{row_idx}', 'values': [[status]]}]
            if youtube_url:
                updates.append({'range': f'H{row_idx}', 'values': [[youtube_url]]})
            if drive_url:
                updates.append({'range': f'I{row_idx}', 'values': [[drive_url]]})

            self.main_tab.batch_update(updates)
        except Exception as e:
            logger.error(f"Failed to update row {row_idx}: {e}")

    # ==================== LOGS SHEET METHODS ====================

    def log(self, action: str, details: str = "", status: str = "OK", level: str = "INFO"):
        """Log an activity to the Logs sheet."""
        if not self.logs_tab:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.logs_tab.append_row([timestamp, level, action, details, status])
        except Exception as e:
            logger.error(f"Failed to log to sheet: {e}")

    def log_scan(self, account_name: str, recordings_found: int):
        """Log a Zoom scan event."""
        self.log(
            action="Zoom Scan",
            details=f"Account: {account_name}, Found: {recordings_found} recordings",
            status="OK"
        )

    def log_approval(self, zoom_id: str, topic: str, approved_by: str):
        """Log when a recording is approved."""
        self.log(
            action="Recording Approved",
            details=f"ID: {zoom_id}, Topic: {topic}, By: {approved_by}",
            status="OK"
        )
        # Also update the main sheet
        self.update_recording_status(zoom_id, "APPROVED", approved_by=approved_by)

    def log_download(self, zoom_id: str, topic: str, success: bool = True, error: str = ""):
        """Log a download event."""
        self.log(
            action="Download from Zoom",
            details=f"ID: {zoom_id}, Topic: {topic}" + (f", Error: {error}" if error else ""),
            status="OK" if success else "ERROR",
            level="INFO" if success else "ERROR"
        )

    def log_youtube_upload(self, zoom_id: str, youtube_url: str, success: bool = True, error: str = ""):
        """Log a YouTube upload event."""
        self.log(
            action="YouTube Upload",
            details=f"ID: {zoom_id}, URL: {youtube_url}" + (f", Error: {error}" if error else ""),
            status="OK" if success else "ERROR",
            level="INFO" if success else "ERROR"
        )
        # Update main sheet with YouTube URL
        if success and youtube_url:
            self.update_recording_status(zoom_id, "PROCESSING", youtube_url=youtube_url)

    def log_drive_upload(self, zoom_id: str, drive_url: str, success: bool = True, error: str = ""):
        """Log a Drive backup event."""
        self.log(
            action="Drive Backup",
            details=f"ID: {zoom_id}, URL: {drive_url}" + (f", Error: {error}" if error else ""),
            status="OK" if success else "ERROR",
            level="INFO" if success else "ERROR"
        )
        # Update main sheet with Drive URL
        if success and drive_url:
            self.update_recording_status(zoom_id, "PROCESSING", drive_url=drive_url)

    def log_zoom_deletion(self, zoom_id: str, topic: str, success: bool = True, error: str = ""):
        """Log a Zoom deletion event."""
        self.log(
            action="Zoom Deletion",
            details=f"ID: {zoom_id}, Topic: {topic}" + (f", Error: {error}" if error else ""),
            status="OK" if success else "ERROR",
            level="INFO" if success else "ERROR"
        )

    def log_completion(self, zoom_id: str, topic: str, youtube_url: str, drive_url: str):
        """Log when a recording is fully processed."""
        self.log(
            action="Processing Complete",
            details=f"ID: {zoom_id}, Topic: {topic}",
            status="OK"
        )
        # Update main sheet to COMPLETED with all URLs
        self.update_recording_status(zoom_id, "COMPLETED", youtube_url=youtube_url, drive_url=drive_url)

    def log_error(self, action: str, error: str, zoom_id: str = ""):
        """Log an error."""
        self.log(
            action=action,
            details=f"ID: {zoom_id}, Error: {error}" if zoom_id else f"Error: {error}",
            status="ERROR",
            level="ERROR"
        )
        # Update main sheet to ERROR status
        if zoom_id:
            self.update_recording_status(zoom_id, "ERROR")

    def log_service_start(self):
        """Log service start."""
        self.log(action="Service Started", details="Background automation service started", status="OK")

    def log_service_stop(self):
        """Log service stop."""
        self.log(action="Service Stopped", details="Background automation service stopped", status="OK")
