# 🎨 Google IDX / Firebase Studio - Frontend Build Prompt

## 🎯 Project Overview

Build a **stunning, modern, real-time dashboard** for the YTZ Automation System - a Zoom recording management platform that automates video processing, YouTube compression, and Google Drive backup.

---

## 📋 Complete Prompt for Google IDX/Firebase Studio

```
Create a modern, real-time dashboard web application for a Zoom recording automation system with the following specifications:

=== PROJECT SETUP ===

Framework: React 18+ with TypeScript
Build Tool: Vite
Styling: Vanilla CSS with modern design system (NO Tailwind unless I explicitly request it)
State Management: React Context API + Hooks
Real-time: WebSocket for live updates
Authentication: Google OAuth 2.0

=== DESIGN REQUIREMENTS ===

Theme: Modern, professional dashboard with zen light theme
Color Palette:
  - Primary: #4F46E5 (Indigo)
  - Success: #10B981 (Emerald)
  - Warning: #F59E0B (Amber)
  - Error: #EF4444 (Red)
  - Background: #F9FAFB (Light gray)
  - Surface: #FFFFFF (White)
  - Text Primary: #111827 (Dark gray)
  - Text Secondary: #6B7280 (Medium gray)

Typography:
  - Font: Inter from Google Fonts
  - Headings: 600-700 weight
  - Body: 400-500 weight

Design Principles:
  - Clean, minimal interface
  - Generous whitespace
  - Smooth transitions (200-300ms)
  - Subtle shadows for depth
  - Rounded corners (8-12px)
  - Hover effects on interactive elements
  - Color-coded status badges
  - Responsive layout (mobile-first)

=== PAGES & COMPONENTS ===

1. LOGIN PAGE (/login)
   - Centered card layout with gradient background
   - Google OAuth button (prominent, branded)
   - Demo Mode button (for testing, bypasses auth)
   - Logo and tagline
   - Smooth fade-in animation

2. DASHBOARD PAGE (/)
   - Top Navigation Bar:
     * Logo
     * User profile (avatar, name, email)
     * Logout button
   
   - Service Control Panel (Top Section):
     * Background Service Status indicator (green=running, red=stopped)
     * Uptime counter
     * Start/Stop/Restart buttons (admin only)
     * Real-time status updates via WebSocket
   
   - Statistics Cards (4 cards in grid):
     * Pending Tasks (yellow badge, large number) - "Action Required"
     * My Approvals (purple badge) - "Approved by me today" (User-specific)
     * System Health (green/red) - "All Systems Operational" or "Issues Detected"
     * Processing/Error Ratio - Visual mini-chart or text (e.g., "98% Success Rate")
     * Each card should have subtle hover lift effect
   
   - Tabbed Interface:
     
     TAB 1: QUEUE (Pending Recordings)
     - Table with columns:
       * Date
       * Topic (meeting name)
       * Account
       * Team (dropdown selector)
       * Playlist (dropdown selector)
       * Actions (Approve button)
     - Approve button opens confirmation modal
     - Real-time updates when new recordings detected
     - Empty state: "No pending recordings" with icon
     
     IMPORTANT - USER IDENTITY & APPROVAL TRACKING:
     - The application MUST track exactly WHO performs an action
     - When user logs in via Google:
       * Extract Name, Email, and Avatar URL from ID token
       * Display User Avatar and Name in top navigation bar
       * Store this user profile in React Context/Global State
     - When Approving a recording:
       * The API request MUST include the user's email/identity (handled via X-Token)
       * The "Approved By" field in the database relies on this token
     - In the HISTORY tab:
       * The "Approved By" column MUST display the Approve User's email or name
       * If possible, show a small avatar of the approver next to their name
       * This is critical for accountability in multi-user teams
     
     IMPORTANT - APPROVAL WORKFLOW:
     When user approves a recording:
     1. User selects Team from dropdown (e.g., "Marketing", "Engineering", "Sales")
     2. User selects Playlist from dropdown (e.g., "Weekly Standups", "Client Meetings", "Training")
     3. User clicks "Approve" button
     4. Modal shows confirmation: "Approve recording for [Team] / [Playlist] as [User Name]?"
     5. On confirm, frontend sends POST /approve/{zoom_id} with team and playlist
     6. Backend marks recording as APPROVED in database
     7. Backend broadcasts WebSocket event: recording_approved (including approved_by field)
     8. Frontend receives WebSocket event and updates UI immediately
     9. Toast notification should say: "Approved by [User Name]" verifies the action
     10. Recording moves from PENDING to PROCESSING status
     10. Background service picks up APPROVED recording and starts processing:
         a. Downloads video from Zoom
         b. Uploads to YouTube with title format: "YYYYMMDD Topic Name"
         c. Adds video to the selected YouTube playlist
         d. Uploads captions/transcript to YouTube video
         e. Downloads compressed version from YouTube
         f. Uploads to Google Drive in folder structure: Team/YYYYMMDD Topic Name/
         g. Updates status to COMPLETED with YouTube URL and Drive URL
         h. Broadcasts WebSocket event: recording_completed
     11. Frontend receives completion event and shows success toast
     12. Recording appears in HISTORY tab with clickable YouTube and Drive links
     
     TEAM & PLAYLIST MANAGEMENT:
     - Teams represent organizational units (Marketing, Engineering, Sales, HR, etc.)
     - Playlists are YouTube playlists where videos are organized
     - Each recording MUST have both Team and Playlist selected before approval
     - Dropdowns are populated from GET /options endpoint
     - Options endpoint returns teams and playlists from:
       * Previously used combinations (from database)
       * Configured playlists (from config/playlists.json) ← AUTOMATIC SYNC!
     - **IMPORTANT**: Any playlists you add to backend config/playlists.json will 
       automatically appear in the frontend dropdowns (no frontend code changes needed!)
     - User can type to add NEW team or playlist (autocomplete with existing options)
     - New teams/playlists are automatically saved when used
     - Refresh options by calling GET /options (frontend does this on Queue tab load)
     
     DROPDOWN BEHAVIOR:
     - Show existing options first
     - Allow typing to filter options
     - Allow typing new values (not in list)
     - Show "Add new: [typed value]" option when typing new value
     - Validate: Team and Playlist cannot be empty
     - Show validation error if user tries to approve without selecting both
     
     YOUTUBE INTEGRATION:
     - Videos are uploaded as UNLISTED (not public, not private)
     - Title format: "YYYYMMDD Topic Name" (e.g., "20260202 Weekly Marketing Standup")
     - Description includes: Topic, Recording date, Team, Playlist
     - Video is automatically added to the selected YouTube playlist
     - Captions/transcript are uploaded if available from Zoom
     - YouTube URL format: https://youtu.be/VIDEO_ID
     
     GOOGLE DRIVE INTEGRATION:
     - Files are organized by Team in root folder
     - Each recording gets its own subfolder: "YYYYMMDD Topic Name"
     - Subfolder contains:
       * Video file (MP4, compressed from YouTube)
       * Transcript file (VTT or TXT if available)
     - Drive URL format: https://drive.google.com/file/d/FILE_ID/view
     - Folder structure example:
       Root Folder/
       ├── Marketing/
       │   ├── 20260202 Weekly Standup/
       │   │   ├── 20260202_Weekly_Standup.mp4
       │   │   └── 20260202_Weekly_Standup.vtt
       │   └── 20260201 Client Review/
       │       └── 20260201_Client_Review.mp4
       └── Engineering/
           └── 20260202 Sprint Planning/
               ├── 20260202_Sprint_Planning.mp4
               └── 20260202_Sprint_Planning.vtt
     
     STATUS FLOW:
     PENDING → (user approves) → APPROVED → (background service picks up) → 
     PROCESSING → (upload complete) → COMPLETED
     
     If any step fails: → ERROR (with error message)
     
     UI FEEDBACK:
     - Show loading spinner on Approve button while API call in progress
     - Show success toast: "Recording approved! Processing will begin shortly."
     - Show error toast if approval fails: "Failed to approve: [error message]"
     - Update table row status immediately (optimistic update)
     - If WebSocket event confirms, keep update; if error, revert
     - Show processing indicator (animated) for PROCESSING status
     - Show green checkmark for COMPLETED status
     - Show red X for ERROR status with expandable error details
     
     TAB 2: HISTORY (Completed Recordings)
     - Table with columns:
       * Date
       * Topic
       * Team (shows which team it was assigned to)
       * Playlist (shows which YouTube playlist it's in)
       * Status (badge: COMPLETED/ERROR/PROCESSING)
       * YouTube Link (clickable, opens in new tab, shows thumbnail on hover)
       * Drive Link (clickable, opens in new tab, shows folder icon)
       * Approved By (email of user who approved it)
     - Pagination (50 items per page)
     - Filter by status (All, Completed, Processing, Error)
     - Filter by team (dropdown with all teams)
     - Filter by playlist (dropdown with all playlists)
     - Search by topic (real-time search as you type)
     - Sort by date (newest first by default)
     - Click on row to expand and show full details:
       * Full topic name
       * Recording date and time
       * Approval date and time
       * Processing completion date and time
       * Video duration (if available)
       * File size (if available)
       * Error message (if status is ERROR)
     - Export to CSV button (exports filtered results)
     - Refresh button to manually reload data
     
     TAB 3: LOGS (System Logs)
     - Log viewer with:
       * Timestamp
       * Level (INFO/WARNING/ERROR with color coding)
       * Logger name
       * Message
     - Auto-scroll to bottom
     - Filter by log level
     - Clear logs button
     - Real-time log streaming via WebSocket
     
     TAB 4: ERRORS (Error Logs)
     - Dedicated error viewer
     - Shows only ERROR level logs
     - Red theme
     - Expandable error details
     - Copy error button

=== FEATURES & FUNCTIONALITY ===

Authentication:
- Google OAuth flow using backend /auth/login endpoint
- Store JWT token in localStorage
- Include X-Token header in all API requests
- Demo mode: bypass auth, use mock token
- Auto-redirect to login if token invalid (401)
- Auto-redirect to dashboard if already logged in

Real-time Updates:
- WebSocket connection to ws://localhost:8000/ws
- Listen for events:
  * recording_approved
  * recording_completed
  * service_status_changed
  * new_log_entry
- Auto-reconnect on disconnect
- Show connection status indicator

Data Fetching:
- Fetch stats every 10 seconds (or use WebSocket updates)
- Fetch queue/history on tab switch
- Optimistic UI updates (update UI before server confirms)
- Loading states for all async operations
- Error handling with toast notifications

User Experience:
- Toast notifications for:
  * Successful approval
  * Errors
  * Service status changes
  * Connection status
- Confirmation modals for destructive actions
- Keyboard shortcuts:
  * F5: Refresh data
  * Esc: Close modals
- Smooth page transitions
- Loading skeletons for tables
- Infinite scroll or pagination for large lists

=== API INTEGRATION ===

Backend Base URL: http://localhost:8000

Endpoints to integrate:

GET /health
  - Check backend availability
  - Show connection status

POST /auth/login
  Body: { "token": "<google_id_token>" }
  Response: { "token": "<session_token>", "user": {...} }

GET /stats
  Headers: { "X-Token": "<token>" }
  Response: { 
    "completed": 10, 
    "pending": 5 
  }
  Notes: Cached for 30 seconds on backend for performance

GET /queue
  Headers: { "X-Token": "<token>" }
  Response: [
    {
      "zoom_id": "12345678",
      "topic": "Weekly Marketing Standup",
      "start_time": "2026-02-02T10:00:00Z",
      "date_str": "2026-02-02",
      "account_name": "Zoom Account 1",
      "status": "PENDING",
      "team": null,  // Will be null until user selects
      "playlist": null,  // Will be null until user selects
      "metadata": { ... }
    }
  ]
  Notes: Returns all recordings with status='PENDING'

GET /history?limit=50
  Headers: { "X-Token": "<token>" }
  Response: [
    {
      "zoom_id": "12345678",
      "topic": "Weekly Marketing Standup",
      "start_time": "2026-02-02T10:00:00Z",
      "date_str": "2026-02-02",
      "status": "COMPLETED",  // or "PROCESSING", "ERROR", "APPROVED"
      "team": "Marketing",
      "playlist": "Weekly Standups",
      "youtube_url": "https://youtu.be/abc123",
      "drive_url": "https://drive.google.com/file/d/xyz789/view",
      "approved_by": "user@example.com",
      "created_at": "2026-02-02T10:05:00Z",
      "processed_at": "2026-02-02T10:15:00Z"  // When processing completed
    }
  ]
  Notes: Returns recordings with status != 'PENDING', sorted by created_at DESC

GET /options
  Headers: { "X-Token": "<token>" }
  Response: { 
    "teams": ["Marketing", "Engineering", "Sales", "HR"],
    "playlists": ["Weekly Standups", "Client Meetings", "Training Sessions", "All Hands"]
  }
  Notes: 
  - Returns unique teams and playlists from database (previously used)
  - Also includes teams/playlists from config/playlists.json
  - Frontend should allow adding new values not in this list
  - When user types new value, show "Add new: [value]" option

POST /approve/{zoom_id}
  Headers: { "X-Token": "<token>" }
  Body: { 
    "team": "Marketing",  // REQUIRED
    "playlist": "Weekly Standups"  // REQUIRED
  }
  Response: { 
    "status": "Approved" 
  }
  Notes:
  - This is an ASYNC endpoint (returns immediately)
  - Backend updates database: status='APPROVED', team=..., playlist=..., approved_by=user.email
  - Backend invalidates stats and queue cache
  - Backend broadcasts WebSocket event: recording_approved
  - Background service will pick up APPROVED recordings and process them
  - Processing happens asynchronously (download → YouTube → Drive)
  - Frontend should show optimistic update (move to PROCESSING immediately)
  - Frontend should listen for WebSocket events for real status updates

GET /logs?lines=100&level=INFO
  Headers: { "X-Token": "<token>" }
  Response: { "logs": [{ timestamp, level, logger, message }], "total": 100 }

GET /errors?lines=50
  Headers: { "X-Token": "<token>" }
  Response: { "logs": [...] }

GET /service/status
  Headers: { "X-Token": "<token>" }
  Response: { "status": "running", "running": true, "uptime": 3600 }

POST /service/start
  Headers: { "X-Token": "<token>" }
  Response: { "success": true, "message": "Service started" }

POST /service/stop
  Headers: { "X-Token": "<token>" }
  Response: { "success": true, "message": "Service stopping..." }

POST /service/restart
  Headers: { "X-Token": "<token>" }
  Response: { "success": true, "message": "Service restarted" }

WebSocket: ws://localhost:8000/ws
  Connection: Establish on app load, auto-reconnect on disconnect
  
  Event Types and Handling:
  
  1. recording_approved
     Payload: {
       "type": "recording_approved",
       "zoom_id": "12345678",
       "approved_by": "user@example.com",
       "team": "Marketing",
       "playlist": "Weekly Standups",
       "timestamp": "2026-02-02T10:05:00Z"
     }
     Frontend Action:
     - Remove recording from Queue tab
     - Show toast: "Recording approved by [approved_by]"
     - Update stats (decrement pending count)
     - Refresh queue list
  
  2. recording_completed
     Payload: {
       "type": "recording_completed",
       "zoom_id": "12345678",
       "youtube_url": "https://youtu.be/abc123",
       "drive_url": "https://drive.google.com/file/d/xyz789/view",
       "team": "Marketing",
       "playlist": "Weekly Standups",
       "timestamp": "2026-02-02T10:15:00Z"
     }
     Frontend Action:
     - Update recording status to COMPLETED in History tab
     - Show toast: "Recording processed successfully! [YouTube link]"
     - Update stats (increment completed count)
     - Add clickable YouTube and Drive links to history row
     - Play success sound (optional)
  
  3. recording_processing
     Payload: {
       "type": "recording_processing",
       "zoom_id": "12345678",
       "status": "PROCESSING",
       "message": "Downloading from Zoom...",  // or "Uploading to YouTube...", etc.
       "timestamp": "2026-02-02T10:06:00Z"
     }
     Frontend Action:
     - Update status badge to PROCESSING with animated spinner
     - Show progress message in expandable row details
     - Update in real-time as backend progresses through steps
  
  4. recording_error
     Payload: {
       "type": "recording_error",
       "zoom_id": "12345678",
       "error": "YouTube upload failed: Quota exceeded",
       "timestamp": "2026-02-02T10:10:00Z"
     }
     Frontend Action:
     - Update status to ERROR
     - Show error toast: "Processing failed: [error message]"
     - Add to Errors tab
     - Show retry button (if applicable)
  
  5. service_status_changed
     Payload: {
       "type": "service_status_changed",
       "status": "running",  // or "stopped"
       "timestamp": "2026-02-02T10:00:00Z"
     }
     Frontend Action:
     - Update service status indicator (green/red)
     - Show toast: "Background service [started/stopped]"
     - Update service control panel
  
  6. new_log_entry
     Payload: {
       "type": "new_log_entry",
       "log": {
         "timestamp": "2026-02-02T10:05:30Z",
         "level": "INFO",  // or "WARNING", "ERROR"
         "logger": "BackgroundService",
         "message": "Processing recording 12345678..."
       }
     }
     Frontend Action:
     - Append to Logs tab (if currently viewing)
     - Auto-scroll to bottom
     - Highlight ERROR level logs in red
     - Update error count badge if level is ERROR
  
  7. stats_updated
     Payload: {
       "type": "stats_updated",
       "stats": {
         "pending": 3,
         "completed": 15,
         "processing": 2,
         "errors": 1
       },
       "timestamp": "2026-02-02T10:05:00Z"
     }
     Frontend Action:
     - Update all stats cards immediately
     - Animate number changes (count up/down animation)
     - Update trend indicators
  
  Connection Management:
  - Show "Connected" indicator (green dot) when WebSocket is open
  - Show "Connecting..." (yellow dot) when reconnecting
  - Show "Disconnected" (red dot) when connection lost
  - Auto-reconnect with exponential backoff (2s, 4s, 8s, 16s, 32s max)
  - Max 5 reconnection attempts, then show error banner
  - Reconnect immediately when network comes back online
  - Send ping/pong every 30s to keep connection alive

=== ERROR HANDLING ===

- Network errors: Show "Connection lost" banner
- 401 Unauthorized: Redirect to login
- 403 Forbidden: Show "Admin access required" toast
- 500 Server Error: Show error toast with retry button
- WebSocket disconnect: Show reconnecting indicator
- API timeout: Show timeout message after 30s

=== PERFORMANCE ===

- Lazy load components
- Debounce search inputs (300ms)
- Throttle WebSocket events (100ms)
- Virtualize long lists (react-window)
- Memoize expensive computations
- Code splitting by route

=== ACCESSIBILITY ===

- Semantic HTML
- ARIA labels for interactive elements
- Keyboard navigation
- Focus indicators
- Screen reader friendly
- Color contrast WCAG AA compliant

=== FILE STRUCTURE ===

src/
├── main.tsx                 # Entry point
├── App.tsx                  # Root component with routing
├── index.css                # Global styles + design system
├── pages/
│   ├── Login.tsx            # Login page
│   └── Dashboard.tsx        # Main dashboard
├── components/
│   ├── Navbar.tsx           # Top navigation
│   ├── ServicePanel.tsx     # Service control panel
│   ├── StatsCards.tsx       # Statistics cards
│   ├── QueueTab.tsx         # Pending recordings table
│   ├── HistoryTab.tsx       # Completed recordings table
│   ├── LogsTab.tsx          # System logs viewer
│   ├── ErrorsTab.tsx        # Error logs viewer
│   ├── ApprovalModal.tsx    # Approval confirmation modal
│   ├── Toast.tsx            # Toast notification
│   └── LoadingSpinner.tsx   # Loading indicator
├── context/
│   ├── AuthContext.tsx      # Authentication state
│   ├── WebSocketContext.tsx # WebSocket connection
│   └── ToastContext.tsx     # Toast notifications
├── hooks/
│   ├── useAuth.ts           # Auth hook
│   ├── useWebSocket.ts      # WebSocket hook
│   ├── useApi.ts            # API fetching hook
│   └── useToast.ts          # Toast hook
├── services/
│   ├── api.ts               # API client
│   └── websocket.ts         # WebSocket client
├── types/
│   └── index.ts             # TypeScript interfaces
└── utils/
    ├── formatters.ts        # Date/time formatters
    └── constants.ts         # App constants

=== DEPLOYMENT CONSIDERATIONS ===

- Environment variables:
  * VITE_API_BASE_URL (default: http://localhost:8000)
  * VITE_WS_URL (default: ws://localhost:8000/ws)
  * VITE_GOOGLE_CLIENT_ID (for OAuth)

- Build command: npm run build
- Preview command: npm run preview
- Dev command: npm run dev

- Firebase Hosting configuration:
  * Public directory: dist
  * SPA rewrite: index.html
  * CORS headers for API calls

=== GOOGLE OAUTH SETUP ===

1. Use Google Identity Services (new library)
2. Load script: https://accounts.google.com/gsi/client
3. Initialize with client ID
4. Handle credential response
5. Send ID token to backend /auth/login
6. Store session token from backend
7. Use session token for all API calls

Example OAuth button:
```html
<div id="g_id_onload"
     data-client_id="YOUR_CLIENT_ID"
     data-callback="handleCredentialResponse">
