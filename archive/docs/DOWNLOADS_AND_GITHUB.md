# 📦 Download Directory & GitHub Deployment - Quick Answer

## Where Videos Are Downloaded

### On Your Local Machine (Development)
```
D:\VONG\YTZ Automation\downloads\
```

### On Production Server (Hosting)
```
/home/user/ytz-automation/downloads/
```

## How It Works

### 1. Download (Temporary)
```
Zoom API → downloads/20260202 Meeting.mp4 (500MB)
```
Video is saved temporarily to the `downloads/` folder.

### 2. Upload (Streaming)
```
downloads/20260202 Meeting.mp4 → YouTube API (streaming)
downloads/20260202 Meeting.mp4 → Drive API (streaming)
```
File is read from disk and streamed to YouTube and Drive.

### 3. Cleanup (Immediate)
```
DELETE: downloads/20260202 Meeting.mp4
```
After successful upload verification, file is deleted immediately.

**Result**: `downloads/` folder is empty again, ready for next video.

## GitHub & Deployment

### What's in GitHub ✅
- Source code (`src/`, `frontend/`)
- Configuration templates
- Documentation
- Deployment scripts

### What's NOT in GitHub ❌
- `downloads/` - Temporary files (excluded via `.gitignore`)
- `data/` - Database files (excluded via `.gitignore`)
- `secrets/` - API credentials (excluded via `.gitignore`)
- `.env` - Environment variables (excluded via `.gitignore`)

### Server Setup Process

**1. Clone from GitHub**
```bash
git clone https://github.com/yourusername/ytz-automation.git
cd ytz-automation
```

**2. Server Creates Runtime Directories**
```bash
mkdir -p downloads data secrets
```

**3. You Upload Secrets Manually**
```bash
scp secrets/* user@server:/home/user/ytz-automation/secrets/
```

**4. Run Deployment Script**
```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

## Storage Requirements

### Server Disk Space
- **Minimum**: 5GB free
- **Recommended**: 20GB free
- **Why**: Largest video might be 2-3GB temporarily

### Actual Usage
- Application: ~50MB
- Database: ~10MB
- Downloads: **0-3GB** (temporary, cycles every few minutes)

### Example Timeline
```
00:00 - downloads/ is empty (0GB)
00:01 - Video downloads (2GB)
00:05 - Uploading to YouTube and Drive
00:10 - Upload complete, file deleted
00:10 - downloads/ is empty again (0GB)
```

## Key Points

✅ **Videos are NOT stored permanently on server**
- Downloaded temporarily
- Uploaded immediately
- Deleted after verification

✅ **GitHub repo stays small**
- No large files
- Only source code
- Fast clones

✅ **Server creates folders automatically**
- `downloads/` created on first run
- `data/` created on first run
- No manual setup needed

✅ **Secure credential handling**
- Secrets uploaded separately
- Never committed to Git
- Protected with file permissions

## Quick Deploy Commands

```bash
# On your server:
git clone https://github.com/yourusername/ytz-automation.git
cd ytz-automation
chmod +x deploy/deploy.sh
./deploy/deploy.sh

# Follow the prompts to:
# - Install dependencies
# - Build frontend
# - Setup systemd service
# - Configure nginx
# - Install SSL certificate
```

That's it! The system handles everything else automatically.

## Monitoring Downloads Folder

```bash
# Watch downloads folder in real-time
watch -n 2 'ls -lh /home/user/ytz-automation/downloads/'

# Check disk usage
df -h

# View processing logs
sudo journalctl -u ytz-backend -f
```

## Summary

**Question**: Where will videos be downloaded when hosting on GitHub?

**Answer**: 
1. Videos download to `downloads/` folder **on the server** (not GitHub)
2. `downloads/` folder is **temporary** and **not in Git**
3. Videos are **deleted immediately** after upload
4. Server needs **5-20GB free space** for temporary storage
5. GitHub repo contains **only source code** (~50MB)

**Your GitHub repo will be small and clean** - no large files, just code! 🎉
