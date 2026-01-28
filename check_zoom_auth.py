import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

def test_auth(account_num):
    acc_id = os.getenv(f"ZOOM_{account_num}_ACCOUNT_ID")
    client_id = os.getenv(f"ZOOM_{account_num}_CLIENT_ID")
    client_secret = os.getenv(f"ZOOM_{account_num}_CLIENT_SECRET")
    
    print(f"\n--- Testing Account {account_num} ---")
    
    if not (acc_id and client_id and client_secret):
        print("MISSING credentials in .env")
        return
        
    print(f"Account ID: {acc_id[:4]}...{acc_id[-4:] if len(acc_id)>4 else ''}")
    print(f"Client ID:  {client_id[:4]}...{client_id[-4:] if len(client_id)>4 else ''}")
    # Don't print secret
    
    url = "https://zoom.us/oauth/token"
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {b64_auth}"
    }
    query_params = {
        "grant_type": "account_credentials",
        "account_id": acc_id
    }
    
    try:
        resp = requests.post(url, headers=headers, params=query_params)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            print("[SUCCESS] Token received.")
            data = resp.json()
            print(f"Scope: {data.get('scope')}")
        else:
            print("[FAILED]!")
            print(f"Response: {resp.text}")
            
    except Exception as e:
        print(f"[EXCEPTION]: {e}")

if __name__ == "__main__":
    print("Checking Zoom Credentials independently...")
    test_auth(1)
    test_auth(2)
