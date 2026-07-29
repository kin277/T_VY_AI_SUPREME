"""
====================================================================
WEB SEARCH ENGINE - TÌM KIẾM DỮ LIỆU THỜI GIAN THỰC (MIỄN PHÍ 100%)
====================================================================
"""

import requests
import re
import urllib.parse

class WebSearchEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def search(self, query: str, max_results: int = 4) -> str:
        """Truy xuất kết quả tìm kiếm thời gian thực từ DuckDuckGo"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            response = requests.get(url, headers=self.headers, timeout=8)
            if response.status_code != 200:
                return ""

            html = response.text
            # Trích xuất đoạn tóm tắt bằng Regex
            snippets = re.findall(r'class="result__snippet[^">]*">(.*?)</a>', html, re.DOTALL)
            
            clean_results = []
            for snip in snippets[:max_results]:
                clean_text = re.sub(r'<[^>]+>', '', snip).strip()
                clean_text = clean_text.replace('&quot;', '"').replace('&amp;', '&').replace('&#27;', "'")
                if clean_text:
                    clean_results.append(f"- {clean_text}")

            return "\n".join(clean_results)
        except Exception:
            return ""