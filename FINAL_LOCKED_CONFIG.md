# ✅ FINAL SYSTEM CONFIGURATION - LOCKED AND RIGID

## Drive Folder Mapping (NEVER CHANGE THESE)

### Recording Folders (Videos)
| Category | Playlist Name | Drive Folder ID |
|----------|---------------|-----------------|
| HR | 2.2.5 Enablers - HR | `1m9YBC8GQ7yeB0cwAkgtyopAMzwYRb4Tp` |
| Tech | 2.2.4 Tech Systems and Products | `1-ZdSCOUKHozKaMjCz5RqJkjr0tSKCwaR` |
| Marketing | 2.2.1 Marketing | `1KuMKFhbPzMoPdfAIlJitrI5BZEsd9-3Q` |
| Growth | 2.2.2 Growth | `1eWxD6uZdvF1Gk9byHl4aB71DyH7mWSWs` |
| Project Management | 2.2.5 Enablers - PM | `13FZuXmvh3I_WPn8dKGhCIHQDIAgRfjz5` |
| Research | 2.2.3 Research Analysis Bureau RAB | `1B7aQNscLGkz7jDPiRPt5FF8CGUifHFvm` |
| Community | 2.2.6 Community Building | `13pSMIo4Qso1BToFSP8lRmRukLQiPnETN` |
| OPM | 2.2.5 Enablers - OPM & HR | `1Tn5ZlkTimYJYyjxH3B_eeJLbnF4T0B6N` |
| Events | Essay Contest | `13otF9gCQahMvGaEF18mXYeKOd5Zp3EXJ` |
| Enablers | 2.2.5 Enablers | `1LRE1-1zW_1sKtPjX_7xrlb5OmPE3jBhP` |

### Transcript Folders
| Category | Playlist Name | Transcript Folder ID |
|----------|---------------|---------------------|
| HR | 2.2.5 Enablers - HR | `1ekdVgcqqrGCnZLCUegw4Y79dkc_-wGkB` |
| Tech | 2.2.4 Tech Systems and Products | `1x1ds_HHcLlMM3peBg7UqNWltYjusOfKd` |
| Marketing | 2.2.1 Marketing | `1gPWSqLGRV7pZ8cqGOyMwMFb94eNjANZy` |
| Growth | 2.2.2 Growth | `13SUptwBQ1iL8lqEMWbVDnpemVugXQ5MA` |
| Project Management | 2.2.5 Enablers - PM | `1nW-5ZdbgBjaNMYbdNuV1QziwGAAso-Wr` |
| Research | 2.2.3 Research Analysis Bureau RAB | `1Z-u6SpvGuHRp-sSesmGcHfO4SWXZcsX_` |
| Community | 2.2.6 Community Building | `1lz4L0josi7NXnwZSdxApGF1gJPW1KZFH` |
| OPM | 2.2.5 Enablers - OPM & HR | `1vIMx-FiqoxmN5scG9a4jJbKDN02piJ-7` |
| Events | Essay Contest | `1PGococ2OOJn3KCEekIa-Y2_oF8HKdV81` |
| Enablers | 2.2.5 Enablers | `1PGococ2OOJn3KCEekIa-Y2_oF8HKdV81` |

## Complete Workflow (RIGID STRUCTURE)

### 1. Discovery (Automated - Every 60 seconds)
```
Scan Zoom (90 days back)
↓
Match Meeting ID to Playlist (config/playlists.json)
↓
Add to Database (status: PENDING)
↓
Add to Google Sheet (with auto-matched Team/Playlist if found)
```

### 2. Approval (Manual - Google Sheet)
User fills 3 required fields:
- **Team**: Category name (e.g., "HR", "Tech", "Marketing")
- **Playlist**: Exact playlist name (e.g., "2.2.5 Enablers - HR")
- **Approved By**: User's name/email

