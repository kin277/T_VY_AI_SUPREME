require('dotenv').config(); // 1. Đọc cấu hình từ file .env khi chạy dưới local
const express = require('express');
const app = express();

app.use(express.json());
app.use(express.static('public')); // Chứa giao diện web

// 2. Lấy API Key từ Biến Môi Trường (không sợ bị lộ trên GitHub)
const HF_API_KEY = process.env.HF_API_KEY; 

// Model FLUX.1-schnell (Vẽ siêu nhanh & đẹp)
const MODEL_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell";

// Hàm tự động dịch mọi ngôn ngữ sang Tiếng Anh
async function translateToEnglish(text) {
    try {
        const response = await fetch(
            `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=autodetect|en`
        );
        const data = await response.json();
        
        if (data.responseData && data.responseData.translatedText) {
            return data.responseData.translatedText;
        }
        return text;
    } catch (error) {
        console.error("Lỗi dịch thuật:", error);
        return text;
    }
}

// Endpoint tạo ảnh
app.post('/api/generate-image', async (req, res) => {
    try {
        const { prompt } = req.body;
        if (!prompt) {
            return res.status(400).json({ error: 'Vui lòng nhập mô tả bức ảnh!' });
        }

        // Kiểm tra xem đã cài đặt API Key chưa
        if (!HF_API_KEY) {
            return res.status(500).json({ error: 'Chưa cấu hình HF_API_KEY trong Biến môi trường (Environment Variable)!' });
        }

        // 1. Dịch câu mô tả sang tiếng Anh
        const translatedPrompt = await translateToEnglish(prompt);
        console.log(`[T_VY_AI] Gốc: "${prompt}" -> Dịch: "${translatedPrompt}"`);

        // 2. Gửi request sang Hugging Face
        const hfResponse = await fetch(MODEL_URL, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${HF_API_KEY}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ inputs: translatedPrompt })
        });

        if (!hfResponse.ok) {
            const errorText = await hfResponse.text();
            throw new Error(`Hugging Face API lỗi: ${errorText}`);
        }

        // 3. Chuyển ảnh sang Base64
        const arrayBuffer = await hfResponse.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        const base64Image = `data:image/jpeg;base64,${buffer.toString('base64')}`;

        // 4. Trả kết quả về Frontend
        res.json({
            originalPrompt: prompt,
            translatedPrompt: translatedPrompt,
            image: base64Image
        });

    } catch (error) {
        console.error(error);
        res.status(500).json({ error: error.message || 'Lỗi hệ thống khi tạo ảnh.' });
    }
});

// 3. Sử dụng PORT động do Render cấp (hoặc mặc định 3000 ở local)
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 T_VY_AI Server đang chạy tại cổng: ${PORT}`);
});