
import time
from service_manager import service_manager
import sys

print("--- Force Starting Service ---")
# Ensure we are in correct dir
# service_manager handles paths now

try:
    if service_manager.is_running():
        print("Service already running.")
    else:
        print("Starting service...")
        result = service_manager.start()
        print(f"Start Result: {result}")
        
        # Verify
        time.sleep(2)
        if service_manager.is_running():
            print("SUCCESS: Service is running.")
        else:
            print("FAILURE: Service did not stay running.")
            sys.exit(1)
            
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
