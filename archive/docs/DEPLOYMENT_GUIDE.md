# 🚀 Production Deployment Guide

## Server File Structure

When you deploy to a server (VPS, cloud, etc.), here's how the file system works:

### Directory Structure
```
/home/user/ytz-automation/          # Your application root
├── src/                            # Python source code (from Git)
├── frontend/                       # React frontend (from Git)
├── config/                         # Configuration files (from Git)
├── secrets/                        # API credentials (NOT in Git)
│   ├── client_secret.json         # YouTube OAuth
│   ├── token.json                 # YouTube token
│   ├── token_drive.json           # Drive token
│   └── service_account.json       # Google Sheets service account
├── downloads/                      # TEMPORARY - Created automatically
│   └── (videos downloaded here)   # Deleted after upload
├── data/                           # PERSISTENT - Created automatically
│   └── vong_v2.db                 # SQLite database
└── .env                           # Environment variables (NOT in Git)
```

### How Video Processing Works on Server

**1. Download Phase** (Temporary Storage)
```
Zoom API → Server downloads/ folder
Example: /home/user/ytz-automation/downloads/20260202 Meeting.mp4
Size: ~500MB (temporary)
```

**2. Upload Phase** (Streaming)
```
downloads/20260202 Meeting.mp4 → YouTube API (streaming upload)
downloads/20260202 Meeting.mp4 → Drive API (streaming upload)
```

**3. Cleanup Phase** (Immediate)
```
DELETE: downloads/20260202 Meeting.mp4
Result: downloads/ folder is empty again
```

### Storage Requirements

**Server Disk Space Needed**:
- **Minimum**: 5GB free space
- **Recommended**: 20GB free space
- **Why**: Largest video might be 2-3GB, need buffer for concurrent processing

**Actual Usage**:
- Application code: ~50MB
- Database: ~10MB (grows slowly)
- Downloads folder: 0-3GB (temporary, cycles every few minutes)
- Secrets: <1MB

### What Goes in GitHub

✅ **Included in Git**:
- Source code (`src/`)
- Frontend code (`frontend/`)
- Documentation (`.md` files)
- Requirements (`requirements.txt`, `package.json`)
- Configuration templates

❌ **NOT in Git** (`.gitignore`):
- `downloads/` - Temporary video files
- `data/` - Database files
- `secrets/` - API credentials
- `.env` - Environment variables
- `node_modules/` - Dependencies

### Deployment Process

**Step 1: Clone Repository**
```bash
git clone https://github.com/yourusername/ytz-automation.git
cd ytz-automation
```

**Step 2: Create Runtime Directories**
```bash
mkdir -p downloads data secrets
```

**Step 3: Upload Secrets**
```bash
# Upload these files to secrets/ folder:
scp client_secret.json user@server:/home/user/ytz-automation/secrets/
scp token.json user@server:/home/user/ytz-automation/secrets/
scp token_drive.json user@server:/home/user/ytz-automation/secrets/
scp service_account.json user@server:/home/user/ytz-automation/secrets/
```

**Step 4: Create .env File**
```bash
nano .env
# Paste your environment variables
```

**Step 5: Install Dependencies**
```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run build
```

**Step 6: Start Services**
```bash
# Backend (with systemd)
sudo systemctl start ytz-backend

# Frontend (with nginx)
sudo systemctl restart nginx
```

### Server Recommendations

**Minimum Specs**:
- **CPU**: 2 cores
- **RAM**: 2GB
- **Disk**: 20GB SSD
- **Bandwidth**: Unlimited (or high quota)

**Recommended Specs**:
- **CPU**: 4 cores
- **RAM**: 4GB
- **Disk**: 50GB SSD
- **Bandwidth**: Unlimited

**Why More RAM/CPU**:
- Concurrent video uploads to YouTube and Drive
- Video transcoding (if needed)
- Multiple Zoom accounts scanning simultaneously

### Bandwidth Considerations

**Upload Bandwidth Usage**:
- Average video: 500MB
- Upload to YouTube: 500MB
- Upload to Drive: 500MB
- **Total per video**: ~1GB upload

**Monthly Estimate**:
- 100 videos/month × 1GB = 100GB upload
- **Recommendation**: Unlimited bandwidth plan

### Systemd Service Configuration

**Backend Service** (`/etc/systemd/system/ytz-backend.service`):
```ini
[Unit]
Description=YTZ Automation Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/user/ytz-automation
Environment="PATH=/home/user/ytz-automation/venv/bin"
ExecStart=/home/user/ytz-automation/venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ytz-backend
sudo systemctl start ytz-backend
sudo systemctl status ytz-backend
```

### Nginx Configuration

