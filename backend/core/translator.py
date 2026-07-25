"""
====================================================================
TRANSLATOR - HỖ TRỢ ĐA NGÔN NGỮ
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 1.0.0
====================================================================
"""

import requests
import os

class Translator:
    def __init__(self):
        self.supported_languages = {
            "vi": "Tiếng Việt",
            "en": "English",
            "ko": "한국어",
            "ja": "日本語",
            "zh": "中文",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español",
            "ru": "Русский",
            "ar": "العربية"
        }
    
    def translate(self, text: str, target_lang: str = "vi") -> str:
        """Dịch văn bản sang ngôn ngữ đích"""
        # Sử dụng Google Translate API (có thể dùng free)
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={text.replace(' ', '%20')}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data[0][0][0]
        except:
            pass
        
        # Fallback: trả về nguyên bản
        return text
    
    def detect_language(self, text: str) -> str:
        """Phát hiện ngôn ngữ"""
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={text.replace(' ', '%20')}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data[2]
        except:
            pass
        return "vi"