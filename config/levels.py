"""
====================================================================
CẤU HÌNH 4 CẤP ĐỘ AI - T.VỸ-VIP-FILE
====================================================================
"""

LEVEL_CONFIG = {
    "basic": {
        "id": "basic",
        "name": "AI Thường",
        "color": "#22c55e",
        "price": 0,
        "price_text": "Miễn phí",
        "max_uses_per_day": 999999,
        "features": ["Trả lời nhanh", "Cơ bản", "Không tìm web"],
        "description": "Trả lời cơ bản, không tìm kiếm web.",
        "level": 0
    },
    
    "pro": {
        "id": "pro",
        "name": "AI Pro",
        "color": "#3b82f6",
        "price": 20000,
        "price_text": "20.000đ/tháng",
        "max_uses_per_day": 5,
        "features": ["Trả lời chi tiết", "Tìm kiếm web cơ bản", "Ưu tiên xử lý"],
        "description": "Trả lời chi tiết, có tìm kiếm web.",
        "level": 1
    },
    "plus": {
        "id": "plus",
        "name": "AI Plus",
        "color": "#8b5cf6",
        "price": 50000,
        "price_text": "50.000đ/tháng",
        "max_uses_per_day": 2,
        "features": ["Phân tích sâu", "Suy luận logic", "Đa nguồn dữ liệu", "Ưu tiên cao"],
        "description": "Phân tích sâu, suy luận logic từ đa nguồn.",
        "level": 2
    },
    "pro3": {
        "id": "pro3",
        "name": "AI 3.0 Pro",
        "color": "#ef4444",
        "price": 100000,
        "price_text": "100.000đ/tháng",
        "max_uses_per_day": 0,
        "features": ["Siêu thông minh", "Dự đoán chính xác", "Tối ưu tuyệt đối", "Hỗ trợ 24/7"],
        "description": "Siêu thông minh, dự đoán và tối ưu tuyệt đối.",
        "level": 3
    },
    # ===== THÊM VÀO LEVELS.PY =====
    "expert": {
        "id": "expert",
        "name": "Chế độ Chuyên gia",
        "icon": "🎯",
        "color": "#f59e0b",
        "price": 200000,
        "price_text": "200.000đ/tháng",
        "max_uses_per_day": 0,
        "features": [
            "Phân tích chuyên sâu từng lĩnh vực",
            "Trích dẫn nguồn tham khảo",
            "Xuất báo cáo chi tiết",
            "Tư vấn chuyên môn cao"
        ],
        "description": "Chế độ chuyên gia cho các vấn đề phức tạp.",
        "level": 4
    },
}


def get_level_config(level_id: str):
    return LEVEL_CONFIG.get(level_id, LEVEL_CONFIG["basic"])


def get_level_name(level_id: str) -> str:
    return get_level_config(level_id)["name"]


def get_level_price(level_id: str) -> int:
    return get_level_config(level_id)["price"]