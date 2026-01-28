# 🚀 Zoom Automation: Production Deployment Guide

This guide explains how to host the **Zoom Automation** system (Backend + Web Dashboard) on your VPS.

## 1. Prerequisites
- **Server**: Vultr or Hostinger (Ubuntu/Debian recommended).
- **Domain**: `za.omysha.org` (Pointed to Server IP).
- **Tools**: Git, Docker, or Python+Node (Manual Setup).

## 2. Configuration (`.env`)
Ensure your server `.env` matches your local config, plus these:
```env
# Production Settings
TZ=Asia/Kolkata
# API Key for Manual Sync (Optional but recommended)
API_SECRET_KEY=your_secret_key
```

## 3. Backend Deployment (Systemd)
We will run the backend as a service.

1.  **Install Config**:
    ```bash
    cd /opt/omysha-automation
    pip install -r requirements.txt
    ```

2.  **Create Service**: `/etc/systemd/system/omysha-backend.service`
    ```ini
    [Unit]
    Description=Omysha Zoom Backend
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/opt/omysha-automation
    ExecStart=/usr/local/bin/uvicorn src.api:app --host 0.0.0.0 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

3.  **Start**: `systemctl enable --now omysha-backend`

## 4. Frontend Deployment (Nginx)
We will serve the compiled React app via Nginx and proxy API calls.

1.  **Build Frontend** (Run locally or on server):
    ```bash
    cd frontend
    npm install
    npm run build
    # Output is in dist/ folder
    ```

2.  **Nginx Config**: `/etc/nginx/sites-available/za.omysha.org`
    ```nginx
    server {
        server_name za.omysha.org;
        root /opt/omysha-automation/frontend/dist;
        index index.html;

        # Frontend (SPA Support)
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Backend Proxy
        location /api/ {
            proxy_pass http://localhost:8000/; # Note trailing slash
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    ```

3.  **SSL**: `certbot --nginx -d za.omysha.org`

## 5. Verification
- Open `https://za.omysha.org`
- **Manual Mode**: The system will NOT run automatically.
- Click **"Sync"** in the UI to trigger the Zoom Scan & Auto-Mapping.
