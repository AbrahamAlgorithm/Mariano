import csv
import aiohttp
import asyncio
from playwright.sync_api import sync_playwright

# Read URLs from the CSV file
def read_urls_from_csv(file_path):
    urls = []
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            urls.append(row["Product Link"])
    return urls

# Async function to visit a URL
async def fetch_url(session, url):
    try:
        async with session.get(url) as response:
            status = response.status
            print(f"Visited {url} - Status Code: {status}")
            return status
    except Exception as e:
        print(f"Error visiting {url}: {e}")
        return None

# Async function to visit all URLs
async def visit_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        print("All URLs visited.")

# Main function
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set `headless=False` for GUI
        page = browser.new_page()
        page.goto("https://www.example.com")
        print("Page Title:", page.title())
        browser.close()

if __name__ == "__main__":
    main()
