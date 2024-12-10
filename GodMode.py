from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
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
import os
import time
import random
import asyncio
import json
import pandas as pd
import undetected_chromedriver as uc


async def setup_driver(user_agent=None, proxy=None):
    try:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-features=NetworkService")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-features=IsolateOrigins")
        options.add_argument("--disable-features=CrossSiteDocumentBlockingIfIsolating")
        options.add_argument("--disable-features=CrossSiteDocumentBlockingAlways")
        options.add_argument("--disable-features=ImprovedCookieControls")
        options.add_argument("--disable-features=GlobalMediaControls")
        options.add_argument("--disable-features=MediaRouter")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--incognito")
        options.add_argument("--window-size=1920,1080")

        if user_agent:
            options.add_argument(f"user-agent={user_agent}")

        driver = uc.Chrome(options=options)
        print("Driver setup complete")
        return driver
    except WebDriverException as e:
        print(f"Error setting up undetectable webdriver: {e}")
        return None


async def visit_website(driver, url, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            print(f"Visiting {url}... (Attempt {retries + 1})")
            driver.get(url)
            await asyncio.sleep(10)
            print(f"Successfully loaded {url}")
            return
        except WebDriverException as e:
            print(f"Error visiting {url}: {e}")
            retries += 1
            if retries < max_retries:
                print(f"Retrying... ({retries}/{max_retries})")
            else:
                print(f"Failed to load {url} after {max_retries} attempts")
                raise


async def clear_cookies(driver):
    try:
        driver.delete_all_cookies()
        print("Cookies cleared.")
        await asyncio.sleep(10)
    except WebDriverException as e:
        print(f"Error clearing cookies: {e}")


async def get_product_links(driver, max_retries=3):
    try:
        retries = 0
        product_links = []
        
        while retries < max_retries:
            try:
                # Wait for product grid containers to load
                print("Waiting for product grid containers...")
                WebDriverWait(driver, 30).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="auto-grid-cell"]'))
                )

                # Fetch product containers
                product_grid_containers = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="auto-grid-cell"]')
                
                # Extract product links
                product_links = [
                    container.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    for container in product_grid_containers
                ]
                
                if product_links:
                    print(f"Found {len(product_links)} product links in current page.")
                    return product_links
                else:
                    print("No product links found. Retrying...")
                    retries += 1
                    # Introduce a random human-like delay
                    time.sleep(random.uniform(2, 5))
                    driver.refresh()  # Refresh the page
                    print(f"Page refreshed. Retry {retries}/{max_retries}.")
            except Exception as e:
                print(f"Error retrieving product links on attempt {retries + 1}: {e}")
                retries += 1
                time.sleep(random.uniform(2, 5))
                driver.refresh()
        
        print("Max retries reached. No product links found.")
        return product_links  # Return the empty list if retries are exhausted
    except Exception as e:
        print(f"Critical error in get_product_links: {e}")
        return []


async def click_load_more(driver, max_retries=3, initial_wait=10, backoff_factor=2):
    for attempt in range(max_retries + 1):
        try:
            print(f"Attempt {attempt + 1} to click 'Load More' button...")

            # Wait for the button to be clickable
            load_more_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.LoadMore__load-more-button'))
            )
            print("Load More button located.")

            # Scroll the button into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)

            # Short pause to ensure UI stability
            await asyncio.sleep(random.uniform(1.5, 3.5))

            # Click the button
            load_more_button.click()
            print("Clicked 'Load More' button successfully.")

            # Wait for the content to load
            await asyncio.sleep(random.uniform(5, 10))

            # Confirm new content is loaded (customize the condition as needed)
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("New content loaded successfully.")
            return True

        except (TimeoutException, ElementClickInterceptedException, NoSuchElementException) as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                wait_time = initial_wait * (backoff_factor ** attempt)
                print(f"Retrying after {wait_time} seconds...")
                await asyncio.sleep(wait_time)

                # Refresh the page on retry
                try:
                    driver.refresh()
                    await asyncio.sleep(random.uniform(5, 10))  # Wait for page reload
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    print("Page refreshed successfully.")
                except Exception as refresh_error:
                    print(f"Error refreshing the page: {refresh_error}")
            else:
                print("Max retries reached. 'Load More' button could not be clicked.")
                return False

        except Exception as unexpected_error:
            print(f"Unexpected error: {unexpected_error}")
            return False

    return False


async def main():
    url = "https://www.marianos.com/search?"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

    driver = await setup_driver(user_agent=user_agent)
    if not driver:
        print("Failed to initialize the driver. Exiting...")
        return

    try:
        await visit_website(driver, url)
        await clear_cookies(driver)

        # Fetch product links
        product_links = await get_product_links(driver)
        print(product_links)

        # Click 'Load More' button
        await click_load_more(driver)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        await asyncio.sleep(10)
        driver.quit()
        print("Driver closed.")

if __name__ == "__main__":
    asyncio.run(main())
