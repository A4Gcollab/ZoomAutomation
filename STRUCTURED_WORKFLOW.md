# YTZ Automation - Complete Structured Workflow

## Overview
This document defines the **exact, rigid workflow** that the system follows for every recording.

## Pre-Configured Structure

### YouTube Playlists (EXISTING - DO NOT CREATE NEW)
- `PLXGtGl2Kq18ak7zQvO16G1nnItDlI7Wno` - 2.2.5 Enablers - HR
- `PLXGtGl2Kq18ZQ99TeNVq1-6hxdACNSQ-T` - 2.2.4 Tech Systems and Products
- `PLXGtGl2Kq18YZ1WfSeUlHQQfLod__UyaM` - 2.2.1 Marketing
- `PLXGtGl2Kq18bb0NrayYkB3ijzRXvoBKip` - 2.2.2 Growth
- `PLXGtGl2Kq18a6rXXhp-O4LT8XQ1ySWB1Q` - 2.2.5 Enablers - PM
- `PLXGtGl2Kq18aRxwVpnHliHrzViIpGWdm-` - 2.2.3 Research Analysis Bureau RAB
- `PLXGtGl2Kq18Y5J9avj1liSNDRPSGA21Yx` - 2.2.6 Community Building
- `PLXGtGl2Kq18Z97SIS-64aX7nSNo3NjI_R` - 2.2.5 Enablers - OPM & HR
- `PLXGtGl2Kq18bQ__BBhHz_TD_usIqxzYHJ` - Essay Contest
- `PLXGtGl2Kq18YHzkoQ4Bo_QiGczX0qaooU` - 2.2.5 Enablers

### Google Drive Folders (EXISTING - DO NOT CREATE NEW)
- HR
- Tech
- Marketing
- Growth
- Project Management
- Research
- Community
- OPM
- Events
- Enablers

## Complete Processing Workflow

### Phase 1: Discovery & Ingestion
1. **Scan Zoom** (Every 60 seconds)
   - Query last 90 days from all configured accounts
   - Extract meeting metadata (ID, topic, date, duration, files)
   
2. **Auto-Match Team/Playlist**
   - Check `config/playlists.json` for meeting_id match
   - If found: Auto-populate Team and Playlist columns
   - If not found: Leave blank for manual entry

3. **Add to Database & Google Sheet**
   - Insert into SQLite database with status `PENDING`
   - Append row to Google Sheet "Main" tab
   - Columns: Date | Meeting ID | Title | Team | Playlist | Status | Approved By | YouTube URL | Drive URL

### Phase 2: Approval (Manual)
User reviews Google Sheet and fills:
- **Team**: Must match one of the pre-configured categories
- **Playlist**: Must match one of the existing playlist names
- **Approved By**: User's name/email

Once these 3 fields are filled, status remains `PENDING` but is now eligible for processing.

### Phase 3: Processing (Automated)
For each approved recording:

1. **Update Status to PROCESSING**
   - Database: `status = 'PROCESSING'`
   - Google Sheet: Status column = `PROCESSING`

2. **Download from Zoom**
   - Download MP4 video file
   - Download VTT transcript file (if available)
   - Save to `data/downloads/` with format: `YYYYMMDD Topic Name.mp4`

3. **Upload to YouTube**
   - Title: `YYYYMMDD Topic Name`
   - Description: Include topic, date, team, playlist
   - Privacy: `unlisted`
   - **Upload VTT as captions** (language: English)
   - **Add to specified playlist** (from approval)
   - Get YouTube URL: `https://youtu.be/{video_id}`

