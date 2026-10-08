#!/bin/bash
# YTZ Automation Server Setup Script
# Run this on your fresh Ubuntu Server (GCE/DigitalOcean)
# Usage: sudo ./setup_server.sh

set -e

echo ">>> Updating System..."
apt-get update && apt-get upgrade -y

echo ">>> Installing Docker & Dependencies..."
apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up standard repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo ">>> Configuring Permissions..."
# Add current user to docker group (avoids sudo requirement for docker commands)
usermod -aG docker $USER

echo ">>> Verifying Installation..."
docker info > /dev/null
echo "Docker installed successfully!"

echo ">>> Setup Complete!"
echo "You can now upload your project files."
echo "Suggested Next Step: Log out and log back in for group changes to take effect."
