// ================================================================
// T.VỸ-AI-SUPREME - MAIN JS (HOÀN CHỈNH)
// ================================================================

// ===== DOM =====
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

// ===== STATE =====
let currentConversationId = null;
let currentLevel = 'pro';
let isDark = false;
let isLoggedIn = false;
let userData = null;
let socket = null;
let sessionTimer = null;
const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 giờ

const LEVEL_NAMES = {
    basic: 'AI Thường',
    pro: 'AI Pro',
    plus: 'AI Plus',
    pro3: 'AI 3.0 Pro'
};

// ================================================================
// AUTH FUNCTIONS
// ================================================================

// ===== SWITCH AUTH TAB =====
function switchAuthTab(tab) {
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (tab === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
    } else {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.style.display = 'block';
        loginForm.style.display = 'none';
    }
}

// ===== OPEN LOGIN/REGISTER =====
function openLoginModal() {
    switchAuthTab('login');
    openModal('loginModal');
}

function openRegisterModal() {
    switchAuthTab('register');
    openModal('loginModal');
}

// ===== CHECK LOGIN =====
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
    document.getElementById('authButtons').style.display = 'flex';
    document.getElementById('userInfo').style.display = 'none';
    userName.textContent = 'Khách';
    userAvatar.textContent = '👤';
    userStatus.textContent = 'Chế độ khách';
    logoutBtn.style.display = 'none';
    document.getElementById('upgradeRequired').style.display = 'none';
    showToast('🔓 Bạn đang sử dụng chế độ Khách. Một số chức năng bị giới hạn.', 'info');
}

function showUserMode(user) {
    isLoggedIn = true;
    document.getElementById('authButtons').style.display = 'none';
    document.getElementById('userInfo').style.display = 'flex';
    document.getElementById('headerUserName').textContent = user.username || 'User';
    document.getElementById('headerUserRole').textContent = user.role === 'admin' ? 'Admin' : 'User';
    userName.textContent = user.username || 'User';
    userAvatar.textContent = (user.username || 'U').charAt(0).toUpperCase();
    userStatus.textContent = user.role === 'admin' ? '👑 Admin' : 'Đã đăng nhập';
    logoutBtn.style.display = 'block';
    document.getElementById('upgradeRequired').style.display = 'none';
}

// ===== SESSION TIMEOUT =====
function checkSessionTimeout() {
    if (sessionTimer) clearTimeout(sessionTimer);
    sessionTimer = setTimeout(() => {
        if (isLoggedIn) {
            showToast('⏰ Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.', 'warning');
            logout();
        }
    }, SESSION_TIMEOUT);
}

// Refresh session khi có hoạt động
document.addEventListener('click', () => {
    if (isLoggedIn) checkSessionTimeout();
});
document.addEventListener('keydown', () => {
    if (isLoggedIn) checkSessionTimeout();
});

// ===== CHECK IF FUNCTION IS ALLOWED =====
function requireAuth() {
    if (!isLoggedIn) {
        document.getElementById('upgradeRequired').style.display = 'block';
        document.getElementById('upgradeRequired').scrollIntoView({ behavior: 'smooth', block: 'center' });
        return false;
    }
    return true;
}

// ================================================================
// TOAST
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

// ================================================================
// THEME
// ================================================================
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
        themeToggle.textContent = '☀️';
    } else {
        root.style.setProperty('--color-bg', '#f8f9fa');
        root.style.setProperty('--color-bg-secondary', '#ffffff');
        root.style.setProperty('--color-text', '#1a1a2e');
        root.style.setProperty('--color-text-secondary', '#5a5a7a');
        root.style.setProperty('--color-text-muted', '#8a8aaa');
        root.style.setProperty('--color-border', '#e4e7ec');
        root.style.setProperty('--color-primary-light', '#eef2ff');
        themeToggle.textContent = '🌙';
    }
    localStorage.setItem('tv_theme', isDark ? 'dark' : 'light');
}

