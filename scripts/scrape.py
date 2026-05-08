import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_basic_request():
    print("\n=== Testing Basic Request ===")
    try:
        url = "https://www.agentlocker.ai/agent/falkonry"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to get basic info
        title = soup.find('h1').text.strip()
        description = soup.find('p', class_='text-blue-100').text.strip()
        
        print("✅ Basic request successful")
        print(f"Title: {title}")
        print(f"Description: {description}")
    except Exception as e:
        print("❌ Basic request failed:", str(e))

def test_selenium_scraping():
    print("\n=== Testing Selenium Automation ===")
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        driver = webdriver.Chrome(options=chrome_options)
        
        url = "https://www.agentlocker.ai/agent/falkonry"
        driver.get(url)
        
        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "prose"))
        )
        
        # Try to copy protected content
        description = driver.find_element(By.CLASS_NAME, "prose").text
        
        print("✅ Selenium automation successful")
        print(f"Description: {description[:200]}...")
        
        driver.quit()
    except Exception as e:
        print("❌ Selenium automation failed:", str(e))

def test_api_scraping():
    print("\n=== Testing API Endpoints ===")
    try:
        # Try to access potential API endpoints
        base_url = "https://www.agentlocker.ai/api"
        endpoints = [
            f"/agent/falkonry",
            f"/agents/detail/falkonry",
        ]
        
        for endpoint in endpoints:
            response = requests.get(base_url + endpoint)
            if response.status_code == 200:
                print(f"✅ Found accessible API: {endpoint}")
                print(f"Data sample: {str(response.json())[:200]}...")
            else:
                print(f"❌ API endpoint failed: {endpoint}")
    except Exception as e:
        print("❌ API testing failed:", str(e))

def bypass_client_side_protection():
    print("\n=== Testing Client-Side Protection Bypass ===")
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-javascript")  # Disable JavaScript
        
        driver = webdriver.Chrome(options=chrome_options)
        url = "https://www.agentlocker.ai/agent/falkonry"
        driver.get(url)
        
        # Try to extract content with JS disabled
        content = driver.find_element(By.TAG_NAME, "body").text
        
        print("✅ Client-side protection bypass successful")
        print(f"Content sample: {content[:200]}...")
        
        driver.quit()
    except Exception as e:
        print("❌ Client-side protection bypass failed:", str(e))

if __name__ == "__main__":
    print("Starting scraping tests...")
    
    test_basic_request()
    test_selenium_scraping()
    test_api_scraping()
    bypass_client_side_protection()