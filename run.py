#!/usr/bin/env python3
"""
====================================================================
RUN AI SUPREME - T.VỸ-VIP-FILE
====================================================================
Chạy toàn bộ hệ thống AI Supreme
====================================================================
"""

import os
import sys
import subprocess
import time

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ████████╗██╗   ██╗██╗   ██╗██╗   ██╗     █████╗ ██╗               ║
║   ╚══██╔══╝╚██╗ ██╔╝╚██╗ ██╔╝╚██╗ ██╔╝    ██╔══██╗██║               ║
║      ██║    ╚████╔╝  ╚════╝   ╚════╝     ███████║██║               ║
║      ██║     ╚██╔╝   ██╗██╗   ██╗██╗     ██╔══██║██║               ║
║      ██║      ██║    ╚═╝╚═╝   ╚═╝╚═╝     ██║  ██║██║               ║
║      ╚═╝      ╚═╝                          ╚═╝  ╚═╝╚═╝               ║
║                                                                       ║
║   ███████╗██╗   ██╗██████╗ ██████╗ ███████╗███╗   ███╗███████╗      ║
║   ██╔════╝██║   ██║██╔══██╗██╔══██╗██╔════╝████╗ ████║██╔════╝      ║
║   ███████╗██║   ██║██████╔╝██████╔╝█████╗  ██╔████╔██║█████╗        ║
║   ╚════██║██║   ██║██╔═══╝ ██╔══██╗██╔══╝  ██║╚██╔╝██║██╔══╝        ║
║   ███████║╚██████╔╝██║     ██║  ██║███████╗██║ ╚═╝ ██║███████╗      ║
║   ╚══════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝      ║
║                                                                       ║
║   🚀 T.VỸ-AI-SUPREME v10.5                                           ║
║   📌 Bản quyền: T.VỸ-VIP-FILE                                        ║
║   🔥 Hệ thống AI toàn diện với 4 cấp độ                              ║
║   🌐 Chạy tại: http://localhost:5000                                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

def check_dependencies():
    """Kiểm tra dependencies"""
    try:
        import flask
        import flask_cors
        import flask_socketio
        print("✅ Flask và các thư viện đã được cài đặt.")
        return True
    except ImportError as e:
        print(f"❌ Thiếu thư viện: {e}")
        print("📦 Đang cài đặt dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return False

def run_server():
    """Chạy server Flask"""
    print("\n🔥 ĐANG KHỞI ĐỘNG SERVER...")
    subprocess.run([sys.executable, "app.py"])

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print_banner()
    
    # Kiểm tra và cài đặt dependencies
    check_dependencies()
    
    # Chạy server
    run_server()