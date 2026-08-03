// ================================================================
// T.VỸ-AI-SUPREME - MAIN JS (FULL INTEGRATED & UPGRADED INTELLIGENCE v16.0)
// Dựa trên nền tảng gốc với hệ thống nhận dạng thông minh, tổng hợp web,
// Claude Artifacts, Perplexity Source Cards & Voice Mode Tiếng Việt
// ================================================================

// ===== DOM ELEMENTS =====
const chatContainer = document.getElementById('chatContainer');
const inputField = document.getElementById('inputField');
const sendBtn = document.getElementById('sendBtn');
const levelSelect = document.getElementById('levelSelect');
const levelBadge = document.getElementById('levelBadge');
const chatName = document.getElementById('chatName');
const searchInput = document.getElementById('searchInput');
const themeToggle = document.getElementById('themeToggle');
const logoutBtn = document.getElementById('logoutBtn');
const usageInfo = document.getElementById('usageInfo');
const exportBtn = document.getElementById('exportBtn');
const userAvatar = document.getElementById('userAvatar');
const userName = document.getElementById('userName');
const userStatus = document.getElementById('userStatus');

// ===== DOM BỔ SUNG CHO UPLOAD FILE & SIDEBAR =====
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
const sidebarToggle = document.getElementById('sidebarToggle') || document.getElementById('menuToggleSidebar');

// Tự động thêm Nút Dừng bên cạnh nút gửi (nếu chưa có trong HTML)
let stopBtn = document.getElementById('stopBtn');
if (sendBtn && !stopBtn) {
    stopBtn = document.createElement('button');
    stopBtn.id = 'stopBtn';
    stopBtn.innerHTML = '⏹ Dừng';
    stopBtn.style.display = 'none';
    stopBtn.className = sendBtn.className;
    stopBtn.onclick = stopGenerating;
    sendBtn.parentNode.insertBefore(stopBtn, sendBtn); 
}

// ===== DOM BỔ SUNG CHO VOICE MODE (NÚT MICRO) =====
let voiceBtn = document.getElementById('voiceBtn');
if (sendBtn && !voiceBtn) {
    voiceBtn = document.createElement('button');
    voiceBtn.id = 'voiceBtn';
    voiceBtn.type = 'button';
    voiceBtn.innerHTML = '🎤';
    voiceBtn.title = 'Bật/Tắt Nhận diện giọng nói Tiếng Việt';
    voiceBtn.className = sendBtn.className;
    voiceBtn.style.marginRight = '5px';
    voiceBtn.onclick = toggleVoiceRecognition;
    sendBtn.parentNode.insertBefore(voiceBtn, sendBtn);
}

// ===== STATE =====
let currentConversationId = null;
let currentLevel = 'pro';
let isDark = false;
let isLoggedIn = false;
let userData = null;
let socket = null;
let sessionTimer = null;
const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 giờ

// BIẾN QUẢN LÝ TRẠNG THÁI CHỜ & HỦY REQUEST
let isGenerating = false;
let currentAbortController = null;

// BIẾN QUẢN LÝ VOICE MODE & SPEECH RECOGNITION
let recognition = null;
let isListening = false;
let isVoiceTriggered = false;

const LEVEL_NAMES = {
    basic: 'AI Thường',
    pro: 'AI Pro',
    plus: 'AI Plus',
    pro3: 'AI 3.0 Pro'
};

// ================================================================
// QUẢN LÝ UI KHI ĐANG GENERATING (KHÓA/MỞ & DỪNG)
// ================================================================
function lockUI() {
    isGenerating = true;
    if (inputField) {
        inputField.disabled = true;
        inputField.placeholder = "Đang chờ AI phản hồi...";
    }
    if (sendBtn) sendBtn.style.display = 'none';
    if (stopBtn) stopBtn.style.display = 'inline-block';
}

function unlockUI() {
    isGenerating = false;
    if (inputField) {
        inputField.disabled = false;
        inputField.placeholder = "Nhập tin nhắn của bạn...";
        inputField.focus();
    }
    if (sendBtn) sendBtn.style.display = 'inline-block';
    if (stopBtn) stopBtn.style.display = 'none';
    hideTyping();
    hideDeepThink();
}

function stopGenerating() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
    unlockUI();
    addMessage('system', '⚠️ Đã dừng câu trả lời. Bạn có thể hỏi tiếp hoặc chỉnh sửa tin nhắn phía trên.');
}

// ================================================================
// TOGGLE SIDEBAR (CHỨC NĂNG ĐÓNG MỞ THANH BÊN)
// ================================================================
function toggleSidebar() {
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        sidebar.classList.toggle('closed');
        sidebar.classList.toggle('active');
    }
}

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', toggleSidebar);
}

// ================================================================
// MERMAID DIAGRAM INITIALIZATION
// ================================================================
if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
        startOnLoad: false,
        theme: isDark ? 'dark' : 'default',
        securityLevel: 'loose'
    });
}

function renderMermaidInContainer(container) {
    if (typeof mermaid === 'undefined') return;
    const mermaidBlocks = container.querySelectorAll('.mermaid-code');
    mermaidBlocks.forEach((block, idx) => {
        const code = block.textContent.trim();
        const id = `mermaid-svg-${Date.now()}-${Math.floor(Math.random() * 1000)}-${idx}`;
        const renderDiv = document.createElement('div');
        renderDiv.className = 'mermaid';
        renderDiv.id = id;

        try {
            mermaid.render(id + '-svg', code, (svgCode) => {
                renderDiv.innerHTML = svgCode;
                if (block.parentNode) {
                    block.parentNode.replaceChild(renderDiv, block);
                }
            });
        } catch (err) {
            console.error('Lỗi Render Mermaid Diagram:', err);
        }
    });
}

// ================================================================
// TÍNH NĂNG 1: CLAUDE ARTIFACTS - SPLIT SCREEN LIVE PREVIEW
// ================================================================
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function ensurePreviewPane() {
    let pane = document.getElementById('artifactPreviewPane');
    if (!pane) {
        pane = document.createElement('div');
        pane.id = 'artifactPreviewPane';
        pane.style.cssText = `
            position: fixed;
            top: 0;
            right: -50%;
            width: 50%;
            height: 100vh;
            background: var(--color-bg-secondary, #ffffff);
            border-left: 2px solid var(--color-border, #ccc);
            box-shadow: -5px 0 20px rgba(0,0,0,0.2);
            transition: right 0.3s ease-in-out;
            z-index: 99999;
            display: flex;
            flex-direction: column;
        `;
        pane.innerHTML = `
            <div style="padding: 12px 16px; background: var(--color-bg, #f8f9fa); border-bottom: 1px solid var(--color-border, #ccc); display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: var(--color-text, #333); font-size: 15px; display: flex; align-items: center; gap: 8px;">
                    👁️ Claude Artifact Live Preview
                </strong>
                <div style="display: flex; gap: 8px;">
                    <button onclick="refreshLivePreview()" style="padding: 6px 12px; background: var(--color-primary-light, #eef2ff); border: 1px solid var(--color-border, #ccc); border-radius: 4px; cursor: pointer; font-size: 13px; color: var(--color-text, #333);">🔄 Tải lại</button>
                    <button onclick="closeLivePreview()" style="padding: 6px 12px; background: #ff4d4f; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: bold;">✕ Đóng</button>
                </div>
            </div>
            <iframe id="artifactFrame" style="width: 100%; height: calc(100% - 50px); border: none; background: #ffffff;"></iframe>
        `;
        document.body.appendChild(pane);
    }
    return pane;
}

