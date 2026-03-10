# ✅ FINAL DEPLOYMENT CHECKLIST - za.omysha.org

## 🎯 Your VPS Details

**Domain**: `za.omysha.org`
**IP Address**: `72.61.234.87`
**DNS Status**: ✅ Configured and working

---

## 📋 Pre-Deployment Checklist

### Local Machine (Windows)
- [ ] All code is in: `D:\VONG\YTZ Automation`
- [ ] Secrets folder contains:
  - [ ] `client_secret.json` (YouTube OAuth)
  - [ ] `token.json` (YouTube token)
  - [ ] `token_drive.json` (Drive token)
  - [ ] `service_account.json` (Google Sheets)
- [ ] `.env` file has all environment variables
- [ ] `config/playlists.json` has all Drive folder IDs

### VPS Access
- [ ] Can connect: `ssh root@72.61.234.87`
- [ ] Have root password from Hostinger panel

---

## 🚀 DEPLOYMENT STEPS (Copy-Paste Ready)

### STEP 1: Connect to VPS
```bash
ssh root@72.61.234.87
```
**Enter password from Hostinger panel when prompted**

### STEP 2: Update System
```bash
apt update && apt upgrade -y
```

### STEP 3: Install Software
```bash
# Install Python
apt install -y python3 python3-pip python3-venv

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Nginx
apt install -y nginx

# Install Certbot
apt install -y certbot python3-certbot-nginx

# Install Git
apt install -y git
```

### STEP 4: Create App User
```bash
useradd -m -s /bin/bash ytzapp
usermod -aG sudo ytzapp
passwd ytzapp
# Set password: ytz2026secure (or your choice)
```

### STEP 5: Switch to App User
```bash
su - ytzapp
cd ~
```

### STEP 6: Upload Files

**Option A: Using Git** (Recommended)
```bash
# On VPS (as ytzapp)
git clone https://github.com/yourusername/ytz-automation.git
cd ytz-automation
```

**Option B: Using SCP** (From your Windows machine)
```powershell
# Open PowerShell on Windows
scp -r "D:\VONG\YTZ Automation" ytzapp@72.61.234.87:/home/ytzapp/
```

### STEP 7: Upload Secrets (From Windows)
```powershell
# On your Windows machine (PowerShell)
scp -r "D:\VONG\YTZ Automation\secrets" ytzapp@72.61.234.87:/home/ytzapp/ytz-automation/
scp "D:\VONG\YTZ Automation\.env" ytzapp@72.61.234.87:/home/ytzapp/ytz-automation/
```

### STEP 8: Install Dependencies (On VPS)
```bash
cd /home/ytzapp/ytz-automation

# Python
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Node.js
cd frontend
npm install
npm run build
cd ..
```

### STEP 9: Create Systemd Service
```bash
sudo nano /etc/systemd/system/ytz-backend.service
```

**Paste this**:
```ini
[Unit]
Description=YTZ Automation Backend
After=network.target

[Service]
Type=simple
User=ytzapp
WorkingDirectory=/home/ytzapp/ytz-automation
Environment="PATH=/home/ytzapp/ytz-automation/venv/bin"
ExecStart=/home/ytzapp/ytz-automation/venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save**: `Ctrl+X`, `Y`, `Enter`

**Enable service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ytz-backend
sudo systemctl start ytz-backend
sudo systemctl status ytz-backend
```

### STEP 10: Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/ytz-automation
```

**Paste this**:
```nginx
server {
    listen 80;
    server_name za.omysha.org;

    location / {
        root /home/ytzapp/ytz-automation/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }

    client_max_body_size 5G;
}
```

**Save**: `Ctrl+X`, `Y`, `Enter`

**Enable site**:
```bash
sudo ln -s /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### STEP 11: Install SSL
```bash
sudo certbot --nginx -d za.omysha.org
```
**Follow prompts**:
- Enter email
- Agree to terms
- Choose option 2 (redirect HTTP to HTTPS)

### STEP 12: Configure Firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### STEP 13: Verify
```bash
# Check backend
curl http://localhost:8000/health

# Check logs
sudo journalctl -u ytz-backend -f
```

**Open browser**: `https://za.omysha.org`

---

## ✅ Post-Deployment Verification

- [ ] `https://za.omysha.org` loads
- [ ] SSL certificate is valid (green lock)
- [ ] Can log in with Google
- [ ] Dashboard shows recordings
- [ ] Backend logs show no errors
- [ ] Zoom scanning is active

---

## 🔧 Useful Commands

### View Backend Logs
```bash
sudo journalctl -u ytz-backend -f
```

### Restart Backend
```bash
sudo systemctl restart ytz-backend
```

### Check Service Status
```bash
sudo systemctl status ytz-backend
sudo systemctl status nginx
```

### Monitor Downloads
```bash
watch -n 2 'ls -lh /home/ytzapp/ytz-automation/downloads/'
```

### Check Disk Space
```bash
df -h
```

---

## 🆘 Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u ytz-backend -n 100

# Common fixes:
# 1. Check secrets exist
ls -la /home/ytzapp/ytz-automation/secrets/

# 2. Check .env exists
cat /home/ytzapp/ytz-automation/.env

# 3. Restart service
sudo systemctl restart ytz-backend
```

### 502 Bad Gateway
```bash
# Backend is not running
sudo systemctl status ytz-backend
sudo systemctl start ytz-backend
```

### SSL fails
```bash
# Check DNS
nslookup za.omysha.org

# Try again
sudo certbot --nginx -d za.omysha.org
```

---

## 📞 Quick Reference

**VPS IP**: `72.61.234.87`
**Domain**: `za.omysha.org`
**SSH**: `ssh ytzapp@72.61.234.87`
**App Dir**: `/home/ytzapp/ytz-automation`
**Logs**: `sudo journalctl -u ytz-backend -f`

---

## 🎉 Success Criteria

When deployment is successful, you should see:

1. ✅ `https://za.omysha.org` loads with valid SSL
2. ✅ Login with Google works
3. ✅ Dashboard shows 25 pending recordings
4. ✅ Backend logs show "Scanning Zoom..."
5. ✅ No errors in logs
6. ✅ System auto-refreshes API tokens

**Your system is now live and will run 24/7!**

---

## 📚 Documentation Reference

- **Complete Guide**: `HOSTINGER_DEPLOYMENT.md`
- **API Tokens**: `API_TOKEN_REFRESH.md`
- **File Structure**: `DOWNLOADS_AND_GITHUB.md`
- **Troubleshooting**: `DEPLOYMENT_GUIDE.md`
