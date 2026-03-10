# 🔗 Frontend-Backend Integration Guide

## 🎯 Overview

This guide shows you how to connect your Google IDX/Firebase Studio frontend to your local backend.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Google IDX/Firebase Studio         │
│  (Frontend - React + TypeScript)    │
│  Hosted on Firebase                 │
└──────────────┬──────────────────────┘
               │
               │ HTTPS/WSS
               │
┌──────────────▼──────────────────────┐
│  Your Local Backend                 │
│  (FastAPI + Python)                 │
│  Running on Windows                 │
└─────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Local Development (Easiest)

**Step 1: Run Backend Locally**
```bash
cd "d:\VONG\YTZ Automation"
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

**Step 2: Configure Frontend**
In Google IDX, set environment variable:
```env
VITE_API_BASE_URL=http://YOUR_LOCAL_IP:8000
VITE_WS_URL=ws://YOUR_LOCAL_IP:8000/ws
```

Find your local IP:
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
# Example: 192.168.1.100
```

**Step 3: Test Connection**
Open frontend in browser, check console for:
```
✅ Backend connected: http://192.168.1.100:8000
✅ WebSocket connected
```

---

### Option 2: Expose Backend via Ngrok (Recommended for Firebase Hosting)

**Step 1: Install Ngrok**
```bash
# Download from https://ngrok.com/download
# Or use chocolatey:
choco install ngrok
```

**Step 2: Start Backend**
```bash
cd "d:\VONG\YTZ Automation"
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

**Step 3: Expose with Ngrok**
```bash
ngrok http 8000
```

You'll see:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Step 4: Configure Frontend**
In Google IDX:
```env
VITE_API_BASE_URL=https://abc123.ngrok.io
VITE_WS_URL=wss://abc123.ngrok.io/ws
```

**Step 5: Update Backend CORS**
In `src/api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://your-app.web.app",  # Your Firebase domain
        "https://abc123.ngrok.io"     # Your ngrok URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Option 3: Deploy Backend to Cloud (Production)

**Best Options:**

1. **Vultr VPS** (You already have deployment docs!)
   - Follow `VULTR_DEPLOYMENT.md`
   - Get public IP: `http://YOUR_VPS_IP:8000`
   - Configure frontend to use this URL

2. **Railway.app** (Easiest)
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Deploy
   railway up
   ```

3. **Google Cloud Run** (Serverless)
   ```bash
   # Build container
   docker build -t gcr.io/YOUR_PROJECT/ytz-backend .
   
   # Push to registry
   docker push gcr.io/YOUR_PROJECT/ytz-backend
   
   # Deploy
   gcloud run deploy ytz-backend \
     --image gcr.io/YOUR_PROJECT/ytz-backend \
     --platform managed \
     --allow-unauthenticated
   ```

---

## 🔧 Backend Configuration for Frontend

### 1. Update CORS (CRITICAL!)

**File: `src/api.py`**

```python
from fastapi.middleware.cors import CORSMiddleware

# Get allowed origins from environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

# Default origins for development
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Add to `.env`:**
```env
ALLOWED_ORIGINS=http://localhost:5173,https://your-app.web.app,https://your-app.firebaseapp.com
```

---

### 2. Add Health Check Endpoint

Already exists! Test it:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

---

### 3. Enable WebSocket (Already Done!)

Test WebSocket:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (event) => console.log('Message:', event.data);
```

---

## 🎨 Frontend Configuration

### Environment Variables

**File: `.env` (in your Google IDX project)**

```env
# Backend URLs
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Google OAuth
VITE_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com

# App Config
VITE_APP_NAME=YTZ Automation
VITE_APP_VERSION=2.0.0

