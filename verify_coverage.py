import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

class SimpleZoom:
    def __init__(self):
        self.acc_id = os.getenv("ZOOM_1_ACCOUNT_ID")
        self.client_id = os.getenv("ZOOM_1_CLIENT_ID")
        self.client_secret = os.getenv("ZOOM_1_CLIENT_SECRET")
        self.token = None

    def auth(self):
        url = "https://zoom.us/oauth/token"
        auth_str = f"{self.client_id}:{self.client_secret}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}"
        }
        params = {"grant_type": "account_credentials", "account_id": self.acc_id}
        resp = requests.post(url, headers=headers, params=params)
        resp.raise_for_status()
        self.token = resp.json()['access_token']
        print("[SUCCESS] Zoom Account 1 Authenticated")

    def get_users(self):
        url = "https://api.zoom.us/v2/users?page_size=300&status=active"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            users = resp.json().get('users', [])
            print(f"\n[FOUND] {len(users)} Active Users under Account 1:")
            for u in users:
                print(f"  - Name: {u.get('first_name')} {u.get('last_name')}")
                print(f"    Email: {u.get('email')}")
                print(f"    PMI (Personal Meeting ID): {u.get('pmi')}")
                # We can also check scheduled meetings here if needed, but PMI is key for "Codes"
            return users
        else:
            print(f"[ERROR] listing users: {resp.text}")
            return []

if __name__ == "__main__":
    z = SimpleZoom()
    try:
        z.auth()
        z.get_users()
    except Exception as e:
        print(f"[ERROR] {e}")
