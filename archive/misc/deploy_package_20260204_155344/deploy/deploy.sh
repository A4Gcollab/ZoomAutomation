#!/bin/bash

# YTZ Automation - Quick Deploy Script
# Run this on your server after cloning the repository

set -e  # Exit on error

echo "=========================================="
echo "YTZ Automation - Quick Deploy"
echo "=========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Please do not run as root. Run as your regular user."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Application directory: $APP_DIR"
cd "$APP_DIR"

# Step 1: Create runtime directories
echo ""
echo "Step 1: Creating runtime directories..."
mkdir -p downloads data secrets

# Step 2: Check for secrets
echo ""
echo "Step 2: Checking for secrets..."
if [ ! -f "secrets/client_secret.json" ]; then
    echo "⚠️  WARNING: secrets/client_secret.json not found"
    echo "   Please upload your API credentials to the secrets/ folder"
fi

if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found"
    echo "   Please create .env file with your environment variables"
fi

# Step 3: Install Python dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Install Node dependencies and build frontend
echo ""
echo "Step 4: Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Step 5: Setup systemd service
echo ""
echo "Step 5: Setting up systemd service..."
echo "   This requires sudo access..."

# Update paths in service file
sed "s|/home/user/ytz-automation|$APP_DIR|g" deploy/ytz-backend.service > /tmp/ytz-backend.service

sudo cp /tmp/ytz-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ytz-backend
sudo systemctl restart ytz-backend

echo "   ✅ Backend service installed and started"

# Step 6: Setup nginx
echo ""
echo "Step 6: Setting up nginx..."
read -p "Enter your domain name (e.g., ytz.example.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "   ⚠️  No domain provided, skipping nginx setup"
else
    # Update paths and domain in nginx config
    sed "s|/home/user/ytz-automation|$APP_DIR|g; s|yourdomain.com|$DOMAIN|g" deploy/nginx.conf > /tmp/ytz-automation.nginx

    sudo cp /tmp/ytz-automation.nginx /etc/nginx/sites-available/ytz-automation
    sudo ln -sf /etc/nginx/sites-available/ytz-automation /etc/nginx/sites-enabled/
    
    # Test nginx config
    if sudo nginx -t; then
        sudo systemctl restart nginx
        echo "   ✅ Nginx configured and restarted"
    else
        echo "   ❌ Nginx configuration test failed"
        exit 1
    fi
    
    # Step 7: Setup SSL
    echo ""
    echo "Step 7: Setting up SSL certificate..."
    read -p "Install SSL certificate with Let's Encrypt? (y/n): " INSTALL_SSL
    
    if [ "$INSTALL_SSL" = "y" ]; then
        sudo certbot --nginx -d $DOMAIN
        echo "   ✅ SSL certificate installed"
    fi
fi

# Step 8: Final checks
echo ""
echo "Step 8: Running final checks..."

# Check if service is running
if sudo systemctl is-active --quiet ytz-backend; then
    echo "   ✅ Backend service is running"
else
    echo "   ❌ Backend service is not running"
    echo "   Check logs with: sudo journalctl -u ytz-backend -f"
fi

# Check if nginx is running
if sudo systemctl is-active --quiet nginx; then
    echo "   ✅ Nginx is running"
else
    echo "   ❌ Nginx is not running"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload your API credentials to: $APP_DIR/secrets/"
echo "2. Create .env file with environment variables"
echo "3. Restart backend: sudo systemctl restart ytz-backend"
echo "4. Check logs: sudo journalctl -u ytz-backend -f"
echo ""
if [ ! -z "$DOMAIN" ]; then
    echo "Your application should be available at: https://$DOMAIN"
else
    echo "Your application should be available at: http://your-server-ip"
fi
echo ""
