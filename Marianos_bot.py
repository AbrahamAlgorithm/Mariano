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
    WebDriverException
)
import os
import time
import asyncio
import json
import csv

def save_page_source(driver, file_name="page_source.json"):
    try:
        # Fetch the page source
        page_source = driver.page_source
        print("Page source fetched successfully.")

        # Save the page source to a .json file
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump({"page_source": page_source}, file, ensure_ascii=False, indent=4)
        print(f"Page source saved to {file_name}.")

    except Exception as e:
        print(f"An error occurred while saving the page source: {e}")

async def setup_driver(user_agent=None):
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")  # Open browser in maximized window
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--incognito")  # Open browser in incognito mode
    
    if user_agent:
        options.add_argument(f'--user-agent={user_agent}')
    
    try:
        driver = Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )
        print("WebDriver setup successful.")
        return driver
    except WebDriverException as e:
        print(f"Error setting up WebDriver: {e}")
        return None


async def visit_website(driver, url):
    try:
        print(f"Visiting {url}...")
        driver.get(url)
        await asyncio.sleep(10)  # Wait for the page to load
        print(f"Successfully loaded {url}")
    except WebDriverException as e:
        print(f"Error visiting {url}: {e}")


async def clear_cookies(driver):
    try:
        driver.delete_all_cookies()
        print("Cookies cleared.")
        await asyncio.sleep(10)  # Wait for the cookies to clear
    except WebDriverException as e:
        print(f"Error clearing cookies: {e}")


async def refresh_page(driver):
    try:
        print("Refreshing the page...")
        driver.refresh()
        await asyncio.sleep(100)  # Wait for the page to reload
        print("Page refreshed.")
    except WebDriverException as e:
        print(f"Error refreshing the page: {e}")
        
        
async def type_like_human(element, text, delay=0.2):
    """Simulates typing text into an input field with a delay between each character."""
    for char in text:
        element.send_keys(char)
        await asyncio.sleep(delay)
        
        
async def select_store(driver, zip_code):
    try:
        print("Selecting a store...")

        # Wait for the location input button and click it
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
        print("Clicking on the location button again.")
        await asyncio.sleep(10)
        print("Clicked on the location button.")

        # Wait for the change store button and click it
        change_store_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="ModalityOption-Button-PICKUP"]'))
        )
        change_store_button.click()
        print("Clicked on the change store button.")

        # Wait for the zip search input
        zip_search_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="PostalCodeSearchBox-input"]'))
        )
        zip_search_input.clear()

        # Type the zip code asynchronously with a delay to mimic human typing
        await type_like_human(zip_search_input, zip_code)
        print(f"Typed the zip code: {zip_code}")

        # Click the search icon
        search_icon = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Search"]'))
        )
        search_icon.click()
        print("Clicked on the search icon.")

        # Wait for the specific store in the search results and click it
        store = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="SelectStore-53100516"]'))
        )
        store.click()
        print("Clicked on the selected store.")

        print("Selected store successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")


async def _products(driver):
    try:
        await asyncio.sleep(10)  # Wait for the page to load
        print("Navigating to the Sale Items section...")
        link_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.kds-Link.kds-Link--implied.kds-ProminentLink.kds-ProminentLink--l.headerSection-link.break-words'))
        )
        # driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
        await asyncio.sleep(5)
        link_element.click()
        print("Clicked on 'Keep Shopping' link.")

        # Wait for the next page to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.kds-Link.kds-Link--implied.kds-ProminentLink.kds-ProminentLink--l.headerSection-link.break-words[href="/products/start-my-cart"]'))
        )

        # Click on the "Shop All" link
        shop_all_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.kds-Link.kds-Link--implied.kds-ProminentLink.kds-ProminentLink--l.headerSection-link.break-words[href="/products/start-my-cart"]'))
        )
        shop_all_element.click()
        print("Clicked on 'Shop All' link.")
        await asyncio.sleep(10)  # Wait for the product page to load

        # Now we're on the product page. From here, you can implement further scraping.
        print("Successfully navigated to the product page. Ready for scraping!")
        # save_page_source(driver, file_name="product_page.json")
        
        
        await asyncio.sleep(10)

    except TimeoutException:
        print("Timed out while trying to navigate to the Sale Items section.")
    except Exception as e:
        print(f"An error occurred during navigation: {e}")


async def get_product_links(driver):
    try:
        # Find all the product grid containers
        product_grid_containers = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="auto-grid-cell"]')

        # Extract the links from each product grid container
        product_links = []
        for container in product_grid_containers:
            link_element = container.find_element(By.CSS_SELECTOR, 'a')
            product_links.append(link_element.get_attribute('href'))

        print(f"Found {len(product_links)} product links.")
        print(product_links)
        await asyncio.sleep(20)
        return product_links
    except Exception as e:
        print(f"Error getting product links: {e}")
        return []


async def main():
    """
    Main function to set up WebDriver, visit the website, and scrape product details.
    """
    url = "https://www.marianos.com/"  # Target website
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

    driver = await setup_driver(user_agent)
    if not driver:
        print("Failed to initialize WebDriver. Exiting.")
        return

    try:
        await visit_website(driver, url)
        await clear_cookies(driver)
        await select_store(driver, zip_code="60610")
        await _products(driver)
        await get_product_links(driver)
    finally:
        print("Closing the browser...")
        driver.quit()


# Run the script
if __name__ == "__main__":
    asyncio.run(main())