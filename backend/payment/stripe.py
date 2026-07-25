"""
====================================================================
STRIPE PAYMENT - TÍCH HỢP THANH TOÁN QUA STRIPE
====================================================================
Bản quyền: T.VỸ-VIP-FILE
====================================================================
"""

import os
import stripe
from flask import request, jsonify, session, redirect
from backend.database.db_handler import get_user_by_id, update_subscription

# Cấu hình Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")


def create_checkout_session(price_id, user_id, success_url, cancel_url):
    """Tạo session thanh toán Stripe"""
    if not stripe.api_key:
        return {"error": "Chưa cấu hình Stripe"}

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=user_id
        )
        return {"success": True, "url": checkout_session.url}
    except Exception as e:
        return {"error": str(e)}


def handle_webhook(payload, sig_header):
    """Xử lý webhook từ Stripe"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET", "")
        )
    except Exception as e:
        return {"error": str(e)}

    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        user_id = session_data.get('client_reference_id')
        if user_id:
            expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            update_subscription(user_id, 'pro', expiry)

    return {"status": "success"}