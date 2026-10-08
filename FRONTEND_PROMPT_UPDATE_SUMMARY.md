# ✅ UPDATED: Frontend Prompt with Complete Workflow

## 🎯 What I Added

I've updated `GOOGLE_IDX_FRONTEND_PROMPT.md` with **COMPLETE** details about:

### 1. ✅ Approval Workflow (Step-by-Step)
**Added comprehensive 12-step workflow:**
1. User selects Team dropdown (Marketing, Engineering, Sales, etc.)
2. User selects Playlist dropdown (Weekly Standups, Client Meetings, etc.)
3. User clicks Approve button
4. Modal confirms: "Approve for [Team] / [Playlist]?"
5. Frontend sends POST /approve/{zoom_id}
6. Backend marks as APPROVED
7. Backend broadcasts WebSocket event
8. Frontend updates UI immediately
9. Status changes to PROCESSING
10. Background service processes (Zoom → YouTube → Drive)
11. Frontend receives completion event
12. Recording appears in HISTORY with links

### 2. ✅ Team & Playlist Management
**Explained how dropdowns work:**
- Teams = organizational units (Marketing, Engineering, etc.)
- Playlists = YouTube playlists for organization
- Both REQUIRED before approval
- Populated from GET /options endpoint
- User can type NEW values (autocomplete + "Add new: [value]")
- New values automatically saved when used
- Validation: Cannot approve without both selected

### 3. ✅ YouTube Integration Details
**Complete YouTube workflow:**
- Videos uploaded as UNLISTED
- Title format: "YYYYMMDD Topic Name" (e.g., "20260202 Weekly Marketing Standup")
- Description includes: Topic, date, team, playlist
- Auto-added to selected YouTube playlist
- Captions/transcript uploaded if available
- URL format: https://youtu.be/VIDEO_ID

### 4. ✅ Google Drive Integration Details
**Complete Drive folder structure:**
```
Root Folder/
├── Marketing/
│   ├── 20260202 Weekly Standup/
│   │   ├── 20260202_Weekly_Standup.mp4
│   │   └── 20260202_Weekly_Standup.vtt
│   └── 20260201 Client Review/
│       └── 20260201_Client_Review.mp4
└── Engineering/
    └── 20260202 Sprint Planning/
        ├── 20260202_Sprint_Planning.mp4
        └── 20260202_Sprint_Planning.vtt
```

### 5. ✅ Status Flow Diagram
```
PENDING → (user approves) → APPROVED → (background picks up) → 
PROCESSING → (upload complete) → COMPLETED

If error: → ERROR (with message)
```

### 6. ✅ UI Feedback Details
**Complete UX specifications:**
- Loading spinner on Approve button
- Success toast: "Recording approved! Processing will begin shortly."
- Error toast with specific error message
- Optimistic UI updates
- WebSocket confirmation/revert logic
- Animated processing indicator
- Green checkmark for COMPLETED
- Red X for ERROR with expandable details

### 7. ✅ Enhanced History Tab
**Added filters and features:**
- Filter by status (All, Completed, Processing, Error)
- Filter by team (dropdown)
- Filter by playlist (dropdown)
- Real-time search by topic
- Sort by date (newest first)
- Expandable row details showing:
  * Full topic, dates, duration, file size
  * Error message if failed
- Export to CSV button
- Manual refresh button

### 8. ✅ Detailed API Schemas
**Complete request/response examples:**
- GET /queue - Shows PENDING recordings with null team/playlist
- GET /history - Shows completed with youtube_url, drive_url, approved_by
- GET /options - Returns teams and playlists arrays
- POST /approve - Requires team and playlist, returns immediately
- Notes on caching, async behavior, WebSocket events

### 9. ✅ WebSocket Event Specifications
**7 detailed event types with payloads:**

1. **recording_approved** - When user approves
2. **recording_completed** - When processing finishes
3. **recording_processing** - Progress updates during processing
4. **recording_error** - When processing fails
5. **service_status_changed** - When service starts/stops
6. **new_log_entry** - Real-time log streaming
7. **stats_updated** - Stats changes

**Each event includes:**
- Complete JSON payload structure
- Frontend action to take
- UI updates to make
- Toast notifications to show

### 10. ✅ Connection Management
**WebSocket reliability:**
- Auto-reconnect with exponential backoff (2s, 4s, 8s, 16s, 32s)
- Max 5 reconnection attempts
- Visual indicators (green/yellow/red dot)
- Ping/pong every 30s to keep alive
- Reconnect on network restore

---

## 📋 What Google IDX Will Build

With this updated prompt, the AI will create:

### **Queue Tab (Approval Interface)**
- Table with Team and Playlist dropdowns
- Autocomplete with existing options
- "Add new: [value]" for custom entries
- Validation before approval
- Confirmation modal
- Loading states
- Optimistic updates
- WebSocket real-time sync

### **History Tab (Results Viewer)**
- Clickable YouTube links (with thumbnail on hover)
- Clickable Drive links (with folder icon)
- Team and Playlist columns
- Status badges (COMPLETED/PROCESSING/ERROR)
- Expandable rows with full details
- Multiple filters (status, team, playlist, search)
- Export to CSV
- Real-time updates via WebSocket

### **Real-Time Features**
- Live status updates as backend processes
- Progress messages ("Downloading...", "Uploading to YouTube...")
- Completion notifications with links
- Error notifications with retry options
- Stats updates (animated count changes)
- Log streaming

### **Complete Workflow**
1. User sees pending recording in Queue
2. Selects team from dropdown (or types new)
3. Selects playlist from dropdown (or types new)
4. Clicks Approve → Modal confirms
5. Frontend sends API request
6. UI updates immediately (optimistic)
7. WebSocket confirms approval
8. Status changes to PROCESSING
9. User sees progress updates in real-time
10. Completion notification with YouTube link
11. Recording appears in History with all links
12. User can click to view on YouTube or Drive

---

## 🎯 The Prompt Now Covers

✅ **Complete approval workflow** (12 steps)  
✅ **Team & playlist selection** (dropdowns + custom values)  
✅ **YouTube upload process** (title format, playlists, captions)  
✅ **Google Drive organization** (folder structure, file naming)  
✅ **Status transitions** (PENDING → APPROVED → PROCESSING → COMPLETED)  
✅ **UI feedback** (toasts, spinners, optimistic updates)  
✅ **WebSocket events** (7 event types with complete schemas)  
✅ **Error handling** (validation, API errors, processing failures)  
✅ **Real-time updates** (live status, progress, completion)  
✅ **Filtering & search** (status, team, playlist, topic)  
✅ **Export functionality** (CSV export)  
✅ **Connection management** (auto-reconnect, indicators)  

---

## 🚀 Ready to Use!

The prompt in `GOOGLE_IDX_FRONTEND_PROMPT.md` is now **COMPLETE** and **PRODUCTION-READY**.

Just copy the prompt section (lines 11-478) and paste it into Google IDX/Firebase Studio!

The AI will build you a **fully functional, real-time dashboard** that:
- Handles the complete approval workflow
- Manages teams and playlists
- Shows real-time processing updates
- Displays YouTube and Drive links
- Filters and searches recordings
- Exports data to CSV
- Looks absolutely STUNNING

**Your frontend will be PERFECT! 🎨✨**
