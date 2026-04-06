import json
import time
import schedule
import logging
from dotenv import load_dotenv
from database import init_db, is_seen, mark_as_seen
from scraper import fetch_magicbricks_listings
from telegram_notifier import send_telegram_alert

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path='config.json'):
    with open(config_path, 'r') as f:
        return json.load(f)

def job():
    logging.info("Starting a new scanning job...")
    try:
        config = load_config()
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return
    
    # 1. Fetch Listings
    listings = fetch_magicbricks_listings(
        city=config.get('city'),
        property_type=config.get('property_type'),
        min_price=config.get('min_price'),
        max_price=config.get('max_price')
    )
    
    # 2. Process Listings
    for property_details in listings:
        listing_id = property_details['id']
        platform = "MagicBricks"
        keywords = config.get('keywords', [])
        
        # Basic keyword filtering logic can be added here
        text_to_search = (property_details['location'] + " " + property_details['price']).lower()
        if keywords and not any(k.lower() in text_to_search for k in keywords):
            # Just logging it if strict keyword mode is desired
            # logging.debug(f"Skipping {listing_id} due to missing keywords.")
            pass # Keep it simple for MVP - assuming we want all in the price range
            
        # 3. Check if already seen
        if not is_seen(listing_id):
            logging.info(f"New deal found! {property_details['location']} - {property_details['price']}")
            
            # 4. Alert and Mark as seen
            success = send_telegram_alert(property_details)
            if success:
                mark_as_seen(listing_id, platform)
            else:
                logging.error(f"Failed to send alert for {listing_id}, will not mark as seen yet.")
        else:
            logging.debug(f"Listing {listing_id} already seen. Skipping.")

def main():
    load_dotenv() # Load environment variables from .env
    init_db() # Initialize SQLite Database
    
    try:
        config = load_config()
        interval_seconds = config.get('check_interval', 120)
    except Exception as e:
        logging.error(f"Failed to initialize: {e}")
        return
    
    logging.info(f"Bot started. Running every {interval_seconds} seconds.")
    
    # Run once immediately
    job()
    
    # Schedule the job
    schedule.every(interval_seconds).seconds.do(job)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
