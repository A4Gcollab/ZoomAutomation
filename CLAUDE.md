# CLAUDE.md — YTZ Automation

## What This Project Does

Automated Zoom cloud recording pipeline for A4G Collab/Omysha. It scans Zoom accounts for new recordings, compresses them via YouTube's encoding, backs up to Google Drive, logs to Google Sheets, and deletes originals after a 24-hour safety delay. A Next.js dashboard provides admin control.

## 3-Phase Pipeline

1. **Scan** — Poll multiple Zoom accounts for new recordings, insert into SQLite as PENDING
2. **Process** — Download MP4+VTT from Zoom → upload to YouTube (unlisted) → download compressed → upload to Google Drive → log to Sheets
3. **Cleanup** — Delete original Zoom recording after 24h verification delay

## Tech Stack

- **Backend:** Python 3.10+, FastAPI, SQLite, threading-based background service
- **Frontend:** Next.js 15+, TypeScript, Tailwind CSS, Radix UI, Firebase Auth
- **APIs:** Zoom (Server-to-Server OAuth), YouTube Data v3, Google Drive v3, Google Sheets v4
- **Deployment:** Docker, Nginx reverse proxy, systemd on Vultr VPS (Ubuntu 22.04)

## Project Layout

```
src/                  # Python backend
  main.py             # BackgroundService orchestrator (3-phase pipeline)
  api.py              # FastAPI server, REST routes, WebSocket
  config.py           # Env loading, dynamic multi-account detection
  zoom_client.py      # Zoom OAuth + recording API
  youtube_client.py   # Upload, playlist, captions
  drive_client.py     # Folder nav, file upload (user or service account)
  db_sql.py           # SQLite singleton (thread-safe)
  sheets_integration.py # Google Sheets audit trail
  auth.py             # Firebase/Google token verification
  playlist_manager.py # Playlist CRUD from config
  playlist_folders.py # Keyword-to-playlist matching
  monitor.py          # Disk space, cleanup scheduling
  cache.py            # In-memory TTL cache
  websocket_manager.py # WebSocket connection pool
  metrics.py          # Prometheus counters/gauges
  utils.py            # Retry decorator, filename sanitization, date parsing
  yt_downloader.py    # yt-dlp wrapper
frontend/             # Next.js React dashboard
  src/app/            # Pages: dashboard, login, youtube, drive, settings
  src/components/     # UI components (Radix-based)
  src/firebase/       # Firebase config, auth hooks, provider
config/
  playlists.json      # Playlist mappings (keywords, YouTube IDs, Drive folder IDs)
scripts/              # Setup & deployment (deploy.sh, setup_youtube.py, etc.)
tests/                # test_utils.py (minimal coverage)
data/                 # SQLite DB (vong_v2.db), app.log
secrets/              # OAuth tokens/credentials (git-ignored)
```

## Key Commands

```bash
# Run backend (dev)
python main.py
# or via uvicorn
uvicorn src.api:app --host 0.0.0.0 --port 8000

# Run frontend (dev)
cd frontend && npm run dev

# Docker
docker-compose up --build

# Deploy to VPS
sudo ./scripts/deploy.sh

# Run tests
python -m pytest tests/
```

## Configuration

- `.env` file at project root (see `.env.example` for template)
- Multi-account Zoom: `ZOOM_1_ACCOUNT_ID`, `ZOOM_1_CLIENT_ID`, `ZOOM_1_CLIENT_SECRET` (increment number for more accounts)
- YouTube OAuth tokens stored as pickle files in `secrets/`
- Drive auth supports both `user` and `service_account` modes via `DRIVE_AUTH_MODE`
- Playlist routing configured in `config/playlists.json` (keywords, meeting IDs)

## Database

SQLite at `data/vong_v2.db`. Key table: `recordings` with status flow:
`PENDING → PENDING_PLAYLIST → APPROVED → PROCESSING → COMPLETED`
(or `ERROR` with retry). Also `system_logs` table for log entries.

## Conventions

- Backend entry point is `main.py` at root, which imports from `src/main.py`
- FastAPI app is at `src/api.py` (`src.api:app`)
- All Google API auth flows use pickle token files in `secrets/`
- Frontend uses Firebase Auth (email + Google Sign-In), backend validates tokens in `src/auth.py`
- Prometheus metrics exposed at `/metrics`, health checks at `/health` and `/health/detailed`
- WebSocket at `/ws` for real-time dashboard updates
- Logs rotate at 5MB, 3 backups, stored in `data/app.log`

## Important Notes

- Never commit `secrets/` directory or `.env` files
- YouTube compression is the core strategy — avoids local FFmpeg cost
- 24-hour delete delay is a safety feature; don't reduce without understanding the risk
- `config/playlists.json` drives both YouTube playlist and Drive folder routing
- SQLite DB uses a thread-safe singleton pattern — don't create additional connections
- Frontend deployed via Firebase App Hosting (`apphosting.yaml`)
