"""
====================================================================
AUTH - XÁC THỰC OAuth 2.0 (Google, Facebook, GitHub)
====================================================================
"""

import os
import requests
from flask import request, jsonify, session
from backend.database.db_handler import get_user_by_email, create_user, update_user_role, get_user_by_id
from config.settings import ADMIN_EMAIL

# ================================================================
# GOOGLE AUTH
# ================================================================

def auth_google():
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name', email.split('@')[0] if email else 'User')
        id_token = data.get('id_token')

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
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# FACEBOOK AUTH
# ================================================================

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
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# GITHUB AUTH (CALLBACK)
# ================================================================

def auth_github_callback(code):
    """Xử lý callback từ GitHub OAuth"""
    if not code:
        return {"error": "Không tìm thấy code"}, 400
    
    client_id = os.getenv("GITHUB_CLIENT_ID", "")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
    
    if not client_id or not client_secret:
        return {"error": "Chưa cấu hình GitHub OAuth"}, 400
    
    token_url = "https://github.com/login/oauth/access_token"
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, headers={"Accept": "application/json"}, timeout=10)
        if token_response.status_code == 200:
            token_json = token_response.json()
            access_token = token_json.get("access_token")
            
            if access_token:
                # Lấy thông tin user
                user_url = "https://api.github.com/user"
                user_response = requests.get(user_url, headers={"Authorization": f"Bearer {access_token}"})
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    email = user_data.get("email")
                    name = user_data.get("name") or user_data.get("login")
                    avatar = user_data.get("avatar_url")
                    
                    # Nếu email không public, lấy từ API emails
                    if not email:
                        email_url = "https://api.github.com/user/emails"
                        email_response = requests.get(email_url, headers={"Authorization": f"Bearer {access_token}"})
                        if email_response.status_code == 200:
                            emails = email_response.json()
                            for e in emails:
                                if e.get("primary"):
                                    email = e.get("email")
                                    break
                            if not email and emails:
                                email = emails[0].get("email")
                    
                    if email:
                        # Tạo hoặc tìm user
                        user = get_user_by_email(email)
                        if not user:
                            user_id = create_user(
                                username=name or email.split('@')[0],
                                email=email,
                                provider='github',
                                provider_id=str(user_data.get("id"))
                            )
                        else:
                            user_id = user['id']
                        
                        # Cập nhật role admin nếu là admin email
                        if email == ADMIN_EMAIL and user['role'] != 'admin':
                            update_user_role(user_id, 'admin')
                        
                        return {
                            "success": True,
                            "user_id": user_id,
                            "email": email,
                            "name": name or email.split('@')[0],
                            "avatar": avatar
                        }
                
        return {"error": "Không thể lấy thông tin từ GitHub"}, 400
    except Exception as e:
        return {"error": str(e)}, 500


# ================================================================
# LOGOUT
# ================================================================

def logout():
    session.clear()
    return jsonify({"success": True})


# ================================================================
# GET CURRENT USER
# ================================================================

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Chưa đăng nhập", "is_guest": True}), 401

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"error": "User not found", "is_guest": True}), 404

    user_dict = dict(user)
    return jsonify({
        "id": user_dict['id'],
        "email": user_dict['email'],
        "username": user_dict['username'],
        "role": user_dict['role'],
        "is_guest": user_id.startswith("guest_"),
        "avatar": user_dict.get('avatar', '')
    })