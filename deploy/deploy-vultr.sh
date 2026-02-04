#!/bin/bash

# YTZ Automation - Quick Deploy to Vultr
# This script deploys the application to your Vultr server at 139.84.133.1

set -e

SERVER_IP="139.84.133.1"
SERVER_USER="root"
APP_DIR="/root/ytz-automation"

echo "=========================================="
echo "YTZ Automation - Vultr Deployment"
echo "Server: $SERVER_IP"
echo "=========================================="
echo ""

# Step 1: Create deployment package
echo "Step 1: Creating deployment package..."
cd "$(dirname "$0")/.."

# Create temp directory for deployment
DEPLOY_DIR="deploy_package_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

# Copy necessary files
echo "  - Copying backend files..."
cp -r src "$DEPLOY_DIR/"
cp -r secrets "$DEPLOY_DIR/" 2>/dev/null || echo "  ⚠️  No secrets directory found"
cp main.py "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp .env "$DEPLOY_DIR/" 2>/dev/null || echo "  ⚠️  No .env file found"

echo "  - Copying frontend files..."
cp -r frontend "$DEPLOY_DIR/"

echo "  - Copying deployment scripts..."
cp -r deploy "$DEPLOY_DIR/"

echo "  ✅ Deployment package created: $DEPLOY_DIR"

# Step 2: Upload to server
echo ""
echo "Step 2: Uploading to Vultr server..."
ssh $SERVER_USER@$SERVER_IP "mkdir -p $APP_DIR"
rsync -avz --progress "$DEPLOY_DIR/" $SERVER_USER@$SERVER_IP:$APP_DIR/

echo "  ✅ Files uploaded"

# Step 3: Run setup on server
echo ""
echo "Step 3: Running setup on server..."
ssh $SERVER_USER@$SERVER_IP "cd $APP_DIR && bash deploy/vultr-setup.sh"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Your application is now running at:"
echo "  - Frontend: http://$SERVER_IP:9002"
echo "  - Backend API: http://$SERVER_IP:8000"
echo "  - API Docs: http://$SERVER_IP:8000/docs"
echo ""
echo "To check status:"
echo "  ssh $SERVER_USER@$SERVER_IP 'systemctl status ytz-api ytz-frontend'"
echo ""
