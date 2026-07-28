"""
====================================================================
AI ENGINE - TÍCH HỢP GROQ API (TỰ ĐỘNG CHUYỂN MODEL KHI BỊ RATE LIMIT)
====================================================================
"""

import os
import requests
import time
from typing import Dict, Any

class ClaudeEngine:
    def __init__(self):
        # Model chính (70B) và Model dự phòng tốc độ cao (8B)
        self.primary_model = "llama-3.3-70b-versatile"
        self.fallback_model = "llama-3.1-8b-instant"
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def process(self, query: str, context: str = "", complexity: str = "Trung bình") -> Dict[str, Any]:
        api_key = (
            os.getenv("GROQ_API_KEY") 
            or os.getenv("ANTHROPIC_API_KEY")
        )

        if not api_key:
            return {"error": "Thiếu GROQ_API_KEY. Vui lòng kiểm tra lại cấu hình trên Render."}

        api_key = api_key.strip()

        try:
            if complexity in ["basic", "pro", "Trung bình"]:
                behavior = "Trả lời TRỰC TIẾP, chính xác, ngắn gọn và đi thẳng vào vấn đề."
            elif complexity in ["plus", "Phức tạp"]:
                behavior = "Phân tích kỹ lưỡng, chia nhỏ các ý và giải thích chi tiết."
            elif complexity == "pro3":
                behavior = "Phân tích ở cấp độ chuyên gia cao cấp, lập luận chặt chẽ và sâu sắc."
            else:
                behavior = "Trả lời tự nhiên, thân thiện và chính xác."

            system_prompt = (
                f"Bạn là T.VỸ-AI-SUPREME, trợ lý AI thông minh bằng tiếng Việt.\n"
                f"CHỈ THỊ PHONG CÁCH: {behavior}"
            )

            messages = [{"role": "system", "content": system_prompt}]

            if context:
                # Cắt ngắn context tối đa 1200 ký tự để tiết kiệm token
                messages.append({"role": "user", "content": f"Ngữ cảnh trước đó:\n{context[:1200]}"})
                messages.append({"role": "assistant", "content": "Đã ghi nhận ngữ cảnh."})

            messages.append({"role": "user", "content": query})

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # Lần 1: Gọi Model chính (Llama 3.3 70B)
            payload = {
                "model": self.primary_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }

            response = requests.post(self.url, headers=headers, json=payload, timeout=30)

            # Lần 2: Nếu bị quá tải Rate Limit (429), tự động dùng Model dự phòng 8B Instant
            if response.status_code == 429:
                payload["model"] = self.fallback_model
                time.sleep(1)  # Chờ 1s
                response = requests.post(self.url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                return {"error": f"Lỗi Groq API ({response.status_code}): {response.text}"}

            data = response.json()
            content_text = data["choices"][0]["message"]["content"]

            return {
                "success": True,
                "response": content_text,
                "model": payload["model"]
            }

        except Exception as e:
            return {"error": f"Lỗi kết nối AI Engine: {str(e)}"}