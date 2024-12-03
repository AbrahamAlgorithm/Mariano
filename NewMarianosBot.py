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

async def setup_driver(user_agent=None):
    try:
        options = uc.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--incognito")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        if user_agent:
            options.add_argument(f'--user-agent={user_agent}')

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
        print(f"An error occurred: {e}")

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

# List to store all product data
product_data = []

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

async def process_links_in_new_tab(driver, links):
    main_window = driver.current_window_handle
    driver.execute_script("window.open('');")
    await asyncio.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    
    try:
        for link in links:
            try:
                print(f"Visiting link in new tab: {link}")
                driver.get(link)
                await scrape_product_details(driver)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error processing link {link}: {e}")
                continue
    finally:
        driver.close()
        driver.switch_to.window(main_window)

def save_to_excel(data, filename="product_details.xlsx"):
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel writer object with xlsxwriter engine
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    
    # Write DataFrame to excel
    df.to_excel(writer, index=False, sheet_name='Products')
    
    # Get workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Products']
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    # Set column widths
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
    
    # Save the workbook
    writer.close()
    
    print(f"Excel file saved as {filename}")

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
        
        while True:
            product_links = await get_product_links(driver, max_retries=3)
            
            if product_links:
                await process_links_in_new_tab(driver, product_links)
            
            if not await click_load_more(driver, max_retries=3, initial_wait=10, backoff_factor=2):
                print("No more products to load. Scraping completed.")
                break
            
            await asyncio.sleep(5)
            
    finally:
        # Save all collected data to Excel file
        save_to_excel(product_data)
        print("Closing the browser...")
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())