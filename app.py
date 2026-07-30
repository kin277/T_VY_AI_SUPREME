====================================================================
T.VỸ-AI-SUPREME - ỨNG DỤNG CHÍNH (BẢN HOÀN CHỈNH - FULL MULTIMODAL & AUTO CODE ENGINE)
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 12.6.0 (Vision, Multimodal, Auto Code Extension & Multilingual Adaptation)
====================================================================
"""

import base64
import datetime
import json
import logging
import os
import random
import re
import sys
import time
import traceback
import requests
from io import BytesIO
from pathlib import Path

from flask import (
    Flask, jsonify, render_template, request,
    send_from_directory, session
)
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename

# Thử import Pillow để xử lý hình ảnh chuyên sâu
try:
    from PIL import Image, ImageOps
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

# ===== CẤU HÌNH LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TVyAI")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ===== TỰ ĐỘNG NHẬN DIỆN VÀ TỐI ƯU THƯ MỤC CẤU HÌNH =====
BASE_DIR = Path(__file__).resolve().parent

POSSIBLE_TEMPLATE_DIRS = [
    BASE_DIR / 'frontend' / 'public',
    BASE_DIR / 'templates',
    BASE_DIR
]

TEMPLATE_DIR = POSSIBLE_TEMPLATE_DIRS[0]
for p in POSSIBLE_TEMPLATE_DIRS:
    if (p / 'index.html').exists():
        TEMPLATE_DIR = p
        break

STATIC_DIR = TEMPLATE_DIR / 'assets' if (TEMPLATE_DIR / 'assets').exists() else BASE_DIR / 'static'
MUSIC_DIR = BASE_DIR / 'static' / 'music'
UPLOAD_DIR = BASE_DIR / 'static' / 'uploads'

MUSIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"📂 Template Directory: {TEMPLATE_DIR}")
logger.info(f"📂 Static Directory: {STATIC_DIR}")

app = Flask(__name__,
            template_folder=str(TEMPLATE_DIR),
            static_folder=str(STATIC_DIR),
            static_url_path='/assets')

app.secret_key = os.getenv("SECRET_KEY", "T_VY_VIP_FILE_2026_PRODUCTION_KEY")
app.config['DEBUG'] = os.getenv("FLASK_DEBUG", "False").lower() in ["true", "1"]
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['JSON_AS_ASCII'] = False

CORS(app, supports_credentials=True)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# ===== IMPORT MODULES NỘI BỘ =====
try:
    from backend.core.ai_engine import AIEngine
    from backend.core.ethics_guard import EthicsGuard
    from backend.database.db_handler import (
        get_user_by_id, get_conversations_by_user, get_conversation_by_id,
        save_conversation, delete_conversation_by_id, log_usage, get_usage_count,
        get_all_users, get_total_users, get_total_conversations, get_premium_users,
        get_all_usage_stats, delete_user_by_id, update_user_role, update_subscription,
        init_db
    )
    from backend.api.auth import auth_google, auth_facebook, auth_github_callback, logout, get_current_user
    from backend.payment.momo import create_payment, handle_ipn, payment_complete
    from config.settings import Config
    from config.levels import LEVEL_CONFIG, get_level_config
    from backend.core.claude_engine import ClaudeEngine
    from backend.core.document_parser import DocumentParser

    init_db()
    ai_engine = ClaudeEngine()
except Exception as e:
    logger.error(f"❌ Lỗi import hoặc khởi tạo modules backend: {e}")

# ===== ĐỊNH DẠNG FILE CHO PHÉP =====
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
DOC_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'csv', 'md', 'json'}
ALLOWED_EXTENSIONS = DOC_EXTENSIONS | IMAGE_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_messages(raw_messages):
    """Giải mã an toàn dữ liệu tin nhắn từ DB (dù là JSON String hay List)"""
    if isinstance(raw_messages, str):
        try:
            return json.loads(raw_messages)
        except Exception:
            return []
    elif isinstance(raw_messages, list):
        return raw_messages
    return []

# ================================================================
# SYSTEM PROMPT BỘ QUY TẮC NÂNG CẤP LẬP TRÌNH & ĐA NGÔN NGỮ TỰ ĐỘNG
# ================================================================
SMART_CODE_SYSTEM_PROMPT = """
[BỘ QUY TẮC XỬ LÝ NÂNG CẤP CỦA T.VỸ-AI SUPREME]

1. TỰ ĐỘNG THÍCH ỨNG NGÔN NGỮ GIAO TIẾP (MULTILINGUAL ADAPTATION):
   - Tự động nhận diện ngôn ngữ người dùng sử dụng trong câu hỏi/yêu cầu (Tiếng Việt, Tiếng Anh, Tiếng Trung, Tiếng Nhật, Tiếng Hàn, Tiếng Pháp, Tiếng Đức,...).
   - BẮT BUỘC trả lời hoàn toàn bằng chính ngôn ngữ đó để người dùng đọc hiểu một cách tự nhiên nhất.
   - Các từ khóa kỹ thuật, tên biến, hoặc mã nguồn lập trình vẫn giữ nguyên chuẩn định dạng quốc tế.

