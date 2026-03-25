const API = 'http://localhost:8000/accounts/api';

// ── Token management ──────────────────────────────────────────
const Auth = {
  getAccess:  () => localStorage.getItem('sl_access'),
  getRefresh: () => localStorage.getItem('sl_refresh'),
  getUser:    () => JSON.parse(localStorage.getItem('sl_user') || 'null'),
  isLoggedIn: () => !!localStorage.getItem('sl_access'),

  save(tokens, user) {
    localStorage.setItem('sl_access',  tokens.access);
    localStorage.setItem('sl_refresh', tokens.refresh);
    localStorage.setItem('sl_user',    JSON.stringify(user));
  },

  clear() {
    ['sl_access', 'sl_refresh', 'sl_user'].forEach(k => localStorage.removeItem(k));
  },

  async refreshToken() {
    const refresh = this.getRefresh();
    if (!refresh) return false;
    try {
      const res = await fetch(`${API}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!res.ok) { this.clear(); return false; }
      const data = await res.json();
      localStorage.setItem('sl_access', data.access);
      return true;
    } catch { return false; }
  },

  async fetchWithAuth(url, options = {}) {
    const headers = {
      'Authorization': `Bearer ${this.getAccess()}`,
      ...(options.headers || {}),
    };

    // Không set Content-Type nếu là FormData
    // để browser tự set multipart/form-data + boundary
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    let res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.getAccess()}`;
        res = await fetch(url, { ...options, headers });
      } else {
        this.clear();
        window.location.href = '/accounts/login/';
        return null;
      }
    }
    return res;
  },

  requireAuth() {
    if (!this.isLoggedIn()) {
      window.location.href = '/accounts/login/';
    }
  },

  redirectIfAuth() {
    if (this.isLoggedIn()) {
      window.location.href = '/';
    }
  },

  async logout() {
    try {
      await this.fetchWithAuth(`${API}/logout/`, {
        method: 'POST',
        body: JSON.stringify({ refresh: this.getRefresh() }),
      });
    } catch {}
    this.clear();
    window.location.href = '/';
  },
};

// ── UI Helpers ────────────────────────────────────────────────
function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  const text    = btn.querySelector('.btn-text');
  const spinner = btn.querySelector('.spinner');
  btn.disabled = loading;
  if (text)    text.style.display    = loading ? 'none'  : 'inline';
  if (spinner) spinner.style.display = loading ? 'block' : 'none';
}

function showAlert(id, msg, type = 'error') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `alert ${type} show`;
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('show');
}

function setFieldError(inputId, errId, show, msg) {
  const input = document.getElementById(inputId);
  const err   = document.getElementById(errId);
  if (!input || !err) return;
  input.classList.toggle('error', show);
  err.classList.toggle('show', show);
  if (msg) err.textContent = msg;
}

function clearErrors(ids) {
  ids.forEach(([inp, err]) => setFieldError(inp, err, false));
}

function togglePw(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type      = input.type === 'password' ? 'text' : 'password';
  btn.textContent = input.type === 'password'  ? '👁'  : '🙈';
}

function isValidEmail(e) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e); }

// ── Avatar HTML helpers ───────────────────────────────────────
// Dùng thẻ <img> thay vì background-image để tránh render đen

/**
 * Avatar tròn dùng cho nút navbar (36×36)
 */
function _navAvatarHtml(user) {
  const initials = (user?.full_name || user?.username || '?')[0].toUpperCase();

  if (user?.avatar_url) {
    return `
      <div class="nav-avatar" id="nav-avatar-btn" onclick="toggleDropdown()"
           style="overflow:hidden; padding:0;">
        <img src="${user.avatar_url}"
             alt="avatar"
             style="width:100%;height:100%;object-fit:cover;border-radius:50%;display:block;"
             onerror="this.parentElement.textContent='${initials}';this.parentElement.style.padding='';"
        />
      </div>`;
  }
  return `
    <div class="nav-avatar" id="nav-avatar-btn" onclick="toggleDropdown()">
      ${initials}
    </div>`;
}

/**
 * Avatar vuông nhỏ trong dropdown (40×40)
 */
