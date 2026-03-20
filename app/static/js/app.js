/* ── Theme Manager ── */
const ThemeManager = {
  init() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    }
  },
  toggle() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  },
  get isDark() {
    return document.documentElement.classList.contains('dark');
  }
};
ThemeManager.init();

/* ── Toast Notifications ── */
const Toast = {
  _container: null,

  _getContainer() {
    if (!this._container) {
      this._container = document.createElement('div');
      this._container.className = 'toast-container';
      document.body.appendChild(this._container);
    }
    return this._container;
  },

  _icons: {
    success: '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
    error: '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
    warning: '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
    info: '<svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
  },

  show(message, type = 'info', duration = 5000) {
    const container = this._getContainer();
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `${this._icons[type] || this._icons.info}<span class="flex-1 text-sm font-medium">${message}</span><button onclick="this.parentElement.remove()" class="ml-2 opacity-60 hover:opacity-100">&times;</button>`;
    container.appendChild(el);

    if (duration > 0) {
      setTimeout(() => {
        el.classList.add('toast-exit');
        setTimeout(() => el.remove(), 300);
      }, duration);
    }
    return el;
  },

  success(msg, dur) { return this.show(msg, 'success', dur); },
  error(msg, dur) { return this.show(msg, 'error', dur || 8000); },
  warning(msg, dur) { return this.show(msg, 'warning', dur || 6000); },
  info(msg, dur) { return this.show(msg, 'info', dur); },

  progress(msg) {
    const el = this.show(msg, 'info', 0);
    el.querySelector('svg').outerHTML = '<div class="w-5 h-5 flex-shrink-0 border-2 border-current border-t-transparent rounded-full animate-spin"></div>';
    return {
      el,
      done(finalMsg, type = 'success') {
        el.remove();
        if (finalMsg) Toast.show(finalMsg, type);
      },
      fail(errMsg) {
        el.remove();
        if (errMsg) Toast.error(errMsg);
      }
    };
  }
};

/* ── Confirm Dialog ── */
function confirmDialog(title, message, { confirmText = 'Подтвердить', cancelText = 'Отмена', danger = false } = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'dialog-overlay';
    overlay.innerHTML = `
      <div class="dialog-box" @click.stop>
        <h3 class="text-lg font-semibold mb-2" style="color:var(--text-primary)">${title}</h3>
        <p class="text-sm mb-6" style="color:var(--text-secondary)">${message}</p>
        <div class="flex justify-end gap-3">
          <button class="dialog-cancel px-4 py-2 rounded-lg text-sm font-medium btn-secondary">${cancelText}</button>
          <button class="dialog-confirm px-4 py-2 rounded-lg text-sm font-medium text-white ${danger ? 'bg-red-600 hover:bg-red-700' : 'btn-primary'}">${confirmText}</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);

    const cleanup = (result) => { overlay.remove(); resolve(result); };
    overlay.querySelector('.dialog-cancel').onclick = () => cleanup(false);
    overlay.querySelector('.dialog-confirm').onclick = () => cleanup(true);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) cleanup(false); });
  });
}

/* ── API Helper ── */
async function api(url, { method = 'GET', body, headers = {} } = {}) {
  const opts = { method, headers: { 'Content-Type': 'application/json', ...headers } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ── i18n stub (populated in Sprint 4) ── */
const _i18nData = {};
function t(key, fallback) {
  return _i18nData[key] || fallback || key;
}

/* ── Keyboard Shortcuts ── */
document.addEventListener('keydown', (e) => {
  const mod = e.ctrlKey || e.metaKey;
  if (!mod) return;

  const handlers = {
    's': () => window.dispatchEvent(new CustomEvent('shortcut-save')),
    'g': () => window.dispatchEvent(new CustomEvent('shortcut-generate')),
    'r': () => { if (!e.shiftKey) window.dispatchEvent(new CustomEvent('shortcut-review')); },
    'i': () => window.dispatchEvent(new CustomEvent('shortcut-illustrate')),
    '/': () => showShortcutsHelp(),
  };

  if (e.shiftKey && e.key === 'H') {
    e.preventDefault();
    window.dispatchEvent(new CustomEvent('shortcut-produce-hq'));
    return;
  }

  if (handlers[e.key]) {
    e.preventDefault();
    handlers[e.key]();
  }
});

function showShortcutsHelp() {
  const shortcuts = [
    ['Ctrl+S', 'Сохранить'],
    ['Ctrl+G', 'Генерировать'],
    ['Ctrl+R', 'Ревью'],
    ['Ctrl+Shift+H', 'Produce HQ'],
    ['Ctrl+I', 'Иллюстрация'],
    ['Ctrl+/', 'Подсказки'],
    ['Escape', 'Закрыть панель'],
  ];
  const html = shortcuts.map(([key, desc]) =>
    `<div class="flex justify-between py-1"><kbd class="px-2 py-0.5 rounded text-xs font-mono" style="background:var(--bg-tertiary)">${key}</kbd><span class="text-sm">${desc}</span></div>`
  ).join('');
  const overlay = document.createElement('div');
  overlay.className = 'dialog-overlay';
  overlay.innerHTML = `<div class="dialog-box"><h3 class="text-lg font-semibold mb-3">Клавиатурные сокращения</h3><div class="space-y-1">${html}</div><div class="mt-4 flex justify-end"><button class="btn-primary px-4 py-2 rounded-lg text-sm" onclick="this.closest('.dialog-overlay').remove()">Закрыть</button></div></div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
}

/* ── Language Manager ── */
const LangManager = {
  current: localStorage.getItem('lang') || 'ru',

  async init() {
    try {
      const res = await fetch(`/static/i18n/${this.current}.json`);
      const data = await res.json();
      Object.assign(_i18nData, data);
    } catch (_) {}
  },

  toggle() {
    this.current = this.current === 'ru' ? 'en' : 'ru';
    localStorage.setItem('lang', this.current);
    this.init().then(() => window.location.reload());
  }
};
LangManager.init().then(() => {
  const el = document.getElementById('lang-code');
  if (el) el.textContent = LangManager.current.toUpperCase();
});

/* ── Exports for Alpine.js ── */
window.ThemeManager = ThemeManager;
window.Toast = Toast;
window.confirmDialog = confirmDialog;
window.api = api;
window.t = t;
window.LangManager = LangManager;
