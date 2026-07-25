"""
====================================================================
MUSIC GENERATOR - TẠO NHẠC + LỜI BÀI HÁT BẰNG AI
====================================================================
Bản quyền: T.VỸ-VIP-FILE
Phiên bản: 6.0.0
====================================================================
Tính năng:
- Tạo lời bài hát bằng AI (Hugging Face / Fallback)
- Tạo nhạc nền instrumental bằng MusicGen
- Kết hợp thành bài hát hoàn chỉnh
====================================================================
"""

import os
import torch
import scipy.io.wavfile
import random
import time
import json
import requests
import hashlib
import base64
from typing import Dict, Any, Optional

# ===== KIỂM TRA VÀ CÀI ĐẶT THƯ VIỆN =====
try:
    from transformers import pipeline
except ImportError:
    print("⚠️ Chưa cài transformers. Chạy: pip install transformers torch scipy")
    raise

# ===== CẤU HÌNH =====
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"


# ================================================================
# LYRICS GENERATOR - TẠO LỜI BÀI HÁT
# ================================================================

class LyricGenerator:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        self.fallback_lyrics = self._load_fallback_lyrics()

    def _load_fallback_lyrics(self):
        """Lời bài hát dự phòng theo chủ đề"""
        return {
            "tình yêu": """Verse 1: 
Em là ánh sáng trong đêm tối của anh
Ánh mắt em sưởi ấm trái tim anh

Pre-chorus:
Tình yêu như cơn gió thoáng qua
Mang theo bao nhiêu mơ ước

Chorus:
Ta sẽ mãi bên nhau dù bão giông
Dù thời gian có trôi qua
Tình yêu này không phai mờ
Em mãi là duy nhất trong tim anh

Verse 2:
Trái tim anh chỉ thuộc về em
Như những vì sao lung linh trên bầu trời

Bridge:
Tình yêu là những vì sao lung linh
Là ánh sáng dẫn lối cho ta

Outro:
Mãi mãi bên nhau em nhé
Tình yêu của đời anh""",

            "mùa xuân": """Verse 1:
Mùa xuân về hoa nở khắp nơi
Cánh đào khoe sắc thắm tươi

Pre-chorus:
Gió xuân mang theo bao yêu thương
Tình yêu nảy mầm trong tim

Chorus:
Xuân về trong tim em đó
Mang theo bao hy vọng mới
Tình yêu như nắng xuân ấm áp
Sưởi ấm trái tim ta

Verse 2:
Nắng ấm và tiếng chim hót
Mùa xuân của yêu thương

Bridge:
Xuân về mang theo hy vọng mới
Cho những ước mơ bay cao

Outro:
Mùa xuân của tình yêu
Mãi mãi trong tim ta""",

            "mùa hè": """Verse 1:
Mùa hè rực rỡ nắng vàng
Biển xanh và bãi cát trắng mịn màng

Pre-chorus:
Những chiều hoàng hôn bên bờ biển
Tình yêu như sóng vỗ

Chorus:
Hè về mang theo bao kỷ niệm
Những ngày tháng tươi đẹp
Tình yêu như ánh nắng
Sưởi ấm trái tim ta

Verse 2:
Hạ về với những ước mơ
Tuổi thanh xuân đẹp như mơ

Bridge:
Mùa hè của những ước mơ
Của tình yêu và hy vọng

Outro:
Mùa hè của yêu thương
Mãi trong tim ta""",

            "mùa đông": """Verse 1:
Mùa đông lạnh giá nhưng tình yêu ấm áp
Tuyết rơi trắng xóa phố phường

Pre-chorus:
Giáng sinh về trong tim anh
Mang theo bao yêu thương

Chorus:
Mùa đông của tình yêu
Sưởi ấm trái tim ta
Dù ngoài kia giá lạnh
Tình yêu luôn ấm nồng

Verse 2:
Em ơi mùa đông đã về
Hơi ấm bên em xua tan giá lạnh

Bridge:
Hơi ấm bên em xua tan giá lạnh
Mùa đông của yêu thương

Outro:
Mùa đông của tình yêu
Mãi mãi trong tim""",

            "cuộc sống": """Verse 1:
Cuộc sống là những hành trình
Ta vươn tới những ước mơ

Pre-chorus:
Mỗi ngày là một cơ hội mới
Để ta sống trọn vẹn

Chorus:
Sống là để yêu thương và sẻ chia
Để vươn tới những điều tốt đẹp
Cuộc sống tươi đẹp biết bao
Nếu ta biết trân trọng từng khoảnh khắc

Verse 2:
Mỗi ngày là một cơ hội mới
Hạnh phúc từ những điều giản dị

Bridge:
Hạnh phúc từ những điều giản dị
Yêu thương và sẻ chia

Outro:
Cuộc sống tươi đẹp biết bao
Hãy sống trọn vẹn từng ngày"""
        }

    def detect_topic(self, prompt: str) -> str:
        """Phát hiện chủ đề từ prompt"""
        topics = ["tình yêu", "mùa xuân", "mùa hè", "mùa đông", "cuộc sống"]
        for topic in topics:
            if topic in prompt.lower():
                return topic
        return "cuộc sống"

    def detect_style(self, prompt: str) -> str:
        """Phát hiện thể loại nhạc"""
        p = prompt.lower()
        styles = {
            "pop": ["pop", "nhạc trẻ"],
            "rock": ["rock", "alternative", "metal"],
            "jazz": ["jazz", "blues", "soul"],
            "edm": ["edm", "electronic", "dance"],
            "classical": ["classical", "classic", "orchestral"],
            "rap": ["rap", "hip hop", "trap"],
            "ballad": ["ballad", "tình ca", "slow"],
            "v_pop": ["vpop", "v-pop", "nhạc việt"],
            "k_pop": ["kpop", "k-pop", "hàn quốc"]
        }
        for style, keywords in styles.items():
            if any(k in p for k in keywords):
                return style
        return "pop"

    def detect_mood(self, prompt: str) -> str:
        """Phát hiện tâm trạng"""
        p = prompt.lower()
        if any(k in p for k in ["vui", "happy", "joy", "hạnh phúc"]):
            return "happy"
        if any(k in p for k in ["buồn", "sad", "cô đơn", "đau khổ"]):
            return "sad"
        if any(k in p for k in ["lãng mạn", "romantic", "tình yêu"]):
            return "romantic"
        if any(k in p for k in ["hùng", "epic", "mạnh mẽ"]):
            return "epic"
        return "neutral"

    def generate_lyrics(self, prompt: str, style: str = "pop", mood: str = "happy") -> str:
        """Tạo lời bài hát từ prompt"""
        topic = self.detect_topic(prompt)
        
        # Thử gọi Hugging Face API nếu có token
        if HF_TOKEN:
            try:
                prompt_text = f"""
Tạo lời bài hát hoàn chỉnh với các yêu cầu sau:
- Chủ đề: {prompt}
- Thể loại: {style}
- Tâm trạng: {mood}
- Cấu trúc: Verse 1, Pre-chorus, Chorus, Verse 2, Bridge, Outro
- Ngôn ngữ: Tiếng Việt
- Lời bài hát sáng tạo, có vần điệu, cảm xúc

Lời bài hát:
"""
                payload = {
                    "inputs": prompt_text,
                    "parameters": {
                        "max_new_tokens": 600,
                        "temperature": 0.85,
                        "do_sample": True,
                        "top_p": 0.95
                    }
                }
                
                response = requests.post(HF_API_URL, headers=self.headers, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    lyrics = result[0].get("generated_text", "")
                    if len(lyrics) > 100 and "Verse" in lyrics:
                        return self._clean_lyrics(lyrics)
            except:
                pass

        # Fallback: lấy từ kho dự phòng
        base_lyrics = self.fallback_lyrics.get(topic, self.fallback_lyrics["cuộc sống"])
        return self._customize_lyrics(base_lyrics, prompt, style, mood)

    def _clean_lyrics(self, raw_lyrics: str) -> str:
        """Làm sạch lời bài hát"""
        lines = raw_lyrics.split("\n")
        cleaned = []
        start = False
        
        for line in lines:
            if "Verse" in line or "Chorus" in line or "Pre-chorus" in line or "Bridge" in line or "Outro" in line:
                start = True
            if start and line.strip():
                cleaned.append(line.strip())
        
        if len(cleaned) < 4:
            return raw_lyrics[:500] + "..."
        
        return "\n".join(cleaned)

    def _customize_lyrics(self, base_lyrics: str, prompt: str, style: str, mood: str) -> str:
        """Biến tấu lời dự phòng"""
        lines = base_lyrics.strip().split("\n")
        modified = []
        
        # Lấy từ khóa từ prompt
        prompt_words = prompt.split()[:3]
        topic_phrase = " ".join(prompt_words) if prompt_words else "yêu thương"
        
        for i, line in enumerate(lines):
            # Thêm chủ đề vào Chorus
            if "Chorus" in line and i + 1 < len(lines):
                if not " - " in lines[i + 1]:
                    lines[i + 1] = f"{lines[i + 1]} - {topic_phrase}"
            # Thêm style và mood vào Outro
            if "Outro" in line and i + 1 < len(lines):
                lines[i + 1] = f"{lines[i + 1]} ({style}, {mood})"
            modified.append(lines[i])
        
        return "\n".join(modified)


# ================================================================
# MUSIC GENERATOR - TẠO NHẠC NỀN
# ================================================================

class MusicGenerator:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.synthesiser = None
        self.model_loaded = False
        self.model_name = "facebook/musicgen-medium"
        print(f"🎵 MusicGenerator khởi tạo với device: {self.device}")

    def load_model(self):
        """Tải model MusicGen (lần đầu mất 2-3 phút)"""
        if self.model_loaded:
            return True

        try:
            print(f"🔄 Đang tải model {self.model_name}...")
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

    def generate_instrumental(self, prompt: str, duration: int = 15, style: str = None, mood: str = None) -> Dict:
        """
        Tạo nhạc nền instrumental
        
        Args:
            prompt: Mô tả nhạc
            duration: Độ dài (giây, tối đa 30)
            style: Thể loại
            mood: Tâm trạng
        
        Returns:
            Dict: Kết quả chứa file nhạc
        """
        if not self.model_loaded:
            if not self.load_model():
                return {"error": "Không thể tải model MusicGen"}

        # Xây dựng prompt đầy đủ
        full_prompt = prompt
        if style:
            full_prompt = f"{style} music, {full_prompt}"
        if mood:
            full_prompt = f"{mood} mood, {full_prompt}"

        try:
            # Giới hạn duration
            if duration > 30:
                duration = 30
            if duration < 5:
                duration = 5

            # Random seed để mỗi lần khác nhau
            random_seed = random.randint(0, 2**32 - 1)
            torch.manual_seed(random_seed)
            if self.device.type == 'cuda':
                torch.cuda.manual_seed_all(random_seed)

            # Tạo nhạc
            result = self.synthesiser(
                full_prompt,
                forward_params={
                    "do_sample": True,
                    "max_length": duration * 50
                }
            )

            # Lưu file
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
                "prompt": full_prompt,
                "message": "🎵 Nhạc nền đã được tạo thành công!"
            }
        except Exception as e:
            return {"error": f"Lỗi tạo nhạc: {str(e)}"}

    def generate_with_lyrics(self, prompt: str, duration: int = 15, style: str = None, mood: str = None) -> Dict:
        """
        Tạo bài hát hoàn chỉnh (lời + nhạc)
        """
        # Bước 1: Tạo lời
        lyric_gen = LyricGenerator()
        if not style:
            style = lyric_gen.detect_style(prompt)
        if not mood:
            mood = lyric_gen.detect_mood(prompt)
        
        lyrics = lyric_gen.generate_lyrics(prompt, style, mood)
        
        # Bước 2: Tạo nhạc nền
        music_prompt = f"{style} music, {mood} mood, {prompt}"
        music_result = self.generate_instrumental(music_prompt, duration, style, mood)
        
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
            "prompt": prompt,
            "message": "🎵 Bài hát hoàn chỉnh đã được tạo!"
        }


