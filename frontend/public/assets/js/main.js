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

// ===== STATE =====
let currentConversationId = null;
let currentLevel = 'pro';
let isDark = false;
let isLoggedIn = false;
let userData = null;
let socket = null;

// ===== LEVEL CONFIG =====
const LEVEL_NAMES = {
    basic: 'AI Thường',
    pro: 'AI Pro',
    plus: 'AI Plus',
    pro3: 'AI 3.0 Pro'
};

// ===== THEME =====
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

// Load theme from localStorage
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

// ===== TOAST =====
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

// ===== LOGIN =====
function checkLogin() {
    fetch('/api/auth/me')
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showLogin();
                return;
            }
            userData = data;
            isLoggedIn = true;
            userName.textContent = data.name || 'User';
            userAvatar.textContent = (data.name || 'U').charAt(0).toUpperCase();
            if (data.avatar) {
                userAvatar.style.backgroundImage = `url(${data.avatar})`;
                userAvatar.style.backgroundSize = 'cover';
                userAvatar.style.backgroundPosition = 'center';
                userAvatar.textContent = '';
            }
            document.getElementById('loginModal').classList.remove('active');
            loadUsage();
            initSocket();
            loadConversations();
        })
        .catch(() => showLogin());
}

function showLogin() {
    document.getElementById('loginModal').classList.add('active');
}

function loginGoogle() {
    const email = prompt('Nhập email Google của bạn:', 'user@gmail.com');
    if (!email) return;
    const name = email.split('@')[0];
    fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token: email })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            showToast(data.error || 'Đăng nhập thất bại', 'error');
        }
    })
    .catch(() => showToast('Lỗi kết nối', 'error'));
}

function loginFacebook() {
    const email = prompt('Nhập email Facebook của bạn:', 'user@gmail.com');
    if (!email) return;
    const name = email.split('@')[0];
    fetch('/api/auth/facebook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ access_token: email })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            showToast(data.error || 'Đăng nhập thất bại', 'error');
        }
    })
    .catch(() => showToast('Lỗi kết nối', 'error'));
}

logoutBtn.addEventListener('click', function() {
    if (!confirm('Đăng xuất?')) return;
    fetch('/api/auth/logout', { method: 'POST' })
        .then(() => {
            isLoggedIn = false;
            if (socket) socket.disconnect();
            location.reload();
        });
});

// ===== SOCKET.IO =====
function initSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('✅ Đã kết nối WebSocket');
        socket.emit('join', { room: 'global' });
    });

    socket.on('new_message', (data) => {
        if (data.message && data.user_id !== userData?.id) {
            addMessage('ai', data.message);
        }
    });

    socket.on('joined', (data) => {
        console.log(`📡 Đã tham gia phòng: ${data.room}`);
    });

    socket.on('disconnect', () => {
        console.log('❌ Ngắt kết nối WebSocket');
    });
}

// ===== USAGE =====
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

// ===== NAVIGATION =====
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

// ===== MODALS =====
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

// ===== SEND MESSAGE =====
function sendMessage() {
    const text = inputField.value.trim();
    if (!text) return;

    if (!isLoggedIn) {
        showLogin();
        return;
    }

    addMessage('user', text);
    inputField.value = '';

    const level = levelSelect.value;

    showTyping();

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

// ===== ADD MESSAGE =====
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

// ===== CONVERSATIONS =====
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

// ===== HISTORY =====
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

// ===== EXPORT CHAT =====
exportBtn.addEventListener('click', function() {
    if (!currentConversationId) {
        showToast('Không có đoạn chat để xuất', 'error');
        return;
    }
    window.location.href = `/api/export/${currentConversationId}`;
});

// ===== SEARCH MESSAGES =====
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

// ===== UPGRADE =====
function upgradeTier(tier) {
    if (!isLoggedIn) {
        showLogin();
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

// ===== UPGRADE WITH MOMO =====
function upgradeWithMomo(tier) {
    if (!isLoggedIn) {
        showLogin();
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

// ===== SETTINGS =====
function saveSettings() {
    const darkMode = document.getElementById('darkModeToggle').checked;
    const lang = document.getElementById('langSelect').value;

    if (darkMode !== isDark) toggleTheme();
    localStorage.setItem('tv_lang', lang);

    showToast('✅ Cài đặt đã được lưu!', 'success');
    closeModal('settingsModal');
}

// ===== TYPING INDICATOR =====
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
// TOOLBAR FUNCTIONS
// ================================================================

// ===== AI ĐA LUỒNG =====
function useMultiAI() {
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
}

// ===== TÓM TẮT =====
function summarizeText() {
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
}

// ===== DỊCH NGÔN NGỮ =====
function translateText() {
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
}

// ===== TẠO VIDEO =====
function generateVideo() {
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
}

// ===== PHÂN TÍCH DỮ LIỆU =====
function analyzeData() {
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
}

// ===== TẠO NHẠC CÓ LỜI =====
function generateMusicWithLyrics() {
    const text = inputField.value.trim();
    if (!text) {
        showToast('Vui lòng nhập mô tả bài hát!', 'error');
        return;
    }

    const style = prompt('Chọn thể loại:\npop, rock, jazz, edm, classical, rap, ballad, v_pop, k_pop, rnb', 'pop');
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
}

// ===== TẠO NHẠC =====
function generateMusic() {
    const text = inputField.value.trim();
    if (!text) {
        showToast('Vui lòng nhập mô tả bài hát!', 'error');
        return;
    }

    const style = prompt('Chọn thể loại nhạc:\npop, rock, jazz, edm, classical, rap, ballad, v_pop, k_pop, rnb', 'pop');
    if (!style) return;
    
    const mood = prompt('Chọn tâm trạng:\nhappy, sad, romantic, epic, neutral', 'romantic');
    if (!mood) return;

    addMessage('user', `🎵 Yêu cầu tạo nhạc (${style}, ${mood}): ${text}`);
    inputField.value = '';

    showTyping();
    fetch('/api/generate_music', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: text,
            style: style,
            mood: mood
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
        html += `📌 Tiêu đề: ${data.title || 'Bài hát mới'}\n`;
        html += `🎶 Thể loại: ${data.style || style}\n`;
        html += `🎭 Tâm trạng: ${data.mood || mood}\n`;
        html += `🎵 Tempo: ${data.tempo || '--'} BPM\n`;
        html += `🎹 Key: ${data.key || '--'}\n`;
        html += `🎸 Hợp âm: ${data.chords || '--'}\n`;
        html += `🎤 Lời bài hát:\n${data.lyrics || 'Đang cập nhật...'}\n`;
        if (data.audio_url) {
            html += `\n🔊 Nghe thử: ${data.audio_url}`;
        }
        addMessage('ai', html);
    })
    .catch(() => { hideTyping(); addMessage('ai', '❌ Lỗi kết nối'); });
}

// ===== XÓA CHAT =====
function clearAllMessages() {
    if (!confirm('Xóa toàn bộ tin nhắn trong chat hiện tại?')) return;
    chatContainer.innerHTML = '';
    addMessage('ai', '🗑️ Chat đã được xóa. Hãy bắt đầu trò chuyện mới!');
    currentConversationId = null;
    exportBtn.style.display = 'none';
}

// ===== INIT =====
checkLogin();
inputField.focus();

// Auto-refresh usage every 60 seconds
setInterval(() => {
    if (isLoggedIn) loadUsage();
}, 60000);

console.log('🚀 T.VỸ-AI-SUPREME v10.6 đã sẵn sàng!');
console.log('📌 Bản quyền: T.VỸ-VIP-FILE');
console.log('💳 Thanh toán MoMo đã được tích hợp');