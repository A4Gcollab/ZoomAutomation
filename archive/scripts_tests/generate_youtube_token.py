"""
Generate YouTube OAuth Token Locally.

Run this script on your local machine (which has a browser) to generate
the YouTube OAuth token. Then SCP the token file to the production server.

Usage:
    python generate_youtube_token.py

After running:
    scp secrets/token_youtube.json root@139.84.133.1:/root/ytz-automation/secrets/token_youtube.json
"""
import os
import sys
import pickle

sys.path.insert(0, '.')

import google_auth_oauthlib.flow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

CLIENT_SECRET_PATH = os.path.join("secrets", "client_secret.json")
TOKEN_PATH = os.path.join("secrets", "token_youtube.json")


def main():
    print("=" * 80)
    print("YouTube OAuth Token Generator")
    print("=" * 80)
    print()
    print("This script will open your browser to log into Google and grant YouTube access.")
    print(f"It will save the OAuth token to '{TOKEN_PATH}'.")
    print()

    if not os.path.exists(CLIENT_SECRET_PATH):
        print(f"ERROR: Client secret file not found at: {CLIENT_SECRET_PATH}")
        print("Please download it from Google Cloud Console and place it there.")
        sys.exit(1)

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_PATH, SCOPES
    )

    # Run local server — opens browser for OAuth consent
    credentials = flow.run_local_server(port=0)

    # Save credentials as pickle (same format YouTubeClient expects)
    with open(TOKEN_PATH, "wb") as token_file:
        pickle.dump(credentials, token_file)

    print()
    print("=" * 80)
    print("SUCCESS! YouTube token saved to:", TOKEN_PATH)
    print()
    print("The token includes a refresh_token, so it will auto-renew and should")
    print("never need to be regenerated unless you revoke access.")
    print()
    print("Now SCP this file to your production server:")
    print(f"  scp {TOKEN_PATH} root@139.84.133.1:/root/ytz-automation/{TOKEN_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
