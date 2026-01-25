from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup # We use this to parse the table easily
import time

# --- SHARED CHROME SETUP ---
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Docker path (Keep this for Render)
    chrome_options.binary_location = "/usr/bin/google-chrome"
    return webdriver.Chrome(options=chrome_options)

def verify_credentials_browser(roll_number, password):
    driver = get_driver()
    try:
        driver.get("https://samvidha.iare.ac.in/index.php")
        driver.find_element(By.NAME, "txt_uname").send_keys(roll_number)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        time.sleep(3) # Wait for login
        
        url = driver.current_url
        if "dashboard" in url or "home" in url or "Logout" in driver.page_source:
            return True
        return False
    except:
        return False
    finally:
        driver.quit()

def fetch_attendance_data(roll, password):
    driver = get_driver()
    data = []
    
    try:
        # 1. Login
        driver.get("https://samvidha.iare.ac.in/index.php")
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        time.sleep(3)

        # 2. Check Login Success
        if "Invalid" in driver.page_source:
            return {"error": "Invalid Credentials"}

        # 3. Navigate to Attendance Page
        # This is the standard IARE attendance URL
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        time.sleep(2)

        # 4. Scrape Table
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the main data table (usually has class 'table')
        tables = soup.find_all('table')
        target_table = None
        
        # Look for the table that has "Subject" in the header
        for t in tables:
            if "Subject" in t.text:
                target_table = t
                break
        
        if not target_table:
            return {"error": "Attendance table not found"}

        # Extract Rows
        rows = target_table.find_all('tr')
        for row in rows[1:]: # Skip header
            cols = row.find_all('td')
            if len(cols) >= 4:
                # Clean up text
                subject = cols[1].text.strip()
                total = cols[2].text.strip()
                present = cols[3].text.strip()
                percent = cols[4].text.strip() if len(cols) > 4 else "0"
                
                # Filter out garbage rows
                if subject and total.isdigit():
                    data.append({
                        "subject": subject,
                        "total": int(total),
                        "present": int(present),
                        "percent": percent
                    })

        return {"success": True, "data": data}

    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()
