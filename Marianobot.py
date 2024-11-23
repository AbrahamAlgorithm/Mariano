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
import csv
from datetime import datetime

async def setup_driver(user_agent=None):
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--incognito")
    
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
        await asyncio.sleep(10)
        print(f"Successfully loaded {url}")
    except WebDriverException as e:
        print(f"Error visiting {url}: {e}")

async def clear_cookies(driver):
    try:
        driver.delete_all_cookies()
        print("Cookies cleared.")
        await asyncio.sleep(10)
    except WebDriverException as e:
        print(f"Error clearing cookies: {e}")

async def type_like_human(element, text, delay=0.2):
    for char in text:
        element.send_keys(char)
        await asyncio.sleep(delay)

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
        print("Clicking on the location button again.")
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
    except Exception as e:
        print(f"An error occurred: {e}")

async def _products(driver):
    try:
        await asyncio.sleep(10)
        print("Navigating to the Sale Items section...")
        link_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.kds-Link.kds-Link--implied.kds-ProminentLink.kds-ProminentLink--l.headerSection-link.break-words'))
        )
        await asyncio.sleep(5)
        link_element.click()
        print("Clicked on 'Keep Shopping' link.")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.kds-Link.kds-Link--implied.kds-ProminentLink.kds-ProminentLink--l.headerSection-link.break-words[href="/products/start-my-cart"]'))
        )

        shop_all_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.kds-Link.kds-Link--implied.kds-ProminentLink.kds-ProminentLink--l.headerSection-link.break-words[href="/products/start-my-cart"]'))
        )
        shop_all_element.click()
        print("Clicked on 'Shop All' link.")
        await asyncio.sleep(10)

        print("Successfully navigated to the product page. Ready for scraping!")
        await asyncio.sleep(10)

    except TimeoutException:
        print("Timed out while trying to navigate to the Sale Items section.")
    except Exception as e:
        print(f"An error occurred during navigation: {e}")

async def get_product_links(driver):
    # Create CSV file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f'product_links_{timestamp}.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Product Link'])  # Header
        
        page_number = 1
        total_links = 0
        
        while True:
            try:
                print(f"Scraping page {page_number}...")
                await asyncio.sleep(10)
                
                # Find all product links
                product_containers = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="auto-grid-cell"]'))
                )

                # Extract and save links from current page
                for container in product_containers:
                    try:
                        link = container.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                        writer.writerow([link])
                        total_links += 1
                    except (StaleElementReferenceException, NoSuchElementException) as e:
                        print(f"Error extracting link: {e}")
                        continue

                print(f"Saved {len(product_containers)} links from page {page_number}")
                
                # Try to find and click the next button
                try:
                    next_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.kds-Pagination-next[aria-label="Next page"]'))
                    )
                    next_button.click()
                    
                    # Check if next button is disabled
                    if 'disabled' in next_button.get_attribute('class').split():
                        print("Reached the last page")
                        break
                    
                    # # Scroll to next button and click
                    # driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    # await asyncio.sleep(2)
                    # next_button.click()
                    print(f"Navigating to page {page_number + 1}")
                    page_number += 1
                    await asyncio.sleep(10)
                    
                except (TimeoutException, NoSuchElementException):
                    print("No more pages to scrape")
                    break
                    
            except Exception as e:
                print(f"Error processing page {page_number}: {e}")
                break

    print(f"Scraping completed! Total links collected: {total_links}")
    print(f"Links saved to: {csv_filename}")
    return total_links

async def main():
    url = "https://www.marianos.com/"
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
        total_links = await get_product_links(driver)
        print(f"Successfully scraped {total_links} product links")
        
    finally:
        print("Closing the browser...")
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())