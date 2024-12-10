import asyncio
import random
import logging
from typing import List, Optional

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MarianosScraper:
    def __init__(
        self, 
        base_url: str = "https://www.marianos.com/search?",
        user_agent: Optional[str] = None,
        headless: bool = False,
        timeout: int = 30,
        max_page_loads: int = 50
    ):
        self.base_url = base_url
        self.user_agent = user_agent or self._generate_user_agent()
        self.headless = headless
        self.timeout = timeout
        self.max_page_loads = max_page_loads
        self.driver: Optional[Chrome] = None
        self.product_links: List[str] = []
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
                
                # Wait for page to load
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
            
            # Extract product links
            new_links = [
                container.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                for container in product_containers
            ]
            
            # Filter out duplicates
            unique_new_links = [
                link for link in new_links 
                if link not in self.unique_product_links
            ]
            
            self.unique_product_links.update(unique_new_links)
            self.product_links.extend(unique_new_links)
            
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

    async def scrape(self, search_term: Optional[str] = None) -> List[str]:
        try:
            driver = await self.setup_driver()
            if not driver:
                return []
            url = f"{self.base_url}{f'q={search_term}' if search_term else ''}"

            if not await self.visit_website(url):
                return []
            self.extract_product_links()
            page_loads = 0
            while page_loads < self.max_page_loads:
                if not await self.click_load_more():
                    break
                new_links = self.extract_product_links()

                if not new_links:
                    break
                page_loads += 1
                logger.info(f"Loaded page {page_loads}")

            return list(self.unique_product_links)

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver closed")

async def main():
    scraper = MarianosScraper(max_page_loads=50)
    
    try:
        product_links = await scraper.scrape(search_term="bread")
        
        if product_links:
            pd.DataFrame(product_links, columns=['Product URL']).to_csv('mariano_product_links.csv', index=False)
            logger.info(f"Saved {len(product_links)} unique product links to CSV")
    
    except Exception as e:
        logger.error(f"Scraping process failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())