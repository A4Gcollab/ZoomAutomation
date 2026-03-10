# 🚀 VPS Deployment Guide: YTZ Automation

This guide explains how to host the automation bot 24/7 using a Virtual Private Server (VPS).

## 1. Hostinger vs. Vultr

For running a Docker-based Python bot, you need **Root Access**. Shared Web Hosting (like Hostinger Premium Web Hosting) **will NOT work** because you cannot run background processes or install Docker. You must use a **VPS**.

### 🏆 Recommendation: Vultr (Cloud Compute)
**Why?** Vultr offers a "One-Click Docker" image, meaning you don't have to install Docker manually. It's built for developers.
- **Cost**: ~$6/month (High Performance)
- **Ease of Use**: High (Pre-installed Docker)
- **Billing**: Hourly (Destroy server when not in use to stop paying)

### 🥈 Hostinger (KVM VPS)
**Why?** Checking if you already have it.
- **Cost**: Good initial deals, higher renewal.
- **Ease of Use**: Medium (You often have to install Docker yourself).
- **Billing**: Monthly/Yearly.

---

## 2. Setting Up Vultr (Preferred)

1.  **Create Account**: Go to Vultr.com.
2.  **Deploy New Server**:
    *   **Choose Type**: Cloud Compute (Shared CPU).
    *   **Location**: Choose closest to you (e.g., Singapore/Mumbai).
    *   **Image**: Click "Marketplace Apps" tab -> Search **"Docker"** -> Select **Docker on Ubuntu**.
    *   **Plan**: The $6/mo (1GB RAM) is sufficient.
3.  **Wait**: Wait for IP Address to appear (e.g., `192.168.1.50`).

---

## 3. Connecting & Installing

### Windows (PowerShell)
Open PowerShell and run:
```powershell
ssh root@<YOUR_VPS_IP>
# Enter password found in Vultr Dashboard
```

### Step-by-Step Installation

**1. Create Project Directory:**
```bash
mkdir -p /opt/omysha-automation
cd /opt/omysha-automation
```

**2. Upload Files:**
You can use **FileZilla** (SFTP) to drag-and-drop your project folder to `/opt/omysha-automation`.
*Exclude `venv`, `__pycache__`, and `.git` folders to save time.*

**3. Configure Environment:**
Create your `.env` file on the server:
```bash
nano .env
```
*Paste your `.env` content here. Ctrl+O to save, Ctrl+X to exit.*

**4. Create Secrets Directory:**
```bash
mkdir secrets
# Upload your client_secret.json and credentials to this folder via FileZilla
```

**5. Start the Bot:**
Run Docker Compose (it handles everything):
```bash
docker compose up --build -d
```
*-d runs it in "Detached" mode (background).*

---

## 4. Maintenance / Cheatsheet

| Action | Command |
| :--- | :--- |
| **Check Logs** | `docker compose logs -f` |
| **Stop Bot** | `docker compose down` |
| **Restart Bot** | `docker compose restart` |
| **Update Code** | (Upload new files) then `docker compose up --build -d` |

## 5. Google Sheet Setup
Before leaving, run the setup script **Locally** on your PC once to initialize the Sheet:
```powershell
python -m scripts.setup_v2_sheet
```
Then, inside the Sheet's **Settings** tab, set Command to `START` to wake up the bot on the VPS.
