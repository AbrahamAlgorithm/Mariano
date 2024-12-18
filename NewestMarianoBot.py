import asyncio
import random
import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException
)

# Configuration imports (simulated for this example)
PRODUCT_CATEGORIES = [
    "Meat", "Seafood", "Produce", "Deli", "Bakery", 
    "Dairy & Eggs", "Pantry", "Beverage", "Breakfast", 
    "Natural & Organic", "Adult Beverage", "Frozen"
]

SCRAPER_CONFIG = {
    'max_page_loads_per_category': 1000,
    'search_delay': (5, 10),
    'load_more_delay': (5, 10),
    'zip_code': '60610'
}

class MarianosScraperV2:
    def __init__(self, url="https://www.marianos.com", user_agent=None):
        self.url = url
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        self.driver = None
        self.product_data = []
        self.timeout = 30

    async def setup_driver(self):
        try:
            options = uc.ChromeOptions()
            options.add_argument("--disable-notifications")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--incognito")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            if self.user_agent:
                options.add_argument(f'--user-agent={self.user_agent}')

            self.driver = uc.Chrome(options=options)
            return self.driver
        except WebDriverException as e:
            print(f"Error setting up undetectable WebDriver: {e}")
            return None

    async def visit_website(self):
        try:
            print(f"Visiting {self.url}...")
            self.driver.get(self.url)
            await asyncio.sleep(10)
            print(f"Successfully loaded {self.url}")
        except WebDriverException as e:
            print(f"Error visiting {self.url}: {e}")
            raise

    async def select_store(driver, zip_code):
        try:
            print("Selecting a store...")
            location_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "CurrentModality-button-A11Y-FOCUS-ID"))
            )
            location_button.click()
            await asyncio.sleep(10)
            print("Clicked on the location button.")

            cancel_icon = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "ModalitySelector--CloseButton"))
            )
            cancel_icon.click()
            print("Clicked on the cancel icon.")
            await asyncio.sleep(5)
            
            location_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "CurrentModality-button-A11Y-FOCUS-ID"))
            )
            location_button.click()
            await asyncio.sleep(10)

            change_store_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="ModalityOption-Button-PICKUP"]'))
            )
            change_store_button.click()
            print("Clicked on the change store button.")

            zip_search_input = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="PostalCodeSearchBox-input"]'))
            )
            zip_search_input.clear()

            await type_like_human(zip_search_input, zip_code)
            print(f"Typed the zip code: {zip_code}")

            search_icon = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Search"]'))
            )
            search_icon.click()
            print("Clicked on the search icon.")

            store = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="SelectStore-53100516"]'))
            )
            store.click()
            print("Selected store successfully!")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"An error occured: {e}")

    async def type_like_human(self, element, text, delay=0.2):
        for char in text:
            element.send_keys(char)
            await asyncio.sleep(delay)

    async def search_category(self, category):
        try:
            print(f"Searching for category: {category}")
            
            # Attempt to click and clear initial search bar
            try:
                search_bar = WebDriverWait(self.driver, self.timeout).until(
                    EC.element_to_be_clickable((By.ID, "SearchBar-input"))
                )
                search_bar.click()
                search_bar.clear()
            except Exception:
                print("Could not click initial search bar. Trying alternative method.")

            # Find and interact with search input
            search_input = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.ID, "SearchBar-input-open"))
            )
            search_input.clear()
            
            # Type category with human-like typing
            await self.type_like_human(search_input, category)
            search_input.send_keys(Keys.RETURN)
            
            print(f"Searched for category: {category}")
            
            # Wait for page to load
            await asyncio.sleep(random.uniform(*SCRAPER_CONFIG['search_delay']))
            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            return True
        except Exception as e:
            print(f"Error searching for category {category}: {e}")
            return False

    async def get_product_links(self):
        try:
            # Wait for product grid containers to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="auto-grid-cell"]'))
            )

            # Fetch product containers
            product_grid_containers = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="auto-grid-cell"]')
            
            # Extract product links
            product_links = [
                container.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                for container in product_grid_containers
            ]
            
            print(f"Found {len(product_links)} product links in current page.")
            return product_links
        except Exception as e:
            print(f"Error retrieving product links: {e}")
            return []

    async def scrape_product_details(driver):
        try:
            await asyncio.sleep(10)
            
            # Get product details
            product_name = driver.find_element(By.CSS_SELECTOR, 'h1[data-testid="product-details-name"]').text
            upc = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="product-details-upc"]').text.replace("UPC: ", "")
            upc = f"#{upc}"
            location = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="product-details-location"]').text

            try:
                # Find the breadcrumb navigation
                breadcrumb_elements = driver.find_elements(By.CSS_SELECTOR, 'a.kds-Link.kds-Link--inherit.mr-4')

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
                price_element = driver.find_element(By.CSS_SELECTOR, '[typeof="Price"]')
                price = f"${price_element.get_attribute('value')}"
            except NoSuchElementException:
                price_element = driver.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional')
                dollars = price_element.find_element(By.CSS_SELECTOR, 'span.kds-Price-promotional-dropCaps').text
                cents = price_element.find_element(By.CSS_SELECTOR, 'sup.kds-Price-superscript').text.replace(".", "")
                price = f"${dollars}.{cents}"

            try:
                image_element = driver.find_element(By.CSS_SELECTOR, '.ProductImages-image')
                image_url = image_element.get_attribute('src')
            except NoSuchElementException:
                image_url = "No image available"

            # Append data to the global list
            product_data.append({
                'UPC': upc,
                'Category': category,
                'Title': product_name,
                'Location': location,
                'Price': price,
                'Image URL': image_url
            })

            print(f"Scraped product: {product_name}")
            
        except Exception as e:
            print(f"Error scraping product details: {e}")

    async def click_load_more(self):
        try:
            load_more_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.LoadMore__load-more-button'))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)
            await asyncio.sleep(random.uniform(1.5, 3.5))
            load_more_button.click()
            
            await asyncio.sleep(random.uniform(5, 10))
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    async def scrape_category_products(self, category):
        if not await self.search_category(category):
            return

        page_loads = 0
        while page_loads < SCRAPER_CONFIG['max_page_loads_per_category']:
            # Get product links on current page
            product_links = await self.get_product_links()
            
            # Scrape each product
            for link in product_links:
                await self.scrape_product_details(link)
            
            # Try to load more products
            if not await self.click_load_more():
                break
            
            page_loads += 1
            await asyncio.sleep(random.uniform(*SCRAPER_CONFIG['load_more_delay']))

    async def save_to_excel(self, filename="product_details.xlsx"):
        df = pd.DataFrame(self.product_data)
        
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Products')
        
        workbook = writer.book
        worksheet = writer.sheets['Products']
        
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Column width and header formatting...
        worksheet.set_column('A:A', 15)  # UPC
        worksheet.set_column('B:B', 20)  # Category
        worksheet.set_column('C:C', 50)  # Title
        worksheet.set_column('D:D', 15)  # Location
        worksheet.set_column('E:E', 10)  # Price
        worksheet.set_column('F:F', 50)  # Image URL
    
        # Write headers with format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Add auto-filter
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

        writer.close()
        print(f"Excel file saved as {filename}")

    async def run(self):
        try:
            self.driver = await self.setup_driver()
            if not self.driver:
                return

            await self.visit_website()
            await self.select_store(SCRAPER_CONFIG['zip_code'])

            # Scrape products for each category
            for category in PRODUCT_CATEGORIES:
                print(f"Starting scraping for category: {category}")
                await self.scrape_category_products(category)

            # Save collected data
            await self.save_to_excel()

        finally:
            if self.driver:
                self.driver.quit()

async def main():
    scraper = MarianosScraperV2()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())