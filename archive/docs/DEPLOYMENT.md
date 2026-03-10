# YTZ Automation - Production Deployment Guide

## Prerequisites

1. **VPS Server** (Ubuntu 20.04 or later)
   - Minimum 2GB RAM
   - 20GB disk space
   - Public IP address

2. **Domain Name** (optional but recommended)
   - Point your domain's A record to your server's IP

3. **Google OAuth Credentials**
   - Web application client ID for frontend login
   - Service account for Sheets/Drive access

## Quick Deployment

### Option 1: Automated Deployment (Recommended)

```bash
# 1. Clone the repository on your VPS
git clone https://github.com/A4Gcollab/ZoomAutomation.git
cd ZoomAutomation

# 2. Make deployment script executable
chmod +x deploy.sh

# 3. Edit the script to set your domain
nano deploy.sh
# Change: DOMAIN="your-domain.com"

# 4. Run the deployment script
./deploy.sh
```

### Option 2: Manual Deployment

#### Step 1: Install Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python
sudo apt-get install -y python3 python3-pip python3-venv

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Nginx
sudo apt-get install -y nginx

# Install Git
sudo apt-get install -y git
```

#### Step 2: Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/ytz-automation
sudo chown -R $USER:$USER /opt/ytz-automation

# Clone repository
git clone https://github.com/A4Gcollab/ZoomAutomation.git /opt/ytz-automation
cd /opt/ytz-automation

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.production.example .env.production

# Edit configuration
nano .env.production
# Fill in your Google OAuth credentials, Zoom API keys, etc.
```

#### Step 4: Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

#### Step 5: Create Systemd Service

```bash
sudo nano /etc/systemd/system/ytz-automation.service
```

Paste this content:

```ini
[Unit]
Description=YTZ Automation Backend
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/ytz-automation
Environment="PATH=/opt/ytz-automation/venv/bin"
ExecStart=/opt/ytz-automation/venv/bin/uvicorn src.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual username.

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ytz-automation
sudo systemctl start ytz-automation

# Check status
sudo systemctl status ytz-automation
```

#### Step 6: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/ytz-automation
```

Paste this content (replace `your-domain.com` with your actual domain):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (static files)
    location / {
        root /opt/ytz-automation/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

#### Step 7: Setup SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

## Post-Deployment

### Verify Installation

1. **Check Backend**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

2. **Check Frontend**
   - Open your browser to `http://your-domain.com`
   - You should see the login page

3. **Check Logs**
   ```bash
   # Backend logs
   sudo journalctl -u ytz-automation -f
   
   # Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

### Useful Commands

```bash
# Restart backend
sudo systemctl restart ytz-automation

# View backend status
sudo systemctl status ytz-automation

# View backend logs
sudo journalctl -u ytz-automation -f

# Restart Nginx
sudo systemctl restart nginx

# Update application
cd /opt/ytz-automation
git pull
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart ytz-automation
```

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u ytz-automation -n 50

# Common issues:
# - Missing credentials files
# - Wrong file permissions
# - Port 8000 already in use
```

### Frontend shows blank page

```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Rebuild frontend
cd /opt/ytz-automation/frontend
npm run build

# Check file permissions
ls -la /opt/ytz-automation/frontend/dist
```

### Login doesn't work

1. Check Google OAuth configuration:
   - Authorized JavaScript origins: `https://your-domain.com`
   - Authorized redirect URIs: `https://your-domain.com`

2. Check browser console for errors

3. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

### Service control buttons don't work

- This is expected in production. The in-process service management is designed for development.
- In production, use systemd commands:
  ```bash
  sudo systemctl start ytz-automation
  sudo systemctl stop ytz-automation
  sudo systemctl restart ytz-automation
  ```

## Security Recommendations

1. **Firewall**
   ```bash
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

2. **Secure Credentials**
   - Never commit credentials to git
   - Use environment variables or secure files
   - Restrict file permissions:
     ```bash
     chmod 600 .env.production
     chmod 600 credentials/*
     ```

3. **Regular Updates**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade -y
   ```

4. **Backup**
   - Backup `data/app.db` regularly
   - Backup credentials files
   - Consider automated backups

## Support

For issues or questions:
- Check logs first
- Review this guide
- Check GitHub issues: https://github.com/A4Gcollab/ZoomAutomation/issues
