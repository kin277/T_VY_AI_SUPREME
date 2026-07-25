"""
====================================================================
SELF-LEARNING AI - TỰ HỌC TỪ LỊCH SỬ CHAT
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 1.0.0
====================================================================
"""

import json
import datetime
from collections import defaultdict
from backend.database.db_handler import get_db

class SelfLearningAI:
    def __init__(self):
        self.knowledge_graph = defaultdict(list)
        self.feedback_data = []
        self.learning_rate = 0.1
        
    def load_history(self, user_id: str):
        """Tải lịch sử chat để học"""
        with get_db() as conn:
            conversations = conn.execute(
                "SELECT messages FROM conversations WHERE user_id = ?",
                (user_id,)
            ).fetchall()
            
            for conv in conversations:
                try:
                    msgs = json.loads(conv['messages']) if conv['messages'] else []
                    for i in range(len(msgs) - 1):
                        if msgs[i]['role'] == 'user' and msgs[i+1]['role'] == 'ai':
                            self.knowledge_graph[msgs[i]['content']].append(msgs[i+1]['content'])
                except:
                    pass
        
        return len(self.knowledge_graph)
    
    def learn_from_feedback(self, query: str, response: str, rating: int):
        """Học từ phản hồi của người dùng (1-5 sao)"""
        self.feedback_data.append({
            "query": query,
            "response": response,
            "rating": rating,
            "time": datetime.datetime.now().isoformat()
        })
        
        # Nếu rating cao, lưu vào knowledge graph
        if rating >= 4:
            self.knowledge_graph[query].append(response)
        
        return {"learned": True, "total_feedback": len(self.feedback_data)}
    
    def get_improved_response(self, query: str) -> str:
        """Lấy câu trả lời được cải thiện từ knowledge graph"""
        if query in self.knowledge_graph and self.knowledge_graph[query]:
            responses = self.knowledge_graph[query]
            # Ưu tiên câu trả lời gần đây nhất
            return f"🧠 Từ bài học trước:\n\n{responses[-1]}"
        return None