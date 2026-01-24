from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium_validator import verify_credentials_browser
import os

app = Flask(__name__)
# Enable CORS so your Vercel app can talk to this Render app
CORS(app)

@app.route('/api/verify', methods=['POST'])
def verify_user():
    data = request.json
    roll = data.get('roll')
    password = data.get('password')

    if not roll or not password:
        return jsonify({"valid": False, "error": "Missing data"}), 400

    # Call the Selenium Script
    is_valid = verify_credentials_browser(roll, password)

    if is_valid:
        return jsonify({"valid": True, "message": "Login Successful"})
    else:
        return jsonify({"valid": False, "message": "Invalid Credentials"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)