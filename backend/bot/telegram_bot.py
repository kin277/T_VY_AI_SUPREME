# File: backend/bot/telegram_bot.py
import os
import requests
from backend.core.ai_engine import AIEngine

class TelegramAIBot:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.ai_engine = AIEngine()

    def send_message(self, chat_id: int, text: str):
        """Gửi tin nhắn trả lời về Telegram"""
        url = f"{self.api_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Lỗi gửi tin nhắn Telegram: {e}")

    def process_webhook_update(self, update_data: dict):
        """Xử lý sự kiện khi có tin nhắn từ Telegram gửi đến"""
        if "message" in update_data:
            chat_id = update_data["message"]["chat"]["id"]
            user_text = update_data["message"].get("text", "")

            if user_text:
                # Gọi AI Engine xử lý
                response = self.ai_engine.process_ai_request(user_text)
                ai_reply = response.get("message", "Xin lỗi, tôi không thể xử lý yêu cầu này.")
                self.send_message(chat_id, ai_reply)