from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
import csv
import json
from typing import List, Optional

class MarianosScraperPlaywright:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def setup(self):
        """Initialize the Playwright browser and context with optimized settings."""
        playwright = await async_playwright().start()
        
        # Enhanced browser launch options
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-http2',  # Disable HTTP/2 to avoid protocol errors
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        
        # Enhanced context options
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            ignore_https_errors=True,  # Ignore HTTPS errors
            bypass_csp=True,  # Bypass Content Security Policy
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
        )
        
        # Create page with custom timeout
        self.page = await self.context.new_page()
        self.page.set_default_timeout(60000)  # Increase default timeout to 60 seconds
        
        # Add error handlers
        self.page.on("crashedFrame", lambda frame: print(f"Frame crashed: {frame.url}"))
        self.page.on("requestfailed", lambda request: print(f"Request failed: {request.url}"))
        
        print("Browser setup complete")

    async def visit_website(self, url: str, max_retries: int = 3):
        """Visit the website with enhanced retry logic and error handling."""
        for attempt in range(max_retries):
            try:
                print(f"Visiting {url}... (Attempt {attempt + 1})")
                
                # Clear browser cache and cookies before each attempt
                await self.context.clear_cookies()
                
                # Use a more lenient wait_until condition
                response = await self.page.goto(
                    url,
                    wait_until="domcontentloaded",  # Changed from networkidle
                    timeout=60000  # 60 second timeout
                )
                
                if response is None:
                    print("No response received")
                    continue
                    
                if not response.ok:
                    print(f"Response status: {response.status}")
                    continue
                
                # Wait for critical elements to be visible
                try:
                    await self.page.wait_for_selector('body', timeout=10000)
                except PlaywrightTimeoutError:
                    print("Timeout waiting for body element")
                    continue
                
                print(f"Successfully loaded {url}")
                return True
                
            except PlaywrightTimeoutError as e:
                print(f"Timeout error visiting {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                print(f"Error visiting {url}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                    
        raise Exception(f"Failed to load {url} after {max_retries} attempts")

    async def select_store(self, zip_code: str):
        """Select a store using the provided zip code with enhanced error handling."""
        try:
            print("Selecting a store...")
            
            # Wait for and click location button with retry
            async def click_with_retry(selector, max_attempts=3):
                for i in range(max_attempts):
                    try:
                        await self.page.wait_for_selector(selector, state="visible", timeout=10000)
                        await self.page.click(selector)
                        return True
                    except Exception as e:
                        print(f"Attempt {i+1} failed for {selector}: {e}")
                        if i < max_attempts - 1:
                            await asyncio.sleep(2)
                return False
            
            # Location button click
            if not await click_with_retry("#CurrentModality-button-A11Y-FOCUS-ID"):
                raise Exception("Failed to click location button")
            
            await asyncio.sleep(2)
            
            # Cancel icon click
            if not await click_with_retry("#ModalitySelector--CloseButton"):
                print("Warning: Failed to click cancel button, continuing...")
            
            await asyncio.sleep(2)
            
            # Location button click again
            if not await click_with_retry("#CurrentModality-button-A11Y-FOCUS-ID"):
                raise Exception("Failed to click location button second time")
            
            # Click pickup option
            if not await click_with_retry('[data-testid="ModalityOption-Button-PICKUP"]'):
                raise Exception("Failed to click pickup option")
            
            # Enter zip code
            try:
                await self.type_like_human('[data-testid="PostalCodeSearchBox-input"]', zip_code)
            except Exception as e:
                print(f"Error entering zip code: {e}")
                raise
            
            # Click search
            if not await click_with_retry('button[aria-label="Search"]'):
                raise Exception("Failed to click search button")
            
            await asyncio.sleep(3)
            
            # Select store
            if not await click_with_retry('[data-testid="SelectStore-53100516"]'):
                raise Exception("Failed to select store")
            
            await asyncio.sleep(5)
            print("Store selection complete")
            
        except Exception as e:
            print(f"Error in store selection: {e}")
            raise

    async def get_product_links(self) -> List[str]:
        """Extract product links from the current page."""
        try:
            # Wait for product grid to load
            await self.page.wait_for_selector('div[data-testid="auto-grid-cell"]')
            
            # Extract all product links
            links = await self.page.evaluate("""
                () => Array.from(
                    document.querySelectorAll('div[data-testid="auto-grid-cell"] a')
                ).map(a => a.href)
            """)
            
            print(f"Found {len(links)} product links")
            return links
            
        except Exception as e:
            print(f"Error getting product links: {e}")
            return []

    async def scrape_product_details(self) -> Optional[dict]:
        """Scrape details from a product page."""
        try:
            await asyncio.sleep(2)  # Wait for dynamic content
            
            # Extract product details using Playwright's evaluation
            details = await self.page.evaluate("""
                () => {
                    const name = document.querySelector('h1[data-testid="product-details-name"]')?.innerText;
                    const upc = document.querySelector('span[data-testid="product-details-upc"]')?.innerText.replace("UPC: ", "");
                    const location = document.querySelector('span[data-testid="product-details-location"]')?.innerText;
                    
                    const priceElement = document.querySelector('mark.kds-Price-promotional');
                    let price = null;
                    if (priceElement) {
                        const dollars = priceElement.querySelector('.kds-Price-promotional-dropCaps')?.innerText;
                        const cents = priceElement.querySelector('sup.kds-Price-superscript')?.innerText.replace(".", "");
                        price = `$${dollars}.${cents}`;
                    }
                    
                    return { name, upc, location, price };
                }
            """)
            
            return details if all(details.values()) else None
            
        except Exception as e:
            print(f"Error scraping product details: {e}")
            return None

    async def save_links_to_csv(self, links: List[str], filename: str = "product_links.csv"):
        """Save product links to a CSV file."""
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Product Link"])
                for link in links:
                    writer.writerow([link])
            print(f"Saved {len(links)} links to {filename}")
        except Exception as e:
            print(f"Error saving links: {e}")

    async def process_all_products(self, links: List[str], output_file: str = "product_details.csv"):
        """Process all products and save details to CSV."""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Product Name", "UPC", "Location", "Price"])
                
                for link in links:
                    try:
                        await self.page.goto(link, wait_until="networkidle")
                        details = await self.scrape_product_details()
                        
                        if details:
                            writer.writerow([
                                details['name'],
                                details['upc'],
                                details['location'],
                                details['price']
                            ])
                            print(f"Processed: {details['name']}")
                    except Exception as e:
                        print(f"Error processing {link}: {e}")
                        continue
                    
                    await asyncio.sleep(1)  # Polite delay between requests
                    
        except Exception as e:
            print(f"Error in batch processing: {e}")

    async def cleanup(self):
        """Clean up Playwright resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

async def main():
    scraper = MarianosScraperPlaywright()
    
    try:
        await scraper.setup()
        
        # Try alternative URLs if the main one fails
        urls = [
            "https://www.marianos.com/search?"
        ]
        
        success = False
        for url in urls:
            try:
                await scraper.visit_website(url)
                success = True
                break
            except Exception as e:
                print(f"Failed to load {url}: {e}")
                continue
        
        if not success:
            raise Exception("Failed to load any URLs")
            
        await scraper.select_store("60601")
        
        # Get and save product links
        product_links = await scraper.get_product_links()
        if product_links:
            await scraper.save_links_to_csv(product_links)
            await scraper.process_all_products(product_links)
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if scraper.browser:
            await scraper.cleanup()

if __name__ == "__main__":
    asyncio.run(main())