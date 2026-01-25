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

# ... (Imports remain the same) ...

def fetch_attendance_data(roll, password):
    driver = get_driver()
    data = []
    
    try:
        print(f"Logging in for {roll}...")
        driver.get("https://samvidha.iare.ac.in/index.php")
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        time.sleep(4) 
        if "Invalid" in driver.page_source:
            return {"error": "Invalid Credentials"}

        print("Navigating to attendance...")
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        time.sleep(5) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # FIND THE CORRECT TABLE
        # We look for the table that has "Attendance %" in its header
        tables = soup.find_all('table')
        target_table = None
        
        for t in tables:
            if "Attendance %" in t.text or "Attended" in t.text:
                target_table = t
                break
        
        if not target_table:
            return {"error": "Attendance Report table not found"}

        # PARSE ROWS
        # The HTML shows a <thead> and <tbody> structure.
        tbody = target_table.find('tbody')
        if not tbody:
            # Fallback if tbody is missing (sometimes browsers render differently)
            rows = target_table.find_all('tr')
        else:
            rows = tbody.find_all('tr')

        print(f"Found {len(rows)} rows.")
        
        for row in rows:
            cols = row.find_all('td')
            
            # Based on your HTML:
            # col[2] = Course Name
            # col[5] = Conducted (Total)
            # col[6] = Attended (Present)
            # col[7] = %
            
            if len(cols) >= 8: # Ensure row has enough columns
                subject = cols[2].text.strip()
                total_str = cols[5].text.strip()
                present_str = cols[6].text.strip()
                percent = cols[7].text.strip()
                
                # Check if numbers are valid
                if total_str.isdigit() and present_str.isdigit():
                    data.append({
                        "subject": subject,
                        "total": int(total_str),
                        "present": int(present_str),
                        "percent": percent
                    })

        if not data:
             return {"error": "Table found but empty data"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Scraper Error: {e}")
        return {"error": str(e)}
    finally:
        driver.quit()
