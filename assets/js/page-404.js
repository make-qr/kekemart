(function () {
  'use strict';

  function esc(s) {
    var d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }

  function slugFromPath(path) {
    return String(path || '').replace(/\//g, '-');
  }

  function hashFromImg(url) {
    if (!url) return '';
    var m = String(url).match(/static\.wgplayground\.com\/([a-f0-9]{32})\//i);
    return m ? m[1] : '';
  }

  function localGameHref(item) {
    var routes = window.WGP_GAME_ROUTES || {};
    var url = item && item.url;
    if (url && routes[url]) return routes[url].replace(/^\.\.\//, '');
    var m = (url || '').match(/\/game\/(.+?)\/?$/);
    if (m) return 'games/' + slugFromPath(m[1]) + '.html';
    var h = hashFromImg(item && item.img);
    if (h) return 'game.html?ifr=' + encodeURIComponent(h);
    return 'index.html';
  }

  function resolveImg(url) {
    return (window.MM_resolveImg && window.MM_resolveImg(url)) || url || '';
  }

  function makeCard(item) {
    var href = localGameHref(item);
    var img = resolveImg(item.img || '');
    var art = img
      ? ' style="background-image:url(\'' + img.replace(/'/g, '%27') + '\')"'
      : '';
    var pip = item.pip === 'hot' ? '<span class="pip hot">HOT</span>' : item.pip === 'new' ? '<span class="pip new">NEW</span>' : '';
    var by = item.by ? '<span class="by">' + esc(item.by) + '</span>' : '';
    return (
      '<a class="card" href="' +
      esc(href) +
      '" aria-label="' +
      esc(item.name) +
      '" style="--c:' +
      (item.c || '#6366f1') +
      '">' +
      pip +
      '<div class="art"' +
      art +
      '></div>' +
      '<div class="title-default"><h3>' +
      esc(item.name) +
      '</h3></div>' +
      '<div class="veil"></div>' +
      '<div class="body"><h3>' +
      esc(item.name) +
      '</h3>' +
      by +
      '</div>' +
      '<span class="play-circle"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span>' +
      '</a>'
    );
  }

  function renderGrid(id, items) {
    var el = document.getElementById(id);
    if (!el) return;
    if (!items || !items.length) {
      el.innerHTML = '<p class="page-404-empty">No games in this section yet.</p>';
      return;
    }
    el.innerHTML = items.map(makeCard).join('');
  }

  function init() {
    var pathEl = document.getElementById('page404-path');
    if (pathEl) {
      var p = window.location.pathname || '/';
      pathEl.textContent = p.length > 72 ? '…' + p.slice(-69) : p;
    }

    var data = window.WG_404_DATA || {};
    renderGrid('grid-404-trending', data.trending || []);
    renderGrid('grid-404-new', data.new || []);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
