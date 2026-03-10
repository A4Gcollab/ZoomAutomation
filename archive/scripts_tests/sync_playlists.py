import json
import logging
import sys
from pathlib import Path
from src.youtube_client import YouTubeClient
from src import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("SyncPlaylists")

def sync_ids():
    logger.info("Starting Playlist Sync...")
    
    # 1. Initialize Client
    try:
        yt = YouTubeClient(config.YOUTUBE_CLIENT_SECRET_PATH, config.YOUTUBE_TOKEN_PATH)
    except Exception as e:
        logger.error(f"Failed to initialize YouTube Client: {e}")
        logger.error("Please ensure secrets/client_secret.json and secrets/token.json help exist.")
        return

    # 2. Fetch all YouTube Playlists
    logger.info("Fetching your YouTube playlists...")
    yt_playlists = yt.get_playlists()
    logger.info(f"Found {len(yt_playlists)} playlists on YouTube.")
    
    # Map Title -> ID for easy lookup
    # Clean titles: strip whitespace, lower case for comparison
    yt_map = {p['title'].strip().lower(): p['id'] for p in yt_playlists}
    
    # 3. Load Config
    config_path = config.PLAYLIST_CONFIG_PATH
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    updated_count = 0
    missing_count = 0
    
    # 4. Match and Update
    for entry in data.get('playlists', []):
        target_name = entry.get('playlist_name', '').strip()
        current_id = entry.get('playlist_id')
        
        if not target_name:
            continue
            
        # Check match
        match_id = yt_map.get(target_name.lower())
        
        if match_id:
            if current_id != match_id:
                entry['playlist_id'] = match_id
                logger.info(f"MATCHED: '{target_name}' -> {match_id}")
                updated_count += 1
            else:
                logger.info(f"Verified: '{target_name}' already set.")
        else:
            logger.warning(f"MISSING: Could not find playlist '{target_name}' on YouTube. Creating it...")
            
            # Auto-create
            try:
                playlist_id = yt.create_playlist(target_name, f"Auto-created for {entry['category']}", "unlisted")
                entry['playlist_id'] = playlist_id
                logger.info(f"CREATED: {target_name} -> {playlist_id}")
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to create playlist {target_name}: {e}")

    # 5. Save Config
    if updated_count > 0:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Successfully updated {updated_count} IDs in config!")
    else:
        logger.info("No changes needed.")
        
    if missing_count > 0:
        logger.warning(f"{missing_count} playlists defined in config do not exist on YouTube.")

if __name__ == "__main__":
    sync_ids()