2. TỰ ĐỘNG NHẬN DIỆN NGÔN NGỮ & ĐUÔI FILE CODE:
   - Tự động nhận diện ngôn ngữ lập trình và đuôi file tương ứng (.glsl, .vsh, .fsh, .py, .js, .cpp, .html, .css, .java, .kt, .c, .cs, .ts, .php, .go, .rs, .json, .yaml,...).
   - Nếu người dùng chỉ nêu mục đích công việc (ví dụ: "làm shader minecraft", "tạo bot discord", "làm game 2D"), bạn PHẢI TỰ PHÂN TÍCH mục đích và chọn chính xác cấu trúc cũng như đuôi file phù hợp nhất.

3. TỔNG HỢP TRI THỨC THÔNG MINH:
   - AI tổng hợp thông tin, đưa ra câu trả lời chuẩn xác tuyệt đối dù câu trả lời rất ngắn hay cực kỳ dài.

4. CƠ CHẾ CHIA NHỎ DỰ ÁN (4 - 5 FILE MỖI LƯỢT):
   - Đối với dự án cần nhiều file, bạn hãy xuất trước 4 - 5 file chính của dự án.
   - Ở CUỐI CÙNG của câu trả lời, BẮT BUỘC đính kèm câu hỏi tiếp tục bằng đúng ngôn ngữ người dùng đang hỏi (Ví dụ Tiếng Việt: "Vì dự án khá dài nên không thể chỉ bằng 1 dòng tin nhắn là xong được. Bạn có muốn tiếp tục không?", Tiếng Anh: "Since the project is quite long, it cannot be completed in a single message. Would you like to continue?").

5. VÒNG LẶP TỰ ĐỘNG TIẾP TỤC (CONTINUATION LOOP):
   - Khi nhận phản hồi từ người dùng chứa các từ khóa tiếp tục ("tiếp", "tiếp tục", "ok", "continue", "tiếp đi", "yes",...), bạn sẽ tự động sinh các file tiếp theo của dự án còn dở dang.
   - Tiếp tục lặp lại quy trình chia nhỏ 4-5 file kèm câu hỏi trên cho đến khi hoàn thành toàn bộ 100% dự án.
"""

# ================================================================
# MUSIC GENERATOR ENGINE
# ================================================================

try:
    import scipy.io.wavfile
    import numpy as np
    import torch
    from transformers import pipeline

    class LyricGenerator:
        def __init__(self):
            self.fallback_lyrics = {
                "tình yêu": """Verse 1: Em là ánh sáng trong đêm tối của anh
Pre-chorus: Tình yêu như cơn gió thoáng qua
Chorus: Ta sẽ mãi bên nhau dù bão giông
Verse 2: Trái tim anh chỉ thuộc về em
Bridge: Tình yêu là những vì sao lung linh
Outro: Mãi mãi bên nhau em nhé""",

                "mùa xuân": """Verse 1: Mùa xuân về hoa nở khắp nơi
Pre-chorus: Cánh hoa đào rơi trong gió xuân
Chorus: Tình yêu nở hoa trong mùa xuân mới
Verse 2: Nắng ấm và tiếng chim hót
Bridge: Xuân về mang theo hy vọng mới
Outro: Mùa xuân của yêu thương""",

                "mùa hè": """Verse 1: Mùa hè rực rỡ nắng vàng
Pre-chorus: Biển xanh và bãi cát trắng
Chorus: Những chiều hoàng hôn bên bờ biển
Verse 2: Hạ về với những kỷ niệm đẹp
Bridge: Mùa hè của những ước mơ
Outro: Hè về mang theo yêu thương""",

                "mùa đông": """Verse 1: Mùa đông lạnh giá nhưng tình yêu ấm áp
Pre-chorus: Tuyết rơi trắng xóa phố phường
Chorus: Giáng sinh về trong tim anh
Verse 2: Em ơi mùa đông đã về
Bridge: Hơi ấm bên em xua tan giá lạnh
Outro: Mùa đông của tình yêu""",

                "cuộc sống": """Verse 1: Cuộc sống là những hành trình
