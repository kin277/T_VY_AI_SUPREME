"""
====================================================================
SUBSCRIPTION - QUẢN LÝ NÂNG CẤP VÀ GIA HẠN
====================================================================
"""

import datetime
from backend.database.db_handler import get_user_by_id, update_subscription, log_usage
from config.levels import LEVEL_CONFIG

def check_and_upgrade(user_id, tier):
    if tier not in LEVEL_CONFIG:
        return {"error": "Cấp độ không hợp lệ"}

    user = get_user_by_id(user_id)
    if not user:
        return {"error": "Không tìm thấy người dùng"}

    price = LEVEL_CONFIG[tier]['price']
    if price == 0:
        return {"error": "Đây là cấp độ miễn phí"}

    # Mô phỏng thanh toán thành công
    # Trong thực tế, bạn cần tích hợp cổng thanh toán như Stripe, MoMo, v.v.
    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    update_subscription(user_id, tier, expiry)

    # Ghi log nâng cấp
    log_usage(user_id, tier)

    return {
        "success": True,
        "tier": tier,
        "expiry": expiry,
        "message": f"Đã nâng cấp thành công lên {LEVEL_CONFIG[tier]['name']}!"
    }