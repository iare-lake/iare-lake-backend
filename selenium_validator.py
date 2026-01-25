import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- KEEP SELENIUM FOR LOGIN CHECK (Only used for Verify) ---
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/google-chrome"
    return webdriver.Chrome(options=options)

def verify_credentials_browser(roll, password):
    # We stick to Selenium for verify as it's safer for session handling logic
    driver = get_driver()
    try:
        driver.get("https://samvidha.iare.ac.in/index.php")
        wait = WebDriverWait(driver, 10)
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

# --- NEW: LIGHTWEIGHT ATTENDANCE SCRAPER (No Chrome!) ---
def fetch_attendance_data(roll, password):
    # 1. Setup Session
    session = requests.Session()
    # Headers to look like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"1. Login via Requests: {roll}")
        login_url = "https://samvidha.iare.ac.in/index.php"
        
        # Payload must match the HTML form exactly
        payload = {
            'txt_uname': roll,
            'txt_pwd': password,
            'but_submit': 'Sign In' 
        }
        
        # Post Credentials
        response = session.post(login_url, data=payload, headers=headers, timeout=10)
        
        # Verify Login by checking URL or Content
        if "Invalid" in response.text or "Sign In" in response.text:
            # Sometimes successful login redirects, so we check if we are NOT on login page
            if "dashboard" not in response.url and "home" not in response.url:
                 return {"error": "Invalid Credentials (Login Failed)"}

        print("2. Fetching Attendance HTML...")
        att_url = "https://samvidha.iare.ac.in/pages/student/student_attendance.php"
        att_response = session.get(att_url, headers=headers, timeout=10)
        
        if att_response.status_code != 200:
            return {"error": "Failed to load attendance page"}

        print("3. Parsing HTML...")
        soup = BeautifulSoup(att_response.text, 'html.parser')
        
        # Find the specific table by header text
        target_table = None
        for t in soup.find_all('table'):
            if "Attendance %" in t.text or "Attended" in t.text:
                target_table = t
                break
        
        if not target_table:
            # Debug: Maybe session expired or headers needed?
            return {"error": "Table not found (Check logs)"}

        # Extract Rows
        data = []
        rows = target_table.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            # Columns based on your provided source code:
            # [2]=Name, [5]=Total, [6]=Present, [7]=%
            if len(cols) >= 8:
                subject = cols[2].text.strip()
                total_str = cols[5].text.strip()
                present_str = cols[6].text.strip()
                percent = cols[7].text.strip()
                
                # Check for "Shortage" or "Satisfactory" to confirm it's a data row
                if total_str.isdigit() and present_str.isdigit():
                    data.append({
                        "subject": subject,
                        "total": int(total_str),
                        "present": int(present_str),
                        "percent": percent
                    })
        
        if not data:
            return {"error": "Data empty"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
