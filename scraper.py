from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import logging
import re
import hashlib

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
            # Use channel chrome to look more legitimate if available
            try:
                browser = p.chromium.launch(
                    headless=True, 
                    channel='chrome',
                    ignore_default_args=["--enable-automation"]
                )
            except:
                browser = p.chromium.launch(
                    headless=True,
                    ignore_default_args=["--enable-automation"]
                )

            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                    "sec-fetch-user": "?1",
                    "upgrade-insecure-requests": "1",
                }
            )
            page = context.new_page()
            
            import random
            
            # Apply Stealth
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
            cards = soup.select('div[class*="tupleNew__outerTupleWrap"]')
            if not cards:
                cards = soup.select('div[class*="tupleNew__tupleContainer"]')
            if not cards:
                cards = soup.select('div.tuple') # Fallback for older styles
            
            for card in cards:
                try:
                    title_elem = card.select_one('a[class*="tupleNew__propertyHeading"]') or card.find('a')
                    price_elem = card.select_one('div[class*="tupleNew__priceValWrap"]') or card.select_one('div.tupleNew__price') or card.find('div', class_='price')
                    
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

def fetch_plotmarket_listings(search_url):
    logging.info("Fetching PlotMarket listings...")
    listings = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(search_url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)
            html = page.content()
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)
                title_elem = a.find(['h2', 'h3', 'h4'])
                if title_elem or len(text) > 15:
                    if 'plot' in href.lower() or 'property' in href.lower() or 'project' in href.lower():
                        listing_id = hashlib.md5(href.encode()).hexdigest()[:10]
                        full_url = href if href.startswith('http') else 'https://plotmarket.in' + href
                        listings.append({
                            'id': listing_id,
                            'location': text[:100],
                            'price': 'Check Link',
                            'area': 'Check Link',
                            'type': 'Plot',
                            'url': full_url
                        })
        except Exception as e:
            logging.error(f"Error on Plotmarket: {e}")
    unique = { x['id']:x for x in listings }.values()
    return list(unique)

def fetch_squareyards_listings(search_url):
    logging.info("Fetching SquareYards listings...")
    listings = []
    
    # Enforce sorting by newest
    if 'sort=' not in search_url:
        if '?' in search_url:
            search_url += '&sort=newest'
        else:
            search_url += '?sort=newest'
            
    import requests
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        html = requests.get(search_url, headers=headers, timeout=30).text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Squareyards uses div.listing-body for property details
        for body in soup.find_all('div', class_='listing-body'):
            if not body.get('data-url'):
                continue
                
            href = body.get('data-url')
            full_url = href if href.startswith('http') else 'https://www.squareyards.com' + href
            
            heading = body.find('h2', class_='heading')
            title = heading.get_text(strip=True) if heading else "SquareYards Property"
            
            # Search for price inside the parent article
            article = body.parent
            price = "Check Link"
            if article:
                price_elem = article.find(string=re.compile(r'₹|Lac|Cr'))
                if price_elem:
                    price = price_elem.strip()
                    
            listing_id = hashlib.md5(full_url.encode()).hexdigest()[:10]
            listings.append({
                'id': listing_id,
                'location': title,
                'price': price,
                'area': 'Check Link',
                'type': 'Property',
                'url': full_url
            })
    except Exception as e:
        logging.error(f"Error on SquareYards: {e}")
        
    unique = { x['id']:x for x in listings }.values()
    # Limit to top 10 newest to avoid spamming alerts on first run
    return list(unique)[:10]


def fetch_realestateindia_listings(search_url):
    logging.info("Fetching RealEstateIndia listings...")
    listings = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(search_url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)
            html = page.content()
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/property-detail/' in href:
                    text = a.get_text(strip=True)
                    if text and len(text) > 5:
                        full_url = href if href.startswith('http') else 'https://www.realestateindia.com' + href
                        listing_id = hashlib.md5(full_url.encode()).hexdigest()[:10]
                        price = "Check Link"
                        parent = a.parent
                        if parent:
                            price_val = parent.find_all(string=re.compile(r'Lac|Cr|₹'))
                            if price_val:
                                price = price_val[0].strip()
                        listings.append({
                            'id': listing_id,
                            'location': text,
                            'price': price,
                            'area': 'Check Link',
                            'type': 'Property',
                            'url': full_url
                        })
        except Exception as e:
            logging.error(f"Error on RealEstateIndia: {e}")
    unique = { x['id']:x for x in listings }.values()
    return list(unique)

def fetch_housing_listings(search_url):
    logging.info("Fetching Housing.com listings...")
    listings = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36')
            page = context.new_page()
            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(8000)
            html = page.content()
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            for article in soup.find_all('article'):
                a_tag = article.find('a', href=True)
                if a_tag:
                    href = a_tag['href']
                    full_url = href if href.startswith('http') else 'https://housing.com' + href
                    title = a_tag.get_text(strip=True) or "Housing Property"
                    listing_id = hashlib.md5(full_url.encode()).hexdigest()[:10]
                    listings.append({
                        'id': listing_id,
                        'location': title,
                        'price': "Check Link",
                        'area': 'Check Link',
                        'type': 'Property',
                        'url': full_url
                    })
        except Exception as e:
            logging.error(f"Error on Housing: {e}")
    unique = { x['id']:x for x in listings }.values()
    return list(unique)

def fetch_gsale_listings(search_url):
    logging.info("Fetching GSale listings...")
    listings = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(search_url, wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)
            html = page.content()
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/item/' in href:
                    text = a.get_text(strip=True)
                    full_url = href if href.startswith('http') else 'https://gsale.in' + href
                    listing_id = hashlib.md5(full_url.encode()).hexdigest()[:10]
                    listings.append({
                        'id': listing_id,
                        'location': text,
                        'price': "Check Link",
                        'area': 'Check Link',
                        'type': 'Property',
                        'url': full_url
                    })
        except Exception as e:
            logging.error(f"Error on GSale: {e}")
    unique = { x['id']:x for x in listings }.values()
    return list(unique)

def fetch_listings(search_url):
    """
    Wrapper to route to the correct platform scraper.
    """
    if 'magicbricks.com' in search_url:
        return fetch_magicbricks_listings(search_url), "MagicBricks"
    elif '99acres.com' in search_url:
        return fetch_99acres_listings(search_url), "99acres"
    elif 'plotmarket.in' in search_url:
        return fetch_plotmarket_listings(search_url), "PlotMarket"
    elif 'squareyards.com' in search_url:
        return fetch_squareyards_listings(search_url), "SquareYards"
    elif 'realestateindia.com' in search_url:
        return fetch_realestateindia_listings(search_url), "RealEstateIndia"
    elif 'housing.com' in search_url:
        return fetch_housing_listings(search_url), "Housing"
    elif 'gsale.in' in search_url:
        return fetch_gsale_listings(search_url), "GSale"
    else:
        logging.error(f"Unsupported platform URL: {search_url}")
        return [], "Unknown"
