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


async def setup_driver(user_agent=None):
    """
    Sets up the Selenium WebDriver with specified options.

    :param user_agent: Custom user agent string (optional)
    :return: Configured WebDriver instance
    """
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
    """
    Navigates to the specified URL using the WebDriver.

    :param driver: Selenium WebDriver instance
    :param url: URL to visit
    """
    try:
        print(f"Visiting {url}...")
        driver.get(url)
        await asyncio.sleep(2)  # Wait for the page to load
        print(f"Successfully loaded {url}")
    except WebDriverException as e:
        print(f"Error visiting {url}: {e}")


async def clear_cookies(driver):
    """
    Clears all cookies in the current WebDriver session.

    :param driver: Selenium WebDriver instance
    """
    try:
        driver.delete_all_cookies()
        print("Cookies cleared.")
    except WebDriverException as e:
        print(f"Error clearing cookies: {e}")


async def refresh_page(driver):
    """
    Refreshes the current page.

    :param driver: Selenium WebDriver instance
    """
    try:
        print("Refreshing the page...")
        driver.refresh()
        await asyncio.sleep(2)  # Wait for the page to reload
        print("Page refreshed.")
    except WebDriverException as e:
        print(f"Error refreshing the page: {e}")


async def main():
    """
    Main function to set up WebDriver, visit the website, and perform basic operations.
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
        await refresh_page(driver)
    finally:
        print("Closing the browser...")
        driver.quit()


# Run the script
if __name__ == "__main__":
    asyncio.run(main())