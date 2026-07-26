"""
====================================================================
CLAUDE ENGINE - TÍCH HỢP ANTHROPIC CLAUDE API
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 1.0.0
====================================================================
"""

import os
import anthropic
from typing import Dict, Any, Optional

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class ClaudeEngine:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"  # Model mới nhất
        self.max_tokens = 4096
        
    def process(self, query: str, context: str = "") -> Dict[str, Any]:
        """Gọi Claude API để xử lý câu hỏi"""
        if not ANTHROPIC_API_KEY:
            return {"error": "Thiếu ANTHROPIC_API_KEY. Vui lòng thêm vào file .env"}
        
        try:
            # Xây dựng system prompt
            system_prompt = """Bạn là T.VỸ-AI-SUPREME, một trợ lý AI thông minh, 
            trung thực và hữu ích. Bạn luôn trả lời bằng tiếng Việt (trừ khi được yêu cầu khác).
            Bạn có khả năng suy nghĩ sâu, phân tích vấn đề và đưa ra câu trả lời chi tiết, có cấu trúc.
            Bạn không can thiệp vào game, không hack, không tạo công cụ gian lận."""
            
            # Xây dựng messages
            messages = []
            if context:
                messages.append({"role": "user", "content": f"Ngữ cảnh trước đó:\n{context}"})
                messages.append({"role": "assistant", "content": "Tôi đã ghi nhận ngữ cảnh."})
            
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
                "model": self.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
        except Exception as e:
            return {"error": str(e)}