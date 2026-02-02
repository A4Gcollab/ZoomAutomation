#!/usr/bin/env python3
"""
Service Manager - Robust process control for background service
Handles start/stop/restart with proper error handling and health monitoring
"""
import os
import sys
import time
import signal
import psutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("ServiceManager")

class ServiceManager:
    def __init__(self, script_path="debug_main.py", pid_file=".service.pid", lock_file=".lock"):
        self.cwd = Path(os.getcwd()).resolve()
        self.script_path = self.cwd / script_path
        self.pid_file = self.cwd / pid_file
        self.lock_file = self.cwd / lock_file
        self.health_file = self.cwd / ".health"
        
    def get_pid(self):
        """Get PID from file if exists"""
        if self.pid_file.exists():
            try:
                return int(self.pid_file.read_text().strip())
            except:
                return None
        return None
    
    def is_running(self):
        """Check if service is actually running"""
        pid = self.get_pid()
        if not pid:
            # Scan specifically for our script by name/cmdline
            # This is more robust than PID file which desyncs frequently
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info.get('cmdline') or []
                        cmdline_str = ' '.join(cmdline).lower()
                        if ('python' in proc.info['name'].lower() and 
                            ('main.py' in cmdline_str or 'debug_main.py' in cmdline_str)):
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return False
            except Exception:
                return False
        
        try:
            # Trust PID existence if process exists (cmdline check can be flaky on Windows/wrappers)
            psutil.Process(pid) # Check if PID actually exists
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_health(self):
        """Get service health status"""
        if not self.is_running():
            return {
                "status": "stopped",
                "running": False,
                "last_heartbeat": None,
                "uptime": 0
            }
        
        # Read health file
        health_data = {
            "status": "running",
            "running": True,
            "last_heartbeat": None,
            "uptime": 0,
            "last_cycle": None,
            "error_count": 0
        }
        
        if self.health_file.exists():
            try:
                import json
                health_data.update(json.loads(self.health_file.read_text()))
            except:
                pass
        
        # Calculate uptime
        pid = self.get_pid()
        if pid:
            try:
                process = psutil.Process(pid)
                create_time = datetime.fromtimestamp(process.create_time())
                health_data["uptime"] = int((datetime.now() - create_time).total_seconds())
            except:
                pass
        
        return health_data
    
    def start(self):
        """Start the background service"""
        if self.is_running():
            logger.warning("Service is already running")
            return {"success": False, "message": "Service is already running"}
        
        # Clean up stale files
        self._cleanup_stale_files()
        
        # Start process
        try:
            import subprocess
            # Windows-specific flags to detach process
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            
            process = subprocess.Popen(
                [sys.executable, str(self.script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait a bit to see if it starts successfully
            time.sleep(2)
            
            if self.is_running():
                logger.info(f"Service started successfully (PID: {self.get_pid()})")
                return {"success": True, "message": "Service started", "pid": self.get_pid()}
            else:
                # Capture stderr to see why it failed
                try:
                    _, stderr = process.communicate(timeout=1)
                    error_msg = stderr.decode() if stderr else "Unknown error"
                except:
                    error_msg = "Process exited immediately"
                    
                logger.error(f"Service failed to start: {error_msg}")
                return {"success": False, "message": f"Service failed to start: {error_msg}"}
                
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return {"success": False, "message": str(e)}
    
    def stop(self, force=False):
        """Stop the background service"""
        if not self.is_running():
            self._cleanup_stale_files()
            return {"success": True, "message": "Service is not running"}
        
        pid = self.get_pid()
        try:
            process = psutil.Process(pid)
            
            if force:
                # Force kill
                process.kill()
                logger.info(f"Force killed service (PID: {pid})")
            else:
                # Graceful shutdown
                process.terminate()
                # Wait up to 10 seconds for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f"Service stopped gracefully (PID: {pid})")
                except psutil.TimeoutExpired:
                    # Force kill if it doesn't stop
                    process.kill()
                    logger.warning(f"Service force killed after timeout (PID: {pid})")
            
            # Cleanup
            self._cleanup_stale_files()
            return {"success": True, "message": "Service stopped"}
            
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            self._cleanup_stale_files()
            return {"success": False, "message": str(e)}
    
    def restart(self):
        """Restart the service"""
        logger.info("Restarting service...")
        stop_result = self.stop()
        if not stop_result["success"]:
            return stop_result
        
        time.sleep(1)  # Brief pause
        return self.start()
    
    def _cleanup_stale_files(self):
        """Remove stale PID and lock files"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
            if self.lock_file.exists():
                self.lock_file.unlink()
            logger.info("Cleaned up stale files")
        except Exception as e:
            logger.error(f"Failed to cleanup files: {e}")

# Singleton instance
service_manager = ServiceManager()

if __name__ == "__main__":
    # CLI interface
    import argparse
    
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Service Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "health"])
    parser.add_argument("--force", action="store_true", help="Force stop")
    
    args = parser.parse_args()
    
    if args.action == "start":
        result = service_manager.start()
        print(result["message"])
        sys.exit(0 if result["success"] else 1)
        
    elif args.action == "stop":
        result = service_manager.stop(force=args.force)
        print(result["message"])
        sys.exit(0 if result["success"] else 1)
        
    elif args.action == "restart":
        result = service_manager.restart()
        print(result["message"])
        sys.exit(0 if result["success"] else 1)
        
    elif args.action == "status":
        running = service_manager.is_running()
        print(f"Service is {'running' if running else 'stopped'}")
        if running:
            print(f"PID: {service_manager.get_pid()}")
        sys.exit(0 if running else 1)
        
    elif args.action == "health":
        health = service_manager.get_health()
        import json
        print(json.dumps(health, indent=2))
        sys.exit(0)
