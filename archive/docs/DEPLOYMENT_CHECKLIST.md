# YTZ Automation - Deployment Checklist

## Pre-Deployment Preparation

### Local Environment
- [ ] All code changes committed to Git
- [ ] All tests passing locally
- [ ] Backend runs without errors: `python main.py --once`
- [ ] Frontend builds successfully: `cd frontend && npm run build`
- [ ] API endpoints tested: `python scripts/test_api.py`

### Secrets & Credentials
- [ ] `secrets/client_secret.json` - YouTube OAuth credentials
- [ ] `secrets/token.json` - YouTube access token
- [ ] `secrets/token_drive.json` - Google Drive access token  
- [ ] `secrets/service_account.json` - Google Sheets service account
- [ ] All secrets backed up securely

### Environment Configuration
- [ ] `.env` file created with all required variables
- [ ] `DRIVE_ROOT_FOLDER_ID` configured
- [ ] `GOOGLE_SHEET_ID` configured
- [ ] `ADMIN_EMAILS` configured
- [ ] Zoom credentials configured (ZOOM_1_*)
- [ ] Firebase credentials configured

---

## Server Setup

### Initial Server Access
- [ ] SSH access confirmed: `ssh user@server-ip`
- [ ] Server meets minimum requirements:
  - [ ] Ubuntu 20.04+ or Debian 11+
  - [ ] 2GB+ RAM
  - [ ] 20GB+ free disk space
  - [ ] Root/sudo access

### System Dependencies
- [ ] Run server setup script: `sudo bash deploy/setup-server.sh`
- [ ] Verify Python 3.8+: `python3 --version`
- [ ] Verify Node.js 18+: `node --version`
- [ ] Verify Nginx installed: `nginx -v`
- [ ] Firewall configured (ports 22, 80, 443 open)

---

## Application Deployment

### Code Deployment
- [ ] Clone repository to server
  ```bash
  git clone <your-repo-url> /home/ytzuser/ytz-automation
  cd /home/ytzuser/ytz-automation
  ```
- [ ] Upload secrets to server
  ```bash
  scp -r secrets/* user@server:/home/ytzuser/ytz-automation/secrets/
  ```
- [ ] Upload .env file to server
  ```bash
  scp .env user@server:/home/ytzuser/ytz-automation/
  ```
- [ ] Set correct permissions
  ```bash
  chmod 600 secrets/*
  chmod 600 .env
  ```

### Backend Setup
- [ ] Create Python virtual environment
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- [ ] Install Python dependencies
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Test backend configuration
  ```bash
  python -c "from src.config import check_config; check_config()"
  ```
- [ ] Test database initialization
  ```bash
  python -c "from src.db_sql import db; print('DB OK')"
  ```

### Frontend Setup
- [ ] Install Node dependencies
  ```bash
  cd frontend
  npm install
  ```
- [ ] Create production .env.local
  ```bash
  # Update NEXT_PUBLIC_API_BASE_URL to production URL
  nano .env.local
  ```
- [ ] Build frontend
  ```bash
  npm run build
  ```
- [ ] Verify build output exists
  ```bash
  ls -la .next/standalone
  ```

---

## Service Configuration

### Systemd Services
- [ ] Install automation service
  ```bash
  sudo cp deploy/ytz-automation.service /etc/systemd/system/
  sudo sed -i 's|/home/user/ytz-automation|/home/ytzuser/ytz-automation|g' /etc/systemd/system/ytz-automation.service
  ```
- [ ] Install API service
  ```bash
  sudo cp deploy/ytz-api.service /etc/systemd/system/
  sudo sed -i 's|/home/user/ytz-automation|/home/ytzuser/ytz-automation|g' /etc/systemd/system/ytz-api.service
  ```
- [ ] Reload systemd
  ```bash
  sudo systemctl daemon-reload
  ```
- [ ] Enable services
  ```bash
  sudo systemctl enable ytz-automation
  sudo systemctl enable ytz-api
  ```
- [ ] Start services
  ```bash
  sudo systemctl start ytz-automation
  sudo systemctl start ytz-api
  ```

### Nginx Configuration
- [ ] Update nginx config with domain/IP
  ```bash
  sudo cp deploy/nginx.conf /etc/nginx/sites-available/ytz-automation
  sudo sed -i 's|yourdomain.com|your-actual-domain.com|g' /etc/nginx/sites-available/ytz-automation
  sudo sed -i 's|/home/user/ytz-automation|/home/ytzuser/ytz-automation|g' /etc/nginx/sites-available/ytz-automation
  ```
- [ ] Enable site
  ```bash
  sudo ln -sf /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
  ```
- [ ] Test nginx configuration
  ```bash
  sudo nginx -t
  ```
- [ ] Restart nginx
  ```bash
  sudo systemctl restart nginx
  ```