# Feature Flags
VITE_ENABLE_DEMO_MODE=true
VITE_ENABLE_WEBSOCKET=true
VITE_AUTO_REFRESH_INTERVAL=10000
```

**For Production:**
```env
VITE_API_BASE_URL=https://your-backend.com
VITE_WS_URL=wss://your-backend.com/ws
VITE_ENABLE_DEMO_MODE=false
```

---

### API Client Setup

**File: `src/services/api.ts`**

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['X-Token'] = this.token;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.message || 'Request failed');
    }

    return response.json();
  }

  // Auth
  async login(googleToken: string) {
    return this.request<{ token: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ token: googleToken }),
    });
  }

  // Stats
  async getStats() {
    return this.request<{ completed: number; pending: number }>('/stats');
  }

  // Queue
  async getQueue() {
    return this.request<any[]>('/queue');
  }

  // History
  async getHistory(limit = 50) {
    return this.request<any[]>(`/history?limit=${limit}`);
  }

  // Options
  async getOptions() {
    return this.request<{ teams: string[]; playlists: string[] }>('/options');
  }

  // Approve
  async approveRecording(zoomId: string, team: string, playlist: string) {
    return this.request(`/approve/${zoomId}`, {
      method: 'POST',
      body: JSON.stringify({ team, playlist }),
    });
  }

  // Logs
  async getLogs(lines = 100, level?: string) {
    const params = new URLSearchParams({ lines: lines.toString() });
    if (level) params.append('level', level);
    return this.request<{ logs: any[]; total: number }>(`/logs?${params}`);
  }

  // Service
  async getServiceStatus() {
    return this.request<{ status: string; running: boolean; uptime: number }>(
      '/service/status'
    );
  }

  async startService() {
    return this.request('/service/start', { method: 'POST' });
  }

  async stopService() {
    return this.request('/service/stop', { method: 'POST' });
  }

  async restartService() {
    return this.request('/service/restart', { method: 'POST' });
  }
}

export const api = new ApiClient(API_BASE_URL);
```

---

### WebSocket Client Setup

**File: `src/services/websocket.ts`**

```typescript
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

type EventCallback = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Map<string, EventCallback[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;

  connect() {
    try {
      this.ws = new WebSocket(WS_URL);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected', null);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message:', data);
          this.emit(data.type, data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('❌ WebSocket disconnected');
        this.emit('disconnected', null);
        this.reconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.reconnect();
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  on(event: string, callback: EventCallback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: string, callback: EventCallback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach((cb) => cb(data));
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(
        `🔄 Reconnecting in ${delay}ms... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      );
      setTimeout(() => this.connect(), delay);
    } else {
      console.error('❌ Max reconnection attempts reached');
      this.emit('max_reconnect_attempts', null);
    }
  }
}

export const wsClient = new WebSocketClient();
```

---

## 🧪 Testing the Connection

### 1. Test Backend Health

```bash
# Terminal 1: Start backend
cd "d:\VONG\YTZ Automation"
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Open in browser for Swagger UI
```

### 2. Test CORS

```javascript
// In browser console (on frontend)
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(d => console.log('✅ CORS working:', d))
  .catch(e => console.error('❌ CORS error:', e));
```

### 3. Test WebSocket

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('✅ WebSocket connected');
ws.onmessage = (e) => console.log('📨 Message:', e.data);
ws.onerror = (e) => console.error('❌ WebSocket error:', e);
```

### 4. Test Authentication

```javascript
// In browser console
fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ token: 'demo_token' })
})
  .then(r => r.json())
  .then(d => console.log('✅ Auth working:', d))
  .catch(e => console.error('❌ Auth error:', e));
```

---

## 🔒 Security Checklist

- [ ] CORS configured with specific origins (not `*`)
- [ ] HTTPS enabled in production
- [ ] WebSocket using WSS (secure) in production
- [ ] API tokens stored securely (localStorage or httpOnly cookies)
- [ ] Environment variables not committed to git
- [ ] Rate limiting enabled
- [ ] Admin endpoints protected
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using parameterized queries)
- [ ] XSS prevention (React handles this by default)

---

## 🚀 Deployment Checklist

### Backend Deployment

