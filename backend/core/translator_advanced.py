"""
====================================================================
ADVANCED TRANSLATOR - T.VỸ-AI-SUPREME
====================================================================
"""

import requests
import json
from typing import Dict, List, Optional

class AdvancedTranslator:
    def __init__(self):
        self.supported_langs = {
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
            "th": "ไทย",
            "it": "Italiano",
            "pt": "Português",
            "nl": "Nederlands"
        }
    
    def translate(self, text: str, target_lang: str = "vi") -> Dict[str, str]:
        """Dịch văn bản với chất lượng cao"""
        try:
            # Sử dụng Google Translate API (miễn phí)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={text.replace(' ', '%20')}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                translated = data[0][0][0]
                detected_lang = data[2] if len(data) > 2 else "vi"
                
                return {
                    "success": True,
                    "original": text,
                    "translated": translated,
                    "detected_lang": detected_lang,
                    "target_lang": target_lang
                }
        except:
            pass
        
        return {
            "success": False,
            "error": "Không thể dịch văn bản"
        }
    
    def translate_batch(self, texts: List[str], target_lang: str = "vi") -> List[Dict]:
        """Dịch nhiều văn bản cùng lúc"""
        results = []
        for text in texts:
            results.append(self.translate(text, target_lang))
        return results
    
    def get_supported_languages(self) -> Dict[str, str]:
        return self.supported_langs