### SSL Certificate (Optional but Recommended)
- [ ] Install SSL certificate with Let's Encrypt
  ```bash
  sudo certbot --nginx -d your-domain.com
  ```
- [ ] Verify auto-renewal
  ```bash
  sudo certbot renew --dry-run
  ```

---

## Verification

### Service Status
- [ ] Check automation service
  ```bash
  sudo systemctl status ytz-automation
  ```
- [ ] Check API service
  ```bash
  sudo systemctl status ytz-api
  ```
- [ ] Check nginx service
  ```bash
  sudo systemctl status nginx
  ```

### Log Verification
- [ ] View automation logs
  ```bash
  sudo journalctl -u ytz-automation -f
  ```
- [ ] View API logs
  ```bash
  sudo journalctl -u ytz-api -f
  ```
- [ ] Check for errors
  ```bash
  sudo journalctl -u ytz-automation --since "10 minutes ago" | grep ERROR
  sudo journalctl -u ytz-api --since "10 minutes ago" | grep ERROR
  ```

### API Endpoint Tests
- [ ] Health check
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Detailed health
  ```bash
  curl http://localhost:8000/health/detailed
  ```
- [ ] Frontend access
  ```bash
  curl http://localhost/ | grep "YTZ"
  ```

### External Access
- [ ] Frontend loads in browser: `http://your-domain.com`
- [ ] Login works with Google OAuth
- [ ] Dashboard displays correctly
- [ ] API endpoints accessible from frontend

---

## End-to-End Testing

### Workflow Test
- [ ] Login to frontend dashboard
- [ ] Verify "Pending Queue" tab shows recordings
- [ ] Approve a test recording
- [ ] Monitor backend logs for processing
- [ ] Verify YouTube upload completes
- [ ] Verify Google Drive upload completes
- [ ] Check Google Sheets for log entry
- [ ] Verify recording appears in "Completed History"

### Error Handling Test
- [ ] Test with invalid recording (should fail gracefully)
- [ ] Check error logs
- [ ] Verify error notification sent

---

## Post-Deployment

### Monitoring Setup
- [ ] Set up log monitoring
  ```bash
  # Add to crontab for daily log summary
  0 9 * * * journalctl -u ytz-automation --since "24 hours ago" | grep ERROR | mail -s "YTZ Errors" admin@example.com
  ```
- [ ] Set up disk space monitoring
  ```bash
  # Add to crontab for disk space check
  0 */6 * * * df -h /home/ytzuser/ytz-automation/downloads | mail -s "YTZ Disk Usage" admin@example.com
  ```

### Backup Setup
- [ ] Create backup script for database
  ```bash
  # Add to crontab for daily backup
  0 2 * * * cp /home/ytzuser/ytz-automation/data/vong_v2.db /home/ytzuser/backups/vong_v2_$(date +\%Y\%m\%d).db
  ```
- [ ] Test backup restoration

### Documentation
- [ ] Document server access details
- [ ] Document admin credentials
- [ ] Document troubleshooting procedures
- [ ] Share with team

---

## Rollback Procedure

If deployment fails:

1. **Stop services**
   ```bash
   sudo systemctl stop ytz-automation
   sudo systemctl stop ytz-api
   ```

2. **Restore previous version**
   ```bash
   cd /home/ytzuser/ytz-automation
   git reset --hard <previous-commit>
   ```

3. **Rebuild**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   cd frontend && npm install && npm run build
   ```

4. **Restart services**
   ```bash
   sudo systemctl start ytz-automation
   sudo systemctl start ytz-api
   ```

5. **Verify**
   ```bash
   curl http://localhost:8000/health
   ```

---

## Common Issues

### Service won't start
- Check logs: `sudo journalctl -u ytz-automation -n 50`
- Verify .env file exists and has correct permissions
- Verify secrets directory has all required files
- Check Python virtual environment is activated

### Frontend not loading
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Verify frontend build completed: `ls frontend/.next/standalone`
- Check nginx configuration: `sudo nginx -t`

### API not responding
- Check if API service is running: `sudo systemctl status ytz-api`
- Check API logs: `sudo journalctl -u ytz-api -f`
- Verify port 8000 is not blocked: `sudo netstat -tlnp | grep 8000`

### Database errors
- Check database file exists: `ls data/vong_v2.db`
- Check permissions: `ls -la data/`
- Reinitialize if needed: `rm data/vong_v2.db && python -c "from src.db_sql import db"`

---

## Success Criteria

✅ All services running without errors
✅ Frontend accessible and login works
✅ Backend processing recordings successfully
✅ YouTube uploads working
✅ Google Drive uploads working
✅ Google Sheets logging working
✅ No errors in logs for 1 hour
✅ End-to-end workflow tested successfully

---

## Deployment Complete! 🎉

Your YTZ Automation system is now running in production.

**Next Steps:**
- Monitor logs for first 24 hours
- Test with real Zoom recordings
- Set up automated backups
- Configure monitoring alerts
