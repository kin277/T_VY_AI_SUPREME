"""
====================================================================
MOMO PAYMENT - TÍCH HỢP THANH TOÁN QUA MOMO
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import os
import hmac
import hashlib
import requests
import json
import datetime
import uuid
from flask import request, jsonify, session
from backend.database.db_handler import get_user_by_id, update_subscription

# ===== CẤU HÌNH =====
MOMO_PARTNER_CODE = os.getenv("MOMO_PARTNER_CODE", "")
MOMO_ACCESS_KEY = os.getenv("MOMO_ACCESS_KEY", "")
MOMO_SECRET_KEY = os.getenv("MOMO_SECRET_KEY", "")
MOMO_API_URL = "https://test-payment.momo.vn/v2/gateway/api/create"


def create_payment(order_id, amount, order_info, user_id):
    """Tạo yêu cầu thanh toán MoMo"""
    if not MOMO_PARTNER_CODE or not MOMO_ACCESS_KEY or not MOMO_SECRET_KEY:
        return {"error": "Chưa cấu hình MoMo"}

    request_id = str(uuid.uuid4())
    redirect_url = "http://localhost:5000/payment/complete"
    ipn_url = "http://localhost:5000/payment/ipn"

    raw_signature = (f"accessKey={MOMO_ACCESS_KEY}"
                     f"&amount={amount}"
                     f"&extraData="
                     f"&ipnUrl={ipn_url}"
                     f"&orderId={order_id}"
                     f"&orderInfo={order_info}"
                     f"&partnerCode={MOMO_PARTNER_CODE}"
                     f"&redirectUrl={redirect_url}"
                     f"&requestId={request_id}"
                     f"&requestType=payWithMethod")

    # Tạo chữ ký HMAC SHA256
    signature = hmac.new(
        bytes(MOMO_SECRET_KEY, 'ascii'),
        bytes(raw_signature, 'ascii'),
        hashlib.sha256
    ).hexdigest()

    payload = {
        "partnerCode": MOMO_PARTNER_CODE,
        "partnerName": "T.VỸ-AI",
        "storeId": "AI_SUPREME",
        "requestId": request_id,
        "amount": str(amount),
        "orderId": order_id,
        "orderInfo": order_info,
        "redirectUrl": redirect_url,
        "ipnUrl": ipn_url,
        "lang": "vi",
        "extraData": "",
        "requestType": "payWithMethod",
        "signature": signature
    }

    try:
        response = requests.post(MOMO_API_URL, json=payload, timeout=10)
        data = response.json()
        return {
            "success": True,
            "payUrl": data.get("payUrl"),
            "orderId": order_id,
            "amount": amount
        }
    except Exception as e:
        return {"error": str(e)}


def handle_ipn():
    """Xử lý IPN từ MoMo sau khi thanh toán"""
    data = request.json
    order_id = data.get('orderId')
    result_code = data.get('resultCode')

    if result_code == 0:
        # Thanh toán thành công
        user_id = session.get('user_id')
        if user_id:
            # Nâng cấp gói Pro (mặc định)
            expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            update_subscription(user_id, 'pro', expiry)
            return jsonify({"message": "OK"}), 200

    return jsonify({"message": "Error"}), 400


def payment_complete():
    """Trang thông báo kết quả thanh toán"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kết quả thanh toán</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .success { color: green; font-size: 24px; }
            .error { color: red; font-size: 24px; }
            .btn { padding: 12px 24px; background: #2d3b8a; color: #fff; text-decoration: none; border-radius: 8px; display: inline-block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>🔐 Kết quả thanh toán</h1>
        <p id="status">Đang xử lý...</p>
        <a href="/" class="btn">Về trang chủ</a>
        <script>
            const params = new URLSearchParams(window.location.search);
            const result = params.get('resultCode');
            const status = document.getElementById('status');
            if (result === '0') {
                status.innerHTML = '<span class="success">✅ Thanh toán thành công! Gói Pro đã được kích hoạt.</span>';
            } else {
                status.innerHTML = '<span class="error">❌ Thanh toán thất bại. Vui lòng thử lại.</span>';
            }
        </script>
    </body>
    </html>
    """