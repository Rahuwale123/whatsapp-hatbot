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

def send_whatsapp_message(to: str, message_body: str) -> bool:
    """
    Sends a text message to a specified WhatsApp recipient.

    Args:
        to: The recipient's WhatsApp ID (mobile number).
        message_body: The text content of the message to send.

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    url: str = f"https://graph.facebook.com/v22.0/{_PHONE_NUMBER_ID}/messages"
    print(f"[WhatsApp] Attempting to send message to {to}: {message_body[:50]}...")
    
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message_body},
    }
    try:
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