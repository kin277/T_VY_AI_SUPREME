# ====================================================================
# AI ENGINE CORE - SIÊU TRÍ TUỆ (T.VỸ AI SUPREME)
# ====================================================================
# Bản quyền: T.VỸ-VIP-FILE
# Phiên bản: 13.0.0 (Tự duy duy sinh Code thực tế & Khắc phục hoàn toàn Code mẫu)
# ====================================================================

import os
import re
import json
import random
import datetime
import mimetypes
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict

from .ethics_guard import EthicsGuard
from .claude_engine import ClaudeEngine
from config.levels import LEVEL_CONFIG


class FileClassifier:
    """Bộ kiểm định và phân loại File tự động trước khi gửi vào AI"""
    def __init__(self, max_size_mb: int = 15):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Danh sách whitelist mở rộng
        self.allowed_extensions = {
            # Văn bản & Tài liệu
            '.txt', '.pdf', '.docx', '.md', '.csv', '.json',
            # Hình ảnh
            '.png', '.jpg', '.jpeg', '.webp',
            # Mã nguồn
            '.py', '.js', '.ts', '.html', '.css', '.cpp', '.c', '.java'
        }
        
        # Danh sách đen bắt buộc chặn vì lý do bảo mật
        self.blacklisted_files = {'.env', '.gitignore', '.git', 'config.json', 'settings.py'}
        self.blacklisted_extensions = {'.exe', '.bat', '.sh', '.dll', '.so', '.bin', '.zip', '.rar', '.7z'}

    def classify_and_validate(self, file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Kiểm tra tính hợp lệ và phân loại file"""
        if not os.path.exists(file_path):
            return False, "FILE_NOT_FOUND", {"reason": "File không tồn tại trên hệ thống."}

        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # 1. Kiểm tra file hệ thống nhạy cảm hoặc đuôi thực thi nguy hiểm
        if filename in self.blacklisted_files or ext in self.blacklisted_extensions:
            return False, "FILE_REJECTED_SECURITY", {
                "reason": f"File '{filename}' bị từ chối do thuộc danh sách cấm bảo mật."
            }

        # 2. Kiểm tra Extension
        if ext not in self.allowed_extensions:
            return False, "FILE_REJECTED_UNSUPPORTED", {
                "reason": f"Định dạng file '{ext}' hiện chưa được hỗ trợ."
            }

        # 3. Kiểm tra Kích thước File
        file_size = os.path.getsize(file_path)
        if file_size > self.max_size_bytes:
            return False, "FILE_REJECTED_SIZE", {
                "reason": f"Kích thước file ({file_size / (1024*1024):.2f}MB) vượt quá giới hạn ({self.max_size_bytes / (1024*1024)}MB)."
            }

        # 4. Phân loại loại File
        mime_type, _ = mimetypes.guess_type(file_path)
        category = "DOCUMENT"
        if ext in {'.png', '.jpg', '.jpeg', '.webp'}:
            category = "IMAGE"
        elif ext in {'.py', '.js', '.ts', '.html', '.css', '.cpp', '.c', '.java'}:
            category = "CODE"

        return True, "FILE_ALLOWED", {
            "filename": filename,
            "extension": ext,
            "category": category,
            "mime_type": mime_type,
            "size_bytes": file_size
        }


class AIEngine:
    def __init__(self, level: str = "pro"):
        self.level = level
        self.context = []  # Lưu lịch sử chat
        self.memory = defaultdict(list)  # Lưu kiến thức đã học
        self.max_context = 20  # Số tin nhắn tối đa nhớ
        self.ethics = EthicsGuard()
        self.user_id = None
        self.thinking_steps = []  # Lưu các bước suy nghĩ
        self.claude_engine = ClaudeEngine()
        self.file_classifier = FileClassifier(max_size_mb=15)

        # Cấu hình theo cấp độ
        self.config = {
            "basic": {"max_tokens": 1500, "enable_thinking": False, "enable_context": False},
            "pro": {"max_tokens": 4000, "enable_thinking": True, "enable_context": True},
            "plus": {"max_tokens": 8000, "enable_thinking": True, "enable_context": True},
            "pro3": {"max_tokens": 16000, "enable_thinking": True, "enable_context": True}
        }

    def process_ai_request(self, user_message: str, level: str = 'pro', web_synthesis: bool = True) -> Dict[str, Any]:
        """Wrapper giúp tương thích với API Chat Routes"""
        self.level = level
        return self.process(query=user_message)

    def process(self, query: str, file_path: Optional[str] = None, user_id: str = None) -> Dict[str, Any]:
        """Xử lý câu hỏi kết hợp với kiểm tra file đính kèm và kiểm tra đạo đức"""
        self.user_id = user_id
        query = query.strip() if query else ""

        # 1. KIỂM TRA VÀ XỬ LÝ FILE ĐÍNH KÈM (NẾU CÓ)
        file_content_prompt = ""
        if file_path:
            is_allowed, status, file_info = self.file_classifier.classify_and_validate(file_path)
            if not is_allowed:
                return {
                    "type": "error",
                    "message": f"❌ **Tải file thất bại:** {file_info['reason']}"
                }

            if file_info["category"] in ["DOCUMENT", "CODE"]:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(10000)
                        file_content_prompt = f"\n\n[NỘI DUNG FILE ĐÍNH KÈM ({file_info['filename']})]:\n{content}"
                except Exception as e:
                    file_content_prompt = f"\n\n[Lỗi đọc nội dung file: {str(e)}]"
            elif file_info["category"] == "IMAGE":
                file_content_prompt = f"\n\n[NGƯỜI DÙNG ĐÃ TẢI LÊN MỘT HÌNH ẢNH: {file_info['filename']}]"

        if not query and file_path:
            query = "Hãy phân tích nội dung file đính kèm giúp tôi."

        if not query and not file_path:
            return {"error": "Câu hỏi hoặc file không được để trống"}

        # 2. KIỂM TRA ĐẠO ĐỨC
        ethics_check = self.ethics.validate(query)
        if not ethics_check["allowed"]:
            return {
                "type": "ethics_violation",
                "message": ethics_check["message"],
                "details": ethics_check["reason"]
            }

        # 3. NẠP NGỮ CẢNH TỪ LỊCH SỬ
        if user_id:
            self._load_context(user_id)

        # 4. LƯU VÀO LỊCH SỬ CHAT
        full_user_input = query + file_content_prompt
        self.context.append({"role": "user", "content": full_user_input, "time": datetime.datetime.now().isoformat()})
        if len(self.context) > self.max_context:
            self.context = self.context[-self.max_context:]

        # 5. SUY NGHĨ TỪNG BƯỚC (Chain of Thought)
        if self.config.get(self.level, {}).get("enable_thinking", True):
            self.thinking_steps = self._think(query)
        else:
            self.thinking_steps = []

        # 6. PHÂN LOẠI Ý ĐỊNH
        intent = self.classify_intent(query)

        # 7. XỬ LÝ THEO INTENT
        result = self._handle_by_intent(full_user_input, intent)

        # 8. LƯU NGỮ CẢNH
        if user_id:
            self._save_context(user_id)

        # 9. ĐÍNH KÈM SUY NGHĨ VÀ ARTIFACT CHECK
        if self.thinking_steps:
            result["thinking"] = self.thinking_steps

        # Tự động phát hiện Claude Artifact
        result["has_artifact"] = self._detect_artifacts(result.get("message", ""))

        return result

    def _think(self, query: str) -> List[str]:
        """Quá trình suy nghĩ từng bước thực tế (Chain of Thought)"""
        steps = []
        steps.append(f"🔍 Phân tích yêu cầu: '{query[:60]}...'")
        topics = self._detect_topics(query)
        if topics:
            steps.append(f"📚 Chủ đề nhận diện: {', '.join(topics[:3])}")
        complexity = self._assess_complexity(query)
        steps.append(f"📊 Độ phức tạp: {complexity}")
        steps.append(f"🧠 Kích hoạt trí tuệ nhân tạo suy nghĩ cấu trúc & thuật toán tối ưu...")
        steps.append(f"🚀 Đang tạo câu trả lời và mã nguồn hoàn chỉnh...")
        return steps

    def _detect_topics(self, query: str) -> List[str]:
        """Phát hiện chủ đề trong câu hỏi"""
        topics = []
        q = query.lower()

        topic_keywords = {
            "Lập trình & Thuật toán": ["code", "lập trình", "python", "javascript", "java", "c++", "html", "css", "web", "function", "class", "app", "game"],
            "Trí tuệ nhân tạo": ["ai", "machine learning", "deep learning", "neural", "chatgpt", "claude", "gemini"],
            "Âm nhạc": ["nhạc", "music", "bài hát", "giai điệu", "hợp âm", "sáng tác"],
            "Hình ảnh & Đồ họa": ["ảnh", "hình ảnh", "draw", "paint", "vẽ", "thiết kế", "design", "svg"],
            "Khoa học & Toán": ["vật lý", "hóa học", "sinh học", "thiên văn", "toán", "khoa học"],
            "Đời sống & Tư vấn": ["cuộc sống", "tình yêu", "gia đình", "bạn bè", "sức khỏe", "hạnh phúc"],
            "Kinh tế & Tài chính": ["kinh tế", "tài chính", "đầu tư", "chứng khoán", "tiền", "thị trường"]
        }

        for topic, keywords in topic_keywords.items():
            if any(k in q for k in keywords):
                topics.append(topic)

        return topics if topics else ["Tổng hợp"]

    def _get_learned_knowledge(self, query: str) -> bool:
        if not self.user_id:
            return False
        q = query.lower()
        for key in self.memory.get(self.user_id, []):
            if any(word in q for word in key.split()[:3]):
                return True
        return False

    def _assess_complexity(self, query: str) -> str:
        q = query.lower()
        complex_keywords = ["code", "lập trình", "tạo game", "viết app", "tại sao", "giải thích chi tiết", "phân tích", "so sánh", "thuật toán", "xây dựng hệ thống"]
        if any(k in q for k in complex_keywords) or len(q.split()) > 15:
            return "Cao (Cần AI tự suy nghĩ sâu & lập trình đầy đủ)"
        return "Trung bình"

    def classify_intent(self, query: str) -> str:
        q = query.lower()
        if any(k in q for k in ["code", "lập trình", "viết code", "function", "class", "def", "html", "css", "js", "python", "tạo game", "viết app"]):
            return "code"
        if any(k in q for k in ["ảnh", "hình ảnh", "draw", "paint", "vẽ", "design", "hình"]):
            return "image"
        if any(k in q for k in ["nhạc", "music", "bài hát", "giai điệu", "hợp âm"]):
            return "music"
        if any(k in q for k in ["tìm", "search", "google", "tra cứu", "thông tin"]):
            return "web_search"
        if any(k in q for k in ["tư vấn", "hướng dẫn", "cách", "làm thế nào"]):
            return "advice"
        if any(k in q for k in ["tại sao", "giải thích", "phân tích", "so sánh"]):
            return "analysis"
        if any(k in q for k in ["dịch", "translate", "ngôn ngữ"]):
            return "translate"
        return "general"

    def _handle_by_intent(self, query: str, intent: str) -> Dict[str, Any]:
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
    # CÁC HÀM XỬ LÝ DÙNG TRÍ TUỆ NHÂN TẠO THỰC TẾ (KHÔNG CÓ TEMPLATE)
    # ================================================================

    def handle_general(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(query)
        return {"type": "chat", "message": response, "intent": "general"}

    def handle_code(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(query)
        return {"type": "code", "message": response, "intent": "code"}

    def handle_image(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(f"Yêu cầu xử lý/mô tả hoặc tạo mã SVG/Canvas cho hình ảnh: {query}")
        return {"type": "image", "message": response, "intent": "image"}

    def handle_music(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(f"Yêu cầu sáng tác lời bài hát, hợp âm hoặc đoạn mã âm thanh Web Audio API: {query}")
        return {"type": "music", "message": response, "intent": "music"}

    def handle_web_search(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(query)
        return {"type": "web_search", "message": response, "intent": "web_search"}

    def handle_advice(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(query)
        return {"type": "advice", "message": response, "intent": "advice"}

    def handle_analysis(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(query)
        return {"type": "analysis", "message": response, "intent": "analysis"}

    def handle_creative(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(query)
        return {"type": "creative", "message": response, "intent": "creative"}

    def handle_translate(self, query: str) -> Dict[str, Any]:
        response = self._generate_intelligent_response(query)
        return {"type": "translate", "message": response, "intent": "translate"}

    # ================================================================
    # CÁC HÀM TRUYỀN PROMPT ÉP AI PHẢI TỰ SUY NGHĨ VÀ VIẾT CODE ĐẦY ĐỦ
    # ================================================================

    def _get_context_summary(self) -> str:
        """Tóm tắt ngữ cảnh cuộc trò chuyện"""
        if not self.context or not self.config.get(self.level, {}).get("enable_context", True):
            return ""

        recent = self.context[-5:]
        summary = "📜 **LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY:**\n"
        for msg in recent:
            role = "👤 Người dùng" if msg["role"] == "user" else "🤖 AI"
            summary += f"{role}: {msg['content'][:150]}\n"
        return summary

    def _generate_intelligent_response(self, query: str) -> str:
        """Sinh câu trả lời thông qua AI Engine với System Instruction ép AI tự lập trình 100%"""
        context_text = self._get_context_summary()
        
        # PROMPT ÉP AI KHÔNG ĐƯỢC DÙNG CODE MẪU, PHẢI TỰ SUY NGHĨ VÀ VIẾT ĐẦY ĐỦ
        system_instruction = (
            "Bạn là T.VỸ AI SUPREME - Trí tuệ Nhân tạo Chuyên gia Lập trình & Giải quyết Vấn đề Cao cấp.\n\n"
            "QUY TẮC PHẢN HỒI BẮT BỘC (TUÂN THỦ 100%):\n"
            "1. TỰ SUY NGHĨ & LẬP TRÌNH: Khi nhận yêu cầu viết code hay giải quyết bài toán, bạn phải dùng trí tuệ để TỰ THIẾT KẾ THUẬT TOÁN VÀ VIẾT MÃ NGUỒN MỚI HOÀN TOÀN phù hợp chính xác nhất với prompt của người dùng.\n"
            "2. KHÔNG DÙNG CODE MẪU CỐ ĐỊNH: Tuyệt đối KHÔNG sử dụng các đoạn mã mẫu ngắn dựng sẵn hoặc dữ liệu giả lập.\n"
            "3. VIẾT CODE HOÀN CHỈNH: Viết code ĐẦY ĐỦ từ đầu đến cuối bất kể dài bao nhiêu lines. TUYỆT ĐỐI KHÔNG cắt xén code (CẤM dùng các dấu như '...', '// code tiếp ở đây', '// TODO: tự viết tiếp').\n"
            "4. CLAUDE ARTIFACT PREVIEW: Nếu người dùng yêu cầu làm Web, Game, UI, giao diện HTML/CSS/JS, hãy gom toàn bộ HTML, CSS (trong thẻ <style>) và JavaScript (trong thẻ <script>) vào duy nhất MỘT khối ```html ... ``` để tính năng Xem Trước Trực Tiếp (Live Preview) khởi chạy thành công.\n"
            "5. ĐA NGÔN NGỮ & PHÂN TÍCH MẠCH LẠC: Trả lời rõ ràng, đi thẳng vào vấn đề bằng ngôn ngữ của người dùng."
        )

        full_prompt = system_instruction
        if context_text:
            full_prompt += f"\n\n{context_text}"
        full_prompt += f"\n\nYÊU CẦU CHI TIẾT CỦA NGƯỜI DÙNG:\n{query}"

        # Gọi Claude Engine để kết nối API AI thực tế
        claude_result = self.claude_engine.process(full_prompt)
        
        if isinstance(claude_result, dict):
            if "error" in claude_result:
                ai_text = f"⚠️ Lỗi kết nối AI Engine: {claude_result['error']}"
            else:
                ai_text = claude_result.get("response", "Không nhận được phản hồi từ AI.")
        else:
            ai_text = str(claude_result)

        return ai_text

    def _detect_artifacts(self, text: str) -> bool:
        """Tự động phát hiện mã HTML/SVG/XML để bật Claude Artifact Live Preview"""
        pattern = r"```(html|svg|xml)[\s\S]*?```"
        return bool(re.search(pattern, text, re.IGNORECASE))

    # ================================================================
    # HÀM LƯU TRỮ NGỮ CẢNH (TỰ HỌC)
    # ================================================================

    def _load_context(self, user_id: str):
        pass

    def _save_context(self, user_id: str):
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
        memory = self.memory.get(user_id, [])
        return {
            "total_learned": len(memory),
            "context_length": len(self.context),
            "level": self.level,
            "thinking_enabled": self.config.get(self.level, {}).get("enable_thinking", True)
        }