</div>
<div class="g_id_signin" data-type="standard"></div>
```

=== ADDITIONAL REQUIREMENTS ===

- Add favicon and app icons
- Add meta tags for SEO
- Add loading screen on initial load
- Add offline detection
- Add session timeout warning (30 min)
- Add "Last updated" timestamp on data
- Add refresh button on each tab
- Add export to CSV for history
- Add dark mode toggle (bonus)

=== TESTING CHECKLIST ===

Before deployment, verify:
- [ ] Login with Google OAuth works
- [ ] Demo mode works
- [ ] All tabs load correctly
- [ ] Approval flow works end-to-end
- [ ] WebSocket connects and receives updates
- [ ] Service control buttons work (admin only)
- [ ] Logs stream in real-time
- [ ] Error handling shows appropriate messages
- [ ] Mobile responsive (test on phone)
- [ ] Logout clears session
- [ ] Auto-redirect on 401
- [ ] Toast notifications appear
- [ ] Loading states show correctly

=== DESIGN INSPIRATION ===

Look at these for inspiration:
- Vercel Dashboard (clean, modern)
- Linear App (smooth animations)
- Stripe Dashboard (professional, data-focused)
- Notion (minimal, functional)

=== FINAL NOTES ===

- Prioritize USER EXPERIENCE over feature completeness
- Make it FAST and RESPONSIVE
- Use SMOOTH ANIMATIONS (but not excessive)
- Keep it SIMPLE and INTUITIVE
- Make it look PROFESSIONAL and PREMIUM
- Ensure it's ACCESSIBLE
- Make it DELIGHTFUL to use

Build this as a production-ready application that will WOW users on first impression!
```

