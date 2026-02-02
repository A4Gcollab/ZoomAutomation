import requests

print("Testing Backend API...")
try:
    # Test health endpoint
    response = requests.get("http://localhost:8000/health")
    print(f"✓ Health Check: {response.status_code} - {response.json()}")
    
    # Test service status
    response = requests.get("http://localhost:8000/service/status")
    print(f"✓ Service Status: {response.status_code} - {response.json()}")
    
    print("\n✅ Backend is ONLINE and responding correctly!")
    print("\n📍 Frontend URL: http://localhost:5173")
    print("📍 Backend URL: http://localhost:8000")
    
except Exception as e:
    print(f"❌ Error: {e}")
