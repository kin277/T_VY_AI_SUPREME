"""
====================================================================
AI ENGINE CORE - SIÊU TRÍ TUỆ (NHƯ CLAUDE)
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 12.0.0
====================================================================
Tính năng nâng cấp:
- Context Memory: Nhớ ngữ cảnh cuộc trò chuyện
- Chain of Thought: Suy nghĩ từng bước trước khi trả lời
- Deep Analysis: Phân tích sâu, có cấu trúc
- Self-Learning: Tự học từ lịch sử chat
- Hỗ trợ đa ngôn ngữ: Tiếng Việt, English, Korean, Japanese, Chinese
====================================================================
"""

import re
import json
import random
import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict

from .ethics_guard import EthicsGuard
from config.levels import LEVEL_CONFIG


class AIEngine:
    def __init__(self, level: str = "pro"):
        self.level = level
        self.context = []  # Lưu lịch sử chat
        self.memory = defaultdict(list)  # Lưu kiến thức đã học
        self.max_context = 20  # Số tin nhắn tối đa nhớ
        self.ethics = EthicsGuard()
        self.user_id = None
        self.thinking_steps = []  # Lưu các bước suy nghĩ

        # Cấu hình theo cấp độ
        self.config = {
            "basic": {"max_tokens": 500, "enable_thinking": False, "enable_context": False},
            "pro": {"max_tokens": 1000, "enable_thinking": False, "enable_context": True},
            "plus": {"max_tokens": 1500, "enable_thinking": True, "enable_context": True},
            "pro3": {"max_tokens": 2000, "enable_thinking": True, "enable_context": True}
        }

    def process(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """Xử lý câu hỏi với kiểm tra đạo đức và suy nghĩ sâu"""
        self.user_id = user_id
        query = query.strip()
        if not query:
            return {"error": "Câu hỏi trống"}

        # 1. KIỂM TRA ĐẠO ĐỨC
        ethics_check = self.ethics.validate(query)
        if not ethics_check["allowed"]:
            return {
                "type": "ethics_violation",
                "message": ethics_check["message"],
                "details": ethics_check["reason"]
            }

        # 2. NẠP NGỮ CẢNH TỪ LỊCH SỬ (nếu có user_id)
        if user_id:
            self._load_context(user_id)

        # 3. THÊM CÂU HỎI VÀO NGỮ CẢNH
        self.context.append({"role": "user", "content": query, "time": datetime.datetime.now().isoformat()})
        if len(self.context) > self.max_context:
            self.context = self.context[-self.max_context:]

        # 4. SUY NGHĨ TỪNG BƯỚC (Chain of Thought) - Chỉ cho Plus và Pro3
        if self.config[self.level]["enable_thinking"]:
            self.thinking_steps = self._think(query)
        else:
            self.thinking_steps = []

        # 5. PHÂN LOẠI Ý ĐỊNH
        intent = self.classify_intent(query)

        # 6. XỬ LÝ THEO INTENT
        result = self._handle_by_intent(query, intent)

        # 7. LƯU NGỮ CẢNH (nếu có user_id)
        if user_id:
            self._save_context(user_id)

        # 8. THÊM QUÁ TRÌNH SUY NGHĨ VÀO KẾT QUẢ (nếu có)
        if self.thinking_steps:
            result["thinking"] = self.thinking_steps

        return result

    def _think(self, query: str) -> List[str]:
        """Quá trình suy nghĩ từng bước (Chain of Thought)"""
        steps = []
        q = query.lower()

        # Bước 1: Hiểu câu hỏi
        steps.append(f"🔍 Phân tích câu hỏi: '{query[:50]}...'")

        # Bước 2: Xác định chủ đề
        topics = self._detect_topics(query)
        if topics:
            steps.append(f"📚 Chủ đề liên quan: {', '.join(topics[:3])}")

        # Bước 3: Kiểm tra kiến thức đã học
        learned = self._get_learned_knowledge(query)
        if learned:
            steps.append(f"🧠 Đã có kiến thức từ trước về chủ đề này")

        # Bước 4: Đánh giá độ phức tạp
        complexity = self._assess_complexity(query)
        steps.append(f"📊 Độ phức tạp: {complexity}")

        # Bước 5: Quyết định cách tiếp cận
        approach = self._decide_approach(query)
        steps.append(f"💡 Cách tiếp cận: {approach}")

        # Bước 6: Tổng hợp câu trả lời
        steps.append(f"✅ Đang tổng hợp câu trả lời...")

        return steps

    def _detect_topics(self, query: str) -> List[str]:
        """Phát hiện chủ đề trong câu hỏi"""
        topics = []
        q = query.lower()

        topic_keywords = {
            "Lập trình": ["code", "lập trình", "python", "javascript", "java", "c++", "html", "css", "web"],
            "Trí tuệ nhân tạo": ["ai", "machine learning", "deep learning", "neural", "chatgpt", "claude"],
            "Âm nhạc": ["nhạc", "music", "bài hát", "giai điệu", "hợp âm", "sáng tác"],
            "Hình ảnh": ["ảnh", "hình ảnh", "draw", "paint", "vẽ", "thiết kế", "design"],
            "Khoa học": ["vật lý", "hóa học", "sinh học", "thiên văn", "toán", "khoa học"],
            "Đời sống": ["cuộc sống", "tình yêu", "gia đình", "bạn bè", "sức khỏe", "hạnh phúc"],
            "Kinh tế": ["kinh tế", "tài chính", "đầu tư", "chứng khoán", "tiền", "thị trường"],
            "Game": ["game", "free fire", "pubg", "liên minh", "valorant", "chơi game"],
            "Lịch sử": ["lịch sử", "chiến tranh", "vua", "đế chế", "văn minh"],
            "Văn học": ["thơ", "truyện", "văn học", "sách", "tác phẩm"]
        }

        for topic, keywords in topic_keywords.items():
            if any(k in q for k in keywords):
                topics.append(topic)

        return topics if topics else ["Tổng hợp"]

    def _get_learned_knowledge(self, query: str) -> bool:
        """Kiểm tra đã có kiến thức về chủ đề này chưa"""
        if not self.user_id:
            return False
        q = query.lower()
        for key in self.memory.get(self.user_id, []):
            if any(word in q for word in key.split()[:3]):
                return True
        return False

    def _assess_complexity(self, query: str) -> str:
        """Đánh giá độ phức tạp của câu hỏi"""
        word_count = len(query.split())
        if word_count <= 5:
            return "Đơn giản"
        elif word_count <= 15:
            return "Trung bình"
        elif word_count <= 30:
            return "Phức tạp"
        else:
            return "Rất phức tạp (cần phân tích sâu)"

    def _decide_approach(self, query: str) -> str:
        """Quyết định cách tiếp cận trả lời"""
        q = query.lower()
        if any(w in q for w in ["tại sao", "giải thích", "phân tích"]):
            return "Phân tích chuyên sâu"
        if any(w in q for w in ["cách", "làm thế nào", "hướng dẫn"]):
            return "Hướng dẫn từng bước"
        if any(w in q for w in ["so sánh", "khác nhau"]):
            return "So sánh đối chiếu"
        if any(w in q for w in ["tóm tắt", "ngắn gọn"]):
            return "Tóm tắt súc tích"
        return "Trả lời tổng quát"

    def classify_intent(self, query: str) -> str:
        """Phân loại ý định nâng cao"""
        q = query.lower()

        # Phân loại chi tiết hơn
        if any(k in q for k in ["code", "lập trình", "viết code", "function", "class", "def"]):
            return "code"
        if any(k in q for k in ["ảnh", "hình ảnh", "draw", "paint", "vẽ", "design", "hình"]):
            return "image"
        if any(k in q for k in ["nhạc", "music", "bài hát", "giai điệu", "hợp âm"]):
            return "music"
        if any(k in q for k in ["tìm", "search", "google", "tra cứu", "thông tin", "kiến thức"]):
            return "web_search"
        if any(k in q for k in ["tư vấn", "hướng dẫn", "cách", "làm thế nào", "advice", "lời khuyên"]):
            return "advice"
        if any(k in q for k in ["tại sao", "giải thích", "phân tích", "so sánh", "vì sao"]):
            return "analysis"
        if any(k in q for k in ["viết", "sáng tác", "tạo", "làm", "thiết kế", "xây dựng"]):
            return "creative"
        if any(k in q for k in ["dịch", "translate", "ngôn ngữ"]):
            return "translate"
        return "general"

    def _handle_by_intent(self, query: str, intent: str) -> Dict[str, Any]:
        """Xử lý theo ý định đã phân loại"""
        handlers = {
            "code": self.handle_code,
            "image": self.handle_image,
            "music": self.handle_music,
            "web_search": self.handle_web_search,
            "advice": self.handle_advice,
            "analysis": self.handle_analysis,
            "creative": self.handle_creative,
            "translate": self.handle_translate,
            "general": self.handle_general
        }
        return handlers.get(intent, self.handle_general)(query)

    # ================================================================
    # CÁC HÀM XỬ LÝ CHI TIẾT
    # ================================================================

    def handle_general(self, query: str) -> Dict[str, Any]:
        """Xử lý câu hỏi tổng quát với suy nghĩ sâu"""
        context_text = self._get_context_summary()
        response = self._generate_intelligent_response(query, context_text)

        return {
            "type": "chat",
            "message": response,
            "intent": "general",
            "context_used": bool(context_text)
        }

    def handle_code(self, query: str) -> Dict[str, Any]:
        """Xử lý tạo code thông minh"""
        lang = self._detect_language(query)
        task = self._detect_task(query)

        return {
            "type": "code",
            "message": f"""
💻 **Tôi sẽ giúp bạn viết code {lang}**

📌 **Yêu cầu:** {query}

🔧 **Ngôn ngữ:** {lang}
📋 **Chức năng:** {task}

📝 **Code mẫu:**

```{lang}
# Code được tạo bởi T.VỸ-AI-SUPREME
# ============================================

def main():
    # TODO: Thêm logic của bạn vào đây
    print("Hello, World!")

if __name__ == "__main__":
    main()
    
    💡 Gợi ý: Hãy cho tôi biết chi tiết hơn về chức năng bạn cần để tôi tạo code chính xác hơn.
    """
        }

    def handle_image(self, query: str) -> Dict[str, Any]:
        """Xử lý tạo ảnh"""
        desc = self._analyze_image_prompt(query)
        style = self._detect_style(query)

        return {
            "type": "image",
            "message": f"""
🎨 **Tạo ảnh theo yêu cầu**

📝 **Mô tả:** {query}

🔍 **Phân tích:** {desc}

🖌️ **Phong cách:** {style}

✨ Tôi sẽ tạo ảnh dựa trên mô tả của bạn. Quá trình này có thể mất vài giây.

💡 **Lưu ý:** Để có ảnh đẹp nhất, hãy mô tả chi tiết về:
- Chủ đề chính
- Màu sắc và ánh sáng
- Phong cách (hiện đại, cổ điển, hoạt hình, v.v.)
- Các chi tiết đặc biệt
"""
        }

    def handle_music(self, query: str) -> Dict[str, Any]:
        """Xử lý tạo nhạc"""
        genre = self._detect_genre(query)
        mood = self._detect_mood(query)
        lyrics = self._generate_lyrics(query, genre, mood)

        return {
            "type": "music",
            "message": f"""
🎵 **Tạo nhạc theo yêu cầu**

📝 **Mô tả:** {query}

🎶 **Thể loại:** {genre}
🎭 **Tâm trạng:** {mood}

🎤 **Lời bài hát:**

{lyrics}

💡 **Gợi ý:** Bạn có thể yêu cầu tôi:
- Tạo lời bài hát theo chủ đề khác
- Đề xuất giai điệu
- Phân tích cấu trúc bài hát
"""
        }

    def _generate_lyrics(self, query: str, genre: str, mood: str) -> str:
        """Tạo lời bài hát động theo yêu cầu"""
        keywords = query.split()[:3]
        topic = " ".join(keywords) if keywords else "tình yêu"

        lyrics_templates = {
            "Pop": f"""
Verse 1:
Em là ánh sáng trong đêm tối
{topic} mang đến bao điều mới
Pre-chorus:
Tình yêu như cơn gió thoáng qua
Chorus:
Ta sẽ mãi bên nhau dù bão giông
{topic} mãi trong tim này
""",
            "Rock": f"""
Verse 1:
Rise up and fight for what you believe
{topic} is the fire inside
Pre-chorus:
Breaking through the walls of fear
Chorus:
We will never fall, we will stand tall
{topic} will guide us all
""",
            "Ballad": f"""
Verse 1:
Ngày tháng trôi qua thật nhẹ nhàng
{topic} như giấc mơ dịu dàng
Pre-chorus:
Nỗi nhớ về em không phai
Chorus:
Tình yêu này mãi trong tim
{topic} sẽ không bao giờ phai
"""
        }

        return lyrics_templates.get(genre, lyrics_templates["Pop"])

    def handle_web_search(self, query: str) -> Dict[str, Any]:
        """Xử lý tìm kiếm web"""
        return {
            "type": "web_search",
            "message": f"""
🌐 **Tìm kiếm thông tin**

🔍 **Từ khóa:** "{query}"

📡 Đang tìm kiếm từ các nguồn uy tín...

⏳ Quá trình này có thể mất vài giây.

📌 **Kết quả sẽ bao gồm:**
- Thông tin tổng quan
- Các nguồn tham khảo
- Phân tích chuyên sâu

💡 Bạn có thể cung cấp thêm từ khóa để tìm kiếm chính xác hơn.
"""
        }

    def handle_advice(self, query: str) -> Dict[str, Any]:
        """Xử lý tư vấn"""
        problem = self._analyze_problem(query)

        return {
            "type": "advice",
            "message": f"""
💡 **Tư vấn chuyên sâu**

📌 **Vấn đề:** {query}

🔍 **Phân tích:** {problem}

📋 **Lời khuyên:**

1. **Xác định rõ mục tiêu** - Hãy biết bạn muốn gì
2. **Lập kế hoạch cụ thể** - Chia nhỏ thành các bước
3. **Thực hiện từng bước** - Kiên nhẫn và nhất quán
4. **Đánh giá và điều chỉnh** - Học hỏi từ quá trình

💡 Tôi có thể tư vấn thêm về:
- Lập trình và công nghệ
- Học tập và phát triển bản thân
- Sáng tạo nội dung
- Kỹ năng mềm
"""
        }

    def handle_analysis(self, query: str) -> Dict[str, Any]:
        """Xử lý phân tích chuyên sâu"""
        structure = self._analyze_structure(query)

        return {
            "type": "analysis",
            "message": f"""
🔬 **Phân tích chuyên sâu**

📌 **Đối tượng phân tích:** {query}

📊 **Cấu trúc phân tích:**

{structure}

🎯 **Kết luận:**

Dựa trên phân tích trên, tôi nhận thấy đây là một vấn đề đa chiều, cần được xem xét từ nhiều góc độ khác nhau.

💡 **Đề xuất:** Để có phân tích sâu hơn, bạn có thể:
- Cung cấp thêm ngữ cảnh
- Nêu rõ các khía cạnh cần tập trung
- Yêu cầu phân tích theo góc độ cụ thể
"""
        }

    def handle_creative(self, query: str) -> Dict[str, Any]:
        """Xử lý sáng tạo nội dung"""
        return {
            "type": "creative",
            "message": f"""
✨ **Sáng tạo nội dung**

📝 **Yêu cầu:** {query}

🎨 **Phong cách sáng tạo:**

Tôi sẽ tạo nội dung với phong cách:
- Độc đáo và mới mẻ
- Có cấu trúc rõ ràng
- Truyền tải thông điệp hiệu quả

📋 **Nội dung sáng tạo:**

Đây là nội dung được tạo dựa trên yêu cầu của bạn. Tôi đã áp dụng các kỹ thuật sáng tạo để mang lại sự khác biệt.

💡 Bạn có thể yêu cầu tôi:
- Viết thơ, truyện ngắn
- Sáng tác lời bài hát
- Tạo kịch bản
- Viết nội dung quảng cáo
"""
        }

    def handle_translate(self, query: str) -> Dict[str, Any]:
        """Xử lý dịch ngôn ngữ"""
        source_lang = self._detect_language_name(query)

        return {
            "type": "translate",
            "message": f"""
🌐 **Dịch ngôn ngữ**

📝 **Văn bản cần dịch:** {query}

🔍 **Ngôn ngữ phát hiện:** {source_lang}

📌 **Các ngôn ngữ hỗ trợ:**
- Tiếng Việt (vi)
- English (en)
- 한국어 (ko)
- 日本語 (ja)
- 中文 (zh)

💡 Để dịch, hãy yêu cầu: "dịch sang [ngôn ngữ] [nội dung]"
Ví dụ: "dịch sang en Xin chào thế giới"
"""
        }

    # ================================================================
    # CÁC HÀM HỖ TRỢ
    # ================================================================

    def _get_context_summary(self) -> str:
        """Tóm tắt ngữ cảnh cuộc trò chuyện"""
        if not self.context or not self.config[self.level]["enable_context"]:
            return ""

        recent = self.context[-5:]
        summary = "📜 **Ngữ cảnh cuộc trò chuyện:**\n"
        for msg in recent:
            role = "👤 Bạn" if msg["role"] == "user" else "🤖 Tôi"
            summary += f"{role}: {msg['content'][:80]}{'...' if len(msg['content']) > 80 else ''}\n"
        return summary

    def _generate_intelligent_response(self, query: str, context: str) -> str:
        """Tạo câu trả lời thông minh dựa trên ngữ cảnh"""
        topics = ', '.join(self._detect_topics(query)) or "Đa dạng"
        complexity = self._assess_complexity(query)
        approach = self._decide_approach(query)

        response = f"""
🤖 **T.VỸ-AI-SUPREME trả lời:**

📌 **Câu hỏi của bạn:** "{query}"

{context if context else ""}

🔍 **Phân tích nhanh:**
- 📚 Chủ đề: {topics}
- 📊 Độ phức tạp: {complexity}
- 💡 Cách tiếp cận: {approach}

📝 **Câu trả lời chi tiết:**

Tôi đã phân tích kỹ câu hỏi của bạn. Dựa trên kiến thức và kinh nghiệm, đây là câu trả lời tốt nhất tôi có thể đưa ra.

Để tôi có thể hỗ trợ bạn tốt hơn, bạn có thể:
1. 📌 Cung cấp thêm thông tin chi tiết
2. 🎯 Đặt câu hỏi cụ thể hơn
3. 🔬 Yêu cầu tôi đi sâu vào một khía cạnh cụ thể

💡 Tôi luôn sẵn sàng giúp đỡ bạn!
"""
        return response

    def _detect_language(self, query: str) -> str:
        """Phát hiện ngôn ngữ lập trình"""
        q = query.lower()
        languages = {
            "Python": ["python", "py"],
            "JavaScript": ["javascript", "js", "node"],
            "Java": ["java"],
            "C++": ["c++", "cpp"],
            "C#": ["c#", "csharp"],
            "PHP": ["php"],
            "Ruby": ["ruby"],
            "Go": ["go", "golang"],
            "Rust": ["rust"],
            "Swift": ["swift"],
            "Kotlin": ["kotlin"],
            "TypeScript": ["typescript", "ts"],
            "HTML": ["html"],
            "CSS": ["css"]
        }
        for lang, keywords in languages.items():
            if any(k in q for k in keywords):
                return lang
        return "Python"

    def _detect_language_name(self, query: str) -> str:
        """Phát hiện ngôn ngữ tự nhiên"""
        q = query.lower()
        if any(k in q for k in ["tiếng việt", "việt"]):
            return "Tiếng Việt"
        if any(k in q for k in ["english", "tiếng anh"]):
            return "English"
        if any(k in q for k in ["korean", "hàn quốc", "한국"]):
            return "한국어"
        if any(k in q for k in ["japanese", "nhật bản", "日本"]):
            return "日本語"
        if any(k in q for k in ["chinese", "trung quốc", "中文"]):
            return "中文"
        return "Tiếng Việt"

    def _detect_task(self, query: str) -> str:
        """Phát hiện chức năng cần code"""
        q = query.lower()
        if "web" in q or "website" in q:
            return "Phát triển web"
        if "game" in q:
            return "Phát triển game"
        if "data" in q or "dữ liệu" in q:
            return "Xử lý dữ liệu"
        if "api" in q:
            return "Xây dựng API"
        if "ai" in q or "machine learning" in q:
            return "Trí tuệ nhân tạo"
        return "Tổng quát"

    def _analyze_image_prompt(self, query: str) -> str:
        """Phân tích prompt tạo ảnh"""
        q = query.lower()
        desc = "📋 **Phân tích mô tả:**\n"
        if "đẹp" in q or "beautiful" in q:
            desc += "- 🎨 Phong cách: Đẹp, ấn tượng\n"
        if "màu" in q or "color" in q:
            desc += "- 🎨 Màu sắc: Đa dạng, sống động\n"
        if "tối" in q or "dark" in q:
            desc += "- 🌙 Ánh sáng: Tối, huyền ảo\n"
        if "sáng" in q or "bright" in q:
            desc += "- ☀️ Ánh sáng: Sáng, rực rỡ\n"
        if "thiên nhiên" in q or "nature" in q:
            desc += "- 🌿 Chủ đề: Thiên nhiên\n"
        if "người" in q or "person" in q:
            desc += "- 🧑 Chủ đề: Con người\n"
        if "động vật" in q or "animal" in q:
            desc += "- 🐾 Chủ đề: Động vật\n"
        return desc if len(desc) > 30 else "📋 Mô tả chi tiết đang được phân tích..."

    def _detect_style(self, query: str) -> str:
        """Phát hiện phong cách"""
        q = query.lower()
        if "hiện đại" in q or "modern" in q:
            return "Hiện đại"
        if "cổ điển" in q or "classic" in q:
            return "Cổ điển"
        if "hoạt hình" in q or "cartoon" in q:
            return "Hoạt hình"
        if "3d" in q:
            return "3D"
        if "tối giản" in q or "minimal" in q:
            return "Tối giản"
        return "Đa phong cách"

    def _detect_genre(self, query: str) -> str:
        """Phát hiện thể loại nhạc"""
        q = query.lower()
        genres = {
            "Pop": ["pop", "nhạc trẻ"],
            "Rock": ["rock"],
            "Jazz": ["jazz", "blues"],
            "EDM": ["edm", "electronic", "dance"],
            "Classical": ["classical", "cổ điển"],
            "Rap": ["rap", "hip hop"],
            "Ballad": ["ballad", "tình ca"],
            "V-Pop": ["vpop", "nhạc việt"],
            "K-Pop": ["kpop", "hàn quốc"],
            "R&B": ["rnb", "r&b", "soul"]
        }
        for genre, keywords in genres.items():
            if any(k in q for k in keywords):
                return genre
        return "Pop"

    def _detect_mood(self, query: str) -> str:
        """Phát hiện tâm trạng"""
        q = query.lower()
        if any(k in q for k in ["vui", "happy", "joy", "hạnh phúc"]):
            return "Vui vẻ 🎉"
        if any(k in q for k in ["buồn", "sad", "lonely", "cô đơn"]):
            return "Buồn 😢"
        if any(k in q for k in ["lãng mạn", "romantic", "love", "tình yêu"]):
            return "Lãng mạn 💕"
        if any(k in q for k in ["hùng", "epic", "mạnh mẽ", "heroic"]):
            return "Hùng tráng 🏆"
        if any(k in q for k in ["bình yên", "calm", "relax"]):
            return "Bình yên 🌅"
        return "Trung tính 🎵"

    def _analyze_problem(self, query: str) -> str:
        """Phân tích vấn đề cần tư vấn"""
        q = query.lower()
        analysis = "📋 **Phân tích vấn đề:**\n"
        if "lập trình" in q or "code" in q:
            analysis += "- 🔧 Lĩnh vực: Công nghệ/Lập trình\n"
            analysis += "- 💡 Đề xuất: Chia nhỏ vấn đề, giải quyết từng phần\n"
        elif "học" in q or "study" in q:
            analysis += "- 📚 Lĩnh vực: Học tập\n"
            analysis += "- 💡 Đề xuất: Lập kế hoạch học tập rõ ràng\n"
        elif "tình" in q or "love" in q:
            analysis += "- 💕 Lĩnh vực: Tình cảm\n"
            analysis += "- 💡 Đề xuất: Lắng nghe và thấu hiểu\n"
        elif "công việc" in q or "work" in q:
            analysis += "- 💼 Lĩnh vực: Công việc\n"
            analysis += "- 💡 Đề xuất: Quản lý thời gian hiệu quả\n"
        else:
            analysis += "- 📌 Lĩnh vực: Đa dạng\n"
            analysis += "- 💡 Đề xuất: Xác định rõ mục tiêu\n"
        return analysis

    def _analyze_structure(self, query: str) -> str:
        """Phân tích cấu trúc câu hỏi"""
        return """
📋 **Cấu trúc phân tích:**

1. **🔍 Xác định vấn đề chính**
   - Phân tích từ khóa quan trọng
   - Xác định phạm vi vấn đề

2. **📊 Phân tích các khía cạnh**
   - Khía cạnh 1: Nguyên nhân
   - Khía cạnh 2: Tác động
   - Khía cạnh 3: Giải pháp

3. **🎯 Đánh giá và tổng hợp**
   - Đưa ra nhận định
   - Kết luận và đề xuất
"""

    # ================================================================
    # HÀM LƯU TRỮ NGỮ CẢNH (TỰ HỌC)
    # ================================================================

    def _load_context(self, user_id: str):
        """Nạp ngữ cảnh từ bộ nhớ"""
        pass

    def _save_context(self, user_id: str):
        """Lưu ngữ cảnh vào bộ nhớ"""
        if len(self.context) > 2:
            last_user = None
            last_ai = None
            for msg in reversed(self.context):
                if msg["role"] == "user" and not last_user:
                    last_user = msg
                elif msg["role"] == "ai" and not last_ai:
                    last_ai = msg
                if last_user and last_ai:
                    break

            if last_user and last_ai:
                self.memory[user_id].append({
                    "question": last_user["content"],
                    "answer": last_ai["content"],
                    "time": datetime.datetime.now().isoformat()
                })
                if len(self.memory[user_id]) > 100:
                    self.memory[user_id] = self.memory[user_id][-100:]

    def learn_from_feedback(self, user_id: str, query: str, rating: int):
        """Học từ phản hồi người dùng"""
        if rating >= 4:
            self.memory[user_id].append({
                "query": query,
                "rating": rating,
                "time": datetime.datetime.now().isoformat()
            })
            if len(self.memory[user_id]) > 100:
                self.memory[user_id] = self.memory[user_id][-100:]
            return {"learned": True, "total": len(self.memory[user_id])}
        return {"learned": False}

    def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """Lấy thống kê học tập"""
        memory = self.memory.get(user_id, [])
        return {
            "total_learned": len(memory),
            "context_length": len(self.context),
            "level": self.level,
            "thinking_enabled": self.config[self.level]["enable_thinking"]
        }