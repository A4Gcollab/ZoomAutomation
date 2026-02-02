import requests

try:
    response = requests.get("http://localhost:8000/service/status")
    print(f"Service Status: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
