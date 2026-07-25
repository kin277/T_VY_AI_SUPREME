"""
====================================================================
IMAGE GENERATOR - TẠO ẢNH BẰNG AI (DALL-E / Stability AI)
====================================================================
"""

import os
import requests
import base64
import json

def generate_image_dalle(prompt, size="512x512", api_key=None):
    """
    Tạo ảnh bằng OpenAI DALL-E API
    """
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "Thiếu OPENAI_API_KEY"}

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "dall-e-2",
        "prompt": prompt,
        "n": 1,
        "size": size
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            image_url = result['data'][0]['url']
            return {"success": True, "url": image_url}
        else:
            return {"error": response.json().get('error', {}).get('message', 'Lỗi không xác định')}
    except Exception as e:
        return {"error": str(e)}


def generate_image_stability(prompt, api_key=None):
    """
    Tạo ảnh bằng Stability AI API (Stable Diffusion)
    """
    if not api_key:
        api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        return {"error": "Thiếu STABILITY_API_KEY"}

    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 7,
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 30
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            # Lấy ảnh base64
            result = response.json()
            image_data = result['artifacts'][0]['base64']
            image_url = f"data:image/png;base64,{image_data}"
            return {"success": True, "url": image_url}
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}