**Frontend + API Proxy** (`/etc/nginx/sites-available/ytz-automation`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend (React build)
    location / {
        root /home/user/ytz-automation/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Enable and Restart**:
```bash
sudo ln -s /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Monitoring & Logs

**View Backend Logs**:
```bash
sudo journalctl -u ytz-backend -f
```

**View Nginx Logs**:
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

**Check Disk Usage**:
```bash
df -h
du -sh /home/user/ytz-automation/downloads/
```

**Monitor Downloads Folder**:
```bash
watch -n 5 'ls -lh /home/user/ytz-automation/downloads/'
```

### Automatic Cleanup (Cron Job)

Even though the app cleans up after itself, add a safety cron job:

```bash
crontab -e
```

Add this line:
```cron
0 */6 * * * find /home/user/ytz-automation/downloads/ -type f -mtime +1 -delete
```

This deletes any files in downloads/ older than 1 day (backup cleanup).

### Security Considerations

**1. Protect Secrets**:
```bash
chmod 600 secrets/*
chmod 600 .env
```

**2. Firewall**:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

**3. SSL Certificate** (Let's Encrypt):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Backup Strategy

**What to Backup**:
- ✅ `data/vong_v2.db` - Database (daily)
- ✅ `secrets/` - API credentials (once)
- ✅ `.env` - Environment variables (once)
- ❌ `downloads/` - No need (temporary)

**Automated Backup Script**:
```bash
#!/bin/bash
# /home/user/backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/home/user/backups"
APP_DIR="/home/user/ytz-automation"

mkdir -p $BACKUP_DIR

# Backup database
cp $APP_DIR/data/vong_v2.db $BACKUP_DIR/vong_v2_$DATE.db

# Backup secrets (encrypted)
tar -czf $BACKUP_DIR/secrets_$DATE.tar.gz -C $APP_DIR secrets/

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

**Cron Schedule**:
```cron
0 2 * * * /home/user/backup.sh
```

### Troubleshooting

**Problem**: Downloads folder filling up
**Solution**: 
```bash
# Check for stuck processes
ps aux | grep python
# Manually clean
rm -rf /home/user/ytz-automation/downloads/*
# Restart service
sudo systemctl restart ytz-backend
```

**Problem**: Out of disk space
**Solution**:
```bash
# Check usage
df -h
du -sh /home/user/ytz-automation/*
# Clean old logs
sudo journalctl --vacuum-time=7d
```

**Problem**: Upload fails
**Solution**:
- Check internet connection
- Verify API tokens are valid
- Check logs for specific error
- Ensure Drive/YouTube quotas not exceeded

### Performance Optimization

**1. Use SSD Storage**:
- Faster video read/write
- Better for database operations

**2. Increase Upload Speed**:
- Choose server with high upload bandwidth
- Use server geographically close to Google data centers

**3. Concurrent Processing**:
- Current: Processes 1 video at a time
- Future: Can be modified to process multiple videos concurrently

### Cost Estimates

**VPS Hosting** (Monthly):
- **Budget**: Vultr/DigitalOcean - $12/month (2GB RAM, 50GB SSD)
- **Recommended**: Vultr/DigitalOcean - $24/month (4GB RAM, 80GB SSD)
- **Premium**: Linode/AWS - $40/month (8GB RAM, 160GB SSD)

**Bandwidth**:
- Most VPS providers include 1-2TB/month
- 100 videos/month = ~100GB (well within limits)

**Total Monthly Cost**: $12-40 depending on specs

## Quick Deploy Commands

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/ytz-automation.git
cd ytz-automation
mkdir -p downloads data secrets

# 2. Upload secrets (from local machine)
scp secrets/* user@server:/home/user/ytz-automation/secrets/

# 3. Create .env
nano .env
# Paste environment variables

# 4. Install backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Install frontend
cd frontend
npm install
npm run build
cd ..

# 6. Setup systemd service
sudo cp deploy/ytz-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ytz-backend
sudo systemctl start ytz-backend

# 7. Setup nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ytz-automation
sudo ln -s /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. Setup SSL
sudo certbot --nginx -d yourdomain.com

# Done!
```

## Summary

**Downloads Directory**:
- Created automatically on server
- NOT in Git
- Temporary storage only
- Auto-cleaned after each upload
- Typical size: 0-3GB (cycles rapidly)

**Your GitHub repo contains**:
- Source code
- Configuration templates
- Documentation

**Server creates at runtime**:
- `downloads/` - Temporary video storage
- `data/` - Database
- `secrets/` - You upload these manually

**This ensures**:
- ✅ No large files in Git
- ✅ Fast deployments
- ✅ Minimal disk usage
- ✅ Secure credential handling
