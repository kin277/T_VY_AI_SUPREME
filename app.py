"""
====================================================================
T.VỸ-AI-SUPREME - ỨNG DỤNG CHÍNH (HOÀN CHỈNH & NÂNG CẤP GIAO DIỆN)
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 11.0.0
====================================================================
Tính năng:
- Chat AI với 4 cấp độ
- Tạo nhạc (lời + nhạc nền)
- Đăng nhập Google/Facebook/GitHub
- Nâng cấp gói Pro/Plus/3.0 Pro
- Thanh toán MoMo
- Admin Panel & Lịch sử Chat / Export
- Dark/Light mode & Giao diện tối ưu hóa UI/UX
====================================================================
"""

import datetime
import json
import os
import random
import sys
import time
import requests

from flask import (
    Flask, jsonify, render_template, request,
    send_from_directory, session
)
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ===== CẤU HÌNH FLASK =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'frontend', 'public')
STATIC_DIR = os.path.join(TEMPLATE_DIR, 'assets')

app = Flask(__name__,
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR,
            static_url_path='/assets')

app.secret_key = "T_VY_VIP_FILE_2025"
app.config['DEBUG'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# ===== IMPORT MODULES =====
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

# ===== KHỞI TẠO DATABASE =====
init_db()

# ===== KHỞI TẠO AI =====
ai_engine = AIEngine(level="pro")
ethics = EthicsGuard()

# ================================================================
# MUSIC GENERATOR (TÍCH HỢP MUSICGEN + LYRICS)
# ================================================================

try:
    import scipy.io.wavfile
    import torch
    from transformers import pipeline

    class LyricGenerator:
        def __init__(self):
            self.fallback_lyrics = self._load_fallback_lyrics()

        def _load_fallback_lyrics(self):
            return {
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
            for topic in topics:
                if topic in prompt.lower():
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
            print(f"🎵 MusicGenerator khởi tạo với device: {self.device}")
            self.lyric_gen = LyricGenerator()

        def load_model(self):
            if self.model_loaded:
                return True
            try:
                print(f"🔄 Đang tải model {self.model_name}... (lần đầu mất 2-3 phút)")
                self.synthesiser = pipeline(
                    "text-to-audio",
                    model=self.model_name,
                    device=0 if self.device.type == 'cuda' else -1
                )
                self.model_loaded = True
                print("✅ Model MusicGen đã tải thành công!")
                return True
            except Exception as e:
                print(f"❌ Lỗi tải model: {e}")
                return False

        def generate_instrumental(self, prompt, duration=15, style=None, mood=None):
            if not self.model_loaded:
                if not self.load_model():
                    return {"error": "Không thể tải model MusicGen"}

            full_prompt = prompt
            if style:
                full_prompt = f"{style} music, {full_prompt}"
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
                filepath = os.path.join("static", "music", filename)
                os.makedirs("static/music", exist_ok=True)

                scipy.io.wavfile.write(
                    filepath,
                    rate=result["sampling_rate"],
                    data=result["audio"]
                )

                return {
                    "success": True,
                    "filepath": filepath,
                    "filename": filename,
                    "duration": duration,
                    "download_url": f"/static/music/{filename}",
                    "prompt": full_prompt
                }
            except Exception as e:
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
    print("🎵 MusicGenerator đã sẵn sàng!")

except ImportError as e:
    print(f"⚠️ MusicGenerator không khả dụng: {e}")
    print("📌 Để kích hoạt, chạy: pip install transformers torch scipy")

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
                "note": "⚠️ Đây là bản demo. Hãy cài transformers để có nhạc thật."
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
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route('/static/music/<filename>')
def serve_music(filename):
    return send_from_directory('static/music', filename)

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
        return """
        <html>
        <head><title>Lỗi</title></head>
        <body style="font-family:Arial;text-align:center;padding:50px;">
            <h2>❌ Lỗi xác thực</h2>
            <p>Không tìm thấy mã xác thực từ GitHub.</p>
            <p><a href="/">Quay lại trang chủ</a></p>
        </body>
        </html>
        """, 400

    result = auth_github_callback(code)

    if result.get("error"):
        return f"""
        <html>
        <head><title>Lỗi</title></head>
        <body style="font-family:Arial;text-align:center;padding:50px;">
            <h2>❌ Đăng nhập thất bại</h2>
            <p>{result['error']}</p>
            <p><a href="/">Quay lại trang chủ</a></p>
        </body>
        </html>
        """, 400

    if result.get("success"):
        session['user_id'] = result['user_id']
        session['user_email'] = result['email']
        session['user_name'] = result['name']

        return """
        <html>
        <head>
            <title>Đăng nhập thành công</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; background: #0a0a0f; color: #fff; }}
                .success {{ color: #22c55e; font-size: 48px; }}
                .btn {{ display: inline-block; padding: 10px 24px; background: #6c5ce7; color: #fff; text-decoration: none; border-radius: 8px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="success">✅</div>
            <h2>Đăng nhập thành công!</h2>
            <p>Chào mừng <strong>{}</strong>!</p>
            <p>Đang chuyển hướng...</p>
            <a href="/" class="btn">Về trang chủ</a>
            <script>
                setTimeout(() => {{
                    if (window.opener) {{
                        window.opener.location.reload();
                        window.close();
                    }} else {{
                        window.location.href = '/';
                    }}
                }}, 1500);
            </script>
        </body>
        </html>
        """.format(result['name'])

    return """
    <html>
    <head><title>Lỗi</title></head>
    <body style="font-family:Arial;text-align:center;padding:50px;">
        <h2>❌ Đăng nhập thất bại</h2>
        <p>Đã xảy ra lỗi không xác định.</p>
        <p><a href="/">Quay lại trang chủ</a></p>
    </body>
    </html>
    """, 400

# ================================================================
# CHAT ROUTES
# ================================================================

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    conv_id = data.get('conversation_id', None)
    level = data.get('level', 'pro')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Vui lòng đăng nhập"}), 401

    if not message:
        return jsonify({"error": "Vui lòng nhập câu hỏi"}), 400

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "User không tồn tại"}), 401

    if user['role'] != 'admin':
        max_uses = {'basic': 999999, 'pro': 5, 'plus': 2, 'pro3': 0}.get(level, 0)
        used = get_usage_count(user_id, level)
        if max_uses > 0 and used >= max_uses:
            return jsonify({
                "error": f"Đã hết lượt {level} hôm nay ({used}/{max_uses})",
                "limit_reached": True
            }), 429
        log_usage(user_id, level)

    if not conv_id:
        conv_id = str(uuid.uuid4()) if 'uuid' in globals() else str(time.time())
        name = message[:30] + ("..." if len(message) > 30 else "")
        messages = []
    else:
        conv = get_conversation_by_id(conv_id, user_id)
        if not conv:
            return jsonify({"error": "Không tìm thấy đoạn chat"}), 404
        messages = conv['messages']

    messages.append({
        "role": "user",
        "content": message,
        "time": datetime.datetime.now().isoformat()
    })

    ai_engine.level = level
    result = ai_engine.process(message)
    ai_response = result.get("message", "Đã xử lý thành công.")

    messages.append({
        "role": "ai",
        "content": ai_response,
        "time": datetime.datetime.now().isoformat()
    })

    save_conversation(user_id, conv_id, name, messages, level)
    convs = get_conversations_by_user(user_id)

    socketio.emit('new_message', {
        'user_id': user_id,
        'conversation_id': conv_id,
        'message': ai_response
    }, room='global')

    return jsonify({
        "type": "chat",
        "message": ai_response,
        "conversation_id": conv_id,
        "conversations": [dict(c) for c in convs],
        "level": level
    })

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
        return jsonify({"error": "Not found"}), 404

    return jsonify({"conversation": conv})