function _dropdownAvatarHtml(user) {
  const initials = (user?.full_name || user?.username || '?')[0].toUpperCase();

  if (user?.avatar_url) {
    return `
      <div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;overflow:hidden;">
        <img src="${user.avatar_url}"
             alt="avatar"
             style="width:100%;height:100%;object-fit:cover;display:block;"
             onerror="
               this.parentElement.style.cssText='width:40px;height:40px;border-radius:10px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--accent),var(--accent2));font-size:16px;font-weight:700;color:#080c14;';
               this.parentElement.textContent='${initials}';
             "
        />
      </div>`;
  }
  return `
    <div style="
      width:40px; height:40px; border-radius:10px; flex-shrink:0;
      background:linear-gradient(135deg, var(--accent), var(--accent2));
      display:flex; align-items:center; justify-content:center;
      font-size:16px; font-weight:700; color:#080c14;">
      ${initials}
    </div>`;
}

// ── Navbar builder ────────────────────────────────────────────
// ════════════════════════════════════════════════════════════
// buildNavbar — tích hợp chuông thông báo + nút chat
// ════════════════════════════════════════════════════════════

const NOTIF_API = 'http://localhost:8000/api/notifications';

// ── Notification state ────────────────────────────────────
let _notifData      = [];
let _unreadCount    = 0;
let _notifOpen      = false;
let _notifInterval  = null;
let _chatCourseId   = null; // courseId hiện tại để mở chat

