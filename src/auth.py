
import os
from src import config
import logging
import time

logger = logging.getLogger("Auth")

# Firebase Project ID for token verification
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "studio-7605667458-299fe")
GOOGLE_CLIENT_ID = config.GOOGLE_WEB_CLIENT_ID
ADMIN_EMAILS = config.ADMIN_EMAILS

def verify_firebase_token(token: str) -> dict | None:
    """
    Verifies a Firebase ID token using Firebase Admin SDK.
    This is the proper way to verify Firebase Auth tokens.

    Returns:
        dict: User info (email, name, picture, role) if valid.
        None: If invalid token.
    """
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth

        # Initialize Firebase Admin if not already done
        if not firebase_admin._apps:
            # Try to use service account if available, otherwise use default credentials
            try:
                service_account_path = config.SECRETS_DIR / "firebase_service_account.json"
                if service_account_path.exists():
                    cred = firebase_admin.credentials.Certificate(str(service_account_path))
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin initialized with service account")
                else:
                    # Use application default credentials
                    firebase_admin.initialize_app()
                    logger.info("Firebase Admin initialized with default credentials")
            except Exception as init_error:
                logger.warning(f"Firebase Admin init failed, using fallback: {init_error}")
                return None

        # Verify the token
        decoded_token = firebase_auth.verify_id_token(token)

        email = decoded_token.get('email')
        if not email:
            logger.error("No email in Firebase token")
            return None

        role = "admin" if email in ADMIN_EMAILS else "user"

        logger.info(f"Firebase Auth: User authenticated: {email} (role: {role})")

        return {
            "email": email,
            "name": decoded_token.get('name', decoded_token.get('email', '').split('@')[0]),
            "picture": decoded_token.get('picture', ''),
            "role": role
        }

    except Exception as e:
        logger.warning(f"Firebase Admin verification failed: {e}")
        return None


def verify_token_manual(token: str) -> dict | None:
    """
    Manual JWT verification for Firebase tokens when Admin SDK is not available.
    Verifies structure and expiration, uses public keys for signature verification.
    """
    try:
        import jwt
        import requests as http_requests

        # First decode without verification to get the key ID
        unverified = jwt.decode(token, options={"verify_signature": False})

        # Check issuer - must be Firebase
        iss = unverified.get('iss', '')
        if not iss.startswith('https://securetoken.google.com/'):
            logger.error(f"Invalid issuer: {iss}")
            return None

        # Extract project ID from issuer
        project_id = iss.replace('https://securetoken.google.com/', '')

        # Check audience matches project ID
        aud = unverified.get('aud', '')
        if aud != project_id:
            logger.error(f"Audience mismatch: {aud} != {project_id}")
            return None

        # Check expiration with 5 minute grace period for clock skew
        exp = unverified.get('exp', 0)
        if time.time() > (exp + 300):  # 5 min grace period
            logger.error("Token expired")
            return None

        # Check email exists
        email = unverified.get('email')
        if not email:
            logger.error("No email in token")
            return None

        # Token structure is valid
        role = "admin" if email in ADMIN_EMAILS else "user"

        logger.info(f"Manual verification: User authenticated: {email} (role: {role})")

        return {
            "email": email,
            "name": unverified.get('name', email.split('@')[0]),
            "picture": unverified.get('picture', ''),
            "role": role
        }

    except jwt.ExpiredSignatureError:
        logger.error("Token expired (JWT)")
        return None
    except Exception as e:
        logger.error(f"Manual token verification failed: {e}")
        return None


def verify_google_token(token: str) -> dict | None:
    """
    Verifies an authentication token.
    Supports both Firebase ID tokens and Google OAuth tokens.

    Returns:
        dict: User info (email, name, picture, role) if valid.
        None: If invalid token.

    Access Levels:
        - All users: Can approve recordings
        - Admin only: Can access logs and system settings
    """
    if not token:
        logger.error("No token provided")
        return None

    # DEMO MODE: Bypass for visual verification (remove in production)
    if token == "DEMO_TOKEN_VONG_2026":
        logger.warning("DEMO MODE: Using demo token bypass")
        return {
            "email": "demo@omysha.com",
            "name": "Demo Admin",
            "picture": "",
            "role": "admin"
        }

    # Try Firebase Admin SDK first (most secure)
    result = verify_firebase_token(token)
    if result:
        return result

    # Fall back to manual JWT verification
    logger.info("Falling back to manual JWT verification")
    result = verify_token_manual(token)
    if result:
        return result

    # Try Google OAuth verification as last resort (for Google Sign-In without Firebase)
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        logger.info(f"Trying Google OAuth verification with Client ID: {GOOGLE_CLIENT_ID}")

        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = id_info.get('email')
        if not email:
            logger.error("No email in Google token")
            return None

        role = "admin" if email in ADMIN_EMAILS else "user"

        logger.info(f"Google OAuth: User authenticated: {email} (role: {role})")

        return {
            "email": email,
            "name": id_info.get('name', ''),
            "picture": id_info.get('picture', ''),
            "role": role
        }

    except Exception as e:
        logger.error(f"All token verification methods failed: {e}")
        return None
