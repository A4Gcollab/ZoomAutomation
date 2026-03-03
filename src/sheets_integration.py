
import gspread
import logging
from datetime import datetime
from src import config
from src.sheet_schema_v2 import SheetSchemaV2

logger = logging.getLogger("SheetManager")

class SheetManager:
    def __init__(self, credentials, sheet_id=None):
        self.sheet_id = sheet_id or config.GOOGLE_SHEET_ID
        # FORCE RELOAD V3
        self.client = gspread.authorize(credentials)
        
        # Retry with exponential backoff for transient API errors (429, 500, 503)
        max_retries = 3
        backoff_times = [10, 30, 60]  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                self.doc = self.client.open_by_key(self.sheet_id)
                logger.info(f"Connected to Google Sheet: {self.doc.title}")
                
                # Cache Tabs Safely
                self.settings_tab = self._safe_get_worksheet(SheetSchemaV2.TAB_SETTINGS)
                self.logs_tab = self._safe_get_worksheet(SheetSchemaV2.TAB_LOGS)
                self.dashboard_tab = self._safe_get_worksheet(SheetSchemaV2.TAB_DASHBOARD)
                self.main_tab = self._safe_get_worksheet(SheetSchemaV2.TAB_MAIN)
                
                # Ensure all tabs exist and have headers
                self.ensure_tabs()
                break  # Success — exit retry loop
                
            except gspread.exceptions.APIError as e:
                error_code = e.response.status_code if hasattr(e, 'response') else 0
                if error_code in (429, 500, 503) and attempt < max_retries:
                    wait = backoff_times[attempt]
                    logger.warning(f"Google Sheets API error {error_code} (attempt {attempt + 1}/{max_retries}). Retrying in {wait}s...")
                    import time
                    time.sleep(wait)
                else:
                    logger.error(f"Failed to connect to Google Sheet: {e}")
                    raise
            except Exception as e:
                logger.error(f"Failed to connect to Google Sheet: {e}")
                raise

    def _safe_get_worksheet(self, title):
        """Safely get a worksheet by title, returning None if not found."""
        try:
            return self.doc.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            logger.warning(f"Worksheet '{title}' not found. Some features may be disabled.")
            return None
        except Exception as e:
            logger.error(f"Error fetching worksheet '{title}': {e}")
            return None

    def ensure_tabs(self):
        """Ensure all required worksheets exist and have correct headers."""
        try:
            # 1. Main Tab
            if not self.main_tab:
                logger.info(f"Creating worksheet '{SheetSchemaV2.TAB_MAIN}'")
                self.main_tab = self.doc.add_worksheet(title=SheetSchemaV2.TAB_MAIN, rows="1000", cols="20")
                self.main_tab.append_row(SheetSchemaV2.HEADERS_MAIN)
            
            # 2. Settings Tab
            if not self.settings_tab:
                logger.info(f"Creating worksheet '{SheetSchemaV2.TAB_SETTINGS}'")
                self.settings_tab = self.doc.add_worksheet(title=SheetSchemaV2.TAB_SETTINGS, rows="100", cols="5")
                self.settings_tab.append_row(["KEY", "VALUE"])
                self.settings_tab.append_row([SheetSchemaV2.KEY_COMMAND, SheetSchemaV2.CMD_IDLE])
                self.settings_tab.append_row([SheetSchemaV2.KEY_LAST_RUN, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            
            # 3. Logs Tab
            if not self.logs_tab:
                logger.info(f"Creating worksheet '{SheetSchemaV2.TAB_LOGS}'")
                self.logs_tab = self.doc.add_worksheet(title=SheetSchemaV2.TAB_LOGS, rows="2000", cols="5")
                self.logs_tab.append_row(["TIMESTAMP", "MESSAGE"])
            
            # 4. Dashboard Tab
            if not self.dashboard_tab:
                logger.info(f"Creating worksheet '{SheetSchemaV2.TAB_DASHBOARD}'")
                self.dashboard_tab = self.doc.add_worksheet(title=SheetSchemaV2.TAB_DASHBOARD, rows="100", cols="5")
                self.dashboard_tab.append_row(["METRIC", "VALUE"])
                self.dashboard_tab.append_row(["Total Processed", "0"])
                self.dashboard_tab.append_row(["Storage Saved", "0 GB"])
                self.dashboard_tab.append_row(["Last Sync", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

        except Exception as e:
            logger.error(f"Failed to ensure worksheets: {e}")

    def check_command_state(self):
        """
        Poll the Settings tab for the current COMMAND state.
        Returns: 'IDLE', 'START', or 'REFRESH'
        """
        try:
            # Assuming A1 is 'COMMAND' and B1 is the value
            # Actually schema says A1:B2, where A1=Key, B1=Value might be safer to lookup
            # Let's read the whole A:B range
            if not self.settings_tab:
                return SheetSchemaV2.CMD_IDLE
            
            records = self.settings_tab.get_all_values()
            for row in records:
                if row[0] == SheetSchemaV2.KEY_COMMAND:
                    return row[1].strip().upper()
            return SheetSchemaV2.CMD_IDLE
        except Exception as e:
            logger.error(f"Failed to read command state: {e}")
            return SheetSchemaV2.CMD_IDLE

    def set_command_state(self, state):
        """Reset the command state (e.g. back to IDLE after running)."""
        try:
            # We need to find the cell.
            if not self.settings_tab: return
            cell = self.settings_tab.find(SheetSchemaV2.KEY_COMMAND)
            if cell:
                self.settings_tab.update_cell(cell.row, cell.col + 1, state)
        except Exception as e:
            logger.error(f"Failed to set command state: {e}")

    def log_system_status(self, message, level="INFO"):
        """Write a log entry to System_Logs tab."""
        if not self.logs_tab: return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Prepend to top (Row 2) to keep latest visible? 
            # Appending is faster. Let's stick to append.
            self.logs_tab.append_row([timestamp, f"[{level}] {message}"])
            # Keep log size managed? (Optional future optimization)
        except Exception:
            pass

    def update_dashboard(self, processed_count, saved_space_gb):
        """Update Dashboard metrics."""
        if not self.dashboard_tab: return
        try:
            # Hardcoded based on setup script
            # B2: Total Processed
            # B3: Storage Saved
            # B4: Last Sync
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.dashboard_tab.update(range_name='B2:B4', values=[[processed_count], [f"{saved_space_gb:.2f} GB"], [timestamp]])
        except Exception:
            pass

    def get_existing_ids(self):
        """Get all Meeting IDs currently in the Main Sheet."""
        try:
            # Meeting ID is Column 2 (Index 1)
            # col_values(2) returns the whole column including header
            if not self.main_tab: return []
            vals = self.main_tab.col_values(2)
            return vals[1:] if vals else []
        except Exception:
            return []

    def log_new_recordings(self, recordings_list):
        """
        Add new recordings to the sheet in PENDING status.
        Does NOT set Team or Playlist (User must fill them).
        Includes deduplication to prevent adding existing recordings.
        """
        existing_ids = set(self.get_existing_ids())
        logger.debug(f"Found {len(existing_ids)} existing recordings in sheet")
        
        new_rows = []
        skipped_count = 0
        
        for rec in recordings_list:
            zoom_id = str(rec.get('uuid', rec.get('id', '')))
            
            if not zoom_id:
                logger.debug("Skipping recording with empty ID")
                skipped_count += 1
                continue
                
            if zoom_id in existing_ids:
                logger.debug(f"Skipping duplicate: {zoom_id} - {rec.get('topic', 'Unknown')}")
                skipped_count += 1
                continue
            
            # Schema: Date, ID, Title, Team, Playlist, Status, ApprovedBy, YT, Drive
            date_str = rec.get('start_time', '')[:10]
            
            row = [
                date_str,                  # Date
                zoom_id,                   # Meeting ID
                rec.get('topic', ''),      # Title
                rec.get('team', ''),       # Team (Auto or Manual)
                rec.get('playlist', ''),   # Playlist (Auto or Manual)
                "PENDING",                 # Status
                "",                        # Approved By (Manual)
                "",                        # YT Link
                ""                         # Drive Link
            ]
            new_rows.append(row)
            existing_ids.add(zoom_id)  # Add to set to prevent duplicates within this batch
            logger.debug(f"Queued new recording: {zoom_id} - {rec.get('topic', 'Unknown')}")
            
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} duplicate/invalid recordings")
            
        if new_rows:
            logger.info(f"Adding {len(new_rows)} new recordings to Sheet.")
            if self.main_tab:
                self.main_tab.append_rows(new_rows)
            return len(new_rows)
        return 0

    def add_recording(self, rec):
        """Add a single recording to the sheet."""
        zoom_id = str(rec.get('uuid', rec.get('id', '')))
        existing_ids = self.get_existing_ids()
        if zoom_id in existing_ids:
            return False
            
        date_str = rec.get('start_time', '')[:10]
        row = [
            date_str, 
            zoom_id, 
            rec.get('topic', ''), 
            rec.get('team', ''), 
            rec.get('playlist', ''), 
            "PENDING", 
            "", 
            "", 
            ""
        ]
        if self.main_tab:
            self.main_tab.append_row(row)
            return True
        return False

    def get_pending_approvals(self):
        """
        Get rows that are 'PENDING' but have been 'Approved' by a user.
        Validation: Must have 'Approved By', 'Team', and 'Playlist' filled.
        """
        try:
            if not self.main_tab: return []
            all_values = self.main_tab.get_all_values()
            if not all_values: return []
            
            headers = all_values[0]
            rows = all_values[1:]
            
            tasks = []
            
            # Indexes (0-based from logic view)
            # 0: Date, 1: ID, 2: Title, 3: Team, 4: Playlist
            # 5: Status, 6: Approved By
            
            for idx, row in enumerate(rows):
                if len(row) < 7: continue # Malformed row
                
                status = row[5].strip().upper()
                approved_by = row[6].strip()
                team = row[3].strip()
                playlist = row[4].strip()
                
                if status == 'PENDING' and approved_by and team and playlist:
                    # VALID TASK
                    tasks.append({
                        'row_idx': idx + 2, # Sheet is 1-based, +1 for header
                        'date': row[0],
                        'meeting_id': row[1],
                        'topic': row[2],
                        'team': team,
                        'playlist': playlist,
                        'approved_by': approved_by
                    })
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to fetch pending approvals: {e}")
            return []

    def update_row_status(self, row_idx, status, youtube_url="", drive_url=""):
        """Update a row's status and links."""
        try:
            # Status is Col 6 (F), YT is Col 8 (H), Drive is Col 9 (I)
            # batch_update is efficient
            updates = [
                {'range': f'F{row_idx}', 'values': [[status]]},
            ]
            if youtube_url:
                updates.append({'range': f'H{row_idx}', 'values': [[youtube_url]]})
            if drive_url:
                updates.append({'range': f'I{row_idx}', 'values': [[drive_url]]})
                
            if self.main_tab:
                self.main_tab.batch_update(updates)
        except Exception as e:
            logger.error(f"Failed to update row {row_idx}: {e}")
