# File: backend/api/chat_routes.py
from flask import Blueprint, request, jsonify
from backend.core.ai_engine import AIEngine

# Khởi tạo Blueprint cho các API Chat
chat_bp = Blueprint('chat_bp', __name__)
ai_engine = AIEngine()

@chat_bp.route('/chat', methods=['POST'])
def handle_chat():
    """API Tiếp nhận tin nhắn từ giao diện Web & xử lý phản hồi AI"""
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    level = data.get('level', 'pro')
    web_synthesis = data.get('web_synthesis', True)

    if not user_message:
        return jsonify({"error": "Nội dung tin nhắn không được để trống!", "success": False}), 400

    try:
        # Gọi engine xử lý AI
        result = ai_engine.process_ai_request(
            user_message=user_message,
            level=level,
            web_synthesis=web_synthesis
        )

        return jsonify({
            "success": True,
            "conversation_id": data.get('conversation_id') or "conv_12345",
            "message": result.get("message", ""),
            "sources": result.get("sources", []),
            "has_artifact": result.get("has_artifact", False)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Lỗi hệ thống khi xử lý AI: {str(e)}"
        }), 500

@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """API Lấy danh sách lịch sử hội thoại"""
    return jsonify({
        "success": True,
        "conversations": [
            {"id": "conv_12345", "name": "Thảo luận AI Supreme", "created_at": "2026-08-01T10:00:00"}
        ]
    })