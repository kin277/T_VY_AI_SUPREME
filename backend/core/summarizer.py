"""
====================================================================
SUMMARIZER - TÓM TẮT VĂN BẢN THÔNG MINH
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 1.0.0
====================================================================
"""

import re
import math
from collections import Counter

class Summarizer:
    def __init__(self):
        self.stop_words = {"và", "của", "là", "trong", "với", "cho", "những", "các", "được", "có", "tại", "một"}
    
    def summarize(self, text: str, max_sentences: int = 5) -> str:
        """Tóm tắt văn bản"""
        if len(text) < 200:
            return text
        
        # Tách câu
        sentences = re.split(r'[.!?]+\s*', text)
        sentences = [s.strip() for s in sentences if len(s) > 20]
        
        if len(sentences) <= max_sentences:
            return ' '.join(sentences)
        
        # Tính điểm từ khóa
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(words)
        
        # Loại bỏ stop words
        for sw in self.stop_words:
            if sw in word_freq:
                del word_freq[sw]
        
        # Chọn câu quan trọng nhất
        scores = []
        for sent in sentences:
            sent_words = re.findall(r'\b\w+\b', sent.lower())
            score = sum(word_freq.get(w, 0) for w in sent_words if w not in self.stop_words)
            scores.append((score, sent))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s[1] for s in scores[:max_sentences]]
        
        # Sắp xếp theo thứ tự xuất hiện
        result = []
        for sent in sentences:
            if sent in top_sentences:
                result.append(sent)
        
        return '. '.join(result) + '.'