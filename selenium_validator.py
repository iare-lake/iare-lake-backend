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
    options.add_argument("--window-size=1920,1080") # Big window to ensure table renders
    
    # Render Path
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
        print(f"1. Selenium Login: {roll}...")
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        # Check if login worked
        try:
            wait.until(EC.url_contains("home"))
        except:
            if "Invalid" in driver.page_source:
                return {"error": "Invalid Credentials"}
            # Continue if we are just stuck on a loading screen but url changed

        print("2. Navigating to Attendance...")
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        
        # Wait for the table to appear using a simpler check
        time.sleep(6) # Safe wait for Render
        
        print("3. Parsing Data...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the table based on the SOURCE CODE you provided
        # We look for a <th> that contains "Course Name"
        target_table = None
        for t in soup.find_all('table'):
            if "Course Name" in t.text:
                target_table = t
                break
        
        if not target_table:
            print("debug: Table not found. Current URL:", driver.current_url)
            return {"error": "Attendance Table not found"}

        # Extract Rows
        rows = target_table.find_all('tr')
        
        # Based on your HTML Source Code:
        # Index 0: S.No
        # Index 1: Course Code
        # Index 2: Course Name <--- TARGET
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
                
                # Check for "Satisfactory" or "Shortage" in the last col to confirm it's a data row
                if total_str.isdigit() and present_str.isdigit():
                    data.append({
                        "subject": subject,
                        "total": int(total_str),
                        "present": int(present_str),
                        "percent": percent
                    })
        
        if not data:
            return {"error": "Table found but is empty"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
    finally:
        driver.quit()
