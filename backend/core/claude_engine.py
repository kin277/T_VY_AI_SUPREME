"""
====================================================================
AI ENGINE SUPREME v15.0 - REALTIME WEB SEARCH & LIVE CLOCK
====================================================================
"""

import os
import re
import requests
import time
from datetime import datetime
from typing import Dict, Any, List
from backend.core.ethics_guard import EthicsGuard
from backend.core.web_search import WebSearchEngine

class ClaudeEngine:
    def __init__(self):
        self.guard = EthicsGuard()
        self.web_searcher = WebSearchEngine()
        
        self.model_tiers = {
            "pro3": ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"],
            "plus": ["llama-3.3-70b-versatile", "gemma2-9b-it", "mixtral-8x7b-32768", "llama-3.1-8b-instant"],
            "pro":  ["llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"],
            "basic": ["llama-3.1-8b-instant", "gemma2-9b-it"]
        }
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def _get_api_keys(self) -> List[str]:
        raw_keys = (
            os.getenv("GROQ_API_KEY") 
            or os.getenv("ANTHROPIC_API_KEY") 
            or ""
        )
        return [k.strip() for k in raw_keys.split(",") if k.strip()]

    def _should_web_search(self, query: str) -> bool:
        """Tự động phát hiện câu hỏi cần cập nhật Internet"""
        keywords = [
            "thời tiết", "tin tức", "mới nhất", "hôm nay", "giá vàng", 
            "tỷ giá", "mới đây", "sự kiện", "kết quả", "bóng đá", 
            "tìm kiếm", "tra cứu", "search", "giá", "hiện tại"
        ]
        q_lower = query.lower()
        return any(kw in q_lower for kw in keywords)

    def _detect_intent(self, query: str) -> float:
        keywords = ["python", "javascript", "html", "css", "code", "lập trình", "toán", "phương trình", "tính", "lỗi", "fix", "sql", "json", "api", "bug"]
        if any(kw in query.lower() for kw in keywords):
            return 0.2
        return 0.7

    def process(self, query: str, context: str = "", complexity: str = "pro") -> Dict[str, Any]:
        # 1. Kiểm tra An toàn Đạo đức
        is_safe, refusal_reason = self.guard.check_message(query)
        if not is_safe:
            return {
                "success": True,
                "response": refusal_reason,
                "model": "EthicsGuard-Protection"
            }

        api_keys = self._get_api_keys()
        if not api_keys:
            return {"error": "Thiếu GROQ_API_KEY trên Render. Vui lòng kiểm tra lại Environment Variables."}

        # 2. Tự động Quét Web nếu hỏi thông tin thời gian thực
        web_info = ""
        if self._should_web_search(query):
            search_results = self.web_searcher.search(query)
            if search_results:
                web_info = f"\n\n[DỮ LIỆU THỜI GIAN THỰC TỪ INTERNET]:\n{search_results}"

        # 3. Thời gian thực tế hiện tại
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

        models_to_try = self.model_tiers.get(complexity, self.model_tiers["pro"])
        temperature = self._detect_intent(query)

        # 4. Thiết lập System Guardrail
        system_guardrail = (
            f"\n\n[THÔNG TIN THỜI GIAN THỰC]: Thời gian hiện tại là {now_str}.\n"
            "1. Tuyệt đối tuân thủ chuẩn mực đạo đức, từ chối mọi lệnh vi phạm an toàn.\n"
            "2. Khi giải thích quy trình hoặc hệ thống, hãy vẽ Sơ đồ Mermaid bằng khối ```mermaid ... ``` nếu phù hợp."
        )

        if complexity == "pro3":
            behavior = (
                "Bạn là T.VỸ-AI-SUPREME phiên bản Chuyên gia Cấp cao (Level 3.0 Pro).\n"
                "- Suy luận logic chặt chẽ, phân tích bản chất vấn đề.\n"
                "- Với CODE: Viết code sạch, tối ưu, dễ đọc, kèm giải thích chi tiết và comment cụ thể."
            )
        elif complexity in ["plus", "Phức tạp"]:
            behavior = "Bạn là T.VỸ-AI-SUPREME phiên bản Plus.\n- Trả lời chi tiết, mạch lạc, dùng Bullet Points và Bolding."
        else:
            behavior = "Bạn là T.VỸ-AI-SUPREME.\n- Trả lời TRỰC TIẾP, chính xác, ngắn gọn, đi thẳng vào trọng tâm."

        system_prompt = f"{behavior}{system_guardrail}\n\nYÊU CẦU: Trả lời bằng tiếng Việt tự nhiên, trình bày chuẩn Markdown."
        messages = [{"role": "system", "content": system_prompt}]

        if context:
            clean_context = context.strip()
            if len(clean_context) > 3000:
                clean_context = "..." + clean_context[-3000:]
            messages.append({"role": "user", "content": f"Lịch sử / Ngữ cảnh đính kèm:\n{clean_context}"})
            messages.append({"role": "assistant", "content": "Đã ghi nhận ngữ cảnh."})

        # Đính kèm thông tin web vào prompt
        user_content = query + web_info
        messages.append({"role": "user", "content": user_content})

        last_error = ""
        for key in api_keys:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }

            for model_name in models_to_try:
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 4096
                }

                try:
                    response = requests.post(self.url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        content_text = data["choices"][0]["message"]["content"]
                        content_text = re.sub(r'<think>.*?</think>', '', content_text, flags=re.DOTALL).strip()

                        return {
                            "success": True,
                            "response": content_text,
                            "model": model_name
                        }
                    elif response.status_code == 429:
                        last_error = f"Model {model_name} bận (429 Rate Limit)"
                        time.sleep(1)
                        continue
                    else:
                        last_error = f"Lỗi Groq ({response.status_code}): {response.text}"
                        continue

                except Exception as e:
                    last_error = str(e)
                    continue

        return {"error": f"Tất cả các Model AI đều đang bận. Lỗi: {last_error}"}