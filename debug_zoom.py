import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

account_id = os.getenv("ZOOM_1_ACCOUNT_ID", "").strip().strip('"').strip("'")
client_id = os.getenv("ZOOM_1_CLIENT_ID", "").strip().strip('"').strip("'")
client_secret = os.getenv("ZOOM_1_CLIENT_SECRET", "").strip().strip('"').strip("'")

print(f"DEBUG: Account ID: {account_id}")
print(f"DEBUG: Client ID:  {client_id[:4]}...{client_id[-4:]}")
print(f"DEBUG: Secret:     {client_secret[:4]}...{client_secret[-4:]}")

url = "https://zoom.us/oauth/token"
auth_str = f"{client_id}:{client_secret}"
b64_auth = base64.b64encode(auth_str.encode()).decode()

headers = {
    "Authorization": f"Basic {b64_auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}

params = {
    "grant_type": "account_credentials",
    "account_id": account_id
}

print(f"Params: {params}")

# Attempt 1: Query Params
print("\n--- ATTEMPT 1: Query Params ---")
try:
    resp = requests.post(url, headers=headers, params=params)
    print(f"Status Code: {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(f"EXCEPTION: {e}")

# Attempt 2: Form Body
print("\n--- ATTEMPT 2: Form Body ---")
try:
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    resp = requests.post(url, headers=headers, data=params)
    print(f"Status Code: {resp.status_code}")
    print(resp.text)
except Exception as e:
    print(f"EXCEPTION: {e}")
