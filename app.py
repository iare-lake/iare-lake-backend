import os
import requests  # <--- NEW: Import this library
from flask import Flask, request, jsonify, Response # <--- NEW: Import Response
from flask_cors import CORS
from selenium_validator import verify_credentials_browser

app = Flask(__name__)
CORS(app)

# --- ROUTE 1: Login Verification (Existing) ---
@app.route('/api/verify', methods=['POST'])
def verify_user():
    data = request.json
    roll = data.get('roll')
    password = data.get('password')

    if not roll or not password:
        return jsonify({"valid": False, "error": "Missing data"}), 400

    print(f"Verifying user: {roll}")
    
    # Call the selenium script
    is_valid = verify_credentials_browser(roll, password)

    if is_valid:
        return jsonify({"valid": True, "message": "Login Successful"})
    else:
        return jsonify({"valid": False, "message": "Invalid Credentials"})

# --- ROUTE 2: Document Downloader (NEW) ---
@app.route('/api/download', methods=['POST'])
def proxy_download():
    # 1. Get data from your website
    data = request.json
    roll = data.get('roll')
    doc_type = data.get('type')

    if not roll or not doc_type:
        return jsonify({"error": "Missing data"}), 400

    # 2. Construct the AWS S3 URL secretly
    # (The user never sees this URL, only your server does)
    base_url = "https://iare-data.s3.ap-south-1.amazonaws.com/uploads"
    
    if doc_type == "PHOTO":
        s3_url = f"{base_url}/STUDENTS/{roll}/{roll}.jpg"
        filename = f"{roll}.jpg"
        content_type = "image/jpeg"
    elif doc_type == "FIELDPROJECT":
        s3_url = f"{base_url}/FIELDPROJECT/2024-25_{roll}_FM.pdf"
        filename = f"{roll}_FieldProject.pdf"
        content_type = "application/pdf"
    else:
        # For standard certificates (TC, Caste, etc.)
        s3_url = f"{base_url}/STUDENTS/{roll}/DOCS/{roll}_{doc_type}.jpg"
        filename = f"{roll}_{doc_type}.jpg"
        content_type = "image/jpeg"

    print(f"Server fetching file from: {s3_url}")

    # 3. Fetch the file from AWS S3
    try:
        # stream=True means we download it chunk-by-chunk (efficient)
        remote_file = requests.get(s3_url, stream=True)
        
        # Check if the file actually exists on AWS
        if remote_file.status_code != 200:
            return jsonify({"error": "File not found on server"}), 404

        # 4. Stream the file back to the User
        # We define headers to tell the browser "This is a file, download it!"
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": content_type
        }
        
        # This sends the data directly from AWS -> Your Server -> User
        return Response(
            remote_file.iter_content(chunk_size=1024),
            headers=headers,
            status=200
        )

    except Exception as e:
        print(f"Download Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/api/attendance', methods=['POST'])
def get_attendance():
    data = request.json
    roll = data.get('roll')
    password = data.get('password')

    if not roll or not password:
        return jsonify({"error": "Missing credentials"}), 400

    print(f"Fetching attendance for: {roll}")
    
    # Call Selenium Scraper
    result = fetch_attendance_data(roll, password)

    if "error" in result:
        # If credentials were wrong or table not found
        status = 401 if "Invalid" in result['error'] else 500
        return jsonify(result), status
    
    return jsonify(result)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

