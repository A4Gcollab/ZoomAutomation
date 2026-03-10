
import sys
import os
import traceback
import logging

# Configure basic logging to file immediately
logging.basicConfig(filename='crash.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    print("Attempting to import main...")
    logging.info("Attempting to import main...")
    import main
    print("Import successful. Running main.main()...")
    logging.info("Import successful. Running main.main()...")
    
    # Run main logic
    main.main()
    
except Exception:
    error_msg = traceback.format_exc()
    print(f"CRASH: {error_msg}")
    logging.critical(f"CRASH:\n{error_msg}")
    sys.exit(1)