4. **Upload to Google Drive**
   - Navigate to Team folder (create if doesn't exist)
   - Upload video file with same name: `YYYYMMDD Topic Name.mp4`
   - Upload transcript file: `YYYYMMDD Topic Name_transcript.txt`
   - Get Drive URL: `https://drive.google.com/file/d/{file_id}/view`

5. **Verify Uploads**
   - Confirm YouTube video is accessible
   - Confirm Drive files are accessible
   - If either fails: STOP and mark as ERROR

6. **Delete from Zoom** (ONLY after successful verification)
   - Call Zoom API: `DELETE /meetings/{meeting_id}/recordings`
   - Action: `delete` (permanent deletion)
   - Log deletion timestamp

7. **Cleanup Local Files**
   - Delete downloaded video from `data/downloads/`
   - Delete downloaded transcript from `data/downloads/`

8. **Update Final Status**
   - Database: `status = 'COMPLETED'`, add YouTube URL, Drive URL, processed timestamp
   - Google Sheet: Status = `COMPLETED`, populate YouTube URL and Drive URL columns
   - Log: "✅ Completed: {meeting_id} - {title}"

### Phase 4: Error Handling
If ANY step fails:
1. **Update Status to ERROR**
   - Database: `status = 'ERROR'`, `error_message = {exception}`
   - Google Sheet: Status = `ERROR`
2. **DO NOT delete from Zoom**
3. **DO NOT delete local files** (for manual recovery)
4. **Log detailed error** for debugging
5. **Send notification** (if configured)

## Safety Protocols

### Critical Rules
1. **NEVER delete from Zoom** until YouTube AND Drive uploads are verified
2. **NEVER create new playlists** - only use existing ones from `playlists.json`
3. **NEVER create new Drive folders** at root level - only use existing team folders
4. **ALWAYS upload transcripts** if available (both to YouTube as captions and Drive as file)
5. **ALWAYS use the exact naming format**: `YYYYMMDD Topic Name`

### Verification Checklist
Before marking as COMPLETED:
- [ ] YouTube video is accessible
- [ ] YouTube captions are uploaded (if transcript exists)
- [ ] Video is added to correct playlist
- [ ] Drive video file is uploaded
- [ ] Drive transcript file is uploaded (if exists)
- [ ] Google Sheet is updated with both URLs
- [ ] Database is updated with both URLs
- [ ] Zoom recording is deleted
- [ ] Local files are cleaned up

## Configuration Files

### `config/playlists.json`
Maps meeting IDs to playlists. Format:
```json
{
  "playlist_id": "PLXGtGl2Kq18...",
  "playlist_name": "2.2.1 Marketing",
  "category": "Marketing",
  "meeting_ids": ["88986938073"]
}
```

### Google Sheet Schema
| Date | Meeting ID | Title | Team | Playlist | Status | Approved By | YouTube URL | Drive URL |
|------|------------|-------|------|----------|--------|-------------|-------------|-----------|

### Database Schema
```sql
CREATE TABLE recordings (
    zoom_id TEXT PRIMARY KEY,
    account_name TEXT,
    topic TEXT,
    start_time TEXT,
    date_str TEXT,
    status TEXT DEFAULT 'PENDING',
    team TEXT,
    playlist TEXT,
    approved_by TEXT,
    video_url TEXT,
    transcript_url TEXT,
    youtube_url TEXT,
    drive_url TEXT,
    metadata JSON,
    created_at TIMESTAMP,
    processed_at TIMESTAMP,
    error_message TEXT
)
```

## Monitoring & Logs

### Log Levels
- **INFO**: Normal operations (scan, upload, completion)
- **WARNING**: Non-critical issues (missing transcript, playlist add failed)
- **ERROR**: Critical failures (upload failed, API error)

### Key Metrics
- Total recordings discovered
- Total recordings processed
- Total recordings pending approval
- Total recordings in error state
- Storage saved (GB)
- Last scan timestamp
- Last processing timestamp

## Deployment Notes

### Environment Variables Required
```bash
# Zoom Accounts
ZOOM_1_ACCOUNT_ID=...
ZOOM_1_CLIENT_ID=...
ZOOM_1_CLIENT_SECRET=...
ZOOM_2_ACCOUNT_ID=...
ZOOM_2_CLIENT_ID=...
ZOOM_2_CLIENT_SECRET=...

# Google Services
GOOGLE_SHEET_ID=...
YOUTUBE_CLIENT_SECRET_PATH=...
YOUTUBE_TOKEN_PATH=...
DRIVE_TOKEN_PATH=...
DRIVE_SERVICE_ACCOUNT_FILE=...
```

### Service Startup
```bash
# Backend
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run dev -- -p 9002
```

### Health Checks
- API: `GET /health`
- Service Status: `GET /service/status`
- Recent Logs: `GET /logs?lines=100`
