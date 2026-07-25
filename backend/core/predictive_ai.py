"""
====================================================================
PREDICTIVE AI - DỰ ĐOÁN CÂU HỎI TIẾP THEO
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 1.0.0
====================================================================
"""

import json
import random
from collections import Counter
from backend.database.db_handler import get_db

class PredictiveAI:
    def __init__(self):
        self.user_patterns = {}
        self.common_questions = [
            "Bạn có thể giúp gì?",
            "Làm thế nào để tối ưu code?",
            "Tạo ảnh bằng AI như thế nào?",
            "Giải thích về machine learning",
            "Hướng dẫn viết Python"
        ]
    
    def analyze_user(self, user_id: str):
        """Phân tích mẫu hỏi của người dùng"""
        with get_db() as conn:
            conversations = conn.execute(
                "SELECT messages FROM conversations WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            
            keywords = []
            for conv in conversations:
                try:
                    msgs = json.loads(conv['messages']) if conv['messages'] else []
                    for msg in msgs:
                        if msg['role'] == 'user':
                            words = msg['content'].split()
                            keywords.extend([w for w in words if len(w) > 3])
                except:
                    pass
            
            if keywords:
                self.user_patterns[user_id] = Counter(keywords).most_common(5)
        
        return self.user_patterns.get(user_id, [])
    
    def predict_next_question(self, user_id: str) -> str:
        """Dự đoán câu hỏi tiếp theo của người dùng"""
        if user_id in self.user_patterns:
            patterns = self.user_patterns[user_id]
            if patterns:
                top_keyword = patterns[0][0]
                return f"Dựa trên lịch sử của bạn, bạn có muốn hỏi về '{top_keyword}' không?"
        
        return random.choice(self.common_questions)