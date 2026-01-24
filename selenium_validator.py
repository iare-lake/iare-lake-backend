from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def verify_credentials_browser(roll_number, password):
    # Chrome Options for Headless (Server) Environment
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Render-specific location for Chrome (Managed by Dockerfile)
    # If testing locally on Windows, comment this line out:
    chrome_options.binary_location = "/usr/bin/google-chrome" 

    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print(f"Checking {roll_number}...")
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        # Wait logic could be added here, but sleep is simple for now
        time.sleep(2)

        driver.find_element(By.NAME, "txt_uname").send_keys(roll_number)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()

        time.sleep(4) # Wait for login

        current_url = driver.current_url
        page_source = driver.page_source
        
        driver.quit()

        # Success Conditions
        if "dashboard" in current_url or "home" in current_url:
            return True
        if "Logout" in page_source or "Sign Out" in page_source:
            return True
            
        return False

    except Exception as e:
        print(f"Error: {e}")
        return False