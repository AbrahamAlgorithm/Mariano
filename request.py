import requests
from bs4 import BeautifulSoup

baseurl = 'https://www.marianos.com/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

r = requests.get(f'https://www.marianos.com/products/start-my-cart')
soup = BeautifulSoup(r.content, 'lxml')
productlist = soup.find_all('div', class_='AutoGrid-cell min-w-0')

productlinks = []

for items in productlist:
    for link in item.find_all('a', href=True):
        productlinks.append(baseurl = link['href'])
        
        
print(productlinks)