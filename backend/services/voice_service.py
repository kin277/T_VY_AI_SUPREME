# File: backend/services/voice_service.py
import os
import io

class VoiceService:
    def __init__(self, lang='vi'):
        self.lang = lang

    def text_to_speech_bytes(self, text: str) -> io.BytesIO:
        """Chuyển văn bản thành Audio Stream Giọng nói Tiếng Việt"""
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=self.lang, slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp
        except ImportError:
            print("⚠️ Hãy cài gTTS bằng lệnh: pip install gTTS")
            return None
        except Exception as e:
            print(f"❌ Lỗi Text-to-Speech: {e}")
            return None