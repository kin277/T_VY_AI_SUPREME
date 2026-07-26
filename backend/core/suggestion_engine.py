"""
====================================================================
SUGGESTION ENGINE - T.VỸ-AI-SUPREME
====================================================================
"""

import random
from collections import Counter
from typing import List, Dict, Any

class SuggestionEngine:
    def __init__(self):
        self.topics = {
            "technology": [
                "Trí tuệ nhân tạo sẽ thay đổi thế giới như thế nào?",
                "Tương lai của lập trình với AI",
                "Blockchain và ứng dụng trong đời sống",
                "Cách bảo vệ dữ liệu cá nhân trên mạng",
                "Xu hướng công nghệ 2025"
            ],
            "programming": [
                "Học Python hay JavaScript trước?",
                "Cách tối ưu code hiệu quả",
                "Làm thế nào để trở thành lập trình viên giỏi",
                "Các framework web phổ biến nhất",
                "DevOps là gì và tại sao quan trọng"
            ],
            "life": [
                "Cách quản lý thời gian hiệu quả",
                "Bí quyết học tập nhanh và nhớ lâu",
                "Làm sao để duy trì động lực làm việc",
                "Phương pháp đọc sách hiệu quả",
                "Cân bằng công việc và cuộc sống"
            ],
            "science": [
                "Vũ trụ có bao nhiêu thiên hà?",
                "Bí ẩn về lỗ đen",
                "Tương lai của năng lượng tái tạo",
                "Công nghệ CRISPR và chỉnh sửa gen",
                "Biến đổi khí hậu và giải pháp"
            ],
            "health": [
                "Dinh dưỡng hợp lý cho người bận rộn",
                "Các bài tập thể dục tại nhà hiệu quả",
                "Cách giảm stress và lo âu",
                "Lợi ích của thiền định",
                "Giấc ngủ và sức khỏe tinh thần"
            ]
        }
    
    def get_suggestions(self, history: List[str] = None, count: int = 5) -> List[str]:
        """Lấy gợi ý câu hỏi dựa trên lịch sử"""
        if history and len(history) > 0:
            # Phân tích từ khóa từ lịch sử
            keywords = self._extract_keywords(history)
            suggestions = self._get_suggestions_by_keywords(keywords, count)
        else:
            # Gợi ý ngẫu nhiên
            all_topics = []
            for topic_list in self.topics.values():
                all_topics.extend(topic_list)
            suggestions = random.sample(all_topics, min(count, len(all_topics)))
        
        return suggestions
    
    def _extract_keywords(self, history: List[str]) -> List[str]:
        """Trích xuất từ khóa từ lịch sử chat"""
        text = " ".join(history).lower()
        keywords = []
        topic_mapping = {
            "python": "programming",
            "javascript": "programming",
            "code": "programming",
            "ai": "technology",
            "machine learning": "technology",
            "học": "life",
            "cách": "life",
            "vũ trụ": "science",
            "khoa học": "science",
            "sức khỏe": "health",
            "tập thể dục": "health"
        }
        
        for word, topic in topic_mapping.items():
            if word in text:
                keywords.append(topic)
        
        return list(set(keywords)) if keywords else ["technology", "life"]
    
    def _get_suggestions_by_keywords(self, keywords: List[str], count: int) -> List[str]:
        """Lấy gợi ý dựa trên từ khóa"""
        all_suggestions = []
        for keyword in keywords:
            if keyword in self.topics:
                all_suggestions.extend(self.topics[keyword])
        
        if len(all_suggestions) < count:
            # Bổ sung từ các chủ đề khác
            other_topics = [t for t in self.topics.keys() if t not in keywords]
            for topic in other_topics:
                all_suggestions.extend(self.topics[topic][:2])
        
        return list(set(all_suggestions))[:count]