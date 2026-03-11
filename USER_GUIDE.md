# 📘 YTZ Automation — User Guide

> A step-by-step guide for **admins and team leads** who use the dashboard to manage Zoom recording uploads.

---

## 1. What Does This System Do?

YTZ Automation handles your organization's Zoom cloud recordings **automatically**:

1. **Detects** new recordings from all connected Zoom accounts.
2. **Categorizes** them by matching the meeting title to keywords (e.g., "HR", "Tech", "Marketing").
3. **Uploads** the video to a YouTube playlist (unlisted) and Google Drive folder.
4. **Logs** every action to a shared Google Sheet for full transparency.
5. **Deletes** the original Zoom cloud recording after 24 hours, once backups are verified.

> **You don't need to download anything manually.** The system runs 24/7 on a dedicated server.

---

## 2. The Dashboard

The **web dashboard** is available at your organization's URL (e.g., `https://za.omysha.org`).

### 2.1 Logging In

- Click **"Sign in with Google"** on the login page.
- Use your **organization Google account** (e.g., `you@omysha.com`).
- Only authorized email addresses can access the dashboard.

### 2.2 Dashboard Overview

After logging in, you'll see:

| Section         | What It Shows                                                       |
|-----------------|---------------------------------------------------------------------|
| **Stats Bar**   | Total completed, pending, processing, approved, and errored videos. |
| **Queue**       | Recordings waiting for your approval.                               |
| **History**     | All processed recordings with YouTube and Drive links.              |
| **Logs**        | Live system logs (errors, successes, etc.).                         |

---

## 3. How Videos Get Processed

### 3.1 Auto-Matched Videos (No Action Required)

If a Zoom meeting title contains a **known keyword**, the system automatically:
- Assigns it to the correct **team** and **playlist**.
- Marks it as **APPROVED**.
- Begins processing immediately — no admin action needed.

**Example keywords that trigger auto-matching:**

| Keyword            | Assigned Category       | YouTube Playlist                     |
|--------------------|-------------------------|--------------------------------------|
| `hr`, `recruitment`| HR                      | 2.2.5 Enablers - HR                 |
| `tech`, `systems`  | Tech                    | 2.2.4 Tech Systems and Products     |
| `marketing`, `brand`| Marketing              | 2.2.1 Marketing                     |
| `growth`, `sales`  | Growth                  | 2.2.2 Growth                        |
| `research`, `rab`  | Research                | 2.2.3 Research Analysis Bureau RAB   |
| `community`        | Community               | 2.2.6 Community Building             |
| `townhall`         | Townhall                | Townhall                             |
| `essay`, `contest` | Events                  | Essay Contest                        |
| `sponsorship`      | Sponsorship             | Sponsorship and Fundraising          |
| `intern`, `pm meeting` | Project Management  | 2.2.5 Enablers - PM                 |

> Keywords are **case-insensitive**. A meeting titled "HR Standup Call" will match because it contains "hr".

### 3.2 Unmatched Videos (Requires Your Approval)

If a recording's title doesn't match any keyword, it appears in the **Queue** as `PENDING_PLAYLIST`.

**To approve:**

1. Find the recording in the Queue.
2. **Select a Team** (e.g., Tech, HR, Marketing).
3. **Select a Playlist** (e.g., "2.2.4 Tech Systems and Products").
4. Click **Approve**.

> **Bulk Approval**: When you approve one instance of a recurring meeting, all other pending instances of the same meeting are automatically approved with the same settings.

---

## 4. Recording Lifecycle

Every video goes through these stages:

```
PENDING_PLAYLIST → APPROVED → PROCESSING → COMPLETED → ZOOM DELETED
        ↑                                       ↑             ↑
  (No keyword match)              (YouTube + Drive done)  (After 24h safety)
```

