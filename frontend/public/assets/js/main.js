// ================================================================
// T.VỸ-AI-SUPREME - MAIN JS (FULL INTEGRATED & UPGRADED INTELLIGENCE)
// Dựa trên nền tảng gốc với hệ thống nhận dạng thông minh & tổng hợp web toàn diện cho mọi cấp độ AI
// CẬP NHẬT: Thêm tính năng Chặn input khi chờ, Nút Dừng, Copy & Edit tin nhắn chuẩn xác.
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
// TOGGLE MENU & DÒNG SUY NGHĨ
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

function showDeepThink(stage = 0) {}
function hideDeepThink() {}

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
            addMessage('ai', data.message);
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
// ADD MESSAGE & EDIT/COPY CỦA NGƯỜI DÙNG & AI
// ================================================================
function addMessage(role, content) {
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
    const mermaidRegex = /```mermaid\s*([\s\S]*?)\s*```/g;
    formattedContent = formattedContent.replace(mermaidRegex, (match, code) => {
        return `<pre class="mermaid-code">${code}</pre>`;
    });

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
            <div class="msg-content" id="content-${msgId}">${formattedContent}</div>
            <div class="msg-actions" style="margin-top: 8px; font-size: 0.85em; display: flex; gap: 15px; opacity: 0.85;">
                <span style="cursor:pointer;" onclick="copyMessage('${msgId}')">📋 Copy</span>
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
    renderMermaidInContainer(msgDiv);

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

            addMessage('ai', `📑 **Kết quả phân tích tài liệu chuyên sâu (${file.name}):**\n\n${data.analysis || data.summary || data.message}`);
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
// SEND MESSAGE (NÂNG CẤP CHẶN, CANCEL & EDIT TRUYỀN LẠI)
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
        addMessage('ai', data.message || 'Đã xử lý thành công.');
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
                c.messages.forEach(m => addMessage(m.role, m.content));
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
// TOOLBAR FUNCTIONS
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
            data.results.forEach(r => {
                html += `📌 **${r.model}** (Độ chính xác: ${r.accuracy}%):\n${r.response}\n\n`;
            });
            html += `🏆 **Kết quả tốt nhất:** ${data.best.model}`;
            addMessage('ai', html);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

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
            addMessage('ai', `📝 **Tóm tắt chuyên sâu:**\n\n${data.summary}\n\n📊 Độ dài gốc: ${data.original_length} ký tự → ${data.summarized_length} ký tự`);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

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
        addMessage('user', `🌐 Yêu cầu dịch sang ${lang}: ${text}`);
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
            addMessage('ai', `🌐 **Dịch chuẩn xác sang ${lang}:**\n\n${data.translated}`);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

function generateVideo() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập mô tả video!', 'error');
            return;
        }
        const template = prompt('Chọn loại video:\nshort (15s)\nmedium (30s)\nlong (60s)', 'short');
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
            addMessage('ai', `🎬 **Video đang được tạo:**\n\n📌 Tiêu đề: ${data.title}\n⏱️ Thời lượng: ${data.duration}s\n📐 Độ phân giải: ${data.resolution}\n🎨 Phong cách: ${data.style}\n🔗 Link: ${data.url}\n\n⏳ Trạng thái: ${data.status}`);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

function analyzeData() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập văn bản hoặc số cần phân tích!', 'error');
            return;
        }
        const numbers = text.split(',').map(n => parseFloat(n.trim())).filter(n => !isNaN(n));
        
        lockUI();
        if (numbers.length > 1) {
            addMessage('user', '📊 Yêu cầu phân tích số: ' + text);
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
                addMessage('ai', `📊 **Phân tích dữ liệu số:**\n\n📌 Số lượng: ${data.count}\n📉 Nhỏ nhất: ${data.min}\n📈 Lớn nhất: ${data.max}\n📊 Trung bình: ${data.mean}\n📏 Trung vị: ${data.median}\n📐 Tổng: ${data.sum}`);
            })
            .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối'); });
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
                addMessage('ai', `📊 **Phân tích văn bản:**\n\n📌 Số từ: ${data.word_count}\n📝 Số câu: ${data.sentence_count}\n📏 Độ dài trung bình từ: ${data.avg_word_length}\n🔤 Số từ độc nhất: ${data.unique_words}\n📖 Độ dễ đọc: ${data.readability}`);
            })
            .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối'); });
        }
    });
}

function generateMusicWithLyrics() {
    if (isGenerating) { showToast('⚠️ Đang chờ AI phản hồi...', 'warning'); return; }
    requireAuthAndExecute(() => {
        const text = inputField ? inputField.value.trim() : '';
        if (!text) {
            showToast('Vui lòng nhập mô tả bài hát!', 'error');
            return;
        }
        const style = prompt('Chọn thể loại:\npop, rock, jazz, edm, classical, rap, ballad, v_pop, k_pop', 'pop');
        if (!style) return;
        const mood = prompt('Chọn tâm trạng:\nhappy, sad, romantic, epic, neutral', 'happy');
        if (!mood) return;
        const duration = parseInt(prompt('Chọn độ dài (giây, tối đa 420 - 7 phút):', '60')) || 60;
        addMessage('user', `🎵 Yêu cầu tạo nhạc (${style}, ${mood}, ${duration}s): ${text}`);
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
            let html = `🎵 **Bài hát đã được tạo!**\n\n`;
            html += `📌 Thời lượng: ${data.duration} giây\n`;
            html += `🎤 Thể loại: ${data.style}\n`;
            html += `🎭 Tâm trạng: ${data.mood}\n`;
            html += `📦 Số đoạn ghép: ${data.num_segments || 1}\n\n`;
            html += `📝 Lời bài hát:\n${data.lyrics}\n\n`;
            html += `🔊 Tải nhạc: <a href="${data.download_url}" download style="color:var(--color-primary);text-decoration:underline;">${data.music_file}</a>`;
            addMessage('ai', html);
        })
        .catch(() => { unlockUI(); addMessage('ai', '❌ Lỗi kết nối'); });
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
// INIT
// ================================================================
checkLogin();
if (inputField) inputField.focus();

setInterval(() => {
    if (isLoggedIn) loadUsage();
}, 60000);

if (typeof io !== 'undefined') {
    initSocket();
}

console.log('🚀 T.VỸ-AI-SUPREME v15.0: Nâng cấp luồng hội thoại & giao diện chống spam hoàn hảo!');
console.log('📌 Bản quyền: T.VỸ-VIP-FILE');