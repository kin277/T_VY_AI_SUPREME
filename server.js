import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors'; 
import { GoogleGenAI, Type } from '@google/genai';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();
const app = express();

app.use(cors());
app.use(express.json());

// 🟢 1. PHỤC VỤ TÀI NGUYÊN FRONTEND
// Phục vụ thư mục public (chứa index.html, assets,...)
app.use(express.static(path.join(__dirname, 'frontend/public')));

// Bảo hiểm: Mở thêm đường dẫn /src trỏ tới frontend/src (nếu src nằm ngoài public)
app.use('/src', express.static(path.join(__dirname, 'frontend/src')));

// Khởi tạo Gemini AI Client
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

// ==========================================
// 1. ĐỊNH NGHĨA CÁC TOOL (GỌI API THỰC TẾ)
// ==========================================

async function getWeather({ location }) {
    try {
        console.log(`🔍 Đang tra cứu thời tiết thật cho: ${location}...`);
        const response = await fetch(`https://wttr.in/${encodeURIComponent(location)}?format=j1`);
        
        if (!response.ok) {
            return { error: `Không tìm thấy thông tin thời tiết cho địa điểm "${location}".` };
        }

        const data = await response.json();
        const current = data.current_condition[0];
        const conditionText = current.lang_vi?.[0]?.value || current.weatherDesc?.[0]?.value || "Không rõ";

        return {
            location: location,
            temperature: `${current.temp_C}°C`,
            feels_like: `${current.FeelsLikeC}°C`,
            condition: conditionText,
            humidity: `${current.humidity}%`,
            wind_speed: `${current.windspeedKmph} km/h`
        };
    } catch (error) {
        console.error("Lỗi khi gọi API thời tiết:", error);
        return { error: "Không thể kết nối đến máy chủ thời tiết lúc này." };
    }
}

const toolFunctions = { getWeather };

const weatherDeclaration = {
    name: 'getWeather',
    description: 'Lấy thông tin thời tiết hiện tại theo tên địa điểm thực tế',
    parameters: {
        type: Type.OBJECT,
        properties: {
            location: {
                type: Type.STRING,
                description: 'Tên thành phố hoặc tỉnh thành (VD: Hà Nội, TP.HCM, Đà Nẵng, Tokyo)',
            },
        },
        required: ['location'],
    },
};

const SYSTEM_INSTRUCTION = "Bạn là trợ lý AI thông minh. Hãy trả lời trực tiếp, đầy đủ câu hỏi của người dùng bằng tiếng Việt. Tuyệt đối không xuất các câu thoại chào mừng mô phỏng hay danh sách plugin.";

// 🟢 2. ROUTE KIỂM TRA TRẠNG THÁI SERVER (Đổi sang /health để không đè index.html)
app.get('/health', (req, res) => {
    res.send("🚀 Server Render đang hoạt động bình thường!");
});

// ==========================================
// 2. ROUTE /chat XỬ LÝ ĐA NĂNG
// ==========================================
app.post('/chat', async (req, res) => {
    try {
        const { message } = req.body;

        if (!message) {
            return res.status(400).json({ error: "Vui lòng nhập câu hỏi!" });
        }

        // Bước A: Gửi yêu cầu tới Gemini
        let response = await ai.models.generateContent({
            model: 'gemini-2.0-flash',
            contents: message,
            config: {
                systemInstruction: SYSTEM_INSTRUCTION,
                tools: [{ functionDeclarations: [weatherDeclaration] }],
            },
        });

        const functionCalls = response.functionCalls;
        let finalAnswer = response.text;

        // Bước B: Nếu có Function Call
        if (functionCalls && functionCalls.length > 0) {
            const call = functionCalls[0];
            const functionName = call.name;
            const functionArgs = call.args;

            console.log(`🤖 Gemini yêu cầu chạy Tool: ${functionName}`, functionArgs);

            if (toolFunctions[functionName]) {
                const toolResult = await toolFunctions[functionName](functionArgs);

                const secondResponse = await ai.models.generateContent({
                    model: 'gemini-2.0-flash',
                    contents: [
                        { role: 'user', parts: [{ text: message }] },
                        { role: 'model', parts: response.candidates[0].content.parts },
                        {
                            role: 'user',
                            parts: [{
                                functionResponse: {
                                    name: functionName,
                                    response: toolResult
                                }
                            }]
                        }
                    ],
                    config: { systemInstruction: SYSTEM_INSTRUCTION }
                });

                finalAnswer = secondResponse.text;
            }
        }

        return res.json({ 
            reply: finalAnswer,
            message: finalAnswer,
            text: finalAnswer 
        });

    } catch (error) {
        console.error("Lỗi khi xử lý Chat:", error);
        res.status(500).json({ error: "Có lỗi xảy ra khi xử lý phản hồi từ AI.", details: error.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Server đang chạy tại cổng ${PORT}`);
});