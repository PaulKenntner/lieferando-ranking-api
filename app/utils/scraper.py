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

    def _get_restaurant_location(self, driver, restaurant_id: str) -> Optional[tuple]:
        """Get restaurant's location (postal code and city) from its menu page"""
        try:
            restaurant_url = f"{self.base_url}/speisekarte/{restaurant_id}"
            logging.info(f"Getting restaurant location from: {restaurant_url}")
            
            driver.get(restaurant_url)
            time.sleep(5)  # Wait for initial load
            
            try:
                # Find the "Über uns" button using text content
                button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@data-qa='button']//div[@data-qa='text'][contains(text(), 'Über uns')]"))
                )
                button.click()
                time.sleep(3)  # Wait for address to load
                logging.info("Clicked button to show address")
                
                # Get postal code and city
                address_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-qa='restaurant-info-modal-info-address-element']"))
                )
                address_text = address_element.text
                logging.info(f"Found address: {address_text}")
                
                # Extract postal code and city
                parts = address_text.split('\n')
                location_line = [p for p in parts if any(c.isdigit() for c in p)][-1]
                # Split into postal code and city
                postal_code = ''.join(filter(str.isdigit, location_line))
                city = location_line.split()[-1]
                
                logging.info(f"Extracted location: {postal_code} {city}")
                return (postal_code, city)
                
            except Exception as e:
                logging.error(f"Error getting restaurant location: {str(e)}")
                return None
                
        except Exception as e:
            logging.error(f"Error accessing restaurant page: {str(e)}")
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
            # Use both postal code and city in the URL
            url = f"{self.base_url}/lieferservice/essen/{postal_code}-{city.lower()}"
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
