PRODUCT_CATEGORIES = [
    "Meat",
    "Seafood", 
    "Produce", 
    "Deli", 
    "Bakery", 
    "Dairy & Eggs", 
    "Pantry", 
    "Beverage", 
    "Breakfast", 
    "Natural & Organic", 
    "Adult Beverage", 
    "Frozen"
]

SCRAPER_CONFIG = {
    'max_page_loads_per_category': 1000,
    'search_delay': (5, 10),
    'load_more_delay': (5, 10)
}