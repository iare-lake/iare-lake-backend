import requests
from bs4 import BeautifulSoup

# Use a real browser User-Agent to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://samvidha.iare.ac.in",
    "Referer": "https://samvidha.iare.ac.in/index.php"
}

def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

def verify_credentials_browser(roll, password):
    session = get_session()
    login_url = "https://samvidha.iare.ac.in/index.php"
    
    try:
        # STEP 1: GET the login page to find hidden tokens
        print("1. Fetching login page...")
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # STEP 2: Scrape ALL hidden inputs automatically
        payload = {}
        for input_tag in soup.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                payload[name] = value

        # STEP 3: Override with actual credentials
        payload["txt_uname"] = roll
        payload["txt_pwd"] = password
        
        # Ensure the submit button key is present (required by PHP)
        if "but_submit" not in payload:
            payload["but_submit"] = "" 

        # STEP 4: POST the data back
        print("2. Sending login request...")
        post_response = session.post(login_url, data=payload)

        # STEP 5: Validate Login
        if 'name="txt_uname"' in post_response.text or "Invalid" in post_response.text:
            print("Login Failed: Check credentials or server response.")
            return False
            
        print("Login Successful!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def fetch_attendance_data(roll, password):
    session = get_session()
    login_url = "https://samvidha.iare.ac.in/index.php"
    
    try:
        # --- LOGIN FLOW (Same as above) ---
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        payload = {}
        for input_tag in soup.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                payload[name] = value

        payload["txt_uname"] = roll
        payload["txt_pwd"] = password
        if "but_submit" not in payload: payload["but_submit"] = ""

        login_response = session.post(login_url, data=payload)

        if 'name="txt_uname"' in login_response.text or "Invalid" in login_response.text:
            return {"error": "Invalid Credentials"}

        # --- FETCH DATA ---
        print("3. Fetching attendance...")
        # Note: The URL usually changes to 'home' after login. 
        # Make sure this specific URL is correct for your college portal.
        attendance_url = "https://samvidha.iare.ac.in/home?action=stud_att_STD"
        
        data_response = session.get(attendance_url)
        soup = BeautifulSoup(data_response.text, 'html.parser')
        
        # --- PARSING LOGIC ---
        data = []
        target_table = None
        
        for t in soup.find_all('table'):
            if "Course Name" in t.text or "Attendance %" in t.text:
                target_table = t
                break
        
        if not target_table:
            return {"error": "Attendance Table not found (Login might be successful, but page layout changed)"}

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
