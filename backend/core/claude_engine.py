"""
====================================================================
AI ENGINE SUPREME v13.0 ULTIMATE
- Smart Intent Detection (Code/Math vs Creative)
- Multi-Model 3-Layer Fallback Chain
- Smart Context Trimming (Không bao giờ mất ngữ cảnh)
- Enhanced Code & Markdown Formatting
====================================================================
"""

import os
import re
import requests
import time
from typing import Dict, Any, List

class ClaudeEngine:
    def __init__(self):
        # Danh sách chuỗi Model dự phòng xếp theo độ mạnh cho từng gói
        self.model_tiers = {
            "pro3": ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
            "plus": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama-3.1-8b-instant"],
            "pro":  ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
            "basic": ["llama-3.1-8b-instant"]
        }
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def _detect_intent(self, query: str) -> float:
        """Tự động điều chỉnh độ sáng tạo/chính xác dựa trên nội dung câu hỏi"""
        keywords = ["python", "javascript", "html", "css", "code", "lập trình", "toán", "phương trình", "tính", "lỗi", "fix", "sql", "json", "api", "bug"]
        query_lower = query.lower()
        if any(kw in query_lower for kw in keywords):
            return 0.2  # Thấp để đạt độ chính xác cao nhất cho Code & Toán
        return 0.7      # Bình thường cho giao tiếp tự nhiên

    def process(self, query: str, context: str = "", complexity: str = "pro") -> Dict[str, Any]:
        api_key = (
            os.getenv("GROQ_API_KEY") 
            or os.getenv("ANTHROPIC_API_KEY")
        )

        if not api_key:
            return {"error": "Thiếu GROQ_API_KEY trên Render. Vui lòng kiểm tra lại Environment Variables."}

        api_key = api_key.strip()

        # 1. Chọn chuỗi Model & nhiệt độ theo cấp độ yêu cầu
        models_to_try = self.model_tiers.get(complexity, self.model_tiers["pro"])
        temperature = self._detect_intent(query)

        # 2. Định hình tính cách & phong cách trả lời cho AI
        if complexity == "pro3":
            behavior = (
                "Bạn là T.VỸ-AI-SUPREME phiên bản Chuyên gia Cấp cao (Level 3.0 Pro).\n"
                "- Suy luận logic chặt chẽ, phân tích bản chất vấn đề.\n"
                "- Với CODE: Viết code sạch, tối ưu, dễ đọc, kèm giải thích chi tiết và comment cụ thể.\n"
                "- Với TOÁN/LOGIC: Trình bày từng bước giải thích rõ ràng."
            )
        elif complexity in ["plus", "Phức tạp"]:
            behavior = (
                "Bạn là T.VỸ-AI-SUPREME phiên bản Plus.\n"
                "- Trả lời chi tiết, mạch lạc, chia rõ các mục bằng Bullet Points và Bolding."
            )
        else:
            behavior = (
                "Bạn là T.VỸ-AI-SUPREME.\n"
                "- Trả lời TRỰC TIẾP, chính xác, ngắn gọn, đi thẳng vào trọng tâm vấn đề."
            )

        system_prompt = (
            f"{behavior}\n"
            f"YÊU CẦU ĐỊNH DẠNG: Trả lời bằng tiếng Việt tự nhiên, trình bày chuẩn Markdown đẹp mắt."
        )

        messages = [{"role": "system", "content": system_prompt}]

        # 3. Quản lý ngữ cảnh thông minh (giữ lại 2000 ký tự gần nhất)
        if context:
            clean_context = context.strip()
            if len(clean_context) > 2000:
                clean_context = "..." + clean_context[-2000:]
            messages.append({"role": "user", "content": f"Lịch sử hội thoại trước đó:\n{clean_context}"})
            messages.append({"role": "assistant", "content": "Đã ghi nhớ ngữ cảnh."})

        messages.append({"role": "user", "content": query})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 4. Chạy qua chuỗi Model dự phòng (Fallback Chain)
        last_error = ""
        for model_name in models_to_try:
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4096
            }

            try:
                response = requests.post(self.url, headers=headers, json=payload, timeout=35)
                
                if response.status_code == 200:
                    data = response.json()
                    content_text = data["choices"][0]["message"]["content"]

                    # Lọc sạch thẻ tư duy nội bộ <think> của DeepSeek-R1
                    content_text = re.sub(r'<think>.*?</think>', '', content_text, flags=re.DOTALL).strip()

                    return {
                        "success": True,
                        "response": content_text,
                        "model": model_name
                    }
                elif response.status_code in [429, 500, 503]:
                    # Nấc dự phòng: Nếu model bận/rate limit -> thử model tiếp theo
                    last_error = f"Model {model_name} bận ({response.status_code})"
                    time.sleep(0.5)
                    continue
                else:
                    return {"error": f"Lỗi Groq API ({response.status_code}): {response.text}"}

            except Exception as e:
                last_error = str(e)
                continue

        return {"error": f"Tất cả các Model AI đều đang bận. Lỗi gần nhất: {last_error}"}