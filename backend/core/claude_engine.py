"""
====================================================================
AI ENGINE SUPREME v15.5 - REALTIME WEB SEARCH, LIVE CLOCK & DYNAMIC VISION ENGINE
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 12.6.0 / 15.5 (Khắc phục phản hồi cố định & Tối ưu Vision/Multimodal)
====================================================================
"""

import os
import re
import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.core.ethics_guard import EthicsGuard
from backend.core.web_search import WebSearchEngine

class ClaudeEngine:
    def __init__(self):
        self.guard = EthicsGuard()
        self.web_searcher = WebSearchEngine()
        
        # Danh sách các Model AI theo từng Cấp độ
        self.model_tiers = {
            "pro3": ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"],
            "plus": ["llama-3.3-70b-versatile", "gemma2-9b-it", "mixtral-8x7b-32768", "llama-3.1-8b-instant"],
            "pro":  ["llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"],
            "basic": ["llama-3.1-8b-instant", "gemma2-9b-it"]
        }

        # Danh sách Model chuyên xử lý Hình ảnh (Vision)
        self.vision_models = [
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview"
        ]

        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def _get_api_keys(self) -> List[str]:
        """Tự động quét và lấy danh sách API Key (Hỗ trợ nhiều Key phân cách bởi dấu phẩy)"""
        keys = []
        for env_var in ["GROQ_API_KEY", "GROQ_API_KEYS", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]:
            raw_keys = os.getenv(env_var, "")
            if raw_keys:
                for k in raw_keys.split(","):
                    k_clean = k.strip()
                    if k_clean and k_clean not in keys:
                        keys.append(k_clean)
        return keys

    def _should_web_search(self, query: str) -> bool:
        """Tự động phát hiện câu hỏi cần cập nhật thông tin Internet"""
        keywords = [
            "thời tiết", "tin tức", "mới nhất", "hôm nay", "giá vàng", 
            "tỷ giá", "mới đây", "sự kiện", "kết quả", "bóng đá", 
            "tìm kiếm", "tra cứu", "search", "giá", "hiện tại"
        ]
        q_lower = query.lower()
        return any(kw in q_lower for kw in keywords)

    def _detect_intent(self, query: str) -> float:
        """Tự động điều chỉnh Temperature theo độ chính xác của câu hỏi"""
        keywords = [
            "python", "javascript", "html", "css", "code", "lập trình", 
            "toán", "phương trình", "tính", "lỗi", "fix", "sql", "json", "api", "bug"
        ]
        if any(kw in query.lower() for kw in keywords):
            return 0.2
        return 0.7

    def process(
        self, 
        query: str, 
        context: str = "", 
        complexity: str = "pro", 
        image_url: Optional[str] = None, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Xử lý yêu cầu AI đa phương thức (Văn bản + Hình ảnh + Tìm kiếm Web + Ngữ cảnh dự án).
        """
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
            return {
                "error": "Chưa cấu hình GROQ_API_KEY trong file .env hoặc biến môi trường! Vui lòng thêm GROQ_API_KEY để AI hoạt động."
            }

        # Lấy hình ảnh từ image_url hoặc image_base64 trong kwargs
        img_target = image_url or kwargs.get('image_base64')

        # 2. Tự động Quét Web nếu hỏi thông tin thời gian thực
        web_info = ""
        if self._should_web_search(query):
            try:
                search_results = self.web_searcher.search(query)
                if search_results:
                    web_info = f"\n\n[DỮ LIỆU THỜI GIAN THỰC TỪ INTERNET]:\n{search_results}"
            except Exception as e:
                web_info = ""

        # 3. Thời gian thực tế hiện tại
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

        # 4. Xác định danh sách Model cần thử (Tự động ưu tiên Vision Model nếu có hình ảnh)
        base_models = self.model_tiers.get(complexity, self.model_tiers["pro"])
        if img_target:
            models_to_try = self.vision_models + [m for m in base_models if m not in self.vision_models]
        else:
            models_to_try = base_models

        temperature = self._detect_intent(query)

        # 5. Thiết lập System Guardrail
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

        # 6. Bảo tồn Ngữ cảnh hội thoại & Bộ quy tắc hệ thống (Tối ưu không cắt xén quy tắc)
        if context:
            clean_context = context.strip()
            if len(clean_context) > 4000:
                # Bảo tồn phần đầu (chứa bộ quy tắc hệ thống) và phần cuối (hội thoại gần nhất)
                clean_context = clean_context[:1500] + "\n\n[... Đã thu gọn lịch sử cũ ...]\n\n" + clean_context[-2500:]
            messages.append({"role": "user", "content": f"Lịch sử / Ngữ cảnh đính kèm:\n{clean_context}"})
            messages.append({"role": "assistant", "content": "Đã ghi nhận ngữ cảnh."})

        # Đính kèm thông tin web vào prompt
        user_content = query + web_info

        # 7. Xử lý định dạng tin nhắn Người dùng (Xử lý đa phương thức / Vision)
        if img_target:
            user_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_content},
                    {"type": "image_url", "image_url": {"url": img_target}}
                ]
            }
        else:
            user_message = {"role": "user", "content": user_content}

        messages.append(user_message)

        # 8. Vòng lặp thử qua các API Keys và Models cho đến khi có phản hồi thật
        last_error = ""
        for key in api_keys:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }

            for model_name in models_to_try:
                # Nếu model không hỗ trợ Vision nhưng input có ảnh -> Tự động biến đổi payload thành văn bản thuần để tránh lỗi 400
                if img_target and model_name not in self.vision_models:
                    formatted_messages = []
                    for m in messages:
                        if m.get("role") == "user" and isinstance(m.get("content"), list):
                            formatted_messages.append({
                                "role": "user",
                                "content": f"[Hình ảnh đính kèm]: {user_content}"
                            })
                        else:
                            formatted_messages.append(m)
                    payload_messages = formatted_messages
                else:
                    payload_messages = messages

                payload = {
                    "model": model_name,
                    "messages": payload_messages,
                    "temperature": temperature,
                    "max_tokens": 4096
                }

                try:
                    response = requests.post(self.url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        content_text = data["choices"][0]["message"]["content"]
                        # Loại bỏ thẻ suy luận rác <think>...</think> nếu có từ các model như DeepSeek
                        content_text = re.sub(r'<think>.*?</think>', '', content_text, flags=re.DOTALL).strip()

                        if content_text:
                            return {
                                "success": True,
                                "response": content_text,
                                "model": model_name
                            }
                    elif response.status_code == 429:
                        last_error = f"Model {model_name} bị Rate Limit (429)"
                        time.sleep(0.5)
                        continue
                    else:
                        last_error = f"Lỗi Groq ({response.status_code}): {response.text}"
                        continue

                except Exception as e:
                    last_error = str(e)
                    continue

        return {"error": f"Không thể kết nối với AI Engine. Chi tiết lỗi: {last_error}"}