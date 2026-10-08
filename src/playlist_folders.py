"""
Playlist to Google Drive Folder Mapping
Maps YouTube playlist names to their corresponding Google Drive folder IDs
"""

# Mapping of playlist names to Google Drive VIDEO folder IDs
PLAYLIST_FOLDER_MAPPING = {
    "AI Training session for Sankles": "1lX2dwZT3OX-2p35hdH5OfJVTaEoexM9e",
    "2.2.1 Marketing and PR": "13pSMIo4Qso1BToFSP8lRmRukLQiPnETN",
    "2.2.2 Growth": "1B7aQNscLGkz7jDPiRPt5FF8CGUifHFvm",
    "2.2.3 Research Analysis Bureau RAB": "13FZuXmvh3I_WPn8dKGhCIHQDIAgRfjz5",
    "2.2.4 Tech Systems and Products": "1eWxD6uZdvF1Gk9byHl4aB71DyH7mWSWs",
    "2.2.5 Enablers - HR/OPM": "1LRE1-1zW_1sKtPjX_7xrlb5OmPE3jBhP",
    "2.2.5 Enablers - PM": "1-ZdSCOUKHozKaMjCz5RqJkjr0tSKCwaR",
    "2.2.6 community building CB": "16KiC87V_40yFGe2zp4170HaH-tx2pp4K",
    "2.2.5 Enablers": "1KuMKFhbPzMoPdfAIlJitrI5BZEsd9-3Q",
    "Essay Contest": "1_qj6pUo93aHp0ffBhjDkZMBLuP_Gpo30",
    "General Meetings": "17vqCD1aXLdWh7PBhUKRaBNcB0C7wihpv",
    "Townhall": "1cRC-sMGdU4oYh8g5cenHI-YzYw9Zy5A5",
    "omysha alignment meeting": "1Uyj8PsEbCA-8obySdnE5VFNnrTCJSDBC",
    "sponsorship and fundraising": "16KiC87V_40yFGe2zp4170HaH-tx2pp4K",
    "Miscellaneous": "1hSsWll8tSZ1MvOpObt4IeQnpBy_JQLtW",
    "Exit interview": "1Af4ngqwQ22MSeaDPC5DTC_oymbWmNMGv"
}

# Mapping of playlist names to Google Drive TRANSCRIPT folder IDs
TRANSCRIPT_FOLDER_MAPPING = {
    "AI Training session for Sankles": "1IHNq_SHaLXN6IwGcTV-AIVW61LWfZRdT",
    "2.2.1 Marketing and PR": "1Z-u6SpvGuHRp-sSesmGcHfO4SWXZcsX_",
    "2.2.2 Growth": "1nW-5ZdbgBjaNMYbdNuV1QziwGAAso-Wr",
    "2.2.3 Research Analysis Bureau RAB": "13SUptwBQ1iL8lqEMWbVDnpemVugXQ5MA",
    "2.2.4 Tech Systems and Products": "1gPWSqLGRV7pZ8cqGOyMwMFb94eNjANZy",
    "2.2.5 Enablers - HR/OPM": "1ekdVgcqqrGCnZLCUegw4Y79dkc_-wGkB",
    "2.2.5 Enablers - PM": "1lz4L0josi7NXnwZSdxApGF1gJPW1KZFH",
    "2.2.6 community building CB": "1slLMUwbjqGMwRGeX_Gc1XRP5jVYoPTze",
    "2.2.5 Enablers": "132wTjgl9UuN6-qedka_LcbcQBkb5NSm7",
    "Essay Contest": "1PGococ2OOJn3KCEekIa-Y2_oF8HKdV81",
    "General Meetings": "1vIMx-FiqoxmN5scG9a4jJbKDN02piJ-7",
    "Townhall": "1Rwn_IB8yPhkPT4oFin28KIhcgjLAcTKT",
    "omysha alignment meeting": "1ViCmRYXbbE2gGCKYkhr3iHaNURcYfQuD",
    "sponsorship and fundraising": "1slLMUwbjqGMwRGeX_Gc1XRP5jVYoPTze",
    "Miscellaneous": "1qYyOYdYJ2EsewD-o7x6whRsRrlmb-6zp",
    "Exit interview": "1gVu02dlS_lcCz5sbYZtotNlMLmbaZWD4"

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
