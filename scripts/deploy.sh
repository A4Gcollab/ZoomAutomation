#!/bin/bash

# ZOM Automation - Deployment Script
# Usage: sudo ./deploy.sh

set -e # Exit on error

echo "🚀 Starting Deployment..."

# 1. Update System
echo "📦 Updating System Packages..."
apt-get update && apt-get install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# 2. Setup Directories
APP_DIR="/opt/omysha-automation"
echo "📂 Setting up directory: $APP_DIR"
mkdir -p $APP_DIR

# 3. Python Env
echo "BS Creating Virtual Environment..."
if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv $APP_DIR/venv
fi
source $APP_DIR/venv/bin/activate
pip install -r $APP_DIR/requirements.txt

# 4. Backend Service
echo "⚙️  Configuring Backend Service..."
SERVICE_FILE="/etc/systemd/system/omysha-backend.service"
cat > $SERVICE_FILE <<EOL
[Unit]
Description=Omysha Zoom Backend
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/uvicorn src.api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl enable omysha-backend
systemctl restart omysha-backend

# 5. Frontend (Nginx)
echo "🌐 Configuring Nginx..."
NGINX_CONF="/etc/nginx/sites-available/za.omysha.org"
cat > $NGINX_CONF <<EOL
server {
    server_name za.omysha.org;
    root $APP_DIR/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL

# Link if not exists
if [ ! -L /etc/nginx/sites-enabled/za.omysha.org ]; then
    ln -s $NGINX_CONF /etc/nginx/sites-enabled/
fi

# Remove default if exists
rm -f /etc/nginx/sites-enabled/default

# Test and Restart Nginx
nginx -t
systemctl restart nginx

echo "✅ Deployment Config Complete!"
echo "👉 Action Required: Upload your .env file to $APP_DIR/.env"
echo "👉 Action Required: Run 'certbot --nginx -d za.omysha.org' for SSL"
