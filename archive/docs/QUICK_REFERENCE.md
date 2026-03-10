# 🚀 YTZ Automation - Quick Reference Card

## 📋 TL;DR - What You Need

### For Google IDX/Firebase Studio

**Copy this entire prompt:**
👉 See `GOOGLE_IDX_FRONTEND_PROMPT.md` (lines 9-400)

**Key Points:**
- Framework: React 18 + TypeScript + Vite
- Styling: Vanilla CSS (modern design system)
- Auth: Google OAuth 2.0
- Real-time: WebSocket
- Theme: Zen light theme, professional dashboard

---

## 🔧 Backend Enhancements

**See:** `BACKEND_ENHANCEMENT.md`

**Quick Install:**
```bash
cd "d:\VONG\YTZ Automation"

# Add to requirements.txt
slowapi==0.1.9
python-jose[cryptography]
aiofiles==23.2.1
httpx==0.25.2
pydantic-settings==2.1.0
prometheus-client==0.19.0

# Install
pip install -r requirements.txt
```

**New Features:**
- ✅ WebSocket for real-time updates
- ✅ Rate limiting
- ✅ Prometheus metrics
- ✅ Enhanced error handling
- ✅ Caching layer
- ✅ Auto-generated API docs

---

## 🔌 Connecting Frontend to Backend

**See:** `FRONTEND_BACKEND_INTEGRATION.md`

### Option 1: Local Network (Development)

**Backend:**
```bash
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (in Google IDX):**
```env
VITE_API_BASE_URL=http://YOUR_LOCAL_IP:8000
VITE_WS_URL=ws://YOUR_LOCAL_IP:8000/ws
```

Find your IP:
```bash
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.100)
```

---

### Option 2: Ngrok (Recommended)

**Install Ngrok:**
```bash
choco install ngrok
# or download from https://ngrok.com/download
```

**Start Backend:**
```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

**Expose with Ngrok:**
```bash
ngrok http 8000
# Copy the https URL (e.g., https://abc123.ngrok.io)
```

**Frontend (in Google IDX):**
```env
VITE_API_BASE_URL=https://abc123.ngrok.io
VITE_WS_URL=wss://abc123.ngrok.io/ws
```

**Update Backend CORS:**
```python
# src/api.py
allow_origins=[
    "http://localhost:5173",
    "https://your-app.web.app",
    "https://abc123.ngrok.io"  # Add your ngrok URL
]
```

---

### Option 3: Deploy Backend (Production)

**Use Vultr (you already have docs!):**
```bash
# See VULTR_DEPLOYMENT.md
# Get public IP: http://YOUR_VPS_IP:8000
```

**Or use Railway.app:**
```bash
npm install -g @railway/cli
railway login
railway up
# Get URL: https://your-app.railway.app
```

**Frontend:**
```env
VITE_API_BASE_URL=https://your-backend-url.com
VITE_WS_URL=wss://your-backend-url.com/ws
```

---

## 🎨 Frontend Design System

**Colors:**
```css
--primary: #4F46E5 (Indigo)
--success: #10B981 (Emerald)
--warning: #F59E0B (Amber)
--error: #EF4444 (Red)
--background: #F9FAFB
--text: #111827
```

**Font:**
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Components:**
- Login page with Google OAuth
- Dashboard with 4 tabs (Queue, History, Logs, Errors)
- Service control panel
- Stats cards
- Real-time updates via WebSocket

---

## 📡 API Endpoints

**Base URL:** `http://localhost:8000`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | ❌ | Health check |
| `/docs` | GET | ❌ | Swagger UI |
| `/ws` | WS | ❌ | WebSocket |
| `/auth/login` | POST | ❌ | Login |
| `/stats` | GET | ✅ | Statistics |
| `/queue` | GET | ✅ | Pending recordings |
| `/history` | GET | ✅ | Completed recordings |
| `/approve/{id}` | POST | ✅ | Approve recording |
| `/logs` | GET | ✅ | System logs |
| `/service/status` | GET | ✅ | Service status |
| `/service/start` | POST | ✅ | Start service |

---

## 🧪 Testing

**Test Backend:**
```bash
# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs
```

**Test CORS:**
```javascript
// In browser console
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(d => console.log('✅ CORS working:', d));
```

**Test WebSocket:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (e) => console.log('📨', e.data);
```

---

## 🐛 Common Issues

### CORS Error
**Fix:** Add frontend origin to backend CORS:
```python
# src/api.py
allow_origins=["http://localhost:5173", "https://your-app.web.app"]
```

### WebSocket Won't Connect
**Fix:** Check URL scheme:
- Local: `ws://localhost:8000/ws`
- HTTPS: `wss://your-domain.com/ws`

### 401 Unauthorized
**Fix:** Check token in header:
```javascript
headers: { 'X-Token': 'your_token_here' }
```

### Can't Access Backend from Frontend
**Fix:** Use ngrok or deploy backend to cloud

---

## 📦 File Structure

