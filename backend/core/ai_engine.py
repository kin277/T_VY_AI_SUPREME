"""
====================================================================
AI ENGINE CORE - XỬ LÝ SUY LUẬN THÔNG MINH
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
Ràng buộc đạo đức: Không can thiệp game, không hack, chỉ tư vấn.
====================================================================
"""

import re
import json
import random
import datetime
from typing import Dict, Any, Optional

from .ethics_guard import EthicsGuard
from config.levels import LEVEL_CONFIG


class AIEngine:
    def __init__(self, level: str = "pro"):
        self.level = level
        self.context = {}
        self.memory = []
        self.max_memory = 100
        self.ethics = EthicsGuard()

    def process(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """Xử lý câu hỏi với kiểm tra đạo đức"""
        query = query.strip()
        if not query:
            return {"error": "Câu hỏi trống"}

        # Kiểm tra đạo đức
        ethics_check = self.ethics.validate(query)
        if not ethics_check["allowed"]:
            return {
                "type": "ethics_violation",
                "message": ethics_check["message"],
                "details": ethics_check["reason"]
            }

        # Nếu yêu cầu tối ưu game → chuyển sang hướng dẫn an toàn
        if "tối ưu" in query.lower() or "buff" in query.lower():
            safe_advice = self.ethics.get_safe_advice(query)
            if safe_advice:
                return {
                    "type": "advice",
                    "message": safe_advice,
                    "note": "Đây là hướng dẫn an toàn và hợp pháp."
                }

        # Phân loại ý định
        intent = self.classify_intent(query)

        # Xử lý theo intent
        if intent == "code":
            return self.handle_code(query)
        elif intent == "image":
            return self.handle_image(query)
        elif intent == "music":
            return self.handle_music(query)
        elif intent == "web_search":
            return self.handle_web_search(query)
        elif intent == "advice":
            return self.handle_advice(query)
        else:
            return self.handle_general(query)

    def classify_intent(self, query: str) -> str:
        """Phân loại ý định an toàn"""
        q = query.lower()
        if any(k in q for k in ["code", "lập trình", "viết code"]):
            return "code"
        if any(k in q for k in ["ảnh", "hình ảnh", "draw", "paint", "vẽ"]):
            return "image"
        if any(k in q for k in ["nhạc", "music", "bài hát"]):
            return "music"
        if any(k in q for k in ["tìm", "search", "google", "tra cứu"]):
            return "web_search"
        if any(k in q for k in ["tư vấn", "hướng dẫn", "cách", "làm thế nào", "advice"]):
            return "advice"
        return "general"

    def generate_response(self, query: str) -> str:
        """Tạo phản hồi dài, đầy đủ, ít icon"""
        return f"""
Câu hỏi của bạn: "{query}"

Tôi đã tiếp nhận và phân tích câu hỏi của bạn. Dựa trên kiến thức và khả năng của tôi, tôi sẽ cố gắng đưa ra câu trả lời chi tiết và hữu ích nhất.

Để tôi có thể hỗ trợ bạn tốt hơn, bạn có thể cung cấp thêm thông tin hoặc đặt câu hỏi cụ thể hơn. Tôi luôn sẵn sàng giúp đỡ bạn trong phạm vi cho phép và tuân thủ các nguyên tắc đạo đức.

Nếu bạn cần tư vấn về kỹ thuật, tối ưu hệ thống, lập trình, sáng tạo nội dung, hay tìm kiếm thông tin, tôi đều có thể hỗ trợ.

Bạn có muốn tôi giúp đỡ cụ thể về lĩnh vực nào không?
"""

    def handle_general(self, query: str) -> Dict[str, Any]:
        return {
            "type": "chat",
            "message": self.generate_response(query),
            "intent": "general"
        }

    def handle_code(self, query: str) -> Dict[str, Any]:
        return {
            "type": "code",
            "message": """
Tôi sẽ giúp bạn tạo code. Vui lòng cho tôi biết:
- Ngôn ngữ lập trình bạn muốn sử dụng (Python, JavaScript, Java, C++, ...)
- Chức năng cụ thể bạn cần code thực hiện
- Môi trường chạy (web, mobile, desktop, ...)

Tôi sẽ tạo code sạch, có chú thích và tối ưu.
"""
        }

    def handle_image(self, query: str) -> Dict[str, Any]:
        return {
            "type": "image",
            "message": """
Tôi có thể tạo hình ảnh dựa trên mô tả của bạn. Hãy mô tả chi tiết:
- Chủ đề chính của bức ảnh
- Màu sắc và phong cách mong muốn
- Các chi tiết đặc biệt bạn muốn có

Tôi sẽ sử dụng AI để tạo ra hình ảnh theo yêu cầu của bạn.
"""
        }

    def handle_music(self, query: str) -> Dict[str, Any]:
        return {
            "type": "music",
            "message": """
Tôi có thể hỗ trợ bạn về âm nhạc:
- Tạo lời bài hát theo chủ đề
- Phân tích cấu trúc bài hát
- Đề xuất thể loại và phong cách phù hợp
- Hướng dẫn sử dụng phần mềm làm nhạc

Hãy cho tôi biết bạn cần hỗ trợ gì về âm nhạc.
"""
        }

    def handle_web_search(self, query: str) -> Dict[str, Any]:
        return {
            "type": "web_search",
            "message": f"""
Tôi đang tìm kiếm thông tin về: "{query}"

Tôi sẽ tổng hợp từ các nguồn uy tín và đáng tin cậy. Quá trình này có thể mất vài giây.

Trong lúc chờ đợi, bạn có thể cung cấp thêm ngữ cảnh hoặc từ khóa cụ thể để tôi tìm kiếm chính xác hơn.
"""
        }

    def handle_advice(self, query: str) -> Dict[str, Any]:
        return {
            "type": "advice",
            "message": """
Tôi có thể tư vấn cho bạn về nhiều lĩnh vực:
- Lập trình và phát triển phần mềm
- Học tập và nghiên cứu
- Tối ưu hệ thống và thiết bị (hợp pháp)
- Sáng tạo nội dung (viết, vẽ, âm nhạc)
- Kỹ năng mềm và làm việc

Hãy cho tôi biết bạn cần tư vấn về vấn đề gì, tôi sẽ giúp bạn một cách tốt nhất.
"""
        }