function openLivePreview(code) {
    ensurePreviewPane();
    const pane = document.getElementById('artifactPreviewPane');
    const frame = document.getElementById('artifactFrame');
    window.currentArtifactCode = code;
    pane.style.right = '0';

    // Đưa mã nguồn vào iframe thời gian thực
    frame.srcdoc = code;
}

function openLivePreviewById(artId) {
    const rawCode = window['artifact_code_' + artId];
    if (rawCode) {
        openLivePreview(rawCode);
    } else {
        showToast('❌ Không tìm thấy mã nguồn xem trước!', 'error');
    }
}

function refreshLivePreview() {
    const frame = document.getElementById('artifactFrame');
    if (frame && window.currentArtifactCode) {
        frame.srcdoc = window.currentArtifactCode;
        showToast('🔄 Đã làm mới giao diện Preview!', 'info');
    }
}

function closeLivePreview() {
    const pane = document.getElementById('artifactPreviewPane');
    if (pane) {
        pane.style.right = '-50%';
    }
}

// ================================================================
// TÍNH NĂNG 2: PERPLEXITY SOURCE CARDS (THẺ TRÍCH DẪN & FAVICON)
// ================================================================
function renderSourceCardsHtml(sources) {
    if (!sources || !Array.isArray(sources) || sources.length === 0) return '';

    let cardsHtml = `
        <div class="perplexity-sources-wrapper" style="margin-bottom: 14px; padding: 10px; background: var(--color-primary-light, rgba(74,110,224,0.08)); border-radius: 10px; border: 1px solid var(--color-border, #e4e7ec);">
            <div style="font-size: 0.82em; font-weight: 600; color: var(--color-text-secondary, #666); margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                🌐 Nguồn thông tin tổng hợp (${sources.length}):
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
    `;

    sources.forEach(source => {
        let url = source.url || '#';
        let title = source.title || source.name || 'Trang web';
        let domain = source.domain;
        if (!domain && url !== '#') {
            try { domain = new URL(url).hostname; } catch(e) { domain = 'website'; }
        }
        let favicon = source.favicon || `https://www.google.com/s2/favicons?domain=${domain || 'google.com'}&sz=32`;

        cardsHtml += `
            <a href="${url}" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; background: var(--color-bg-secondary, #ffffff); border: 1px solid var(--color-border, #d0d5dd); border-radius: 16px; font-size: 12px; color: var(--color-text, #101828); text-decoration: none; transition: all 0.2s;" onmouseover="this.style.borderColor='#4a6ee0';this.style.transform='translateY(-1px)'" onmouseout="this.style.borderColor='var(--color-border)';this.style.transform='none'">
                <img src="${favicon}" style="width: 14px; height: 14px; border-radius: 2px; object-fit: contain;" onerror="this.src='https://www.google.com/s2/favicons?domain=google.com'">
                <span style="max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500;">${escapeHtml(title)}</span>
            </a>
        `;
    });

    cardsHtml += `
            </div>
        </div>
    `;
    return cardsHtml;
}

// ================================================================
// TÍNH NĂNG 3: VOICE MODE (NHẬN DẠNG & ĐỌC PHẢN HỒI TIẾNG VIỆT)
// ================================================================
function initVoiceMode() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Trình duyệt không hỗ trợ Web Speech API.');
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'vi-VN';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = function() {
        isListening = true;
        if (voiceBtn) {
            voiceBtn.style.background = '#ff4d4f';
            voiceBtn.style.color = '#ffffff';
            voiceBtn.innerHTML = '🛑';
        }
        showToast('🎙️ Đang lắng nghe giọng nói Tiếng Việt...', 'info');
    };

    recognition.onresult = function(event) {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        if (inputField) {
            inputField.value = transcript;
        }
    };

    recognition.onend = function() {
        isListening = false;
        if (voiceBtn) {
            voiceBtn.style.background = '';
            voiceBtn.style.color = '';
            voiceBtn.innerHTML = '🎤';
        }

        // Tự động gửi tin nhắn sau khi nói xong
        if (inputField && inputField.value.trim().length > 0) {
            isVoiceTriggered = true;
            sendMessage();
        }
    };

    recognition.onerror = function(event) {
        isListening = false;
        if (voiceBtn) {
            voiceBtn.style.background = '';
            voiceBtn.style.color = '';
            voiceBtn.innerHTML = '🎤';
        }
        showToast('❌ Lỗi nhận dạng giọng nói: ' + event.error, 'error');
    };
}

function toggleVoiceRecognition() {
    if (!recognition) {
        initVoiceMode();
    }
    if (!recognition) {
        showToast('❌ Trình duyệt của bạn không hỗ trợ Nhận dạng Giọng nói!', 'error');
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        try {
            recognition.start();
        } catch(e) {
            recognition.stop();
        }
    }
}

function speakVietnamese(text) {
    if (!('speechSynthesis' in window)) return;
    
    // Hủy các giọng đọc đang phát dở
    window.speechSynthesis.cancel();

    // Lọc bỏ thẻ HTML và Markdown code trước khi đọc
    let cleanText = text
        .replace(/<[^>]*>/g, '')
        .replace(/```[\s\S]*?```/g, 'Mã nguồn chi tiết đã được hiển thị trên màn hình.')
        .replace(/[*#_`~]/g, '')
        .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'vi-VN';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Tìm giọng đọc tiếng Việt thích hợp nếu hệ thống hỗ trợ
    const voices = window.speechSynthesis.getVoices();
    const viVoice = voices.find(v => v.lang.includes('vi') || v.lang.includes('VI'));
    if (viVoice) {
        utterance.voice = viVoice;
    }

    window.speechSynthesis.speak(utterance);
}

// Khởi tạo Voice Mode ngay khi load script
initVoiceMode();

// ================================================================
// AUTH FUNCTIONS
// ================================================================
function switchAuthTab(tab) {
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (tab === 'login') {
        if (loginTab) loginTab.classList.add('active');
        if (registerTab) registerTab.classList.remove('active');
        if (loginForm) loginForm.style.display = 'block';
        if (registerForm) registerForm.style.display = 'none';
    } else {
        if (registerTab) registerTab.classList.add('active');
        if (loginTab) loginTab.classList.remove('active');
        if (registerForm) registerForm.style.display = 'block';
        if (loginForm) loginForm.style.display = 'none';
    }
}

function openLoginModal() {
    switchAuthTab('login');
    openModal('loginModal');
}

function openRegisterModal() {
    switchAuthTab('register');
    openModal('loginModal');
}

function checkLogin() {
    fetch('/api/auth/me')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showGuestMode();
                return;
            }
            userData = data;
            isLoggedIn = true;
            showUserMode(data);
            loadUsage();
            loadConversations();
            checkSessionTimeout();
        })
        .catch(() => {
            showGuestMode();
        });
}

