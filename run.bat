@echo off
echo ============================================
echo  T.VỸ-AI-SUPREME - START
echo ============================================
cd /d E:\T_VY_AI_SUPREME

REM === SET BIẾN MÔI TRƯỜNG ===
set HF_HOME=E:\hf_cache
set HUGGINGFACE_HUB_CACHE=E:\hf_cache
set TRANSFORMERS_CACHE=E:\hf_cache
set HF_XET_HIGH_PERFORMANCE=1

echo 📁 Cache: %HF_HOME%
echo 🚀 Đang khởi động...
echo ============================================

REM === CHẠY SERVER ===
"C:\Users\Welcome\AppData\Local\Programs\Python\Python311\python.exe" app.py
pause