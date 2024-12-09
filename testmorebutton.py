import asyncio
import random
import logging
import json
import os
from typing import Optional, List, Dict, Any

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedWebScraper:
    def __init__(
        self, 
        base_url: str, 
        output_dir: str = 'scraper_output',
        max_retries: int = 3,
        timeout: int = 30,
        user_agent: Optional[str] = None
    ):
        """
        Initialize the advanced web scraper with configurable parameters.
        
        :param base_url: The base URL to scrape
        :param output_dir: Directory to save scraped data
        :param max_retries: Maximum number of retries for operations
        :param timeout: Default timeout for web operations
        :param user_agent: Custom user agent string
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agent = user_agent or self._generate_random_user_agent()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Proxy and IP rotation setup (placeholder for future enhancement)
        self.proxy_list: List[str] = []
        self.current_proxy: Optional[str] = None

    @staticmethod
    def _generate_random_user_agent() -> str:
        """
        Generate a randomized user agent to reduce detection.
        
        :return: Random user agent string
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        return random.choice(user_agents)

    async def setup_driver(self) -> Optional[uc.Chrome]:
        """
        Setup an undetectable Chrome WebDriver with advanced configurations.
        
        :return: Configured WebDriver or None if setup fails
        """
        try:
            options = uc.ChromeOptions()
            
            # Advanced browser configurations
            options.add_argument("--disable-notifications")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--incognito")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            
            # Add user agent
            options.add_argument(f'--user-agent={self.user_agent}')
            
            # Experimental: Add more stealth options
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Create the undetectable driver
            driver = uc.Chrome(options=options)
            
            # Additional stealth techniques
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Undetectable WebDriver setup successful")
            return driver

        except Exception as e:
            logger.error(f"Error setting up undetectable WebDriver: {e}")
            return None

    async def visit_website(self, driver: uc.Chrome, url: str) -> bool:
        """
        Visit a website with advanced error handling and retry mechanism.
        
        :param driver: WebDriver instance
        :param url: URL to visit
        :return: True if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Visiting {url}... (Attempt {attempt + 1})")
                driver.get(url)
                
                # Wait for page to load
                WebDriverWait(driver, self.timeout).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Random human-like delay
                await asyncio.sleep(random.uniform(2, 5))
                
                logger.info(f"Successfully loaded {url}")
                return True
            
            except Exception as e:
                logger.warning(f"Error visiting {url}: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to load {url} after {self.max_retries} attempts")
                    return False

    async def advanced_load_more(self, driver: uc.Chrome) -> bool:
        """
        Advanced 'Load More' button clicking with sophisticated error handling.
        
        :param driver: WebDriver instance
        :return: True if successful, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Load More attempt {attempt + 1}")
                
                # Wait for the button, using multiple possible selectors
                load_more_selectors = [
                    'button.LoadMore__load-more-button',
                    'div[data-testid="load-more"]',
                    'a.load-more-link',
                    'button#load-more'
                ]
                
                load_more_button = None
                for selector in load_more_selectors:
                    try:
                        load_more_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not load_more_button:
                    logger.warning("No 'Load More' button found")
                    return False
                
                # Scroll to button smoothly
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                    load_more_button
                )
                
                # Human-like interaction simulation
                await asyncio.sleep(random.uniform(1.5, 3.5))
                
                # Click with JavaScript to avoid potential overlay issues
                driver.execute_script("arguments[0].click();", load_more_button)
                
                # Wait for content to load
                await asyncio.sleep(random.uniform(5, 10))
                
                # Verify content load
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                logger.info("Successfully clicked 'Load More'")
                return True
            
            except Exception as e:
                logger.warning(f"Load More error: {e}")
                
                if attempt < self.max_retries - 1:
                    # Refresh page and wait
                    driver.refresh()
                    await asyncio.sleep(random.uniform(5, 10))
                else:
                    logger.error("Failed to click 'Load More' after multiple attempts")
                    return False

    async def scrape_data(self, driver: uc.Chrome) -> List[Dict[str, Any]]:
        """
        Scrape data from the webpage.
        
        :param driver: WebDriver instance
        :return: List of scraped data dictionaries
        """
        scraped_data = []
        
        try:
            # Example: Find all product elements (customize as needed)
            product_elements = driver.find_elements(By.CSS_SELECTOR, '.product-item')
            
            for element in product_elements:
                try:
                    product_data = {
                        'name': element.find_element(By.CSS_SELECTOR, '.product-name').text,
                        'price': element.find_element(By.CSS_SELECTOR, '.product-price').text,
                        # Add more fields as needed
                    }
                    scraped_data.append(product_data)
                except Exception as e:
                    logger.warning(f"Error extracting product data: {e}")
        
        except Exception as e:
            logger.error(f"Error during data scraping: {e}")
        
        return scraped_data

    async def save_data(self, data: List[Dict[str, Any]], filename: str = 'scraped_data'):
        """
        Save scraped data to JSON and CSV files.
        
        :param data: List of scraped data dictionaries
        :param filename: Base filename for output files
        """
        if not data:
            logger.warning("No data to save")
            return
        
        # Save JSON
        json_path = os.path.join(self.output_dir, f'{filename}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Save CSV (requires pandas)
        import pandas as pd
        csv_path = os.path.join(self.output_dir, f'{filename}.csv')
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        logger.info(f"Data saved: {json_path}, {csv_path}")

    async def main_scraping_workflow(self):
        """
        Main asynchronous scraping workflow.
        """
        driver = await self.setup_driver()
        if not driver:
            logger.error("Failed to setup WebDriver")
            return
        
        try:
            # Visit website
            if not await self.visit_website(driver, self.base_url):
                return
            
            # Load more content
            content_loaded = await self.advanced_load_more(driver)
            if not content_loaded:
                logger.warning("Could not load more content")
            
            # Scrape data
            scraped_data = await self.scrape_data(driver)
            
            # Save data
            await self.save_data(scraped_data)
        
        except Exception as e:
            logger.error(f"Unexpected error in scraping workflow: {e}")
        
        finally:
            # Always close the driver
            if driver:
                driver.quit()
                logger.info("Browser closed successfully")

async def main():
    """
    Entry point for the scraping script.
    """
    scraper = AdvancedWebScraper(
        base_url="https://www.marianos.com/search?",
        output_dir='marianos_data',
        max_retries=3,
        timeout=30
    )
    
    await scraper.main_scraping_workflow()

if __name__ == "__main__":
    asyncio.run(main())