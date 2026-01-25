import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- SETUP CHROME ---
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Speed up: Don't wait for images/css
    options.page_load_strategy = 'eager'
    # Render Path
    options.binary_location = "/usr/bin/google-chrome"
    return webdriver.Chrome(options=options)

# --- LOGIN CHECK (Used by Certificate) ---
def verify_credentials_browser(roll, password):
    driver = get_driver()
    try:
        driver.get("https://samvidha.iare.ac.in/index.php")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        try:
            wait.until(EC.url_contains("home"))
            return True
        except:
            if "Logout" in driver.page_source: return True
            return False
    except:
        return False
    finally:
        driver.quit()

# --- HYBRID ATTENDANCE FETCH (Selenium Login -> Requests Fetch) ---
def fetch_attendance_data(roll, password):
    driver = get_driver()
    session = requests.Session()
    
    try:
        print(f"1. Selenium Login: {roll}...")
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()

        # Wait for login success (Dashboard URL)
        try:
            wait.until(EC.url_contains("home"))
        except:
            if "Invalid" in driver.page_source:
                return {"error": "Invalid Credentials"}
            # If we didn't reach home and no invalid msg, risky but might have worked
        
        # --- MAGIC STEP: STEAL COOKIES ---
        print("2. Extracting Session Cookies...")
        selenium_cookies = driver.get_cookies()
        
        # Transfer cookies to Requests Session
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'])
            
        # We can now close Selenium to save RAM
        driver.quit()
        
        # --- FAST STEP: DOWNLOAD WITH REQUESTS ---
        print("3. Downloading Attendance via Requests...")
        att_url = "https://samvidha.iare.ac.in/pages/student/student_attendance.php"
        
        # Mimic browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://samvidha.iare.ac.in/home'
        }
        
        response = session.get(att_url, headers=headers)
        
        if response.status_code != 200:
            return {"error": "Failed to access attendance page"}

        # --- PARSE HTML ---
        print("4. Parsing Data...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find table by specific header text from your source code
        target_table = None
        for t in soup.find_all('table'):
            if "Attendance %" in t.text or "Attended" in t.text:
                target_table = t
                break
        
        if not target_table:
            # Debug: print title to see if we are on login page
            print("Page Title:", soup.title.text if soup.title else "No Title")
            return {"error": "Table not found (Session might have failed)"}

        data = []
        rows = target_table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # Columns: [2]=Course Name, [5]=Total, [6]=Present, [7]=%
            if len(cols) >= 8:
                subject = cols[2].text.strip()
                total_str = cols[5].text.strip()
                present_str = cols[6].text.strip()
                percent = cols[7].text.strip()
                
                if total_str.isdigit() and present_str.isdigit():
                    data.append({
                        "subject": subject,
                        "total": int(total_str),
                        "present": int(present_str),
                        "percent": percent
                    })
        
        if not data:
            return {"error": "Table found but empty"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Error: {e}")
        try:
            driver.quit() # Ensure driver closes on error
        except:
            pass
        return {"error": str(e)}
