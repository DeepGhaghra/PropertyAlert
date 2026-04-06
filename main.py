import os
import time
import schedule
import logging
from dotenv import load_dotenv
from database import init_db, is_seen, mark_as_seen
from scraper import fetch_listings
from telegram_notifier import send_telegram_alert

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def job():
    logging.info("Starting a new scanning job...")
    
    # Support multiple URLs comma separated in the .env
    search_urls_str = os.getenv('SEARCH_URL')
    if not search_urls_str:
        logging.error("No SEARCH_URL found in .env")
        return

    # Use a more robust way to split URLs that might contain commas
    search_urls = []
    if ',' in search_urls_str:
        # Split by comma followed by 'http' to avoid splitting inside query parameters
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


def main():
    load_dotenv() # Load environment variables from .env
    init_db() # Initialize SQLite Database
    
    try:
        interval_seconds = int(os.getenv('CHECK_INTERVAL_SECONDS', 120))
    except ValueError:
        interval_seconds = 120
    
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
