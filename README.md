# YTZ Automation System

> **Automated Zoom Recording Management** - Download, compress via YouTube, and backup to Google Drive with organized folder structures.

## 🎯 Overview

YTZ Automation is a complete workflow automation system that:
- 🔍 **Detects** new Zoom cloud recordings automatically
- ✅ **Approves** recordings via web dashboard (manual control)
- 📺 **Uploads** to YouTube for compression and hosting
- 💾 **Backs up** to Google Drive with organized folders
- 📊 **Tracks** everything in Google Sheets for transparency

## ✨ Features

- **Multi-Account Zoom Support** - Manage recordings from multiple Zoom accounts
- **Web Dashboard** - Modern Next.js interface with real-time updates
- **Smart Processing** - Automatic retry logic and error recovery
- **Playlist Organization** - Auto-create YouTube playlists and Drive folders
- **Complete Audit Trail** - Every action logged to Google Sheets
- **24/7 Operation** - Runs as a background service with health monitoring

## 🏗️ Architecture

```
┌─────────────┐
│  Zoom API   │ ──┐
└─────────────┘   │
                  ▼
┌─────────────────────────────┐
│  Backend (Python)           │
│  - Polling & Processing     │
│  - FastAPI Server           │
└─────────────────────────────┘
         │              │
         ▼              ▼
┌──────────────┐  ┌──────────────┐
│  YouTube API │  │  Drive API   │
└──────────────┘  └──────────────┘
         │              │
         └──────┬───────┘
                ▼
┌─────────────────────────────┐
│  Frontend (Next.js)         │
│  - Dashboard                │
│  - Approval Interface       │
└─────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Google Cloud Project with APIs enabled:
  - YouTube Data API v3
  - Google Drive API
  - Google Sheets API
- Zoom Server-to-Server OAuth App
- Firebase project (for authentication)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ytz-automation
   ```

2. **Set up backend**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Copy environment template
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Set up frontend**
   ```bash
   cd frontend
   npm install
   cp .env.local.example .env.local
   # Edit .env.local with your credentials
   ```

4. **Add API credentials**
   - Place `client_secret.json` in `secrets/` (YouTube OAuth)
   - Place `token.json` in `secrets/` (YouTube token)
   - Place `token_drive.json` in `secrets/` (Drive token)
   - Place `service_account.json` in `secrets/` (Sheets service account)

5. **Run locally**
   ```bash
   # Terminal 1: Backend automation
   python main.py
   
   # Terminal 2: API server
   python -m uvicorn src.api:app --reload --port 8000
   
   # Terminal 3: Frontend
   cd frontend
   npm run dev
   ```

6. **Access dashboard**
   - Open http://localhost:9002
   - Login with Google account (must be in ADMIN_EMAILS)

## 📦 Production Deployment

### Option 1: Automated Deployment (Recommended)

1. **Prepare server** (Ubuntu 20.04+ or Debian 11+)
   ```bash
   # On server, as root
   curl -o setup-server.sh https://raw.githubusercontent.com/your-repo/deploy/setup-server.sh
   chmod +x setup-server.sh
   sudo ./setup-server.sh
   ```

2. **Deploy application**
   ```bash
   # Switch to application user
   sudo su - ytzuser
   
   # Clone repository
   git clone <your-repo-url> /home/ytzuser/ytz-automation
   cd /home/ytzuser/ytz-automation
   
   # Upload secrets (from local machine)
   scp -r secrets/* ytzuser@server:/home/ytzuser/ytz-automation/secrets/
   scp .env ytzuser@server:/home/ytzuser/ytz-automation/
   
   # Run deployment script
   bash deploy/deploy.sh
   ```

3. **Verify deployment**
   ```bash
   # Check services
   sudo systemctl status ytz-automation
   sudo systemctl status ytz-api
   
   # Check logs
   sudo journalctl -u ytz-automation -f
   ```

### Option 2: Manual Deployment

See [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) for detailed step-by-step instructions.

## 📖 Documentation

- **[PRD.md](./PRD.md)** - Product Requirements Document
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Detailed deployment guide
- **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist
- **[QUICKSTART.md](./QUICKSTART.md)** - Quick reference guide

## 🛠️ Configuration

### Required Environment Variables

```bash
# Zoom Configuration
ZOOM_1_ACCOUNT_ID=your_account_id
ZOOM_1_CLIENT_ID=your_client_id
ZOOM_1_CLIENT_SECRET=your_client_secret

# Google Drive
DRIVE_ROOT_FOLDER_ID=your_folder_id

# Google Sheets
GOOGLE_SHEET_ID=your_sheet_id

# Admin Access
ADMIN_EMAILS=admin@example.com
```

See [.env.example](./.env.example) for complete configuration options.

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check configuration
python -c "from src.config import check_config; check_config()"

# Check logs
tail -f data/app.log
```

### Frontend not connecting to API
```bash
# Verify API is running
curl http://localhost:8000/health

# Check frontend environment
cat frontend/.env.local | grep API_BASE_URL
```

### Videos not uploading
```bash
# Check YouTube quota
# Check Drive storage space
# Check logs for specific errors
sudo journalctl -u ytz-automation | grep ERROR
```

## 📊 Monitoring

### Service Status
```bash
# Check all services
sudo systemctl status ytz-automation
sudo systemctl status ytz-api
sudo systemctl status nginx
```

### View Logs
```bash
# Backend automation logs
sudo journalctl -u ytz-automation -f

# API server logs
sudo journalctl -u ytz-api -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Health Check
```bash
# API health
curl http://localhost:8000/health/detailed

# Disk space
df -h /home/ytzuser/ytz-automation/downloads
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

[Your License Here]

## 🆘 Support

For issues and questions:
- Check [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- Review logs: `sudo journalctl -u ytz-automation -f`
- Open an issue on GitHub

---

**Built with ❤️ for automated Zoom recording management**
