# 🚀 Zoom Automation: Hostinger Deployment Guide

This guide takes you from "Zero" to "Live" on Hostinger VPS in about 15 minutes.

## Phase 1: Create the Server (Hostinger)

1.  **Account**: Log in to [hpanel.hostinger.com](https://hpanel.hostinger.com/).
2.  **Order VPS**:
    *   Go to **VPS** -> **Create New**.
    *   **Choose Plan**: **KVM 2** (Recommended).
        *   *Why?* It has 2 vCPU / 8 GB RAM. The "KVM 1" (4GB) is also okay, but KVM 2 is safer for video processing.
    *   **Location**: Choose closest to you (e.g., Singapore, Mumbai, USA).
3.  **OS Setup**:
    *   When asked for "Operating System", select **Application** -> **Ubuntu 22.04**.
    *   **Password**: Set a strong root password (you will need this!).
4.  **Wait**: It takes about 5 minutes to provision.
5.  **Get IP**: On the Dashboard, copy your **SSH IP** (e.g., `192.168.1.5`).

## Phase 2: Domain Setup (DNS)

1.  Go to your Domain DNS settings.
2.  Add a new **A Record**:
    *   **Host**: `za` (This makes it `za.omysha.org`)
    *   **Value**: `YOUR_HOSTINGER_IP`
    *   **TTL**: `Automatic` or `3600`.

## Phase 3: The Deployment (Terminal)

Open your **local** terminal (PowerShell) or use the Hostinger "Browser Terminal".

### 1. Push Latest Code
Make sure your local code is on GitHub.
```powershell
git push
```

### 2. Production Settings
TZ=Asia/Kolkata
# API Key for Manual Sync (Optional but recommended)
API_SECRET_KEY=your_secret_key

# --- OAUTH SETUP (REQUIRED) ---
# 1. Create Project in Google Cloud Console
# 2. API & Services -> Credentials -> Create OAuth Client ID (Web Application)
# 3. Add Authorized Origins: https://za.omysha.org
# 4. Copy Client ID below:
GOOGLE_WEB_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

### 3. Frontend Config (.env)
You must also add the Client ID to the **Frontend** build.
Create `frontend/.env`:
```env
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

### 4. Connect to Hostinger
Replace the IP with your real server IP.
```bash
ssh root@123.456.78.90
# (Type 'yes' to trust key. Paste your password.)
```

### 5. Run the Auto-Installer
I wrote a script to do everything for you. Paste these 3 lines:

```bash
cd /opt
git clone https://github.com/A4Gcollab/ZoomAutomation omysha-automation
cd omysha-automation && chmod +x scripts/deploy.sh && ./scripts/deploy.sh
```

**Wait...** The script will install Python, Nginx, Dependencies, and configure the services.

### 4. Create Secrets
When the script finishes, it will ask you to create the `.env` file.
```bash
nano .env
```
*   **PASTE** the contents of your local `.env` file here.
*   **Press**: `Ctrl+O` -> `Enter` (Save) -> `Ctrl+X` (Exit).

### 5. Secure with SSL
Make it HTTPS.
```bash
certbot --nginx -d za.omysha.org
# (Select Option 2: Redirect, if asked)
```

### 6. Final Restart
Force everything to reload with the new configs.
```bash
systemctl restart omysha-backend
systemctl restart nginx
```

## Phase 4: Validating

1.  Open Chrome: `https://za.omysha.org`
2.  **Log In**: Use your Google Account.
3.  **Check Sync**: Click the "Sync" button. It should spin and say "Scanning Zoom...".

---

### Troubleshooting
*   **Logs**: `journalctl -u omysha-backend -f` (Shows live backend logs)
*   **Restart**: `reboot` (If everything stuck, just reboot the VPS)

