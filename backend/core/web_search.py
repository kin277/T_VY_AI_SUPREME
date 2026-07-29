"""
====================================================================
WEB SEARCH ENGINE - TÌM KIẾM DỮ LIỆU THỜI GIAN THỰC (MIỄN PHÍ 100%)
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 12.6.0 (Hỗ trợ giải mã HTML chuẩn, Lấy Tiêu đề + Snippet & Chống Block IP)
====================================================================
"""

import html
import logging
import random
import re
import urllib.parse
import requests

logger = logging.getLogger("TVyAI.WebSearch")

class WebSearchEngine:
    def __init__(self):
        # Danh sách User-Agent xoay tua để tránh bị DuckDuckGo chặn
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
        ]

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://duckduckgo.com/"
        }

    def _clean_text(self, text: str) -> str:
        """Làm sạch thẻ HTML và giải mã Ký tự đặc biệt"""
        if not text:
            return ""
        # Loại bỏ các thẻ HTML
        clean = re.sub(r'<[^>]+>', '', text)
        # Giải mã các ký tự HTML (&quot;, &amp;, &#27;,...)
        clean = html.unescape(clean)
        # Làm sạch khoảng trắng thừa
        return re.sub(r'\s+', ' ', clean).strip()

    def search(self, query: str, max_results: int = 4) -> str:
        """
        Truy xuất kết quả tìm kiếm thời gian thực từ DuckDuckGo.
        Trả về chuỗi văn bản tổng hợp Tiêu đề + Đoạn tóm tắt để AI đọc.
        """
        if not query or not query.strip():
            return ""

        try:
            encoded_query = urllib.parse.quote(query.strip())
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            response = requests.get(url, headers=self._get_headers(), timeout=8)
            if response.status_code != 200:
                logger.warning(f"DuckDuckGo trả về mã lỗi: {response.status_code}")
                return ""

            html_content = response.text

            # 1. Trích xuất Đoạn tóm tắt (Snippets) bằng Regex
            snippets = re.findall(r'class="result__snippet[^">]*">(.*?)</a>', html_content, re.DOTALL)
            
            # 2. Trích xuất Tiêu đề (Titles) bằng Regex
            titles = re.findall(r'class="result__a[^">]*">(.*?)</a>', html_content, re.DOTALL)

            clean_results = []
            
            # Ghép Tiêu đề + Snippet tương ứng
            for i in range(min(len(snippets), max_results)):
                snip_text = self._clean_text(snippets[i])
                title_text = self._clean_text(titles[i]) if i < len(titles) else ""

                if snip_text:
                    if title_text:
                        clean_results.append(f"• **{title_text}**: {snip_text}")
                    else:
                        clean_results.append(f"- {snip_text}")

            return "\n".join(clean_results)

        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm web: {e}")
            return ""

    def search_raw(self, query: str, max_results: int = 4) -> list:
        """
        Hàm bổ trợ: Trả về danh sách cấu trúc dict [{'title', 'snippet'}]
        """
        raw_text = self.search(query, max_results)
        if not raw_text:
            return []
        return [{"content": line} for line in raw_text.split("\n") if line.strip()]