import mechanicalsoup
from bs4 import BeautifulSoup

def get_browser():
    # Create a browser object that mimics Chrome
    browser = mechanicalsoup.StatefulBrowser(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    )
    return browser

def verify_credentials_fast(roll, password):
    browser = get_browser()
    login_url = "https://samvidha.iare.ac.in/index.php"

    try:
        # 1. Open Login Page
        print(f"DEBUG: Opening {login_url}")
        browser.open(login_url)

        # 2. Select the Login Form
        # We select the form that has the username input
        browser.select_form('form[action="index.php"]') 
        
        # Fallback: If action isn't explicitly index.php, just pick the first form
        if not browser.get_current_form():
            browser.select_form()

        # 3. Fill Details
        # MechanicalSoup automatically keeps existing hidden tokens!
        browser["txt_uname"] = roll
        browser["txt_pwd"] = password

        # 4. Submit
        # This automatically finds the submit button and sends its value
        response = browser.submit_selected()

        # 5. Check Success
        # If we are still on the login page (input field exists), it failed
        if 'name="txt_uname"' in response.text or "Invalid" in response.text:
            print("DEBUG: Login Failed - Invalid Credentials or Blocked")
            return False
            
        print("DEBUG: Login Successful")
        return True

    except Exception as e:
        print(f"DEBUG: Error {e}")
        return False

def fetch_attendance_fast(roll, password):
    browser = get_browser()
    login_url = "https://samvidha.iare.ac.in/index.php"
    
    try:
        # --- LOGIN FLOW ---
        browser.open(login_url)
        
        # Select form
        browser.select_form('form[action="index.php"]')
        if not browser.get_current_form():
             browser.select_form() # Select first form if explicit select fails

        # Fill data
        browser["txt_uname"] = roll
        browser["txt_pwd"] = password
        
        # Submit
        response = browser.submit_selected()

        # Validate
        if 'name="txt_uname"' in response.text:
            return {"error": "Invalid Credentials (Login Failed)"}

        # --- FETCH ATTENDANCE ---
        print("DEBUG: Fetching attendance...")
        attendance_url = "https://samvidha.iare.ac.in/home?action=stud_att_STD"
        
        # MechanicalSoup maintains the session/cookies automatically
        browser.open(attendance_url)
        
        # Use BS4 to parse the page content (browser.page is a BS4 object)
        page = browser.page
        
        # --- PARSING (Same Logic) ---
        data = []
        target_table = None

        for t in page.find_all('table'):
            txt = t.get_text()
            if "Course Name" in txt or "Attendance %" in txt:
                target_table = t
                break
        
        if not target_table:
            return {"error": "Attendance Table not found"}

        rows = target_table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 8:
                subject = cols[2].get_text(strip=True)
                total_str = cols[5].get_text(strip=True)
                present_str = cols[6].get_text(strip=True)
                percent = cols[7].get_text(strip=True)
                
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
        return {"error": str(e)}
