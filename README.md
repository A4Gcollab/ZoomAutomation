# YTZ Automation System

> **Automated Zoom Recording Management** - Download, compress via YouTube, and backup to Google Drive with organized folder structures.

## 🎯 Overview

YTZ Automation is a complete workflow automation system built for Omysha. It manages the entire lifecycle of Zoom cloud recordings by automating the heavy lifting.

- 🔍 **Detects** new Zoom cloud recordings automatically
- ✅ **Approves** recordings via a clean Next.js web dashboard
- 📺 **Compresses** videos by uploading them to YouTube (unlisted) and downloading the optimized `MP4`
- 💾 **Backs up** the highly-compressed video and `VTT` transcripts to assigned Google Drive folders
- 📊 **Tracks** all operations in Google Sheets for full transparency
- 🗑️ **Auto-Deletes** the original massive Zoom cloud recordings 24 hours after a healthy backup is verified.

## ✨ Features

- **Multi-Account Zoom Support** - Parallel scanning from multiple active Zoom accounts.
- **Smart Video Compression Pipeline** - Leverages YouTube's world-class video encoding to shrink gigabyte zoom files down to small Drive backups.
- **Playlist Organization** - Automatically binds specific meeting topics (like "HR" or "Townhall") to strict YouTube Playlists and matching Google Drive Folders.
- **Complete Audit Trail** - Every success, failure, and retry is logged to Google Sheets.
- **24/7 Background Daemon** - Runs persistently with Phase 1 (Scanning), Phase 2 (Execution), and Phase 3 (Cleanup) health cycles.


### The Compression Workflow
To bypass Zoom's massive raw file sizes, this system does not copy directly from Zoom to Drive. Once a video is approved:
1. It downloads the RAW video from Zoom.
2. It uploads the video to the A4G-Collab YouTube channel as `Unlisted`.
3. YouTube natively processes and perfectly compresses the video.
4. The Backend downloads the newly compressed `MP4` back from YouTube.
5. It uploads *this* compressed file (alongside the original transcript) to Google Drive, saving enormous amounts of Drive storage.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- Google Cloud Project with APIs enabled (YouTube Data API v3, Google Drive, Google Sheets)
- Zoom Server-to-Server OAuth App
- Firebase Authentication Project (Email/Password & Google Sign-In)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/A4Gcollab/ZoomAutomation.git
   cd ZoomAutomation
   ```

2. **Set up Python Backend**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up Next.js Frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Add API credentials**
   - Populate `.env` in the root folder using `.env.example` as a template.
   - Place `client_secret.json` in `secrets/` (YouTube OAuth)
   - Place `token.json` in `secrets/` (YouTube live token)
   - Place `token_drive.json` in `secrets/` (Drive token)
   - Place `service_account.json` in `secrets/` (Sheets service account)

5. **Run Locally**
   ```bash
   # Windows
   ./Start_Automation.bat
   
   # Or manually (running all services):
   python src/main.py             # Starts background daemon
   uvicorn src.api:app --port 8000 # Starts FastAPI
   cd frontend && npm run dev     # Starts UI dashboard
   ```

## 📦 Production Deployment (VPS)

The system is designed to run seamlessly on a Vultr VPS (Ubuntu 22.04 LTS). 

**Recommended Deployment (via bash script):**
```bash
sudo ./scripts/deploy.sh
```

For strict manual deployment controls, systemd configurations, and exact firewall rules, see to the `HANDOVER.md` and `DOCUMENTATION.md` files located in the root directory.

## 📖 Deep-Dive Documentation

- **[DOCUMENTATION.md](./DOCUMENTATION.md)** - Master pipeline logic and architecture details.
- **[USER_GUIDE.md](./USER_GUIDE.md)** - A User Mannual for Zoom Automation.
- **[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)** - A Developer's Mannual for Zoom Automation.



## 🤝 Contributing

1. Create a feature branch (`git checkout -b feature/xyz`)
2. Make your improvements
3. Ensure no secrets (like `token.json` or `.env` files) are tracked by git.
4. Submit a Pull Request to the `main` or active deployment branch.

---

**Built with patience for automated Zoom recording management by Tech lead Sneha Chouksey at A4GCollab **
