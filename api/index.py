from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
from selenium import webdriver
import time

app = Flask(__name__)

# Function to extract Product Title
def get_title(soup):
    try:
        title_h1 = soup.find("h1", class_='ProductInfoCard__ProductName-sc-113r60q-10 dsuWXl')
        title = title_h1.text.strip()
    except AttributeError:
        title = ""
    return title

# Function to extract Product Price
def get_price(soup):
    try:
        price_div = soup.find("div", class_='ProductVariants__PriceContainer-sc-1unev4j-7 gGENtH')
        price = price_div.text.strip()
    except AttributeError:
        price = ""
    return price

# Function to extract Product Images
def get_images(soup):
    try:
        img_tags = soup.find_all("img", class_='ProductCarousel__CarouselImage-sc-11ow1fv-4')
        imgs = [img_tag.get('src') for img_tag in img_tags]
    except AttributeError:
        imgs = []
    return imgs

# Function to extract Product Description
def get_description(soup):
    try:
        h_containers = soup.find_all("p", class_='ProductAttribute__ProductAttributesName-sc-dyoysr-5 heSLbJ')
        d_containers = soup.find_all("div", class_='ProductAttribute__ProductAttributesDescription-sc-dyoysr-6 jJVAqC')

        data = [{'heading': h_container.find("span").text.strip(), 'description': d_container.text.strip()} 
                for h_container, d_container in zip(h_containers, d_containers)]
    except AttributeError:
        data = []
    return data

# Function to scrape product details
def scrape_product_details(searchQuery):
    options = webdriver.FirefoxOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    
    # Load the webpage
    driver.get(f"https://blinkit.com/s/?q={searchQuery}")
    time.sleep(5)

    # Simulate scrolling to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        print("scrolling")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for the page to load new content
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Get the HTML content after scrolling
    print("Scrolling done")
    soup = BeautifulSoup(driver.page_source, "html.parser")

    product_a_tags = soup.find_all('a', attrs={'data-test-id': 'plp-product'})
    hrefs = [product_a_tag.get('href') for product_a_tag in product_a_tags]

    print(hrefs)
    print(len(hrefs))

    product_details = {"title": [], "price": [], "images": [], "description": []}

    i = 0

    # Loop for extracting product details from each link 
    for href in hrefs:
        new_url = "https://www.blinkit.com" + href
        driver.get(new_url)
        new_soup = BeautifulSoup(driver.page_source, "html.parser")

        product_details["title"].append(get_title(new_soup))
        product_details["price"].append(get_price(new_soup))
        product_details["images"].append(get_images(new_soup))
        product_details["description"].append(get_description(new_soup))

        print(product_details)

        i += 1
        print(i)

    driver.quit()  # Close the browser
    return product_details

@app.route('/')
def index():
    return "Welcome to the Blinkit Product Scraper!"

# API route to scrape product details
@app.route('/scrape-blinkit', methods=['POST'])
def scrape_product():
    search_query = request.json.get('searchQuery')
    if search_query:
        product_details = scrape_product_details(search_query)
        return jsonify(product_details)
    else:
        return jsonify({"error": "Search query not provided"}), 400

if __name__ == '__main__':
    app.run()
