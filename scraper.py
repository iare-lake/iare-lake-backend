# PLAN B: OPTIMIZED SELENIUM (Add 'selenium' and 'webdriver-manager' to requirements.txt)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

def get_driver():
    options = Options()
    # OPTIMIZATIONS FOR RENDER
    options.add_argument("--headless=new") # Faster headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    
    # BLOCK IMAGES & CSS (Massive Speed Boost)
    prefs = {
        "profile.managed_default_content_settings.images": 2, 
        "profile.managed_default_content_settings.stylesheets": 2
    }
    options.add_experimental_option("prefs", prefs)
    
    # Don't wait for the page to fully load (just get the HTML)
    options.page_load_strategy = 'eager' 
    
    return webdriver.Chrome(options=options)

def fetch_attendance_fast(roll, password):
    driver = get_driver()
    try:
        # 1. Login
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        # Fast input
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        
        # Click and wait briefly
        btn = driver.find_element(By.NAME, "but_submit")
        btn.click()
        
        # 2. Force Navigate (Don't wait for redirect, just go)
        # Give it 0.5s for the cookie to set
        time.sleep(0.5) 
        driver.get("https://samvidha.iare.ac.in/home?action=stud_att_STD")
        
        # 3. Parse with BS4 (Faster than Selenium)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # ... Insert your Parsing Logic Here ...
        # (Copy the parsing logic from the previous code)
        
        # For testing:
        if "Course Name" in driver.page_source:
             return {"success": True, "data": []} # Add real data parsing here
        else:
             return {"error": "Login Failed"}

    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()

def verify_credentials_fast(roll, password):
    # Reuse the function above or simplify it
    res = fetch_attendance_fast(roll, password)
    return "success" in res
