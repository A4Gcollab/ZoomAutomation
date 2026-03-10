import os
import sys
import time
from pathlib import Path
from src.config import DATA_DIR

LOCK_FILE = DATA_DIR / "app.lock"

def acquire_lock():
    """
    Tries to acquire a lock by creating a file.
    If the file exists and is older than 2 hours, it deletes it (stale lock).
    """
    if LOCK_FILE.exists():
        # Check if stale (older than 2 hours)
        creation_time = LOCK_FILE.stat().st_mtime
        if time.time() - creation_time > 7200:
            print("Found stale lock file. Removing...")
            try:
                LOCK_FILE.unlink()
            except OSError:
                print("Could not remove stale lock.")
                sys.exit(1)
        else:
            print("Another instance is running. Exiting.")
            sys.exit(0)

    try:
        LOCK_FILE.touch()
    except OSError:
        print("Could not create lock file.")
        sys.exit(1)

def release_lock():
    """Removes the lock file."""
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass
