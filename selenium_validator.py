from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Speed up loading
    options.page_load_strategy = 'eager'
    options.binary_location = "/usr/bin/google-chrome"
    return webdriver.Chrome(options=options)

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

def fetch_attendance_data(roll, password):
    driver = get_driver()
    data = []
    
    try:
        print(f"1. Login: {roll}...")
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        # Wait for Home/Dashboard
        try:
            wait.until(EC.url_contains("home"))
        except:
            if "Invalid" in driver.page_source:
                return {"error": "Invalid Credentials"}

        print("2. Navigating to Attendance...")
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        
        # WAIT for the table header "Course Name" (From your source code)
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'Course Name')]")))
        except:
            print("   Wait timed out. Trying to parse anyway...")

        print("3. Parsing Table...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the table containing "Course Name"
        target_table = None
        for t in soup.find_all('table'):
            if "Course Name" in t.text:
                target_table = t
                break
        
        if not target_table:
            # Fallback: Look for "Attendance %" if Course Name is missing
            for t in soup.find_all('table'):
                if "Attendance %" in t.text:
                    target_table = t
                    break
            
            if not target_table:
                return {"error": "Attendance Table not found (Check Render Logs)"}

        # Extract Rows
        rows = target_table.find_all('tr')
        print(f"   Found {len(rows)} rows.")
        
        # COLUMN MAPPING (Based on your Source Code):
        # Index 2: Course Name
        # Index 5: Conducted (Total)
        # Index 6: Attended (Present)
        # Index 7: Attendance %
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 8:
                subject = cols[2].text.strip()
                total_str = cols[5].text.strip()
                present_str = cols[6].text.strip()
                percent = cols[7].text.strip()
                
                # Filter out empty or header rows
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
        return {"error": str(e)}
    finally:
        driver.quit()
