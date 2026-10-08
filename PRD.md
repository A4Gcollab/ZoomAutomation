# Product Requirements Document (PRD)
# YTZ Automation System

## 1. Overview
**Product Name:** YTZ (YouTube-to-Zoom) Automation System  
**Version:** 1.0  
**Date:** January 11, 2026  
**Author:** VONG Team  
**Status:** In Production

### Purpose
Automate the complete workflow of Zoom cloud recording management by downloading recordings, uploading to YouTube for compression, and backing up to Google Drive with organized folder structures. This eliminates manual processing and ensures all meeting recordings are preserved efficiently.

### Success Metrics
- **Processing Success Rate:** >95% of recordings processed without manual intervention
- **Storage Efficiency:** 40-60% reduction in file size through YouTube re-encoding
- **Time Savings:** Zero manual intervention required for standard recordings
- **Reliability:** 24/7 automated operation with error recovery

## 2. Problem Statement
Organizations using Zoom generate large volumes of cloud recordings that need to be:
- Downloaded before Zoom's automatic deletion (typically 30-90 days)
- Compressed to save storage costs
- Backed up to long-term storage (Google Drive)
- Organized in a searchable folder hierarchy

Manual processing is time-consuming, error-prone, and doesn't scale across multiple Zoom accounts. Missing a recording means permanent data loss.

## 3. Target Users
- **Primary Users:** Organizations/teams managing multiple Zoom accounts with frequent recordings
- **Secondary Users:** IT administrators who need automated backup solutions
- **User Personas:** 
  - Educational institutions recording lectures
  - Businesses archiving client meetings
  - Content creators managing webinar recordings

## 4. Goals & Objectives

### Business Goals
- Eliminate manual recording management overhead
- Reduce storage costs through intelligent compression
- Prevent data loss from missed downloads
- Support multi-account Zoom deployments

### User Goals
- Set-and-forget automation that runs continuously
- Organized, searchable archive of all recordings
- Compressed files that maintain acceptable quality
- Reliable backup to Google Drive

### Non-Goals
- Real-time streaming or live recording
- Video editing or post-processing beyond compression
- Public video hosting (YouTube videos are unlisted)
- Support for platforms other than Zoom/YouTube/Drive

## 5. Features & Requirements

### Must Have (P0)
- [x] Multi-account Zoom support via Server-to-Server OAuth
- [x] Automatic detection of new cloud recordings
- [x] Download video (MP4) and transcript files from Zoom
- [x] Upload to YouTube as unlisted videos
- [x] Re-download compressed version from YouTube
- [x] Upload to Google Drive with year-based folder hierarchy
- [x] State management to prevent duplicate processing
- [x] Error handling and retry logic
- [x] Automatic cleanup of local temporary files
- [x] Configurable check interval (default: 1 hour)

### Should Have (P1)
- [x] Logging with rotation (5MB max, 5 backups)
- [x] Disk space monitoring and cleanup
- [x] Lock mechanism to prevent concurrent runs
- [x] Notification system for errors (webhook support)
- [ ] Dashboard for monitoring processing status
- [ ] Manual retry mechanism for failed recordings

### Nice to Have (P2)
- [ ] Web UI for configuration and monitoring
- [ ] Support for additional cloud storage (OneDrive, Dropbox)
- [ ] Custom video quality/compression settings
- [ ] Automatic deletion of Zoom recordings after successful backup
- [ ] Email notifications in addition to webhooks

## 6. User Stories

1. **As an** IT administrator, **I want to** configure multiple Zoom accounts, **so that** all organizational recordings are automatically backed up
2. **As a** business owner, **I want** recordings compressed before Drive upload, **so that** I minimize storage costs
3. **As a** compliance officer, **I want** all recordings organized by date, **so that** I can quickly find specific meetings
4. **As a** system operator, **I want** error notifications, **so that** I can intervene when automation fails
5. **As a** user, **I want** the system to run continuously, **so that** I never miss a recording

## 7. Technical Architecture

### System Workflow
```
1. Poll Zoom API (every hour) → Detect new recordings
2. Download MP4 + Transcript → Local storage (downloads/)
3. Upload to YouTube → Unlisted video
4. Wait 60s for processing → Download compressed version
5. Upload to Google Drive → Year/Meeting folder structure
6. Cleanup local files → Mark as completed in state DB
```

### Technology Stack
- **Language:** Python 3.x
- **APIs:** 
  - Zoom API (Server-to-Server OAuth)
  - YouTube Data API v3 (OAuth 2.0)
  - Google Drive API v3 (Service Account)
- **Dependencies:** 
  - `requests` - HTTP client
  - `google-auth` - Google authentication
  - `yt-dlp` - YouTube video download
- **Storage:** JSON-based state database
- **Deployment:** Docker container with docker-compose

### Platform
- **Runtime:** Docker container (Linux-based)
- **Host OS:** Windows (with Docker Desktop)
- **Execution:** Background service via VBS script launcher

### Performance Requirements
- **Check Interval:** Configurable (default 3600s/1 hour)
- **Processing Time:** <10 minutes per recording (excluding YouTube processing wait)
- **Disk Space:** Automatic cleanup when <1GB free
- **Concurrency:** Single instance (lock-protected)

