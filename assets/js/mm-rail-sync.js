(function () {
  'use strict';

  var FAV_KEY = 'wg_favourites';
  var REC_KEY = 'wg_recent';

  function pagePrefix() {
    return location.pathname.indexOf('/games/') !== -1 ? '../' : '';
  }

  function readJson(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeJson(key, val) {
    try {
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) {}
  }

  function normalizeGameUrl(url) {
    if (!url || url.indexOf('http') === 0) return url;
    if (window.MM_normalizeGameHref) return window.MM_normalizeGameHref(url);
    var p = pagePrefix();
    if (!p) return url;
    if (url.indexOf('../') === 0 || url.charAt(0) === '/') return url;
    if (url.indexOf('games/') === 0) return p + url;
    if (/^mm-/.test(url)) return p + 'games/' + url;
    if (/\.html(\?|#|$)/.test(url)) return p + (url.indexOf('games/') === 0 ? url : 'games/' + url);
    if (url === 'monkey-mart.html' || url === 'index.html' || url.indexOf('games-catalogue') === 0) {
      return p + url;
    }
    return p + url;
  }

  function normalizeRecentList() {
    var list = readJson(REC_KEY, []);
    if (!Array.isArray(list) || !list.length) return;
    var changed = false;
    list = list.map(function (item) {
      if (!item || !item.url) return item;
      var fixed = normalizeGameUrl(item.url);
      if (fixed !== item.url) {
        changed = true;
        item = Object.assign({}, item, { url: fixed });
      }
      if (item.img && item.img.indexOf('http') !== 0 && item.img.indexOf('..') !== 0) {
        var img = item.img.indexOf('assets/') === 0 || item.img.indexOf('hosted-games/') === 0
          ? pagePrefix() + item.img
          : item.img;
        if (img !== item.img) {
          changed = true;
          item = Object.assign({}, item, { img: img });
        }
      }
      return item;
    });
    if (changed) writeJson(REC_KEY, list);
  }

  function normalizeFavList() {
    var list = readJson(FAV_KEY, []);
    if (!Array.isArray(list) || !list.length) return;
    var changed = false;
    list = list.map(function (item) {
      if (!item || !item.url) return item;
      var fixed = normalizeGameUrl(item.url);
      if (fixed !== item.url) {
        changed = true;
        return Object.assign({}, item, { url: fixed });
      }
      return item;
    });
    if (changed) writeJson(FAV_KEY, list);
  }

  function setCountEl(id, n) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = String(n);
    el.setAttribute('data-empty', n === 0 ? 'true' : 'false');
  }

  function syncRailCounts() {
    var favs = readJson(FAV_KEY, []);
    var recent = readJson(REC_KEY, []);
    if (!Array.isArray(favs)) favs = [];
    if (!Array.isArray(recent)) recent = [];
    setCountEl('favouritesCount', favs.length);
    setCountEl('recentCount', recent.length);
  }

  function catalogGameCard(path, g, localUrl) {
    return {
      name: g.name || path,
      by: g.by || 'MonkeyMart.one',
      url: localUrl,
      img: g.img || '',
      c: g.c || '#6366f1',
    };
  }

  function buildSurprisePool() {
    var pool = [];
    var seen = {};
    var p = pagePrefix();

    function add(item) {
      if (!item || !item.url || !item.name) return;
      var key = item.url + '|' + item.name;
      if (seen[key]) return;
      seen[key] = true;
      pool.push({
        name: item.name,
        by: item.by || '',
        url: normalizeGameUrl(item.url),
        img: item.img || '',
        c: item.c || '#6366f1',
      });
    }

    var wg = window.WGP_CATALOG || {};
    Object.keys(wg).forEach(function (path) {
      var g = wg[path];
      if (!g || !g.ifr) return;
      var slug = path.replace(/\//g, '-');
      add(catalogGameCard(path, g, p + 'games/' + slug + '.html'));
    });

    var native = window.MM_NATIVE_CATALOG || {};
    Object.keys(native).forEach(function (slug) {
      var g = native[slug];
      if (!g) return;
      add(catalogGameCard('mm/' + slug, g, p + 'games/mm-' + slug + '.html'));
    });

    add({
      name: 'Monkey Mart',
      by: 'MonkeyMart.one',
      url: p + 'monkey-mart.html',
      img: p + 'assets/images/site/monkey-mart-logo.png',
      c: '#16a34a',
    });

    if (pool.length) window.__surprisePool = pool;
    return pool;
  }

  function pushCurrentGameRecent() {
    var g = window.WG_GAME;
    if (!g || !g.name) return;
    var entry = {
      name: g.name,
      url: normalizeGameUrl(g.url || location.pathname.split('/').pop()),
      img: g.image || g.img || '',
      by: (g.by || '').replace(/^by\s+/i, '') || 'MonkeyMart.one',
      ts: Date.now(),
    };
    if (window.WGFav && window.WGFav.pushRecent) {
      window.WGFav.pushRecent(entry);
      return;
    }
    var list = readJson(REC_KEY, []);
    if (!Array.isArray(list)) list = [];
    list = list.filter(function (x) {
      return x && x.url !== entry.url && x.name !== entry.name;
    });
    list.unshift(entry);
    writeJson(REC_KEY, list.slice(0, 40));
  }

  function patchWGFav() {
    if (!window.WGFav || window.WGFav.__mmPatched) return;
    window.WGFav.__mmPatched = true;
    ['pushRecent', 'toggleFav', 'pushFav', 'removeFav'].forEach(function (fn) {
      if (!window.WGFav[fn]) return;
      var orig = window.WGFav[fn];
      window.WGFav[fn] = function () {
        var out = orig.apply(this, arguments);
        syncRailCounts();
        window.dispatchEvent(new CustomEvent('mm-rail-sync'));
        return out;
      };
    });
    if (window.WGFav.listFavs) {
      var origList = window.WGFav.listFavs;
      window.WGFav.listFavs = function () {
        var list = origList.call(this);
        return (list || []).map(function (item) {
          if (!item || !item.url) return item;
          return Object.assign({}, item, { url: normalizeGameUrl(item.url) });
        });
      };
    }
  }

  function emitSync() {
    normalizeRecentList();
    normalizeFavList();
    buildSurprisePool();
    syncRailCounts();
  }

  function run() {
    emitSync();
    patchWGFav();
    pushCurrentGameRecent();
    syncRailCounts();

    window.addEventListener('storage', function (e) {
      if (e.key === FAV_KEY || e.key === REC_KEY) syncRailCounts();
    });
    window.addEventListener('mm-rail-sync', syncRailCounts);
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) emitSync();
    });
  }

  window.MM_RAIL_SYNC = {
    sync: emitSync,
    syncCounts: syncRailCounts,
    buildSurprisePool: buildSurprisePool,
    normalizeGameUrl: normalizeGameUrl,
    pushCurrentGameRecent: pushCurrentGameRecent,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run, { once: true });
  } else {
    run();
  }
})();
