import json
from pathlib import Path

def extract_ids():
    db_path = Path("data/db.json")
    if not db_path.exists():
        print("No database found.")
        return

    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        recordings = data.get('recordings', {})
        
        print("\n--- FOUND MEETING IDs IN HISTORY ---")
        print(f"{'MEETING ID':<15} | {'TOPIC'}")
        print("-" * 60)
        
        seen_ids = set()
        
        for key, rec in recordings.items():
            zoom_id = rec.get('zoom_id')
            # Metadata might be nested or direct depending on schema version
            meta = rec.get('metadata', {})
            topic = meta.get('topic', 'Unknown Topic')
            
            if zoom_id not in seen_ids:
                print(f"{zoom_id:<15} | {topic}")
                seen_ids.add(zoom_id)
                
        print("-" * 60)
        print("Copy these IDs to map them to playlists.\n")
        
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    extract_ids()
