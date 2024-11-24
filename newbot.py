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
import undetected_chromedriver as uc




async def setup_driver(user_agent=None):
    try:
        # Use undetected-chromedriver to create a stealth driver instance
        options = uc.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")  # Open browser in maximized window
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--incognito")  # Open browser in incognito mode
        options.add_argument("--disable-gpu")  # Disable GPU acceleration
        options.add_argument("--window-size=1920,1080")  # Set window size

        # Add a custom user agent if provided
        if user_agent:
            options.add_argument(f'--user-agent={user_agent}')

        # Create an undetectable ChromeDriver instance
        driver = uc.Chrome(options=options)
        print("Undetectable WebDriver setup successful")
        return driver
    except WebDriverException as e:
        print(f"Error setting up undetectable WebDriver: {e}")
        return None




async def visit_website(driver, url, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            print(f"Visiting {url}... (Attempt {retries + 1})")
            driver.get(url)
            await asyncio.sleep(10)  # Wait for the page to load
            print(f"Successfully loaded {url}")
            return  # Exit the function if successful
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
        await asyncio.sleep(10)  # Wait for the cookies to clear
    except WebDriverException as e:
        print(f"Error clearing cookies: {e}")
        
        
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
        await asyncio.sleep(10)
    except Exception as e:
        print(f"An error occurred: {e}")
        
        
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
        
        
async def save_links_to_csv(links, file_name="product_links.csv"):
    try:
        with open(file_name, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Product Link"])  # Header
            for link in links:
                writer.writerow([link])
        print(f"Saved {len(links)} links to {file_name}.")
    except Exception as e:
        print(f"Error saving links to CSV: {e}")


async def scrape_product_details(driver, csv_file="product_details.csv"):
    """Scrape product details from the current page and save to a CSV file."""
    try:
        await asyncio.sleep(20)  # Wait for the page to load
        product_name = driver.find_element(By.CSS_SELECTOR, 'h1[data-testid="product-details-name"]').text
        upc = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="product-details-upc"]').text.replace("UPC: ", "")
        location = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="product-details-location"]').text

        # Extract price
        price_element = driver.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional')
        dollars = price_element.find_element(By.CSS_SELECTOR, 'span.kds-Price-promotional-dropCaps').text
        cents = price_element.find_element(By.CSS_SELECTOR, 'sup.kds-Price-superscript').text.replace(".", "")
        price = f"${dollars}.{cents}"

        # Save the data to a CSV file
        with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([product_name, upc, location, price])

        print(f"Scraped and saved product: {product_name}")
    except Exception as e:
        print(f"Error scraping product details: {e}")


async def visit_links_and_scrape(driver, csv_file="product_details.csv", links_file="product_links.csv"):
    """Visit each link from the CSV file and scrape product details."""
    try:
        # Create the CSV file and write the header
        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Product Name", "Unit", "UPC", "Location", "Price"])

        # Read links from the CSV file
        with open(links_file, mode="r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                link = row[0]
                print(f"Visiting link: {link}")
                driver.get(link)
                await scrape_product_details(driver, csv_file)
    except Exception as e:
        print(f"Error visiting links and scraping: {e}")


async def main():
    url = "https://www.marianos.com/search?"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    
    driver = await setup_driver(user_agent)
    if not driver:
        print("Failed to setup undetectable WebDriver...Exiting.")
        return
    
    try:
        await visit_website(driver, url, max_retries=3)
        await clear_cookies(driver)
        await select_store(driver, "60601")
        
        # Get product links
        product_links = await get_product_links(driver)
        
        # Save links to CSV
        links_file = "product_links.csv"
        if product_links:
            await save_links_to_csv(product_links, links_file)
        
        # Visit each link and scrape product details
        csv_file = "product_details.csv"
        await visit_links_and_scrape(driver, csv_file, links_file)
    finally:
        print("Closing the browser...")
        driver.quit()       

if __name__ == "__main__":
    asyncio.run(main())