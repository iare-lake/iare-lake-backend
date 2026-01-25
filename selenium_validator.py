from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Docker path
    options.binary_location = "/usr/bin/google-chrome" 
    return webdriver.Chrome(options=options)

def verify_credentials_browser(roll, password):
    driver = get_driver()
    try:
        driver.get("https://samvidha.iare.ac.in/index.php")
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        time.sleep(3)
        if "dashboard" in driver.current_url or "home" in driver.current_url or "Logout" in driver.page_source:
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
        # Login
        driver.get("https://samvidha.iare.ac.in/index.php")
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        time.sleep(3)

        # Go to Attendance
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        time.sleep(2)

        # Parse Table
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find table with "Subject" in header
        target = None
        for t in soup.find_all('table'):
            if "Subject" in t.text:
                target = t
                break
        
        if not target:
            return {"error": "Table not found"}

        rows = target.find_all('tr')
        for row in rows[1:]: # Skip header
            cols = row.find_all('td')
            if len(cols) >= 4:
                data.append({
                    "subject": cols[1].text.strip(),
                    "total": int(cols[2].text.strip()),
                    "present": int(cols[3].text.strip()),
                    "percent": cols[4].text.strip() if len(cols) > 4 else "0"
                })

        return {"success": True, "data": data}
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()