- [ ] Backend running on public server (Vultr/Railway/Cloud Run)
- [ ] HTTPS certificate installed (Let's Encrypt)
- [ ] Firewall configured (allow ports 80, 443)
- [ ] Environment variables set
- [ ] Database backed up
- [ ] Logs configured
- [ ] Health checks passing
- [ ] CORS configured for production domain

### Frontend Deployment (Firebase)

```bash
# In Google IDX terminal

# 1. Build
npm run build

# 2. Test build locally
npm run preview

# 3. Deploy to Firebase
firebase deploy

# 4. Get deployment URL
# Example: https://ytz-automation.web.app
```

**Update Backend CORS:**
```python
# src/api.py
allow_origins=[
    "https://ytz-automation.web.app",
    "https://ytz-automation.firebaseapp.com"
]
```

---

## 🐛 Troubleshooting

### Issue: CORS Error

**Symptom:** Browser console shows:
```
Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:5173' 
has been blocked by CORS policy
```

**Solution:**
1. Check backend CORS configuration includes frontend origin
2. Restart backend after changing CORS settings
3. Clear browser cache
4. Check for typos in origin URLs

---

### Issue: WebSocket Connection Failed

**Symptom:** WebSocket shows "disconnected" or errors

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check WebSocket endpoint: `ws://localhost:8000/ws` (not `wss://`)
3. Check firewall isn't blocking WebSocket
4. Try different port if 8000 is blocked
5. Check browser console for specific error

---

### Issue: 401 Unauthorized

**Symptom:** All API calls return 401

**Solution:**
1. Check token is being sent in `X-Token` header
2. Check token is valid (not expired)
3. Try demo mode to bypass auth
4. Check backend logs for auth errors
5. Re-login to get fresh token

---

### Issue: Can't Connect to Backend from Frontend

**Symptom:** Network errors, timeout

**Solution:**
1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check firewall:**
   ```bash
   # Windows: Allow port 8000
   netsh advfirewall firewall add rule name="YTZ Backend" dir=in action=allow protocol=TCP localport=8000
   ```

3. **Use correct IP:**
   - `localhost` only works on same machine
   - Use local IP (192.168.x.x) for same network
   - Use ngrok for internet access

4. **Check environment variables:**
   ```javascript
   console.log(import.meta.env.VITE_API_BASE_URL);
   // Should match your backend URL
   ```

---

## 📊 Monitoring

### Backend Logs

```bash
# Watch logs in real-time
tail -f data/app.log

# Filter errors only
grep ERROR data/app.log

# Count requests
grep "GET /stats" data/app.log | wc -l
```

### Frontend Logs

```javascript
// Enable verbose logging
localStorage.setItem('debug', 'true');

// Check API calls
// Open DevTools > Network tab
// Filter by "Fetch/XHR"
```

---

## 🎯 Success Criteria

Your integration is working if:

- ✅ Frontend loads without errors
- ✅ Login works (Google OAuth or Demo mode)
- ✅ Dashboard shows real data from backend
- ✅ Approving a recording updates immediately
- ✅ WebSocket shows "connected" status
- ✅ Logs stream in real-time
- ✅ Service control buttons work
- ✅ No CORS errors in console
- ✅ No 401/403 errors
- ✅ Mobile responsive

---

## 📚 Additional Resources

- [FastAPI CORS Docs](https://fastapi.tiangolo.com/tutorial/cors/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Firebase Hosting](https://firebase.google.com/docs/hosting)
- [Ngrok Documentation](https://ngrok.com/docs)
- [Google OAuth Setup](https://developers.google.com/identity/gsi/web/guides/overview)

---

## 🆘 Need Help?

1. Check backend logs: `data/app.log`
2. Check browser console (F12)
3. Test endpoints with Swagger UI: `http://localhost:8000/docs`
4. Verify environment variables
5. Try demo mode to isolate auth issues
6. Check network tab for failed requests

---

**You're all set! 🚀 Your frontend and backend should now be connected and working beautifully!**
