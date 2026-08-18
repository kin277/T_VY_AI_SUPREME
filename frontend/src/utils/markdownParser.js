// Tách Code Artifacts và format Markdown tin nhắn AI
export function parseAiResponse(rawText) {
    // Regex tìm các đoạn mã HTML/CSS/JS để đưa vào Live Artifact Preview
    const artifactRegex = /```(html|css|javascript|js)([\s\S]*?)```/gi;
    let match;
    let artifacts = [];

    while ((match = artifactRegex.exec(rawText)) !== null) {
        artifacts.push({
            language: match[1],
            code: match[2].trim()
        });
    }

    return {
        formattedText: rawText, // Có thể kết hợp thư viện 'marked.js' ở đây
        artifacts
    };
}