"""
====================================================================
DATABASE MODELS - T.VỸ-VIP-FILE
====================================================================
"""

from datetime import datetime
import uuid

class User:
    def __init__(self, data=None):
        self.id = data.get("id") if data else str(uuid.uuid4())
        self.username = data.get("username", "")
        self.email = data.get("email", "")
        self.password = data.get("password", "")
        self.role = data.get("role", "user")
        self.subscription_tier = data.get("subscription_tier", "basic")
        self.subscription_expiry = data.get("subscription_expiry")
        self.provider = data.get("provider", "local")
        self.provider_id = data.get("provider_id", "")
        self.created_at = data.get("created_at", datetime.now().isoformat())
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "subscription_tier": self.subscription_tier,
            "subscription_expiry": self.subscription_expiry,
            "provider": self.provider,
            "created_at": self.created_at
        }

class Conversation:
    def __init__(self, data=None):
        self.id = data.get("id") if data else str(uuid.uuid4())
        self.user_id = data.get("user_id", "")
        self.name = data.get("name", "Đoạn chat mới")
        self.messages = data.get("messages", [])
        self.count = data.get("count", 0)
        self.level = data.get("level", "pro")
        self.created_at = data.get("created_at", datetime.now().isoformat())
        self.updated_at = data.get("updated_at", datetime.now().isoformat())
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "messages": self.messages,
            "count": self.count,
            "level": self.level,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class UsageLog:
    def __init__(self, data=None):
        self.user_id = data.get("user_id", "")
        self.tier = data.get("tier", "pro")
        self.date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        self.count = data.get("count", 0)