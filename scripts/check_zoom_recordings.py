import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src import config
from src.zoom_client import ZoomClient

def check_zoom_recordings():
    print("="*60)
    print("🎥 ZOOM RECORDING DIAGNOSTIC TOOL")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check Config
    print("\n[1] Configuration Check:")
    accounts = config.ZOOM_ACCOUNTS
    if not accounts:
        print("❌ No Zoom accounts found in configuration.")
        print("   Please ensure ZOOM_1_ACCOUNT_ID, ZOOM_1_CLIENT_ID, ZOOM_1_CLIENT_SECRET are set in .env")
        return

    print(f"✅ Found {len(accounts)} configured Zoom account(s).")

    # 2. Scan Accounts
    print("\n[2] Scanning Accounts...")
    
    # Search range: Last 90 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    print(f"   Date Range: {start_date} to {end_date}")

    total_recordings_found = 0

    for acc in accounts:
        name = acc.get('name', 'Unknown')
        print(f"\n   🔍 Checking {name}...")
        
        try:
            client = ZoomClient(acc)
            users = list(client.get_all_users())
            print(f"      Found {len(users)} user(s).")
            
            for user in users:
                user_email = user.get('email', 'unknown')
                print(f"      👤 Scanning user: {user_email}...")
                
                # Fetch recordings
                recs = client.get_user_recordings(user['id'], start_date, end_date)
                
                if recs:
                    print(f"         ✅ Found {len(recs)} recording(s):")
                    for r in recs:
                        duration = r.get('duration', 0)
                        size_mb = r.get('total_size', 0) / (1024*1024)
                        print(f"            - [{r['start_time'][:10]}] ID: {r['id']} | {r['topic']} ({duration}m, {size_mb:.1f}MB)")
                    total_recordings_found += len(recs)
                else:
                    print(f"         ⚠️  No recordings found for this user.")
                    
        except Exception as e:
            print(f"      ❌ Failed to connect/scan {name}: {e}")

    print("\n" + "="*60)
    print(f"TOTAL RECORDINGS FOUND: {total_recordings_found}")
    print("="*60)

if __name__ == "__main__":
    check_zoom_recordings()
