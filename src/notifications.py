import requests
import os
import logging

logger = logging.getLogger("Notifier")

def send_notification(message, level="INFO"):
    """
    Send a notification to a webhook (Discord/Slack).
    Configure logic based on what webhook URL is present.
    """
    webhook_url = os.getenv("NOTIFICATION_WEBHOOK_URL")
    
    if not webhook_url:
        logger.debug("No notification webhook configured. Skipping.")
        return

    # Basic payload structure (Discord compatible, adaptable for Slack)
    payload = {
        "content": f"**[{level}] A4G-Collab Automation**\n{message}"
    }
    
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

def notify_error(context, error):
    msg = f":warning: **Error in {context}**\n```{str(error)}```"
    send_notification(msg, "ERROR")

def notify_success(details):
    msg = f":white_check_mark: **Success**\n{details}"
    send_notification(msg, "SUCCESS")
