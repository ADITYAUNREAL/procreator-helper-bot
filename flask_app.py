from flask import Flask, request, jsonify
import os

from payments.verify import verify_payment
from invoice.generate_invoice import create_invoice
from database.db import save_payment

app = Flask(__name__)

@app.route("/cashfree-webhook", methods=["POST"])
def cashfree_webhook():
    data = request.json

    if not data:
        return jsonify({"error": "No data"}), 400

    try:
        # Cashfree webhook structure (2023-08-01)
        order_id = data["data"]["order"]["order_id"]
        payment_status = data["data"]["payment"]["payment_status"]
        customer_id = data["data"]["customer_details"]["customer_id"]

    except KeyError as e:
        print("Webhook parsing error:", e)
        print("Full payload:", data)
        return jsonify({"error": "Invalid payload"}), 400

    # Only act on successful payment
    if payment_status != "SUCCESS":
        return jsonify({"status": "ignored"}), 200

    # Verify payment with Cashfree API
    if not verify_payment(order_id):
        return jsonify({"error": "Payment verification failed"}), 400

    # Save payment to DB
    save_payment(order_id, "PAID")

    # Generate invoice
    create_invoice(data)

    print(f"✅ Payment verified for order {order_id}")

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    # IMPORTANT for Railway
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
