(function () {
  'use strict';

  var debugQuery = /[?&]mm_debug=1(?:&|$)/.test(location.search);
  if (!debugQuery) return;

  window.__MM_DIAG__ = true;
  window.__MM_DEV__ = true;

  var panel;
  var log = [];

  function esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function ensurePanel() {
    if (panel) return panel;
    panel = document.createElement('div');
    panel.id = 'mm-diag-panel';
    panel.setAttribute('role', 'region');
    panel.setAttribute('aria-label', 'MonkeyMart diagnostics');
    panel.innerHTML =
      '<div class="mm-diag-head"><strong>MM Diagnostics</strong>' +
      '<span class="mm-diag-sub">localhost / ?mm_debug=1 — không ẩn lỗi</span>' +
      '<button type="button" id="mm-diag-close" aria-label="Thu gọn">−</button></div>' +
      '<div class="mm-diag-body" id="mm-diag-body"></div>';
    document.documentElement.appendChild(panel);
    document.getElementById('mm-diag-close').addEventListener('click', function () {
      panel.classList.toggle('is-collapsed');
    });
    return panel;
  }

  function render() {
    ensurePanel();
    var body = document.getElementById('mm-diag-body');
    if (!body) return;
    if (!log.length) {
      body.innerHTML = '<p class="mm-diag-empty">Đang quét overlay / console / iframe…</p>';
      return;
    }
    body.innerHTML = log
      .map(function (item, i) {
        return (
          '<article class="mm-diag-item" data-i="' +
          i +
          '">' +
          '<div class="mm-diag-kind">' +
          esc(item.kind) +
          '</div>' +
          '<pre class="mm-diag-text">' +
          esc(item.text) +
          '</pre>' +
          (item.detail ? '<pre class="mm-diag-detail">' + esc(item.detail) + '</pre>' : '') +
          '</article>'
        );
      })
      .join('');
  }

  function add(kind, text, detail) {
    if (!text) return;
    var key = kind + '|' + text;
    if (log.some(function (x) {
      return x.key === key;
    })) return;
    log.push({ key: key, kind: kind, text: text, detail: detail || '' });
    render();
  }

  function scanOverlays() {
    document.querySelectorAll('body *').forEach(function (el) {
      if (el.id === 'mm-diag-panel' || el.closest('#mm-diag-panel')) return;
      if (el.id === 'playerIframe') return;
      var st = getComputedStyle(el);
      if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0') return;
      var r = el.getBoundingClientRect();
      if (r.width < 40 || r.height < 16) return;
      var t = (el.innerText || el.textContent || '').trim();
      if (!t || t.length > 600) return;
      var isFixed = st.position === 'fixed' || st.position === 'absolute';
      var bottomRight = isFixed && r.bottom > window.innerHeight * 0.55 && r.right > window.innerWidth * 0.45;
      var looksLikeAdErr =
        /lỗi|error|máy chủ|server|tag error|quảng cáo|adsbygoogle|chỉ bạn|only you will see/i.test(t) ||
        el.matches('ins.adsbygoogle, .adsbygoogle, [data-ad-status=error], [data-ad-status=unfilled]');
      if (!looksLikeAdErr && !(bottomRight && /google|ads|tag|pub/i.test(String(el.className) + el.id))) return;
      var src = el.tagName.toLowerCase();
      if (el.id) src += '#' + el.id;
      if (el.className) src += '.' + String(el.className).trim().split(/\s+/).slice(0, 3).join('.');
      add(
        'Overlay DOM',
        t,
        'element: ' +
          src +
          '\nposition: ' +
          st.position +
          '  rect: ' +
          Math.round(r.left) +
          ',' +
          Math.round(r.top) +
          ' ' +
          Math.round(r.width) +
          'x' +
          Math.round(r.height) +
          '\nstyle.display=' +
          st.display
      );
      el.style.setProperty('outline', '2px solid #f59e0b', 'important');
      el.style.setProperty('z-index', '2147483646', 'important');
    });

    document.querySelectorAll('ins.adsbygoogle').forEach(function (ins) {
      var st = ins.getAttribute('data-ad-status') || '(no status)';
      add('AdSense slot', 'ins.adsbygoogle — data-ad-status=' + st, ins.outerHTML.slice(0, 400));
    });
  }

  function hookConsole() {
    ['error', 'warn'].forEach(function (level) {
      var orig = console[level];
      console[level] = function () {
        var msg = Array.prototype.map.call(arguments, String).join(' ');
        if (/ads|tag|pub|403|404|blocked|failed/i.test(msg)) {
          add('console.' + level, msg);
        }
        return orig.apply(console, arguments);
      };
    });
  }

  function watchIframe() {
    var iframe = document.getElementById('playerIframe');
    if (!iframe) return;
    iframe.addEventListener('load', function () {
      var src = iframe.getAttribute('src') || '';
      var data = iframe.getAttribute('data-mm-play') || '';
      add('Game iframe loaded', 'src=' + src, 'data-mm-play=' + data);
    });
    iframe.addEventListener('error', function () {
      add('Game iframe error', 'Không load được iframe game', iframe.getAttribute('src') || '');
    });
  }

  function explainIfAdsense() {
    if (!document.querySelector('script[src*="adsbygoogle.js"]')) return;
    add(
      'Giải thích (AdSense)',
      'Toast đỏ góc phải thường là cảnh báo AdSense chỉ publisher thấy — không phải lỗi game.\n' +
        'Trên localhost (127.0.0.1) domain chưa được duyệt → Google hiện "Lỗi thẻ / Tag error" hoặc bản dịch "Máy chủ…".\n' +
        'Trên monkeymart.one thật sẽ hết nếu ad unit + domain đúng; localhost có thể bỏ qua.',
      'client=ca-pub-4151519079019358'
    );
  }

  function injectStyles() {
    if (document.getElementById('mm-diag-style')) return;
    var s = document.createElement('style');
    s.id = 'mm-diag-style';
    s.textContent =
      '#mm-diag-panel{position:fixed;top:12px;right:12px;left:12px;max-width:520px;margin-left:auto;z-index:2147483647;' +
      'background:#1e1b4b;color:#f8fafc;border:2px solid #f59e0b;border-radius:12px;font:13px/1.45 system-ui,sans-serif;' +
      'box-shadow:0 12px 40px rgba(0,0,0,.45);max-height:min(70vh,520px);display:flex;flex-direction:column}' +
      '#mm-diag-panel.is-collapsed .mm-diag-body{display:none}' +
      '.mm-diag-head{display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.12)}' +
      '.mm-diag-head strong{flex:1}.mm-diag-sub{font-size:11px;opacity:.75}' +
      '#mm-diag-close{border:0;background:#f59e0b;color:#111827;border-radius:6px;width:28px;height:28px;cursor:pointer;font-size:18px}' +
      '.mm-diag-body{overflow:auto;padding:10px 12px}' +
      '.mm-diag-item{margin:0 0 10px;padding:8px 10px;background:rgba(255,255,255,.06);border-radius:8px}' +
      '.mm-diag-kind{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#fbbf24;margin-bottom:4px}' +
      '.mm-diag-text,.mm-diag-detail{margin:0;white-space:pre-wrap;word-break:break-word;font:12px/1.4 ui-monospace,monospace}' +
      '.mm-diag-detail{opacity:.8;margin-top:6px;font-size:11px}';
    document.head.appendChild(s);
  }

  function run() {
    injectStyles();
    ensurePanel();
    hookConsole();
    watchIframe();
    explainIfAdsense();
    scanOverlays();
    setInterval(scanOverlays, 2000);
    try {
      new MutationObserver(scanOverlays).observe(document.body, { childList: true, subtree: true });
    } catch (e) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
