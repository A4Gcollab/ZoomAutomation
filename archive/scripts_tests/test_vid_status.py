from src.youtube_client import YouTubeClient
from src.config import SECRETS_DIR

yt = YouTubeClient(SECRETS_DIR / "client_secret.json", SECRETS_DIR / "token.json")
response = yt.youtube.videos().list(
    part="status,snippet",
    id="OeiNITZwUUzo"
).execute()

for item in response.get("items", []):
    print("Title:", item["snippet"]["title"])
    print("Status:", item["status"]["uploadStatus"])
    print("Rejection:", item["status"].get("rejectionReason", "None"))
    print("Privacy:", item["status"]["privacyStatus"])
