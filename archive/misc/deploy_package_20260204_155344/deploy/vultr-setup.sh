#!/bin/bash

# Vultr Server Setup Script
# Run this ON the Vultr server after uploading files

set -e

echo "=========================================="
echo "Setting up YTZ Automation on Vultr"
echo "=========================================="
echo ""

# Update system
echo "Step 1: Updating system..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo ""
echo "Step 2: Installing dependencies..."
apt-get install -y python3 python3-pip python3-venv nodejs npm nginx git curl

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

echo "  ✅ Dependencies installed"
echo "  - Python: $(python3 --version)"
echo "  - Node.js: $(node --version)"

# Setup Python virtual environment
echo ""
echo "Step 3: Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "  ✅ Python environment ready"

# Setup Frontend
echo ""
echo "Step 4: Setting up frontend..."
cd frontend
npm install
npm run build
cd ..
echo "  ✅ Frontend built"

# Create systemd service for backend
echo ""
echo "Step 5: Creating backend service..."
cat > /etc/systemd/system/ytz-api.service << 'EOF'
[Unit]
Description=YTZ Automation API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ytz-automation
Environment="PATH=/root/ytz-automation/venv/bin"
ExecStart=/root/ytz-automation/venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for frontend
echo ""
echo "Step 6: Creating frontend service..."
cat > /etc/systemd/system/ytz-frontend.service << 'EOF'
[Unit]
Description=YTZ Automation Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ytz-automation/frontend
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx
echo ""
echo "Step 7: Configuring nginx..."
cat > /etc/nginx/sites-available/ytz-automation << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://localhost:9002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# Start services
echo ""
echo "Step 8: Starting services..."
systemctl daemon-reload
systemctl enable ytz-api ytz-frontend nginx
systemctl restart ytz-api ytz-frontend nginx

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Services status:"
systemctl status ytz-api --no-pager -l || true
systemctl status ytz-frontend --no-pager -l || true
echo ""
echo "Access your application at:"
echo "  http://$(curl -s ifconfig.me)"
echo ""
