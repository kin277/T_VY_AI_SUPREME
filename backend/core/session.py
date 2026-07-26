"""
====================================================================
SESSION MANAGER - T.VỸ-AI-SUPREME
====================================================================
"""

import datetime
import uuid
from typing import Optional, Dict

class SessionManager:
    def __init__(self):
        self.sessions = {}  # Lưu session tạm (có thể thay bằng database)
        self.session_timeout_hours = 24  # 24 giờ tự động đăng xuất
    
    def create_session(self, user_id: str) -> str:
        """Tạo session mới"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.datetime.now(),
            "expires_at": datetime.datetime.now() + datetime.timedelta(hours=self.session_timeout_hours)
        }
        return session_id
    
    def get_user_id(self, session_id: str) -> Optional[str]:
        """Lấy user_id từ session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        if datetime.datetime.now() > session["expires_at"]:
            del self.sessions[session_id]
            return None
        
        return session["user_id"]
    
    def refresh_session(self, session_id: str) -> bool:
        """Gia hạn session"""
        if session_id not in self.sessions:
            return False
        self.sessions[session_id]["expires_at"] = datetime.datetime.now() + datetime.timedelta(hours=self.session_timeout_hours)
        return True
    
    def delete_session(self, session_id: str):
        """Xóa session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_guest_session(self) -> str:
        """Tạo session cho khách"""
        guest_id = f"guest_{str(uuid.uuid4())[:8]}"
        return self.create_session(guest_id)