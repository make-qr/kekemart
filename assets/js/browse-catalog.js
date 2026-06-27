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

  function localGamePage(path) {
    var href = 'games/' + slugFromPath(path) + '.html';
    return (window.MM_normalizeGameHref && window.MM_normalizeGameHref(href)) || href;
  }

  function makeCard(g) {
    var img = (window.MM_resolveImg && window.MM_resolveImg(g.img)) || g.img || '';
    var art = img
      ? ' style="background-image:url(\'' + img.replace(/'/g, '%27') + '\')"'
      : '';
    var by = g.by ? '<span class="by">' + esc(g.by) + '</span>' : '';
    var favPayload = encodeURIComponent(
      JSON.stringify({
        name: g.name,
        by: g.by || '',
        img: g.img || '',
        url: g._local,
        c: g.c || '#6366f1',
      })
    );
    var isFav =
      window.WGFav && window.WGFav.isFav && window.WGFav.isFav(g._local) ? ' is-fav' : '';
    return (
      '<a class="card" href="' +
      esc(g._local) +
      '" aria-label="' +
      esc(g.name) +
      '" data-fav="' +
      favPayload +
      '" style="--c:' +
      (g.c || '#6366f1') +
      '">' +
      '<div class="art"' +
      art +
      '></div>' +
      '<button type="button" class="card-fav' +
      isFav +
      '" aria-label="Toggle favourite">' +
      '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21l-1.45-1.32C5.4 14.36 2 11.28 2 7.5 2 5 4 3 6.5 3c1.74 0 3.41.81 4.5 2.09C12.09 3.81 13.76 3 15.5 3 18 3 20 5 20 7.5c0 3.78-3.4 6.86-8.55 12.18L12 21z"/></svg></button>' +
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

  function catSlug(name) {
    return String(name || '')
      .toLowerCase()
      .replace(/&/g, 'and')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }

  function catSlugLoose(name) {
    return catSlug(name).replace(/-and-/g, '-');
  }

  function catMatches(game, slug) {
    if (!slug) return true;
    if (window.MM_CATEGORIES && window.MM_CATEGORIES.gameMatchesSlug) {
      return window.MM_CATEGORIES.gameMatchesSlug(game, slug);
    }
    slug = slug.toLowerCase();
    return (game.cats || []).some(function (c) {
      return catSlug(c) === slug || catSlugLoose(c) === slug;
    });
  }

  function parseQuery() {
    var params = new URLSearchParams(window.location.search);
    return {
      q: (params.get('q') || '').trim(),
      cat: (params.get('cat') || '').trim().toLowerCase(),
    };
  }

  function pushQuery(q, cat) {
    var params = new URLSearchParams();
    if (q) params.set('q', q);
    if (cat) params.set('cat', cat);
    var qs = params.toString();
    var url = window.location.pathname.split('/').pop() + (qs ? '?' + qs : '');
    window.history.replaceState(null, '', url);
  }

  function buildGames() {
    var catalog = window.WGP_CATALOG || {};
    var games = [];
    Object.keys(catalog).forEach(function (path) {
      var g = catalog[path];
      if (!g || !g.ifr) return;
      games.push({
        path: path,
        name: g.name || path,
        by: g.by || '',
        img: g.img || '',
        c: g.c || '#6366f1',
        cats: g.cats || [],
        _local: localGamePage(path),
        _source: 'wgp',
      });
    });

    var native = window.MM_NATIVE_CATALOG || {};
    Object.keys(native).forEach(function (slug) {
      var g = native[slug];
      if (!g) return;
      games.push({
        path: 'mm/' + slug,
        name: g.name || slug,
        by: g.by || 'MonkeyMart.one',
        img: g.img || '',
        c: g.c || '#16a34a',
        cats: g.cats || ['MonkeyMart Classics'],
        _local: (function () {
          var href = 'games/mm-' + slug + '.html';
          return (window.MM_normalizeGameHref && window.MM_normalizeGameHref(href)) || href;
        })(),
        _source: 'native',
        _popular: !!g.popular,
      });
    });

    games.sort(function (a, b) {
      if (a._popular && !b._popular) return -1;
      if (!a._popular && b._popular) return 1;
      return a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
    });
    return games;
  }

  function collectCategories(games) {
    var counts = {};
    games.forEach(function (g) {
      (g.cats || []).forEach(function (cat) {
        if (!cat) return;
        counts[cat] = (counts[cat] || 0) + 1;
      });
    });
    return Object.keys(counts)
      .sort(function (a, b) {
        return counts[b] - counts[a] || a.localeCompare(b);
      })
      .map(function (name) {
        return { name: name, slug: catSlug(name), count: counts[name] };
      });
  }

  var PAGE_SIZE = 60;

  function render(state) {
    var grid = document.getElementById('catalogGrid');
    var empty = document.getElementById('catalogEmpty');
    var countEl = document.getElementById('catalogCount');
    var titleEl = document.getElementById('catalogResultsTitle');
    var subtitle = document.getElementById('catalogSubtitle');
    var loadBtn = document.getElementById('catalogLoadMore');
    if (!grid) return;

    var filtered = state.games.filter(function (g) {
      if (state.cat) {
        if (!catMatches(g, state.cat)) return false;
      }
      if (!state.q) return true;
      var hay = (g.name + ' ' + g.by + ' ' + (g.cats || []).join(' ')).toLowerCase();
      return hay.indexOf(state.q.toLowerCase()) !== -1;
    });

    if (state.q || state.cat) state.visible = filtered.length;
    var slice = filtered.slice(0, state.visible);

    grid.innerHTML = slice.map(makeCard).join('');
    if (countEl) {
      countEl.textContent =
        slice.length < filtered.length
          ? slice.length + ' of ' + filtered.length + ' games'
          : filtered.length + ' games';
    }
    var label = 'All games';
    if (state.cat) {
      if (window.MM_CATEGORIES && window.MM_CATEGORIES.labelForSlug) {
        label = window.MM_CATEGORIES.labelForSlug(state.cat);
      } else {
        for (var i = 0; i < state.categories.length; i++) {
          if (state.categories[i].slug === state.cat || catSlugLoose(state.categories[i].name) === state.cat) {
            label = state.categories[i].name;
            break;
          }
        }
        if (label === 'All games') label = 'Filtered games';
      }
    }
    if (titleEl) {
      titleEl.textContent = label;
      document.title = label + ' — MonkeyMart.one';
    }
    var crumb = document.querySelector('.breadcrumb [aria-current="page"]');
    if (crumb && state.cat) {
      crumb.textContent = label;
    }
    if (subtitle) {
      var nativeN = state.games.filter(function (g) { return g._source === 'native'; }).length;
      var wgpN = state.games.length - nativeN;
      subtitle.textContent =
        'Play ' + state.games.length + ' free browser games — ' +
        nativeN + ' MonkeyMart classics + ' + wgpN + ' casual titles. No download.';
    }
    if (empty) empty.hidden = filtered.length > 0;
    if (loadBtn) {
      var more = slice.length < filtered.length;
      loadBtn.hidden = !more;
      loadBtn.textContent = 'Load more games (' + (filtered.length - slice.length) + ' left)';
    }
  }

  function buildChipCategories(games) {
    if (window.MM_CATEGORIES && window.MM_CATEGORIES.buildList) {
      return window.MM_CATEGORIES.buildList().map(function (c) {
        return { name: c.name, slug: c.slug, count: c.count };
      });
    }
    return collectCategories(games);
  }

  function renderChips(state) {
    var wrap = document.getElementById('catalogChips');
    if (!wrap) return;
    var html =
      '<button type="button" class="chip' +
      (state.cat ? '' : ' active') +
      '" data-cat="">All</button>';
    state.categories.forEach(function (c) {
      var active =
        state.cat === c.slug || (state.cat && catSlugLoose(c.name) === state.cat);
      html +=
        '<button type="button" class="chip' +
        (active ? ' active' : '') +
        '" data-cat="' +
        esc(c.slug) +
        '">' +
        esc(c.name) +
        ' <span class="count">' +
        c.count +
        '</span></button>';
    });
    wrap.innerHTML = html;
  }

  function init() {
    var games = buildGames();
    var categories = buildChipCategories(games);
    var query = parseQuery();
    var searchInput = document.getElementById('catalogSearchInput');

    var state = {
      games: games,
      categories: categories,
      q: query.q,
      cat: query.cat,
      visible: PAGE_SIZE,
    };

    if (searchInput) searchInput.value = state.q;

    renderChips(state);
    render(state);

    document.getElementById('catalogChips')?.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-cat]');
      if (!btn) return;
      state.cat = btn.getAttribute('data-cat') || '';
      state.visible = PAGE_SIZE;
      pushQuery(state.q, state.cat);
      renderChips(state);
      render(state);
    });

    searchInput?.addEventListener('input', function () {
      state.q = searchInput.value.trim();
      state.visible = PAGE_SIZE;
      pushQuery(state.q, state.cat);
      render(state);
    });

    document.getElementById('catalogLoadMore')?.addEventListener('click', function () {
      state.visible += PAGE_SIZE;
      render(state);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
