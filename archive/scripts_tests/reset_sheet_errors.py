"""
Reset Google Sheet 'ERROR' rows back to 'PENDING'.

When videos were approved via the Google Sheet and then failed (e.g., YouTube auth),
main.py updated the Sheet row to 'ERROR'.
Our previous `reset_youtube_errors.py` script only reset the local SQL database,
which means SheetManager.get_pending_approvals() is STILL ignoring them because
their Sheet row says 'ERROR' instead of 'PENDING'.

This script fixes that by resetting those rows in the Google Sheet itself.
"""
import sys
import logging
from src import config
from src.drive_client import DriveClient
from src.sheets_integration import SheetManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("SheetReset")

def main():
    apply = "--apply" in sys.argv
    
    # 1. Connect to Drive/Sheets
    logger.info("Connecting to Google Sheets...")
    drive = DriveClient(
        auth_mode=config.DRIVE_AUTH_MODE,
        service_account_file=config.DRIVE_SERVICE_ACCOUNT_FILE,
        client_secret_path=config.YOUTUBE_CLIENT_SECRET_PATH,
        token_path=config.DRIVE_TOKEN_PATH
    )
    sm = SheetManager(drive.credentials)
    
    if not sm.main_tab:
        logger.error("Could not find the Main tab in the Google Sheet.")
        return
        
    # 2. Get all rows
    logger.info("Fetching all rows from the Main tab...")
    all_values = sm.main_tab.get_all_values()
    if not all_values or len(all_values) < 2:
        logger.info("No data found in sheet.")
        return
        
    headers = all_values[0]
    rows = all_values[1:]
    
    to_reset = []
    
    # Indexes (0-based)
    # 0: Date, 1: ID, 2: Title, 3: Team, 4: Playlist
    # 5: Status, 6: Approved By
    for idx, row in enumerate(rows):
        if len(row) < 7: continue
        
        status = row[5].strip().upper()
        # Look for ERROR rows that have an approver (meaning they were approved and then failed)
        if status == 'ERROR' and row[6].strip():
            # Add to list (idx + 2 because rows is 0-indexed, and sheet has 1 header row + is 1-indexed)
            to_reset.append({
                'row_idx': idx + 2,
                'topic': row[2],
                'team': row[3],
                'playlist': row[4],
                'approved_by': row[6]
            })
            
    print(f"\nFound {len(to_reset)} ERROR rows in Google Sheet that need resetting:")
    for task in to_reset:
        print(f"  Row {task['row_idx']}: {task['topic']}")
        
    if not to_reset:
        print("\nNothing to reset in the Google Sheet!")
        return
        
    if not apply:
        print("\n" + "="*60)
        print("DRY RUN — no changes made to the Google Sheet.")
        print("Run with --apply to reset these rows back to PENDING:")
        print("  python reset_sheet_errors.py --apply")
        return
        
    # 3. Apply changes (Batch Update)
    print("\nResetting rows in Google Sheet...")
    # Update the Status column (Column F) back to PENDING
    # Also clear the YouTube and Drive Links (Columns M and N) just in case
    
    updates = []
    for task in to_reset:
        row_num = task['row_idx']
        updates.extend([
            {'range': f'F{row_num}', 'values': [['PENDING']]},
            {'range': f'M{row_num}:N{row_num}', 'values': [['', '']]}  # Clear link columns
        ])
    
    # We do a batch update to avoid hitting rate limits
    sm.main_tab.batch_update(updates)
    print(f"\n✅ Reset {len(to_reset)} rows in Google Sheet back to PENDING.")
    print("They will be picked up by the pipeline in the next cycle!")


if __name__ == "__main__":
    main()