| Status              | Meaning                                                              |
|---------------------|----------------------------------------------------------------------|
| `PENDING_PLAYLIST`  | Waiting for admin to assign a team and playlist.                     |
| `APPROVED`          | Queued for processing. The system will handle it in the next cycle.  |
| `PROCESSING`        | Currently being downloaded from Zoom and uploaded to YouTube/Drive.  |
| `COMPLETED`         | Successfully uploaded to YouTube and Google Drive.                   |
| `ERROR`             | Something went wrong. The system will auto-retry up to 3 times.     |
| `ZOOM DELETED`      | Original Zoom cloud recording has been safely deleted.               |

---

## 5. Where Do My Videos End Up?

Every completed video is stored in **two places**:

### YouTube (Unlisted)
- Uploaded to the **A4G-Collab YouTube channel**.
- Set to **Unlisted** — not publicly discoverable, but accessible via link.
- Automatically added to the correct playlist.
- Captions/transcripts are uploaded alongside the video.

### Google Drive
- The **compressed video** (MP4) is uploaded to the matching Drive folder.
- The **transcript** (VTT) is uploaded to a separate transcripts subfolder.
- Organized by team/category.

### Google Sheets
- Every recording is logged in a shared Google Sheet.
- Includes: Date, Meeting ID, Title, Team, Playlist, Status, YouTube Link, Drive Link.

---

## 6. Automatic Zoom Deletion

To save Zoom cloud storage, the system automatically deletes original recordings **after a safety period**:

1. The video must be **COMPLETED** (uploaded to both YouTube and Drive).
2. At least **24 hours** must have passed since completion.
3. The system **re-verifies** that the YouTube video and Drive file still exist.
4. **Only then** does it delete from Zoom.

> If either the YouTube or Drive backup is missing, the system **will NOT delete** the Zoom original. This is a critical safety mechanism.

---

## 7. Error Handling & Auto-Recovery

The system handles errors gracefully:

- **Auto-Retry**: Failed recordings are retried up to **3 times** automatically.
- **Stuck Processing**: If a video is stuck in `PROCESSING` for over 60 minutes, it's automatically reset and retried.
- **YouTube Quota**: If YouTube's daily upload quota is hit, the system pauses uploads for 24 hours and resumes automatically.

> If a video fails after 3 retries, it appears in the error list. Contact your system administrator.

---

## 8. Google Sheets Audit Trail

The linked Google Sheet serves as your complete audit trail:

| Column       | Description                          |
|--------------|--------------------------------------|
| Date         | Recording date                       |
| Meeting ID   | Zoom meeting identifier              |
| Title        | Meeting topic name                   |
| Team         | Assigned team/category               |
| Playlist     | YouTube playlist name                |
| Status       | Current processing status            |
| Approved By  | Email of the admin who approved      |
| YT Link      | YouTube video link (when completed)  |
| Drive Link   | Google Drive file link               |

---

## 9. FAQ

### Q: A recording is stuck in "PENDING" — what do I do?
**A:** Go to the Queue, select the appropriate Team and Playlist, and click Approve. The system will process it in the next 60-second cycle.

### Q: Can I change the playlist after approving?
**A:** Not through the dashboard currently. Contact the system administrator to update the database record manually.

### Q: How long does processing take?
**A:** Typically **5–15 minutes** per video, depending on file size. Large files (2+ GB) may take longer.

### Q: A video shows ERROR status — is my recording lost?
**A:** No. The original is still safe on Zoom Cloud. The system will auto-retry up to 3 times. If it still fails, the admin can investigate the error message.

### Q: Who can access the dashboard?
**A:** Only users with authorized Google accounts. All logged-in users can approve recordings. Admin users have additional access to system logs and settings.

### Q: How do I add a new keyword or category?
**A:** This requires editing the `playlists.json` configuration file. Contact your system administrator or developer.

---

## 10. Support

If you encounter any issues:

1. **Check the Logs** tab in the dashboard for recent error messages.
2. **Check Google Sheets** for the recording's current status.
3. Contact the **system administrator** with the recording's Meeting ID and the error message.

---

*This guide covers the YTZ Automation System v2.1. For technical or developer documentation, see the Developer Guide.*
