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
    
    # OPTIMIZATION 1: Don't wait for full page load (Images/CSS)
    # 'eager' means: Wait for HTML to parse, but don't wait for images/stylesheets
    options.page_load_strategy = 'eager' 
    
    # OPTIMIZATION 2: Disable Images explicitly to save bandwidth/RAM
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    # Docker path
    options.binary_location = "/usr/bin/google-chrome" 
    return webdriver.Chrome(options=options)

def verify_credentials_browser(roll, password):
    driver = get_driver()
    try:
        driver.get("https://samvidha.iare.ac.in/index.php")
        
        # Wait up to 20s for login box
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        # Check success
        try:
            # Wait for URL to change to home
            wait.until(EC.url_contains("home"))
            return True
        except:
            # Fallback check
            if "Logout" in driver.page_source or "Sign out" in driver.page_source:
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
        
        # Increased wait to 30s for slow server
        wait = WebDriverWait(driver, 30) 
        wait.until(EC.presence_of_element_located((By.NAME, "txt_uname")))
        
        driver.find_element(By.NAME, "txt_uname").send_keys(roll)
        driver.find_element(By.NAME, "txt_pwd").send_keys(password)
        driver.find_element(By.NAME, "but_submit").click()
        
        # Check for success marker or failure
        try:
            wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Sign out")))
        except:
            if "Invalid" in driver.page_source:
                return {"error": "Invalid Credentials"}
            # Continue anyway, sometimes 'Sign out' is hidden in menu

        print("2. Navigating to Attendance...")
        driver.get("https://samvidha.iare.ac.in/pages/student/student_attendance.php")
        
        # Wait for the specific card body that contains the table
        # We look for the "Attendance %" header in the table
        print("   Waiting for table data...")
        try:
            # Wait until any table cell with data appears, or the header
            wait.until(EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'Attendance %')]")))
        except:
            print("   Timeout waiting for table header.")
            # Fallback: Just dump HTML and try parsing anyway
            
        print("3. Parsing...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the table by looking for the specific header "Attendance %"
        target_table = None
        for t in soup.find_all('table'):
            if "Attendance %" in t.text:
                target_table = t
                break
        
        if not target_table:
            # Debugging: Print all table headers found
            headers = [t.text[:50] for t in soup.find_all('table')]
            print(f"   Table not found. Headers seen: {headers}")
            return {"error": "Attendance Table not found (Render Timeout)"}

        # Extract Rows
        # Handle cases where tbody might be missing or present
        rows = target_table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # Columns based on your source code:
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
             return {"error": "Table found but empty data"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Scraper Error: {e}")
        return {"error": f"Server Error: {str(e)}"}
    finally:
        driver.quit()
