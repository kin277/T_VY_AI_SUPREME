"""
====================================================================
ETHICS GUARD - BẢO VỆ ĐẠO ĐỨC AI
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import re
from config.ethics_rules import ETHICS_RULES, check_ethics


class EthicsGuard:
    def __init__(self):
        self.name = "EthicsGuard"
        self.version = "1.0.0"

    def validate(self, query: str) -> dict:
        """Xác thực yêu cầu của người dùng"""
        result = check_ethics(query)
        if result["violation"]:
            return {
                "allowed": False,
                "message": result["message"],
                "reason": f"Phát hiện từ khóa: {result['keyword']}"
            }
        return {"allowed": True, "message": "Yêu cầu hợp lệ."}

    def get_safe_advice(self, query: str) -> str:
        """Đưa ra lời khuyên an toàn thay vì can thiệp trực tiếp"""
        if "tối ưu" in query.lower() or "buff" in query.lower():
            return """
Để cải thiện hiệu năng thiết bị một cách an toàn và hợp pháp, bạn có thể:

1. Đóng các ứng dụng không cần thiết đang chạy nền
2. Tắt hiệu ứng hoạt hình trong cài đặt nhà phát triển
3. Sử dụng chế độ hiệu năng cao (nếu có)
4. Cập nhật hệ điều hành và driver lên phiên bản mới nhất
5. Xóa bộ nhớ cache thường xuyên
6. Hạn chế chạy nhiều ứng dụng cùng lúc

Đây là những cách tối ưu hợp pháp và an toàn cho thiết bị của bạn.
"""
        return None