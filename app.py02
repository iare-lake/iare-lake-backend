import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
# Import the new fast functions
from scraper import verify_credentials_fast, fetch_attendance_fast

app = Flask(__name__)
# Enable CORS so your frontend can talk to this backend
CORS(app)

@app.route('/', methods=['GET'])
def health_check():
    return "IARE Lake Backend is Running (Fast Mode)", 200

@app.route('/api/verify', methods=['POST'])
def verify_user():
    data = request.json
    roll = data.get('roll')
    password = data.get('password')
    
    if not roll or not password:
        return jsonify({"valid": False, "error": "Missing details"}), 400

    is_valid = verify_credentials_fast(roll, password)
    return jsonify({"valid": is_valid})

@app.route('/api/attendance', methods=['POST'])
def get_attendance():
    data = request.json
    roll = data.get('roll')
    password = data.get('password')
    
    # Call the fast scraper
    result = fetch_attendance_fast(roll, password)
    
    if "error" in result:
        return jsonify(result), 500 # Return error status
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def proxy_download():
    # This just proxies S3 files, it's already fast enough using Requests
    data = request.json
    roll = data.get('roll')
    doc_type = data.get('type')
    
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
        # Generic docs
        s3_url = f"{base_url}/STUDENTS/{roll}/DOCS/{roll}_{doc_type}.jpg"
        filename = f"{roll}_{doc_type}.jpg"
        content_type = "image/jpeg"

    try:
        remote = requests.get(s3_url, stream=True, timeout=10)
        if remote.status_code != 200:
            return jsonify({"error": "File not found on server"}), 404
            
        headers = { 
            "Content-Disposition": f"attachment; filename={filename}", 
            "Content-Type": content_type 
        }
        return Response(remote.iter_content(chunk_size=1024), headers=headers, status=200)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
