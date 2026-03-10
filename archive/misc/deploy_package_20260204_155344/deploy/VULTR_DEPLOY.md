# YTZ Automation - Vultr Deployment Guide

## Quick Deploy

### Prerequisites
- SSH access to Vultr server (139.84.133.1)
- SSH key configured or root password

### Option 1: Automated Deployment (Recommended)

```bash
# From your local machine (Windows - use Git Bash or WSL)
cd "d:\VONG\YTZ Automation"
bash deploy/deploy-vultr.sh
```

This will:
1. Package all necessary files
2. Upload to Vultr server
3. Install dependencies
4. Build frontend
5. Setup systemd services
6. Configure nginx
7. Start all services

### Option 2: Manual Deployment

#### Step 1: Upload Files
```bash
# Create package
cd "d:\VONG\YTZ Automation"
tar -czf ytz-automation.tar.gz src frontend main.py requirements.txt .env secrets deploy

# Upload to server
scp ytz-automation.tar.gz root@139.84.133.1:/root/

# SSH into server
ssh root@139.84.133.1

# Extract
cd /root
tar -xzf ytz-automation.tar.gz
mv ytz-automation-* ytz-automation
cd ytz-automation
```

#### Step 2: Run Setup
```bash
bash deploy/vultr-setup.sh
```

## Verify Deployment

### Check Services
```bash
ssh root@139.84.133.1 'systemctl status ytz-api ytz-frontend'
```

### Check Logs
```bash
# Backend logs
ssh root@139.84.133.1 'journalctl -u ytz-api -f'

# Frontend logs
ssh root@139.84.133.1 'journalctl -u ytz-frontend -f'
```

### Test Endpoints
```bash
# Health check
curl http://139.84.133.1:8000/health

# Frontend
curl http://139.84.133.1:9002
```

## Access URLs

- **Frontend**: http://139.84.133.1:9002
- **Backend API**: http://139.84.133.1:8000
- **API Documentation**: http://139.84.133.1:8000/docs

## Troubleshooting

### Service not starting
```bash
# Check logs
journalctl -u ytz-api -n 50
journalctl -u ytz-frontend -n 50

# Restart services
systemctl restart ytz-api ytz-frontend nginx
```

### Port already in use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :9002

# Kill process if needed
kill -9 <PID>
```

### Update deployment
```bash
# On server
cd /root/ytz-automation
git pull  # if using git
systemctl restart ytz-api ytz-frontend
```