if (localStorage.getItem('tv_theme') === 'dark') {
    isDark = true;
    document.documentElement.style.setProperty('--color-bg', '#1a1a2e');
    document.documentElement.style.setProperty('--color-bg-secondary', '#2a2a4e');
    document.documentElement.style.setProperty('--color-text', '#f0f0f0');
    document.documentElement.style.setProperty('--color-text-secondary', '#b0b0c0');
    document.documentElement.style.setProperty('--color-text-muted', '#8888aa');
    document.documentElement.style.setProperty('--color-border', '#3a3a5e');
    document.documentElement.style.setProperty('--color-primary-light', '#3a3a5e');
    themeToggle.textContent = '☀️';
}

themeToggle.addEventListener('click', toggleTheme);

// ================================================================
// TOGGLE MENU
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

// ================================================================
// DEEP THINK
// ================================================================
function showDeepThink(stage = 0) {
    const indicator = document.getElementById('deepThinkIndicator');
    const status = document.getElementById('thinkStatus');
    if (!indicator || !status) return;

    const stages = [
        "🔍 Đang phân tích câu hỏi...",
        "📚 Tìm kiếm kiến thức liên quan...",
        "🧠 Xây dựng lập luận...",
        "✍️ Tổng hợp câu trả lời..."
    ];

    indicator.style.display = 'block';
    status.textContent = stages[Math.min(stage, stages.length - 1)] || stages[0];
}

function hideDeepThink() {
    const indicator = document.getElementById('deepThinkIndicator');
    if (indicator) indicator.style.display = 'none';
}

