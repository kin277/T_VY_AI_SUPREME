"""
====================================================================
TELEGRAM BOT - TỰ ĐỘNG TRẢ LỜI QUA TELEGRAM
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import os
import requests
from flask import request, jsonify

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return {"error": "Thiếu TELEGRAM_BOT_TOKEN"}

    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def handle_telegram_webhook():
    data = request.json
    if not data:
        return jsonify({"ok": False}), 400

    message = data.get('message')
    if not message:
        return jsonify({"ok": True}), 200

    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')

    if chat_id and text:
        from backend.core.ai_engine import AIEngine
        ai = AIEngine(level="pro")
        response = ai.process(text)
        reply = response.get("message", "Xin lỗi, tôi chưa hiểu câu hỏi của bạn.")
        send_telegram_message(chat_id, f"🤖 T.VỸ-AI:\n\n{reply}")

    return jsonify({"ok": True}), 200