```
YTZ Automation/
├── src/
│   ├── api.py                    # Main API (FastAPI)
│   ├── db_sql.py                 # Database
│   ├── auth.py                   # Authentication
│   ├── websocket_manager.py      # NEW: WebSocket
│   ├── metrics.py                # NEW: Prometheus
│   ├── cache.py                  # NEW: Caching
│   └── exceptions.py             # NEW: Error handling
├── data/
│   ├── vong_v2.db               # SQLite database
│   └── app.log                  # Logs
├── secrets/
│   └── (OAuth credentials)
├── BACKEND_ENHANCEMENT.md        # 👈 Backend guide
├── GOOGLE_IDX_FRONTEND_PROMPT.md # 👈 Frontend prompt
├── FRONTEND_BACKEND_INTEGRATION.md # 👈 Integration guide
└── QUICK_REFERENCE.md           # 👈 This file
```

---

## 🚀 Deployment Steps

### 1. Enhance Backend
```bash
# Add new dependencies
pip install slowapi python-jose aiofiles httpx pydantic-settings prometheus-client

# Create new files (see BACKEND_ENHANCEMENT.md)
# - src/websocket_manager.py
# - src/metrics.py
# - src/cache.py
# - src/exceptions.py

# Update src/api.py with enhancements

# Test
python -m uvicorn src.api:app --reload
```

### 2. Build Frontend in Google IDX
```bash
# Copy prompt from GOOGLE_IDX_FRONTEND_PROMPT.md
# Paste into Google IDX/Firebase Studio
# Wait for AI to build the app

# Set environment variables
VITE_API_BASE_URL=http://YOUR_BACKEND_URL
VITE_WS_URL=ws://YOUR_BACKEND_URL/ws
VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID

# Build
npm run build

# Deploy to Firebase
firebase deploy
```

### 3. Connect Them
```bash
# Option A: Use ngrok
ngrok http 8000

# Option B: Deploy backend to Vultr/Railway
# See VULTR_DEPLOYMENT.md or Railway docs

# Update frontend env vars with backend URL
# Update backend CORS with frontend URL
```

---

## ✅ Success Checklist

- [ ] Backend running and accessible
- [ ] Frontend deployed to Firebase
- [ ] CORS configured correctly
- [ ] WebSocket connecting
- [ ] Login working (Google OAuth or Demo)
- [ ] Dashboard showing real data
- [ ] Approvals working
- [ ] Logs streaming in real-time
- [ ] Service controls working
- [ ] Mobile responsive
- [ ] No errors in console

---

## 🎯 Your Backend is AMAZING Because:

- ⚡ Real-time WebSocket updates
- 📊 Prometheus metrics (`/metrics`)
- 🛡️ Rate limiting (10 req/min)
- 💾 Intelligent caching (30s TTL)
- 📚 Auto-generated docs (`/docs`)
- 🏥 Detailed health checks
- 🚨 Enhanced error handling
- 🎯 Production-ready

---

## 🎨 Your Frontend Will Be AMAZING Because:

- 🎨 Modern, professional design
- ⚡ Real-time updates
- 📱 Mobile responsive
- 🔐 Google OAuth
- 🎯 Intuitive UX
- 🚀 Fast (< 2s load)
- ♿ Accessible
- 🎭 Smooth animations

---

## 📚 Documentation

1. **BACKEND_ENHANCEMENT.md** - How to make your backend production-ready
2. **GOOGLE_IDX_FRONTEND_PROMPT.md** - Complete prompt for Google IDX
3. **FRONTEND_BACKEND_INTEGRATION.md** - How to connect them
4. **QUICK_REFERENCE.md** - This file (quick lookup)

---

## 🆘 Need Help?

**Backend Issues:**
- Check logs: `data/app.log`
- Check health: `http://localhost:8000/health`
- Check docs: `http://localhost:8000/docs`

**Frontend Issues:**
- Check browser console (F12)
- Check Network tab for failed requests
- Verify environment variables

**Connection Issues:**
- Test CORS with curl
- Test WebSocket with browser console
- Check firewall settings
- Verify URLs match

---

## 🎉 You're Ready!

1. ✅ Copy prompt from `GOOGLE_IDX_FRONTEND_PROMPT.md`
2. ✅ Paste into Google IDX/Firebase Studio
3. ✅ Enhance backend with `BACKEND_ENHANCEMENT.md`
4. ✅ Connect them with `FRONTEND_BACKEND_INTEGRATION.md`
5. ✅ Deploy and enjoy! 🚀

**Your YTZ Automation system will be PRODUCTION-READY and AMAZING! 🔥**

---

## 💡 Pro Tips

- Use **ngrok** for quick testing (no deployment needed)
- Use **Railway.app** for easy backend deployment
- Use **Firebase Hosting** for frontend (already in Google IDX)
- Enable **demo mode** for testing without Google OAuth
- Check **Swagger UI** (`/docs`) for API exploration
- Monitor **metrics** (`/metrics`) for performance
- Use **WebSocket** for real-time feel
- Keep **CORS** updated when changing domains

---

**Built with ❤️ for the VONG Team**
