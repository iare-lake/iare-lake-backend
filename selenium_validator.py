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
    # REMOVED 'eager' strategy. We will wait for full load now.
    options.binary_location = "/usr/bin/google-chrome"
    return webdriver.Chrome(options=options)

def verify_credentials_browser(roll, password):
    driver = get_driver()
    try:
        driver.get("https://samvidha.iare.ac.in/index.php")
        wait = WebDriverWait(driver, 20)
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
        
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        # Explicitly wait for the dashboard to load
        try:
            wait.until(EC.url_contains("home"))
            print("   Login successful. URL is now home.")
        except:
            print("   Warning: URL did not change to home. Checking source...")
            if "Invalid" in driver.page_source:
                return {"error": "Invalid Credentials"}

        print("2. Navigating to Attendance...")
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        
        # Hard wait to ensure render completes
        time.sleep(8)
        
        # --- DEBUGGING PRINTS ---
        print(f"   Current URL: {driver.current_url}")
        print(f"   Page Title: {driver.title}")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table')
        print(f"   Tables found: {len(tables)}")
        
        if len(tables) > 0:
            print(f"   First Table Headers: {tables[0].text[:50]}...")
        else:
            print("   CRITICAL: No tables found in HTML source.")
            # If no tables, return error immediately
            return {"error": "Page loaded but no tables found."}
        # ------------------------

        # SEARCH STRATEGY: BROAD
        target_table = None
        
        # 1. Try finding by Source Code Header "Course Name"
        for t in tables:
            if "Course Name" in t.text or "Subject" in t.text:
                target_table = t
                break
        
        # 2. Fallback: Just take the biggest table (The report is always the biggest)
        if not target_table:
            print("   Target header not found. Selecting table with most rows...")
            target_table = max(tables, key=lambda t: len(t.find_all('tr')))

        if not target_table:
            return {"error": "Attendance Table logic failed"}

        # Extract Rows
        rows = target_table.find_all('tr')
        print(f"   Processing {len(rows)} rows from target table.")
        
        for row in rows:
            cols = row.find_all('td')
            # The indices might shift if mobile view kicks in, but let's try standard
            # [2]=Course Name, [5]=Total, [6]=Present, [7]=%
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
             return {"error": "Table parsed but data empty"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
    finally:
        driver.quit()
