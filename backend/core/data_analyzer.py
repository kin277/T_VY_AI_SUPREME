"""
====================================================================
DATA ANALYZER - PHÂN TÍCH DỮ LIỆU THÔNG MINH
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 1.0.0
====================================================================
"""

import json
import csv
import io
import statistics
from typing import Dict, Any, List

class DataAnalyzer:
    def __init__(self):
        pass
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Phân tích văn bản"""
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        return {
            "word_count": len(words),
            "sentence_count": sentences,
            "avg_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
            "unique_words": len(set(words)),
            "readability": self._calculate_readability(text)
        }
    
    def _calculate_readability(self, text: str) -> str:
        """Tính độ dễ đọc"""
        words = text.split()
        if not words:
            return "Không đủ dữ liệu"
        
        avg_len = sum(len(w) for w in words) / len(words)
        if avg_len < 4:
            return "Rất dễ đọc"
        elif avg_len < 5:
            return "Dễ đọc"
        elif avg_len < 6:
            return "Trung bình"
        elif avg_len < 7:
            return "Khá khó đọc"
        else:
            return "Rất khó đọc"
    
    def analyze_numbers(self, numbers: List[float]) -> Dict[str, Any]:
        """Phân tích dãy số"""
        if not numbers:
            return {"error": "Không có dữ liệu"}
        
        return {
            "count": len(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "mean": statistics.mean(numbers),
            "median": statistics.median(numbers),
            "sum": sum(numbers)
        }