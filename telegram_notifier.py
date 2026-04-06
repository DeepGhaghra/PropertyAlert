import os
import requests
import logging

def send_telegram_alert(property_details):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logging.error("Telegram credentials not found in environment.")
        return False

    message = f"""🏠 *New Property Found!*

📍 Location: {property_details.get('location', 'Unknown')}
💰 Price: {property_details.get('price', 'Unknown')}
📐 Area: {property_details.get('area', 'Unknown')}
🏷 Type: {property_details.get('type', 'Unknown')}

🔗 [Link]({property_details.get('url', '#')})

🔥 Possible Deal"""

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.info(f"Telegram alert sent for listing: {property_details.get('id')}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram alert: {e}")
        return False
