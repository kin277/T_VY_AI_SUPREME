"""
====================================================================
MEDIA PROCESSOR - T.VỸ-AI-SUPREME
====================================================================
"""

import requests
import json
import re
from typing import Dict, Any

class MediaProcessor:
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
    
    def extract_youtube_info(self, url: str) -> Dict[str, Any]:
        """Lấy thông tin video YouTube"""
        try:
            # Trích xuất video ID
            video_id = self._extract_video_id(url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}
            
            # Gọi YouTube API (cần API key)
            if self.youtube_api_key:
                api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={self.youtube_api_key}&part=snippet,contentDetails"
                response = requests.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        item = data['items'][0]
                        return {
                            "title": item['snippet']['title'],
                            "description": item['snippet']['description'],
                            "duration": item['contentDetails']['duration'],
                            "thumbnail": item['snippet']['thumbnails']['high']['url']
                        }
            return {"error": "Không thể lấy thông tin video"}
        except Exception as e:
            return {"error": str(e)}
    
    def generate_podcast_script(self, topic: str, duration: int = 5) -> str:
        """Tạo kịch bản podcast từ chủ đề"""
        script_template = f"""
🎙️ **PODCAST: {topic.upper()}**

📝 **Thời lượng:** {duration} phút

🎯 **Mục tiêu:** Cung cấp thông tin chuyên sâu về {topic}

---

**[Giới thiệu - 30s]**
Xin chào! Chào mừng bạn đến với podcast hôm nay. Chúng ta sẽ cùng khám phá về {topic}.

---

**[Nội dung chính - {duration-1} phút]**
Hôm nay, chúng ta sẽ đi sâu vào các khía cạnh quan trọng của {topic}:

1. **Khái niệm cơ bản**
   - {topic} là gì?
   - Tại sao {topic} lại quan trọng?

2. **Ứng dụng thực tế**
   - {topic} được áp dụng như thế nào trong đời sống?
   - Các ví dụ điển hình

3. **Xu hướng và tương lai**
   - {topic} sẽ phát triển ra sao?
   - Cơ hội và thách thức

---

**[Kết luận - 30s]**
Cảm ơn bạn đã lắng nghe! Hẹn gặp lại trong tập tiếp theo.

---

💡 **Hướng dẫn ghi âm:**
- Đọc với giọng tự nhiên, tốc độ vừa phải
- Nhấn mạnh các ý chính
- Thêm âm nhạc nền phù hợp
"""
        return script_template
    
    def _extract_video_id(self, url: str) -> str:
        """Trích xuất YouTube video ID từ URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([\w-]+)',
            r'(?:youtu\.be\/)([\w-]+)',
            r'(?:youtube\.com\/embed\/)([\w-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None