
import requests
import sys

try:
    print("Checking API Health...")
    r = requests.get('http://localhost:8000/service/status')
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
    
    if r.status_code == 200:
        print("API is accessible.")
        data = r.json()
        print(f"Service Status: {data.get('status')}")
    else:
        print("API returned error.")
        sys.exit(1)
        
except Exception as e:
    print(f"Setup Error: {e}")
    sys.exit(1)
