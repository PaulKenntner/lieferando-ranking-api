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

    async def get_ranking(self, restaurant_id: str) -> Optional[Dict]:
        """Get current ranking for a restaurant"""
        try:
            city = self._extract_city(restaurant_id)
            if not city:
                logging.warning(f"Could not extract city from restaurant ID: {restaurant_id}")
                return None
                
            logging.info(f"Searching in city: {city}")
            
            result = await self._get_search_results(city, restaurant_id)  # Pass restaurant_id
            return result

        except Exception as e:
            logging.error(f"Error in get_ranking: {str(e)}")
            return None

    async def _get_search_results(self, city: str, target_restaurant_id: str) -> Optional[Dict]:
        """Get search results using Selenium"""
        driver = None
        try:
            driver = self._create_driver()
            url = f"{self.base_url}/lieferservice/essen/{city}"
            logging.info(f"Searching: {url}")
            
            driver.get(url)
            time.sleep(10)  # Initial wait for page load
            
            try:
                parent_container = driver.find_element(By.CSS_SELECTOR, "[data-qa='list-all-open-content']")
                rank = 0
                
                while True:
                    # Get current restaurant cards
                    restaurant_cards = parent_container.find_elements(By.CSS_SELECTOR, "[data-qa='restaurant-card']")
                    
                    # Process visible cards
                    for card in restaurant_cards[rank:]:  # Start from last processed rank
                        rank += 1
                        try:
                            link = card.find_element(By.TAG_NAME, "a")
                            url = link.get_attribute('href')
                            
                            if target_restaurant_id in url:
                                name = card.find_element(By.CSS_SELECTOR, "[data-qa='restaurant-info-name']")
                                # Get rating
                                try:
                                    rating = card.find_element(By.CSS_SELECTOR, "[data-qa='restaurant-ratings']")
                                    raw_rating = rating.text.strip()
                                    # Convert "4,5\n(66)" format to "★4.5 (66 reviews)"
                                    parts = raw_rating.split('\n')
                                    if len(parts) == 2:
                                        score = parts[0].replace(',', '.')
                                        reviews = parts[1].strip('()')
                                        rating_text = f"{score} ({reviews} reviews)"
                                    else:
                                        rating_text = raw_rating
                                except NoSuchElementException:
                                    rating_text = None
                                    logging.warning("Rating not found for restaurant")
                                
                                logging.info(f"Found target restaurant at rank {rank}")
                                return {
                                    'restaurant_slug': target_restaurant_id,
                                    'rank': rank,
                                    'rating': rating_text
                                }
                        except Exception as e:
                            logging.warning(f"Error processing restaurant card: {str(e)}")
                            continue
                    
                    # If we haven't found the restaurant yet, scroll and continue
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        logging.warning("Reached end of page without finding target restaurant")
                        return None
                    
                    logging.info(f"Scrolled, checked {rank} restaurants so far")
                
            except Exception as e:
                logging.error(f"Error finding main restaurant list: {str(e)}")
                return None
            
        except Exception as e:
            logging.error(f"Error in get_search_results: {str(e)}")
            return None
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass 
