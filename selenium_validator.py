import requests
from bs4 import BeautifulSoup

# Global headers to mimic a real browser so the server doesn't block us
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_session():
    """
    Creates a session. This is the 'magic' part.
    It automatically handles cookies (PHPSESSID) just like a web browser.
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

def verify_credentials_browser(roll, password):
    """
    Verifies login using a fast HTTP POST request instead of opening a browser.
    """
    session = get_session()
    
    # These keys (txt_uname, etc.) must match the <input name="..."> in the website's HTML
    login_payload = {
        "txt_uname": roll,
        "txt_pwd": password,
        "but_submit": "Submit"  # PHP forms often check if the submit button was pressed
    }
    
    try:
        # Send the login data to the server
        response = session.post("https://samvidha.iare.ac.in/index.php", data=login_payload)
        
        # Check if login failed
        # If the response still contains the login field 'txt_uname', it means we are still on the login page.
        if 'name="txt_uname"' in response.text or "Invalid" in response.text:
            return False
            
        # If we got redirected or the page content changed, login was successful
        return True
    except Exception as e:
        print(f"Error in verification: {e}")
        return False

def fetch_attendance_data(roll, password):
    """
    Logs in and fetches attendance HTML, then parses it with BeautifulSoup.
    """
    session = get_session()
    
    login_payload = {
        "txt_uname": roll,
        "txt_pwd": password,
        "but_submit": "Submit"
    }
    
    try:
        # 1. LOGIN
        print(f"Logging in user: {roll}")
        login_response = session.post("https://samvidha.iare.ac.in/index.php", data=login_payload)
        
        # Verify login success before proceeding
        if 'name="txt_uname"' in login_response.text or "Invalid" in login_response.text:
            return {"error": "Invalid Credentials or Login Failed"}

        # 2. GET ATTENDANCE PAGE
        # The session holds the cookies, so we are authorized to see this page now.
        print("Fetching attendance page...")
        attendance_url = "https://samvidha.iare.ac.in/home?action=stud_att_STD"
        attendance_response = session.get(attendance_url)
        
        # 3. PARSE DATA (BeautifulSoup)
        # This part replaces your Selenium logic of finding elements
        soup = BeautifulSoup(attendance_response.text, 'html.parser')
        
        data = []
        target_table = None
        
        # Logic to find the correct table (same logic you had before, adapted for BS4)
        for table in soup.find_all('table'):
            text_content = table.get_text()
            if "Course Name" in text_content or "Attendance %" in text_content:
                target_table = table
                break
        
        if not target_table:
            return {"error": "Attendance Table not found"}

        # Extract rows
        rows = target_table.find_all('tr')
        
        # Skip header, start processing
        for row in rows:
            cols = row.find_all('td')
            # Check if row has enough columns (Your logic checked for 8)
            if len(cols) >= 8:
                subject = cols[2].get_text(strip=True)
                total_str = cols[5].get_text(strip=True)
                present_str = cols[6].get_text(strip=True)
                percent = cols[7].get_text(strip=True)
                
                # Basic validation
                if total_str.isdigit() and present_str.isdigit():
                    data.append({
                        "subject": subject,
                        "total": int(total_str),
                        "present": int(present_str),
                        "percent": percent
                    })

        if not data:
             return {"error": "Table found but no data rows extracted"}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"Scraping Error: {e}")
        return {"error": str(e)}