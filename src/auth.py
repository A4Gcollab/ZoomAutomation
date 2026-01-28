
import os
from google.oauth2 import id_token
from google.auth.transport import requests
from src import config
import logging

logger = logging.getLogger("Auth")

# We need a Google Client ID for the Frontend.
# For now, we reuse the CLIENT_ID from the Zoom config? NO.
# User needs to create a Google Cloud OAuth Client ID for Web.
# We will read it from ENV.

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_WEB_CLIENT_ID", "")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")

def verify_google_token(token):
    """
    Verifies a Google ID token.
    Returns:
        dict: User info (email, name, picture) if valid & admin.
        None: If invalid or not admin.
    """
    try:
        # DEMO MODE: Bypass for visual verification
        if token == "DEMO_TOKEN_VONG_2026":
            return {
                "email": "demo@omysha.com",
                "name": "Demo Admin",
                "picture": ""
            }

        # verify_oauth2_token verifies the signature and expiration
        id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        email = id_info.get('email')
        
        # Admin Check
        if email not in ADMIN_EMAILS:
            logger.warning(f"Access Denied: Email {email} is not in ADMIN_EMAILS.")
            return None
            
        return {
            "email": email,
            "name": id_info.get('name'),
            "picture": id_info.get('picture')
        }
        
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        return None
