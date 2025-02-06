import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import time
from typing import Optional, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LieferandoScraper:
    """Scraper for Lieferando rankings"""
    
    def __init__(self):
        self.base_url = "https://www.lieferando.de"
        self.known_chains = ['loco-chicken', 'happy-slice', 'happy-slice-pizza']

    def _extract_city(self, restaurant_id: str) -> Optional[str]:
        """Extract city name from restaurant ID"""
        parts = restaurant_id.split('-')
        
        for chain in self.known_chains:
            if restaurant_id.startswith(chain):
                remaining = restaurant_id[len(chain):].strip('-')
                city = remaining.split('-')[-1]
                city = city.replace('i-', '').replace('markt', '').strip('-')
                return city
        return None

    def _create_driver(self):
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--enable-javascript')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = uc.Chrome(
                options=options,
                version_main=132,
                headless=True
            )
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logging.error(f"Error creating driver: {str(e)}")
            raise

    def _get_restaurant_location(self, driver, restaurant_id: str, max_retries: int = 3) -> Optional[tuple]:
        """Get restaurant's location (postal code and city) from its menu page"""
        for attempt in range(max_retries):
            try:
                restaurant_url = f"{self.base_url}/speisekarte/{restaurant_id}"
                logging.info(f"Attempt {attempt + 1}/{max_retries}: Getting location from {restaurant_url}")
                
                driver.get(restaurant_url)
                time.sleep(5 + attempt * 2)  # Increase wait time with each retry
                
                try:
                    # Find and click the "Über uns" button
                    button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//button[@data-qa='button']//div[@data-qa='text'][contains(text(), 'Über uns')]"))
                    )
                    logging.info("Found 'Über uns' button")
                    button.click()
                    time.sleep(3 + attempt * 1)  # Increase wait time with each retry
                    
                    # Get address
                    address_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='restaurant-info-modal-info-address-element']"))
                    )
                    address_text = address_element.text
                    logging.info(f"Raw address text: '{address_text}'")
                    
                    if not address_text.strip():
                        logging.warning("Empty address text, retrying...")
                        continue
                    
                    # Extract location
                    parts = address_text.split('\n')
                    location_line = next(
                        line for line in parts 
                        if any(part.isdigit() and len(part.strip()) == 5 for part in line.split())
                    )
                    
                    postal_code = ''.join(c for c in location_line if c.isdigit())[:5]
                    city = location_line.split(postal_code)[-1].strip()
                    
                    if postal_code and city:
                        logging.info(f"Successfully extracted location: {postal_code} {city}")
                        return (postal_code, city)
                    
                    logging.warning("Failed to extract complete location, retrying...")
                    
                except Exception as e:
                    logging.error(f"Error in attempt {attempt + 1}: {str(e)}")
                    if attempt == max_retries - 1:
                        return None
                    continue
                    
            except Exception as e:
                logging.error(f"Error accessing page in attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    return None
                continue
            
        logging.error(f"Failed to get location after {max_retries} attempts")
        return None

    async def get_ranking(self, restaurant_id: str) -> Optional[Dict]:
        """Get current ranking for a restaurant"""
        driver = None
        try:
            driver = self._create_driver()
            
            # First get the restaurant's location
            location = self._get_restaurant_location(driver, restaurant_id)
            if not location:
                logging.warning(f"Could not get location for restaurant: {restaurant_id}")
                return None
                
            postal_code, city = location
            logging.info(f"Searching in {postal_code} {city}")
            
            # Now search in that location
            result = await self._get_search_results(postal_code, city, restaurant_id, driver)
            return result

        except Exception as e:
            logging.error(f"Error in get_ranking: {str(e)}")
            return None
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    async def _get_search_results(self, postal_code: str, city: str, target_restaurant_id: str, driver) -> Optional[Dict]:
        """Get search results using Selenium"""
        try:
            url = f"{self.base_url}/lieferservice/essen/{postal_code}-{city.lower()}"
            logging.info(f"Searching: {url}")
            
            driver.get(url)
            time.sleep(10)  # Initial wait for page load
            
            try:
                parent_container = driver.find_element(By.CSS_SELECTOR, "[data-qa='list-all-open-content']")
                rank = 0
                previous_restaurant_count = 0
                unchanged_count = 0  # Counter for when restaurant count doesn't change
                
                while True:
                    # Get current restaurant cards
                    restaurant_cards = parent_container.find_elements(By.CSS_SELECTOR, "[data-qa='restaurant-card']")
                    current_restaurant_count = len(restaurant_cards)
                    
                    # If we haven't found new restaurants in 3 scrolls, assume we've reached closed restaurants
                    if current_restaurant_count == previous_restaurant_count:
                        unchanged_count += 1
                        if unchanged_count >= 3:
                            logging.warning(f"No new restaurants found after {rank} entries - stopping search")
                            return None
                    else:
                        unchanged_count = 0  # Reset counter when we find new restaurants
                    
                    # Process visible cards
                    for card in restaurant_cards[rank:]:  # Start from last processed rank
                        rank += 1
                        try:
                            link = card.find_element(By.TAG_NAME, "a")
                            url = link.get_attribute('href')
                            
                            if target_restaurant_id in url:
                                # Get rating
                                try:
                                    rating = card.find_element(By.CSS_SELECTOR, "[data-qa='restaurant-ratings']")
                                    rating_text = rating.text.strip()
                                    rating_value = float(rating_text.split()[0].replace(',', '.'))
                                except (NoSuchElementException, ValueError, IndexError):
                                    rating_value = None
                                    logging.warning("Rating not found or invalid for restaurant")
                                
                                logging.info(f"Found target restaurant at rank {rank}")
                                return {
                                    'restaurant_slug': target_restaurant_id,
                                    'rank': rank,
                                    'rating': rating_value
                                }
                        except Exception as e:
                            logging.warning(f"Error processing restaurant card: {str(e)}")
                            continue
                    
                    # Update previous count before scrolling
                    previous_restaurant_count = current_restaurant_count
                    
                    # Scroll and check for new content
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height and unchanged_count >= 2:
                        logging.warning(f"Reached end of list after checking {rank} restaurants")
                        return None
                    
                    logging.info(f"Scrolled, checked {rank} restaurants so far")
                
            except Exception as e:
                logging.error(f"Error finding main restaurant list: {str(e)}")
                return None
            
        except Exception as e:
            logging.error(f"Error in get_search_results: {str(e)}")
            return None 
