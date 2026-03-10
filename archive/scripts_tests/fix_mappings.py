import json
import codecs
from src.youtube_client import YouTubeClient
from src import config

# Clean mappings (Config Name -> Correct YouTube Playlist ID)
MAPPING = {
    "2.2.5 Enablers - HR": "PL8yNrvcL-DjwrYWKnTtOSnJ5LJPZwscme", # Maps to 2.2.5 Enablers - HR/OPM
    "2.2.4 Tech Systems and Products": "PL8yNrvcL-DjwbjZIPWHGwgWQ3e5sKYwwd",
    "2.2.1 Marketing": "PL8yNrvcL-DjwPNaFACH_V9mxKlKvkFEhS", # Maps to 2.2.1 Marketing & PR
    "2.2.2 Growth": "PL8yNrvcL-DjyA7HYNGB5XGihg7QwdaKRf",
    "2.2.5 Enablers - PM": "PL8yNrvcL-DjxMxtZkxt_sdJOuPUnCxgtu",
    "2.2.3 Research Analysis Bureau RAB": "PL8yNrvcL-Djzh6H5tNeTARMk1sZ7eBUtE",
    "2.2.6 Community Building": "PL8yNrvcL-DjzTc_gdhyDv0ll4x1HRmNPw",
    "2.2.5 Enablers - OPM & HR": "PL8yNrvcL-DjwrYWKnTtOSnJ5LJPZwscme", # Combine with HR/OPM
    "Essay Contest": "PL8yNrvcL-DjysA8ZgYj2OjxNWyhunGPPE",
    "2.2.5 Enablers": "PL8yNrvcL-DjxNkZzqIMpRO6j3vEsfnewS", # Map generic to Miscellaneous
    "Townhall": "PL8yNrvcL-Djxwt1gQZscBUA1qWYG3u28u",
    "omysha alignment meeting": "PL8yNrvcL-DjwX0cc2jvtlUdtBXnFT2MSj", # Maps to Omysha Alignment meetings
    "sponsorship and fundraising": "PL8yNrvcL-DjxEzsS3QI5r3LUrXayIgMoJ" # Maps to A4G Horizons Sponsership...
}

# Auto-created IDs to delete
TO_DELETE = [
    "PL8yNrvcL-DjzVH-1XYss842Re6xbyrBt1", # sponsorship and fundraising
    "PL8yNrvcL-Djzh5emwNL6YC135M0e3Rv3a", # omysha alignment meeting
    "PL8yNrvcL-DjylHED5-fcb1r76L_KfzoV_", # 2.2.5 Enablers
    "PL8yNrvcL-DjwDB7PouRWIuCL6e_PoG4Bp", # 2.2.5 Enablers - OPM & HR
    "PL8yNrvcL-Djy1xLD-3sAWE-3wa6_OOTSI", # 2.2.1 Marketing
    "PL8yNrvcL-DjwPu-5w4-NhpDwivFlbuRC1"  # 2.2.5 Enablers - HR
]

def main():
    print("Deleting duplicate playlists...")
    yt = YouTubeClient(config.YOUTUBE_CLIENT_SECRET_PATH, config.YOUTUBE_TOKEN_PATH)
    for pid in TO_DELETE:
        try:
            yt.youtube.playlists().delete(id=pid).execute()
            print(f"Deleted playlist {pid}")
        except Exception as e:
            print(f"Failed to delete {pid}: {e}")

    print("Updating config/playlists.json...")
    with codecs.open("config/playlists.json", "r", "utf-8") as f:
        data = json.load(f)

    for p in data["playlists"]:
        name = p["playlist_name"]
        if name in MAPPING:
            p["playlist_id"] = MAPPING[name]
    
    data["default_playlist_id"] = "PL8yNrvcL-DjxNkZzqIMpRO6j3vEsfnewS" # Miscellaneous

    with codecs.open("config/playlists.json", "w", "utf-8") as f:
        json.dump(data, f, indent=2)

    print("Success")

if __name__ == "__main__":
    main()
