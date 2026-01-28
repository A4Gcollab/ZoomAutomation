import os
import logging
from dotenv import load_dotenv
from src.zoom_client import ZoomClient
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.ERROR)

def check_zoom():
    load_dotenv()
    print("\n" + "="*80)
    print("ZOOM ID DISCOVERY TOOL v2")
    print("="*80)
    
    # Check Account 1 & 2
    for idx in [1, 2]:
        acc_id = os.getenv(f"ZOOM_{idx}_ACCOUNT_ID")
        if not acc_id:
            continue
            
        print(f"\nScanning Account {idx} (ID: {acc_id})...")
        
        try:
            creds = {
                'account_id': acc_id,
                'client_id': os.getenv(f"ZOOM_{idx}_CLIENT_ID"),
                'client_secret': os.getenv(f"ZOOM_{idx}_CLIENT_SECRET"),
                'name': f"Acct{idx}"
            }
            client = ZoomClient(creds)
            
            # 1. Get Users
            users = list(client.get_all_users())
            print(f"Found {len(users)} Users.")
            
            for user in users:
                uid = user['id']
                email = user['email']
                pmi = user.get('pmi', 'N/A')
                print(f"  User: {email} (PMI: {pmi})")
                
                # 2. Check Recordings (Last 30 days)
                to_date = datetime.now().strftime('%Y-%m-%d')
                from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                try:
                    recs = client.get_user_recordings(uid, from_date, to_date)
                    print(f"    - Found {len(recs)} recent recordings.")
                    seen_ids = set()
                    for r in recs:
                        mid = str(r.get('id', 'Unknown'))
                        topic = r.get('topic', 'Unknown')
                        if mid not in seen_ids:
                            print(f"      [RECORDING] ID: {mid:<12} | Topic: {topic}")
                            seen_ids.add(mid)
                except Exception as e:
                    print(f"    - Error fetching recordings: {e}")

                # 3. Try Scheduled Meetings (might fail scope)
                try:
                    meetings = client.get_user_meetings(uid)
                    print(f"    - Found {len(meetings)} scheduled meetings.")
                    for m in meetings:
                        mid = str(m.get('id', 'Unknown'))
                        topic = m.get('topic', 'Unknown')
                        print(f"      [MEETING]   ID: {mid:<12} | Topic: {topic}")
                except Exception as e:
                    pass # Expected if scope missing
                    
        except Exception as e:
            print(f"Failed to connect to Account {idx}: {e}")
            
    print("\n" + "="*80)

if __name__ == "__main__":
    check_zoom()
