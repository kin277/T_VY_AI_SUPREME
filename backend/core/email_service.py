"""
====================================================================
EMAIL SERVICE - GỬI EMAIL TỰ ĐỘNG
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email, subject, body):
    """Gửi email đơn giản qua SMTP"""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SENDER_EMAIL", "")
    sender_password = os.getenv("SENDER_PASSWORD", "")

    if not sender_email or not sender_password:
        print("⚠️ Chưa cấu hình email. Vui lòng thêm SENDER_EMAIL và SENDER_PASSWORD vào file .env")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Đã gửi email đến {to_email}")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi email: {e}")
        return False


def send_welcome_email(email, username):
    """Gửi email chào mừng"""
    subject = "Chào mừng bạn đến với T.VỸ-AI-SUPREME!"
    body = f"""
Xin chào {username},

Chào mừng bạn đến với T.VỸ-AI-SUPREME - Trợ lý AI thế hệ mới!

Bạn đã đăng ký thành công tài khoản. Dưới đây là những tính năng bạn có thể sử dụng:

- Trò chuyện với AI thông minh
- Tạo ảnh bằng AI (DALL-E / Stable Diffusion)
- Tạo code mọi ngôn ngữ
- Tìm kiếm thông tin đa nguồn
- Tư vấn và hướng dẫn kỹ thuật

Nâng cấp lên gói Pro, Plus hoặc 3.0 Pro để trải nghiệm đầy đủ tính năng!

---
Trân trọng,
Đội ngũ T.VỸ-AI
Website: http://localhost:5000
    """
    return send_email(email, subject, body)


def send_upgrade_email(email, username, tier):
    """Gửi email xác nhận nâng cấp"""
    tier_names = {
        'pro': 'Pro',
        'plus': 'Plus',
        'pro3': '3.0 Pro'
    }
    tier_display = tier_names.get(tier, tier.upper())

    subject = f"Xác nhận nâng cấp gói {tier_display} - T.VỸ-AI"
    body = f"""
Xin chào {username},

Chúc mừng bạn đã nâng cấp thành công lên gói {tier_display}!

Các tính năng của gói {tier_display}:
- Trả lời chi tiết, chính xác hơn
- Tìm kiếm web đa nguồn
- Ưu tiên xử lý
- Hỗ trợ 24/7

Cảm ơn bạn đã tin tưởng và sử dụng dịch vụ của chúng tôi!

---
Trân trọng,
Đội ngũ T.VỸ-AI
Website: http://localhost:5000
    """
    return send_email(email, subject, body)


def send_password_reset_email(email, username, reset_link):
    """Gửi email đặt lại mật khẩu"""
    subject = "Đặt lại mật khẩu - T.VỸ-AI-SUPREME"
    body = f"""
Xin chào {username},

Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn.

Vui lòng click vào link bên dưới để đặt lại mật khẩu:
{reset_link}

Link có hiệu lực trong 30 phút.

Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.

---
Trân trọng,
Đội ngũ T.VỸ-AI
    """
    return send_email(email, subject, body)