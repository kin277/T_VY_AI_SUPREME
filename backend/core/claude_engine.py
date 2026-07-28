"""
====================================================================
CLAUDE ENGINE - TÍCH HỢP ANTHROPIC CLAUDE API (DIRECT REST)
====================================================================
"""

import os
import requests
from typing import Dict, Any

class ClaudeEngine:
    def __init__(self):
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4096
        self.url = "https://api.anthropic.com/v1/messages"
        
    def process(self, query: str, context: str = "", complexity: str = "Trung bình") -> Dict[str, Any]:
        # Đọc trực tiếp API key động từ môi trường mỗi lần gọi
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            return {"error": "Thiếu ANTHROPIC_API_KEY trên Render. Vui lòng kiểm tra lại tab Environment."}
        
        try:
            if complexity == "Trung bình":
                behavior = "Hãy trả lời TRỰC TIẾP, chính xác, ngắn gọn và đi thẳng vào vấn đề."
            elif "Phức tạp" in complexity:
                behavior = "Hãy phân tích kỹ lưỡng, chia nhỏ các ý và giải thích chi tiết."
            else:
                behavior = "Hãy tóm tắt các ý chính và đặt 1-2 câu hỏi gợi mở."

            system_prompt = f"Bạn là T.VỸ-AI-SUPREME, trợ lý AI thông minh bằng tiếng Việt.\nCHỈ THỊ: {behavior}"
            
            messages = []
            if context:
                messages.append({"role": "user", "content": f"Ngữ cảnh trước đó:\n{context}"})
                messages.append({"role": "assistant", "content": "Đã ghi nhận ngữ cảnh."})
            
            messages.append({"role": "user", "content": query})
            
            # Cấu hình Header chuẩn cho Anthropic REST API
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": system_prompt,
                "messages": messages
            }
            
            # Gọi trực tiếp qua thư viện requests (ổn định tuyệt đối trên Render)
            response = requests.post(self.url, headers=headers, json=payload, timeout=45)
            
            if response.status_code != 200:
                return {"error": f"Lỗi từ Anthropic API ({response.status_code}): {response.text}"}
            
            data = response.json()
            content_text = data.get("content", [{}])[0].get("text", "Không nhận được phản hồi từ AI.")
            
            return {
                "success": True,
                "response": content_text,
                "model": self.model
            }
            
        except Exception as e:
            return {"error": f"Lỗi kết nối HTTP trực tiếp: {str(e)}"}