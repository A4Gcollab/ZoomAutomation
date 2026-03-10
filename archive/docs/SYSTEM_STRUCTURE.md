# YTZ Automation - Complete System Structure

## ✅ FINAL IMPLEMENTATION STATUS

### Core Workflow (100% Complete)
The system now follows this **exact, rigid structure**:

1. **Discovery** (Every 60 seconds)
   - Scans last 90 days from both Zoom accounts
   - Auto-matches recordings to existing playlists using `config/playlists.json`
   - Adds to database and Google Sheet with status `PENDING`

2. **Approval** (Manual via Google Sheet)
   - User fills: Team, Playlist, Approved By
   - System validates against existing playlists only
   - No new playlists are created

3. **Processing** (Automated)
   ```
   Download from Zoom
   ↓
   Upload to YouTube (with captions)
   ↓
   Add to existing playlist
   ↓
   Upload to Drive (video + transcript)
   ↓
   Verify both uploads
   ↓
   Delete from Zoom (only if verified)
   ↓
   Cleanup local files
   ↓
   Mark as COMPLETED
   ```

### Existing YouTube Playlists (DO NOT CREATE NEW)
| Playlist ID | Name | Category |
|-------------|------|----------|
| PLXGtGl2Kq18ak7zQvO16G1nnItDlI7Wno | 2.2.5 Enablers - HR | HR |
| PLXGtGl2Kq18ZQ99TeNVq1-6hxdACNSQ-T | 2.2.4 Tech Systems and Products | Tech |
| PLXGtGl2Kq18YZ1WfSeUlHQQfLod__UyaM | 2.2.1 Marketing | Marketing |
| PLXGtGl2Kq18bb0NrayYkB3ijzRXvoBKip | 2.2.2 Growth | Growth |
| PLXGtGl2Kq18a6rXXhp-O4LT8XQ1ySWB1Q | 2.2.5 Enablers - PM | Project Management |
| PLXGtGl2Kq18aRxwVpnHliHrzViIpGWdm- | 2.2.3 Research Analysis Bureau RAB | Research |
| PLXGtGl2Kq18Y5J9avj1liSNDRPSGA21Yx | 2.2.6 Community Building | Community |
| PLXGtGl2Kq18Z97SIS-64aX7nSNo3NjI_R | 2.2.5 Enablers - OPM & HR | OPM |
| PLXGtGl2Kq18bQ__BBhHz_TD_usIqxzYHJ | Essay Contest | Events |
| PLXGtGl2Kq18YHzkoQ4Bo_QiGczX0qaooU | 2.2.5 Enablers | Enablers |

### Existing Drive Folders (DO NOT CREATE NEW)
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

### File Naming Convention
**Format**: `YYYYMMDD Topic Name`

**Examples**:
- `20260202 Tech Systems Meeting.mp4`
- `20260202 Tech Systems Meeting_transcript.txt`

### Safety Protocols

#### Critical Rules
1. ✅ **NEVER delete from Zoom** until YouTube AND Drive uploads are verified
2. ✅ **NEVER create new playlists** - only use existing ones
3. ✅ **NEVER create new Drive folders** at root - only use existing team folders
4. ✅ **ALWAYS upload transcripts** (YouTube captions + Drive file)
5. ✅ **ALWAYS verify uploads** before deletion

#### Verification Process
Before deleting from Zoom:
- Check YouTube video status is 'uploaded' or 'processed'
- Check Drive file ID exists
- If either fails: Skip deletion and log warning

### Current System Status

**Database**: `data/vong_v2.db`
- Total recordings: 29
- Completed: 3
- Pending: 25
- Processing: 1

**Zoom Accounts**: 2 configured
- Account 1: ms2Lnt5UQKa6nK9x-VH2kw
- Account 2: ms2Lnt5UQKa6nK9x-VH2kw

**Scan Range**: Last 90 days
**Scan Frequency**: Every 60 seconds

### Google Sheet Structure
**Sheet ID**: `1k-SC36HxPRb9SdY9PvaT4qYtZa8Sw5fmWBK30WPKhao`

**Tabs**:
- Main: Recording list with approval workflow
- Settings: System configuration
- System Logs: Activity logs
- Dashboard: Metrics and stats

**Main Tab Columns**:
| Date | Meeting ID | Title | Team | Playlist | Status | Approved By | YouTube URL | Drive URL |
|------|------------|-------|------|----------|--------|-------------|-------------|-----------|

### API Endpoints

**Service Control**:
- `GET /service/status` - Check service status
- `POST /service/stop` - Stop background service
- `POST /service/restart` - Restart background service

**Data**:
- `GET /recordings` - List all recordings
- `GET /recordings/pending` - List pending approvals
- `GET /recordings/history` - List completed recordings
- `POST /recordings/{zoom_id}/approve` - Approve a recording

**Monitoring**:
- `GET /health` - Health check
- `GET /logs?lines=100` - Recent logs
- `GET /stats` - System statistics

### Deployment Configuration

**Backend** (Port 8000):
```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

**Frontend** (Port 9002):
```bash
cd frontend && npm run dev -- -p 9002
```

### Environment Variables (All Set)
```bash
# Zoom Accounts
ZOOM_1_ACCOUNT_ID=ms2Lnt5UQKa6nK9x-VH2kw
ZOOM_1_CLIENT_ID=Esf9CN4IR8GhEz6KxMZehA
ZOOM_1_CLIENT_SECRET=ECCeChIS46pmG7bAMET6X549d6y8rr5i

ZOOM_2_ACCOUNT_ID=ms2Lnt5UQKa6nK9x-VH2kw
ZOOM_2_CLIENT_ID=kdeCDUucRoGNLeLGzUsBNg
ZOOM_2_CLIENT_SECRET=Pd0UgTVUvkdF0z1pXYi4zjRgZ55IyY9o

# Google Services
GOOGLE_SHEET_ID=1k-SC36HxPRb9SdY9PvaT4qYtZa8Sw5fmWBK30WPKhao
GOOGLE_WEB_CLIENT_ID=1079890311690-76c0cmphkalvf0eim3si18o6in8rg1v1.apps.googleusercontent.com
```

### Key Features

#### Self-Healing
- Auto-reconnects to APIs if connection drops
- Retries failed operations with exponential backoff
- Continues running even if one service is temporarily down

#### Comprehensive Logging
- Every action is logged with timestamp
- Errors include full stack traces
- Logs available via API and Google Sheet

#### Data Safety
- Never deletes source until backup is verified
- Maintains local copies until upload confirmation
- Tracks every file through complete lifecycle

### Next Steps for User

1. **Open Google Sheet**: https://docs.google.com/spreadsheets/d/1k-SC36HxPRb9SdY9PvaT4qYtZa8Sw5fmWBK30WPKhao/edit

2. **Review Pending Recordings**: 25 videos waiting for approval

3. **Fill Required Fields**:
   - Team (must match existing category)
   - Playlist (must match existing playlist name)
   - Approved By (your name/email)

4. **System Will Automatically**:
   - Download from Zoom
   - Upload to YouTube with captions
   - Add to specified playlist
   - Upload to Drive (video + transcript)
   - Verify uploads
   - Delete from Zoom
   - Mark as COMPLETED

### Monitoring Commands

**Check total recordings**:
```bash
python scripts/inventory_report.py
```

**Count unique Zoom meetings**:
```bash
$env:PYTHONPATH="."; python scripts/count_unique_zoom.py
```

**View recent logs**:
```bash
curl http://localhost:8000/logs?lines=50
```

**Check service status**:
```bash
curl http://localhost:8000/service/status
```

## System is 100% Ready for Production Deployment
