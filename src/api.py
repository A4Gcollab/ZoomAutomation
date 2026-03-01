
from fastapi import FastAPI, HTTPException, Header, Depends, Body, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
import traceback
from src.db_sql import db
from src.auth import verify_google_token
from src import config
from contextlib import asynccontextmanager
import os
from src.main import BackgroundService
from datetime import datetime
import time
import psutil

# Import new modules
from src.websocket_manager import manager as ws_manager
from src.metrics import get_metrics, api_requests, api_latency, recordings_processed, active_websockets, background_service_status
from src.cache import cache

log_file = config.DATA_DIR / "app.log"
bg_service: Optional[BackgroundService] = None
_service_start_time: Optional[float] = None

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bg_service, _service_start_time
    logger.info("=" * 60)
    logger.info("API STARTUP - Initializing Background Service")
    logger.info("=" * 60)

    try:
        bg_service = BackgroundService()
        bg_service.start()
        time.sleep(0.5)

        if bg_service.is_alive():
            _service_start_time = time.time()
            logger.info("Background Service Thread Started Successfully")
            background_service_status.set(1)
        else:
            logger.error("Background Service Thread FAILED to start!")
            background_service_status.set(0)

    except Exception as e:
        logger.error(f"CRITICAL: Failed to start background service: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        background_service_status.set(0)

    yield

    # Shutdown
    logger.info("API SHUTDOWN - Stopping Background Service")
    if bg_service:
        bg_service.running = False
        background_service_status.set(0)


app = FastAPI(
    title="YTZ Automation API",
    description="YouTube-Zoom Automation System",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Metrics Middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        api_requests.labels(endpoint=request.url.path, method=request.method).inc()
        api_latency.labels(endpoint=request.url.path).observe(duration)
        return response
    except Exception as e:
        logger.error(f"Request error {request.url.path}: {e}")
        raise


# --- DEPENDENCIES ---
def get_current_user(x_token: str = Header(...)):
    """Verify user authentication."""
    try:
        user = verify_google_token(x_token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid Authentication")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication error")


def require_admin(user: dict = Depends(get_current_user)):
    """Require admin role for sensitive operations."""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# --- ROUTES ---

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/health/detailed")
def detailed_health():
    """Detailed system health check"""
    try:
        # Database check
        db_healthy = True
        try:
            db.get_stats()
        except Exception as e:
            db_healthy = False
            logger.error(f"Database health check failed: {e}")

        # Background service check
        service_healthy = bg_service is not None and bg_service.is_alive()

        # Disk space check
        try:
            disk = psutil.disk_usage('/')
            disk_healthy = disk.percent < 90
            disk_info = {
                "status": "ok" if disk_healthy else "warning",
                "used_percent": round(disk.percent, 2),
                "free_gb": round(disk.free / (1024 ** 3), 2)
            }
        except Exception:
            disk_healthy = True
            disk_info = {"status": "unknown"}

        # Memory check
        try:
            memory = psutil.virtual_memory()
            memory_healthy = memory.percent < 90
            memory_info = {
                "status": "ok" if memory_healthy else "warning",
                "used_percent": round(memory.percent, 2),
                "available_gb": round(memory.available / (1024 ** 3), 2)
            }
        except Exception:
            memory_healthy = True
            memory_info = {"status": "unknown"}

        overall_status = "healthy" if all([
            db_healthy, service_healthy, disk_healthy, memory_healthy
        ]) else "degraded"

        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "ok" if db_healthy else "error",
                "background_service": "ok" if service_healthy else "error",
                "disk_space": disk_info,
                "memory": memory_info,
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    try:
        from prometheus_client import CONTENT_TYPE_LATEST
        return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return Response(content="# Error generating metrics", media_type="text/plain")


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "message": "Connection alive"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.post("/auth/login")
def login(token_data: dict = Body(...)):
    """Convert Google ID Token to Session verification."""
    token = token_data.get('token')
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    user = verify_google_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return {"token": token, "user": user, "status": "Login Successful"}


@app.get("/stats")
def get_stats(user: dict = Depends(get_current_user)):
    try:
        cached_stats = cache.get("stats")
        if cached_stats:
            return cached_stats
        stats = db.get_stats()
        cache.set("stats", stats, ttl_seconds=30)
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"completed": 0, "pending": 0, "errors": 0, "processing": 0, "approved": 0}


@app.get("/queue")
def get_queue(user: dict = Depends(get_current_user)):
    try:
        return db.get_pending()
    except Exception as e:
        logger.error(f"Queue error: {e}")
        return []


@app.get("/history")
def get_history(limit: int = 50, user: dict = Depends(get_current_user)):
    try:
        return db.get_history(limit)
    except Exception as e:
        logger.error(f"History error: {e}")
        return []


@app.get("/options")
def get_options(user: dict = Depends(get_current_user)):
    try:
        return db.get_options()
    except Exception as e:
        logger.error(f"Options error: {e}")
        return {"teams": [], "playlists": []}


@app.post("/approve/{zoom_id:path}")
async def approve_recording(zoom_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user)):
    team = payload.get("team")
    playlist = payload.get("playlist")

    if not team or not playlist:
        raise HTTPException(status_code=400, detail="Team and Playlist are required.")

    try:
        # First approve the specific recording
        db.update_recording(zoom_id, {
            "team": team,
            "playlist": playlist,
            "status": "APPROVED",
            "approved_by": user['email']
        })

        # Then bulk-approve ALL other pending instances of the same recurring meeting
        meeting_id = db.get_meeting_id_for_zoom_id(zoom_id)
        bulk_count = 0
        if meeting_id:
            bulk_count = db.bulk_approve_by_meeting_id(meeting_id, team, playlist, user['email'])

        # Invalidate cache
        cache.delete("stats")
        cache.delete("queue")

        # Broadcast update
        try:
            await ws_manager.broadcast({
                "type": "recording_approved",
                "zoom_id": zoom_id,
                "approved_by": user['email'],
                "team": team,
                "playlist": playlist,
                "bulk_count": bulk_count,
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass  # WebSocket broadcast is non-critical

        return {"status": "Approved", "bulk_approved": bulk_count}
    except Exception as e:
        logger.error(f"Approve error for {zoom_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve: {str(e)}")


@app.get("/logs")
def get_logs(lines: int = 100, level: str = None):
    """Get system logs with optional filtering by level"""
    if not os.path.exists(log_file):
        return {"logs": [], "total": 0}

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        structured_logs = []
        for line in recent_lines:
            line = line.strip()
            if not line:
                continue

            try:
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    timestamp = parts[0]
                    logger_name = parts[1]
                    log_level = parts[2].strip()
                    message = parts[3]

                    if level and log_level != level:
                        continue

                    structured_logs.append({
                        "timestamp": timestamp,
                        "level": log_level,
                        "logger": logger_name,
                        "message": message
                    })
                else:
                    structured_logs.append({
                        "timestamp": "",
                        "level": "INFO",
                        "logger": "System",
                        "message": line
                    })
            except Exception:
                structured_logs.append({
                    "timestamp": "",
                    "level": "INFO",
                    "logger": "System",
                    "message": line
                })

        return {"logs": structured_logs, "total": len(structured_logs)}

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return {"logs": [], "total": 0}


@app.get("/errors")
def get_errors(lines: int = 50):
    """Get only ERROR level logs"""
    return get_logs(lines=lines * 3, level="ERROR")


@app.post("/sync")
def trigger_sync(user: dict = Depends(get_current_user)):
    return {"status": "Sync Initiated (Loop runs every 60s)"}


@app.get("/sheets-url")
def get_sheets_url(user: dict = Depends(get_current_user)):
    sheet_id = config.GOOGLE_SHEET_ID
    if not sheet_id:
        raise HTTPException(status_code=404, detail="Google Sheets not configured")
    return {
        "url": f"https://docs.google.com/spreadsheets/d/{sheet_id}",
        "sheet_id": sheet_id
    }


# --- SERVICE MANAGEMENT ---

@app.get("/service/status")
def get_service_status():
    global bg_service, _service_start_time
    is_running = bg_service is not None and bg_service.is_alive()
    uptime = 0
    if is_running and _service_start_time:
        uptime = int(time.time() - _service_start_time)
    return {
        "status": "running" if is_running else "stopped",
        "running": is_running,
        "uptime": uptime,
        "last_heartbeat": datetime.now().isoformat() if is_running else None
    }


@app.get("/service/health")
def get_service_health():
    return get_service_status()


@app.post("/service/start")
def start_service(user: dict = Depends(get_current_user)):
    global bg_service, _service_start_time
    if bg_service and bg_service.is_alive():
        return {"success": True, "message": "Service already running"}

    try:
        bg_service = BackgroundService()
        bg_service.start()
        _service_start_time = time.time()
        logger.info("Service Started via API")
        background_service_status.set(1)
        return {"success": True, "message": "Service started"}
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/service/stop")
def stop_service(user: dict = Depends(get_current_user)):
    global bg_service, _service_start_time
    if bg_service:
        bg_service.running = False
        _service_start_time = None
        background_service_status.set(0)
        return {"success": True, "message": "Service stopping..."}
    return {"success": True, "message": "Service was not running"}


@app.post("/service/restart")
def restart_service(user: dict = Depends(get_current_user)):
    global bg_service, _service_start_time

    # Stop current service
    if bg_service:
        bg_service.running = False
        # Wait for it to stop (max 5s)
        for _ in range(10):
            if not bg_service.is_alive():
                break
            time.sleep(0.5)

    # Start new one
    try:
        bg_service = BackgroundService()
        bg_service.start()
        _service_start_time = time.time()
        background_service_status.set(1)
        logger.info("Service Restarted via API")
        return {"success": True, "message": "Service restarted"}
    except Exception as e:
        logger.error(f"Failed to restart service: {e}")
        background_service_status.set(0)
        raise HTTPException(status_code=500, detail=str(e))
