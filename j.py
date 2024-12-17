import asyncio
import random
import logging
from typing import List, Optional

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
                    logger.warning("Store selection failed")
                    return []

            for category in PRODUCT_CATEGORIES:
                logger.info(f"Scraping category: {category}")
                links = await self.scrape_category(category)
                logger.info(f"Collected {len(links)} links from category {category}")

            logger.info(f"Scraping complete. Total product links found: {len(self.all_product_links)}")
            return self.all_product_links

        finally:
            if self.driver:
                self.driver.quit()

async def main():
    scraper = MarianosScraper(
        headless=True, 
        zip_code="60611"  # Replace with your desired ZIP code
    )
    product_links = await scraper.scrape()

    if product_links:
        df = pd.DataFrame({"Product Links": product_links})
        df.to_csv("marianos_product_links.csv", index=False)
        logger.info("Saved product links to 'marianos_product_links.csv'")
    else:
        logger.error("No product links found!")

if __name__ == "__main__":
    asyncio.run(main())
