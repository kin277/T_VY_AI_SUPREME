import express from 'express';
import dotenv from 'dotenv';
import { GoogleGenAI, Type } from '@google/genai';

dotenv.config();

const app = express();
app.use(express.json());

// Khởi tạo Gemini AI Client
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

// ==========================================
// 1. ĐỊNH NGHĨA CÁC TOOL (GỌI API THỰC TẾ)
// ==========================================

// Logic lấy thời tiết THỰC TẾ từ wttr.in
async function getWeather({ location }) {
    try {
        console.log(`🔍 Đang tra cứu thời tiết thật cho: ${location}...`);
        
        // Gọi API wttr.in (Trả về JSON format=j1)
        const response = await fetch(`https://wttr.in/${encodeURIComponent(location)}?format=j1`);
        
        if (!response.ok) {
            return { error: `Không tìm thấy thông tin thời tiết cho địa điểm "${location}".` };
        }

        const data = await response.json();
        const current = data.current_condition[0];

        // Ưu tiên lấy mô tả tiếng Việt nếu API hỗ trợ, không thì lấy tiếng Anh
        const conditionText = current.lang_vi?.[0]?.value || current.weatherDesc?.[0]?.value || "Không rõ";

        // Trả về dữ liệu thực tế cho Gemini suy luận
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

// Bảng ánh xạ hàm để Server tự gọi khi AI yêu cầu
const toolFunctions = {
    getWeather: getWeather
};

// Khai báo Schema Tool cho Gemini hiểu
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

// ==========================================
// 2. ROUTE /chat XỬ LÝ ĐA NĂNG
// ==========================================
app.post('/chat', async (req, res) => {
    try {
        const { message } = req.body;

        if (!message) {
            return res.status(400).json({ error: "Vui lòng nhập câu hỏi!" });
        }

        // Bước A: Gửi yêu cầu tới Gemini kèm danh sách Tools
        let response = await ai.models.generateContent({
            model: 'gemini-2.0-flash',
            contents: message,
            config: {
                tools: [{ functionDeclarations: [weatherDeclaration] }],
            },
        });

        // Bước B: Kiểm tra xem Gemini có yêu cầu gọi Tool không
        const functionCalls = response.functionCalls;

        if (functionCalls && functionCalls.length > 0) {
            const call = functionCalls[0];
            const functionName = call.name;
            const functionArgs = call.args;

            console.log(`🤖 Gemini yêu cầu chạy Tool: ${functionName}`, functionArgs);

            // Chạy hàm tương ứng trên Server
            if (toolFunctions[functionName]) {
                // Gọi API thực tế
                const toolResult = await toolFunctions[functionName](functionArgs);

                // Gửi kết quả dữ liệu thật về cho Gemini tổng hợp
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
                    ]
                });

                return res.json({ reply: secondResponse.text });
            }
        }

        // Nếu câu hỏi thông thường (không liên quan đến thời tiết), Gemini trả lời thẳng
        res.json({ reply: response.text });

    } catch (error) {
        console.error("Lỗi khi xử lý Chat:", error);
        res.status(500).json({ error: "Có lỗi xảy ra khi xử lý phản hồi từ AI." });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`🚀 Server đang chạy tại http://localhost:${PORT}`);
});