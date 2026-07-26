"""
====================================================================
MULTI-LANGUAGE TRANSLATOR - T.VỸ-AI-SUPREME
====================================================================
"""

import requests
import os
from typing import Dict, List

class LanguageDetector:
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
            "ar": "العربية",
            "hi": "हिन्दी",
            "th": "ไทย"
        }
    
    def detect(self, text: str) -> str:
        """Phát hiện ngôn ngữ của văn bản"""
        try:
            # Sử dụng Google Translate API (miễn phí)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={text.replace(' ', '%20')}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                lang_code = data[2] if len(data) > 2 else "vi"
                return lang_code
        except:
            pass
        return "vi"  # Mặc định
    
    def translate(self, text: str, target_lang: str = "vi") -> str:
        """Dịch văn bản sang ngôn ngữ đích"""
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={text.replace(' ', '%20')}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                return data[0][0][0]
        except:
            pass
        return text
    
    def get_supported_languages(self) -> Dict[str, str]:
        return self.supported_languages