
import psutil
import os
import signal
import sys

print("--- Zombie Hunter ---")
my_pid = os.getpid()
killed_count = 0

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.pid == my_pid:
            continue
            
        cmdline = proc.info['cmdline']
        if cmdline and 'python' in proc.info['name'].lower():
            # Check for our scripts
            if any(s in ' '.join(cmdline) for s in ['main.py', 'debug_main.py', 'uvicorn']):
                print(f"Found Zombie: PID={proc.pid} Cmd={' '.join(cmdline)}")
                try:
                    proc.kill()
                    print(f"Killed PID {proc.pid}")
                    killed_count += 1
                except Exception as e:
                    print(f"Failed to kill {proc.pid}: {e}")
                    
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

# Force remove lock files
for f in [".lock", "data/app.lock", ".service.pid", ".health"]:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"Removed stale file: {f}")
        except Exception as e:
            print(f"Error removing {f}: {e}")

print(f"Hunt Complete. Killed {killed_count} zombies.")
