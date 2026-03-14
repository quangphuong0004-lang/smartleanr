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
function buildNavbar(activePage = '') {
  const user     = Auth.getUser();
  const loggedIn = Auth.isLoggedIn();

  const guestLinks = `
    <a href="/" class="nav-link ${activePage === 'home' ? 'active' : ''}">Trang chủ</a>
    <a href="/courses/" class="nav-link ${activePage === 'courses' ? 'active' : ''}">Khóa học</a>
    <a href="/accounts/login/"
       class="btn btn-outline"
       style="padding:8px 18px; font-size:13px;">Đăng nhập</a>
    <a href="/accounts/register/"
       class="btn btn-primary"
       style="padding:8px 18px; font-size:13px;">Đăng ký</a>
  `;

  const userLinks = `
    <a href="/" class="nav-link ${activePage === 'home' ? 'active' : ''}">Trang chủ</a>
    <a href="/courses/" class="nav-link ${activePage === 'courses' ? 'active' : ''}">Khóa học</a>
    <a href="/dashboard/" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}">Dashboard</a>
    <div style="position:relative">

      ${_navAvatarHtml(user)}

      <div class="nav-dropdown" id="nav-dropdown" style="display:none">
        <div style="padding:12px 14px 10px; display:flex; align-items:center; gap:12px">

          ${_dropdownAvatarHtml(user)}

          <div style="min-width:0; flex:1">
            <div style="font-weight:600; font-size:14px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">
              ${user?.full_name || user?.username || ''}
            </div>
            <div style="font-size:12px; color:var(--text2); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis">
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
        <a href="/accounts/change-password/" class="nav-dropdown-item">Đổi mật khẩu</a>
        <div class="nav-dropdown-sep"></div>
        <div class="nav-dropdown-item danger" onclick="Auth.logout()">Đăng xuất</div>
      </div>
    </div>
  `;

  document.getElementById('navbar-links').innerHTML = loggedIn ? userLinks : guestLinks;
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