from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import logging
import re

def fetch_magicbricks_listings(search_url):
    """
    Playwright-based function to fetch listings from Magicbricks.
    """
    logging.info(f"Fetching MagicBricks listings via Playwright...")
    listings = []
    
    if "?" in search_url and "propertySortBy=" not in search_url:
        search_url += "&propertySortBy=posteddate"
    elif "?" not in search_url:
        search_url += "?propertySortBy=posteddate"
        
    with sync_playwright() as p:
        try:
            # Launch headless browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            logging.info(f"Loading URL: {search_url}")
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait a few seconds for JS to render the cards
            page.wait_for_timeout(5000) 
            
            # Get the page source
            html = page.content()
            browser.close()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.find_all('div', class_='mb-srp__card')
            
            for card in cards:
                try:
                    title_elem = card.find('h2', class_='mb-srp__card--title')
                    price_elem = card.find('div', class_='mb-srp__card__price--amount')
                    summary_elem = card.find('div', class_='mb-srp__card__summary')
                    
                    if title_elem and price_elem and summary_elem:
                        # Find the property ID from the container
                        container_id = summary_elem.get('id', '')
                        listing_id_match = re.search(r'\d+', container_id)
                        listing_id = listing_id_match.group(0) if listing_id_match else container_id

                        # Generate Hex Encoded ID (MB<id> -> hex string)
                        mb_string = "MB" + str(listing_id)
                        hex_id = "".join([hex(ord(c))[2:] for c in mb_string])
                        
                        # Try to find the exact url from the page source JSONs
                        exact_url = ""
                        url_pattern = r'https://www\.magicbricks\.com/propertyDetails/[^"]+&id=' + hex_id
                        url_matches = re.findall(url_pattern, html)
                        if url_matches:
                            exact_url = url_matches[0]
                        else:
                            # Fallback MagicBricks link structure
                            title_slug = title_elem.text.strip().replace(' ', '-')
                            exact_url = f"https://www.magicbricks.com/propertyDetails/{title_slug}&id={hex_id}"
                        
                        listings.append({
                            'id': listing_id,
                            'location': title_elem.text.strip(),
                            'price': price_elem.text.strip(),
                            'area': 'Check Link', 
                            'type': 'Property',
                            'url': exact_url,
                        })

                except Exception as e:
                    logging.warning(f"Error parsing a card: {e}")
                    continue
                    
            if not listings:
                logging.info("No listings found. Double check if the URL returns results.")
                
        except Exception as e:
            logging.error(f"Playwright encountered an error: {e}")
            
    return listings
def fetch_99acres_listings(search_url):
    """
    Playwright-based function to fetch listings from 99acres.
    """
    logging.info(f"Fetching 99acres listings via Playwright...")
    listings = []
    
    # Enforce sorting by date_desc for 99acres
    if "sort=" not in search_url:
        if "?" in search_url:
            search_url += "&sort=date_desc"
        else:
            search_url += "?sort=date_desc"
            
    from playwright_stealth import Stealth
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            import random
            
            # Apply Stealth to hide Playwright presence
            stealth_config = Stealth()
            stealth_config.apply_stealth_sync(page)
            
            # Additional human behavior patterns
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Randomize user agent slightly per request
            logging.info("Visiting 99acres with Stealth mode & Human Delays...")
            
            # Visit a search engine first sometimes to mimic a referral
            try:
                page.goto("https://www.google.com/search?q=99acres+nashik+commercial", wait_until='domcontentloaded', timeout=20000)
                page.wait_for_timeout(random.randint(2000, 5000))
            except:
                pass

            page.goto("https://www.99acres.com/", wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(random.randint(3000, 6000))
            
            logging.info(f"Loading Search URL: {search_url}")
            page.goto(search_url, wait_until='networkidle', timeout=60000)
            
            # More human-like scrolling and pausing
            for _ in range(random.randint(3, 6)):
                scroll_amount = random.randint(300, 700)
                page.mouse.wheel(0, scroll_amount)
                page.wait_for_timeout(random.randint(1000, 3000))
                # Small mouse move
                page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            
            page.wait_for_timeout(5000) # Final wait for all JS to finish
            html = page.content()
            
            if "Access Denied" in html:
                logging.error("99acres still blocked us. Trying one last slow-load fallback...")
                page.reload(wait_until='networkidle')
                page.wait_for_timeout(15000)
                html = page.content()
                if "Access Denied" in html:
                    browser.close()
                    return []
            
            browser.close() 


            
            soup = BeautifulSoup(html, 'html.parser')

            # Relaxed selection to catch different types of tuples
            cards = soup.select('div[class*="tupleNew__tupleContainer"]')
            if not cards:
                cards = soup.select('div.tuple') # Fallback for older styles
            
            for card in cards:
                try:
                    title_elem = card.select_one('a.tupleNew__propertyHeading') or card.find('a')
                    price_elem = card.select_one('div.tupleNew__price') or card.find('div', class_='price')
                    
                    if title_elem:
                        link_href = title_elem.get('href', '')
                        if not link_href.startswith('http') and link_href:
                            link_href = "https://www.99acres.com" + link_href
                        
                        # More robust ID extraction
                        listing_id = "unknown"
                        # Try spid- first
                        id_match = re.search(r'spid-([A-Z0-9]+)', link_href)
                        if id_match:
                            listing_id = id_match.group(1)
                        else:
                            # Fallback: Hash of the URL if no ID found
                            import hashlib
                            listing_id = hashlib.md5(link_href.encode()).hexdigest()[:10]

                        
                        listings.append({
                            'id': listing_id,
                            'location': title_elem.get_text(strip=True),
                            'price': price_elem.get_text(strip=True) if price_elem else "Contact for Price",
                            'area': 'Check Link',
                            'type': 'Property',
                            'url': link_href,
                        })
                except Exception as e:
                    logging.warning(f"Error parsing a 99acres card: {e}")
                    continue
                    
            if not listings:
                logging.info("No 99acres listings found.")
                
        except Exception as e:
            logging.error(f"Playwright encountered an error on 99acres: {e}")
            
    return listings

def fetch_listings(search_url):
    """
    Wrapper to route to the correct platform scraper.
    """
    if 'magicbricks.com' in search_url:
        return fetch_magicbricks_listings(search_url), "MagicBricks"
    elif '99acres.com' in search_url:
        return fetch_99acres_listings(search_url), "99acres"
    else:
        logging.error(f"Unsupported platform URL: {search_url}")
        return [], "Unknown"