### 3. Processing (Automated - Triggered by Approval)
```
1. Download from Zoom
   ├─ Video (MP4)
   └─ Transcript (VTT/TXT)

2. Upload to YouTube
   ├─ Title: "YYYYMMDD Topic Name"
   ├─ Upload video
   ├─ Upload transcript as captions
   └─ Add to playlist (from approval)

3. Upload to Drive
   ├─ Video → drive_folder_id (from config)
   └─ Transcript → transcript_folder_id (from config)

4. Verify Uploads
   ├─ Check YouTube status
   └─ Check Drive file IDs

5. Delete from Zoom (ONLY if verified)
   └─ Permanent deletion via API

6. Cleanup Local Files
   ├─ Delete video from data/downloads/
   └─ Delete transcript from data/downloads/

7. Mark as COMPLETED
   ├─ Update database
   └─ Update Google Sheet with URLs
```

## Critical Rules (NEVER VIOLATE)

1. ✅ **NEVER create new YouTube playlists** - Only use the 10 existing ones
2. ✅ **NEVER create new Drive folders** - Only use the exact folder IDs provided
3. ✅ **NEVER delete from Zoom** until both YouTube AND Drive uploads are verified
4. ✅ **ALWAYS upload transcripts** to both YouTube (captions) and Drive (file)
5. ✅ **ALWAYS use separate folders** for videos and transcripts in Drive
6. ✅ **ONLY create new playlists/folders** when user explicitly creates them via frontend

## New Playlist Creation (Future Feature)

When user creates a new playlist via frontend:
1. Frontend sends: `playlist_name`, `category`
2. Backend creates:
   - New YouTube playlist
   - New Drive folder for recordings
   - New Drive folder for transcripts
3. Backend updates `config/playlists.json` with:
   - `playlist_id` (from YouTube)
   - `drive_folder_id` (from Drive)
   - `transcript_folder_id` (from Drive)
4. System immediately starts using new folders

## File Naming Convention

**Format**: `YYYYMMDD Topic Name`

**Examples**:
- Video: `20260202 Tech Systems Meeting.mp4`
- Transcript: `20260202 Tech Systems Meeting_transcript.txt`
- YouTube Title: `20260202 Tech Systems Meeting`

## Current System Status

**Total Recordings**: 29 unique meetings
- ✅ Completed: 3
- ⏳ Pending: 25
- ⚙️ Processing: 1

**Zoom Accounts**: 2 configured
**Scan Range**: Last 90 days
**Scan Frequency**: Every 60 seconds

## Configuration Files

### `config/playlists.json`
Contains complete mapping:
```json
{
  "playlist_id": "PLXGtGl2Kq18ak7zQvO16G1nnItDlI7Wno",
  "playlist_name": "2.2.5 Enablers - HR",
  "category": "HR",
  "drive_folder_id": "1m9YBC8GQ7yeB0cwAkgtyopAMzwYRb4Tp",
  "transcript_folder_id": "1ekdVgcqqrGCnZLCUegw4Y79dkc_-wGkB",
  "meeting_ids": ["81198809795"]
}
```

### Google Sheet
**ID**: `1k-SC36HxPRb9SdY9PvaT4qYtZa8Sw5fmWBK30WPKhao`
**URL**: https://docs.google.com/spreadsheets/d/1k-SC36HxPRb9SdY9PvaT4qYtZa8Sw5fmWBK30WPKhao/edit

## Verification Checklist

Before marking as COMPLETED, system verifies:
- [x] YouTube video uploaded (status: 'uploaded' or 'processed')
- [x] YouTube captions uploaded (if transcript exists)
- [x] Video added to correct playlist
- [x] Drive video uploaded to correct folder
- [x] Drive transcript uploaded to correct folder
- [x] Both Drive file IDs exist
- [x] Google Sheet updated with both URLs
- [x] Zoom recording deleted
- [x] Local files cleaned up

## Error Handling

If ANY step fails:
1. Status → `ERROR`
2. Error message logged
3. Zoom recording NOT deleted
4. Local files preserved for manual recovery
5. Google Sheet shows ERROR status

## System is Production Ready ✅

All configurations locked. System will:
- ✅ Use exact Drive folder IDs provided
- ✅ Never create new folders unless explicitly requested
- ✅ Upload videos and transcripts to separate folders
- ✅ Verify all uploads before deletion
- ✅ Maintain complete audit trail
