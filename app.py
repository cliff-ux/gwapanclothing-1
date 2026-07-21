import base64
from datetime import datetime
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows your frontend to communicate with the backend safely

# ==========================================================================
# Safaricom Daraja API Credentials Configuration
# ==========================================================================
MPESA_CONSUMER_KEY = "YOUR_CONSUMER_KEY"
MPESA_CONSUMER_SECRET = "YOUR_CONSUMER_SECRET"
MPESA_SHORTCODE = "YOUR_STORE_SHORT_CODE"  # Often the Store Number for Till accounts
MPESA_TILL_NUMBER = "YOUR_ONLINE_TILL_NUMBER"  # PartyB
MPESA_PASSKEY = "YOUR_LIPA_NA_MPESA_PASSKEY"
CALLBACK_URL = "https://yourdomain.com/api/mpesa/callback"


def generate_access_token():
    """Fetches a secure OAuth token from Safaricom."""
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    # Use https://api.safaricom.co.ke for Production
    
    credentials = f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {"Authorization": f"Basic {encoded_credentials}"}
    response = requests.get(url, headers=headers)
    return response.json().get("access_token")


@app.route("/api/stkpush", methods=["POST"])
def mpesa_stk_push():
    data = request.get_json()
    phone_number = data.get("phone")  # Format must be 2547XXXXXXXX or 2541XXXXXXXX
    amount = str(int(data.get("amount")))  # Ensure integer string parsing

    access_token = generate_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Generate Lipa Na Mpesa Password parameter
    password_string = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    mpesa_password = base64.b64encode(password_string.encode()).decode()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    # Use https://api.safaricom.co.ke for Production

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # CRITICAL TILL CONFIGURATION CHANGES
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": mpesa_password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerBuyGoodsOnline",  # Explicitly tells Safaricom this is a Till route
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": MPESA_TILL_NUMBER,  # The actual Till Number customers see
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "GWAPAFFECTION",
        "TransactionDesc": "Premium Architectural Denim Order",
    }

    response = requests.post(url, json=payload, headers=headers)
    return jsonify(response.json()), response.status_code


@app.route("/api/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """Safaricom hits this endpoint to confirm if payment was successful or canceled."""
    callback_data = request.get_json()
    result_code = callback_data["Body"]["stkCallback"]["ResultCode"]

    if result_code == 0:
        # Payment Successful
        merchant_request_id = callback_data["Body"]["stkCallback"][
            "MerchantRequestID"
        ]
        # Logic to mark order as PAID in your system goes here
        print(f"Order Success! ID: {merchant_request_id}")
    else:
        # Payment Canceled or Failed
        print(f"Transaction Failed/Canceled with Code: {result_code}")

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted Successfully"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)