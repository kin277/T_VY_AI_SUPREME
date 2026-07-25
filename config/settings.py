"""
====================================================================
CẤU HÌNH CHUNG DỰ ÁN - T.VỸ-VIP-FILE
====================================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_NAME = "T.VỸ-AI-SUPREME"
    APP_VERSION = "11.0.0"
    AUTHOR = "T.VỸ-VIP-FILE"
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "T_VY_VIP_FILE_2025")

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

    # ===== ADMIN EMAIL (DÙNG CHO FIREBASE OAuth) =====
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin.ltvy@gmail.com")

    # ===== OAuth (Firebase) =====
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
    FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")

    # ===== MoMo Payment =====
    MOMO_PARTNER_CODE = os.getenv("MOMO_PARTNER_CODE", "")
    MOMO_ACCESS_KEY = os.getenv("MOMO_ACCESS_KEY", "")
    MOMO_SECRET_KEY = os.getenv("MOMO_SECRET_KEY", "")

    # ===== Stripe Payment =====
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # ===== Email SMTP =====
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

    # ===== Suno AI Music =====
    SUNO_API_KEY = os.getenv("SUNO_API_KEY", "")

    # ===== Limits =====
    MESSAGE_LIMIT_PER_CONVERSATION = 2000
    MAX_CONVERSATIONS_PER_USER = 100
    REQUEST_TIMEOUT = 30

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ===== EXPORT BIẾN CHO DỄ DÙNG =====
ADMIN_EMAIL = Config.ADMIN_EMAIL
DEBUG = Config.DEBUG
SECRET_KEY = Config.SECRET_KEY
HOST = Config.HOST
PORT = Config.PORT