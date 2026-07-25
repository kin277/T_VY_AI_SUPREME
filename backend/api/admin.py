"""
====================================================================
ADMIN PANEL - QUẢN LÝ NGƯỜI DÙNG & THỐNG KÊ
====================================================================
"""

from flask import request, jsonify, session
from backend.database.db_handler import get_user_by_id, get_db, get_conversations

def is_admin(user_id):
    user = get_user_by_id(user_id)
    return user and user['role'] == 'admin'

def admin_required(f):
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id or not is_admin(user_id):
            return jsonify({"error": "Yêu cầu quyền Admin"}), 403
        return f(*args, **kwargs)
    return wrapper

def get_all_users():
    """Lấy danh sách tất cả người dùng (chỉ Admin)"""
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    with get_db() as conn:
        users = conn.execute("""
            SELECT id, username, email, role, subscription_tier, subscription_expiry, created_at
            FROM users ORDER BY created_at DESC
        """).fetchall()
        return jsonify([dict(u) for u in users])

def get_all_conversations():
    """Lấy tất cả đoạn chat (chỉ Admin)"""
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    with get_db() as conn:
        convs = conn.execute("""
            SELECT c.id, c.name, c.count, c.level, c.created_at, u.username, u.email
            FROM conversations c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
            LIMIT 100
        """).fetchall()
        return jsonify([dict(c) for c in convs])

def get_stats():
    """Thống kê hệ thống (chỉ Admin)"""
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
        total_convs = conn.execute("SELECT COUNT(*) as count FROM conversations").fetchone()['count']
        total_usage = conn.execute("SELECT SUM(count) as total FROM usage_logs").fetchone()['total'] or 0
        premium_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE subscription_tier != 'basic'").fetchone()['count']

        return jsonify({
            "total_users": total_users,
            "total_conversations": total_convs,
            "total_usage": total_usage,
            "premium_users": premium_users
        })

def delete_user(user_id_to_delete):
    """Xóa người dùng (chỉ Admin)"""
    admin_id = session.get('user_id')
    if not admin_id or not is_admin(admin_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    if user_id_to_delete == admin_id:
        return jsonify({"error": "Không thể tự xóa chính mình"}), 400

    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id_to_delete,))
        conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id_to_delete,))
        conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id_to_delete,))
        conn.commit()

    return jsonify({"success": True})