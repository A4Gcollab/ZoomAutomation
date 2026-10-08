# YTZ Automation - Quick Start Guide

## 🚀 Quick Start (Windows)

### Option 1: One-Click Start (Easiest)
```bash
# Double-click this file:
start.bat
```

This will:
1. Start the backend on port 8000
2. Start the frontend on port 5173
3. Open your browser automatically

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Browser:**
```
http://localhost:5173
```

## 🎯 Demo Mode Login

The login page now has a **Demo Mode** button that bypasses Google OAuth entirely.

Just click "Enter Dashboard" and you're in! No Google account needed for testing.

## ✅ Verify Everything Works

### 1. Check Backend
Open: `http://localhost:8000/health`

Should see: `{"status":"ok"}`

### 2. Check Frontend
Open: `http://localhost:5173`

Should see: Beautiful login page with gradient background

### 3. Login
Click the "Enter Dashboard" button

Should: Navigate to dashboard immediately

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process if needed
taskkill /PID <process_id> /F

# Try again
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### Frontend won't start
```bash
# Check if port 5173 is in use
netstat -ano | findstr :5173

# Kill the process if needed
taskkill /PID <process_id> /F

# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Login button doesn't work
1. Open browser console (F12)
2. Look for errors
3. Make sure backend is running (check `http://localhost:8000/health`)
4. Try refreshing the page

### Service Start button doesn't work
- The service auto-starts with the backend
- Check the "Background Service" status on the dashboard
- If it shows "Stopped", the service will start automatically when you approve a recording

## 📊 Dashboard Features

### Service Control Panel
- Shows if background service is running
- Start/Stop/Restart buttons (admin only)
- Uptime counter

### Stats Cards
- Pending recordings
- Completed recordings
- Error count
- Total recordings

### Tabs
- **Queue**: Approve pending recordings
- **History**: View completed recordings with YouTube/Drive links
- **Logs**: System logs with timestamps
- **Errors**: Dedicated error viewer

## 🎨 UI Features

- Clean, modern design
- Zen light theme
- Color-coded status badges
- Real-time updates every 10 seconds
- Responsive layout

## 🔐 Security Note

Demo mode is for **development and testing only**. 

For production:
1. Set up proper Google OAuth credentials
2. Configure admin emails in `src/config.py`
3. Remove or disable demo mode

## 📝 Next Steps

1. ✅ Start the application
2. ✅ Login with demo mode
3. ✅ Explore the dashboard
4. ✅ Try approving a recording (if you have Zoom data)
5. ✅ Check the logs tab

## 💡 Tips

- **Auto-refresh**: Dashboard updates every 10 seconds
- **Keyboard**: Press F5 to manually refresh
- **Console**: Press F12 to see detailed logs
- **Multiple tabs**: You can open multiple dashboard tabs

## 🆘 Still Having Issues?

1. Make sure both backend and frontend are running
2. Check browser console for errors (F12)
3. Check backend logs in the terminal
4. Verify `http://localhost:8000/health` returns OK
5. Try clearing browser cache and localStorage

## 📚 Documentation

- `DEPLOYMENT.md` - Production deployment guide
- `README.md` - Project overview
- `src/config.py` - Configuration settings