# ================================================================
# HÀM GỌI BÊN NGOÀI
# ================================================================

def generate_music_with_lyrics(prompt: str, duration: int = 15, style: str = None, mood: str = None) -> Dict:
    """Tạo bài hát hoàn chỉnh (lời + nhạc)"""
    generator = MusicGenerator()
    return generator.generate_with_lyrics(prompt, duration, style, mood)

def generate_instrumental_only(prompt: str, duration: int = 15, style: str = None, mood: str = None) -> Dict:
    """Chỉ tạo nhạc nền (không có lời)"""
    generator = MusicGenerator()
    return generator.generate_instrumental(prompt, duration, style, mood)

def generate_lyrics_only(prompt: str, style: str = None, mood: str = None) -> Dict:
    """Chỉ tạo lời bài hát (không có nhạc)"""
    lyric_gen = LyricGenerator()
    if not style:
        style = lyric_gen.detect_style(prompt)
    if not mood:
        mood = lyric_gen.detect_mood(prompt)
    
    lyrics = lyric_gen.generate_lyrics(prompt, style, mood)
    return {
        "success": True,
        "lyrics": lyrics,
        "style": style,
        "mood": mood,
        "prompt": prompt
    }

def get_music_status() -> Dict:
    """Kiểm tra trạng thái model"""
    generator = MusicGenerator()
    return {
        "model_loaded": generator.model_loaded,
        "device": str(generator.device),
        "model_name": generator.model_name
    }