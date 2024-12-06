from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException
)
import undetected_chromedriver as uc
import asyncio
import random


async def setup_driver(user_agent=None):
    """
    Sets up the undetectable WebDriver with specified options.
    """
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


async def visit_pages(driver, base_url, start_page=1, max_pages=5, delay_between_pages=10):
    """
    Visits pages incrementally, modifies the URL by appending the 'page' parameter, and processes each page.
    """
    current_page = start_page

    while current_page <= max_pages:
        try:
            # Construct the URL for the current page
            url = f"{base_url}?page={current_page}"
            print(f"Visiting page {current_page}: {url}")

            # Open a new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])

            # Load the page
            driver.get(url)
            print(f"Loaded page {current_page}")

            # Wait to simulate processing the page content
            await asyncio.sleep(delay_between_pages)

            # Process content (placeholder for additional logic)
            print(f"Processed page {current_page}")

            # Close the current tab
            driver.close()

            # Switch back to the parent tab
            driver.switch_to.window(driver.window_handles[0])

            # Increment to the next page
            current_page += 1

        except WebDriverException as e:
            print(f"Error visiting page {current_page}: {e}")
            break  # Stop if there's an issue with navigation

    print("Finished visiting all pages.")


async def main():
    """
    Main function to set up the driver and visit pages.
    """
    base_url = "https://www.marianos.com/search"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    start_page = 1
    max_pages = 10
    delay_between_pages = 20  # Seconds to wait on each page

    # Set up the driver
    driver = await setup_driver(user_agent)
    if not driver:
        print("Failed to setup undetectable WebDriver...Exiting.")
        return

    try:
        # Visit pages incrementally
        await visit_pages(driver, base_url, start_page, max_pages, delay_between_pages)
    finally:
        print("Closing the browser...")
        driver.quit()


if __name__ == "__main__":
    asyncio.run(main())
