import os
import time
import threading
import telebot
import schedule
import logging
from dotenv import load_dotenv
from database import init_db, is_seen, mark_as_seen
from scraper import fetch_listings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not BOT_TOKEN:
    logging.error("No TELEGRAM_BOT_TOKEN found in .env file.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def send_telegram_alert(property_details):
    message = f"""🏠 *New Property Found!*

📍 Location: {property_details.get('location', 'Unknown')}
💰 Price: {property_details.get('price', 'Unknown')}
📐 Area: {property_details.get('area', 'Unknown')}
🏷 Type: {property_details.get('type', 'Unknown')}

🔗 [Link]({property_details.get('url', '#')})

🔥 Possible Deal"""
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        logging.info(f"Telegram alert sent for listing: {property_details.get('id')}")
        return True
    except Exception as e:
        logging.error(f"Failed to send Telegram alert: {e}")
        return False

def job():
    logging.info("Starting a new scanning job...")
    
    search_urls_str = os.getenv('SEARCH_URL')
    if not search_urls_str:
        logging.error("No SEARCH_URL found in .env")
        return

    search_urls = []
    if ',' in search_urls_str:
        parts = search_urls_str.split(',http')
        for i, part in enumerate(parts):
            if i == 0:
                search_urls.append(part.strip())
            else:
                search_urls.append('http' + part.strip())
    else:
        search_urls = [search_urls_str.strip()]
    
    keywords_str = os.getenv('KEYWORDS', '')
    keywords = [k.strip() for k in keywords_str.split(',')] if keywords_str else []

    for url in search_urls:
        logging.info(f"Scanning target: {url}...")

        # 1. Fetch Listings via generic wrapper
        listings, platform = fetch_listings(url)
        
        # 2. Process Listings
        for property_details in listings:
            listing_id = f"{platform}_{property_details['id']}" # Platform specific ID
            
            text_to_search = (property_details['location'] + " " + property_details['price']).lower()
            if keywords and not any(k.lower() in text_to_search for k in keywords):
                continue 
                
            # 3. Check if already seen
            if not is_seen(listing_id):
                logging.info(f"New deal found on {platform}! {property_details['location']} - {property_details['price']}")
                
                # Update details with platform for notification
                property_details['type'] = f"{property_details['type']} ({platform})"
                
                # 4. Alert and Mark as seen
                success = send_telegram_alert(property_details)
                if success:
                    mark_as_seen(listing_id, platform)
                else:
                    logging.error(f"Failed to send alert for {listing_id}, will not mark as seen yet.")
            else:
                logging.debug(f"Listing {listing_id} already seen. Skipping.")

def run_schedule():
    try:
        interval_seconds = int(os.getenv('CHECK_INTERVAL_SECONDS', 120))
    except ValueError:
        interval_seconds = 120
    
    schedule.every(interval_seconds).seconds.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- TELEGRAM BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello! I am your Property Alert Bot.\n\n"
                          "I am running in the background and will notify you when new listings match your criteria.\n\n"
                          "Commands:\n"
                          "/scan - Force an immediate scan\n"
                          "/status - Check bot status")

@bot.message_handler(commands=['scan'])
def force_scan(message):
    bot.reply_to(message, "🔍 Starting a manual scan. I will notify you if I find any new deals.")
    threading.Thread(target=job).start()

@bot.message_handler(commands=['status'])
def status_check(message):
    urls = os.getenv('SEARCH_URL', 'None')
    keywords = os.getenv('KEYWORDS', 'None')
    interval = os.getenv('CHECK_INTERVAL_SECONDS', '120')
    
    status_msg = f"🟢 *Bot is Running*\n\n" \
                 f"*Interval:* Every {interval} seconds\n" \
                 f"*Keywords:* {keywords}\n\n" \
                 f"*Scanning URLs:* {urls[:100]}..."
                 
    bot.reply_to(message, status_msg, parse_mode="Markdown")

if __name__ == "__main__":
    init_db() # Initialize SQLite Database
    
    logging.info("Starting background scheduler thread...")
    # Run first job immediately before scheduling
    threading.Thread(target=job).start()
    
    # Start the background scheduling thread
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    
    logging.info("Starting Telegram Bot polling...")
    # Start telegram bot polling
    bot.infinity_polling()
