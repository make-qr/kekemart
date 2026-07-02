(function () {
  'use strict';

  var FAV_KEY = 'wg_favourites';
  var LIMIT_RECOMMEND = 12;
  var LIMIT_CLASSICS = 18;
  var CLASSIC_SLUGS = [
    'slope',
    'cookie-clicker',
    'fnaf-1',
    'moto-x3m',
    'subway-surfers',
    'retro-bowl',
    '1v1.lol',
    'tunnel-rush',
    'drift-boss',
    'vex-3',
    'drift-hunters',
    'pacman',
  ];

  function getGrids() {
    if (window.__WG_GRIDS__) return window.__WG_GRIDS__;
    return (window.WG_DATA && window.WG_DATA.grids) || {};
  }

  function pagePrefix() {
    return location.pathname.indexOf('/games/') !== -1 ? '../' : '';
  }

  function esc(s) {
    var d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }

  function readFavs() {
    try {
      var raw = localStorage.getItem(FAV_KEY);
      var list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list) ? list : [];
    } catch (e) {
      return [];
    }
  }

  function currentGameUrl() {
    var g = window.WG_GAME || {};
    return (g.url || '').replace(/[?#].*$/, '');
  }

  function normalizeUrl(url) {
    if (!url) return '';
    if (window.MM_normalizeGameHref) return window.MM_normalizeGameHref(url);
    var p = pagePrefix();
    if (url.indexOf('http') === 0) {
      var routes = window.WGP_GAME_ROUTES || {};
      return routes[url] ? normalizeUrl(routes[url]) : url;
    }
    if (p && url.indexOf('../') !== 0 && url.indexOf('games/') === 0) return p + url;
    return url;
  }

  function localImg(url) {
    return (window.MM_resolveImg && window.MM_resolveImg(url)) || url || '';
  }

  function slugFromWgpUrl(url) {
    var m = (url || '').match(/\/game\/(.+?)\/?$/);
    return m ? m[1].replace(/\//g, '-') : '';
  }

  function catalogEntryFromItem(item) {
    var url = item.url || '';
    var path = '';
    var m = url.match(/\/game\/(.+?)\/?$/);
    if (m) path = m[1];
    else if (url.indexOf('games/mm-') !== -1) {
      path = 'mm/' + url.replace(/^.*games\/mm-/, '').replace(/\.html.*$/, '');
    }
    var cat = window.WGP_CATALOG || {};
    if (path && cat[path]) return cat[path];
    var native = window.MM_NATIVE_CATALOG || {};
    var slug = path.replace(/^mm\//, '');
    if (native[slug]) return native[slug];
    return null;
  }

  function itemCats(item) {
    var entry = catalogEntryFromItem(item);
    if (entry && entry.cats && entry.cats.length) return entry.cats;
    if (item.cats && item.cats.length) return item.cats;
    if (item.meta) {
      var first = String(item.meta).split('·')[0].trim();
      if (first) return [first];
    }
    return [];
  }

  function favPayload(item) {
    return encodeURIComponent(
      JSON.stringify({
        name: item.name || '',
        by: item.by || '',
        img: item.img || item.image || '',
        url: item.url || '',
        c: item.c || '',
        pip: item.pip || '',
        preview: item.preview || '',
      })
    );
  }

  function itemKey(item) {
    return (item.url || '') + '|' + (item.name || '');
  }

  function itemForCard(item) {
    return {
      name: item.name || '',
      by: item.by || '',
      img: localImg(item.img || item.image || item.bg || ''),
      url: normalizeUrl(item.url || ''),
      c: item.c || '#6366f1',
      pip: item.pip || '',
      preview: item.preview || '',
      big: !!item.big,
    };
  }

  function cardHtml(item) {
    var g = itemForCard(item);
    if (typeof window.makeCard === 'function') {
      return window.makeCard(g, g.big);
    }
    return makeCard(item);
  }

  function getGridColumns(el) {
    if (!el) return 6;
    var cols = getComputedStyle(el).gridTemplateColumns.split(' ').filter(Boolean).length;
    return cols > 0 ? cols : 6;
  }

  function gridCellCount(items) {
    var total = 0;
    (items || []).forEach(function (item) {
      total += item.big ? 4 : 1;
    });
    return total;
  }

  function buildTrendNewFillers(usedKeys, preferPip) {
    var grids = getGrids();
    var list = [];
    var seen = usedKeys || {};

    function tryAdd(item, pipOverride) {
      if (!item || !item.name || !item.url) return;
      var key = itemKey(item);
      if (seen[key]) return;
      seen[key] = true;
      var copy = Object.assign({}, item);
      if (pipOverride) copy.pip = pipOverride;
      list.push(copy);
    }

    var opposite = preferPip === 'hot' ? grids.new || [] : grids.trending || [];
    var same = preferPip === 'hot' ? grids.trending || [] : grids.new || [];
    opposite.forEach(function (item) {
      tryAdd(item, preferPip === 'hot' ? 'new' : 'hot');
    });
    same.forEach(function (item) {
      tryAdd(item, preferPip);
    });

    var cat = window.WGP_CATALOG || {};
    Object.keys(cat).forEach(function (path) {
      var g = cat[path];
      if (!g || !g.ifr) return;
      var pip = g.pip || (g.featured ? 'hot' : '');
      if (pip !== 'hot' && pip !== 'new') return;
      tryAdd(
        {
          name: g.name,
          by: g.by,
          url: pagePrefix() + 'games/' + path.replace(/\//g, '-') + '.html',
          img: g.img,
          c: g.c,
          pip: pip,
          cats: g.cats,
        },
        pip
      );
    });

    if (preferPip === 'hot') {
      list.sort(function (a, b) {
        var an = a.pip === 'new' ? 0 : a.pip === 'hot' ? 1 : 2;
        var bn = b.pip === 'new' ? 0 : b.pip === 'hot' ? 1 : 2;
        return an - bn;
      });
    } else if (preferPip === 'new') {
      list.sort(function (a, b) {
        var ah = a.pip === 'hot' ? 0 : a.pip === 'new' ? 1 : 2;
        var bh = b.pip === 'hot' ? 0 : b.pip === 'new' ? 1 : 2;
        return ah - bh;
      });
    }

    return excludeCurrent(list);
  }

  function padGridItems(items, cols, fillers) {
    var out = (items || []).slice();
    if (!out.length) return out;

    var seen = {};
    out.forEach(function (item) {
      seen[itemKey(item)] = true;
    });

    var remainder = gridCellCount(out) % cols;
    if (remainder === 0) return out;

    var need = cols - remainder;
    for (var i = 0; i < fillers.length && need > 0; i++) {
      var filler = fillers[i];
      if (!filler || filler.big) continue;
      var key = itemKey(filler);
      if (seen[key]) continue;
      seen[key] = true;
      out.push(filler);
      need -= 1;
    }
    return out;
  }

  function makeCard(item) {
    var g = itemForCard(item);
    var href = g.url;
    var img = g.img;
    var bigClass = g.big ? ' card-2x' : '';
    var art = img ? " style=\"background-image:url('" + img.replace(/'/g, '%27') + "')\"" : '';
    var pip =
      g.pip === 'hot'
        ? '<span class="pip hot">HOT</span>'
        : g.pip === 'new'
          ? '<span class="pip new">NEW</span>'
          : g.pip === 'editor'
            ? '<span class="pip editor">Editor\'s pick</span>'
            : '';
    var by = g.by ? '<span class="by">' + esc(g.by) + '</span>' : '';
    var isFav =
      window.WGFav && window.WGFav.isFav && window.WGFav.isFav(item.url) ? ' is-fav' : '';
    var preview = g.preview
      ? ' data-preview="' + encodeURIComponent(g.preview) + '"'
      : '';
    return (
      '<a class="card' +
      bigClass +
      '" href="' +
      esc(href) +
      '" aria-label="' +
      esc(g.name) +
      '" data-fav="' +
      favPayload(item) +
      '"' +
      preview +
      ' style="--c:' +
      g.c +
      '">' +
      pip +
      '<div class="art"' +
      art +
      '></div>' +
      '<button type="button" class="card-fav' +
      isFav +
      '" aria-label="Toggle favourite">' +
      '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21l-1.45-1.32C5.4 14.36 2 11.28 2 7.5 2 5 4 3 6.5 3c1.74 0 3.41.81 4.5 2.09C12.09 3.81 13.76 3 15.5 3 18 3 20 5 20 7.5c0 3.78-3.4 6.86-8.55 12.18L12 21z"/></svg>' +
      '</button>' +
      '<div class="title-default"><h3>' +
      esc(g.name) +
      '</h3></div>' +
      '<div class="veil"></div>' +
      '<div class="body"><h3>' +
      esc(g.name) +
      '</h3>' +
      by +
      '</div>' +
      '<span class="play-circle"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span>' +
      '</a>'
    );
  }

  function renderGrid(id, items, preferPip) {
    var el = document.getElementById(id);
    if (!el) return;
    if (!items || !items.length) {
      el.innerHTML = '';
      return;
    }

    var used = {};
    items.forEach(function (item) {
      used[itemKey(item)] = true;
    });
    var fillers = buildTrendNewFillers(used, preferPip);
    var cols = getGridColumns(el);
    var padded = padGridItems(items, cols, fillers);
    el.innerHTML = padded.map(cardHtml).join('');

    var cols2 = getGridColumns(el);
    if (cols2 !== cols) {
      padded = padGridItems(items, cols2, fillers);
      el.innerHTML = padded.map(cardHtml).join('');
    }
  }

  function excludeCurrent(items) {
    var cur = currentGameUrl();
    var curName = (window.WG_GAME && window.WG_GAME.name) || '';
    return (items || []).filter(function (item) {
      if (!item) return false;
      var u = normalizeUrl(item.url || '');
      if (cur && u === normalizeUrl(cur)) return false;
      if (curName && item.name === curName) return false;
      return true;
    });
  }

  function allCatalogPool() {
    var pool = [];
    var seen = {};
    var grids = getGrids();

    function add(item) {
      if (!item || !item.name || !item.url) return;
      var key = item.url + '|' + item.name;
      if (seen[key]) return;
      seen[key] = true;
      pool.push(item);
    }

    (grids.trending || []).forEach(add);
    (grids.new || []).forEach(add);

    var cat = window.WGP_CATALOG || {};
    Object.keys(cat).forEach(function (path) {
      var g = cat[path];
      if (!g) return;
      var slug = path.replace(/\//g, '-');
      add({
        name: g.name,
        by: g.by,
        url: pagePrefix() + 'games/' + slug + '.html',
        img: g.img,
        c: g.c,
        cats: g.cats,
      });
    });

    var native = window.MM_NATIVE_CATALOG || {};
    Object.keys(native).forEach(function (slug) {
      var g = native[slug];
      if (!g || g.embedMode === 'fallback') return;
      add({
        name: g.name,
        by: 'MonkeyMart.one',
        url: pagePrefix() + 'games/mm-' + slug + '.html',
        img: g.img,
        c: g.c,
        cats: g.cats,
      });
    });

    return pool;
  }

  function buildClassics() {
    var cat = window.MM_NATIVE_CATALOG || {};
    var slugs = Object.keys(cat);
    if (!slugs.length) return [];

    function priorityIndex(slug) {
      var i = CLASSIC_SLUGS.indexOf(slug);
      return i === -1 ? 999 : i;
    }

    return slugs
      .map(function (slug) {
        var g = cat[slug];
        return { slug: slug, g: g };
      })
      .filter(function (item) {
        return item.g && item.g.embedMode !== 'fallback';
      })
      .sort(function (a, b) {
        var ap = priorityIndex(a.slug);
        var bp = priorityIndex(b.slug);
        if (ap !== bp) return ap - bp;
        if (a.g.popular && !b.g.popular) return -1;
        if (!a.g.popular && b.g.popular) return 1;
        return (a.g.name || '').localeCompare(b.g.name || '');
      })
      .slice(0, LIMIT_CLASSICS)
      .map(function (item) {
        var g = item.g;
        return {
          name: g.name,
          by: 'MonkeyMart.one',
          url: pagePrefix() + 'games/mm-' + item.slug + '.html',
          img: g.img,
          c: g.c || '#16a34a',
          cats: g.cats,
        };
      });
  }

  function ensureClassicsSection() {
    var bottom = document.getElementById('mmGameBottom');
    if (!bottom || document.getElementById('grid-game-classics')) return;

    var block =
      '<div class="section-head mm-game-classics-head">' +
      '<h2><span class="dot" style="background:#16a34a"></span>MonkeyMart classics</h2>' +
      '<a class="more" href="' +
      pagePrefix() +
      'games-catalogue.html?cat=monkeymart-classics">See all &rarr;</a>' +
      '</div>' +
      '<div class="grid grid-dense" id="grid-game-classics"></div>';
    bottom.insertAdjacentHTML('beforeend', block);
  }

  function loadNativeCatalog(done) {
    if (window.MM_NATIVE_CATALOG) {
      done();
      return;
    }
    var existing = document.querySelector('script[src*="mm-native-catalog.js"]');
    if (existing) {
      var waits = 0;
      var iv = setInterval(function () {
        waits += 1;
        if (window.MM_NATIVE_CATALOG || waits >= 40) {
          clearInterval(iv);
          done();
        }
      }, 100);
      return;
    }
    var s = document.createElement('script');
    s.src = pagePrefix() + 'assets/js/mm-native-catalog.js';
    s.onload = done;
    s.onerror = done;
    document.head.appendChild(s);
  }

  function buildRecommendations() {
    var favs = readFavs();
    if (!favs.length) return [];

    var favCats = {};
    favs.forEach(function (f) {
      itemCats(f).forEach(function (c) {
        favCats[c] = (favCats[c] || 0) + 1;
      });
    });
    var topCats = Object.keys(favCats).sort(function (a, b) {
      return favCats[b] - favCats[a];
    });
    if (!topCats.length) return [];

    var pool = allCatalogPool();
    var scored = pool
      .map(function (item) {
        var cats = itemCats(item);
        var score = 0;
        cats.forEach(function (c) {
          score += favCats[c] || 0;
        });
        return { item: item, score: score };
      })
      .filter(function (row) {
        return row.score > 0;
      })
      .sort(function (a, b) {
        if (b.score !== a.score) return b.score - a.score;
        return (a.item.name || '').localeCompare(b.item.name || '');
      });

    var out = [];
    var seen = {};
    scored.forEach(function (row) {
      var key = row.item.url + '|' + row.item.name;
      if (seen[key]) return;
      seen[key] = true;
      out.push(row.item);
    });
    return excludeCurrent(out).slice(0, LIMIT_RECOMMEND);
  }

  function renderBottom() {
    var grids = getGrids();
    var trending = excludeCurrent(grids.trending || []);
    var newest = excludeCurrent(grids.new || []);
    var recommend = buildRecommendations();
    var classics = excludeCurrent(buildClassics());

    ensureClassicsSection();
    renderGrid('grid-game-trending', trending, 'hot');
    renderGrid('grid-game-new', newest, 'new');
    renderGrid('grid-game-recommend', recommend, 'hot');
    renderGrid('grid-game-classics', classics, 'hot');

    var head = document.getElementById('mmRecommendHead');
    var section = document.getElementById('mmGameBottom');
    if (head) head.hidden = recommend.length === 0;
    if (section && !trending.length && !newest.length && !recommend.length && !classics.length) {
      section.hidden = true;
    }
  }

  var resizeTimer;
  function onResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderBottom, 150);
  }

  function bindFavRefresh() {
    window.addEventListener('mm-rail-sync', renderBottom);
    window.addEventListener('storage', function (e) {
      if (e.key === FAV_KEY) renderBottom();
    });
    window.addEventListener('resize', onResize);
  }

  function init() {
    if (!document.getElementById('mmGameBottom')) return;
    loadNativeCatalog(function () {
      renderBottom();
      bindFavRefresh();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