---

## 🎨 Design System Reference

### Colors

```css
:root {
  /* Primary Colors */
  --primary-50: #EEF2FF;
  --primary-100: #E0E7FF;
  --primary-500: #4F46E5;
  --primary-600: #4338CA;
  --primary-700: #3730A3;
  
  /* Success */
  --success-50: #ECFDF5;
  --success-500: #10B981;
  --success-600: #059669;
  
  /* Warning */
  --warning-50: #FFFBEB;
  --warning-500: #F59E0B;
  --warning-600: #D97706;
  
  /* Error */
  --error-50: #FEF2F2;
  --error-500: #EF4444;
  --error-600: #DC2626;
  
  /* Neutral */
  --gray-50: #F9FAFB;
  --gray-100: #F3F4F6;
  --gray-200: #E5E7EB;
  --gray-300: #D1D5DB;
  --gray-400: #9CA3AF;
  --gray-500: #6B7280;
  --gray-600: #4B5563;
  --gray-700: #374151;
  --gray-800: #1F2937;
  --gray-900: #111827;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-fast: 150ms ease-in-out;
  --transition-base: 200ms ease-in-out;
  --transition-slow: 300ms ease-in-out;
}
```

### Component Examples

**Button:**
```css
.btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: all var(--transition-base);
  cursor: pointer;
  border: none;
  font-size: 14px;
}

.btn-primary {
  background: var(--primary-500);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
```

