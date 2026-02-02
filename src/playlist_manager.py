import json
import logging
from pathlib import Path

logger = logging.getLogger("PlaylistManager")

class PlaylistManager:
    def __init__(self, config_path):
        """
        Initialize playlist manager with configuration file.
        
        Args:
            config_path: Path to playlists.json configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.playlist_cache = {}
        
    def _load_config(self):
        """Load playlist configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Basic Schema Validation
            if not isinstance(data, dict):
                raise ValueError("Config root must be a dictionary")
            
            if 'playlists' in data and not isinstance(data['playlists'], list):
                 raise ValueError("'playlists' must be a list")
            
            # Validate individual mappings if they exist
            for idx, mapping in enumerate(data.get('playlists', [])):
                if 'playlist_id' not in mapping:
                    logger.warning(f"Playlist mapping at index {idx} missing 'playlist_id'. Skipping.")
                if 'playlist_name' not in mapping:
                    logger.warning(f"Playlist mapping at index {idx} missing 'playlist_name'.")
            
            return data
            
        except FileNotFoundError:
            logger.error(f"Playlist configuration not found at {self.config_path}")
            return {"playlists": [], "default_playlist_id": None, "default_category": "General"}
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Invalid configuration in {self.config_path}: {e}")
            return {"playlists": [], "default_playlist_id": None, "default_category": "General"}
    
    def find_playlist(self, video_title, zoom_id=None):
        """
        Find the best matching playlist for a video.
        Prioritizes Zoom Meeting ID match, then title keywords.
        
        Args:
            video_title: Title of the video
            zoom_id: Zoom Meeting ID (optional)
            
        Returns:
            dict: {
                'playlist_id': str,
                'playlist_name': str,
                'category': str,
                'confidence': float (0-1)
            }
        """
        title_lower = video_title.lower()
        zoom_id_str = str(zoom_id) if zoom_id else ""
        
        # 1. Check for exact Zoom Meeting ID match
        if zoom_id_str:
            for mapping in self.config.get('playlists', []):
                if zoom_id_str in mapping.get('meeting_ids', []):
                    logger.info(f"Found exact match for Zoom ID {zoom_id_str} -> {mapping.get('playlist_name')}")
                    return {
                        'playlist_id': mapping.get('playlist_id'),
                        'playlist_name': mapping.get('playlist_name'),
                        'category': mapping.get('category', 'General'),
                        'confidence': 1.0
                    }

        # 2. Strict Mode - No Keyword Fallback
        # User requested to remove keyword matching ("keywords thingy")
        logger.warning(f"No exact match found for Zoom ID: {zoom_id_str}. Keyword matching is disabled.")
        
        return {
            'playlist_id': self.config.get('default_playlist_id'),
            'playlist_name': 'Default',
            'category': self.config.get('default_category', 'General'),
            'confidence': 0.0
        }
    
    def find_playlist_by_name(self, name):
        """
        Find playlist details by exact or partial name match (from Sheet dropdown).
        """
        if not name: return {'playlist_id': None}
        
        name_lower = name.lower().strip()
        
        for p in self.config.get('playlists', []):
            if p.get('playlist_name', '').lower() == name_lower:
                return {
                    'playlist_id': p.get('playlist_id'),
                    'playlist_name': p.get('playlist_name'),
                    'category': p.get('category', 'General')
                }
        
        return {'playlist_id': None}

    def should_create_new_playlist(self, video_title, match_result):
        """
        Determine if a new playlist should be created based on match confidence.
        
        Args:
            video_title: Title of the video
            match_result: Result from find_playlist()
            
        Returns:
            dict or None: Suggested playlist details if should create, None otherwise
        """
        # Only suggest new playlist if auto-creation is enabled and confidence is very low
        if not self.config.get('auto_create_playlists', False):
            return None
        
        if match_result['confidence'] > 0.2:
            return None
        
        # Try to extract category from title
        # Look for patterns like "Finance Meeting", "Legal Discussion", etc.
        title_lower = video_title.lower()
        
        # Common meeting type keywords
        meeting_types = ['meeting', 'discussion', 'review', 'sync', 'call', 'session']
        
        for meeting_type in meeting_types:
            if meeting_type in title_lower:
                # Extract word before meeting type
                parts = title_lower.split(meeting_type)[0].strip().split()
                if parts:
                    suggested_category = parts[-1].title()
                    
                    # Check if this category already exists
                    exact_match_exists = any(
                        m.get('category', '').lower() == suggested_category.lower()
                        for m in self.config.get('playlists', [])
                    )
                    
                    if not exact_match_exists:
                        return {
                            'category': suggested_category,
                            'suggested_name': f"2.2.X Omysha {suggested_category}",
                            'keywords': [suggested_category.lower(), f"{suggested_category.lower()} {meeting_type}"]
                        }
        
        return None
    
    def add_playlist_to_config(self, playlist_id, playlist_name, category, keywords):
        """
        Add a new playlist to the configuration file.
        
        Args:
            playlist_id: YouTube playlist ID
            playlist_name: Name of the playlist
            category: Category for Drive organization
            keywords: List of keywords for matching
        """
        new_mapping = {
            'playlist_id': playlist_id,
            'playlist_name': playlist_name,
            'category': category,
            'meeting_ids': [],
            'keywords': keywords
        }
        
        if 'playlists' not in self.config:
            self.config['playlists'] = []
            
        self.config['playlists'].append(new_mapping)
        
        # Save updated configuration
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Added new playlist to configuration: {playlist_name}")
        except Exception as e:
            logger.error(f"Failed to update playlist configuration: {e}")
