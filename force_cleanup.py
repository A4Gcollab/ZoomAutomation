
# Start of file
import os
import sys
from pathlib import Path

# Correct path based on src/lock.py view
LOCK_FILE = Path("data/app.lock")
PID_FILE = Path(".service.pid")
HEALTH_FILE = Path(".health")

print("--- Force Cleanup ---")

if LOCK_FILE.exists():
    try:
        LOCK_FILE.unlink()
        print("Removed .lock file")
    except Exception as e:
        print(f"Error removing .lock: {e}")
else:
    print(".lock file not found")

if PID_FILE.exists():
    try:
        PID_FILE.unlink()
        print("Removed .service.pid file")
    except Exception as e:
        print(f"Error removing .service.pid: {e}")
else:
    print(".service.pid file not found")
    
if HEALTH_FILE.exists():
    try:
        HEALTH_FILE.unlink()
        print("Removed .health file")
    except Exception as e:
        print(f"Error removing .health: {e}")
else:
    print(".health file not found")
    
print("Cleanup complete.")
