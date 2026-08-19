// Quản lý việc kết nối với máy chủ Backend hoặc Gemini API trực tiếp
export class ApiService {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async sendChatMessage(prompt, systemPrompt, config = {}, onStream = null) {
        const payload = {
            prompt,
            systemPrompt,
            temperature: config.temperature || 0.7,
            maxTokens: config.maxTokens || 2048,
            model: config.model || 'gemini-1.5-flash'
        };

        const response = await fetch(`${this.baseURL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Lỗi hệ thống');
        }

        return await response.json();
    }
}