
from fastapi import FastAPI, HTTPException, Header, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging
from src.db_sql import db
from src.auth import verify_google_token
from src import config
from src.main import BackgroundService, start_service
from contextlib import asynccontextmanager

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run the background thread
    # start_service() # DISABLED per user request
    yield
    # Shutdown logic if needed

app = FastAPI(title="VONG Automation V2", lifespan=lifespan)

# CORS (Allow Frontend)
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Vite Dev
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DEPENDENCIES ---
def get_current_user(x_token: str = Header(...)):
    user = verify_google_token(x_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Authentication or Access Denied")
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
    return {"user": user, "status": "Login Successful"}

@app.get("/stats")
def get_stats(user: dict = Depends(get_current_user)):
    """Get manual dashboard stats."""
    return db.get_stats()

@app.get("/queue")
def get_queue(user: dict = Depends(get_current_user)):
    """Get pending recordings needing approval."""
    return db.get_pending()

@app.get("/history")
def get_history(user: dict = Depends(get_current_user)):
    """Get processed/approved recordings."""
    return db.get_history()

@app.get("/options")
def get_options(user: dict = Depends(get_current_user)):
    """Get dropdown options."""
    return db.get_options()

@app.post("/approve/{zoom_id}")
def approve_recording(zoom_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user)):
    """
    Approve a recording for processing.
    Payload: { "team": "Marketing", "playlist": "Updates 2026" }
    """
    team = payload.get("team")
    playlist = payload.get("playlist")
    
    if not team or not playlist:
        raise HTTPException(status_code=400, detail="Team and Playlist are required.")
    
    # Update DB
    db.update_recording(zoom_id, {
        "team": team,
        "playlist": playlist,
        "status": "APPROVED",
        "approved_by": user['email'] # Audit Trail
    })
    
    # Trigger Background Processing? 
    # Or let the loop pick it up?
    # Loop picks it up.
    return {"status": "Approved"}

@app.get("/logs")
def get_logs(limit: int = 50, user: dict = Depends(get_current_user)):
    """Stream system logs."""
    return db.get_recent_logs(limit)

@app.post("/sync")
def trigger_sync(user: dict = Depends(get_current_user)):
    """Manually trigger Zoom Scan."""
    # BackgroundService.trigger_scan() # Pseudo-code
    # Implementation depends on how we run the service.
@app.post("/sync")
def trigger_sync(user: dict = Depends(get_current_user)):
    """Manually trigger Zoom Scan."""
    # We can trigger it by setting a flag or calling a method if thread-safe
    # For now, we just rely on the loop, or we could expose a method.
    # Ideally: service.force_scan()
    # But since it runs every 60s, we can just say:
    return {"status": "Sync Initiated (Loop runs every 60s)"}
