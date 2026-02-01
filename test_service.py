
import sys
import os
import time
from service_manager import service_manager

print("--- Testing Service Start ---")
print(f"Current CWD: {os.getcwd()}")
print(f"Script Path: {service_manager.script_path}")
print(f"Script Exists: {service_manager.script_path.exists()}")

# Clean up first
service_manager.stop(force=True)
time.sleep(1)

# Try Start
print("\nAttempting Start...")
result = service_manager.start()
print(f"Start Result: {result}")

if result['success']:
    print("\nService Started. Checking process...")
    time.sleep(2)
    running = service_manager.is_running()
    print(f"Is Running: {running}")
    if running:
        print("Test Passed! Stopping service...")
        service_manager.stop()
    else:
        print("Test FAILED: Service claimed start but is not running.")
else:
    print("Test FAILED: Start command reported failure.")