function showGuestMode() {
    isLoggedIn = false;
    const authBtns = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');
    const upgradeReq = document.getElementById('upgradeRequired');

    if (authBtns) authBtns.style.display = 'flex';
    if (userInfo) userInfo.style.display = 'none';
    if (userName) userName.textContent = 'Khách';
    if (userAvatar) userAvatar.textContent = '👤';
    if (userStatus) userStatus.textContent = 'Chế độ khách';
    if (logoutBtn) logoutBtn.style.display = 'none';
    if (upgradeReq) upgradeReq.style.display = 'none';
    
    showToast('🔓 Bạn đang sử dụng chế độ Khách. Một số chức năng bị giới hạn.', 'info');
}

function showUserMode(user) {
    isLoggedIn = true;
    const authBtns = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');
    const headerUserName = document.getElementById('headerUserName');
    const headerUserRole = document.getElementById('headerUserRole');
    const upgradeReq = document.getElementById('upgradeRequired');

    if (authBtns) authBtns.style.display = 'none';
    if (userInfo) userInfo.style.display = 'flex';
    if (headerUserName) headerUserName.textContent = user.username || 'User';
    if (headerUserRole) headerUserRole.textContent = user.role === 'admin' ? 'Admin' : 'User';
    if (userName) userName.textContent = user.username || 'User';
    if (userAvatar) userAvatar.textContent = (user.username || 'U').charAt(0).toUpperCase();
    if (userStatus) userStatus.textContent = user.role === 'admin' ? '👑 Admin' : 'Đã đăng nhập';
    if (logoutBtn) logoutBtn.style.display = 'block';
    if (upgradeReq) upgradeReq.style.display = 'none';
}

function checkSessionTimeout() {
    if (sessionTimer) clearTimeout(sessionTimer);
    sessionTimer = setTimeout(() => {
        if (isLoggedIn) {
            showToast('⏰ Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.', 'warning');
            logout();
        }
    }, SESSION_TIMEOUT);
}

document.addEventListener('click', () => { if (isLoggedIn) checkSessionTimeout(); });
document.addEventListener('keydown', () => { if (isLoggedIn) checkSessionTimeout(); });

function requireAuth() {
    if (!isLoggedIn) {
        const upgradeReq = document.getElementById('upgradeRequired');
        if (upgradeReq) {
            upgradeReq.style.display = 'block';
            upgradeReq.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return false;
    }
    return true;
}

// ================================================================
// TOAST & THEME
// ================================================================
function showToast(message, type = 'info') {
    const existing = document.querySelector('.toast-message');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast-message ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function toggleTheme() {
    isDark = !isDark;
    const root = document.documentElement;
    if (isDark) {
        root.style.setProperty('--color-bg', '#1a1a2e');
        root.style.setProperty('--color-bg-secondary', '#2a2a4e');
        root.style.setProperty('--color-text', '#f0f0f0');
        root.style.setProperty('--color-text-secondary', '#b0b0c0');
        root.style.setProperty('--color-text-muted', '#8888aa');
        root.style.setProperty('--color-border', '#3a3a5e');
        root.style.setProperty('--color-primary-light', '#3a3a5e');
        if (themeToggle) themeToggle.textContent = '☀️';
    } else {
        root.style.setProperty('--color-bg', '#f8f9fa');
        root.style.setProperty('--color-bg-secondary', '#ffffff');
        root.style.setProperty('--color-text', '#1a1a2e');
        root.style.setProperty('--color-text-secondary', '#5a5a7a');
        root.style.setProperty('--color-text-muted', '#8a8aaa');
        root.style.setProperty('--color-border', '#e4e7ec');
        root.style.setProperty('--color-primary-light', '#eef2ff');
        if (themeToggle) themeToggle.textContent = '🌙';
    }
    localStorage.setItem('tv_theme', isDark ? 'dark' : 'light');

    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({ theme: isDark ? 'dark' : 'default' });
    }
}

if (localStorage.getItem('tv_theme') === 'dark') {
    toggleTheme();
}

if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

// ================================================================
// TOGGLE MENU & DÒNG SUY NGHĨ (DEEP THINK)
// ================================================================
function toggleMenu() {
    const menu = document.getElementById('functionMenu');
    if (menu) menu.classList.toggle('show');
}

document.addEventListener('click', function(event) {
    const menu = document.getElementById('functionMenu');
    const toggleBtn = document.getElementById('menuToggle');
    if (menu && toggleBtn) {
        if (!menu.contains(event.target) && !toggleBtn.contains(event.target)) {
            menu.classList.remove('show');
        }
    }
});

function showDeepThink(stage = 0) {
    if (!chatContainer) return;
    let thinkEl = document.getElementById('deepThinkIndicator');
    const stages = [
        '🧠 Đang phân tích yêu cầu & ngữ cảnh...',
        '🌐 Đang tổng hợp dữ liệu tìm kiếm web...',
        '💡 Đang tối ưu hóa mã nguồn và câu trả lời...'
    ];
    
    if (!thinkEl) {
        thinkEl = document.createElement('div');
        thinkEl.id = 'deepThinkIndicator';
        thinkEl.className = 'deep-think-box';
        thinkEl.style.padding = '10px 14px';
        thinkEl.style.margin = '10px 0';
        thinkEl.style.borderRadius = '8px';
        thinkEl.style.background = 'var(--color-primary-light)';
        thinkEl.style.color = 'var(--color-text)';
        thinkEl.style.fontSize = '0.9em';
        thinkEl.style.borderLeft = '4px solid #4a6ee0';
        chatContainer.appendChild(thinkEl);
    }
    thinkEl.innerHTML = `⚙️ <i>${stages[stage % stages.length]}</i>`;
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideDeepThink() {
    const el = document.getElementById('deepThinkIndicator');
    if (el) el.remove();
}

// ================================================================
// LOGIN / LOGOUT OAUTH
// ================================================================
function loginGoogle() {
    if (typeof firebase === 'undefined') return;
    const provider = new firebase.auth.GoogleAuthProvider();
    provider.addScope('email');
    provider.addScope('profile');

    showToast('⏳ Đang kết nối với Google...', 'info');

    firebase.auth().signInWithPopup(provider)
        .then((result) => {
            const user = result.user;
            return fetch('/api/auth/google', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: user.email,
                    name: user.displayName || user.email.split('@')[0],
                    id_token: user.accessToken
                })
            });
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast('✅ Đăng nhập thành công!', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showToast('❌ ' + (data.error || 'Đăng nhập thất bại'), 'error');
            }
        })
        .catch((error) => {
            console.error('Google login error:', error);
            if (error.code === 'auth/popup-closed-by-user') {
                showToast('⚠️ Bạn đã đóng cửa sổ đăng nhập', 'error');
            } else {
                showToast('❌ Lỗi: ' + error.message, 'error');
            }
        });
}

