# Zoom Automation Pipeline
**Master Documentation**

This document outlines the architecture, deployment, and usage of the Zoom Automation pipeline. This system automatically pulls completed cloud recordings from connected Zoom accounts, organizes them based on topic names, uploads them to designated YouTube playlists and Google Drive folders, and deletes the original file from Zoom to save space.

---

## 🏗️ Architecture Layout

The codebase has been highly structured to prioritize modularity and stability.

-   **`/src`**: Contains all core logic.
    -   `main.py`: The orchestrator thread. Manages scanning, download/upload, and the cleanup queue.
    -   `youtube_client.py` / `drive_client.py` / `zoom_client.py`: API wrappers handling their respective OAuth and Network logic.
    -   `db.py` / `db_sql.py`: Data persistence layer (SQLite) handling the `PENDING -> PROCESSING -> COMPLETED` lifecycle.
-   **`/config`**: Configuration data.
    -   `playlists.json`: Controls where specific video keywords are routed. (e.g., matching "HR" to the HR playlist ID).
-   **`/secrets`**: (Git-ignored) Contains OAuth binaries required for Google (`token_youtube.json`, `token_drive.json`, etc.)
-   **`/data`**: Contains the SQLite database file tracking all successfully downloaded and uploaded recordings, preventing duplicates.
-   **`/archive`**: Contains older documentation, test payload dumps, development scripts, and system logs saved during the project's construction phase.

---

## 🚀 How It Works (The Pipeline)

1.  **Phase 1 - Discovery (Scanning Zoom)**
    Every 60 seconds, the background service connects to the registered Zoom accounts (`Server-to-Server OAuth`). It pulls all recordings made within the last 2 days. It analyzes the `topic` name against `playlists.json`. 
    -   If a keyword matches, the video is instantly added to the database as **`APPROVED`**.
    -   If no keyword matches, it remains **`PENDING`** until an admin categorizes it via the Frontend UI.

2.  **Phase 2 - Execution (Processing Queue)**
    The system reads the **`APPROVED`** queue.
    -   It downloads the `MP4` Recording and the `VTT` Transcript to the local server.
    -   It uses `YouTubeClient` to upload the video and captions to the verified A4G-Collab YouTube channel (`unlisted`), attaching it directly to the matched Playlist.
    -   It downloads the `MP4` Recording from youtube and then it uses `DriveClient` to mirror the downloaded `MP4` and `VTT` files into the matching Google Drive Folder.
    -   The record is flipped to **`COMPLETED`**.

3.  **Phase 3 - Cleanup (Zoom Deletion)**
    To ensure data safety, videos are not deleted instantly.
    -   After `DELETE_DELAY_HOURS` (Configurable, defaults to a 24 hours) has passed since Completion, Phase 3 wakes up.
    -   It queries the YouTube API and Drive API a *second time* to strictly verify the uploads are still 100% active and healthy.
    -   Only if both verifications pass does it send the final `DELETE` command to the Zoom Cloud, freeing up recording quota.

---

## 💻 Developer Commands

**Start the Service Locally**
From standard powershell on your computer:
```bash
./Start_Automation.bat
```
*(This triggers the `main.py` entrypoint)*

**Run a Database/Pipeline Mock Execution**
If you want to force test a video without recording a real one on Zoom, run the provided utility via the isolated virtual environment:
*(Live VPS only)*
```bash
cd /home/ytzapp/ZoomAutomation && ./venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from src.db_sql import db
p = db.get_pending()
if p:
    rec = p[0]
    db.update_recording(rec['zoom_id'], {'status': 'APPROVED', 'team': 'Tech', 'playlist': '2.2.4 Tech Systems and Products', 'approved_by': 'AutoTest'})
    print(f\"Forced video: '{rec['topic']}' to APPROVED!\")
"
```

---

## 🌐 VPS (Vultr) Management

The active, live node runs on a dedicated Vultr instance. 

1.  **Re-deploying Updates**
    If you change the source code on your local computer, you must push the changes to the active User Path on the VPS:
    ```powershell
    # Run from local computer
    scp -r src root@YOUR_SERVER_IP:/home/ytzapp/ZoomAutomation/
    ```

2.  **Monitoring the Live Pipeline**
    To view exactly what the server is doing in real-time:
    ```bash
    # Run inside VPS
    sudo journalctl -u ytz-backend -f
    ```

3.  **Restarting the Backend Process**
    Whenever `src/` or `config/` files change, restart the systemd service:
    ```bash
    # Run inside VPS
    systemctl restart ytz-backend
    ```
