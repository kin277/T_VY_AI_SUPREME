"""
====================================================================
DATABASE MODELS - T.VỸ-AI-SUPREME
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import sqlite3
import json
import uuid
import datetime
from typing import Dict, Any, Optional, List

DB_PATH = "database.db"


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
                last_music_reset TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Bảng user_memory (Trí nhớ dài hạn của AI)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory_key TEXT NOT NULL,
                memory_value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, memory_key)
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

        # Bảng user_preferences (Tùy chỉnh người dùng)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pref_key TEXT NOT NULL,
                pref_value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, pref_key)
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


# ================================================================
# USER FUNCTIONS
# ================================================================

def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id: str) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(username: str, email: str, password: str = None, 
                provider: str = 'local', provider_id: str = None, 
                role: str = 'user') -> str:
    user_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (id, username, email, password, role, provider, provider_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, email, password, role, provider, provider_id)
        )
        conn.commit()
    return user_id


def update_user_role(user_id: str, role: str):
    with get_db() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()


def update_subscription(user_id: str, tier: str, expiry: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET subscription_tier = ?, subscription_expiry = ? WHERE id = ?",
            (tier, expiry, user_id)
        )
        conn.commit()


def update_last_music_reset(user_id: str, reset_time: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET last_music_reset = ? WHERE id = ?",
            (reset_time, user_id)
        )
        conn.commit()


def get_last_music_reset(user_id: str) -> Optional[str]:
    with get_db() as conn:
        result = conn.execute(
            "SELECT last_music_reset FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        return result['last_music_reset'] if result else None


# ================================================================
# MEMORY FUNCTIONS (Trí nhớ dài hạn)
# ================================================================

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


def delete_memory(user_id: str, key: str):
    """Xóa trí nhớ của AI về người dùng"""
    with get_db() as conn:
        conn.execute(
            "DELETE FROM user_memory WHERE user_id = ? AND memory_key = ?",
            (user_id, key)
        )
        conn.commit()


# ================================================================
# CONVERSATION FUNCTIONS
# ================================================================

def save_conversation(user_id: str, conv_id: str, name: str, messages: list, level: str = 'pro'):
    """Lưu hoặc cập nhật đoạn chat"""
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO conversations (id, user_id, name, messages, count, level, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (conv_id, user_id, name, json.dumps(messages, ensure_ascii=False), len(messages)//2, level))
        conn.commit()


def get_conversations_by_user(user_id: str) -> List[Dict]:
    """Lấy tất cả đoạn chat của user"""
    with get_db() as conn:
        return conn.execute("""
            SELECT id, name, count, level, created_at, updated_at
            FROM conversations WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,)).fetchall()


def get_conversation_by_id(conv_id: str, user_id: str) -> Optional[Dict]:
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


def delete_conversation_by_id(conv_id: str, user_id: str):
    """Xóa một đoạn chat"""
    with get_db() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conv_id, user_id))
        conn.commit()


# ================================================================
# USAGE LOG FUNCTIONS
# ================================================================

def log_usage(user_id: str, tier: str):
    """Ghi log lượt sử dụng"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO usage_logs (user_id, tier, date, count) VALUES (?, ?, ?, 1) "
            "ON CONFLICT(user_id, tier, date) DO UPDATE SET count = count + 1",
            (user_id, tier, today)
        )
        conn.commit()


def get_usage_count(user_id: str, tier: str) -> int:
    """Lấy số lượt sử dụng trong ngày"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        log = conn.execute(
            "SELECT count FROM usage_logs WHERE user_id = ? AND tier = ? AND date = ?",
            (user_id, tier, today)
        ).fetchone()
        return log['count'] if log else 0


def reset_usage_count(user_id: str, tier: str):
    """Reset lượt sử dụng"""
    with get_db() as conn:
        conn.execute(
            "DELETE FROM usage_logs WHERE user_id = ? AND tier = ?",
            (user_id, tier)
        )
        conn.commit()


# ================================================================
# PREFERENCE FUNCTIONS
# ================================================================

def save_preference(user_id: str, key: str, value: str):
    """Lưu tùy chỉnh người dùng"""
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO user_preferences (user_id, pref_key, pref_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, key, value))
        conn.commit()


def get_preference(user_id: str, key: str) -> Optional[str]:
    """Lấy tùy chỉnh người dùng"""
    with get_db() as conn:
        result = conn.execute(
            "SELECT pref_value FROM user_preferences WHERE user_id = ? AND pref_key = ?",
            (user_id, key)
        ).fetchone()
        return result['pref_value'] if result else None


def get_all_preferences(user_id: str) -> Dict[str, str]:
    """Lấy tất cả tùy chỉnh người dùng"""
    with get_db() as conn:
        results = conn.execute(
            "SELECT pref_key, pref_value FROM user_preferences WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        return {row['pref_key']: row['pref_value'] for row in results}


# ================================================================
# ADMIN FUNCTIONS
# ================================================================

def get_all_users() -> List[Dict]:
    """Lấy tất cả user (cho admin)"""
    with get_db() as conn:
        return conn.execute("""
            SELECT id, username, email, role, subscription_tier, subscription_expiry, created_at
            FROM users ORDER BY created_at DESC
        """).fetchall()


def get_total_users() -> int:
    with get_db() as conn:
        result = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
        return result['count'] if result else 0


def get_total_conversations() -> int:
    with get_db() as conn:
        result = conn.execute("SELECT COUNT(*) as count FROM conversations").fetchone()
        return result['count'] if result else 0


def get_premium_users() -> int:
    with get_db() as conn:
        result = conn.execute(
            "SELECT COUNT(*) as count FROM users WHERE subscription_tier != 'basic'"
        ).fetchone()
        return result['count'] if result else 0


def get_all_usage_stats() -> int:
    with get_db() as conn:
        result = conn.execute("SELECT SUM(count) as total FROM usage_logs").fetchone()
        return result['total'] if result else 0


def delete_user_by_id(user_id: str):
    """Xóa user (cho admin)"""
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM user_memory WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
        conn.commit()