@app.route('/delete/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    delete_conversation_by_id(conv_id, user_id)
    return jsonify({"success": True})

# ================================================================
# MUSIC ROUTES
# ================================================================

@app.route('/api/generate_music', methods=['POST'])
def generate_music_api():
    data = request.get_json()
    prompt = data.get('prompt', '')
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
    if user['role'] != 'admin':
        max_music_uses = 20
        used = get_usage_count(user_id, 'music')
        if used >= max_music_uses:
            return jsonify({
                "error": f"Đã hết lượt tạo nhạc hôm nay ({used}/{max_music_uses}). Lượt mới sẽ được reset lúc 9h sáng.",
                "limit_reached": True
            }), 429
        log_usage(user_id, 'music')

    try:
        result = music_gen.generate_with_lyrics(prompt, duration, style, mood)
        if result.get('error'):
            return jsonify({"error": result['error']}), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_lyrics', methods=['POST'])
def generate_lyrics_api():
    data = request.get_json()
    prompt = data.get('prompt', '')
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

@app.route('/api/music/styles')
def music_styles_api():
    return jsonify({
        "styles": ["pop", "rock", "jazz", "edm", "classical", "rap", "ballad", "v_pop", "k_pop"]
    })

@app.route('/api/music/moods')
def music_moods_api():
    return jsonify({
        "moods": ["happy", "sad", "romantic", "epic", "neutral"]
    })

# ================================================================
# USAGE & UPGRADE ROUTES
# ================================================================

@app.route('/api/usage/<tier>')
def get_usage(tier):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user['role'] == 'admin':
        return jsonify({"remaining": 999999, "used": 0, "max": 999999, "unlimited": True})

    if tier == 'music':
        max_uses = 20
        used = get_usage_count(user_id, 'music')
        return jsonify({
            "remaining": max_uses - used,
            "used": used,
            "max": max_uses,
            "unlimited": False
        })

    max_uses = {'basic': 999999, 'pro': 5, 'plus': 2, 'pro3': 0}.get(tier, 0)
    used = get_usage_count(user_id, tier)

    return jsonify({
        "remaining": max(0, max_uses - used) if max_uses > 0 else 0,
        "used": used,
        "max": max_uses,
        "unlimited": max_uses == 999999
    })

@app.route('/api/upgrade', methods=['POST'])
def upgrade():
    data = request.get_json()
    tier = data.get('tier')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    if tier not in LEVEL_CONFIG:
        return jsonify({"error": "Cấp độ không hợp lệ"}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    price = LEVEL_CONFIG[tier]['price']
    if price == 0:
        return jsonify({"error": "Đây là cấp độ miễn phí"}), 400

    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    update_subscription(user_id, tier, expiry)

    return jsonify({
        "success": True,
        "tier": tier,
        "expiry": expiry,
        "message": f"Đã nâng cấp thành công lên {LEVEL_CONFIG[tier]['name']}!"
    })

# ================================================================
# PAYMENT ROUTES (MoMo)
# ================================================================

@app.route('/api/payment/create', methods=['POST'])
def create_payment_api():
    data = request.get_json()
    tier = data.get('tier', 'pro')
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    prices = {'pro': 20000, 'plus': 50000, 'pro3': 100000}

    if tier not in prices:
        return jsonify({"error": "Gói không hợp lệ"}), 400

    amount = prices[tier]
    order_id = f"AI_{user_id}_{int(datetime.datetime.now().timestamp())}"
    order_info = f"Nâng cấp gói {tier.upper()} - T.VỸ-AI"

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

# ================================================================
# ADMIN ROUTES
# ================================================================

def is_admin(user_id):
    user = get_user_by_id(user_id)
    return user and user['role'] == 'admin'

@app.route('/api/admin/stats')
def admin_stats():
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    return jsonify({
        "total_users": get_total_users(),
        "total_conversations": get_total_conversations(),
        "total_usage": get_all_usage_stats(),
        "premium_users": get_premium_users()
    })

@app.route('/api/admin/users')
def admin_users():
    user_id = session.get('user_id')
    if not user_id or not is_admin(user_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    users = get_all_users()
    return jsonify([dict(u) for u in users])

@app.route('/api/admin/delete_user/<user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    admin_id = session.get('user_id')
    if not admin_id or not is_admin(admin_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    if user_id == admin_id:
        return jsonify({"error": "Không thể tự xóa chính mình"}), 400

    delete_user_by_id(user_id)
    return jsonify({"success": True})

@app.route('/api/admin/set_role', methods=['POST'])
def admin_set_role():
    admin_id = session.get('user_id')
    if not admin_id or not is_admin(admin_id):
        return jsonify({"error": "Yêu cầu quyền Admin"}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    role = data.get('role')

    if not user_id or role not in ['user', 'admin']:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    if user_id == admin_id:
        return jsonify({"error": "Không thể thay đổi vai trò của chính mình"}), 400

    update_user_role(user_id, role)
    return jsonify({"success": True})

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
        return jsonify({"error": "Not found"}), 404

    lines = [f"=== {conv['name']} ===", f"Tạo: {conv['created_at']}", f"Cấp độ: {conv['level']}", ""]
    for msg in conv['messages']:
        role = "Bạn" if msg['role'] == 'user' else "AI"
        lines.append(f"[{role}] {msg['content']}")
        lines.append("")

    text = "\n".join(lines)
    return text, 200, {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Disposition': f'attachment; filename=chat_{conv_id}.txt'
    }

# ================================================================
# SOCKET.IO
# ================================================================

@socketio.on('connect')
def handle_connect():
    print('✅ Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('❌ Client disconnected')

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined', {'room': room})

@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)
        emit('left', {'room': room})

@socketio.on('send_message')
def handle_send_message(data):
    room = data.get('room')
    message = data.get('message')
    if room and message:
        emit('new_message', message, room=room)

# ================================================================
# MAIN
# ================================================================

if __name__ == '__main__':
    os.makedirs("static/music", exist_ok=True)

    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║  T.VỸ-AI-SUPREME v11.0                                              ║
║  Bản quyền: T.VỸ-VIP-FILE                                           ║
║  🔥 Chat AI 4 cấp độ                                                ║
║  🎵 Tạo nhạc bằng AI (MusicGen + Lyrics)                           ║
║  💳 Thanh toán MoMo                                                 ║
║  👑 Admin Panel                                                     ║
║  🚀 Chạy tại: http://localhost:5000                                 ║
║  📁 Thư mục nhạc: static/music/                                     ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)