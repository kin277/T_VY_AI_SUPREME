"""
====================================================================
CLAUDE ENGINE - TÍCH HỢP ANTHROPIC CLAUDE API
====================================================================
"""

import os
import anthropic
from typing import Dict, Any

class ClaudeEngine:
    def __init__(self):
        # Lấy trực tiếp API key
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            
        # Sử dụng chuẩn model ổn định
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4096
        
    def process(self, query: str, context: str = "", complexity: str = "Trung bình") -> Dict[str, Any]:
        # Tự động reload key nếu chưa có
        if not self.client:
            self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if self.api_key:
                self.client = anthropic.Anthropic(api_key=self.api_key)

        if not self.client or not self.api_key:
            return {"error": "Lỗi: Chưa cấu hình ANTHROPIC_API_KEY trong Environment của Render."}
        
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
            
            # Gọi API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )
            
            return {
                "success": True,
                "response": response.content[0].text,
                "model": self.model
            }
        except Exception as e:
            # Trả về nguyên văn lỗi từ Anthropic để dễ nhận biết
            error_msg = str(e)
            print(f"ANHROPI_EXCEPTION: {error_msg}")
            return {"error": f"Lỗi Claude API chi tiết: {error_msg}"}