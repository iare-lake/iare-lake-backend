import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Headers are CRITICAL. They make the server think we are a real Chrome browser.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://samvidha.iare.ac.in",
    "Referer": "https://samvidha.iare.ac.in/index.php"
}

def get_session():
    """Create a browser session with memory (cookies)"""
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

def login_to_portal(session, roll, password):
    """
    Handles the login logic.
    Returns True if success, False if invalid credentials.
    """
    login_url = "https://samvidha.iare.ac.in/index.php"
    
    try:
        # 1. GET the page first to load hidden tokens and cookies
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Find where the form submits to (Action URL)
        form = soup.find("form")
        if not form:
            return False
            
        action = form.get("action")
        # Handle cases where action is empty or "#"
        if action and action != "#" and "javascript" not in action:
            post_url = urljoin(login_url, action)
        else:
            post_url = login_url

        # 3. Automatically grab all hidden input fields (CSRF tokens, viewstates)
        payload = {}
        for inp in soup.find_all("input"):
            if inp.get("name"):
                payload[inp["name"]] = inp.get("value", "")

        # 4. Fill in user details
        payload["txt_uname"] = roll
        payload["txt_pwd"] = password
        
        # Ensure the submit button key exists (PHP often requires this)
        if "but_submit" not in payload:
            payload["but_submit"] = "Submit"

        # 5. POST the data (The actual login)
        post_response = session.post(post_url, data=payload)

        # 6. Check if login worked
        # If we see the username input field again, login failed.
        if 'name="txt_uname"' in post_response.text or "Invalid" in post_response.text:
            return False
            
        return True

    except Exception as e:
        print(f"Login Exception: {e}")
        return False

def verify_credentials_fast(roll, password):
    """Called by /api/verify"""
    session = get_session()
    return login_to_portal(session, roll, password)

def fetch_attendance_fast(roll, password):
    """Called by /api/attendance"""
    session = get_session()
    
    # 1. Login
    if not login_to_portal(session, roll, password):
        return {"error": "Invalid Credentials"}

    # 2. Fetch Attendance Page
    # Note: The session cookie from login_to_portal is automatically used here
    attendance_url = "https://samvidha.iare.ac.in/home?action=stud_att_STD"
    
    try:
        response = session.get(attendance_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 3. Parse Table
        data = []
        target_table = None

        # Robust search for the correct table
        for table in soup.find_all('table'):
            txt = table.get_text()
            if "Course Name" in txt or "Attendance %" in txt:
                target_table = table
                break
        
        if not target_table:
            return {"error": "Attendance table not found. (Login might have timed out)"}

        rows = target_table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # Adjust column index based on your table structure
            if len(cols) >= 8:
                data.append({
                    "subject": cols[2].get_text(strip=True),
                    "total": int(cols[5].get_text(strip=True)),
                    "present": int(cols[6].get_text(strip=True)),
                    "percent": cols[7].get_text(strip=True)
                })

        if not data:
            return {"error": "Table found but empty"}
            
        return {"success": True, "data": data}

    except Exception as e:
        return {"error": str(e)}
