
import sys
import os
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)

# 1. Load Config
from src.config import GOOGLE_WEB_CLIENT_ID
print(f"Config Client ID: {GOOGLE_WEB_CLIENT_ID}")

# 2. Test Auth Module
from src.auth import verify_google_token

# Simulate a token (this will fail verification but should trigger our debug logs)
fake_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImZhIn0.eyJhdWQiOiJWRVJZX0RJR0ZFUkVOVF9JRCIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsImVtYWlsIjoieW9nZXNoQG9teXNoYS5jb20ifQ.signature"

print("\n--- Testing with Fake Token ---")
result = verify_google_token(fake_token)
print(f"Result: {result}")
