# 🚀 Zoom Automation: Vultr Deployment Guide

This guide is specifically tailored for **Vultr** to ensure you choose the exact right options to get the automation running smoothly.

## Phase 1: Deploying the Server on Vultr

1.  **Log in** to your [Vultr Dashboard](https://my.vultr.com/).
2.  Click the blue **+ (Plus)** button and select **Deploy New Server**.
3.  **Choose Server**:
    *   Select **Cloud Compute - Shared CPU**.
4.  **CPU & Storage Technology**:
    *   Select **AMD High Performance** or **Intel High Performance** (Standard is also fine, but High Perf is faster for builds).
5.  **Server Location**:
    *   Choose the location closest to you (e.g., **Bangalore**, **Mumbai**, or **Singapore**).
6.  **Server Image** (CRITICAL):
    *   Click the **Operating System** tab.
    *   Select **Ubuntu**.
    *   Select **22.04 LTS x64** (Do NOT choose 24.04 as it has some python changes that can be tricky).
7.  **Server Size**:
    *   **Recommended**: **50 GB NVMe / 2 GB Memory** (~$12/month).
    *   *Minimum*: The $6/month (1GB RAM) plan *can* work, but building the Frontend might crash due to low memory. 2GB is safe.
8.  **Add Auto Backups**: Optional (Turn off to save money).
9.  **SSH Keys**:
    *   If you know how to use SSH keys, add yours.
    *   If not, just skip this; Vultr will generate a **root password** for you.
10. **Hostname & Label**:
    *   Enter `omysha-automation` for both.
11. Click **Deploy Now**.

## Phase 2: Domain Setup (DNS)

While the server is installing (takes ~2 minutes):

1.  Copy your new **IP Address** from the Vultr dashboard (e.g., `45.12.34.56`).
2.  Go to your Domain Registrar (Godaddy, Namecheap, Cloudflare, etc.).
3.  Add an **A Record**:
    *   **Name/Host**: `za` (This creates `za.omysha.org`)
    *   **Value/Target**: `YOUR_VULTR_IP_ADDRESS`
    *   **TTL**: Automatic or 1 Hour.

## Phase 3: The Deployment (Terminal)

You will need a terminal to send the commands. You can use **Putty** (Windows), **PowerShell**, or the **Vultr Web Console** (top right of server details page > View Console).

### 1. Connect to Server
Open PowerShell on your computer:
```powershell
ssh root@YOUR_SERVER_IP
# Type 'yes' to trust the fingerprint.
# Paste the password (hidden when pasting) from Vultr dashboard.
```

### 2. Run the Auto-Installer
I have updated the deployment script to handle everything (Node.js, Frontend Build, Python env). Just copy-paste this **ENTIRE** block:

```bash
cd /opt
# Remove old folder if it exists to be safe
rm -rf omysha-automation
# Clone the repo
git clone https://github.com/A4Gcollab/ZoomAutomation omysha-automation
# Run the deployment script
cd omysha-automation && chmod +x scripts/deploy.sh && ./scripts/deploy.sh
```

**☕ Grab a coffee.** This will take about 5-8 minutes. It will:
1.  Install Python & System Utilities.
2.  Install Node.js v20.
3.  Install Project Dependencies.
4.  **Build the Frontend Website** (This takes the longest).
5.  Configure Nginx & Systemd.

### 3. Configure Secrets (.env)
Once the script says `✅ Deployment Config Complete!`, you need to add your secrets.

1.  Open the editor:
    ```bash
    nano .env
    ```
2.  **Paste** your exact `.env` content from your local computer.
    *   *Tip*: In Putty/PowerShell, right-click usually pastes.
3.  **Save & Exit**:
    *   Press `Ctrl + O`, then `Enter` (to write file).
    *   Press `Ctrl + X` (to exit).

### 4. Setup SSL (HTTPS)
Secure your site so you can log in with Google.
```bash
certbot --nginx -d za.omysha.org
```
*   Enter your email if asked.
*   Agree to terms (`Y`).
*   If asked to Redirect, choose **2** (Redirect).

### 5. Final Restart
Ensure everything is up with the new config:
```bash
systemctl restart omysha-backend
systemctl restart nginx
```

## Phase 4: Validation

1.  Go to `https://za.omysha.org`.
2.  You should see your login page.
3.  **Log in** and check if it syncs.

---

### Troubleshooting
*   **502 Bad Gateway**: The backend isn't running. Check logs:
    ```bash
    journalctl -u omysha-backend -f
    ```
*   **Permission Denied**: Run `chown -R www-data:www-data /opt/omysha-automation/frontend/dist`
