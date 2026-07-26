"""
====================================================================
DATABASE HANDLER - KẾT NỐI VÀ THAO TÁC SQLITE
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import sqlite3
import json
import uuid
import datetime
from contextlib import contextmanager
from typing import Dict, Any, Optional, List

DB_PATH = "database.db"

# ===== THÊM VÀO DB_HANDLER.PY =====

def save_memory(user_id: str, key: str, value: str):
    """Lưu trí nhớ của AI về người dùng"""
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO user_memory (user_id, memory_key, memory_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, key, value))
        conn.commit()

def get_memory(user_id: str, key: str) -> Optional[str]:
    """Lấy trí nhớ của AI về người dùng"""
    with get_db() as conn:
        result = conn.execute(
            "SELECT memory_value FROM user_memory WHERE user_id = ? AND memory_key = ?",
            (user_id, key)
        ).fetchone()
        return result['memory_value'] if result else None

def get_all_memories(user_id: str) -> Dict[str, str]:
    """Lấy tất cả trí nhớ của AI về người dùng"""
    with get_db() as conn:
        results = conn.execute(
            "SELECT memory_key, memory_value FROM user_memory WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return {row['memory_key']: row['memory_value'] for row in results}

def init_db():
    """Khởi tạo database và các bảng"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Bảng users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT,
                role TEXT DEFAULT 'user',
                subscription_tier TEXT DEFAULT 'basic',
                subscription_expiry TEXT,
                provider TEXT DEFAULT 'local',
                provider_id TEXT,
                avatar TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Bảng conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT,
                messages TEXT,
                count INTEGER DEFAULT 0,
                level TEXT DEFAULT 'pro',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Bảng usage_logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                UNIQUE(user_id, tier, date)
            )
        ''')

        conn.commit()


@contextmanager
def get_db():
    """Context manager cho kết nối database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ===== USER FUNCTIONS =====

def get_user_by_email(email):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(username, email, password=None, provider='local', provider_id=None, role='user'):
    user_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, username, email, password, role, provider, provider_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, email, password, role, provider, provider_id)
        )
        conn.commit()
    return user_id


def update_subscription(user_id, tier, expiry):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET subscription_tier = ?, subscription_expiry = ? WHERE id = ?",
            (tier, expiry, user_id)
        )
        conn.commit()


def update_user_role(user_id, role):
    with get_db() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()


# ===== CONVERSATION FUNCTIONS =====

def save_conversation(user_id, conv_id, name, messages, level='pro'):
    """Lưu hoặc cập nhật đoạn chat"""
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO conversations (id, user_id, name, messages, count, level, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (conv_id, user_id, name, json.dumps(messages, ensure_ascii=False), len(messages)//2, level))
        conn.commit()


def get_conversations_by_user(user_id):
    """Lấy tất cả đoạn chat của user"""
    with get_db() as conn:
        return conn.execute("""
            SELECT id, name, count, level, created_at, updated_at
            FROM conversations WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,)).fetchall()


def get_conversation_by_id(conv_id, user_id):
    """Lấy chi tiết một đoạn chat"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, user_id)
        ).fetchone()
        if row:
            data = dict(row)
            try:
                data['messages'] = json.loads(data['messages']) if data['messages'] else []
            except:
                data['messages'] = []
            return data
        return None


def delete_conversation_by_id(conv_id, user_id):
    """Xóa một đoạn chat"""
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        conn.commit()


def delete_all_conversations(user_id):
    """Xóa tất cả đoạn chat của user"""
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        conn.commit()


# ===== USAGE LOG FUNCTIONS =====

def log_usage(user_id, tier):
    """Ghi log lượt sử dụng"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO usage_logs (user_id, tier, date, count) VALUES (?, ?, ?, 1) "
            "ON CONFLICT(user_id, tier, date) DO UPDATE SET count = count + 1",
            (user_id, tier, today)
        )
        conn.commit()


def get_usage_count(user_id, tier):
    """Lấy số lượt sử dụng trong ngày"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        log = conn.execute(
            "SELECT count FROM usage_logs WHERE user_id = ? AND tier = ? AND date = ?",
            (user_id, tier, today)
        ).fetchone()
        return log['count'] if log else 0


def get_all_usage_stats():
    """Lấy tổng lượt sử dụng toàn hệ thống (cho admin)"""
    with get_db() as conn:
        result = conn.execute("SELECT SUM(count) as total FROM usage_logs").fetchone()
        return result['total'] if result else 0


# ===== ADMIN FUNCTIONS =====

def get_all_users():
    """Lấy tất cả user (cho admin)"""
    with get_db() as conn:
        return conn.execute("""
            SELECT id, username, email, role, subscription_tier, subscription_expiry, created_at
            FROM users ORDER BY created_at DESC
        """).fetchall()


def get_total_users():
    """Lấy tổng số user"""
    with get_db() as conn:
        result = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
        return result['count'] if result else 0


def get_total_conversations():
    """Lấy tổng số đoạn chat"""
    with get_db() as conn:
        result = conn.execute("SELECT COUNT(*) as count FROM conversations").fetchone()
        return result['count'] if result else 0


def get_premium_users():
    """Lấy số user trả phí"""
    with get_db() as conn:
        result = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE subscription_tier != 'basic'"
        ).fetchone()
        return result['count'] if result else 0


def delete_user_by_id(user_id):
    """Xóa user (cho admin)"""
    with get_db() as conn:
        # Xóa các bảng liên quan
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
        conn.commit()


def get_user_usage_stats(user_id):
    """Lấy thống kê sử dụng của một user"""
    with get_db() as conn:
        total_usage = conn.execute(
            "SELECT SUM(count) as total FROM usage_logs WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conv_count = conn.execute(
            "SELECT COUNT(*) as count FROM conversations WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return {
            "total_usage": total_usage['total'] if total_usage else 0,
            "conversation_count": conv_count['count'] if conv_count else 0
        }


# ===== SESSION FUNCTIONS =====

def get_session_user():
    """Lấy user từ session (dùng trong auth)"""
    from flask import session
    user_id = session.get('user_id')
    if user_id:
        return get_user_by_id(user_id)
    return None