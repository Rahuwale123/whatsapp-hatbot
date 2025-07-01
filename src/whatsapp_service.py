"""
This module provides functionalities for interacting with the WhatsApp Business API.
It includes functions for initializing WhatsApp configuration, sending messages,
and handling incoming message webhooks.
"""

import json
import requests
from typing import Dict, Any, Optional

from src import config

# Global configuration variables for WhatsApp API
_ACCESS_TOKEN: str = ""
_PHONE_NUMBER_ID: str = ""

def initialize_whatsapp_config(access_token: str, phone_number_id: str) -> None:
    """
    Initializes the global WhatsApp API access token and phone number ID.

    Args:
        access_token: The WhatsApp Business API access token.
        phone_number_id: The WhatsApp Business Account's phone number ID.
    """
    global _ACCESS_TOKEN, _PHONE_NUMBER_ID
    _ACCESS_TOKEN = access_token
    _PHONE_NUMBER_ID = phone_number_id
    print("[WhatsApp] WhatsApp API configuration initialized.")

def send_whatsapp_message(to: str, message_body: str, button_data: Optional[Dict[str, str]] = None) -> bool:
    """
    Sends a text message or an interactive message with a button to a specified WhatsApp recipient.

    Args:
        to: The recipient's WhatsApp ID (mobile number).
        message_body: The text content of the message.
        button_data: Optional dictionary containing button details (type, label, value).

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    url: str = f"https://graph.facebook.com/v22.0/{_PHONE_NUMBER_ID}/messages"
    print(f"[WhatsApp] Attempting to send message to {to}: {message_body[:50]}...")
    
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload: Dict[str, Any]

    if button_data:
        button_type = button_data.get("type")
        button_label = button_data.get("label")
        button_value = button_data.get("value")

        # Truncate button_label if it exceeds 20 characters
        if button_label and len(button_label) > 20:
            button_label = button_label[:20]

        if button_type == "phone_number":
            # For phone number, use tel: scheme in URL
            action_url = f"tel:{button_value}"
        elif button_type == "url":
            # Ensure URL has http(s):// or mailto: prefix for proper opening
            if not (button_value.startswith("http://") or button_value.startswith("https://") or button_value.startswith("mailto:")):
                action_url = f"https://{button_value}"
            else:
                action_url = button_value
        else:
            # Fallback to text message if button_data is malformed
            print(f"[❌ ERROR] Invalid button type '{button_type}' received. Sending as text message.")
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message_body},
            }
            action_url = "" # Reset to avoid linting warnings

        if button_type in ["phone_number", "url"] and action_url:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "cta_url",
                    "body": {
                        "text": message_body
                    },
                    "action": {
                        "name": "cta_url",
                        "parameters": {
                            "display_text": button_label,
                            "url": action_url
                        }
                    }
                }
            }
        else:
            # Fallback to text message if button construction failed
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": message_body},
            }

    else: # No button data, send a regular text message
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message_body},
        }

    try:
        # Ensure 'json' parameter is used for requests.post
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        print("[WhatsApp] Message sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[❌ ERROR] Failed to send WhatsApp message: {e}")
        if e.response is not None:
            print(f"[❌ ERROR] WhatsApp API Error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"[❌ ERROR] An unexpected error occurred while sending WhatsApp message: {e}")
        return False

def handle_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant information from incoming WhatsApp message data.

    Args:
        message_data: A dictionary containing the parsed message information.

    Returns:
        A dictionary with extracted message details.
    """
    from_number: str = message_data.get("from", '')
    message_body: str = message_data.get("text", {}).get("body", '')
    message_type: str = message_data.get("type", '')
    profile_name: str = message_data.get("from_profile", {}).get("name", '')

    print(f"[WhatsApp] Incoming message from {from_number} (Display Name: {profile_name if profile_name else 'N/A'}): {message_body[:50]}...")

    # No MySQL Integration: User existence/insertion is no longer handled here.
    
    # Return the extracted information for further processing in main.py
    return {
        "from_number": from_number,
        "message_body": message_body,
        "message_type": message_type,
        "profile_name": profile_name
    } 