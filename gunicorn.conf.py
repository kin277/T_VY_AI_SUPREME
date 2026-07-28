bind = "0.0.0.0:5000"
workers = 2
worker_class = "gthread"  # Đã đổi từ eventlet sang gthread để không bị lỗi DNS
timeout = 120