#!/bin/bash

# YTZ Automation - Complete Server Setup Script
# This script sets up a fresh Ubuntu/Debian server for YTZ Automation

set -e  # Exit on error

echo "=========================================="
echo "YTZ Automation - Server Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "Step 1: Updating system packages..."
apt-get update
apt-get upgrade -y

# Install system dependencies
echo ""
echo "Step 2: Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    nginx \
    git \
    curl \
    wget \
    certbot \
    python3-certbot-nginx \
    htop \
    ufw

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Node.js version is too old. Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

echo "   ✅ System dependencies installed"
echo "   - Python: $(python3 --version)"
echo "   - Node.js: $(node --version)"
echo "   - npm: $(npm --version)"

# Configure firewall
echo ""
echo "Step 3: Configuring firewall..."
ufw --force enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
echo "   ✅ Firewall configured"

# Create application user
echo ""
echo "Step 4: Creating application user..."
if ! id -u ytzuser > /dev/null 2>&1; then
    useradd -m -s /bin/bash ytzuser
    usermod -aG www-data ytzuser
    echo "   ✅ User 'ytzuser' created"
else
    echo "   ℹ️  User 'ytzuser' already exists"
fi

# Create application directory
echo ""
echo "Step 5: Setting up application directory..."
APP_DIR="/home/ytzuser/ytz-automation"
mkdir -p "$APP_DIR"
chown -R ytzuser:www-data "$APP_DIR"
echo "   ✅ Application directory: $APP_DIR"

echo ""
echo "=========================================="
echo "✅ Server Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps (run as ytzuser):"
echo "1. Clone repository: git clone <your-repo-url> $APP_DIR"
echo "2. Upload secrets to: $APP_DIR/secrets/"
echo "3. Create .env file in: $APP_DIR/"
echo "4. Run deployment script: cd $APP_DIR && bash deploy/deploy.sh"
echo ""
echo "To switch to ytzuser: sudo su - ytzuser"
echo ""
