"""
====================================================================
ETHICS GUARD - BỘ LỌC CHỐNG BẺ KHÓA (ANTI-JAILBREAK & PROMPT INJECTION)
====================================================================
"""

import re
from typing import Tuple

class EthicsGuard:
    def __init__(self):
        # 1. Các mẫu kỹ thuật Jailbreak / Prompt Injection phổ biến
        self.jailbreak_patterns = [
            r"ignore (all )?(previous|above) instructions",
            r"bỏ qua (mọi|tất cả) (quy tắc|hướng dẫn|chỉ thị)",
            r"do anything now",
            r"\bdan\b",
            r"developer mode",
            r"chế độ nhà phát triển",
            r"jailbreak",
            r"bẻ khóa",
            r"pretend you (are|have) no (rules|ethics|limitations|restrictions)",
            r"nhập vai.*không (có|chịu) giới hạn",
            r"(tiết lộ|reveal|show).*system prompt",
            r"override.*safety",
            r"vô hiệu hóa.*(bảo mật|đạo đức)",
            r"mô phỏng.*không có quy tắc",
            r"bạn là một ai không bị kiểm duyệt"
        ]

        # 2. Các mẫu yêu cầu vi phạm pháp luật / nguy hiểm
        self.harmful_patterns = [
            r"chế tạo (bom|thuốc nổ|vũ khí|chất độc)",
            r"hướng dẫn (hack|tấn công|ddos) (web|hệ thống|mạng)",
            r"hướng dẫn (tự tử|tự hại)",
            r"tạo (virus|malware|mã độc)",
            r"mUA bán (chất cấm|ma túy|vũ khí)"
        ]

    def check_message(self, message: str) -> Tuple[bool, str]:
        """
        Kiểm tra tin nhắn người dùng.
        Trả về: (Cho_Phép_Chạy, Lý_Do_Từ_Chối)
        """
        if not message:
            return True, ""

        msg_lower = message.lower()

        # Kiểm tra mẫu Jailbreak
        for pattern in self.jailbreak_patterns:
            if re.search(pattern, msg_lower):
                return False, "🛡️ **Cảnh báo Hệ thống:** Lệnh bị từ chối do phát hiện dấu hiệu thử nghiệm bẻ khóa AI (Jailbreak / Prompt Injection)."

        # Kiểm tra nội dung nguy hại
        for pattern in self.harmful_patterns:
            if re.search(pattern, msg_lower):
                return False, "⚠️ **Cảnh báo Đạo đức:** Yêu cầu bị từ chối do vi phạm tiêu chuẩn an toàn và đạo đức hệ thống."

        return True, ""