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
        zip_code: Optional[str] = None,
        proxies: Optional[List[Dict[str, str]]] = None
    ):
        self.base_url = base_url
        self.user_agent = user_agent or self._generate_user_agent()
        self.headless = headless
        self.timeout = timeout
        self.zip_code = zip_code
        self.driver: Optional[Chrome] = None
        self.all_product_links: List[str] = []
        self.unique_product_links: set = set()
        
        # Proxy configuration
        self.proxies = proxies or []
        self.current_proxy = None

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
        
        # # Advanced CDP Detection Evasion
        # options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        
        # Add proxy if available
        if self.current_proxy:
            proxy_arg = f"--proxy-server={self.current_proxy['http']}"
            options.add_argument(proxy_arg)
        
        # Randomize user agent
        options.add_argument(f"user-agent={self.user_agent}")
        
        if self.headless:
            options.add_argument("--headless")
        
        return options

    def _rotate_proxy(self):
        """Rotate to the next proxy in the list."""
        if not self.proxies:
            logger.warning("No proxies configured")
            return None
        
        # If no current proxy or current proxy is the last in the list, start over
        if not self.current_proxy or self.proxies.index(self.current_proxy) == len(self.proxies) - 1:
            self.current_proxy = self.proxies[0]
        else:
            current_index = self.proxies.index(self.current_proxy)
            self.current_proxy = self.proxies[current_index + 1]
        
        logger.info(f"Rotating to proxy: {self.current_proxy['http']}")
        return self.current_proxy

    async def setup_driver(self) -> Optional[Chrome]:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Rotate proxy for each driver setup attempt
                if self.proxies:
                    self._rotate_proxy()
                
                options = self._setup_driver_options()
                self.driver = uc.Chrome(options=options)
                
                # Additional CDP detection evasion
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": self.user_agent,
                    "platform": "Windows"
                })
                
                # Modify navigator.webdriver property
                self.driver.execute_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                logger.info("Driver setup complete")
                return self.driver
            
            except WebDriverException as e:
                logger.error(f"Error setting up undetectable webdriver (Attempt {attempt + 1}): {e}")
                
                if attempt == max_attempts - 1:
                    logger.error("Failed to setup driver after maximum attempts")
                    return None
                
                await asyncio.sleep(random.uniform(3, 7))
        
        return None

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

    async def select_store(self) -> bool:
        if not self.zip_code:
            logger.warning("No zip code provided for store selection")
            return False

        try:
            logger.info("Starting store selection process...")

            location_button = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.ID, "CurrentModality-button-A11Y-FOCUS-ID"))
            )
            location_button.click()
            await asyncio.sleep(random.uniform(5, 10))

            try:
                cancel_icon = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ModalitySelector--CloseButton"))
                )
                cancel_icon.click()
                await asyncio.sleep(random.uniform(2, 5))
            except Exception:
                logger.info("No cancel icon found or could not click it")

            location_button = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.ID, "CurrentModality-button-A11Y-FOCUS-ID"))
            )
            location_button.click()
            await asyncio.sleep(random.uniform(5, 10))

            change_store_button = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="ModalityOption-Button-PICKUP"]'))
            )
            change_store_button.click()
            logger.info("Clicked on the change store button")

            zip_search_input = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="PostalCodeSearchBox-input"]'))
            )
            zip_search_input.clear()
            
            await self.type_like_human(zip_search_input, self.zip_code)
            logger.info(f"Typed the zip code: {self.zip_code}")

            search_icon = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Search"]'))
            )
            search_icon.click()
            logger.info("Clicked on the search icon")

            store = WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="SelectStore-53100516"]'))
            )
            store.click()
            logger.info("Selected store successfully!")

            await asyncio.sleep(random.uniform(5, 10))
            return True

        except Exception as e:
            logger.error(f"An error occurred during store selection: {e}")
            return False

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

    async def scrape_category(self, category: str) -> List[str]:
        if not await self.search_category(category):
            return []
        
        category_links = []
        page_loads = 0
        
        while page_loads < SCRAPER_CONFIG['max_page_loads_per_category']:
            await self.dismiss_qualtrics_popup()
            new_links = self.extract_product_links()
            category_links.extend(new_links)
            if not await self.click_load_more():
                break
                
            await asyncio.sleep(random.uniform(*SCRAPER_CONFIG['load_more_delay']))
            
            page_loads += 1
            logger.info(f"Loaded page {page_loads} for category {category}")
        
        logger.info(f"Finished scraping category {category}. Found {len(category_links)} links.")
        return category_links

    async def scrape(self) -> List[str]:
        try:
            driver = await self.setup_driver()
            if not driver:
                return []
            
            if not await self.visit_website(self.base_url):
                return []

            await self.dismiss_qualtrics_popup()
            
            if self.zip_code:
                store_selected = await self.select_store()
                if not store_selected:
                    logger.warning("Failed to select store, continuing anyway")

            all_product_links = []
            for category in PRODUCT_CATEGORIES:
                category_links = await self.scrape_category(category)
                all_product_links.extend(category_links)
            
            return all_product_links
        
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
    try:
        # Configure proxies (you should replace these with actual working proxies)
        proxies = [
            {"http": "http://proxy1.example.com:8080"},
            {"http": "http://proxy2.example.com:8080"},
            {"http": "http://proxy3.example.com:8080"}
        ]
        
        # Configure scraper with specific parameters
        scraper = MarianosScraper(
            headless=SCRAPER_CONFIG.get('headless', False),
            zip_code=SCRAPER_CONFIG.get('zip_code'),
            timeout=SCRAPER_CONFIG.get('timeout', 30),
            proxies=proxies  # Add proxy list
        )
        
        # Run the scraper
        product_links = await scraper.scrape()
        
        # Save results to CSV
        if product_links:
            df = pd.DataFrame({'product_link': product_links})
            output_file = SCRAPER_CONFIG.get('output_file', 'marianos_product.csv')
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(product_links)} product links to {output_file}")
        else:
            logger.warning("No product links were found")
    
    except Exception as e:
        logger.error(f"Unexpected error in main execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())