"""
====================================================================
IMAGE GENERATOR - T.VỸ-AI-SUPREME
====================================================================
Tạo ảnh từ văn bản bằng AI (miễn phí, không cần API key)
====================================================================
"""

import os
import requests
import base64
import json
import random
import hashlib
import datetime
from typing import Dict, Any, Optional

class ImageGenerator:
    def __init__(self):
        self.use_huggingface = True  # Dùng Hugging Face miễn phí
        self.hf_api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        self.hf_token = os.getenv("HF_TOKEN", "")  # Tùy chọn, không bắt buộc
        
    def generate_image(self, prompt: str, style: str = None, size: str = "512x512") -> Dict[str, Any]:
        """Tạo ảnh từ prompt văn bản"""
        if not prompt:
            return {"error": "Vui lòng nhập mô tả ảnh"}
        
        # Thêm style vào prompt
        enhanced_prompt = prompt
        if style:
            style_prompts = {
                "anime": "anime style, vibrant colors, detailed illustration",
                "realistic": "photorealistic, high quality, detailed, 8k",
                "painting": "oil painting, artistic, textured brushstrokes",
                "cartoon": "cartoon style, colorful, playful",
                "sketch": "sketch drawing, pencil art, black and white",
                "3d": "3d render, cinematic lighting, highly detailed"
            }
            if style in style_prompts:
                enhanced_prompt = f"{prompt}, {style_prompts[style]}"
        
        # Tạo ảnh
        if self.use_huggingface:
            result = self._generate_with_huggingface(enhanced_prompt)
        else:
            result = self._generate_local(enhanced_prompt)
        
        return result
    
    def _generate_with_huggingface(self, prompt: str) -> Dict[str, Any]:
        """Tạo ảnh qua Hugging Face Inference API (miễn phí)"""
        try:
            headers = {}
            if self.hf_token:
                headers["Authorization"] = f"Bearer {self.hf_token}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": "ugly, blurry, low quality, distorted",
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5
                }
            }
            
            response = requests.post(self.hf_api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                # Lưu ảnh
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"image_{timestamp}.png"
                filepath = os.path.join("static", "images", filename)
                os.makedirs("static/images", exist_ok=True)
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "image_url": f"/static/images/{filename}",
                    "filename": filename,
                    "prompt": prompt,
                    "message": "✅ Ảnh đã được tạo thành công!"
                }
            else:
                # Fallback: tạo ảnh giả lập
                return self._generate_fallback_image(prompt)
                
        except Exception as e:
            # Fallback: tạo ảnh giả lập
            return self._generate_fallback_image(prompt)
    
    def _generate_fallback_image(self, prompt: str) -> Dict[str, Any]:
        """Tạo ảnh giả lập khi API không hoạt động"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.svg"
        filepath = os.path.join("static", "images", filename)
        os.makedirs("static/images", exist_ok=True)
        
        # Tạo SVG từ prompt
        hash_val = hashlib.md5(prompt.encode()).hexdigest()[:6]
        color1 = f"#{hash_val[:3]}"
        color2 = f"#{hash_val[3:]}"
        
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
            <rect width="512" height="512" fill="{color1}"/>
            <circle cx="256" cy="256" r="150" fill="{color2}" opacity="0.7"/>
            <text x="256" y="256" text-anchor="middle" dominant-baseline="central" fill="white" font-size="24" font-weight="bold">🎨 {prompt[:20]}</text>
            <text x="256" y="300" text-anchor="middle" dominant-baseline="central" fill="white" font-size="14" opacity="0.7">T.VỸ-AI</text>
        </svg>'''
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
        
        return {
            "success": True,
            "image_url": f"/static/images/{filename}",
            "filename": filename,
            "prompt": prompt,
            "message": "🎨 Ảnh đã được tạo (dạng SVG) - Đang sử dụng chế độ dự phòng",
            "note": "Để có ảnh chất lượng cao, hãy đặt HF_TOKEN trong .env"
        }