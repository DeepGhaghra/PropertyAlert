import requests
from bs4 import BeautifulSoup
import logging
import time

def fetch_magicbricks_listings(city, property_type, min_price, max_price):
    """
    MVP function to fetch listings from Magicbricks.
    Since MagicBricks frequently updates HTML structures, 
    this targets a generic search pattern.
    """
    logging.info(f"Fetching MagicBricks listings for {property_type} in {city}...")
    
    base_url = "https://www.magicbricks.com/property-for-sale/residential-real-estate"
    
    params = {
        "cityName": city,
        "proptype": property_type,
        "budgetMin": min_price,
        "budgetMax": max_price
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    listings = []
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hypothetical class selector for MagicBricks cards
        cards = soup.find_all('div', class_='mb-srp__card')
        
        for card in cards:
            try:
                title_elem = card.find('h2', class_='mb-srp__card--title')
                price_elem = card.find('div', class_='mb-srp__card__price--amount')
                link_elem = card.find('a', class_='mb-srp__card__info--link')
                
                if title_elem and price_elem and link_elem:
                    url = link_elem.get('href')
                    if not url.startswith('http'):
                        url = 'https://www.magicbricks.com' + url
                    
                    listing_id = link_elem.get('id') or url
                    
                    listings.append({
                        'id': listing_id,
                        'location': title_elem.text.strip(),
                        'price': price_elem.text.strip(),
                        'area': 'Check Link for Area',
                        'type': property_type,
                        'url': url,
                    })
            except Exception as e:
                logging.warning(f"Error parsing a card: {e}")
                continue
                
        if not listings:
            logging.info("No listings found automatically. MagicBricks might be blocking basic requests or HTML structure changed.")
            # For testing the flow, we can yield a dummy listing. 
            # Commenting out the dummy by default so it doesn't spam.
            '''
            listings.append({
                'id': f'dummy_{int(time.time())}',
                'location': f'{city} (Dummy Test)',
                'price': f'₹ {max_price // 2}',
                'area': '1000 sqft',
                'type': property_type,
                'url': 'https://www.magicbricks.com'
            })
            '''
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching from MagicBricks: {e}")
        
    return listings
