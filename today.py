import asyncio
import random
import logging
from typing import List, Optional, Dict

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException
)
import undetected_chromedriver as uc
import pandas as pd

from config import PRODUCT_CATEGORIES, SCRAPER_CONFIG

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MarianosScraper:
    def __init__(
        self, 
        base_url: str = "https://www.marianos.com/",
        user_agent: Optional[str] = None,
        headless: bool = False,
        timeout: int = 30,
        zip_code: Optional[str] = None
    ):
        self.base_url = base_url
        self.user_agent = user_agent or self._generate_user_agent()
        self.headless = headless
        self.timeout = timeout
        self.zip_code = zip_code
        self.driver: Optional[Chrome] = None
        self.all_product_links: List[str] = []
        self.unique_product_links: set = set()
        self.product_data: List[Dict] = []

    @staticmethod
    def _generate_user_agent() -> str:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        return random.choice(user_agents)

    def _setup_driver_options(self) -> Options:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument("--incognito")
        options.add_argument(f"user-agent={self.user_agent}")
        
        if self.headless:
            options.add_argument("--headless")
        
        return options

    async def dismiss_qualtrics_popup(self) -> bool:
        try:
            popup = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'We want to hear from you!')]"))
            )
            no_thanks_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'No, thanks')]"))
            )

            self.driver.execute_script("arguments[0].click();", no_thanks_button)
            
            logger.info("Qualtrics popup successfully dismissed")

            await asyncio.sleep(random.uniform(1, 3))
            
            return True
        
        except (TimeoutException, NoSuchElementException):
            logger.info("No Qualtrics popup found")
            return False
        
        except Exception as e:
            logger.warning(f"Error handling Qualtrics popup: {e}")
            return False

    async def type_like_human(self, element, text: str, delay: float = 0.2):
        for char in text:
            element.send_keys(char)
            await asyncio.sleep(delay)

    async def scrape_product_details(self, link: str) -> Optional[Dict]:
        try:
            await asyncio.sleep(3)  # Allow page to load
            
            # Get product details
            product_name = self.driver.find_element(By.CSS_SELECTOR, 'h1[data-testid="product-details-name"]').text
            upc = self.driver.find_element(By.CSS_SELECTOR, 'span[data-testid="product-details-upc"]').text.replace("UPC: ", "")
            upc = f"#{upc}"
            location = self.driver.find_element(By.CSS_SELECTOR, 'span[data-testid="product-details-location"]').text

            try:
                # Find the breadcrumb navigation
                breadcrumb_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a.kds-Link.kds-Link--inherit.mr-4')

                # Iterate through the breadcrumb links and find the one that is not "Home"
                for breadcrumb_element in breadcrumb_elements:
                    if breadcrumb_element.text != "Home":
                        category = breadcrumb_element.text
                        break
                else:
                    category = "Uncategorized"
            except NoSuchElementException:
                category = "Uncategorized"

            try:
                price_element = self.driver.find_element(By.CSS_SELECTOR, '[typeof="Price"]')
                price = f"${price_element.get_attribute('value')}"
            except NoSuchElementException:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional')
                    dollars = price_element.find_element(By.CSS_SELECTOR, 'span.kds-Price-promotional-dropCaps').text
                    cents = price_element.find_element(By.CSS_SELECTOR, 'sup.kds-Price-superscript').text.replace(".", "")
                    price = f"${dollars}.{cents}"
                except NoSuchElementException:
                    price = "Price Not Available"

            try:
                image_element = self.driver.find_element(By.CSS_SELECTOR, '.ProductImages-image')
                image_url = image_element.get_attribute('src')
            except NoSuchElementException:
                image_url = "No image available"

            product_detail = {
                'UPC': upc,
                'Category': category,
                'Title': product_name,
                'Location': location,
                'Price': price,
                'Image URL': image_url,
                'Product Link': link
            }

            logger.info(f"Scraped product: {product_name}")
            return product_detail
            
        except Exception as e:
            logger.error(f"Error scraping product details: {e}")
            return None

    async def process_product_links(self, category_links: List[str]) -> List[Dict]:
        main_window = self.driver.current_window_handle
        category_product_details = []

        try:
            # Open a new tab
            self.driver.execute_script("window.open('');")
            await asyncio.sleep(2)
            
            # Switch to the new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])

            for link in category_links:
                try:
                    logger.info(f"Processing link: {link}")
                    self.driver.get(link)
                    
                    # Scrape product details
                    product_detail = await self.scrape_product_details(link)
                    
                    if product_detail:
                        category_product_details.append(product_detail)
                    
                    # Short random delay between product page visits
                    await asyncio.sleep(random.uniform(2, 5))

                except Exception as link_error:
                    logger.error(f"Error processing link {link}: {link_error}")
                    continue

        except Exception as e:
            logger.error(f"Critical error in processing links: {e}")
        
        finally:
            # Close the tab and switch back to main window
            self.driver.close()
            self.driver.switch_to.window(main_window)

        return category_product_details

    def extract_product_links(self) -> List[str]:
        try:
            product_containers = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="auto-grid-cell"]'))
            )

            new_links = [
                container.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                for container in product_containers
            ]

            unique_new_links = [
                link for link in new_links 
                if link not in self.unique_product_links
            ]
            
            self.unique_product_links.update(unique_new_links)
            self.all_product_links.extend(unique_new_links)
            
            logger.info(f"Found {len(unique_new_links)} new product links")
            return unique_new_links
        
        except Exception as e:
            logger.error(f"Error extracting product links: {e}")
            return []

    async def click_load_more(self) -> bool:
        try:
            load_more_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.LoadMore__load-more-button'))
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                load_more_button
            )           
            await asyncio.sleep(random.uniform(1.5, 3.5))
            load_more_button.click()
            logger.info("Clicked 'Load More' button")
            await asyncio.sleep(random.uniform(5, 10))
            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )            
            return True
        
        except (TimeoutException, NoSuchElementException):
            logger.info("No more 'Load More' button found")
            return False
        
        except Exception as e:
            logger.warning(f"Error clicking 'Load More' button: {e}")
            return False

    async def search_category(self, category: str) -> bool:
        try:
            try:
                search_bar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "SearchBar-input"))
                )
                search_bar.click()
                search_bar.clear()
                logger.info("Clicked initial search bar")
            except Exception:
                logger.warning("Could not click initial search bar")

            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "SearchBar-input-open"))
            )
            search_input.clear()
            await self.type_like_human(search_input, category)
            search_input.send_keys(Keys.RETURN)
            
            logger.info(f"Searched for category: {category}")
            await asyncio.sleep(random.uniform(*SCRAPER_CONFIG['search_delay']))

            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        
        except Exception as e:
            logger.error(f"Error searching for category {category}: {e}")
            return False

    async def scrape_category(self, category: str) -> List[Dict]:
        if not await self.search_category(category):
            return []
        
        category_product_details = []
        page_loads = 0
        
        while page_loads < SCRAPER_CONFIG['max_page_loads_per_category']:
            # Dismiss any popups
            await self.dismiss_qualtrics_popup()
            
            # Extract product links for current page
            current_page_links = self.extract_product_links()
            
            # Process links in a new tab and collect product details
            page_product_details = await self.process_product_links(current_page_links)
            category_product_details.extend(page_product_details)
            
            # Try to click load more button
            if not await self.click_load_more():
                break
                
            await asyncio.sleep(random.uniform(*SCRAPER_CONFIG['load_more_delay']))
            
            page_loads += 1
            logger.info(f"Loaded page {page_loads} for category {category}")
        
        logger.info(f"Finished scraping category {category}. Found {len(category_product_details)} product details.")
        return category_product_details

    async def setup_driver(self) -> Optional[Chrome]:
        try:
            options = self._setup_driver_options()
            self.driver = uc.Chrome(options=options)
            logger.info("Driver setup complete")
            return self.driver
        except WebDriverException as e:
            logger.error(f"Error setting up undetectable webdriver: {e}")
            return None

    async def visit_website(self, url: str, max_retries: int = 3) -> bool:
        if not self.driver:
            logger.error("Driver not initialized")
            return False

        for attempt in range(max_retries):
            try:
                logger.info(f"Visiting {url}... (Attempt {attempt + 1})")
                self.driver.get(url)

                WebDriverWait(self.driver, self.timeout).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                logger.info(f"Successfully loaded {url}")
                await asyncio.sleep(random.uniform(2, 5))
                return True
            
            except Exception as e:
                logger.warning(f"Error visiting {url}: {e}")
                
                if attempt == max_retries - 1:
                    logger.error(f"Failed to load {url} after {max_retries} attempts")
                    return False
                
                await asyncio.sleep(random.uniform(3, 7))

    async def scrape(self) -> List[Dict]:
        try:
            driver = await self.setup_driver()
            if not driver:
                return []
            
            if not await self.visit_website(self.base_url):
                return []

            await self.dismiss_qualtrics_popup()
            
            all_product_details = []
            for category in PRODUCT_CATEGORIES:
                category_product_details = await self.scrape_category(category)
                all_product_details.extend(category_product_details)
            
            return all_product_details
        
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
            return []

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("WebDriver closed successfully")
                except Exception as e:
                    logger.error(f"Error closing WebDriver: {e}")

async def main():
    scraper = MarianosScraper(
        headless=SCRAPER_CONFIG.get('headless', False),
        zip_code=SCRAPER_CONFIG.get('zip_code'),
        timeout=SCRAPER_CONFIG.get('timeout', 30)
    )
    product_details = await scraper.scrape()
    if product_details:
        logger.info(f"Scraped {len(product_details)} products successfully")
    else:
        logger.warning("No products were scraped")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())