### Security
- **Credentials:** Stored in `.env` file and `secrets/` directory
- **API Access:** 
  - Zoom: Server-to-Server OAuth (no user interaction)
  - YouTube: OAuth 2.0 with refresh tokens
  - Drive: Service Account (no user interaction)
- **Video Privacy:** YouTube uploads are unlisted (not public)
- **File Permissions:** Local files cleaned up after processing

## 8. Data Model

### State Database (`data/db.json`)
```json
{
  "recordings": {
    "<zoom_recording_id>": {
      "status": "completed|error|processing",
      "detected_at": "ISO timestamp",
      "completed_at": "ISO timestamp",
      "youtube_id": "video_id",
      "steps": ["detected", "downloaded", "youtube_upload", "drive_upload"],
      "error": "error message if failed",
      "metadata": { "topic": "...", "start_time": "..." }
    }
  }
}
```

### Folder Structure
```
YTZ Automation/
├── src/                    # Source code modules
├── secrets/                # API credentials
│   ├── client_secret.json  # YouTube OAuth
│   ├── token.json          # YouTube refresh token
│   └── service_account.json # Drive service account
├── data/                   # Application data
│   ├── db.json            # State database
│   └── app.log            # Rotating logs
├── downloads/             # Temporary file storage
├── main.py                # Entry point
└── docker-compose.yml     # Container orchestration
```

### Google Drive Hierarchy
```
Root Folder/
└── 2026/
    └── 20260111 Meeting Topic/
        ├── 20260111_Meeting_Topic.mp4
        └── 20260111_Meeting_Topic.vtt
```

## 9. Dependencies & Constraints

### External Dependencies
- **Zoom API:** Rate limits apply (varies by plan)
- **YouTube API:** Daily quota of 10,000 units (1 upload = ~1,600 units)
- **Google Drive API:** 1TB storage limit (varies by account)
- **YouTube Processing:** Variable wait time (typically 1-5 minutes)

### Constraints
- **YouTube Quota:** Maximum ~6 uploads per day with free quota
- **File Size:** Zoom recordings can be 1-5GB; YouTube max is 256GB
- **Processing Delay:** 60-second wait may be insufficient for large files
- **Network:** Requires stable internet for large file transfers
- **Zoom Retention:** Recordings auto-delete after account retention period

### Known Risks
- **YouTube Spam Detection:** Unlisted videos may be flagged/removed
- **API Quota Exhaustion:** YouTube quota limits daily uploads
- **Drive Storage:** May hit quota with high recording volume
- **Network Failures:** Large uploads may timeout or fail

## 10. Current Status & Timeline

### Completed Milestones ✅
- [x] Core automation pipeline (Zoom → YouTube → Drive)
- [x] Multi-account Zoom support
- [x] State management and idempotency
- [x] Error handling and notifications
- [x] Docker containerization
- [x] Logging and monitoring
- [x] Disk space management

### Known Issues 🐛
- **YouTube Video Removal:** Some uploaded videos are being removed by YouTube (spam detection)
- **Drive Quota Errors:** Occasional quota exceeded errors
- **Processing Wait Time:** 60s may be insufficient for large files

### Planned Improvements 📋
| Feature | Priority | Target Date | Status |
|---------|----------|-------------|--------|
| Investigate YouTube removals | P0 | TBD | In Progress |
| Fix Drive quota handling | P0 | TBD | In Progress |
| Dynamic processing wait time | P1 | TBD | Not Started |
| Web dashboard | P2 | TBD | Not Started |

## 11. Configuration

### Environment Variables
```bash
# Zoom Accounts (supports multiple)
ZOOM_1_ACCOUNT_ID=<account_id>
ZOOM_1_CLIENT_ID=<client_id>
ZOOM_1_CLIENT_SECRET=<client_secret>

# Google Drive
DRIVE_ROOT_FOLDER_ID=<folder_id>

# Operational
CHECK_INTERVAL=3600  # seconds
NOTIFICATION_WEBHOOK_URL=<optional>
```

### Deployment
```bash
# Run once (manual)
python main.py --once

# Run continuously (daemon)
python main.py

# Docker deployment
docker-compose up -d
```

## 12. Open Questions

- [ ] **YouTube Removal Issue:** Why are unlisted videos being removed? Is it spam detection or policy violation?
- [ ] **Optimal Processing Wait:** Should we implement adaptive wait times based on file size?
- [ ] **Zoom Deletion:** Should we auto-delete Zoom recordings after successful backup?
- [ ] **Quota Management:** How to handle YouTube quota exhaustion gracefully?
- [ ] **Monitoring:** What metrics should be exposed for operational monitoring?

## 13. Appendix

### Related Documents
- [Conversation History](c7234391-42b2-4cd9-926f-7e7efb351e9c): Initial development and troubleshooting
- Source Code: `d:\VONG\YTZ Automation\`

### API Documentation
- [Zoom Cloud Recording API](https://developers.zoom.us/docs/api/rest/reference/zoom-api/methods/#operation/recordingsList)
- [YouTube Data API v3](https://developers.google.com/youtube/v3/docs)
- [Google Drive API v3](https://developers.google.com/drive/api/v3/reference)
