import logging
import requests
import time

logger = logging.getLogger("ZohoIntegration")

class ZohoNotifier:
    def __init__(self, webhook_url=None, enabled=False):
        """
        Initialize Zoho Cliq notifier.
        
        Args:
            webhook_url: Zoho Cliq webhook URL
            enabled: Whether Zoho notifications are enabled
        """
        self.webhook_url = webhook_url
        self.enabled = enabled and webhook_url
        
    def notify_new_playlist(self, playlist_name, video_title, category):
        """
        Send notification to HR team when a new playlist is created.
        
        Args:
            playlist_name: Name of the newly created playlist
            video_title: Title of the video that triggered creation
            category: Suggested category
        """
        if not self.enabled:
            logger.debug("Zoho notifications disabled, skipping")
            return
        
        message = {
            "text": f"🆕 **New Playlist Created**\n\n"
                   f"**Playlist:** {playlist_name}\n"
                   f"**Triggered by:** {video_title}\n"
                   f"**Category:** {category}\n\n"
                   f"⚠️ **Action Required:** Please review and approve this playlist creation."
        }
        
        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            if response.status_code == 200:
                logger.info(f"Sent Zoho notification for new playlist: {playlist_name}")
            else:
                logger.warning(f"Zoho notification failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send Zoho notification: {e}")
    
    def notify_critical_error(self, context, error_message, suggested_action=None):
        """
        Send critical error notification to HR/ops team.
        
        Args:
            context: Where the error occurred (e.g., "YouTube Upload", "Drive Upload")
            error_message: The error message
            suggested_action: Optional suggested action to resolve
        """
        if not self.enabled:
            logger.debug("Zoho notifications disabled, skipping")
            return
        
        message_text = f"🚨 **Critical Error**\n\n" \
                      f"**Context:** {context}\n" \
                      f"**Error:** {error_message}\n"
        
        if suggested_action:
            message_text += f"\n**Suggested Action:** {suggested_action}"
        
        message = {"text": message_text}
        
        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            if response.status_code == 200:
                logger.info(f"Sent critical error notification to Zoho")
            else:
                logger.warning(f"Zoho notification failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send Zoho notification: {e}")
