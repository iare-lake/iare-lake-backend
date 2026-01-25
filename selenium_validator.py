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
    # Docker path
    options.binary_location = "/usr/bin/google-chrome" 
    return webdriver.Chrome(options=options)

def verify_credentials_browser(roll, password):
    driver = get_driver()
    try:
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        # Smart Wait for Login Form
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        # Wait for URL change or Logout button
        try:
            wait.until(EC.url_contains("home"))
            return True
        except:
            if "Logout" in driver.page_source:
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
        print(f"1. Logging in {roll}...")
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        wait = WebDriverWait(driver, 15) # 15s max wait
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        # Wait for login to complete
        try:
            wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Sign out")))
        except:
            # If we don't see Sign out, check for error
            if "Invalid" in driver.page_source:
                return {"error": "Invalid Credentials"}
            # If still on login page
            if "login.php" in driver.current_url:
                return {"error": "Login Failed (Stuck on login page)"}

        print("2. Navigating to Attendance...")
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        
        # CRITICAL FIX: Wait specifically for the "ATTENDANCE REPORT" text
        # This ensures the table is actually loaded before we try to read it
        try:
            print("   Waiting for table to load...")
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'ATTENDANCE REPORT')]")))
        except:
            print(f"   Timeout! Current URL: {driver.current_url}")
            return {"error": "Attendance page timeout (Render too slow)"}

        print("3. Parsing Table...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the specific card with "ATTENDANCE REPORT"
        # based on the HTML you provided
        report_header = soup.find(lambda tag: tag.name == "h3" and "ATTENDANCE REPORT" in tag.text)
        
        if not report_header:
            return {"error": "Report Header not found in HTML"}
            
        # The table is in the parent card's body
        # We go up to the card, then find the table inside it
        card_body = report_header.find_parent("div", class_="card").find("div", class_="card-body")
        target_table = card_body.find("table")
        
        if not target_table:
            return {"error": "Table tag not found inside Report Card"}

        # Extract Rows
        rows = target_table.find_all('tr')
        print(f"   Found {len(rows)} rows.")

        for row in rows:
            cols = row.find_all('td')
            # Columns: [0]=S.No, [1]=Code, [2]=Name, ..., [5]=Conducted, [6]=Attended, [7]=%
            if len(cols) >= 8:
                subject = cols[2].text.strip()
                total_str = cols[5].text.strip()
                present_str = cols[6].text.strip()
                percent = cols[7].text.strip()
                
                # Validation
                if total_str.isdigit() and present_str.isdigit():
                    data.append({
                        "subject": subject,
                        "total": int(total_str),
                        "present": int(present_str),
                        "percent": percent
                    })

        if not data:
             return {"error": "Table empty (No subjects found)"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Scraper Error: {e}")
        return {"error": f"Server Error: {str(e)}"}
    finally:
        driver.quit()
