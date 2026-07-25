"""
====================================================================
ZALO BOT - TỰ ĐỘNG TRẢ LỜI QUA ZALO
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import os
import requests
from flask import request, jsonify

ZALO_OA_TOKEN = os.getenv("ZALO_OA_TOKEN", "")
ZALO_API_URL = "https://openapi.zalo.me/v2.0/oa/message"


def send_zalo_message(user_id, text):
    if not ZALO_OA_TOKEN:
        return {"error": "Thiếu ZALO_OA_TOKEN"}

    headers = {"access_token": ZALO_OA_TOKEN, "Content-Type": "application/json"}
    data = {"user_id": user_id, "message": {"text": text}}

    try:
        response = requests.post(ZALO_API_URL, headers=headers, json=data)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def handle_zalo_webhook():
    data = request.json
    if not data:
        return jsonify({"ok": False}), 400

    # Xử lý tin nhắn từ Zalo
    return jsonify({"ok": True}), 200