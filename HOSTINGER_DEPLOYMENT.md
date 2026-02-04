# 🚀 HOSTINGER VPS DEPLOYMENT - za.omysha.org

## Complete Step-by-Step Guide

### Prerequisites
- ✅ Hostinger VPS purchased
- ✅ Domain `za.omysha.org` pointed to VPS IP
- ✅ SSH access to VPS
- ✅ All API credentials ready locally

---

## STEP 1: Get Your VPS IP Address

### From Hostinger Panel
1. Log in to Hostinger
2. Go to **VPS** section
3. Click on your VPS
4. Copy the **IP Address** (e.g., `123.45.67.89`)

### Verify DNS
```bash
# On your local machine
nslookup za.omysha.org
```

**Expected output**:
```
Server:  dns.server.com
Address:  8.8.8.8

Name:    za.omysha.org
Address:  123.45.67.89  # Should match your VPS IP
```

**If IP doesn't match**:
1. Go to Hostinger DNS settings
2. Update A record for `za` subdomain
3. Point to your VPS IP
4. Wait 5-10 minutes for DNS propagation

---

## STEP 2: Initial VPS Setup

### Connect to VPS
```bash
ssh root@123.45.67.89
# Or if you have a username:
ssh username@123.45.67.89
```

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Software
```bash
# Install Python 3.11+
sudo apt install -y python3 python3-pip python3-venv

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install -y nginx

# Install Certbot (for SSL)
sudo apt install -y certbot python3-certbot-nginx

# Install Git
sudo apt install -y git

# Install other utilities
sudo apt install -y curl wget unzip
```

### Create Application User
```bash
# Create dedicated user for the app
sudo useradd -m -s /bin/bash ytzapp
sudo usermod -aG sudo ytzapp

# Set password
sudo passwd ytzapp

# Switch to app user
sudo su - ytzapp
```

---

## STEP 3: Upload Files to VPS

### Method 1: Using Git (Recommended)

**On your local machine**:
```bash
# Initialize git repo (if not already)
cd "D:\VONG\YTZ Automation"
git init
git add .
git commit -m "Initial commit"

# Push to GitHub (create private repo first)
git remote add origin https://github.com/yourusername/ytz-automation.git
git branch -M main
git push -u origin main
```

**On VPS**:
```bash
# As ytzapp user
cd /home/ytzapp
git clone https://github.com/yourusername/ytz-automation.git
cd ytz-automation
```

### Method 2: Using SCP (Direct Upload)

**On your local machine (PowerShell)**:
```powershell
# Upload entire project
scp -r "D:\VONG\YTZ Automation" ytzapp@123.45.67.89:/home/ytzapp/

# Or use WinSCP (GUI tool)
# Download from: https://winscp.net/
```

### Method 3: Using SFTP (FileZilla)

1. Download FileZilla: https://filezilla-project.org/
2. Connect:
   - Host: `sftp://123.45.67.89`
   - Username: `ytzapp`
   - Password: (your password)
   - Port: `22`
3. Drag and drop entire folder

---

## STEP 4: Upload Secrets

**On your local machine**:
```powershell
# Upload secrets folder
scp -r "D:\VONG\YTZ Automation\secrets" ytzapp@123.45.67.89:/home/ytzapp/ytz-automation/

# Upload .env file
scp "D:\VONG\YTZ Automation\.env" ytzapp@123.45.67.89:/home/ytzapp/ytz-automation/
```

**Verify on VPS**:
```bash
cd /home/ytzapp/ytz-automation
ls -la secrets/
# Should see: client_secret.json, token.json, token_drive.json, service_account.json

cat .env
# Should see all your environment variables
```

---

## STEP 5: Install Dependencies

**On VPS**:
```bash
cd /home/ytzapp/ytz-automation

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# Install Node packages and build frontend
cd frontend
npm install
npm run build
cd ..
```

---

## STEP 6: Setup Systemd Service

**Create service file**:
```bash
sudo nano /etc/systemd/system/ytz-backend.service
```

**Paste this** (update paths if needed):
```ini
[Unit]
Description=YTZ Automation Backend Service
After=network.target

[Service]
Type=simple
User=ytzapp
WorkingDirectory=/home/ytzapp/ytz-automation
Environment="PATH=/home/ytzapp/ytz-automation/venv/bin"
ExecStart=/home/ytzapp/ytz-automation/venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Enable and start service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ytz-backend
sudo systemctl start ytz-backend

# Check status
sudo systemctl status ytz-backend
```

**View logs**:
```bash
sudo journalctl -u ytz-backend -f
```

---

## STEP 7: Configure Nginx

**Create nginx config**:
```bash
sudo nano /etc/nginx/sites-available/ytz-automation
```

**Paste this**:
```nginx
server {
    listen 80;
    server_name za.omysha.org;

    # Frontend (React build)
    location / {
        root /home/ytzapp/ytz-automation/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeout for long uploads
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Increase max upload size
    client_max_body_size 5G;
}
```

