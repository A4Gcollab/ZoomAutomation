
import os
import sys
from src.zoom_client import ZoomClient
from src import config
from datetime import datetime, timedelta

def count_unique():
    now = datetime.now()
    start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    
    unique_ids = set()
    
    for i, acc in enumerate(config.ZOOM_ACCOUNTS, 1):
        client = ZoomClient(acc)
        try:
            for user in client.get_all_users():
                recs = client.get_user_recordings(user['id'], start_date, today)
                for r in recs:
                    unique_ids.add(str(r['id']))
        except Exception as e:
            print(f"Error {i}: {e}")
            
    print(f"Total Unique Meeting IDs: {len(unique_ids)}")

if __name__ == "__main__":
    count_unique()