function loginFacebook() {
    if (typeof firebase === 'undefined') return;
    const provider = new firebase.auth.FacebookAuthProvider();
    provider.addScope('email');
    provider.addScope('public_profile');

    showToast('⏳ Đang kết nối với Facebook...', 'info');

    firebase.auth().signInWithPopup(provider)
        .then((result) => {
            const user = result.user;
            return fetch('/api/auth/facebook', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: user.email,
                    name: user.displayName || user.email.split('@')[0],
                    access_token: user.accessToken
                })
            });
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast('✅ Đăng nhập thành công!', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showToast('❌ ' + (data.error || 'Đăng nhập thất bại'), 'error');
            }
        })
        .catch((error) => {
            console.error('Facebook login error:', error);
            showToast('❌ Lỗi: ' + error.message, 'error');
        });
}

function loginGitHub() {
    const clientId = 'Ov23liwojcTDuo4p42aG';
    const redirectUri = window.location.origin + '/auth/github/callback';
    const scope = 'user:email';
    const url = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
    
    const width = 600;
    const height = 600;
    const left = (window.screen.width - width) / 2;
    const top = (window.screen.height - height) / 2;
    const popup = window.open(
        url,
        'github-auth',
        `width=${width},height=${height},left=${left},top=${top},scrollbars=yes`
    );
    
    showToast('⏳ Đang chuyển đến GitHub...', 'info');
    
    const checkPopup = setInterval(() => {
        if (popup && popup.closed) {
            clearInterval(checkPopup);
            setTimeout(() => {
                fetch('/api/auth/me')
                    .then(res => res.json())
                    .then(data => {
                        if (!data.error) location.reload();
                    });
            }, 500);
        }
    }, 500);
}

function logout() {
    if (!confirm('Đăng xuất?')) return;

    const signOutPromise = (typeof firebase !== 'undefined' && firebase.auth)
        ? firebase.auth().signOut()
        : Promise.resolve();

    signOutPromise
        .then(() => fetch('/api/auth/logout', { method: 'POST' }))
        .then(() => location.reload())
        .catch(error => {
            showToast('❌ Lỗi đăng xuất: ' + error.message, 'error');
        });
}

// ================================================================
// MODALS & SOCKET.IO
// ================================================================
function openModal(id) { document.getElementById(id)?.classList.add('active'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('active'); }

document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) this.classList.remove('active');
    });
});

function initSocket() {
    if (typeof io === 'undefined') return;
    socket = io();
    socket.on('connect', () => {
        console.log('✅ Connected to socket');
        socket.emit('join', { room: 'global' });
    });
    socket.on('new_message', (data) => {
        if (data.message && data.user_id !== userData?.id) {
            addMessage('ai', data.message, data.sources);
        }
    });
}

// ================================================================
// USAGE & NAVIGATION
// ================================================================
function loadUsage() {
    if (!levelSelect || !usageInfo) return;
    const tier = levelSelect.value;
    fetch(`/api/usage/${tier}`)
        .then(res => res.json())
        .then(data => {
            if (data.unlimited) {
                usageInfo.textContent = '♾️ Không giới hạn';
            } else if (data.remaining <= 0) {
                usageInfo.textContent = '⚠️ Hết lượt hôm nay';
            } else {
                usageInfo.textContent = `Lượt còn lại: ${data.remaining}/${data.max}`;
            }
        })
        .catch(() => {});
}

if (levelSelect) {
    levelSelect.addEventListener('change', function() {
        currentLevel = this.value;
        const name = LEVEL_NAMES[currentLevel] || 'AI Pro';
        if (levelBadge) levelBadge.textContent = name;
        if (chatName) chatName.textContent = name;
        loadUsage();
    });
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        this.classList.add('active');
        const tab = this.dataset.tab;
        if (tab === 'history') {
            openModal('historyModal');
            loadHistory();
        } else if (tab === 'settings') {
            openModal('settingsModal');
        } else if (tab === 'upgrade') {
            openModal('upgradeModal');
        } else if (tab === 'chat') {
            closeModal('historyModal');
            closeModal('settingsModal');
            closeModal('upgradeModal');
            if (inputField) inputField.focus();
        }
    });
});