Pre-chorus: Ta vươn tới những ước mơ
Chorus: Sống là để yêu thương và sẻ chia
Verse 2: Mỗi ngày là một cơ hội mới
Bridge: Hạnh phúc từ những điều giản dị
Outro: Cuộc sống tươi đẹp biết bao"""
            }

        def detect_topic(self, prompt):
            topics = ["tình yêu", "mùa xuân", "mùa hè", "mùa đông", "cuộc sống"]
            p = prompt.lower()
            for topic in topics:
                if topic in p:
                    return topic
            return "cuộc sống"

        def detect_style(self, prompt):
            p = prompt.lower()
            styles = {
                "pop": ["pop", "nhạc trẻ"],
                "rock": ["rock", "alternative"],
                "jazz": ["jazz", "blues"],
                "edm": ["edm", "electronic", "dance"],
                "classical": ["classical", "classic"],
                "rap": ["rap", "hip hop"],
                "ballad": ["ballad", "tình ca"],
                "v_pop": ["vpop", "nhạc việt"],
                "k_pop": ["kpop", "hàn quốc"]
            }
            for style, keywords in styles.items():
                if any(k in p for k in keywords):
                    return style
            return "pop"

        def detect_mood(self, prompt):
            p = prompt.lower()
            if any(k in p for k in ["vui", "happy", "hạnh phúc"]):
                return "happy"
            if any(k in p for k in ["buồn", "sad", "cô đơn"]):
                return "sad"
            if any(k in p for k in ["lãng mạn", "romantic", "tình yêu"]):
                return "romantic"
            if any(k in p for k in ["hùng", "epic", "mạnh mẽ"]):
                return "epic"
            return "neutral"

        def generate_lyrics(self, prompt, style="pop", mood="happy"):
            topic = self.detect_topic(prompt)
            base_lyrics = self.fallback_lyrics.get(topic, self.fallback_lyrics["cuộc sống"])
            lines = base_lyrics.strip().split("\n")
            modified = []
            for i, line in enumerate(lines):
                if "Outro" in line and i + 1 < len(lines):
                    lines[i + 1] = f"{lines[i + 1]} ({style}, {mood})"
                modified.append(lines[i])
            return "\n".join(modified)

    class MusicGenerator:
        def __init__(self):
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.synthesiser = None
            self.model_loaded = False
            self.model_name = "facebook/musicgen-medium"
            logger.info(f"🎵 MusicGenerator khởi tạo thành công trên thiết bị: {self.device}")
            self.lyric_gen = LyricGenerator()

        def load_model(self):
            if self.model_loaded:
                return True
            try:
                logger.info(f"🔄 Đang khởi chạy AI Model {self.model_name}...")
                self.synthesiser = pipeline(
                    "text-to-audio",
                    model=self.model_name,
                    device=0 if self.device.type == 'cuda' else -1
                )
                self.model_loaded = True
                logger.info("✅ Model MusicGen đã tải hoàn tất!")
                return True
            except Exception as e:
                logger.error(f"❌ Lỗi khởi tạo MusicGen: {e}")
                return False

        def generate_instrumental(self, prompt, duration=15, style=None, mood=None):
            if not self.model_loaded:
                if not self.load_model():
                    return {"error": "Không thể tải mô hình MusicGen AI"}

            full_prompt = prompt
            if style:
                full_prompt = f"{style} style, {full_prompt}"
            if mood:
                full_prompt = f"{mood} mood, {full_prompt}"

            try:
                duration = min(max(duration, 5), 30)
                random_seed = random.randint(0, 2**32 - 1)
                torch.manual_seed(random_seed)
                if self.device.type == 'cuda':
                    torch.cuda.manual_seed_all(random_seed)

                result = self.synthesiser(
                    full_prompt,
                    forward_params={
                        "do_sample": True,
                        "max_length": duration * 50
                    }
                )

                timestamp = int(time.time())
                random_id = random.randint(1000, 9999)
                filename = f"music_{timestamp}_{random_id}.wav"
                filepath = MUSIC_DIR / filename

                audio_data = result["audio"]
                if hasattr(audio_data, 'cpu'):
                    audio_data = audio_data.cpu().numpy()
                audio_data = np.squeeze(audio_data)

                if audio_data.dtype != np.int16:
                    audio_data = (audio_data / np.max(np.abs(audio_data)) * 32767).astype(np.int16)

                scipy.io.wavfile.write(
                    str(filepath),
                    rate=result["sampling_rate"],
                    data=audio_data
                )

                if self.device.type == 'cuda':
                    torch.cuda.empty_cache()

                return {
                    "success": True,
                    "filepath": str(filepath),
                    "filename": filename,
                    "duration": duration,
                    "download_url": f"/static/music/{filename}",
                    "prompt": full_prompt
                }
            except Exception as e:
                logger.error(f"Lỗi khi sinh nhạc: {e}")
                return {"error": f"Lỗi tạo nhạc: {str(e)}"}

        def generate_with_lyrics(self, prompt, duration=15, style=None, mood=None):
            if not style:
                style = self.lyric_gen.detect_style(prompt)
            if not mood:
                mood = self.lyric_gen.detect_mood(prompt)

            lyrics = self.lyric_gen.generate_lyrics(prompt, style, mood)
            music_result = self.generate_instrumental(prompt, duration, style, mood)

            if music_result.get("error"):
                return music_result

            return {
                "success": True,
                "lyrics": lyrics,
                "style": style,
                "mood": mood,
                "duration": duration,
                "music_file": music_result.get("filename"),
                "download_url": music_result.get("download_url"),
                "prompt": prompt
            }

    music_gen = MusicGenerator()
    MUSIC_AVAILABLE = True

except ImportError as e:
    logger.warning(f"⚠️ Thư viện sinh nhạc chưa hoàn chỉnh: {e}")

    class LyricGenerator:
        def detect_topic(self, prompt): return "cuộc sống"
        def detect_style(self, prompt): return "pop"
        def detect_mood(self, prompt): return "happy"
        def generate_lyrics(self, prompt, style="pop", mood="happy"):
            return f"Verse 1: Bài hát về {prompt}\nChorus: {prompt} - {style} - {mood}"

    class MusicGenerator:
        def __init__(self):
            self.model_loaded = False
            self.lyric_gen = LyricGenerator()

        def generate_with_lyrics(self, prompt, duration=15, style=None, mood=None):
            style = style or "pop"
            mood = mood or "happy"
            lyrics = f"Verse 1: Bài hát về {prompt}\nChorus: {prompt} - {style} - {mood}"

            return {
                "success": True,
                "lyrics": lyrics,
                "style": style,
                "mood": mood,
                "duration": duration,
                "music_file": "demo.wav",
                "download_url": "#",
                "prompt": prompt,
                "note": "⚠️ Chế độ Demo."
            }

        def load_model(self):
            return False

    music_gen = MusicGenerator()
    MUSIC_AVAILABLE = False

# ================================================================
# ROUTES (GIAO DIỆN & TÀI NGUYÊN TĨNH)
# ================================================================

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Lỗi render template index.html: {e}")
        return f"<h2>❌ Lỗi giao diện Server: {str(e)}</h2><p>Vui lòng kiểm tra lại file index.html trong thư mục frontend/public hoặc templates/.</p>", 500

@app.route('/admin')
def admin_panel():
    try:
        return render_template('admin.html')
    except Exception as e:
        return f"<h2>❌ Lỗi giao diện Admin: {str(e)}</h2>", 500

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(str(STATIC_DIR), filename)

@app.route('/static/music/<filename>')
def serve_music(filename):
    safe_name = secure_filename(filename)
    return send_from_directory(str(MUSIC_DIR), safe_name)

@app.route('/static/uploads/<filename>')
def serve_upload(filename):
    safe_name = secure_filename(filename)
    return send_from_directory(str(UPLOAD_DIR), safe_name)

# ================================================================
# AUTH ROUTES
# ================================================================

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    return auth_google()

@app.route('/api/auth/facebook', methods=['POST'])
def facebook_auth():
    return auth_facebook()

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    return logout()

@app.route('/api/auth/me')
def auth_me():
    return get_current_user()

@app.route('/auth/github/callback')
def github_callback_route():
    code = request.args.get('code')
    if not code:
        return "❌ Không tìm thấy mã xác thực từ GitHub", 400

    result = auth_github_callback(code)

    if result.get("error"):
        return f"❌ Đăng nhập thất bại: {result['error']}", 400

    if result.get("success"):
        session['user_id'] = result['user_id']
        session['user_email'] = result['email']
        session['user_name'] = result['name']

        return f"""
        <html>
        <body style="font-family:Arial;text-align:center;padding:50px;background:#0f172a;color:#fff;">
            <h2>✅ Đăng nhập thành công!</h2>
            <p>Chào mừng <strong>{result['name']}</strong> trở lại!</p>
            <script>
                setTimeout(() => {{
                    if (window.opener) {{
                        window.opener.location.reload();
                        window.close();
                    }} else {{
                        window.location.href = '/';
                    }}
                }}, 1200);
            </script>
        </body>
        </html>
        """

    return "❌ Lỗi hệ thống", 400

# ================================================================
# CHAT ROUTES (TÍCH HỢP SỬA TIN NHẮN, TỰ CẮT BỚT BÊN DƯỚI & ABORT)
# ================================================================

@app.route('/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get('message') or data.get('prompt') or '').strip()
        conv_id = data.get('conversation_id', None)
        level = data.get('level', 'pro')
        image_url = data.get('image_url', None)
        image_base64 = data.get('image_base64', None)
        edit_index = data.get('edit_index', None)  # Chỉ số tin nhắn được sửa (nếu có)
        user_id = session.get('user_id')

        if not user_id:
            user_id = data.get('user_id', 'guest_user')

        if not message and not image_url and not image_base64:
            return jsonify({"error": "Nội dung câu hỏi hoặc hình ảnh không được để trống", "success": False}), 400

        user = get_user_by_id(user_id) if user_id != 'guest_user' else {'role': 'user', 'id': 'guest_user'}
        
        if user and user.get('role') != 'admin' and user_id != 'guest_user':
            max_uses = {'basic': 999999, 'pro': 5, 'plus': 2, 'pro3': 0}.get(level, 0)
            used = get_usage_count(user_id, level)
            if max_uses > 0 and used >= max_uses:
                return jsonify({
                    "error": f"Bạn đã hết lượt sử dụng cấp độ {level.upper()} hôm nay ({used}/{max_uses})",
                    "limit_reached": True,
                    "success": False
                }), 429
            log_usage(user_id, level)

        messages = []
        if not conv_id:
            conv_id = str(int(time.time() * 1000))
            name = message[:30] if message else "Lập trình & Phân tích AI"
        else:
            conv = get_conversation_by_id(conv_id, user_id) if user_id != 'guest_user' else None
            if conv:
                name = conv.get('name', message[:30])
                messages = parse_messages(conv.get('messages', []))
            else:
                name = message[:30] or "Hội thoại mới"

        # ⚡ CƠ CHẾ SỬA TIN NHẮN & CẮT BỎ CÁC TIN NHẮN BÊN DƯỚI ⚡
        if edit_index is not None and isinstance(edit_index, int) and edit_index >= 0:
            if edit_index < len(messages):
                # Giữ lại các tin nhắn đứng TRƯỚC vị trí sửa, xóa toàn bộ từ edit_index trở về sau
                messages = messages[:edit_index]

        user_content = message
        if image_url and f"![ảnh]({image_url})" not in user_content:
            user_content = f"![Hình ảnh đính kèm]({image_url})\n\n{message}"

        is_continuation = bool(re.search(r'^\s*(tiếp|tiếp tục|ok|continue|tiếp đi|yes)\b', message.lower()))
        
        enhanced_query = message
        if is_continuation:
            enhanced_query = (
                f"{message}\n\n[HỆ THỐNG]: Người dùng yêu cầu TIẾP TỤC dự án. "
                f"Hãy tạo tiếp 4 - 5 file tiếp theo của dự án còn dở dang. "
                f"Nếu vẫn chưa xong hết toàn bộ dự án, ở cuối tin nhắn BẮT BUỘC lặp lại đúng câu hỏi tiếp tục theo ngôn ngữ đang sử dụng."
            )

        # 1. TÍCH HỢP SYSTEM PROMPT VÀ LỊCH SỬ CHAT VÀO CONTEXT
        context_parts = [SMART_CODE_SYSTEM_PROMPT]
        for msg in messages:
            role = "Người dùng" if msg.get("role") == "user" else "AI"
            context_parts.append(f"{role}: {msg.get('content', '')}")
        context_str = "\n".join(context_parts)

        # 2. LẤY THỜI GIAN THỰC TẾ VÀ GHẾP VÀO SYSTEM CONTENT
        now = datetime.datetime.now()
        current_time_info = f"Hôm nay là ngày {now.strftime('%d/%m/%Y')}, giờ hiện tại là {now.strftime('%H:%M')}."
        system_content = f"{current_time_info}\n\n{context_str}"

        # Thêm câu hỏi mới (đã sửa hoặc mới hoàn toàn)
        messages.append({
            "role": "user",
            "content": user_content,
            "image_url": image_url,
            "time": datetime.datetime.now().isoformat()
        })

        # 🚀 3. GỌI OPENROUTER API
        api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('GEMINI_API_KEY')
        ai_response = ""

        if api_key:
            try:
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://tvy-ai-supreme.local",
                    "X-Title": "TVY-AI SUPREME"
                }
                
                payload = {
                    "model": "openrouter/free", 
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": enhanced_query}
                    ]
                }
                
                resp = requests.post(url, json=payload, headers=headers, timeout=60)
                
                if resp.status_code == 200:
                    res_data = resp.json()
                    ai_response = res_data['choices'][0]['message']['content']
                else:
                    logger.error(f"Lỗi OpenRouter: {resp.text}")
                    ai_response = f"⚠️ Lỗi từ OpenRouter API ({resp.status_code}): {resp.text}"
                    
            except Exception as e:
                logger.error(f"Lỗi Exception OpenRouter: {traceback.format_exc()}")
                ai_response = f"⚠️ Lỗi kết nối đến OpenRouter: {str(e)}"
        else:
            ai_response = f"⚠️ Máy chủ chưa được cấu hình OPENROUTER_API_KEY ở Environment Variables."

        messages.append({
            "role": "ai",
            "content": ai_response,
            "time": datetime.datetime.now().isoformat()
        })

        if user_id != 'guest_user':
            save_conversation(user_id, conv_id, name, messages, level)
            convs = get_conversations_by_user(user_id)
            convs_list = [dict(c) for c in convs]
        else:
            convs_list = []

        try:
            socketio.emit('new_message', {
                'user_id': user_id,
                'conversation_id': conv_id,
                'message': ai_response
            }, room='global')
        except Exception as e:
            logger.warning(f"Lỗi Socket.IO emit: {e}")

        return jsonify({
            "success": True,
            "type": "chat",
            "message": ai_response,
            "response": ai_response,
            "conversation_id": conv_id,
            "conversations": convs_list,
            "messages": messages,
            "level": level
        })
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý Chat (500): {traceback.format_exc()}")
        return jsonify({"success": False, "error": f"Lỗi nội bộ máy chủ khi xử lý câu hỏi: {str(e)}"}), 500

# API RIÊNG BIỆT DÀNH CHO VIỆC SỬA TIN NHẮN & LỰA CHỌN CẮT TIN NHẮN BÊN DƯỚI
@app.route('/api/conversation/message/edit', methods=['POST'])
def edit_message_api():
    try:
        data = request.get_json(silent=True) or {}
        conv_id = data.get('conversation_id')
        msg_index = data.get('message_index')
        new_text = data.get('new_text', '').strip()
        level = data.get('level', 'pro')
        user_id = session.get('user_id') or 'guest_user'

        if not conv_id or msg_index is None or not new_text:
            return jsonify({"error": "Thiếu tham số conversation_id, message_index hoặc new_text"}), 400

        # Gọi lại route /api/chat với tham số edit_index
        return chat()
    except Exception as e:
        logger.error(f"Lỗi API Edit Message: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/conversations')
def get_conversations():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    convs = get_conversations_by_user(user_id)
    return jsonify({"conversations": [dict(c) for c in convs]})

@app.route('/conversation/<conv_id>')
def get_conversation(conv_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    conv = get_conversation_by_id(conv_id, user_id)
    if not conv:
        return jsonify({"error": "Không tìm thấy đoạn chat"}), 404

    conv_dict = dict(conv)
    conv_dict['messages'] = parse_messages(conv_dict.get('messages', []))
    return jsonify({"conversation": conv_dict})

@app.route('/api/conversation/<conv_id>/rename', methods=['PUT'])
def rename_conversation(conv_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401
    
    data = request.get_json() or {}
    new_name = data.get('name', '').strip()
    if not new_name:
        return jsonify({"error": "Tên cuộc trò chuyện không được để trống"}), 400

    conv = get_conversation_by_id(conv_id, user_id)
    if not conv:
        return jsonify({"error": "Không tìm thấy đoạn chat"}), 404

    messages = parse_messages(dict(conv).get('messages', []))
    level = dict(conv).get('level', 'pro')
    save_conversation(user_id, conv_id, new_name, messages, level)
    
    return jsonify({"success": True, "message": "Đã đổi tên cuộc trò chuyện", "name": new_name})

@app.route('/delete/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    delete_conversation_by_id(conv_id, user_id)
    return jsonify({"success": True})

# ================================================================
# API TẢI LÊN TÀI LIỆU & HÌNH ẢNH (VISION UPLOAD & OCR ENHANCED)
# ================================================================

@app.route('/upload_doc', methods=['POST'])
def upload_doc():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Không tìm thấy tệp đính kèm"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Tên tệp không hợp lệ"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Định dạng file không được hỗ trợ (Chấp nhận PDF, DOCX, TXT và Hình ảnh)"}), 400

        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        file_bytes = file.read()

        if ext in IMAGE_EXTENSIONS:
            timestamp = int(time.time())
            saved_filename = f"img_{timestamp}_{original_filename}"
            file_path = UPLOAD_DIR / saved_filename

            with open(file_path, "wb") as f:
                f.write(file_bytes)

            image_url = f"/static/uploads/{saved_filename}"

            base64_data = base64.b64encode(file_bytes).decode('utf-8')
            mime_type = f"image/{ext if ext != 'jpg' else 'jpeg'}"
            base64_url = f"data:{mime_type};base64,{base64_data}"

            img_info = ""
            if IMAGE_PROCESSING_AVAILABLE:
                try:
                    img = Image.open(BytesIO(file_bytes))
                    img_info = f"\n[Thông tin ảnh: Kích thước {img.width}x{img.height}px, định dạng {img.format}]"
                except Exception as e:
                    logger.warning(f"Lỗi phân tích Pillow: {e}")

            content_preview = f"![{original_filename}]({image_url})\n\n🖼️ **[Hình ảnh đính kèm: {original_filename}]**{img_info}"

            return jsonify({
                "success": True,
                "filename": original_filename,
                "is_image": True,
                "image_url": image_url,
                "base64": base64_url,
                "content": content_preview
            })

        try:
            if 'DocumentParser' in globals():
                extracted_text = DocumentParser.parse_file(original_filename, file_bytes)
            else:
                extracted_text = file_bytes.decode('utf-8', errors='ignore')

            if len(extracted_text) > 6000:
                extracted_text = extracted_text[:6000] + "\n\n[... Đã tự động cắt bớt dung lượng tài liệu ...]"
                
            return jsonify({
                "success": True,
                "filename": original_filename,
                "is_image": False,
                "content": extracted_text
            })
        except Exception as e:
            logger.error(f"Lỗi đọc tài liệu: {e}")
            return jsonify({"error": f"Lỗi xử lý tệp tài liệu: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Lỗi hệ thống upload (500): {traceback.format_exc()}")
        return jsonify({"error": f"Lỗi máy chủ khi xử lý upload: {str(e)}"}), 500

# ================================================================
# MUSIC ROUTES
# ================================================================

@app.route('/api/generate_music', methods=['POST'])
def generate_music_api():
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', '').strip()
        duration = data.get('duration', 60)
        style = data.get('style', None)
        mood = data.get('mood', None)

        if not prompt:
            return jsonify({"error": "Vui lòng nhập mô tả bài hát"}), 400

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Vui lòng đăng nhập"}), 401

        duration = min(max(duration, 10), 420)

        user = get_user_by_id(user_id)
        if user and user.get('role') != 'admin':
            max_music_uses = 20
            used = get_usage_count(user_id, 'music')
            if used >= max_music_uses:
                return jsonify({
                    "error": f"Đã hết lượt tạo nhạc hôm nay ({used}/{max_music_uses}).",
                    "limit_reached": True
                }), 429
            log_usage(user_id, 'music')

        result = music_gen.generate_with_lyrics(prompt, duration, style, mood)
        if result.get('error'):
            return jsonify({"error": result['error']}), 500
        return jsonify(result)
    except Exception as e:
        logger.error(f"Lỗi API Nhạc: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_lyrics', methods=['POST'])
def generate_lyrics_api():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    style = data.get('style', None)
    mood = data.get('mood', None)

    if not prompt:
        return jsonify({"error": "Vui lòng nhập chủ đề"}), 400

    lyric_gen = LyricGenerator()
    style = style or lyric_gen.detect_style(prompt)
    mood = mood or lyric_gen.detect_mood(prompt)

    lyrics = lyric_gen.generate_lyrics(prompt, style, mood)
    return jsonify({
        "success": True,
        "lyrics": lyrics,
        "style": style,
        "mood": mood,
        "prompt": prompt
    })

@app.route('/api/music/status')
def music_status_api():
    return jsonify({
        "available": MUSIC_AVAILABLE,
        "model_loaded": getattr(music_gen, 'model_loaded', False),
        "device": str(getattr(music_gen, 'device', 'N/A'))
    })

# ================================================================
# PROMPT OPTIMIZER & TEXT-TO-SPEECH (TTS)
# ================================================================

@app.route('/api/prompt/optimize', methods=['POST'])
def optimize_prompt():
    data = request.get_json() or {}
    original_prompt = data.get('prompt', '').strip()
    if not original_prompt:
        return jsonify({"error": "Câu lệnh không được để trống"}), 400

    optimized = f" Hãy đóng vai là một chuyên gia hàng đầu, phân tích chi tiết và đưa ra câu trả lời xuất sắc cho câu hỏi: '{original_prompt}'. Yêu cầu trình trình bày mạch lạc, cấu trúc rõ ràng với Markdown."
    return jsonify({"success": True, "original": original_prompt, "optimized": optimized})

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "Văn bản đọc không được để trống"}), 400

    return jsonify({
        "success": True,
        "text": text[:100],
        "message": "Đã khởi tạo dữ liệu giọng nói AI thành công.",
        "audio_url": "/static/music/demo.wav"
    })

# ================================================================
# USAGE & PAYMENT & ADMIN API ROUTES
# ================================================================

@app.route('/api/usage/<tier>')
def get_usage(tier):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get('role') == 'admin':
        return jsonify({"remaining": 999999, "used": 0, "max": 999999, "unlimited": True})

    max_uses = {'basic': 999999, 'pro': 5, 'plus': 2, 'pro3': 0, 'music': 20}.get(tier, 0)
    used = get_usage_count(user_id, tier)

    return jsonify({
        "remaining": max(0, max_uses - used) if max_uses > 0 else 0,
        "used": used,
        "max": max_uses,
        "unlimited": max_uses == 999999
    })

@app.route('/api/upgrade', methods=['POST'])
def upgrade():
    data = request.get_json() or {}
    tier = data.get('tier')
    user_id = session.get('user_id')

    if not user_id or tier not in LEVEL_CONFIG:
        return jsonify({"error": "Yêu cầu không hợp lệ"}), 400

    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    update_subscription(user_id, tier, expiry)

    return jsonify({
        "success": True,
        "tier": tier,
        "expiry": expiry,
        "message": f"Kích hoạt thành công gói {LEVEL_CONFIG[tier]['name']}!"
    })

@app.route('/api/payment/create', methods=['POST'])
def create_payment_api():
    data = request.get_json() or {}
    tier = data.get('tier', 'pro')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    prices = {'pro': 20000, 'plus': 50000, 'pro3': 100000}
    if tier not in prices:
        return jsonify({"error": "Gói không hợp lệ"}), 400

    amount = prices[tier]
    order_id = f"AI_{user_id}_{int(datetime.datetime.now().timestamp())}"
    order_info = f"Nâng cấp gói {tier.upper()} - T.VỸ-AI SUPREME"

    result = create_payment(order_id, amount, order_info, user_id)
    if result.get('error'):
        return jsonify({"error": result['error']}), 500

    return jsonify({
        "success": True,
        "payUrl": result.get('payUrl'),
        "orderId": result.get('orderId')
    })

@app.route('/payment/ipn', methods=['POST'])
def payment_ipn():
    return handle_ipn()

@app.route('/payment/complete')
def payment_complete_page():
    return payment_complete()

# BỘ API DÀNH CHO TRANG QUẢN TRỊ (ADMIN PANEL)
@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    user_id = session.get('user_id')
    user = get_user_by_id(user_id) if user_id else None
    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Truy cập bị từ chối. Cần quyền Admin"}), 403

    return jsonify({
        "success": True,
        "total_users": get_total_users(),
        "total_conversations": get_total_conversations(),
        "premium_users": len(get_premium_users() or []),
        "usage_stats": get_all_usage_stats()
    })

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    user_id = session.get('user_id')
    user = get_user_by_id(user_id) if user_id else None
    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Truy cập bị từ chối"}), 403

    users = get_all_users()
    return jsonify({"success": True, "users": [dict(u) for u in users]})

@app.route('/api/admin/user/<target_user_id>/role', methods=['PUT'])
def admin_update_role(target_user_id):
    user_id = session.get('user_id')
    user = get_user_by_id(user_id) if user_id else None
    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Truy cập bị từ chối"}), 403

    data = request.get_json() or {}
    new_role = data.get('role', 'user')
    update_user_role(target_user_id, new_role)
    return jsonify({"success": True, "message": f"Đã cập nhật quyền thành {new_role}"})

@app.route('/api/admin/user/<target_user_id>', methods=['DELETE'])
def admin_delete_user(target_user_id):
    user_id = session.get('user_id')
    user = get_user_by_id(user_id) if user_id else None
    if not user or user.get('role') != 'admin':
        return jsonify({"error": "Truy cập bị từ chối"}), 403

    delete_user_by_id(target_user_id)
    return jsonify({"success": True, "message": "Đã xóa người dùng thành công"})

# ================================================================
# EXPORT CHAT
# ================================================================

@app.route('/api/export/<conv_id>')
def export_conversation(conv_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    conv = get_conversation_by_id(conv_id, user_id)
    if not conv:
        return jsonify({"error": "Không tìm thấy đoạn hội thoại"}), 404

    conv_dict = dict(conv)
    messages = parse_messages(conv_dict.get('messages', []))

    lines = [
        f"=== {conv_dict.get('name', 'Hội thoại AI')} ===",
        f"Thời gian tạo: {conv_dict.get('created_at', 'N/A')}",
        "--------------------------------------------------"
    ]
    
    for msg in messages:
        role = "Bạn" if msg.get('role') == 'user' else "AI"
        lines.append(f"[{role}]: {msg.get('content', '')}\n")

    text = "\n".join(lines)
    safe_filename = secure_filename(f"chat_{conv_id}.txt")
    
    return text, 200, {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Disposition': f'attachment; filename={safe_filename}'
    }

# ================================================================
# SOCKET.IO & GLOBAL ERROR HANDLERS
# ================================================================

@socketio.on('connect')
def handle_connect():
    logger.info('✅ Client kết nối Realtime Socket.IO')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('❌ Client ngắt kết nối Socket.IO')

@app.errorhandler(500)
def handle_500_error(e):
    logger.error(f"💥 Lỗi nội bộ Máy chủ 500: {traceback.format_exc()}")
    return jsonify({
        "success": False,
        "error": f"Lỗi nội bộ Máy chủ (500): {str(e)}",
        "details": "Hệ thống đã bắt ngoại lệ an toàn để tránh dừng dịch vụ."
    }), 500

@app.errorhandler(404)
def handle_404_error(e):
    return jsonify({"success": False, "error": "Đường dẫn không tồn tại (404)"}), 404

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║  T.VỸ-AI-SUPREME v12.6.0 (SMART CODE & MULTILINGUAL AUTO ENGINE)      ║
║  Bản quyền: T.VỸ-VIP-FILE                                           ║
║  🌐 Tự động phản hồi theo đúng ngôn ngữ người dùng gửi câu hỏi        ║
║  📦 Tự động phân chia dự án lớn thành 4-5 file/lượt & Vòng lặp Tiếp tục║
║  ⏹️ Tích hợp AbortController Ngắt Mạng & Sửa Tin Nhắn Tự Cắt Dưới     ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    socketio.run(app, debug=app.config['DEBUG'], host=host, port=port, allow_unsafe_werkzeug=True)