// ================================================================
// LOGIN / LOGOUT
// ================================================================
function loginGoogle() {
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

// ===== GITHUB LOGIN =====
function loginGitHub() {
    const clientId = 'Ov23liwojcTDuo4p42aG';
    const redirectUri = window.location.origin + '/auth/github/callback';
    const scope = 'user:email';
    const url = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}`;
    
    // Mở popup
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
    
    // Kiểm tra popup đóng
    const checkPopup = setInterval(() => {
        if (popup && popup.closed) {
            clearInterval(checkPopup);
            // Reload trang sau khi popup đóng
            setTimeout(() => {
                fetch('/api/auth/me')
                    .then(res => res.json())
                    .then(data => {
                        if (!data.error) {
                            location.reload();
                        }
                    });
            }, 500);
        }
    }, 500);
}

function logout() {
    if (!confirm('Đăng xuất?')) return;

    firebase.auth().signOut()
        .then(() => {
            return fetch('/api/auth/logout', { method: 'POST' });
        })
        .then(() => {
            location.reload();
        })
        .catch(error => {
            showToast('❌ Lỗi đăng xuất: ' + error.message, 'error');
        });
}

// ================================================================
// MODALS
// ================================================================
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) this.classList.remove('active');
    });
});

// ================================================================
// SOCKET.IO
// ================================================================
function initSocket() {
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
// USAGE
// ================================================================
function loadUsage() {
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

levelSelect.addEventListener('change', function() {
    currentLevel = this.value;
    const name = LEVEL_NAMES[currentLevel] || 'AI Pro';
    levelBadge.textContent = name;
    chatName.textContent = name;
    loadUsage();
});

// ================================================================
// NAVIGATION
// ================================================================
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
            inputField.focus();
        }
    });
});

// ================================================================
// SEND MESSAGE
// ================================================================
function sendMessage() {
    const text = inputField.value.trim();
    if (!text) return;

    if (!isLoggedIn) {
        showToast('🔒 Vui lòng đăng nhập để sử dụng chức năng này.', 'warning');
        document.getElementById('upgradeRequired').style.display = 'block';
        document.getElementById('upgradeRequired').scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
    }

    addMessage('user', text);
    inputField.value = '';

    const level = levelSelect.value;

    showTyping();
    showDeepThink(0);

    setTimeout(() => showDeepThink(1), 800);
    setTimeout(() => showDeepThink(2), 1600);
    setTimeout(() => showDeepThink(3), 2400);

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: text,
            conversation_id: currentConversationId,
            level: level
        })
    })
    .then(res => res.json())
    .then(data => {
        hideTyping();
        hideDeepThink();
        if (data.error) {
            addMessage('ai', '❌ ' + data.error);
            if (data.limit_reached) {
                openModal('upgradeModal');
            }
            return;
        }
        if (data.conversation_id) {
            currentConversationId = data.conversation_id;
            exportBtn.style.display = 'inline-block';
        }
        addMessage('ai', data.message || 'Đã xử lý thành công.');
        loadUsage();
        if (data.conversation_id) {
            fetch('/conversations')
                .then(r => r.json())
                .then(d => {
                    const conv = d.conversations?.find(c => c.id === data.conversation_id);
                    if (conv) chatName.textContent = conv.name || 'AI Pro';
                });
        }
    })
    .catch(err => {
        hideTyping();
        hideDeepThink();
        addMessage('ai', '❌ Lỗi kết nối: ' + err.message);
    });
}

sendBtn.addEventListener('click', sendMessage);
inputField.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

// ================================================================
// ADD MESSAGE
// ================================================================
function addMessage(role, content) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper ' + role;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ' + role;
    msgDiv.innerHTML = content + `<span class="time">${new Date().toLocaleTimeString()}</span>`;

    wrapper.appendChild(msgDiv);
    chatContainer.appendChild(wrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ================================================================
// CONVERSATIONS
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

// ================================================================
// HISTORY
// ================================================================
function loadHistory() {
    const list = document.getElementById('historyList');
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
    fetch(`/conversation/${id}`)
        .then(res => res.json())
        .then(data => {
            if (data.conversation) {
                const c = data.conversation;
                currentConversationId = c.id;
                chatContainer.innerHTML = '';
                c.messages.forEach(m => addMessage(m.role, m.content));
                closeModal('historyModal');
                exportBtn.style.display = 'inline-block';
                if (c.level) {
                    levelSelect.value = c.level;
                    const name = LEVEL_NAMES[c.level] || 'AI Pro';
                    levelBadge.textContent = name;
                    chatName.textContent = c.name || name;
                    currentLevel = c.level;
                    loadUsage();
                }
                document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
                document.querySelector('.nav-item[data-tab="chat"]').classList.add('active');
            }
        });
}

function deleteConversation(id) {
    if (!confirm('Xóa đoạn chat này?')) return;
    fetch(`/delete/${id}`, { method: 'DELETE' })
        .then(() => {
            if (id === currentConversationId) {
                currentConversationId = null;
                chatContainer.innerHTML = '';
                exportBtn.style.display = 'none';
                addMessage('ai', 'Đoạn chat mới đã được tạo. Hãy bắt đầu trò chuyện!');
                chatName.textContent = 'AI Pro';
            }
            loadHistory();
            loadConversations();
        });
}

// ================================================================
// EXPORT CHAT
// ================================================================
exportBtn.addEventListener('click', function() {
    if (!currentConversationId) {
        showToast('Không có đoạn chat để xuất', 'error');
        return;
    }
    window.location.href = `/api/export/${currentConversationId}`;
});

// ================================================================
// SEARCH MESSAGES
// ================================================================
function searchMessages() {
    const keyword = searchInput.value.trim();
    if (!keyword) {
        document.querySelectorAll('.message').forEach(el => el.style.background = '');
        document.getElementById('searchResult').classList.remove('show');
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
    resultEl.textContent = `🔍 Tìm thấy ${found} kết quả cho "${keyword}"`;
    resultEl.classList.add('show');
    setTimeout(() => resultEl.classList.remove('show'), 4000);
}

searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        searchMessages();
    }
});

// ================================================================
// UPGRADE
// ================================================================
function upgradeTier(tier) {
    if (!isLoggedIn) {
        showToast('🔒 Vui lòng đăng nhập để nâng cấp.', 'warning');
        openLoginModal();
        return;
    }

    const tierNames = {
        'pro': 'Pro',
        'plus': 'Plus',
        'pro3': '3.0 Pro'
    };

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
            levelSelect.value = tier;
            const name = LEVEL_NAMES[tier] || 'AI Pro';
            levelBadge.textContent = name;
            chatName.textContent = name;
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

    const tierNames = {
        'pro': 'Pro',
        'plus': 'Plus',
        'pro3': '3.0 Pro'
    };

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
// SETTINGS
// ================================================================
function saveSettings() {
    const darkMode = document.getElementById('darkModeToggle').checked;
    const lang = document.getElementById('langSelect').value;

    if (darkMode !== isDark) toggleTheme();
    localStorage.setItem('tv_lang', lang);

    showToast('✅ Cài đặt đã được lưu!', 'success');
    closeModal('settingsModal');
}

// ================================================================
// TYPING INDICATOR
// ================================================================
function showTyping() {
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
// TOOLBAR FUNCTIONS (CÓ KIỂM TRA ĐĂNG NHẬP)
// ================================================================

function requireAuthAndExecute(callback) {
    if (!isLoggedIn) {
        document.getElementById('upgradeRequired').style.display = 'block';
        document.getElementById('upgradeRequired').scrollIntoView({ behavior: 'smooth', block: 'center' });
        showToast('🔒 Vui lòng đăng nhập để sử dụng chức năng này.', 'warning');
        return;
    }
    callback();
}

function useMultiAI() {
    requireAuthAndExecute(() => {
        const text = inputField.value.trim();
        if (!text) {
            showToast('Vui lòng nhập câu hỏi!', 'error');
            return;
        }
        addMessage('user', '🧠 Yêu cầu AI Đa luồng: ' + text);
        inputField.value = '';
        showTyping();
        fetch('/api/multi_ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text })
        })
        .then(res => res.json())
        .then(data => {
            hideTyping();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            let html = '🧠 **Kết quả AI Đa luồng:**\n\n';
            data.results.forEach(r => {
                html += `📌 **${r.model}** (Độ chính xác: ${r.accuracy}%):\n${r.response}\n\n`;
            });
            html += `🏆 **Kết quả tốt nhất:** ${data.best.model}`;
            addMessage('ai', html);
        })
        .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

function summarizeText() {
    requireAuthAndExecute(() => {
        const text = inputField.value.trim();
        if (!text) {
            showToast('Vui lòng nhập văn bản cần tóm tắt!', 'error');
            return;
        }
        addMessage('user', '📝 Yêu cầu tóm tắt: ' + text);
        inputField.value = '';
        showTyping();
        fetch('/api/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, max_sentences: 5 })
        })
        .then(res => res.json())
        .then(data => {
            hideTyping();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            addMessage('ai', `📝 **Tóm tắt:**\n\n${data.summary}\n\n📊 Độ dài gốc: ${data.original_length} ký tự → ${data.summarized_length} ký tự`);
        })
        .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

function translateText() {
    requireAuthAndExecute(() => {
        const text = inputField.value.trim();
        if (!text) {
            showToast('Vui lòng nhập văn bản cần dịch!', 'error');
            return;
        }
        const lang = prompt('Nhập mã ngôn ngữ đích:\nvi (Tiếng Việt)\nen (English)\nko (한국어)\nja (日本語)\nzh (中文)\nfr (Français)\nde (Deutsch)\nes (Español)\nru (Русский)\nar (العربية)', 'en');
        if (!lang) return;
        addMessage('user', `🌐 Yêu cầu dịch sang ${lang}: ${text}`);
        inputField.value = '';
        showTyping();
        fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, lang: lang })
        })
        .then(res => res.json())
        .then(data => {
            hideTyping();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            addMessage('ai', `🌐 **Dịch sang ${lang}:**\n\n${data.translated}`);
        })
        .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

function generateVideo() {
    requireAuthAndExecute(() => {
        const text = inputField.value.trim();
        if (!text) {
            showToast('Vui lòng nhập mô tả video!', 'error');
            return;
        }
        const template = prompt('Chọn loại video:\nshort (15s)\nmedium (30s)\nlong (60s)', 'short');
        if (!template) return;
        addMessage('user', `🎬 Yêu cầu tạo video (${template}): ${text}`);
        inputField.value = '';
        showTyping();
        fetch('/api/generate_video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: text, template: template })
        })
        .then(res => res.json())
        .then(data => {
            hideTyping();
            if (data.error) {
                addMessage('ai', '❌ ' + data.error);
                return;
            }
            addMessage('ai', `🎬 **Video đang được tạo:**\n\n📌 Tiêu đề: ${data.title}\n⏱️ Thời lượng: ${data.duration}s\n📐 Độ phân giải: ${data.resolution}\n🎨 Phong cách: ${data.style}\n🔗 Link: ${data.url}\n\n⏳ Trạng thái: ${data.status}`);
        })
        .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

function analyzeData() {
    requireAuthAndExecute(() => {
        const text = inputField.value.trim();
        if (!text) {
            showToast('Vui lòng nhập văn bản hoặc số cần phân tích!', 'error');
            return;
        }
        const numbers = text.split(',').map(n => parseFloat(n.trim())).filter(n => !isNaN(n));
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
                hideTyping();
                if (data.error) {
                    addMessage('ai', '❌ ' + data.error);
                    return;
                }
                addMessage('ai', `📊 **Phân tích dữ liệu số:**\n\n📌 Số lượng: ${data.count}\n📉 Nhỏ nhất: ${data.min}\n📈 Lớn nhất: ${data.max}\n📊 Trung bình: ${data.mean}\n📏 Trung vị: ${data.median}\n📐 Tổng: ${data.sum}`);
            })
            .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
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
                hideTyping();
                if (data.error) {
                    addMessage('ai', '❌ ' + data.error);
                    return;
                }
                addMessage('ai', `📊 **Phân tích văn bản:**\n\n📌 Số từ: ${data.word_count}\n📝 Số câu: ${data.sentence_count}\n📏 Độ dài trung bình từ: ${data.avg_word_length}\n🔤 Số từ độc nhất: ${data.unique_words}\n📖 Độ dễ đọc: ${data.readability}`);
            })
            .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
        }
    });
}

function generateMusicWithLyrics() {
    requireAuthAndExecute(() => {
        const text = inputField.value.trim();
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
        fetch('/api/generate_music', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: text,
                style: style,
                mood: mood,
                duration: Math.min(duration, 420)
            })
        })
        .then(res => res.json())
        .then(data => {
            hideTyping();
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
        .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
    });
}

function clearAllMessages() {
    if (!confirm('Xóa toàn bộ tin nhắn trong chat hiện tại?')) return;
    chatContainer.innerHTML = '';
    addMessage('ai', '🗑️ Chat đã được xóa. Hãy bắt đầu trò chuyện mới!');
    currentConversationId = null;
    exportBtn.style.display = 'none';
}

// ================================================================
// INIT
// ================================================================
checkLogin();
inputField.focus();

// Auto-refresh usage every 60 seconds
setInterval(() => {
    if (isLoggedIn) loadUsage();
}, 60000);

if (typeof io !== 'undefined') {
    initSocket();
}

console.log('🚀 T.VỸ-AI-SUPREME v11.0 đã sẵn sàng!');
console.log('📌 Bản quyền: T.VỸ-VIP-FILE');
console.log('🔐 Hệ thống đăng nhập OAuth đã được tích hợp');
console.log('👤 Chế độ Khách: các chức năng bị giới hạn');