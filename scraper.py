import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 1. Use a standard Browser Header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://samvidha.iare.ac.in",
    "Referer": "https://samvidha.iare.ac.in/index.php"
}

def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session

def login_to_portal(session, roll, password):
    login_url = "https://samvidha.iare.ac.in/index.php"
    
    try:
        # Step 1: Get the Login Page to find the correct button value
        print(f"DEBUG: Fetching {login_url}...")
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Step 2: Prepare the Login Data
        payload = {
            "txt_uname": roll,
            "txt_pwd": password
        }

        # --- CRITICAL FIX: FIND THE EXACT SUBMIT BUTTON VALUE ---
        submit_btn = soup.find("input", {"name": "but_submit"})
        if submit_btn:
            btn_value = submit_btn.get("value")
            print(f"DEBUG: Found submit button value: '{btn_value}'")
            payload["but_submit"] = btn_value
        else:
            print("DEBUG: Could not find submit button, using default.")
            payload["but_submit"] = "Get Access!" # Fallback common value

        # Step 3: Perform Login
        # We assume the form posts to index.php (common for this site)
        print("DEBUG: Sending POST request...")
        post_response = session.post(login_url, data=payload)

        # Step 4: Validate
        # If we are redirected to 'home', or the URL changes, we are good.
        # If we see the 'txt_uname' input again, we failed.
        
        if 'name="txt_uname"' in post_response.text:
            print("DEBUG: Login Failed. Still seeing login input.")
            # OPTIONAL: Print a snippet of the page to see the error message
            # print(post_response.text[:500]) 
            return False
            
        print("DEBUG: Login Successful (Page changed).")
        return True

    except Exception as e:
        print(f"DEBUG: Login Error: {e}")
        return False

def verify_credentials_fast(roll, password):
    session = get_session()
    return login_to_portal(session, roll, password)

def fetch_attendance_fast(roll, password):
    session = get_session()
    
    # 1. Login
    if not login_to_portal(session, roll, password):
        return {"error": "Login Failed. Check Roll No/Password."}

    # 2. Fetch Attendance
    # Note: URL often changes to home?action=stud_att_STD
    attendance_url = "https://samvidha.iare.ac.in/home?action=stud_att_STD"
    
    try:
        print("DEBUG: Fetching attendance page...")
        response = session.get(attendance_url)
        
        # Check if session expired immediately (rare but possible)
        if "Session Expired" in response.text or 'name="txt_uname"' in response.text:
             return {"error": "Session Expired after login."}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. Parse Data (Same logic as before)
        data = []
        target_table = None
        
        for table in soup.find_all('table'):
            txt = table.get_text()
            if "Course Name" in txt or "Attendance %" in txt:
                target_table = table
                break
        
        if not target_table:
            # Debugging: If table not found, what DID we get?
            print("DEBUG: No table found. Page title:", soup.title.string if soup.title else "No Title")
            return {"error": "Attendance Table not found."}

        rows = target_table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 8:
                data.append({
                    "subject": cols[2].get_text(strip=True),
                    "total": int(cols[5].get_text(strip=True)),
                    "present": int(cols[6].get_text(strip=True)),
                    "percent": cols[7].get_text(strip=True)
                })

        if not data:
            return {"error": "Attendance table empty."}

        return {"success": True, "data": data}

    except Exception as e:
        print(f"DEBUG: Parsing Error: {e}")
        return {"error": str(e)}
