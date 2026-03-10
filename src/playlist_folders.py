"""
Playlist to Google Drive Folder Mapping
Maps YouTube playlist names to their corresponding Google Drive folder IDs
"""

# Mapping of playlist names to Google Drive VIDEO folder IDs
PLAYLIST_FOLDER_MAPPING = {
    "2.2.1 Marketing": "1KuMKFhbPzMoPdfAIlJitrI5BZEsd9-3Q",
    "2.2.2 Growth": "1eWxD6uZdvF1Gk9byHl4aB71DyH7mWSWs",
    "2.2.3 Research Analysis Bureau RAB": "1B7aQNscLGkz7jDPiRPt5FF8CGUifHFvm",
    "2.2.4 Tech Systems and Products": "1-ZdSCOUKHozKaMjCz5RqJkjr0tSKCwaR",
    "2.2.5 Enablers - HR": "1m9YBC8GQ7yeB0cwAkgtyopAMzwYRb4Tp",
    "2.2.5 Enablers - PM": "13FZuXmvh3I_WPn8dKGhCIHQDIAgRfjz5",
    "2.2.5 Enablers - OPM & HR": "1Tn5ZlkTimYJYyjxH3B_eeJLbnF4T0B6N",
    "2.2.6 Community Building": "13pSMIo4Qso1BToFSP8lRmRukLQiPnETN",
    "Essay Contest": "13otF9gCQahMvGaEF18mXYeKOd5Zp3EXJ",
    "2.2.5 Enablers": "1LRE1-1zW_1sKtPjX_7xrlb5OmPE3jBhP",
    "Tech": "1eWxD6uZdvF1Gk9byHl4aB71DyH7mWSWs",
    "Growth": "1B7aQNscLGkz7jDPiRPt5FF8CGUifHFvm",
    "Marketing": "1KuMKFhbPzMoPdfAIlJitrI5BZEsd9-3Q",
    "HR": "1m9YBC8GQ7yeB0cwAkgtyopAMzwYRb4Tp",
    "PM": "13FZuXmvh3I_WPn8dKGhCIHQDIAgRfjz5",
    "RAB": "1B7aQNscLGkz7jDPiRPt5FF8CGUifHFvm",
    "Community": "13pSMIo4Qso1BToFSP8lRmRukLQiPnETN",
    "Enablers": "1LRE1-1zW_1sKtPjX_7xrlb5OmPE3jBhP",
}

# Mapping of playlist names to Google Drive TRANSCRIPT folder IDs
TRANSCRIPT_FOLDER_MAPPING = {
    "2.2.1 Marketing": "1gPWSqLGRV7pZ8cqGOyMwMFb94eNjANZy",
    "2.2.2 Growth": "13SUptwBQ1iL8lqEMWbVDnpemVugXQ5MA",
    "2.2.3 Research Analysis Bureau RAB": "1Z-u6SpvGuHRp-sSesmGcHfO4SWXZcsX_",
    "2.2.4 Tech Systems and Products": "1x1ds_HHcLlMM3peBg7UqNWltYjusOfKd",
    "2.2.5 Enablers - HR": "1ekdVgcqqrGCnZLCUegw4Y79dkc_-wGkB",
    "2.2.5 Enablers - PM": "1nW-5ZdbgBjaNMYbdNuV1QziwGAAso-Wr",
    "2.2.5 Enablers - OPM & HR": "1vIMx-FiqoxmN5scG9a4jJbKDN02piJ-7",
    "2.2.6 Community Building": "1lz4L0josi7NXnwZSdxApGF1gJPW1KZFH",
    "Essay Contest": "1PGococ2OOJn3KCEekIa-Y2_oF8HKdV81",
    "2.2.5 Enablers": "1PGococ2OOJn3KCEekIa-Y2_oF8HKdV81",
    "Tech": "1x1ds_HHcLlMM3peBg7UqNWltYjusOfKd",
    "Growth": "13SUptwBQ1iL8lqEMWbVDnpemVugXQ5MA",
    "Marketing": "1gPWSqLGRV7pZ8cqGOyMwMFb94eNjANZy",
    "PM": "1nW-5ZdbgBjaNMYbdNuV1QziwGAAso-Wr",
    "RAB": "1Z-u6SpvGuHRp-sSesmGcHfO4SWXZcsX_",
    "Community": "1lz4L0josi7NXnwZSdxApGF1gJPW1KZFH",
}

def get_drive_folder_id(playlist_name: str, for_transcript: bool = False) -> str:
    """
    Get the Google Drive folder ID for a given playlist name.
    Supports exact match and case-insensitive partial matching.
    
    Args:
        playlist_name: The name of the playlist
        for_transcript: If True, return transcript folder ID, else video folder ID
        
    Returns:
        Google Drive folder ID or None if not found
    """
    mapping = TRANSCRIPT_FOLDER_MAPPING if for_transcript else PLAYLIST_FOLDER_MAPPING
    
    # Try exact match first
    if playlist_name in mapping:
        return mapping[playlist_name]
    
    # Try case-insensitive match
    playlist_lower = playlist_name.lower().strip()
    for key, folder_id in mapping.items():
        if key.lower().strip() == playlist_lower:
            return folder_id
    
    # Try partial match (e.g., "Tech" matches "2.2.4 Tech Systems and Products")
    for key, folder_id in mapping.items():
        if playlist_lower in key.lower() or key.lower() in playlist_lower:
            return folder_id
    
    return None
