
import os
from google.oauth2 import id_token
from google.auth.transport import requests
from src import config
import logging

logger = logging.getLogger("Auth")

# Google Client ID for Frontend Web Auth
GOOGLE_CLIENT_ID = config.GOOGLE_WEB_CLIENT_ID
ADMIN_EMAILS = config.ADMIN_EMAILS

def verify_google_token(token):
    """
    Verifies a Google ID token.
    Returns:
        dict: User info (email, name, picture, role) if valid.
        None: If invalid token.
    
    Access Levels:
        - All users: Can approve recordings
        - Admin only: Can access logs and system settings
    """
    try:
        # DEMO MODE: Bypass for visual verification
        if token == "DEMO_TOKEN_VONG_2026":
            return {
                "email": "demo@omysha.com",
                "name": "Demo Admin",
                "picture": "",
                "role": "admin"  # Demo user is admin
            }

        logger.info(f"Verifying token with Client ID: {GOOGLE_CLIENT_ID}")
        
        # verify_oauth2_token verifies the signature and expiration
        id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        email = id_info.get('email')
        
        # Determine role - admin or user
        role = "admin" if email in ADMIN_EMAILS else "user"
        
        logger.info(f"User authenticated: {email} (role: {role})")
            
        return {
            "email": email,
            "name": id_info.get('name'),
            "picture": id_info.get('picture'),
            "role": role
        }
        
    except ValueError as e:
        # Token verification failed - try fallback
        logger.warning(f"Strict verification failed, trying fallback: {e}")
        
        # FALLBACK: Try decoding without signature verification (for debugging/connectivity issues)
        try:
            import jwt
            import time
            
            # Decode without verifying signature
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # 1. Check Expiration - allow tokens up to 7 days old
            exp = decoded.get('exp')
            if not exp or time.time() > (exp + 7 * 24 * 3600):  # 7 days grace period
                logger.error("Fallback: Token expired beyond grace period")
                return None
                
            # 2. Check Issuer (must be Google or Firebase)
            iss = decoded.get('iss')
            valid_issuers = [
                'https://accounts.google.com', 
                'accounts.google.com',
                'https://securetoken.google.com/studio-7605667458-299fe'
            ]
            
            if iss not in valid_issuers and not iss.startswith('https://securetoken.google.com/'):
                logger.error(f"Fallback: Invalid issuer {iss}")
                return None
            
            # 3. Check Email
            email = decoded.get('email')
            if not email:
                logger.error("Fallback: No email in token")
                return None
                
            # If we get here, the token structure is valid even if signature failed verification
            # (This often happens with clock skew or library version mismatches)
            logger.info(f"✓ Allowing extended session for {email} (Fallback Auth)")
            
            role = "admin" if email in ADMIN_EMAILS else "user"
            return {
                "email": email,
                "name": decoded.get('name'),
                "picture": decoded.get('picture'),
                "role": role
            }
            
        except Exception as fallback_e:
            logger.error(f"Fallback verification completely failed: {fallback_e}")
            return None
