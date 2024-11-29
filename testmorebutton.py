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
        
        
async def click_load_more(driver, max_retries=3, initial_wait=10, backoff_factor=2):
    for attempt in range(max_retries + 1):
        try:
            print(f"Attempt {attempt + 1} to click 'Load More' button...")

            # Wait for the 'Load More' button to be clickable
            load_more_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.LoadMore__load-more-button'))
            )
            print("Load More button located.")

            # Scroll the button into view
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)

            # Short pause to simulate human interaction
            await asyncio.sleep(random.uniform(1.5, 3.5))

            # Click the button
            load_more_button.click()
            print("Clicked 'Load More' button successfully.")

            # Wait for new content to load
            await asyncio.sleep(random.uniform(5, 10))

            # Confirm the page has loaded
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("Page loaded successfully.")

            # Check for error message
            error_message_element = driver.find_elements(By.CSS_SELECTOR, 'p.heading-m')
            if error_message_element and "problem displaying these items" in error_message_element[0].text:
                print("Error detected after page load: 'problem displaying these items'.")
                
                if attempt < max_retries:
                    # Refresh the page to recover
                    print("Refreshing page to retry...")
                    driver.refresh()
                    await asyncio.sleep(random.uniform(5, 10))  # Wait for page reload
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    print("Page refreshed successfully. Retrying 'Load More'...")
                else:
                    print("Max retries reached. Unable to recover from error.")
                    return False
            else:
                print("No error detected. New content is available.")
                return True  # Successfully loaded new content

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
    
    driver = await setup_driver(user_agent)
    if not driver:
        print("Failed to setup undetectable WebDriver...Exiting.")
        return
    
    try:
        await visit_website(driver, url, max_retries=3)
        await clear_cookies(driver)
        await click_load_more(driver, max_retries=3, initial_wait=10, backoff_factor=2)
    
    finally:
        
        print("Closing the browser...")
        driver.quit()
        
if __name__ == "__main__":
    asyncio.run(main())