**Card:**
```css
.card {
  background: white;
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-md);
}
```

**Status Badge:**
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 500;
}

.badge-success {
  background: var(--success-50);
  color: var(--success-600);
}

.badge-error {
  background: var(--error-50);
  color: var(--error-600);
}

.badge-warning {
  background: var(--warning-50);
  color: var(--warning-600);
}
```

---

## 🔌 WebSocket Integration Example

```typescript
// src/services/websocket.ts
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private listeners: Map<string, Function[]> = new Map();

  connect(url: string) {
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected', null);
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.emit(data.type, data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.emit('disconnected', null);
      this.reconnect(url);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };
  }

  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  off(event: string, callback: Function) {
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
      callbacks.forEach(cb => cb(data));
    }
  }

  private reconnect(url: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect(url);
      }, 2000 * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketService();
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile First */
/* Base styles for mobile (< 640px) */

/* Tablet */
@media (min-width: 640px) {
  /* sm */
}

@media (min-width: 768px) {
  /* md */
}

/* Desktop */
@media (min-width: 1024px) {
  /* lg */
}

@media (min-width: 1280px) {
  /* xl */
}
```

---

## 🎯 Success Criteria

Your frontend is AMAZING if:
- ✅ Loads in < 2 seconds
- ✅ Smooth 60fps animations
- ✅ Works perfectly on mobile
- ✅ Real-time updates feel instant
- ✅ No layout shifts
- ✅ Accessible (keyboard + screen reader)
- ✅ Looks professional and premium
- ✅ Intuitive to use (no learning curve)
- ✅ Error states are helpful
- ✅ Users say "WOW!" on first load

---

## 🚀 Ready to Build!

Copy the main prompt section and paste it into Google IDX or Firebase Studio. The AI will build you a production-ready, stunning frontend that connects seamlessly to your backend!

**Good luck! 🎨✨**