// ================================================================
// ADD MESSAGE & EDIT/COPY CỦA NGƯỜI DÙNG & AI (NÂNG CẤP ARTIFACTS & SOURCES)
// ================================================================
function addMessage(role, content, sources = null) {
    if (!chatContainer) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper ' + role;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ' + role;
    
    // Tạo ID ngẫu nhiên cho từng block tin nhắn
    const msgId = 'msg-' + Math.random().toString(36).substr(2, 9);
    msgDiv.id = msgId;
    msgDiv.dataset.rawText = content; // Lưu dữ liệu thô vào dataset

    let formattedContent = content;

    // 1. CHUYỂN ĐỔI MERMAID DIAGRAM
    const mermaidRegex = /```mermaid\s*([\s\S]*?)\s*```/g;
    formattedContent = formattedContent.replace(mermaidRegex, (match, code) => {
        return `<pre class="mermaid-code">${code}</pre>`;
    });

    // 2. CHUYỂN ĐỔI ARTIFACTS (HTML/UI/SVG) LÀM NÚT XEM TRƯỚC LIVE PREVIEW
    if (role === 'ai') {
        const artifactRegex = /```(html|svg|xml)\s*([\s\S]*?)\s*```/gi;
        formattedContent = formattedContent.replace(artifactRegex, (match, lang, code) => {
            const artId = Math.random().toString(36).substr(2, 9);
            window['artifact_code_' + artId] = code;

            return `
                <div class="artifact-block" style="margin: 12px 0; border: 1px solid var(--color-border, #ccc); border-radius: 8px; overflow: hidden;">
                    <div style="background: #2a2a3e; color: #ffffff; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; font-size: 0.85em;">
                        <span>📄 Code Artifact (${lang.toUpperCase()})</span>
                        <button type="button" onclick="openLivePreviewById('${artId}')" style="background: #4a6ee0; color: white; border: none; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.85em;">
                            👁️ Xem trước Live Preview
                        </button>
                    </div>
                    <pre style="margin: 0; padding: 10px; background: var(--color-bg-secondary); overflow-x: auto;"><code>${escapeHtml(code)}</code></pre>
                </div>
            `;
        });
    }

    // 3. XỬ LÝ PERPLEXITY SOURCE CARDS Ở ĐẦU TIN NHẮN AI
    let sourcesHeader = '';
    if (role === 'ai' && sources) {
        sourcesHeader = renderSourceCardsHtml(sources);
    }

    if (role === 'user') {
        msgDiv.innerHTML = `
            <div class="msg-content" id="content-${msgId}">${formattedContent}</div>
            <div class="msg-actions" style="margin-top: 8px; font-size: 0.85em; display: flex; gap: 15px; opacity: 0.85;">
                <span style="cursor:pointer;" onclick="copyMessage('${msgId}')">📋 Copy</span>
                <span style="cursor:pointer;" onclick="editMessage('${msgId}')">✏️ Sửa</span>
            </div>
            <span class="time">${new Date().toLocaleTimeString()}</span>
        `;
    } else if (role === 'system') {
        msgDiv.innerHTML = `<div class="msg-content">${formattedContent}</div>`;
    } else {
        // Role AI
        msgDiv.innerHTML = `
            ${sourcesHeader}
            <div class="msg-content" id="content-${msgId}">${formattedContent}</div>
            <div class="msg-actions" style="margin-top: 8px; font-size: 0.85em; display: flex; gap: 15px; opacity: 0.85;">
                <span style="cursor:pointer;" onclick="copyMessage('${msgId}')">📋 Copy</span>
                <span style="cursor:pointer;" onclick="speakVietnamese(document.getElementById('content-${msgId}').innerText)">🔊 Đọc</span>
            </div>
            <span class="time">${new Date().toLocaleTimeString()}</span>
        `;
    }

    wrapper.appendChild(msgDiv);
    chatContainer.appendChild(wrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    renderMermaidInContainer(msgDiv);
}

// Chức năng Copy tin nhắn
function copyMessage(msgId) {
    const msgDiv = document.getElementById(msgId);
    if (msgDiv) {
        const textToCopy = msgDiv.dataset.rawText || msgDiv.innerText;
        navigator.clipboard.writeText(textToCopy).then(() => {
            showToast('✅ Đã copy tin nhắn vào khay nhớ tạm!', 'success');
        }).catch(err => {
            showToast('❌ Lỗi khi copy: ' + err, 'error');
        });
    }
}

// Chức năng chuyển sang giao diện Sửa
function editMessage(msgId) {
    if (isGenerating) {
        showToast('⚠️ Vui lòng đợi AI trả lời xong hoặc bấm "Dừng" trước khi sửa!', 'warning');
        return;
    }

    const msgDiv = document.getElementById(msgId);
    if (!msgDiv) return;
    
    const rawText = msgDiv.dataset.rawText;
    const contentDiv = document.getElementById(`content-${msgId}`);
    
    contentDiv.innerHTML = `
        <textarea id="edit-input-${msgId}" style="width: 100%; min-height: 80px; padding: 10px; margin-bottom: 8px; border-radius: 6px; border: 1px solid var(--color-border); background: var(--color-bg); color: var(--color-text); font-family: inherit; font-size: inherit; resize: vertical;">${rawText}</textarea>
        <div style="display: flex; gap: 8px;">
            <button onclick="saveEdit('${msgId}')" style="padding: 6px 12px; background: #4a6ee0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 13px;">Lưu & Gửi lại</button>
            <button onclick="cancelEdit('${msgId}')" style="padding: 6px 12px; background: transparent; color: var(--color-text); border: 1px solid var(--color-border); border-radius: 4px; cursor: pointer; font-size: 13px;">Hủy</button>
        </div>
    `;
    
    const actionsDiv = msgDiv.querySelector('.msg-actions');
    if (actionsDiv) actionsDiv.style.display = 'none'; // Ẩn tạm nút sửa/copy
}

// Hủy chỉnh sửa và quay về trạng thái cũ
function cancelEdit(msgId) {
    const msgDiv = document.getElementById(msgId);
    if (!msgDiv) return;
    const rawText = msgDiv.dataset.rawText;
    const contentDiv = document.getElementById(`content-${msgId}`);
    
    let formattedContent = rawText.replace(/```mermaid\s*([\s\S]*?)\s*```/g, (match, code) => {
        return `<pre class="mermaid-code">${code}</pre>`;
    });
    contentDiv.innerHTML = formattedContent;

    const actionsDiv = msgDiv.querySelector('.msg-actions');
    if (actionsDiv) actionsDiv.style.display = 'flex';
    renderMermaidInContainer(contentDiv);
}

// Lưu và gửi câu hỏi mới
function saveEdit(msgId) {
    const textarea = document.getElementById(`edit-input-${msgId}`);
    if (!textarea) return;
    const newText = textarea.value.trim();
    
    if (!newText) {
        showToast('❌ Nội dung không được để trống!', 'error');
        return;
    }

    const msgDiv = document.getElementById(msgId);
    msgDiv.dataset.rawText = newText; // Cập nhật data mới

    let formattedContent = newText.replace(/```mermaid\s*([\s\S]*?)\s*```/g, (match, code) => {
        return `<pre class="mermaid-code">${code}</pre>`;
    });
    document.getElementById(`content-${msgId}`).innerHTML = formattedContent;

    const actionsDiv = msgDiv.querySelector('.msg-actions');
    if (actionsDiv) actionsDiv.style.display = 'flex';
    renderMermaidInContainer(contentDiv);

    // XÓA TẤT CẢ CÁC TIN NHẮN SAU TIN NHẮN ĐANG SỬA
    let wrapper = msgDiv.parentElement;
    let nextWrapper = wrapper.nextElementSibling;
    while(nextWrapper) {
        let toRemove = nextWrapper;
        nextWrapper = nextWrapper.nextElementSibling;
        toRemove.remove();
    }

    // Gửi yêu cầu lại lên server
    sendMessageInternal(newText, true); 
}

// ================================================================
// UPLOAD & PHÂN TÍCH FILE
// ================================================================
function triggerFileUpload() {
    if (isGenerating) {
        showToast('⚠️ Vui lòng đợi AI xử lý xong trước khi tải file lên!', 'warning');
        return;
    }

    requireAuthAndExecute(() => {
        if (fileInput) {
            fileInput.click();
        } else {
            showToast('❌ Không tìm thấy phần tử upload file!', 'error');
        }
    });
}

if (uploadBtn) {
    uploadBtn.addEventListener('click', triggerFileUpload);
}

if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const allowedExts = ['.pdf', '.docx', '.txt'];
        const fileName = file.name.toLowerCase();
        const isValid = allowedExts.some(ext => fileName.endsWith(ext));

        if (!isValid) {
            showToast('❌ Chỉ hỗ trợ định dạng PDF, DOCX và TXT!', 'error');
            fileInput.value = '';
            return;
        }

        if (file.size > 15 * 1024 * 1024) {
            showToast('❌ Dung lượng file vượt quá 15MB!', 'error');
            fileInput.value = '';
            return;
        }

        addMessage('user', `📁 **Đã gửi tài liệu:** ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('conversation_id', currentConversationId || '');
        formData.append('level', levelSelect ? levelSelect.value : 'pro');
        formData.append('smart_synthesis', 'true');

        showTyping();
        lockUI();

        fetch('/api/upload_and_analyze', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            unlockUI();
            fileInput.value = '';

            if (data.error) {
                addMessage('ai', '❌ Lỗi phân tích file: ' + data.error);
                return;
            }

            if (data.conversation_id) {
                currentConversationId = data.conversation_id;
                if (exportBtn) exportBtn.style.display = 'inline-block';
            }

            addMessage('ai', `📑 **Kết quả phân tích tài liệu chuyên sâu (${file.name}):**\n\n${data.analysis || data.summary || data.message}`, data.sources);
            loadUsage();
        })
        .catch(err => {
            unlockUI();
            fileInput.value = '';
            addMessage('ai', '❌ Lỗi tải hoặc phân tích file: ' + err.message);
        });
    });
}

// ================================================================
// SEND MESSAGE (TÍCH HỢP VOICE READ-BACK & PERPLEXITY SOURCES)
// ================================================================
function sendMessage() {
    if (!inputField || isGenerating) return; 
    const text = inputField.value.trim();
    if (!text) return;

    if (!isLoggedIn) {
        showToast('🔒 Vui lòng đăng nhập để sử dụng chức năng này.', 'warning');
        const upgradeReq = document.getElementById('upgradeRequired');
        if (upgradeReq) {
            upgradeReq.style.display = 'block';
            upgradeReq.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }

    inputField.value = '';
    sendMessageInternal(text, false);
}

// Hàm xử lý trung tâm cho cả gửi lần đầu & gửi do Sửa câu hỏi
function sendMessageInternal(text, isResend = false) {
    if (!isResend) {
        addMessage('user', text);
    }

    const level = levelSelect ? levelSelect.value : 'pro';

    // Nhận dạng chính xác yêu cầu lập trình / phức tạp
    const isCodeRequest = /code|viết chương trình|script|function|class|html|css|javascript|python|java|c\+\+|c#|sql|sửa lỗi|debug|tạo ứng dụng|shader|tạo file|file/i.test(text);
    const isComplexQuery = text.length > 50 || /phân tích|so sánh|giải thích chi tiết|tổng hợp|nghiên cứu|chiến lược|tối ưu hóa/i.test(text);
    const requiresWebSynthesis = isCodeRequest || isComplexQuery;

    showTyping();
    showDeepThink(0);
    lockUI(); // Khóa UI và hiện Nút Dừng
    
    currentAbortController = new AbortController(); // Khởi tạo Controller ngắt kết nối

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: text,
            conversation_id: currentConversationId,
            level: level,
            intent_recognition: true,
            web_synthesis: requiresWebSynthesis,
            comprehensive_answer: true,
            full_code: true, 
            strict_code_focus: isCodeRequest, 
            no_ai_self_description: true,    
            direct_output_only: true,        
            auto_format_language: true,      
            ethical_safety_check: true,      
            untruncated_code: true           
        }),
        signal: currentAbortController.signal
    })
    .then(res => res.json())
    .then(data => {
        unlockUI();
        
        if (data.error) {
            addMessage('ai', '❌ ' + data.error);
            if (data.limit_reached) {
                openModal('upgradeModal');
            }
            return;
        }
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            if (exportBtn) exportBtn.style.display = 'inline-block';
        }
        
        const aiResponseText = data.message || 'Đã xử lý thành công.';
        const sourcesList = data.sources || data.web_sources || null;

        addMessage('ai', aiResponseText, sourcesList);

        // NẾU GỬI BẰNG PHƯƠNG THỨC NÓI -> TỰ ĐỘNG ĐỌC LẠI BẰNG TIẾNG VIỆT
        if (isVoiceTriggered) {
            speakVietnamese(aiResponseText);
            isVoiceTriggered = false; // Reset trạng thái
        }

        loadUsage();
        if (data.conversation_id) {
            fetch('/conversations')
                .then(r => r.json())
                .then(d => {
                    const conv = d.conversations?.find(c => c.id === data.conversation_id);
                    if (conv && chatName) chatName.textContent = conv.name || 'AI Pro';
                });
        }
    })
    .catch(err => {
        if (err.name === 'AbortError') {
            return; // Người dùng chủ động bấm Dừng, đã xử lý trong stopGenerating()
        }
        unlockUI();
        addMessage('ai', '❌ Lỗi kết nối: ' + err.message);
    });
}

if (sendBtn) sendBtn.addEventListener('click', sendMessage);
if (inputField) {
    inputField.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            if (e.shiftKey) return;
            e.preventDefault();
            sendMessage();
        }
    });
}

// ================================================================
// CONVERSATIONS & HISTORY
// ================================================================
function loadConversations() {
    fetch('/conversations')
        .then(res => res.json())
        .then(data => {
            const convs = data.conversations || [];
            const badge = document.querySelector('.nav-item[data-tab="history"] .badge');
            if (badge) badge.textContent = convs.length;
        })
        .catch(() => {});
}

function loadHistory() {
    const list = document.getElementById('historyList');
    if (!list) return;
    list.innerHTML = 'Đang tải...';

    fetch('/conversations')
        .then(res => res.json())
        .then(data => {
            const convs = data.conversations || [];
            if (convs.length === 0) {
                list.innerHTML = 'Chưa có đoạn chat nào.';
                return;
            }
            list.innerHTML = convs.map(c => `
                <div class="history-item" onclick="loadConversation('${c.id}')">
                    <span>${c.name}</span>
                    <span style="color:#8a8aaa;font-size:12px;">${new Date(c.updated_at || c.created_at).toLocaleString()}</span>
                    <button class="delete-btn" onclick="event.stopPropagation();deleteConversation('${c.id}')">✕</button>
                </div>
            `).join('');
        })
        .catch(() => list.innerHTML = 'Lỗi tải lịch sử.');
}

function loadConversation(id) {
    if (isGenerating) {
        showToast('Vui lòng đợi AI phản hồi xong trước khi chuyển phòng!', 'warning');
        return;
    }

    fetch(`/conversation/${id}`)
        .then(res => res.json())
        .then(data => {
            if (data.conversation) {
                const c = data.conversation;
                currentConversationId = c.id;
                if (chatContainer) chatContainer.innerHTML = '';
                c.messages.forEach(m => addMessage(m.role, m.content, m.sources));
                closeModal('historyModal');
                if (exportBtn) exportBtn.style.display = 'inline-block';
                if (c.level && levelSelect) {
                    levelSelect.value = c.level;
                    const name = LEVEL_NAMES[c.level] || 'AI Pro';
                    if (levelBadge) levelBadge.textContent = name;
                    if (chatName) chatName.textContent = c.name || name;
                    currentLevel = c.level;
                    loadUsage();
                }
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                const chatTab = document.querySelector('.nav-item[data-tab="chat"]');
                if (chatTab) chatTab.classList.add('active');
            }
        });
}

function deleteConversation(id) {
    if (!confirm('Xóa đoạn chat này?')) return;
    fetch(`/delete/${id}`, { method: 'DELETE' })
        .then(() => {
            if (id === currentConversationId) {
                currentConversationId = null;
                if (chatContainer) chatContainer.innerHTML = '';
                if (exportBtn) exportBtn.style.display = 'none';
                addMessage('ai', 'Đoạn chat mới đã được tạo. Hãy bắt đầu trò chuyện!');
                if (chatName) chatName.textContent = 'AI Pro';
            }
            loadHistory();
            loadConversations();
        });
}

// ================================================================
// EXPORT & SEARCH
// ================================================================
if (exportBtn) {
    exportBtn.addEventListener('click', function() {
        if (!currentConversationId) {
            showToast('Không có đoạn chat để xuất', 'error');
            return;
        }
        window.location.href = `/api/export/${currentConversationId}`;
    });
}

function searchMessages() {
    if (!searchInput) return;
    const keyword = searchInput.value.trim();
    if (!keyword) {
        document.querySelectorAll('.message').forEach(el => el.style.background = '');
        document.getElementById('searchResult')?.classList.remove('show');
        return;
    }

    const messages = document.querySelectorAll('.message');
    let found = 0;
    messages.forEach(msg => {
        const text = msg.textContent.toLowerCase();
        if (text.includes(keyword.toLowerCase())) {
            msg.style.background = '#fef3c7';
            msg.style.transition = 'background 0.3s';
            found++;
            if (found === 1) {
                msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else {
            msg.style.background = '';
        }
    });

    const resultEl = document.getElementById('searchResult');
    if (resultEl) {
        resultEl.textContent = `🔍 Tìm thấy ${found} kết quả cho "${keyword}"`;
        resultEl.classList.add('show');
        setTimeout(() => resultEl.classList.remove('show'), 4000);
    }
}

if (searchInput) {
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchMessages();
        }
    });
}

// ================================================================
// UPGRADE & PAYMENT
// ================================================================
function upgradeTier(tier) {
    if (!isLoggedIn) {
        showToast('🔒 Vui lòng đăng nhập để nâng cấp.', 'warning');
        openLoginModal();
        return;
    }

    const tierNames = { 'pro': 'Pro', 'plus': 'Plus', 'pro3': '3.0 Pro' };
    if (!confirm(`Xác nhận nâng cấp lên gói ${tierNames[tier]}?`)) return;

    fetch('/api/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: tier })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast('✅ ' + data.message, 'success');
            if (levelSelect) levelSelect.value = tier;
            const name = LEVEL_NAMES[tier] || 'AI Pro';
            if (levelBadge) levelBadge.textContent = name;
            if (chatName) chatName.textContent = name;
            currentLevel = tier;
            loadUsage();
            closeModal('upgradeModal');
        } else {
            showToast('❌ ' + data.error, 'error');
        }
    })
    .catch(() => showToast('❌ Lỗi kết nối', 'error'));
}

function upgradeWithMomo(tier) {
    if (!isLoggedIn) {
        showToast('🔒 Vui lòng đăng nhập để nâng cấp.', 'warning');
        openLoginModal();
        return;
    }

    const tierNames = { 'pro': 'Pro', 'plus': 'Plus', 'pro3': '3.0 Pro' };
    if (!confirm(`Xác nhận nâng cấp lên gói ${tierNames[tier]} qua MoMo?`)) return;

    fetch('/api/payment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: tier })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showToast('❌ ' + data.error, 'error');
            return;
        }
        if (data.payUrl) {
            window.open(data.payUrl, '_blank');
            showToast('⏳ Đang chuyển đến MoMo...', 'info');
        }
    })
    .catch(() => showToast('❌ Lỗi kết nối', 'error'));
}

// ================================================================
// SETTINGS & TYPING
// ================================================================
function saveSettings() {
    const darkMode = document.getElementById('darkModeToggle')?.checked;
    const lang = document.getElementById('langSelect')?.value;

    if (darkMode !== undefined && darkMode !== isDark) toggleTheme();
    if (lang) localStorage.setItem('tv_lang', lang);

    showToast('✅ Cài đặt đã được lưu!', 'success');
    closeModal('settingsModal');
}

function showTyping() {
    if (!chatContainer) return;
    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.id = 'typingIndicator';
    typing.style.display = 'block';
    typing.innerHTML = '<span></span><span></span><span></span>';
    chatContainer.appendChild(typing);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function hideTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

// ================================================================
// TOOLBAR FUNCTIONS (5 CHỨC NĂNG MỞ RỘNG)
// ================================================================
function requireAuthAndExecute(callback) {
    if (!isLoggedIn) {
        const upgradeReq = document.getElementById('upgradeRequired');
        if (upgradeReq) {
            upgradeReq.style.display = 'block';
            upgradeReq.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        showToast('🔒 Vui lòng đăng nhập để sử dụng chức năng này.', 'warning');
        return;
    }
    callback();
}

// CHỨC NĂNG 1: AI ĐA LUỒNG (MULTIPLE AI SYNTHESIS)
function useMultiAI() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập câu hỏi!', 'error');
            return;
        }
        addMessage('user', '🧠 Yêu cầu AI Đa luồng: ' + text);
        inputField.value = '';
        showTyping();
        lockUI();
        fetch('/api/multi_ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text, web_synthesis: true })
        })
        .then(res => res.json())
        .then(data => {
            unlockUI();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            let html = '🧠 **Kết quả AI Đa luồng (Đã tổng hợp web & nhận dạng tối ưu):**\n\n';
            if (data.results && Array.isArray(data.results)) {
                data.results.forEach(r => {
                    html += `📌 **${r.model}** (Độ chính xác: ${r.accuracy || 95}%):\n${r.response}\n\n`;
                });
            } else {
                html += data.message || 'Đã phân tích xong câu hỏi qua hệ thống đa luồng.';
            }
            if (data.best) {
                html += `🏆 **Kết quả tốt nhất:** ${data.best.model || data.best}`;
            }
            addMessage('ai', html, data.sources);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối AI Đa luồng'); });
    });
}

// CHỨC NĂNG 2: TÓM TẮT VĂN BẢN (TEXT SUMMARIZER)
function summarizeText() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập văn bản cần tóm tắt!', 'error');
            return;
        }
        addMessage('user', '📝 Yêu cầu tóm tắt: ' + text);
        inputField.value = '';
        showTyping();
        lockUI();
        fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, max_sentences: 5, smart_summary: true })
        })
        .then(res => res.json())
        .then(data => {
            unlockUI();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            const origLen = data.original_length || text.length;
            const sumLen = data.summarized_length || (data.summary ? data.summary.length : 0);
            addMessage('ai', `📝 **Tóm tắt chuyên sâu:**\n\n${data.summary}\n\n📊 Độ dài gốc: ${origLen} ký tự → ${sumLen} ký tự`, data.sources);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối dịch vụ tóm tắt'); });
    });
}

// CHỨC NĂNG 3: DỊCH THUẬT ĐA NGÔN NGỮ (MULTILINGUAL TRANSLATION)
function translateText() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập văn bản cần dịch!', 'error');
            return;
        }
        const lang = prompt('Nhập mã ngôn ngữ đích:\nvi (Tiếng Việt)\nen (English)\nko (한국어)\nja (日本語)\nzh (中文)\nfr (Français)\nde (Deutsch)\nes (Español)\nru (Русский)\nar (العربية)', 'en');
        if (!lang) return;
        addMessage('user', `🌐 Yêu cầu dịch sang [${lang}]: ${text}`);
        inputField.value = '';
        showTyping();
        lockUI();
        fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, lang: lang })
        })
        .then(res => res.json())
        .then(data => {
            unlockUI();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            addMessage('ai', `🌐 **Dịch chuẩn xác sang [${lang}]:**\n\n${data.translated}`);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối dịch thuật'); });
    });
}

// CHỨC NĂNG 4: TẠO VIDEO AI (AI VIDEO GENERATOR)
function generateVideo() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập mô tả kịch bản video!', 'error');
            return;
        }
        const template = prompt('Chọn thời lượng video:\nshort (15s)\nmedium (30s)\nlong (60s)', 'short');
        if (!template) return;
        addMessage('user', `🎬 Yêu cầu tạo video (${template}): ${text}`);
        inputField.value = '';
        showTyping();
        lockUI();
        fetch('/api/generate_video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: text, template: template, web_synthesis: true })
        })
        .then(res => res.json())
        .then(data => {
            unlockUI();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            addMessage('ai', `🎬 **Video AI đang khởi tạo thành công:**\n\n📌 Tiêu đề: ${data.title || text}\n⏱️ Thời lượng: ${data.duration || 15}s\n📐 Độ phân giải: ${data.resolution || '1080p'}\n🎨 Phong cách: ${data.style || 'Chân thực'}\n🔗 Link xem: <a href="${data.url || '#'}" target="_blank">Tải / Xem Video</a>\n\n⏳ Trạng thái: ${data.status || 'Hoàn tất'}`, data.sources);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối tạo video'); });
    });
}

// CHỨC NĂNG 5: PHÂN TÍCH DỮ LIỆU SỐ & TẠO NHẠC SUNO AI (DATA ANALYSIS & SUNO MUSIC)
function analyzeData() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập văn bản hoặc dải số cần phân tích!', 'error');
            return;
        }
        const numbers = text.split(',').map(n => parseFloat(n.trim())).filter(n => !isNaN(n));
        
        lockUI();
        if (numbers.length > 1) {
            addMessage('user', '📊 Yêu cầu phân tích dải số: ' + text);
            inputField.value = '';
            showTyping();
            fetch('/api/analyze_numbers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ numbers: numbers })
            })
            .then(res => res.json())
            .then(data => {
                unlockUI();
                if (data.error) {
                    addMessage('ai', '❌ ' + data.error);
                    return;
                }
                addMessage('ai', `📊 **Kết quả phân tích thống kê số liệu:**\n\n📌 Số lượng phần tử: ${data.count}\n📉 Giá trị nhỏ nhất (Min): ${data.min}\n📈 Giá trị lớn nhất (Max): ${data.max}\n📊 Giá trị trung bình (Mean): ${data.mean}\n📏 Trung vị (Median): ${data.median}\n📐 Tổng cộng (Sum): ${data.sum}`);
            })
            .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối phân tích dữ liệu số'); });
        } else {
            addMessage('user', '📊 Yêu cầu phân tích văn bản: ' + text);
            inputField.value = '';
            showTyping();
            fetch('/api/analyze_text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            })
            .then(res => res.json())
            .then(data => {
                unlockUI();
                if (data.error) {
                    addMessage('ai', '❌ ' + data.error);
                    return;
                }
                addMessage('ai', `📊 **Chỉ số phân tích cấu trúc văn bản:**\n\n📌 Tổng số từ: ${data.word_count}\n📝 Tổng số câu: ${data.sentence_count}\n📏 Độ dài trung bình của từ: ${data.avg_word_length}\n🔤 Số từ độc nhất: ${data.unique_words}\n📖 Đánh giá độ dễ đọc: ${data.readability}`);
            })
            .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối phân tích văn bản'); });
        }
    });
}

function generateMusicWithLyrics() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập chủ đề bài hát!', 'error');
            return;
        }
        const style = prompt('Chọn thể loại nhạc:\npop, rock, jazz, edm, classical, rap, ballad, v_pop, k_pop', 'v_pop');
        if (!style) return;
        const mood = prompt('Chọn tâm trạng:\nhappy, sad, romantic, epic, neutral', 'romantic');
        if (!mood) return;
        const duration = parseInt(prompt('Chọn độ dài bài hát (giây, tối đa 420s - 7 phút):', '60')) || 60;
        addMessage('user', `🎵 Yêu cầu tạo nhạc Suno AI (${style}, ${mood}, ${duration}s): ${text}`);
        inputField.value = '';
        showTyping();
        lockUI();
        fetch('/api/generate_music', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: text,
                style: style,
                mood: mood,
                duration: Math.min(duration, 420),
                web_synthesis: true
            })
        })
        .then(res => res.json())
        .then(data => {
            unlockUI();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            let html = `🎵 **Bài hát Suno AI đã được tạo thành công!**\n\n`;
            html += `📌 Thời lượng: ${data.duration || duration} giây\n`;
            html += `🎤 Thể loại: ${data.style || style}\n`;
            html += `🎭 Tâm trạng: ${data.mood || mood}\n`;
            html += `📦 Số đoạn ghép: ${data.num_segments || 1}\n\n`;
            html += `📝 **Lời bài hát:**\n${data.lyrics || 'Đã tạo xong giai điệu audio.'}\n\n`;
            if (data.download_url || data.music_file) {
                const link = data.download_url || `/static/audio/${data.music_file}`;
                html += `🔊 **Tải bản thu âm hoàn chỉnh:** <a href="${link}" download style="color:var(--color-primary);text-decoration:underline;">Tải File Nhạc MP3</a>`;
            }
            addMessage('ai', html, data.sources);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối máy chủ nhạc Suno AI'); });
    });
}

function clearAllMessages() {
    if (isGenerating) { showToast('Vui lòng đợi hệ thống xử lý xong!', 'warning'); return; }
    if (!confirm('Xóa toàn bộ tin nhắn trong chat hiện tại?')) return;
    if (chatContainer) chatContainer.innerHTML = '';
    addMessage('ai', '🗑️ Chat đã được xóa. Hãy bắt đầu trò chuyện mới!');
    currentConversationId = null;
    if (exportBtn) exportBtn.style.display = 'none';
}

// ================================================================
// INIT & KHỞI TẠO HỆ THỐNG
// ================================================================
checkLogin();
if (inputField) inputField.focus();

setInterval(() => {
    if (isLoggedIn) loadUsage();
}, 60000);

if (typeof io !== 'undefined') {
    initSocket();
}

console.log('🚀 T.VỸ-AI-SUPREME v16.0: Đã tích hợp trọn vẹn Claude Artifacts Live Preview, Perplexity Source Cards & Voice Mode Tiếng Việt!');
console.log('📌 Bản quyền tác giả: T.VỸ-VIP-FILE');