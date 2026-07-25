"""
====================================================================
AUTH - XÁC THỰC OAuth 2.0 (FIREBASE)
====================================================================
"""

import json
import requests
from flask import request, jsonify, session
from backend.database.db_handler import get_user_by_email, create_user, update_user_role
import os
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin.ltvy@gmail.com")


# ===== GOOGLE AUTH =====
def auth_google():
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name', email.split('@')[0] if email else 'User')
        id_token = data.get('id_token')

        # Nếu có token, xác minh với Google
        if id_token:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                token_data = response.json()
                if 'error' in token_data:
                    return jsonify({"error": "Token không hợp lệ"}), 401
                verified_email = token_data.get('email')
                if verified_email:
                    email = verified_email
            else:
                return jsonify({"error": "Xác thực token thất bại"}), 401

        if not email:
            return jsonify({"error": "Không lấy được email"}), 400

        user = get_user_by_email(email)
        if not user:
            user_id = create_user(
                username=name, 
                email=email, 
                provider='google', 
                provider_id=email
            )
        else:
            user_id = user['id']
            if email == ADMIN_EMAIL and user['role'] != 'admin':
                update_user_role(user_id, 'admin')

        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name

        return jsonify({
            "success": True,
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "role": 'admin' if email == ADMIN_EMAIL else 'user'
            }
        })
    except requests.exceptions.Timeout:
        return jsonify({"error": "Kết nối đến Google quá hạn"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== FACEBOOK AUTH =====
def auth_facebook():
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name', email.split('@')[0] if email else 'User')
        access_token = data.get('access_token')

        if access_token:
            url = f"https://graph.facebook.com/me?fields=id,name,email,picture&access_token={access_token}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                fb_data = response.json()
                if 'error' in fb_data:
                    return jsonify({"error": fb_data['error']['message']}), 401
                verified_email = fb_data.get('email')
                if verified_email:
                    email = verified_email
                name = fb_data.get('name', name)

        if not email:
            return jsonify({"error": "Không lấy được email"}), 400

        user = get_user_by_email(email)
        if not user:
            user_id = create_user(
                username=name, 
                email=email, 
                provider='facebook', 
                provider_id=email
            )
        else:
            user_id = user['id']
            if email == ADMIN_EMAIL and user['role'] != 'admin':
                update_user_role(user_id, 'admin')

        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name

        return jsonify({
            "success": True,
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "role": 'admin' if email == ADMIN_EMAIL else 'user'
            }
        })
    except requests.exceptions.Timeout:
        return jsonify({"error": "Kết nối đến Facebook quá hạn"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== LOGOUT =====
def logout():
    session.clear()
    return jsonify({"success": True})


# ===== GET CURRENT USER =====
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập"}), 401

    from backend.database.db_handler import get_user_by_id
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 404

    # Chuyển sqlite3.Row thành dict
    user_dict = dict(user)
    return jsonify({
        "id": user_dict['id'],
        "email": user_dict['email'],
        "username": user_dict['username'],
        "role": user_dict['role'],
        "avatar": user_dict.get('avatar', '')
    })