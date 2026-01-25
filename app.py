import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from selenium_validator import verify_credentials_browser, fetch_attendance_data

app = Flask(__name__)
CORS(app)

@app.route('/api/verify', methods=['POST'])
def verify_user():
    data = request.json
    roll = data.get('roll')
    password = data.get('password')
    if verify_credentials_browser(roll, password):
        return jsonify({"valid": True})
    return jsonify({"valid": False})

@app.route('/api/download', methods=['POST'])
def proxy_download():
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
        s3_url = f"{base_url}/STUDENTS/{roll}/DOCS/{roll}_{doc_type}.jpg"
        filename = f"{roll}_{doc_type}.jpg"
        content_type = "image/jpeg"

    try:
        remote = requests.get(s3_url, stream=True)
        if remote.status_code != 200:
            return jsonify({"error": "File not found on server"}), 404
            
        headers = { "Content-Disposition": f"attachment; filename={filename}", "Content-Type": content_type }
        return Response(remote.iter_content(chunk_size=1024), headers=headers, status=200)
    except:
        return jsonify({"error": "Server Error"}), 500

@app.route('/api/attendance', methods=['POST'])
def get_attendance():
    data = request.json
    result = fetch_attendance_data(data.get('roll'), data.get('password'))
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
