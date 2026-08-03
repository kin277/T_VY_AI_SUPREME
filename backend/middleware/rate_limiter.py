# File: backend/middleware/rate_limiter.py
import time
from flask import request, jsonify
from functools import wraps

# Lưu trữ tạm thời request counts trong bộ nhớ
IP_REQUESTS = {}

def limit_rate(max_requests=20, window_seconds=60):
    """Middleware giới hạn số lượt request mỗi phút theo IP"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr or "127.0.0.1"
            current_time = time.time()

            if ip not in IP_REQUESTS:
                IP_REQUESTS[ip] = []

            # Lọc các request đã hết thời hạn window
            IP_REQUESTS[ip] = [t for t in IP_REQUESTS[ip] if current_time - t < window_seconds]

            if len(IP_REQUESTS[ip]) >= max_requests:
                return jsonify({
                    "error": "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau 1 phút!",
                    "code": 429
                }), 429

            IP_REQUESTS[ip].append(current_time)
            return f(*args, **kwargs)
        return wrapped
    return decorator