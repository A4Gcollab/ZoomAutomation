
from fastapi import FastAPI, HTTPException, Header, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
from src.db_sql import db
from src.auth import verify_google_token
from src import config
from contextlib import asynccontextmanager
from typing import Optional, List
import os
from src.main import BackgroundService

log_file = config.DATA_DIR / "app.log"
bg_service: Optional[BackgroundService] = None

# Logging - must be before lifespan
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bg_service
    logger.info("=" * 60)
    logger.info("API STARTUP - Initializing Background Service")
    logger.info("=" * 60)
    
    # Auto-start on boot
    try:
        logger.info("Creating BackgroundService instance...")
        bg_service = BackgroundService()
        
        logger.info("Starting BackgroundService thread...")
        bg_service.start()
        
        # Verify it actually started
        import time
        time.sleep(0.5)  # Give it a moment to start
        
        if bg_service.is_alive():
            logger.info("✅ Background Service Thread Started Successfully (In-Process)")
            logger.info(f"   Thread ID: {bg_service.ident}")
            logger.info(f"   Daemon: {bg_service.daemon}")
            logger.info(f"   Running: {bg_service.running}")
        else:
            logger.error("❌ Background Service Thread FAILED to start!")
            logger.error("   Thread is not alive after start() call")
            
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"CRITICAL: Failed to start background service thread")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        logger.error("=" * 60)
        
    yield
    
    # Shutdown logic
    logger.info("API SHUTDOWN - Stopping Background Service")
    if bg_service:
        bg_service.running = False
        logger.info("Background Service stop signal sent")

app = FastAPI(title="VONG Automation V2", lifespan=lifespan)

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DEPENDENCIES ---
def get_current_user(x_token: str = Header(...)):
    """Verify user authentication. All authenticated users allowed."""
    user = verify_google_token(x_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Authentication")
    return user

def require_admin(user: dict = Depends(get_current_user)):
    """Require admin role for sensitive operations."""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# --- ROUTES ---

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/login")
def login(token_data: dict = Body(...)):
    """Convert Google ID Token to Session verification."""
    token = token_data.get('token')
    user = verify_google_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return {"token": token, "user": user, "status": "Login Successful"}

@app.get("/stats")
def get_stats(user: dict = Depends(get_current_user)):
    return db.get_stats()

@app.get("/queue")
def get_queue(user: dict = Depends(get_current_user)):
    return db.get_pending()

@app.get("/history")
def get_history(user: dict = Depends(get_current_user)):
    return db.get_history()

@app.get("/options")
def get_options(user: dict = Depends(get_current_user)):
    return db.get_options()

@app.post("/approve/{zoom_id}")
def approve_recording(zoom_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user)):
    team = payload.get("team")
    playlist = payload.get("playlist")
    
    if not team or not playlist:
        raise HTTPException(status_code=400, detail="Team and Playlist are required.")
    
    db.update_recording(zoom_id, {
        "team": team,
        "playlist": playlist,
        "status": "APPROVED",
        "approved_by": user['email']
    })
    return {"status": "Approved"}

@app.get("/logs")
def get_logs(lines: int = 100, level: str = None):
    """Get system logs with optional filtering by level (INFO, WARNING, ERROR)"""
    if not os.path.exists(log_file):
        return {"logs": [{"timestamp": "", "level": "INFO", "message": "Log file not found."}]}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Parse logs into structured format
        structured_logs = []
        for line in recent_lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to parse log format: "2026-01-31 20:33:24,613 - Main - INFO - Message"
            try:
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    timestamp = parts[0]
                    logger_name = parts[1]
                    log_level = parts[2]
                    message = parts[3]
                    
                    # Filter by level if specified
                    if level and log_level != level:
                        continue
                    
                    structured_logs.append({
                        "timestamp": timestamp,
                        "level": log_level,
                        "logger": logger_name,
                        "message": message
                    })
                else:
                    # Fallback for unparsed lines
                    structured_logs.append({
                        "timestamp": "",
                        "level": "INFO",
                        "logger": "System",
                        "message": line
                    })
            except Exception:
                # If parsing fails, add as raw message
                structured_logs.append({
                    "timestamp": "",
                    "level": "INFO",
                    "logger": "System",
                    "message": line
                })
        
        return {"logs": structured_logs, "total": len(structured_logs)}
        
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return {"logs": [{"timestamp": "", "level": "ERROR", "message": f"Error reading logs: {e}"}], "total": 0}

@app.get("/errors")
def get_errors(lines: int = 50):
    """Get only ERROR level logs"""
    return get_logs(lines=lines * 3, level="ERROR")  # Fetch more to get enough errors

@app.post("/sync")
def trigger_sync(user: dict = Depends(get_current_user)):
    # Manual sync trigger could set an event in bg_service if needed
    # For now loop runs every 60s
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

# --- IN-PROCESS SERVICE MANAGEMENT ---

@app.get("/service/status")
def get_service_status():
    global bg_service
    # If thread is alive, it's running
    is_running = bg_service is not None and bg_service.is_alive()
    logger.info(f"Service status check: bg_service={bg_service}, is_alive={bg_service.is_alive() if bg_service else 'N/A'}, is_running={is_running}")
    return {
        "status": "running" if is_running else "stopped",
        "running": is_running,
        "uptime": 0, # Could track start time
        "last_heartbeat": None
    }

@app.get("/service/health")
def get_service_health():
    return get_service_status()

@app.post("/service/start")
def start_service(user: dict = Depends(get_current_user)):
    global bg_service
    if bg_service and bg_service.is_alive():
        return {"success": True, "message": "Service already running"}
    
    try:
        bg_service = BackgroundService()
        bg_service.start()
        logger.info("Service Started via API")
        return {"success": True, "message": "Service started"}
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/service/stop")
def stop_service(user: dict = Depends(require_admin)):
    global bg_service
    if bg_service:
        bg_service.running = False
        # Thread will exit loop
        return {"success": True, "message": "Service stopping..."}
    return {"success": True, "message": "Service was not running"}

@app.post("/service/restart")
def restart_service(user: dict = Depends(require_admin)):
    stop_service(user)
    # Wait briefly? Not blocking API.
    # Start new one
    try:
        start_service(user)
        return {"success": True, "message": "Service restarted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


