#!/bin/bash

# YTZ Automation - Production Deployment Script
# This script sets up the application on a VPS with Nginx and systemd

set -e  # Exit on any error

echo "🚀 YTZ Automation - Production Deployment"
echo "=========================================="

# Configuration
APP_DIR="/opt/ytz-automation"
DOMAIN="your-domain.com"  # Change this to your domain
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Installing system dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx git curl

# Install Node.js 18.x
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo -e "${GREEN}✓ System dependencies installed${NC}"

echo -e "${YELLOW}Step 2: Setting up application directory...${NC}"
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Copy application files (assumes you're running this from the repo)
echo -e "${YELLOW}Step 3: Copying application files...${NC}"
cp -r . $APP_DIR/
cd $APP_DIR

echo -e "${GREEN}✓ Application files copied${NC}"

echo -e "${YELLOW}Step 4: Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Python environment ready${NC}"

echo -e "${YELLOW}Step 5: Building frontend...${NC}"
cd frontend
npm install
npm run build
cd ..

echo -e "${GREEN}✓ Frontend built${NC}"

echo -e "${YELLOW}Step 6: Creating systemd service...${NC}"
sudo tee /etc/systemd/system/ytz-automation.service > /dev/null <<EOF
[Unit]
Description=YTZ Automation Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn src.api:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ytz-automation
sudo systemctl start ytz-automation

echo -e "${GREEN}✓ Backend service created and started${NC}"

echo -e "${YELLOW}Step 7: Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/ytz-automation > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Frontend (static files)
    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        rewrite ^/api/(.*) /\$1 break;
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:$BACKEND_PORT/health;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx configured${NC}"

echo -e "${YELLOW}Step 8: Setting up SSL with Let's Encrypt (optional)...${NC}"
echo -e "${YELLOW}To enable HTTPS, run:${NC}"
echo -e "  sudo apt-get install certbot python3-certbot-nginx"
echo -e "  sudo certbot --nginx -d $DOMAIN"

echo ""
echo -e "${GREEN}=========================================="
echo -e "✅ Deployment Complete!"
echo -e "==========================================${NC}"
echo ""
echo -e "Your application is now running at:"
echo -e "  ${GREEN}http://$DOMAIN${NC}"
echo ""
echo -e "Useful commands:"
echo -e "  ${YELLOW}Check backend status:${NC}  sudo systemctl status ytz-automation"
echo -e "  ${YELLOW}View backend logs:${NC}     sudo journalctl -u ytz-automation -f"
echo -e "  ${YELLOW}Restart backend:${NC}       sudo systemctl restart ytz-automation"
echo -e "  ${YELLOW}Check nginx status:${NC}    sudo systemctl status nginx"
echo -e "  ${YELLOW}View nginx logs:${NC}       sudo tail -f /var/log/nginx/error.log"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Update DOMAIN in this script to your actual domain"
echo -e "  2. Configure your DNS to point to this server"
echo -e "  3. Set up SSL with certbot (see command above)"
echo -e "  4. Update src/config.py with production settings"
echo ""
