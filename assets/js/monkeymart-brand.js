(function () {
  'use strict';

  var CFG = window.MM_BRAND || {
    siteName: 'MonkeyMart.one',
    brandShort: 'MonkeyMart',
    brandHtml: 'Monkey<span>Mart</span>',
    searchPlaceholder: 'Search games…',
    heroGame: null,
  };

  var done = false;

  function pagePrefix() {
    var path = location.pathname;
    if (path.indexOf('/games/') !== -1 || path.indexOf('/blog/') !== -1 || path.indexOf('/game/') !== -1) {
      return '../';
    }
    if (
      path.indexOf('/how-to-play-monkey-mart/') !== -1 ||
      path.indexOf('/monkey-mart-tips/') !== -1 ||
      path.indexOf('/monkey-mart-unblocked/') !== -1
    ) {
      return '../';
    }
    return '';
  }

  function logoSrc() {
    var raw = (CFG.heroGame && CFG.heroGame.img) || 'assets/images/site/monkey-mart-logo.png';
    if (raw.indexOf('http://') === 0 || raw.indexOf('https://') === 0) return raw;
    if (raw.indexOf('../') === 0) return raw;
    return pagePrefix() + raw.replace(/^\//, '');
  }

  function ensureLogoImg(wrap) {
    if (!wrap) return;
    var img = wrap.querySelector('img.mm-logo');
    var src = logoSrc();
    if (!img) {
      img = document.createElement('img');
      img.className = 'mm-logo';
      img.width = 40;
      img.height = 40;
      img.alt = CFG.brandShort || 'MonkeyMart';
      wrap.classList.add('mm-logo-wrap');
      var svg = wrap.querySelector('svg');
      if (svg) svg.replaceWith(img);
      else wrap.appendChild(img);
    }
    if (img.getAttribute('src') !== src) img.setAttribute('src', src);
  }

  function patchBrand() {
    if (!document.body) return;
    var homeLabel = (CFG.siteName || 'MonkeyMart.one') + ' home';
    document.querySelectorAll('a.brand').forEach(function (a) {
      a.setAttribute('aria-label', homeLabel);
    });
    document.querySelectorAll('.brand-text').forEach(function (el) {
      if (CFG.brandHtml) el.innerHTML = CFG.brandHtml;
      else if (/WG/i.test(el.textContent || '')) el.innerHTML = 'Monkey<span>Mart</span>';
    });
    document.querySelectorAll('.brand-mark').forEach(function (wrap) {
      ensureLogoImg(wrap);
    });
    document.querySelectorAll('.auth-modal-logo, .brag-live-logo img').forEach(function (img) {
      if (img.src && img.src.indexOf('logo-square.svg') !== -1) {
        img.src = logoSrc();
        img.alt = CFG.brandShort || 'MonkeyMart';
      }
    });
    document.querySelectorAll('.brag-live-wordmark').forEach(function (el) {
      if (/WG/i.test(el.textContent || '')) {
        el.innerHTML = '<b>Monkey</b><span>Mart</span>';
      }
    });
    document.querySelectorAll('input[type="search"]').forEach(function (inp) {
      if (/wgplayground|2,800|2800/i.test(inp.placeholder || '')) {
        inp.placeholder = CFG.searchPlaceholder;
      }
    });
    document.title = document.title
      .replace(/WGPlayground/gi, CFG.siteName)
      .replace(/WGPlayGround/gi, CFG.siteName);
  }

  function patchLinks() {
    var p = pagePrefix();
    document.querySelectorAll('a[href*="wgplayground.com"]').forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href.indexOf('/game/') !== -1) return;
      if (href.indexOf('games-catalogue') !== -1 || href.indexOf('/selection/') !== -1) {
        var cat = href.match(/games-catalogue\/games\/([^/?#]+)/i);
        a.setAttribute('href', cat ? p + 'games-catalogue.html?cat=' + encodeURIComponent(cat[1].toLowerCase()) : p + 'games-catalogue.html');
      } else if (href.indexOf('developers') !== -1 || href.indexOf('publishers') !== -1) {
        a.style.display = 'none';
      } else if (href.indexOf('privacy') !== -1 || href.indexOf('terms') !== -1 || href.indexOf('contact') !== -1) {
        a.style.display = 'none';
      } else {
        a.setAttribute('href', p + 'index.html');
      }
    });
    document.querySelectorAll('.section-head .more, #catBrowseAll').forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href.indexOf('wgplayground.com') === -1) return;
      if (href.indexOf('games-catalogue') !== -1) {
        var sort = href.match(/sort-(\d+)/);
        var cat = href.match(/games-catalogue\/games\/([^/?#]+)/i);
        if (cat) {
          a.setAttribute('href', p + 'games-catalogue.html?cat=' + encodeURIComponent(cat[1].toLowerCase()));
        } else if (sort) {
          a.setAttribute('href', p + 'games-catalogue.html?sort=' + sort[1]);
        } else {
          a.setAttribute('href', p + 'games-catalogue.html');
        }
      } else {
        a.setAttribute('href', p + 'games-catalogue.html');
      }
    });
    document.querySelectorAll('.rail-catalogue').forEach(function (a) {
      a.setAttribute('href', p + 'games-catalogue.html');
    });
  }

  function patchSearch() {
    var p = pagePrefix();
    document.querySelectorAll('form.search').forEach(function (form) {
      if (form.dataset.mmSearch) return;
      form.dataset.mmSearch = '1';
      form.setAttribute('action', p + 'games-catalogue.html');
      form.setAttribute('method', 'get');
      var inp = form.querySelector('input[name="q"]') || form.querySelector('input[type="search"]');
      if (inp && !inp.getAttribute('name')) inp.setAttribute('name', 'q');
    });
  }

  function patchTopNav() {
    var p = pagePrefix();
    document.querySelectorAll('.top-nav a').forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href.indexOf('wgplayground.com/games-catalogue') !== -1 || href === 'games-catalogue.html') {
        a.setAttribute('href', p + 'games-catalogue.html');
        if (/^games$/i.test((a.textContent || '').trim())) a.textContent = 'All games';
      }
      if (href === 'index.html' || href === p + 'index.html') {
        a.textContent = 'Home';
      }
    });
    document.querySelectorAll('.top-nav').forEach(function (nav) {
      if (nav.dataset.mmTopNav) return;
      var links = nav.querySelectorAll('a');
      if (links.length !== 1) return;
      var only = links[0];
      var catHref = p + 'games-catalogue.html';
      if ((only.getAttribute('href') || '').indexOf('games-catalogue') === -1) return;
      only.classList.remove('active');
      only.textContent = 'All games';
      var home = document.createElement('a');
      home.setAttribute('href', p + 'index.html');
      home.textContent = 'Home';
      nav.insertBefore(home, only);
      nav.dataset.mmTopNav = '1';
    });
  }

  function hidePublisherOverlays() {
    var re = /Lỗi mà chỉ|Error that only you will see|Error that only you/i;
    function scan() {
      document.querySelectorAll('body div, body span, body ins').forEach(function (el) {
        if (el.closest('.topbar, .rail, footer, .player-frame, .embed-modal')) return;
        var t = (el.textContent || '').trim();
        if (!t || t.length > 180 || !re.test(t)) return;
        var box = el;
        for (var i = 0; i < 4 && box.parentElement; i++) {
          if (box.style.position === 'fixed' || (box.className && String(box.className).indexOf('toast') !== -1)) break;
          box = box.parentElement;
        }
        box.style.setProperty('display', 'none', 'important');
        box.setAttribute('aria-hidden', 'true');
      });
    }
    scan();
    try {
      new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
    } catch (e) {}
  }

  function patchSearchKbd() {
    document.querySelectorAll('.topbar form.search kbd').forEach(function (el) {
      el.remove();
    });
  }

  function patchRail() {
    var p = pagePrefix();
    var home = document.querySelector('.rail-item[href="index.html"], .rail-item[href="' + p + 'index.html"]');
    if (!home || document.getElementById('mmRailPlay')) return;
    var a = document.createElement('a');
    a.className = 'rail-item';
    a.id = 'mmRailPlay';
    a.href = p + 'monkey-mart.html';
    a.innerHTML =
      '<span class="ico" style="color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M6 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/></svg></span>' +
      '<span class="label">Monkey Mart</span>';
    home.parentNode.insertBefore(a, home.nextSibling);

    var youHead = document.querySelector('.rail-section--you h4');
    if (youHead) youHead.textContent = 'Your saves';
  }

  function patchFooter() {
    var grid = document.querySelector('footer .foot-grid');
    if (!grid || grid.dataset.mmFoot) return;
    grid.dataset.mmFoot = '1';
    var p = pagePrefix();
    var tagline = CFG.footerTagline || 'Play Monkey Mart and hundreds of free browser games.';
    var logo = logoSrc();
    grid.innerHTML =
      '<div>' +
      '<a class="brand" href="' + p + 'index.html" aria-label="MonkeyMart.one home">' +
      '<span class="brand-mark mm-logo-wrap" aria-hidden="true">' +
      '<img class="mm-logo" src="' + logo + '" alt="MonkeyMart" width="40" height="40" loading="lazy">' +
      '</span>' +
      '<span class="brand-text">' + (CFG.brandHtml || 'Monkey<span>Mart</span>') + '</span></a>' +
      '<p class="mm-foot-tagline">' + tagline + '</p>' +
      '</div>' +
      '<div><h5>Play</h5><ul>' +
      '<li><a href="' + p + 'monkey-mart.html">Monkey Mart</a></li>' +
      '<li><a href="' + p + 'games-catalogue.html">All games</a></li>' +
      '<li><a href="' + p + 'blog/index.html">Blog</a></li>' +
      '</ul></div>' +
      '<div><h5>Guides</h5><ul>' +
      '<li><a href="' + p + 'how-to-play-monkey-mart/index.html">How to play</a></li>' +
      '<li><a href="' + p + 'monkey-mart-tips/index.html">Tips &amp; tricks</a></li>' +
      '<li><a href="' + p + 'monkey-mart-unblocked/index.html">Unblocked</a></li>' +
      '<li><a href="' + p + 'about.html">About</a></li>' +
      '</ul></div>' +
      '<div><h5>Legal</h5><ul>' +
      '<li><a href="' + p + 'contact.html">Contact</a></li>' +
      '<li><a href="' + p + 'privacy.html">Privacy</a></li>' +
      '<li><a href="' + p + 'terms.html">Terms</a></li>' +
      '<li><a href="' + p + 'disclaimer.html">Copyright</a></li>' +
      '<li><a href="' + p + 'faq.html">FAQ</a></li>' +
      '</ul></div>';

    var bottom = document.querySelector('.foot-bottom');
    if (bottom) {
      bottom.innerHTML =
        '<span>© 2026 MonkeyMart.one</span>' +
        '<span>Free browser games · Saved on this device</span>';
    }
  }

  function run() {
    if (done) return;
    done = true;
    patchSearchKbd();
    patchBrand();
    patchLinks();
    patchSearch();
    patchTopNav();
    patchRail();
    patchFooter();
    hidePublisherOverlays();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run, { once: true });
  } else {
    run();
  }
})();
