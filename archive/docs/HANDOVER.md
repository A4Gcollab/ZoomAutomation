# YTZ Automation - Complete Handover Document

**System:** Zoom-to-YouTube Automation (YTZ)
**URL:** https://za.omysha.org
**Server:** 139.84.133.1 (Vultr VPS, Ubuntu 22.04)
**Repository:** https://github.com/A4Gcollab/ZoomAutomation (branch: crazy-almeida)
**Prepared for:** Sneha (Handover walkthrough date/time to be communicated by HR)
**Last updated:** February 2026

---

## Table of Contents

1. [Overall Purpose and Scope](#1-overall-purpose-and-scope)
2. [Complete Technical Setup and Workflow](#2-complete-technical-setup-and-workflow)
3. [Automation Logic, Timelines, Dependencies and Triggers](#3-automation-logic-timelines-dependencies-and-triggers)
4. [Manual Steps and Exception Cases](#4-manual-steps-and-exception-cases)
5. [Known Limitations, Risks and Failure Points](#5-known-limitations-risks-and-failure-points)
6. [Pending Actions, Monitoring and Maintenance](#6-pending-actions-monitoring-and-maintenance)
7. [Handover Walkthrough Checklist (Session with Sneha)](#7-handover-walkthrough-checklist-session-with-sneha)
8. [Quick Reference - Common Commands](#8-quick-reference---common-commands)
9. [Appendix A - Database Schema](#appendix-a---database-schema)
10. [Appendix B - API Endpoints](#appendix-b---api-endpoints)
11. [Appendix C - Playlist/Team Configuration](#appendix-c---playlistteam-configuration)
12. [Appendix D - File Structure](#appendix-d---file-structure)
13. [Appendix E - Environment Variables](#appendix-e---environment-variables)

---

## 1. Overall Purpose and Scope

### What This System Does

YTZ Automation is an end-to-end system that manages Zoom cloud recordings for Omysha. It automates the entire lifecycle:

1. **Scans** Zoom cloud recordings automatically every 60 seconds from 2 Zoom OAuth apps
2. **Lists** new recordings on a web dashboard (https://za.omysha.org) for admin approval
3. After approval, **downloads** the recording from Zoom
4. **Uploads** the video to YouTube (unlisted) with proper title, description, and captions/transcripts
5. **Adds** the video to the correct YouTube playlist based on team/category
6. **Backs up** the video and transcript to Google Drive (secondary backup)
7. **Logs** everything to Google Sheets for audit trail
8. **Auto-deletes** the Zoom cloud recording 24 hours after YouTube upload is verified

### Who Uses It

- **Admin (currently Yogesh, transitioning to Sneha):** Reviews and approves recordings from the dashboard, monitors system health, handles token re-authorization when needed
- **Team members:** Their Zoom meetings are automatically detected - no action needed from them
- **The system itself:** Fully automated after approval - download, upload, backup, log, delete all happen without human intervention

### What It Covers

- ALL Zoom cloud recordings from the Omysha Zoom account (scanned via 2 OAuth apps)
- 10 YouTube playlists mapped to different teams: HR, Tech, Marketing, Growth, PM, Research, Community, OPM, Events, Enablers
- Corresponding Google Drive backup folders per team
- Google Sheets logging for complete audit trail
- Automatic Zoom deletion after verified backup

### Current Status (as of Feb 2026)

- **89 recordings** in PENDING queue (awaiting approval)
- **6 recordings** COMPLETED (uploaded to YouTube, 4 deleted from Zoom)
- **32 unique meetings** tracked
- System is fully operational

---

## 2. Complete Technical Setup and Workflow

### Architecture Overview

```
Internet (HTTPS)
    |
    v
Nginx (port 443, SSL via Let's Encrypt)
    |
    |-- za.omysha.org/        --> Next.js Frontend (port 9002) - Dashboard UI
    |-- za.omysha.org/api/*   --> FastAPI Backend (port 8001)  - REST API
    |-- za.omysha.org/api/ws  --> WebSocket                    - Real-time updates
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Next.js 14 (React, TypeScript) | Dashboard UI for approvals |
| Backend | FastAPI (Python 3.10) | REST API + Background Service |
| Database | SQLite (data/vong_v2.db) | Recording state management |
| Auth | Firebase + Google OAuth | Admin login to dashboard |
| Zoom | Server-to-Server OAuth (2 apps) | Scan and download recordings |
| YouTube | OAuth2 (Desktop App flow) | Upload videos, manage playlists |
| Drive | OAuth2 (User mode) | Backup videos and transcripts |
| Sheets | Service Account | Logging and audit trail |
| Web Server | Nginx + Let's Encrypt SSL | HTTPS reverse proxy |
| Process Manager | systemd | Service lifecycle management |

### Server Details

- **IP:** 139.84.133.1
- **OS:** Ubuntu 22.04
- **SSH:** `ssh root@139.84.133.1`
- **Domain:** za.omysha.org (DNS managed externally, SSL auto-renewed by Certbot)
- **Project path:** /root/ytz-automation
- **Python venv:** /root/ytz-automation/venv

### systemd Services

Two services run the system:

**ytz-api** - Python backend (FastAPI + Background Service):
```
Service file: /etc/systemd/system/ytz-api.service
Working directory: /root/ytz-automation
Command: venv/bin/python -m uvicorn src.api:app --host 127.0.0.1 --port 8001
```

**ytz-frontend** - Next.js dashboard:
```
Service file: /etc/systemd/system/ytz-frontend.service
Working directory: /root/ytz-automation/frontend
Command: npm run start (port 9002)
```

### Nginx Configuration

File: /etc/nginx/sites-enabled/ytz
- `/` proxies to Next.js on port 9002
- `/api/*` proxies to FastAPI on port 8001 (strips /api/ prefix)
- `/api/ws` proxies WebSocket connections
- client_max_body_size set to 5G for large uploads
- SSL managed by Certbot (auto-renews)

### End-to-End Workflow

```
Step 1: SCAN (automatic, every 60 seconds)
   Zoom Cloud --> Background Service --> SQLite DB (status: PENDING)
                                     --> Google Sheets (new row)
                                     --> Dashboard shows new recording

Step 2: APPROVE (manual)
   Admin opens dashboard --> Selects Team & Playlist --> Clicks Approve
   DB status changes: PENDING --> APPROVED

Step 3: PROCESS (automatic, picks up APPROVED recordings)
   Download from Zoom --> Upload to YouTube (unlisted)
                      --> Add to YouTube Playlist
                      --> Upload captions/transcript
                      --> Backup to Google Drive
                      --> Update Google Sheets
   DB status changes: APPROVED --> PROCESSING --> COMPLETED

Step 4: DELETE (automatic, 24 hours after YouTube verified)
   Verify YouTube video exists --> Delete from Zoom cloud
   DB: zoom_deletion_status changes to DELETED
```

---

## 3. Automation Logic, Timelines, Dependencies and Triggers

### The Background Service Loop (src/main.py)

The background service runs as a daemon thread inside the FastAPI process. It executes a continuous loop with 3 phases, sleeping 60 seconds between cycles.

#### Phase 1: SCAN (runs every cycle)

**Trigger:** Automatic, every 60 seconds
**What it does:**
- Connects to both Zoom OAuth apps
- Lists all users in the Zoom account
- For each user, fetches cloud recordings from the last 90 days
- For each recording not already in the database:
  - Adds it to SQLite as PENDING
  - Logs it to Google Sheets
  - If the meeting_id matches an entry in playlists.json, auto-assigns team/playlist
- New recordings appear on the dashboard within ~1 minute

#### Phase 2: PROCESS (runs every cycle)

**Trigger:** User approves a recording via the dashboard
**What it does for each APPROVED recording:**
1. Marks status as PROCESSING in DB
2. Downloads MP4 video from Zoom (to /root/ytz-automation/downloads/)
3. Downloads transcript/captions if available
4. Uploads video to YouTube as unlisted with title format: "YYYYMMDD Meeting Topic"
5. Uploads transcript as YouTube captions
6. Resolves playlist name to YouTube playlist ID (from playlists.json) and adds video
7. Uploads video to Google Drive team folder (backup)
8. Uploads transcript to Google Drive transcript folder
9. Verifies YouTube upload succeeded
10. If YouTube verified: schedules Zoom deletion for NOW + 24 hours
11. Updates Google Sheets with YouTube URL, Drive URL, status
12. Cleans up local downloaded files
13. Marks status as COMPLETED

**Timeline:** Processing takes 2-15 minutes per recording depending on file size.
**If Zoom recording not found (team already deleted manually):** Marks as COMPLETED with note "manually handled" - does NOT error out.

#### Phase 3: CLEANUP (runs every cycle)

**Trigger:** Automatic - checks if any recordings have passed their 24-hour deletion window
**What it does:**
1. Queries DB for COMPLETED recordings where deletion_ready_at <= now
2. Also retries previously FAILED and VERIFICATION_FAILED deletions
3. For each ready recording:
   - Re-verifies YouTube video still exists and is accessible
   - If YouTube client is down but URL exists: trusts the URL (proceeds with deletion)
   - If verified: deletes recording from Zoom (moves to trash)
   - If not verified: marks as VERIFICATION_FAILED (will retry next cycle)

**Timeline:** Deletion happens 24 hours after YouTube upload is verified.

#### Auto-Recovery (every 10 cycles = ~10 minutes)

**Trigger:** Automatic
- Records stuck in PROCESSING for >60 minutes: reset to APPROVED (re-processed)
- Records in ERROR with retry_count < 3: reset to APPROVED (retried)

### Dependency Chain

```
Zoom Cloud Recordings
       |
       v (scan)
   SQLite DB [PENDING] <-- Dashboard reads this
       |
       v (user approves)
   SQLite DB [APPROVED]
       |
       v (background service)
   +-----------+-----------+-----------+
   |           |           |           |
   v           v           v           v
 YouTube    Drive       Sheets    Zoom Delete
 (primary)  (backup)    (log)    (after 24h)
```

**Critical dependency:** YouTube is the PRIMARY backup. Zoom deletion only happens after YouTube upload is verified. Drive is secondary - if Drive fails, the recording still processes successfully.

### Trigger Summary

| Action | Trigger | Automatic? | Timing |
|--------|---------|-----------|--------|
| Scan Zoom for new recordings | Every 60-second cycle | Yes | Continuous |
| Show on dashboard | New recording detected | Yes | Within ~1 minute |
| Auto-assign team/playlist | meeting_id in playlists.json | Yes | During scan |
| Approve recording | Admin clicks Approve button | **Manual** | On demand |
| Download from Zoom | Recording approved | Yes | Next cycle (~60s) |
| Upload to YouTube | After download | Yes | 2-15 minutes |
| Add to YouTube playlist | After upload | Yes | Immediate |
| Backup to Google Drive | After YouTube upload | Yes | 1-5 minutes |
| Log to Google Sheets | At each step | Yes | Real-time |
| Schedule Zoom deletion | After YouTube verified | Yes | Sets timer for +24h |
| Delete from Zoom | 24h after YouTube verified | Yes | Automatic |
| Auto-recover stuck records | Every 10 minutes | Yes | Resets to APPROVED |

---

## 4. Manual Steps and Exception Cases

### Regular Manual Steps

#### 1. Approving Recordings (daily task)

This is the primary manual task. Everything else is automated.

1. Go to https://za.omysha.org
2. Login with your Google account (must be in ADMIN_EMAILS)
3. In the Pending Queue tab, for each recording:
   - Select the appropriate **Team** from the dropdown
   - Select the appropriate **Playlist** from the dropdown
   - Click **Approve**
4. The system handles everything else - upload, backup, logging, deletion

**Tip:** Recordings from known recurring meetings (configured in playlists.json) will have their team/playlist pre-suggested based on meeting ID matching.

#### 2. Re-authorizing YouTube Token (when it expires)

YouTube OAuth tokens expire periodically (approximately every 7 days, or when revoked). When this happens, the system logs `Token refresh failed: invalid_grant`.

**How to fix:**
```bash
ssh root@139.84.133.1
cd /root/ytz-automation
source venv/bin/activate

# Generate auth URL
python3 -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file('secrets/client_secret.json', [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
])
flow.redirect_uri = 'http://localhost:1'
url, _ = flow.authorization_url(prompt='consent', access_type='offline')
print('Open this URL:', url)
"

# 1. Copy the printed URL and open in your browser
# 2. Sign in with the YouTube Google account
# 3. It will redirect to localhost and show an error - that's OK
# 4. Copy the FULL URL from the browser address bar
# 5. Extract the code parameter and run:

python3 -c "
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file('secrets/client_secret.json', [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
])
flow.redirect_uri = 'http://localhost:1'
flow.fetch_token(code='PASTE_THE_CODE_HERE')
with open('secrets/token.json', 'wb') as f:
    pickle.dump(flow.credentials, f)
print('Token saved!')
"

# Restart the service
systemctl restart ytz-api
```

#### 3. Re-authorizing Drive Token (same process)

Same as YouTube but with Drive scopes:
```bash
# Same flow but with these scopes:
# 'https://www.googleapis.com/auth/drive'
# 'https://www.googleapis.com/auth/spreadsheets'
# Save to: secrets/token_drive.json
```

#### 4. Adding a New Team/Playlist

Edit /root/ytz-automation/config/playlists.json and add a new entry:
```json
{
    "playlist_id": "PLXxxxxxxx",
    "playlist_name": "Display Name",
    "category": "Team Category",
    "drive_folder_id": "Google Drive folder ID",
    "transcript_folder_id": "Transcript folder ID",
    "meeting_ids": ["zoom_meeting_id_1", "zoom_meeting_id_2"],
    "keywords": []
}
```
Then restart: `systemctl restart ytz-api`

#### 5. Adding New Admin Users

Edit .env on the server:
```
ADMIN_EMAILS=yogesh@omysha.org,sneha@omysha.org
```
Then restart: `systemctl restart ytz-api`

### Exception Cases

| Scenario | What Happens | Action Needed |
|----------|-------------|---------------|
| Team manually deletes recording from Zoom | When system tries to process, it detects Zoom 404 and marks as COMPLETED with "manually handled" note | None - handled gracefully |
| Team manually uploads to YouTube | Recording stays in PENDING queue on dashboard | Approve it normally - if Zoom file is gone, auto-marks as manual |
| YouTube daily quota exceeded (10,000 units) | System auto-pauses YouTube uploads for 24 hours | None - auto-resumes next day |
| Recording stuck in PROCESSING > 1 hour | Auto-recovery resets to APPROVED for retry | None - automatic. Or restart service manually |
| YouTube token expires | Uploads stop, recordings queue up as APPROVED | Re-authorize token (see step 2 above) |
| Drive upload fails | YouTube upload still succeeds, Drive is secondary | Non-blocking - recording still marked COMPLETED |
| Duplicate recordings detected | Dedup by meeting_id + date prevents new duplicates | For existing dupes, can delete from DB manually |
| Server disk full | Downloads fail | Clear /root/ytz-automation/downloads/ folder |
| Zoom API rate limited | Scanning slows down temporarily | Built-in retry with backoff - auto-recovers |
| Playlist name not found in config | Video uploads to YouTube but not added to playlist | Add the playlist to playlists.json |

---

## 5. Known Limitations, Risks and Failure Points

### Limitations

1. **YouTube daily quota:** 10,000 API units/day. Each video upload costs ~1,600 units. Maximum ~6 uploads per day before the system auto-pauses for 24 hours.

2. **OAuth tokens expire:** YouTube and Drive OAuth tokens need manual re-authorization periodically (every ~7 days, or immediately if revoked from Google account settings). Google Sheets uses a service account which never expires.

3. **Single server, no redundancy:** The system runs on one VPS. If the server goes down, automation stops until restarted. Recordings queue up on Zoom and will be picked up when service resumes.

4. **Zoom scan window:** Only scans the last 90 days of recordings. Recordings older than 90 days will not be detected.

5. **Large files:** Very large recordings (>6GB) may timeout during download or upload. The retry mechanism will attempt up to 3 times.

6. **One approval workflow:** Each recording must be individually approved. There is no bulk approve or auto-approve feature.

7. **Service account Drive limitation:** The Google service account cannot upload files to personal Google Drive (no storage quota). Drive upload uses user OAuth which requires periodic re-authorization.

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| YouTube token expires unnoticed | Medium | Uploads stop, recordings queue up | Check logs daily for `invalid_grant` errors |
| Server disk fills up | Low | Downloads fail | Auto-cleanup of temp files, monitor with `df -h` |
| Database corruption | Very Low | All state lost | Regular backups: `cp data/vong_v2.db data/backup.db` |
| SSL certificate expires | Very Low | Site unreachable | Let's Encrypt auto-renews, verify with `certbot certificates` |
| Zoom app scopes changed | Low | Scanning or deletion stops | Verify scopes in Zoom Marketplace if issues arise |
| Google API changes | Very Low | Integration breaks | Monitor Google Cloud Console for deprecation notices |

### Critical Failure Points (in order of likelihood)

1. **secrets/token.json** (YouTube OAuth) - Most common failure. Token expires or gets revoked. Signs: logs show `invalid_grant`. Fix: re-authorize (see Section 4).

2. **secrets/token_drive.json** (Drive OAuth) - Same issue as YouTube. Drive uploads fail but system continues (YouTube is primary).

3. **Disk space** (/root/ytz-automation/downloads/) - Large videos can fill disk. Service auto-cleans after upload but monitor.

4. **Port conflicts** - If old process doesn't release port 8001 on restart. Fix: `fuser -k 8001/tcp` then restart.

5. **Database lock** - SQLite can lock under heavy concurrent access. Service uses threading lock to prevent this. If stuck: restart service.

6. **Nginx** - If nginx crashes, entire site goes down. Check: `systemctl status nginx`. Fix: `systemctl restart nginx`.

---

## 6. Pending Actions, Monitoring and Maintenance

### Immediate Pending Actions

- [ ] **Drive token re-authorization** - Drive OAuth token is currently expired. Needs re-auth using the process described in Section 4.
- [ ] **Add Sneha to ADMIN_EMAILS** - Update .env with Sneha's email so she can login to the dashboard.
- [ ] **Review 89 PENDING recordings** - Approve or dismiss recordings from the dashboard as needed.
- [ ] **Verify end-to-end pipeline** - Approve one recording and watch it through the full cycle: approve, YouTube upload, and 24h later Zoom deletion.

### Daily Monitoring Checklist

1. **Check the dashboard** (https://za.omysha.org)
   - Are new recordings appearing in the Pending Queue?
   - Are approved recordings moving to Completed?
   - Any errors showing in the Error Logs tab?

2. **Check service health** (if needed):
   ```bash
   ssh root@139.84.133.1
   systemctl status ytz-api        # Should show "active (running)"
   systemctl status ytz-frontend   # Should show "active (running)"
   ```

3. **Check for critical errors:**
   ```bash
   journalctl -u ytz-api --since "24 hours ago" | grep ERROR | grep -v "file_cache"
   ```
   Watch for:
   - `Token refresh failed: invalid_grant` --> Re-authorize YouTube/Drive token
   - `YouTube quota exceeded` --> Wait 24 hours, auto-resumes
   - `Disk space` warnings --> Clear downloads/ folder
   - `Zoom client not found` --> Check .env Zoom credentials

### Weekly Maintenance

1. **Verify tokens are valid:** Check that uploads are succeeding (look at recent Completed entries on dashboard)
2. **Check disk space:** `ssh root@139.84.133.1 "df -h /root"`
3. **Check database size:** `ssh root@139.84.133.1 "ls -lh /root/ytz-automation/data/vong_v2.db"`
4. **Review Google Sheets:** Ensure logging is up to date at https://docs.google.com/spreadsheets/d/17XhkOS7YW0AC7fOC51tXRoLbIOX2MkY2YxN1nJFVlwE

### Monthly Maintenance

1. **SSL certificate:** Verify auto-renewal: `ssh root@139.84.133.1 "certbot certificates"`
2. **Database backup:** `ssh root@139.84.133.1 "cp /root/ytz-automation/data/vong_v2.db /root/ytz-automation/data/backup_$(date +%Y%m%d).db"`
3. **Review playlists.json:** Add meeting IDs for any new recurring meetings that should be auto-matched
4. **Check server updates:** `apt update && apt list --upgradable` (apply with caution)

---

## 7. Handover Walkthrough Checklist (Session with Sneha)

*Handover walkthrough session date and time to be communicated by HR.*

### Pre-Session Preparation

- [ ] Sneha's email added to ADMIN_EMAILS in .env
- [ ] Sneha can login to https://za.omysha.org with her Google account
- [ ] Sneha has SSH access to 139.84.133.1 (or will be set up during session)
- [ ] At least 1-2 PENDING recordings available for live demo
- [ ] This handover document shared with Sneha before the session

### During the Session

#### Part 1: Dashboard Tour (15 minutes)
- [ ] Login flow - Google OAuth, landing on dashboard
- [ ] Pending Queue tab - how recordings appear, selecting team/playlist
- [ ] Approve a recording together (live demo)
- [ ] Completed History tab - see processed recordings with YouTube/Drive links
- [ ] Error Logs tab - how to identify issues
- [ ] Settings page - integration links

#### Part 2: Watch the Automation Work (10 minutes)
- [ ] After approving, watch the backend logs live:
      `journalctl -u ytz-api -f`
- [ ] See download, YouTube upload, Drive backup happen in real-time
- [ ] Show the recording appear in Completed with YouTube URL
- [ ] Explain the 24-hour Zoom deletion timer

#### Part 3: Server Access and Operations (15 minutes)
- [ ] SSH into the server together
- [ ] Show how to check service status: `systemctl status ytz-api`
- [ ] Show how to restart services: `systemctl restart ytz-api`
- [ ] Show how to view and filter logs: `journalctl -u ytz-api --since "1 hour ago"`
- [ ] Show the project directory structure: /root/ytz-automation/
- [ ] Show .env file (explain key variables)
- [ ] Show playlists.json (how teams/playlists are configured)

#### Part 4: Troubleshooting (15 minutes)
- [ ] Show what `invalid_grant` error looks like in logs
- [ ] Walk through YouTube token re-authorization process step by step
- [ ] Show how to check disk space
- [ ] Show the Google Sheets log
- [ ] Explain what to do if recordings are stuck (auto-recovery vs manual restart)

#### Part 5: Q&A and Practice (15 minutes)
- [ ] Sneha approves a recording independently
- [ ] Sneha checks service status independently
- [ ] Sneha reads logs and identifies key information
- [ ] Answer any remaining questions

### Post-Session Verification

- [ ] Sneha can login to dashboard independently
- [ ] Sneha can approve recordings independently
- [ ] Sneha can SSH and check service status
- [ ] Sneha can read and understand service logs
- [ ] Sneha knows how to re-authorize YouTube/Drive tokens
- [ ] Sneha has this document saved and knows where to find it
- [ ] Sneha knows who to contact for server/infrastructure issues

### Ensuring Independent Operation

After the handover, Sneha should be able to:

1. **Daily:** Login to dashboard, review and approve recordings
2. **When alerts appear:** Check logs, identify if it's a token expiry, and re-authorize
3. **When things break:** Restart services, check logs, escalate if needed
4. **Monthly:** Run maintenance checks (disk, backups, SSL)

---

## 8. Quick Reference - Common Commands

```bash
# === SSH into server ===
ssh root@139.84.133.1

# === Service Management ===
systemctl status ytz-api           # Check backend status
systemctl status ytz-frontend      # Check frontend status
systemctl restart ytz-api          # Restart backend (most common fix)
systemctl restart ytz-frontend     # Restart frontend
systemctl restart nginx            # Restart web server

# === View Logs ===
journalctl -u ytz-api -f                                    # Live backend logs
journalctl -u ytz-api --since "1 hour ago" | grep ERROR     # Recent errors
journalctl -u ytz-api --since "24 hours ago" | grep "COMPLETED"  # Recent completions
journalctl -u ytz-frontend -f                                # Live frontend logs

# === Database Quick Checks ===
cd /root/ytz-automation && source venv/bin/activate

# Count by status
python3 -c "from src.db_sql import db; print(db.get_stats())"

# List pending recordings
python3 -c "
from src.db_sql import db
for r in db.get_pending():
    print(r['topic'], '|', r['start_time'][:10])
"

# Check deletion status
python3 -c "
from src.db_sql import db
cur = db.conn.cursor()
cur.execute('SELECT topic, zoom_deletion_status, zoom_deleted_at FROM recordings WHERE status=\"COMPLETED\"')
for r in cur.fetchall():
    print(r[0], '| del:', r[1], '| at:', r[2])
"

# === Disk Space ===
df -h /root

# === Kill stuck port ===
fuser -k 8001/tcp              # If port 8001 is stuck after restart

# === Rebuild Frontend (after code changes) ===
cd /root/ytz-automation/frontend && npm run build
systemctl restart ytz-frontend

# === Database Backup ===
cp /root/ytz-automation/data/vong_v2.db /root/ytz-automation/data/backup_$(date +%Y%m%d).db

# === SSL Certificate Check ===
certbot certificates
```

---

## Appendix A - Database Schema

**SQLite file:** data/vong_v2.db

### recordings table

| Column | Type | Description |
|--------|------|-------------|
| zoom_id | TEXT (PK) | Zoom UUID - unique per recording instance |
| meeting_id | TEXT | Numeric Zoom meeting ID (recurring meetings share this) |
| account_name | TEXT | "Zoom Account 1" or "Zoom Account 2" |
| topic | TEXT | Meeting title from Zoom |
| start_time | TEXT | ISO timestamp of when meeting started |
| date_str | TEXT | Date only (YYYY-MM-DD) for dedup |
| status | TEXT | PENDING / APPROVED / PROCESSING / COMPLETED / ERROR |
| team | TEXT | Department name (set during approval) |
| playlist | TEXT | YouTube playlist name (set during approval) |
| approved_by | TEXT | Email of who approved |
| video_url | TEXT | Zoom download URL |
| transcript_url | TEXT | Zoom transcript URL |
| youtube_url | TEXT | YouTube URL after upload (e.g. https://youtu.be/xxxxx) |
| drive_url | TEXT | Drive URL after backup |
| metadata | JSON | Full Zoom API response for the recording |
| created_at | TIMESTAMP | When record was created in DB |
| error_message | TEXT | Error details if status=ERROR |
| retry_count | INTEGER | Number of processing retries (max 3) |
| processed_at | TEXT | When processing started |
| deletion_ready_at | TEXT | When Zoom deletion is allowed (24h after YouTube verified) |
| zoom_deletion_status | TEXT | NULL / PENDING / DELETED / FAILED / VERIFICATION_FAILED |
| zoom_deleted_at | TEXT | When actually deleted from Zoom |
| zoom_deletion_error | TEXT | Error details if deletion failed |

### system_logs table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment |
| level | TEXT | INFO / ERROR / WARNING |
| message | TEXT | Log message |
| timestamp | TIMESTAMP | When logged |

---

## Appendix B - API Endpoints

**Base URL:** https://za.omysha.org/api

### Public Endpoints (no auth required)

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Basic health check |
| GET | /health/detailed | Full diagnostics (DB, service, disk, memory) |
| GET | /metrics | Prometheus-format metrics |
| GET | /service/status | Background service status |
| WS | /ws | WebSocket for real-time dashboard updates |

### Authenticated Endpoints (requires X-Token header from Google login)

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/login | Verify Google token, returns session token |
| GET | /queue | Get all PENDING recordings |
| GET | /history?limit=50 | Get completed/error recordings |
| GET | /stats | Summary counts |
| GET | /options | Available teams and playlists for dropdowns |
| POST | /approve/{zoom_id} | Approve a recording (body: {team, playlist}) |
| GET | /logs?lines=100&level=INFO | System logs with filtering |
| GET | /errors?lines=50 | Error-level logs only |
| POST | /service/start | Start background service |
| POST | /service/stop | Stop background service |
| POST | /service/restart | Restart background service |
| GET | /sheets-url | Get Google Sheets URL |

---

## Appendix C - Playlist/Team Configuration

**File:** /root/ytz-automation/config/playlists.json

### Current Mapping

| Playlist Name | Team | YouTube Playlist ID | Auto-Matched Meeting IDs |
|--------------|------|---------------------|------------------------|
| 2.2.5 Enablers - HR | HR | PLXGtGl2Kq18ak7zQvO16G1nnItDlI7Wno | 81198809795 |
| 2.2.4 Tech Systems and Products | Tech | PLXGtGl2Kq18ZQ99TeNVq1-6hxdACNSQ-T | 82486284329, 81992981065 |
| 2.2.1 Marketing | Marketing | PLXGtGl2Kq18YZ1WfSeUlHQQfLod__UyaM | 88986938073 |
| 2.2.2 Growth | Growth | PLXGtGl2Kq18bb0NrayYkB3ijzRXvoBKip | 88355536074, 86115620154, 81854001799 |
| 2.2.5 Enablers - PM | Project Management | PLXGtGl2Kq18a6rXXhp-O4LT8XQ1ySWB1Q | 85224726018, 82962537185, 85788605730, 84197418688 |
| 2.2.3 Research Analysis Bureau RAB | Research | PLXGtGl2Kq18aRxwVpnHliHrzViIpGWdm- | (none) |
| 2.2.6 Community Building | Community | PLXGtGl2Kq18Y5J9avj1liSNDRPSGA21Yx | 85189689047 |
| 2.2.5 Enablers - OPM & HR | OPM | PLXGtGl2Kq18Z97SIS-64aX7nSNo3NjI_R | 81059261130 |
| Essay Contest | Events | PLXGtGl2Kq18bQ__BBhHz_TD_usIqxzYHJ | (none) |
| 2.2.5 Enablers | Enablers | PLXGtGl2Kq18YHzkoQ4Bo_QiGczX0qaooU | 9824392507, 7020693264 |

### How Auto-Matching Works

When a new Zoom recording is scanned, if its numeric meeting_id appears in any playlist's meeting_ids array, the system automatically pre-assigns the team and playlist. Recordings from unknown/new meetings appear without a pre-selection and require manual team/playlist choice during approval.

### Adding a New Playlist

1. Create the playlist on YouTube and note the playlist ID (starts with PL...)
2. Create the video and transcript folders on Google Drive and note folder IDs
3. Add entry to playlists.json with the meeting IDs that should auto-match
4. Restart: `systemctl restart ytz-api`

---

## Appendix D - File Structure

```
/root/ytz-automation/
|
|-- src/                          # Python backend source code
|   |-- main.py                   # Background service (3-phase loop: scan/process/cleanup)
|   |-- api.py                    # FastAPI REST endpoints
|   |-- db_sql.py                 # SQLite database operations
|   |-- config.py                 # Configuration loader (.env)
|   |-- auth.py                   # Google OAuth token verification
|   |-- zoom_client.py            # Zoom API client (scan, download, delete)
|   |-- youtube_client.py         # YouTube API client (upload, playlists, captions)
|   |-- drive_client.py           # Google Drive client (upload, folders)
|   |-- sheets_integration.py     # Google Sheets logging
|   |-- utils.py                  # Helpers (filename generation, retry decorator)
|   |-- cache.py                  # In-memory TTL cache for API responses
|   |-- websocket_manager.py      # WebSocket connection manager
|   |-- monitor.py                # Disk space and cleanup monitoring
|   +-- lock.py                   # Single-instance file lock
|
|-- frontend/                     # Next.js frontend
|   |-- src/app/                  # Pages (dashboard, login, settings, youtube, drive)
|   |-- src/components/           # React UI components
|   |-- src/lib/api.ts            # Frontend API client with retry logic
|   +-- .env.local                # Frontend environment (API URL, WS URL)
|
|-- config/
|   +-- playlists.json            # Team/Playlist/Drive folder mapping
|
|-- data/                         # Runtime data (NOT in git)
|   |-- vong_v2.db                # SQLite database
|   +-- app.log                   # Application log file
|
|-- secrets/                      # Auth tokens (NEVER commit)
|   |-- client_secret.json        # Google OAuth client credentials
|   |-- service_account.json      # Google service account (for Sheets)
|   |-- token.json                # YouTube OAuth token (pickle format)
|   +-- token_drive.json          # Drive OAuth token (pickle format)
|
|-- downloads/                    # Temporary video downloads (auto-cleaned)
|-- scripts/                      # Setup and utility scripts
|-- .env                          # All environment variables
|-- requirements.txt              # Python dependencies
+-- venv/                         # Python virtual environment
```

---

## Appendix E - Environment Variables

**File:** /root/ytz-automation/.env

| Variable | Purpose | Current Value |
|----------|---------|--------------|
| ZOOM_1_ACCOUNT_ID | Zoom OAuth App 1 account | ms2Lnt5UQKa6nK9x-VH2kw |
| ZOOM_1_CLIENT_ID | Zoom App 1 client ID | Esf9CN4IR8GhEz6KxMZehA |
| ZOOM_1_CLIENT_SECRET | Zoom App 1 secret | (set in .env) |
| ZOOM_2_ACCOUNT_ID | Zoom OAuth App 2 account | ms2Lnt5UQKa6nK9x-VH2kw |
| ZOOM_2_CLIENT_ID | Zoom App 2 client ID | kdeCDUucRoGNLeLGzUsBNg |
| ZOOM_2_CLIENT_SECRET | Zoom App 2 secret | (set in .env) |
| GOOGLE_WEB_CLIENT_ID | Firebase auth client ID | 1079890311690-...apps.googleusercontent.com |
| GOOGLE_SHEET_ID | Google Sheets spreadsheet ID | 17XhkOS7YW0AC7fOC51tXRoLbIOX2MkY2YxN1nJFVlwE |
| DRIVE_ROOT_FOLDER_ID | Google Drive root folder | 1gHxPqE0vwVJdLZQX0YK5xZ8yN9mW7fR6 |
| DRIVE_AUTH_MODE | Drive auth method | user |
| ENABLE_DRIVE_UPLOAD | Enable Drive backup | true |
| ENABLE_SHEETS_INTEGRATION | Enable Sheets logging | true |
| ADMIN_EMAILS | Allowed admin emails | yogesh@omysha.org |
| API_PORT | Backend API port | 8000 |
| YOUTUBE_PRIVACY_STATUS | YouTube video privacy | unlisted |
| DELETE_DELAY_HOURS | Hours to wait before Zoom deletion | 24 |
| ENABLE_AUTO_DELETE | Enable automatic Zoom deletion | false |
| MAX_YOUTUBE_PROCESSING_WAIT | Max wait for YT processing (seconds) | 300 |
| ENVIRONMENT | Environment mode | development |

### Secret Files (on server at /root/ytz-automation/secrets/)

| File | Format | Purpose | Expires? |
|------|--------|---------|----------|
| client_secret.json | JSON | Google OAuth client credentials | No |
| service_account.json | JSON | Google service account for Sheets | No |
| token.json | Python pickle | YouTube OAuth access/refresh token | Yes (~7 days) |
| token_drive.json | Python pickle | Drive OAuth access/refresh token | Yes (~7 days) |

### Key External Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Dashboard | https://za.omysha.org | Main interface |
| Google Sheet | https://docs.google.com/spreadsheets/d/17XhkOS7YW0AC7fOC51tXRoLbIOX2MkY2YxN1nJFVlwE | Audit log |
| Zoom Marketplace | https://marketplace.zoom.us | Manage OAuth apps and scopes |
| Google Cloud Console | https://console.cloud.google.com | Manage API keys and OAuth |
| Firebase Console | https://console.firebase.google.com | Manage authentication |
| GitHub Repository | https://github.com/A4Gcollab/ZoomAutomation | Source code |

---

## If Everything Breaks - Emergency Recovery

1. SSH into server: `ssh root@139.84.133.1`
2. Restart all services:
   ```bash
   fuser -k 8001/tcp 2>/dev/null
   systemctl restart ytz-api
   systemctl restart ytz-frontend
   systemctl restart nginx
   ```
3. Check what went wrong: `journalctl -u ytz-api --since "10 minutes ago" | grep ERROR`
4. If token expired: follow re-authorization steps in Section 4
5. If database corrupted: restore from backup in data/ folder
6. If disk full: `rm -rf /root/ytz-automation/downloads/*`
7. If nothing works: the system is stateless enough that recordings will queue up on Zoom and can be re-processed once the service is back up

---

*This document is designed to ensure Sneha can understand, operate, and manage the YTZ automation system independently after the handover. The system is mostly hands-off - the primary regular tasks are approving recordings from the dashboard and occasionally re-authorizing OAuth tokens when they expire.*
