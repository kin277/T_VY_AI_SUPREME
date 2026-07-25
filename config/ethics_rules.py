"""
====================================================================
BỘ QUY TẮC ĐẠO ĐỨC AI - T.VỸ-VIP-FILE
====================================================================
AI không được phép làm những việc sau:
- Can thiệp vào phần mềm, game, hệ thống của bên thứ ba
- Hacking, crack, keygen, cheat
- Xâm phạm quyền riêng tư
- Tạo nội dung độc hại, sai trái
- Tư vấn hành vi vi phạm pháp luật
====================================================================
"""

ETHICS_RULES = {
    "forbidden_keywords": [
        "cheat", "hack", "crack", "keygen", "virus", "malware",
        "đánh cắp", "xâm nhập", "phá hoại", "gian lận",
        "crack game", "mod game", "can thiệp game",
        "tăng fps bất hợp pháp", "buff game trái phép",
        "vượt tường lửa", "xâm nhập hệ thống",
        "lấy cắp dữ liệu", "đánh cắp tài khoản"
    ],

    "forbidden_actions": [
        "can_thiep_game",
        "can_thiep_phần_mềm",
        "tạo_file_buff_game",
        "hack_tài_khoản",
        "xâm_phạm_quyền_riêng_tư"
    ],

    "allowed_actions": [
        "tư_vấn_tối_ưu_hệ_thống",
        "hướng_dẫn_cài_đặt",
        "giải_thích_nguyên_lý",
        "hỗ_trợ_học_tập",
        "tạo_nội_dung_sáng_tạo"
    ],

    "response_template": {
        "ethics_violation": "Tôi không thể hỗ trợ yêu cầu này vì nó vi phạm nguyên tắc đạo đức của tôi. Tuy nhiên, tôi có thể hướng dẫn bạn cách cải thiện hiệu suất thiết bị một cách hợp pháp và an toàn.",
        "safe_alternative": "Thay vì can thiệp trực tiếp, tôi khuyên bạn nên điều chỉnh cài đặt hệ thống, tắt ứng dụng không cần thiết, hoặc cập nhật driver để cải thiện hiệu năng."
    }
}


def check_ethics(query: str) -> dict:
    """Kiểm tra xem câu hỏi có vi phạm đạo đức không"""
    q = query.lower()
    for keyword in ETHICS_RULES["forbidden_keywords"]:
        if keyword in q:
            return {
                "violation": True,
                "keyword": keyword,
                "message": ETHICS_RULES["response_template"]["ethics_violation"]
            }
    return {"violation": False, "message": None}