// ── Build navbar ──────────────────────────────────────────
  function buildNavbar(activePage = '') {
    const user     = Auth.getUser();
    const loggedIn = Auth.isLoggedIn();

    const guestLinks = `
      <a href="/" class="nav-link ${activePage === 'home' ? 'active' : ''}">Trang chủ</a>
      <a href="/courses/" class="nav-link ${activePage === 'courses' ? 'active' : ''}">Khóa học</a>
      <a href="/accounts/login/"    class="btn btn-outline" style="padding:8px 18px;font-size:13px">Đăng nhập</a>
      <a href="/accounts/register/" class="btn btn-primary" style="padding:8px 18px;font-size:13px">Đăng ký</a>
    `;

    const myCoursesLink = `
      <a href="/courses/my/" class="nav-link ${activePage === 'my' ? 'active' : ''}">Của tôi</a>
    `;

    const createCourseLink = (user?.role === 'teacher' || user?.role === 'admin') ? `
      <a href="/courses/create/" class="btn btn-primary" style="padding:8px 16px;font-size:13px;white-space:nowrap">
        Tạo khóa học
      </a>
    ` : '';

    const userLinks = `
      <a href="/" class="nav-link ${activePage === 'home' ? 'active' : ''}">Trang chủ</a>
      <a href="/courses/" class="nav-link ${activePage === 'courses' ? 'active' : ''}">Khóa học</a>
      ${myCoursesLink}
      <a href="/dashboard/" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}">Dashboard</a>
      <a href="/ai-tutor/"  class="nav-link ${activePage === 'ai-tutor'  ? 'active' : ''}">Chat AI</a>
      ${createCourseLink}

      <!-- ── Nút Chat (chỉ hiện nếu đang trong trang khóa học) ── -->
      <div id="nav-chat-btn" style="display:none;position:relative">
        <button class="nav-icon-btn" id="chat-trigger-btn" onclick="toggleChatPanel()" title="Chat lớp học">
          💬
        </button>
      </div>

      <!-- ── Chuông thông báo ── -->
      <div style="position:relative">
        <button class="nav-icon-btn" id="notif-bell" onclick="toggleNotifPanel()" title="Thông báo">
          🔔
          <span class="notif-badge" id="notif-badge" style="display:none">0</span>
        </button>

        <!-- Notification panel -->
        <div class="notif-panel" id="notif-panel" style="display:none">
          <div class="notif-panel-header">
            <span class="notif-panel-title">Thông báo</span>
            <button class="notif-read-all" id="notif-read-all" onclick="markAllRead()">Đánh dấu tất cả</button>
          </div>
          <div class="notif-list" id="notif-list">
            <div class="notif-empty">Đang tải...</div>
          </div>
        </div>
      </div>

      <!-- ── Avatar + Dropdown ── -->
      <div style="position:relative">
        ${_navAvatarHtml(user)}
        <div class="nav-dropdown" id="nav-dropdown" style="display:none">
          <div style="padding:12px 14px 10px;display:flex;align-items:center;gap:12px">
            ${_dropdownAvatarHtml(user)}
            <div style="min-width:0;flex:1">
              <div style="font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                ${user?.full_name || user?.username || ''}
              </div>
              <div style="font-size:12px;color:var(--text2);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                ${user?.email || ''}
              </div>
              <div style="margin-top:6px">
                <span class="badge badge-${user?.role === 'teacher' ? 'cyan' : 'green'}">
                  ${user?.role === 'teacher' ? 'Giáo viên' : 'Học sinh'}
                </span>
              </div>
            </div>
          </div>
          <div class="nav-dropdown-sep"></div>
          <a href="/accounts/profile/"         class="nav-dropdown-item">Hồ sơ cá nhân</a>
          <a href="/courses/my/"               class="nav-dropdown-item">Khóa học của tôi</a>
          <a href="/dashboard/"                class="nav-dropdown-item">Dashboard</a>
          <a href="/ai-tutor/"                 class="nav-dropdown-item">AI Tutor</a>
          <a href="/accounts/change-password/" class="nav-dropdown-item">Đổi mật khẩu</a>
          <div class="nav-dropdown-sep"></div>
          <div class="nav-dropdown-item danger" onclick="Auth.logout()">Đăng xuất</div>
        </div>
      </div>
    `;

    document.getElementById('navbar-links').innerHTML = loggedIn ? userLinks : guestLinks;

    // Inject styles
    _injectNavbarStyles();

    if (loggedIn) {
      // Load notifications
      _loadNotifications();
      // Poll mỗi 30s
      clearInterval(_notifInterval);
      _notifInterval = setInterval(_loadNotifications, 30000);

      // Close panels khi click ngoài
      document.addEventListener('click', _handleOutsideClick);
    }
  }

  // ── Inject CSS vào <head> (chỉ 1 lần) ───────────────────
  function _injectNavbarStyles() {
    if (document.getElementById('navbar-extra-styles')) return;
    const style = document.createElement('style');
    style.id = 'navbar-extra-styles';
    style.textContent = `
      /* Icon button chung */
      .nav-icon-btn {
        position: relative; background: rgba(255,255,255,0.06);
        border: 1px solid var(--border); border-radius: 10px;
        width: 36px; height: 36px; cursor: pointer; font-size: 16px;
        display: flex; align-items: center; justify-content: center;
        transition: background 0.2s, border-color 0.2s; color: var(--text);
      }
      .nav-icon-btn:hover { background: rgba(255,255,255,0.1); border-color: var(--border2); }

      /* Badge số */
      .notif-badge {
        position: absolute; top: -5px; right: -5px;
        min-width: 18px; height: 18px; border-radius: 9px;
        background: var(--danger); color: white;
        font-size: 10px; font-weight: 700; line-height: 18px;
        text-align: center; padding: 0 4px;
        border: 2px solid var(--bg);
        animation: badgePop 0.3s cubic-bezier(0.34,1.56,0.64,1);
      }
      @keyframes badgePop { from{transform:scale(0)} to{transform:scale(1)} }

      /* Notification panel */
      .notif-panel {
        position: absolute; top: calc(100% + 10px); right: 0;
        width: 360px; background: var(--panel);
        border: 1px solid var(--border2); border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        z-index: 200; overflow: hidden;
        animation: panelSlide 0.25s cubic-bezier(0.34,1.2,0.64,1);
      }
      @keyframes panelSlide { from{opacity:0;transform:translateY(-8px)} to{opacity:1;transform:translateY(0)} }

      .notif-panel-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 16px; border-bottom: 1px solid var(--border);
      }
      .notif-panel-title { font-family: var(--font-display); font-size: 14px; font-weight: 700; }
      .notif-read-all {
        font-size: 12px; color: var(--accent); background: none; border: none;
        cursor: pointer; font-family: var(--font-body); padding: 0;
        transition: opacity 0.2s;
      }
      .notif-read-all:hover { opacity: 0.7; }

      .notif-list { max-height: 400px; overflow-y: auto; }
      .notif-list::-webkit-scrollbar { width: 3px; }
      .notif-list::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

      .notif-item {
        display: flex; align-items: flex-start; gap: 12px;
        padding: 12px 16px; cursor: pointer;
        transition: background 0.15s; border-bottom: 1px solid rgba(255,255,255,0.04);
        position: relative;
      }
      .notif-item:last-child { border-bottom: none; }
      .notif-item:hover { background: rgba(255,255,255,0.04); }
      .notif-item.unread { background: rgba(74,222,128,0.04); }
      .notif-item.unread::before {
        content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
        background: var(--accent); border-radius: 0 2px 2px 0;
      }

      .notif-icon {
        width: 36px; height: 36px; border-radius: 10px; flex-shrink: 0;
        display: flex; align-items: center; justify-content: center; font-size: 16px;
      }
      .notif-icon.enroll_request  { background: rgba(251,146,60,0.12); }
      .notif-icon.enroll_approved { background: rgba(74,222,128,0.12); }
      .notif-icon.enroll_rejected { background: rgba(248,113,113,0.12); }
      .notif-icon.new_lesson      { background: rgba(34,211,238,0.12); }
      .notif-icon.new_quiz        { background: rgba(167,139,250,0.12); }
      .notif-icon.quiz_result     { background: rgba(251,191,36,0.12); }
      .notif-icon.system          { background: rgba(255,255,255,0.06); }

      .notif-content { flex: 1; min-width: 0; }
      .notif-title   { font-size: 13px; font-weight: 500; line-height: 1.4; margin-bottom: 3px; }
      .notif-message { font-size: 12px; color: var(--text2); line-height: 1.4; margin-bottom: 4px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .notif-time    { font-size: 11px; color: var(--muted); }

      .notif-actions { display: flex; gap: 4px; flex-shrink: 0; }
      .notif-mark-btn {
        width: 26px; height: 26px; border-radius: 7px;
        background: none; border: 1px solid var(--border);
        color: var(--muted); cursor: pointer; font-size: 12px;
        display: flex; align-items: center; justify-content: center;
        transition: all 0.2s;
      }
      .notif-mark-btn:hover { border-color: var(--accent); color: var(--accent); background: rgba(74,222,128,0.08); }

      .notif-empty {
        padding: 32px; text-align: center; color: var(--muted); font-size: 13px;
      }
      .notif-footer {
        padding: 10px 16px; border-top: 1px solid var(--border); text-align: center;
      }
      .notif-footer a { font-size: 12px; color: var(--text2); text-decoration: none; transition: color 0.2s; }
      .notif-footer a:hover { color: var(--accent); }

      /* ── Chat Panel ── */
      .chat-panel {
        position: fixed; bottom: 80px; right: 24px;
        width: 340px; height: 480px;
        background: var(--panel); border: 1px solid var(--border2);
        border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        z-index: 300; display: flex; flex-direction: column; overflow: hidden;
        animation: chatSlide 0.3s cubic-bezier(0.34,1.2,0.64,1);
      }
      @keyframes chatSlide { from{opacity:0;transform:translateY(20px)scale(0.95)} to{opacity:1;transform:translateY(0)scale(1)} }

      .chat-panel-header {
        padding: 14px 16px; background: linear-gradient(135deg, rgba(74,222,128,0.1), rgba(34,211,238,0.07));
        border-bottom: 1px solid var(--border);
        display: flex; align-items: center; gap: 10px;
      }
      .chat-panel-title { font-family: var(--font-display); font-size: 14px; font-weight: 700; flex: 1; }
      .chat-panel-close {
        background: none; border: none; color: var(--text2); cursor: pointer;
        font-size: 16px; width: 28px; height: 28px; border-radius: 8px;
        display: flex; align-items: center; justify-content: center; transition: background 0.2s;
      }
      .chat-panel-close:hover { background: rgba(255,255,255,0.08); }

      .chat-panel-messages {
        flex: 1; overflow-y: auto; padding: 12px;
        display: flex; flex-direction: column; gap: 6px;
      }
      .chat-panel-messages::-webkit-scrollbar { width: 3px; }
      .chat-panel-messages::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

      .cp-msg { max-width: 80%; }
      .cp-msg.mine { align-self: flex-end; }
      .cp-msg-bubble {
        padding: 8px 12px; border-radius: 12px; font-size: 13px; line-height: 1.4;
      }
      .cp-msg.theirs .cp-msg-bubble { background: var(--panel2); border: 1px solid var(--border); border-bottom-left-radius: 3px; }
      .cp-msg.mine   .cp-msg-bubble { background: rgba(74,222,128,0.1); border: 1px solid rgba(74,222,128,0.2); border-bottom-right-radius: 3px; }
      .cp-msg-sender { font-size: 10px; color: var(--muted); margin-bottom: 2px; }
      .cp-msg-time   { font-size: 10px; color: var(--muted); margin-top: 2px; }
      .cp-msg.mine .cp-msg-time { text-align: right; }

      .chat-panel-input {
        padding: 10px 12px; border-top: 1px solid var(--border);
        display: flex; gap: 8px; align-items: flex-end;
      }
      .chat-panel-input textarea {
        flex: 1; background: rgba(255,255,255,0.05); border: 1px solid var(--border);
        border-radius: 10px; color: var(--text); font-family: var(--font-body); font-size: 13px;
        outline: none; resize: none; padding: 8px 10px; line-height: 1.4;
        min-height: 36px; max-height: 90px; transition: border-color 0.2s;
      }
      .chat-panel-input textarea:focus { border-color: var(--accent); }
      .chat-panel-input textarea::placeholder { color: var(--muted); }
      .chat-panel-send {
        width: 34px; height: 34px; border-radius: 9px; flex-shrink: 0;
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        border: none; color: #080c14; font-size: 14px; cursor: pointer;
        display: flex; align-items: center; justify-content: center; transition: opacity 0.2s;
      }
      .chat-panel-send:hover { opacity: 0.85; }
      .chat-panel-send:disabled { opacity: 0.35; cursor: not-allowed; }

      .chat-open-full {
        text-align: center; padding: 8px; border-top: 1px solid var(--border);
      }
      .chat-open-full a { font-size: 11px; color: var(--text2); text-decoration: none; transition: color 0.2s; }
      .chat-open-full a:hover { color: var(--accent); }

      /* Floating chat button (dùng khi trong course page) */
      .floating-chat-btn {
        position: fixed; bottom: 24px; right: 24px; z-index: 200;
        width: 52px; height: 52px; border-radius: 50%;
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        border: none; color: #080c14; font-size: 22px; cursor: pointer;
        box-shadow: 0 8px 24px rgba(74,222,128,0.35);
        display: flex; align-items: center; justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
        display: none; /* hiện bằng JS */
      }
      .floating-chat-btn:hover { transform: scale(1.1); box-shadow: 0 12px 32px rgba(74,222,128,0.45); }
      .floating-chat-btn.show { display: flex; }
    `;
    document.head.appendChild(style);

    // Thêm floating chat button vào body
    if (!document.getElementById('floating-chat-btn')) {
      const btn = document.createElement('button');
      btn.id = 'floating-chat-btn';
      btn.className = 'floating-chat-btn';
      btn.title = 'Chat lớp học';
      btn.innerHTML = '💬';
      btn.onclick = toggleChatPanel;
      document.body.appendChild(btn);
    }

    // Thêm chat panel vào body
    if (!document.getElementById('chat-panel')) {
      const panel = document.createElement('div');
      panel.id = 'chat-panel';
      panel.className = 'chat-panel';
      panel.style.display = 'none';
      document.body.appendChild(panel);
    }
  }

  // ════════════════════════════════════════
  // NOTIFICATIONS
  // ════════════════════════════════════════
  const NOTIF_ICONS = {
    enroll_request:  '📩', enroll_approved: '✅',
    enroll_rejected: '❌', new_lesson:      '📄',
    new_quiz:        '📝', quiz_result:     '🏆', system: '🔔',
  };

  async function _loadNotifications() {
    if (!Auth.isLoggedIn()) return;
    try {
      const res  = await Auth.fetchWithAuth(`${NOTIF_API}/`);
      if (!res) return;
      const data = await res.json();
      _notifData   = data.notifications || [];
      _unreadCount = data.unread_count  || 0;
      _updateBadge();
      if (_notifOpen) _renderNotifList();
    } catch {}
  }

  function _updateBadge() {
    const badge = document.getElementById('notif-badge');
    if (!badge) return;
    if (_unreadCount > 0) {
      badge.textContent = _unreadCount > 99 ? '99+' : _unreadCount;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  }

  function toggleNotifPanel() {
    _notifOpen = !_notifOpen;
    const panel = document.getElementById('notif-panel');
    if (!panel) return;

    // Đóng dropdown avatar nếu đang mở
    const dropdown = document.getElementById('nav-dropdown');
    if (dropdown) dropdown.style.display = 'none';

    if (_notifOpen) {
      panel.style.display = 'block';
      _renderNotifList();
    } else {
      panel.style.display = 'none';
    }
  }

  function _renderNotifList() {
    const list = document.getElementById('notif-list');
    if (!list) return;

    if (!_notifData.length) {
      list.innerHTML = `
        <div class="notif-empty">
          <div style="font-size:32px;margin-bottom:8px">🔔</div>
          Chưa có thông báo nào
        </div>`;
      return;
    }

    list.innerHTML = _notifData.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'unread'}"
          onclick="_notifClick('${n.id}', '${n.url}')">
        <div class="notif-icon ${n.type}">
          ${NOTIF_ICONS[n.type] || '🔔'}
        </div>
        <div class="notif-content">
          <div class="notif-title">${n.title}</div>
          ${n.message ? `<div class="notif-message">${n.message}</div>` : ''}
          <div class="notif-time">${_timeAgo(n.created_at)}</div>
        </div>
        ${!n.is_read ? `
          <div class="notif-actions">
            <button class="notif-mark-btn" onclick="markRead(event,'${n.id}')" title="Đánh dấu đã đọc">✓</button>
          </div>` : ''}
      </div>`).join('') + `
      <div class="notif-footer">
        <a href="/notifications/">Xem tất cả thông báo</a>
      </div>`;
  }

  async function _notifClick(id, url) {
    // Đánh dấu đã đọc
    await markRead(null, id);
    // Chuyển trang
    if (url && url !== 'None' && url !== '') {
      window.location.href = url;
    }
    toggleNotifPanel();
  }

  async function markRead(e, id) {
    if (e) { e.stopPropagation(); }
    try {
      await Auth.fetchWithAuth(`${NOTIF_API}/${id}/`, { method: 'PATCH' });
      const n = _notifData.find(x => x.id === id);
      if (n) { n.is_read = true; _unreadCount = Math.max(0, _unreadCount - 1); }
      _updateBadge();
      _renderNotifList();
    } catch {}
  }

  async function markAllRead() {
    try {
      await Auth.fetchWithAuth(`${NOTIF_API}/read-all/`, { method: 'POST' });
      _notifData.forEach(n => n.is_read = true);
      _unreadCount = 0;
      _updateBadge();
      _renderNotifList();
    } catch {}
  }

  // ════════════════════════════════════════
  // CHAT PANEL (mini)
  // ════════════════════════════════════════
  let _chatWS       = null;
  let _chatOpen     = false;
  let _chatMsgs     = [];
  let _chatMyId     = null;

  function initChatPanel(courseId, courseTitle) {
    /** Gọi hàm này từ trang detail.html hoặc lesson_detail.html */
    _chatCourseId = courseId;
    _chatMyId     = Auth.getUser()?.id;

    // Hiện floating button
    const btn = document.getElementById('floating-chat-btn');
    if (btn) btn.classList.add('show');

    // Render panel header ngay
    _renderChatPanel(courseTitle || 'Chat lớp học');
  }

  function _renderChatPanel(title) {
    const panel = document.getElementById('chat-panel');
    if (!panel) return;
    panel.innerHTML = `
      <div class="chat-panel-header">
        <span style="font-size:18px">💬</span>
        <div class="chat-panel-title">${title}</div>
        <button class="chat-panel-close" onclick="toggleChatPanel()">✕</button>
      </div>
      <div class="chat-panel-messages" id="cp-messages">
        <div style="text-align:center;color:var(--muted);font-size:12px;padding:16px">Đang kết nối...</div>
      </div>
      <div class="chat-panel-input">
        <textarea id="cp-input" placeholder="Nhập tin nhắn..." rows="1"
                  onkeydown="cpHandleKey(event)" oninput="cpResize(this)"></textarea>
        <button class="chat-panel-send" id="cp-send" onclick="cpSend()">➤</button>
      </div>
      <div class="chat-open-full">
        <a href="/courses/${_chatCourseId}/chat/">Mở rộng chat ↗</a>
      </div>
    `;
  }

  function toggleChatPanel() {
    _chatOpen = !_chatOpen;
    const panel = document.getElementById('chat-panel');
    if (!panel || !_chatCourseId) return;

    if (_chatOpen) {
      panel.style.display = 'flex';
      panel.style.flexDirection = 'column';
      _connectChatWS();
      setTimeout(() => document.getElementById('cp-input')?.focus(), 100);
    } else {
      panel.style.display = 'none';
      _disconnectChatWS();
    }
  }

  function _connectChatWS() {
    if (_chatWS && _chatWS.readyState === WebSocket.OPEN) return;
    const token = localStorage.getItem('sl_access');
    const WS    = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    _chatWS     = new WebSocket(`${WS}//localhost:8000/ws/chat/${_chatCourseId}/?token=${token}`);

    _chatWS.onmessage = e => {
      const data = JSON.parse(e.data);
      if (data.type === 'history') {
        _chatMsgs = data.messages || [];
        _renderChatMessages();
      } else if (data.type === 'message') {
        _chatMsgs.push(data);
        _appendChatMsg(data);
      }
    };

    _chatWS.onerror = () => {
      const msgs = document.getElementById('cp-messages');
      if (msgs) msgs.innerHTML = '<div style="text-align:center;color:var(--danger);font-size:12px;padding:12px">Lỗi kết nối WebSocket</div>';
    };
  }

  function _disconnectChatWS() {
    if (_chatWS) { _chatWS.close(); _chatWS = null; }
  }

  function _renderChatMessages() {
    const container = document.getElementById('cp-messages');
    if (!container) return;
    if (!_chatMsgs.length) {
      container.innerHTML = '<div style="text-align:center;color:var(--muted);font-size:12px;padding:16px">Chưa có tin nhắn nào</div>';
      return;
    }
    container.innerHTML = '';
    _chatMsgs.forEach(m => _appendChatMsg(m, false));
    container.scrollTop = container.scrollHeight;
  }

  function _appendChatMsg(m, scroll = true) {
    const container = document.getElementById('cp-messages');
    if (!container) return;
    const isMine = m.sender_id === _chatMyId;
    const time   = new Date(m.created_at).toLocaleTimeString('vi', {hour:'2-digit',minute:'2-digit'});
    const el     = document.createElement('div');
    el.className = `cp-msg ${isMine ? 'mine' : 'theirs'}`;
    el.innerHTML = `
      ${!isMine ? `<div class="cp-msg-sender">${m.sender_name}</div>` : ''}
      <div class="cp-msg-bubble">${_escHtml(m.content)}</div>
      <div class="cp-msg-time">${time}</div>
    `;
    container.appendChild(el);
    if (scroll) container.scrollTop = container.scrollHeight;
  }

  function cpSend() {
    const input   = document.getElementById('cp-input');
    const content = input?.value.trim();
    if (!content || !_chatWS || _chatWS.readyState !== WebSocket.OPEN) return;
    _chatWS.send(JSON.stringify({ type: 'message', content }));
    input.value = '';
    input.style.height = 'auto';
  }

  function cpHandleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); cpSend(); }
  }

  function cpResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 90) + 'px';
  }

  // ════════════════════════════════════════
  // UTILS
  // ════════════════════════════════════════
  function _handleOutsideClick(e) {
    // Đóng notif panel
    const notifPanel = document.getElementById('notif-panel');
    const notifBell  = document.getElementById('notif-bell');
    if (_notifOpen && notifPanel && notifBell &&
        !notifPanel.contains(e.target) && !notifBell.contains(e.target)) {
      _notifOpen = false;
      notifPanel.style.display = 'none';
    }
  }

  function _timeAgo(iso) {
    if (!iso) return '';
    const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (diff < 60)    return 'Vừa xong';
    if (diff < 3600)  return `${Math.floor(diff/60)} phút trước`;
    if (diff < 86400) return `${Math.floor(diff/3600)} giờ trước`;
    if (diff < 604800)return `${Math.floor(diff/86400)} ngày trước`;
    return new Date(iso).toLocaleDateString('vi');
  }

  function _escHtml(s) {
    return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
  }
// ── Dropdown toggle ───────────────────────────────────────────
function toggleDropdown() {
  const dd = document.getElementById('nav-dropdown');
  if (dd) dd.style.display = dd.style.display === 'none' ? 'block' : 'none';
}

// Đóng dropdown khi click ra ngoài
document.addEventListener('click', e => {
  const btn = document.getElementById('nav-avatar-btn');
  const dd  = document.getElementById('nav-dropdown');
  if (dd && btn && !btn.contains(e.target) && !dd.contains(e.target)) {
    dd.style.display = 'none';
  }
});


