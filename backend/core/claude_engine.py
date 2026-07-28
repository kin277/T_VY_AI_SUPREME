"""
====================================================================
CLAUDE ENGINE - TÍCH HỢP ANTHROPIC CLAUDE API
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 1.0.1
====================================================================
"""

import os
import anthropic
from typing import Dict, Any, Optional

class ClaudeEngine:
    def __init__(self):
        # Đọc API key động bên trong __init__ để nhận diện chính xác từ Render Environment
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            
        self.model = "claude-3-5-sonnet-20241022" 
        self.max_tokens = 4096
        
    def process(self, query: str, context: str = "", complexity: str = "Trung bình") -> Dict[str, Any]:
        """Gọi Claude API để xử lý câu hỏi dựa theo độ phức tạp"""
        # Thử đọc lại nếu lúc khởi tạo chưa có
        if not self.client:
            self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
            if self.api_key:
                self.client = anthropic.Anthropic(api_key=self.api_key)

        if not self.client or not self.api_key:
            return {"error": "Thiếu ANTHROPIC_API_KEY trên Render. Vui lòng kiểm tra lại tab Environment."}
        
        try:
            # QUY ĐỊNH CÁCH XỬ LÝ THEO ĐỘ PHỨC TẠP
            if complexity == "Trung bình":
                behavior = (
                    "Câu hỏi có độ phức tạp trung bình/đơn giản. "
                    "Hãy trả lời TRỰC TIẾP, chính xác, ngắn gọn và đi thẳng vào vấn đề."
                )
            elif "Phức tạp" in complexity:
                behavior = (
                    "Câu hỏi khó và mang tính phân tích sâu. "
                    "Hãy suy nghĩ từng bước (Chain of Thought), phân tích kỹ lưỡng, chia nhỏ các ý và đưa ra lời giải thích chi tiết."
                )
            else: # Chung chung
                behavior = (
                    "Câu hỏi khá chung chung hoặc tổng quát. "
                    "Hãy trả lời tóm tắt những ý chính nhất, sau đó BẮT BUỘC phải đặt lại 1-2 câu hỏi gợi mở để người dùng làm rõ ngữ cảnh."
                )

            # Xây dựng System Prompt động
            system_prompt = f"""Bạn là T.VỸ-AI-SUPREME, một trợ lý AI thông minh, trung thực và hữu ích.
Bạn luôn trả lời bằng tiếng Việt.
Bạn không can thiệp vào game, không hack, không tạo công cụ gian lận.

CHỈ THỊ QUAN TRỌNG: {behavior}"""
            
            # Xây dựng tin nhắn
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
                "complexity": complexity,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
        except Exception as e:
            return {"error": f"Lỗi Claude API: {str(e)}"}