**Enable site**:
```bash
sudo ln -s /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

---

## STEP 8: Install SSL Certificate

```bash
sudo certbot --nginx -d za.omysha.org
```

**Follow prompts**:
1. Enter email address
2. Agree to terms
3. Choose to redirect HTTP to HTTPS (option 2)

**Verify SSL**:
```bash
# Visit in browser
https://za.omysha.org
```

**Auto-renewal** (already configured):
```bash
# Test renewal
sudo certbot renew --dry-run
```

---

## STEP 9: Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## STEP 10: Verify Everything Works

### Check Backend
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Check Frontend
```bash
curl http://localhost/
# Should return HTML
```

### Check Public Access
**In your browser**:
```
https://za.omysha.org
```

**You should see**:
- ✅ Frontend loads
- ✅ SSL certificate valid
- ✅ Can log in with Google
- ✅ Dashboard shows recordings

### Check Logs
```bash
# Backend logs
sudo journalctl -u ytz-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

---

## STEP 11: Setup Monitoring

### Create Health Check Script
```bash
nano /home/ytzapp/health_check.sh
```

**Paste**:
```bash
#!/bin/bash

# Check if backend is running
if ! systemctl is-active --quiet ytz-backend; then
    echo "Backend is down! Restarting..."
    sudo systemctl restart ytz-backend
    echo "Backend restarted at $(date)" >> /home/ytzapp/restart.log
fi

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "Nginx is down! Restarting..."
    sudo systemctl restart nginx
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is at ${DISK_USAGE}%"
    # Clean old downloads
    find /home/ytzapp/ytz-automation/downloads/ -type f -mtime +1 -delete
fi
```

**Make executable**:
```bash
chmod +x /home/ytzapp/health_check.sh
```

**Add to crontab**:
```bash
crontab -e
```

**Add this line**:
```cron
*/5 * * * * /home/ytzapp/health_check.sh
```

---

## STEP 12: Setup Backup

### Create Backup Script
```bash
nano /home/ytzapp/backup.sh
```

**Paste**:
```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ytzapp/backups"
APP_DIR="/home/ytzapp/ytz-automation"

mkdir -p $BACKUP_DIR

# Backup database
cp $APP_DIR/data/vong_v2.db $BACKUP_DIR/vong_v2_$DATE.db

# Backup .env
cp $APP_DIR/.env $BACKUP_DIR/env_$DATE.txt

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed at $(date)" >> $BACKUP_DIR/backup.log
```

**Make executable and schedule**:
```bash
chmod +x /home/ytzapp/backup.sh

crontab -e
# Add:
0 2 * * * /home/ytzapp/backup.sh
```

---

## STEP 13: Final Security Hardening

### Protect Secrets
```bash
cd /home/ytzapp/ytz-automation
chmod 600 secrets/*
chmod 600 .env
```

### Disable Root SSH (Optional but Recommended)
```bash
sudo nano /etc/ssh/sshd_config
```

**Change**:
```
PermitRootLogin no
```

**Restart SSH**:
```bash
sudo systemctl restart sshd
```

---

## Verification Checklist

- [ ] VPS IP matches DNS for za.omysha.org
- [ ] All files uploaded to /home/ytzapp/ytz-automation
- [ ] Secrets folder contains all 4 files
- [ ] .env file has all environment variables
- [ ] Python dependencies installed
- [ ] Frontend built successfully
- [ ] Backend service running
- [ ] Nginx configured and running
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] https://za.omysha.org loads correctly
- [ ] Can log in with Google
- [ ] Dashboard shows data
- [ ] Health check script running
- [ ] Backup script scheduled

---

## Useful Commands

### Restart Backend
```bash
sudo systemctl restart ytz-backend
```

### View Backend Logs
```bash
sudo journalctl -u ytz-backend -f
```

### Restart Nginx
```bash
sudo systemctl restart nginx
```

### Check Disk Usage
```bash
df -h
du -sh /home/ytzapp/ytz-automation/*
```

### Monitor Downloads Folder
```bash
watch -n 2 'ls -lh /home/ytzapp/ytz-automation/downloads/'
```

### Update Application
```bash
cd /home/ytzapp/ytz-automation
git pull
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart ytz-backend
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u ytz-backend -n 50

# Common issues:
# - Missing secrets files
# - Wrong file permissions
# - Port 8000 already in use
```

### Frontend shows 502 Bad Gateway
```bash
# Backend is not running
sudo systemctl status ytz-backend
sudo systemctl start ytz-backend
```

### SSL certificate fails
```bash
# Check DNS
nslookup za.omysha.org

# Try manual certbot
sudo certbot certonly --nginx -d za.omysha.org
```

---

## Support

If you encounter issues:
1. Check logs: `sudo journalctl -u ytz-backend -f`
2. Verify DNS: `nslookup za.omysha.org`
3. Test backend: `curl http://localhost:8000/health`
4. Check firewall: `sudo ufw status`

**Your application is now live at: https://za.omysha.org** 🎉
