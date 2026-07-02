(function () {
  'use strict';

  function pagePrefix() {
    return location.pathname.indexOf('/games/') !== -1 ? '../' : '';
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

  /** WG sidebar label → catalog category names on games */
  var LABEL_TO_CATS = {
    '2 players': ['2Players', '2 Players'],
    'dress-up & fashion': ['Dress-up and Fashion', 'Dress-up & Fashion'],
    'dress-up and fashion': ['Dress-up and Fashion', 'Dress-up & Fashion'],
    'card & board': ['Card & Board', 'Card'],
    'puzzles': ['Puzzles', 'Puzzle'],
    'politics & gov.': ['Politics & Government'],
    'politics & government': ['Politics & Government'],
    'rhythm & music': ['Rhythm (Dance & Music)'],
    'role-playing': ['Role-Playing (RPG)'],
    'role-playing (rpg)': ['Role-Playing (RPG)'],
    'sports mgmt.': ['Sports Management'],
    'motorbike & bike': ['Motorbike & Bike', 'Cars'],
    'science fiction': ['Science Fiction'],
    'beat \'em up': ['Beat \'em Up'],
    'cooking & food': ['Cooking & Food'],
    'pet & animal': ['Pet & Animal'],
    'quiz & trivia': ['Quiz & Trivia'],
    'real-time tactics': ['Real-Time Tactics'],
    'military & war': ['Military & War'],
  };

  var NATIVE_FILTERS = {
    'monkeymart-classics': {
      label: 'MonkeyMart Classics',
      match: function () {
        return true;
      },
      nativeOnly: true,
    },
    fnaf: {
      label: 'FNAF',
      match: function (cats) {
        return (cats || []).indexOf('FNAF') !== -1;
      },
      nativeOnly: true,
    },
    'moto-x3m': {
      label: 'Moto X3M',
      match: function (cats) {
        return (cats || []).indexOf('Moto X3M') !== -1;
      },
      nativeOnly: true,
    },
    vex: {
      label: 'Vex',
      match: function (cats) {
        return (cats || []).indexOf('Vex') !== -1;
      },
      nativeOnly: true,
    },
    'fireboy-and-watergirl': {
      label: 'Fireboy & Watergirl',
      match: function (cats) {
        return (cats || []).indexOf('Fireboy & Watergirl') !== -1;
      },
      nativeOnly: true,
    },
    'snail-bob': {
      label: 'Snail Bob',
      match: function (cats) {
        return (cats || []).indexOf('Snail Bob') !== -1;
      },
      nativeOnly: true,
    },
    racing: {
      label: 'Racing',
      match: function (cats) {
        return (cats || []).indexOf('Racing') !== -1;
      },
      nativeOnly: true,
    },
    puzzle: {
      label: 'Puzzle',
      match: function (cats) {
        return (cats || []).indexOf('Puzzle') !== -1;
      },
      nativeOnly: true,
    },
  };

  var CLASSICS_ICON =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>';

  function catalogNamesForLabel(label) {
    var key = String(label || '').toLowerCase();
    if (LABEL_TO_CATS[key]) return LABEL_TO_CATS[key].slice();
    return [label];
  }

  function catNameMatches(cats, targetName) {
    var slug = catSlug(targetName);
    var loose = catSlugLoose(targetName);
    return (cats || []).some(function (c) {
      return c === targetName || catSlug(c) === slug || catSlugLoose(c) === loose;
    });
  }

  function gameMatchesLabel(gameCats, label) {
    return catalogNamesForLabel(label).some(function (name) {
      return catNameMatches(gameCats, name);
    });
  }

  function collectWgpGames() {
    var catalog = window.WGP_CATALOG || {};
    var games = [];
    Object.keys(catalog).forEach(function (path) {
      var g = catalog[path];
      if (!g || !g.ifr) return;
      games.push({ cats: g.cats || [], source: 'wgp' });
    });
    return games;
  }

  function collectNativeGames() {
    var catalog = window.MM_NATIVE_CATALOG || {};
    var games = [];
    Object.keys(catalog).forEach(function (slug) {
      var g = catalog[slug];
      if (!g) return;
      games.push({ cats: g.cats || ['MonkeyMart Classics'], source: 'native', slug: slug });
    });
    return games;
  }

  function countForLabel(label) {
    var wgp = collectWgpGames();
    var native = collectNativeGames();
    var n = 0;
    wgp.forEach(function (g) {
      if (gameMatchesLabel(g.cats, label)) n++;
    });
    native.forEach(function (g) {
      if (gameMatchesLabel(g.cats, label)) n++;
    });
    return n;
  }

  function countNativeFilter(slug) {
    var def = NATIVE_FILTERS[slug];
    if (!def) return 0;
    var catalog = window.MM_NATIVE_CATALOG || {};
    var n = 0;
    Object.keys(catalog).forEach(function (key) {
      var g = catalog[key];
      if (g && def.match(g.cats || [])) n++;
    });
    return n;
  }

  function formatCount(n) {
    if (n >= 1000) {
      var k = n / 1000;
      return (k >= 10 ? Math.round(k) : Math.round(k * 10) / 10) + 'k';
    }
    return String(n);
  }

  function catalogUrl(slug) {
    return pagePrefix() + 'games-catalogue.html?cat=' + encodeURIComponent(slug);
  }

  function buildList() {
    var p = pagePrefix();
    var list = [];
    var classicsN = countNativeFilter('monkeymart-classics');
    if (classicsN) {
      list.push({
        name: 'MonkeyMart Classics',
        slug: 'monkeymart-classics',
        count: classicsN,
        color: '#16a34a',
        icon: CLASSICS_ICON,
        url: catalogUrl('monkeymart-classics'),
      });
    }

    var design = window.WG_CAT_DESIGN || [];
    design.forEach(function (d) {
      var count = countForLabel(d.name);
      if (!count) return;
      var slug = catSlug(d.name);
      list.push({
        name: d.name,
        slug: slug,
        count: count,
        color: d.color || '#6366f1',
        icon: d.icon || '',
        url: catalogUrl(slug),
      });
    });

    return list;
  }

  function gameMatchesSlug(game, slug) {
    if (!slug) return true;
    slug = slug.toLowerCase();

    var nativeDef = NATIVE_FILTERS[slug];
    if (nativeDef) {
      var src = game.source || game._source;
      if (src !== 'native') return false;
      return nativeDef.match(game.cats || []);
    }

    var design = window.WG_CAT_DESIGN || [];
    for (var i = 0; i < design.length; i++) {
      if (catSlug(design[i].name) === slug || catSlugLoose(design[i].name) === slug) {
        return gameMatchesLabel(game.cats, design[i].name);
      }
    }

    return (game.cats || []).some(function (c) {
      return catSlug(c) === slug || catSlugLoose(c) === slug;
    });
  }

  function labelForSlug(slug) {
    if (!slug) return 'All games';
    var nativeDef = NATIVE_FILTERS[slug];
    if (nativeDef) return nativeDef.label;

    var design = window.WG_CAT_DESIGN || [];
    for (var i = 0; i < design.length; i++) {
      if (catSlug(design[i].name) === slug || catSlugLoose(design[i].name) === slug) {
        return design[i].name;
      }
    }

    return slug.replace(/-/g, ' ').replace(/\b\w/g, function (ch) {
      return ch.toUpperCase();
    });
  }

  /** Shape expected by chrome.min.js wgCategories() */
  function buildWgCategories() {
    return buildList().map(function (c) {
      return {
        name: c.name,
        count: formatCount(c.count),
        id: c.slug,
        url: c.url,
        color: c.color,
        icon: c.icon,
      };
    });
  }

  function wireChromeCategories() {
    var cats = buildList();
    if (!cats.length) return;

    var railTop = document.getElementById('railCatTop');
    var railMore = document.getElementById('railCatMore');
    var TOP_N = 8;

    function railItem(c) {
      var icon = (c.icon || '').replace('<svg ', '<svg width="18" height="18" ');
      return (
        '<a class="rail-item" href="' +
        c.url +
        '"><span class="ico" style="color:' +
        c.color +
        '">' +
        icon +
        '</span><span class="label">' +
        c.name +
        '</span><span class="count">' +
        formatCount(c.count) +
        '</span></a>'
      );
    }

    if (railTop) {
      railTop.innerHTML = cats.slice(0, TOP_N).map(railItem).join('');
      if (railMore) railMore.innerHTML = cats.slice(TOP_N).map(railItem).join('');
    }

    var gridEl = document.getElementById('catGrid');
    if (gridEl) {
      var html = '';
      cats.forEach(function (c) {
        html +=
          '<a class="cat-tile" href="' +
          c.url +
          '" style="--c:' +
          c.color +
          '" title="' +
          c.count +
          ' games">' +
          '<span class="ic">' +
          c.icon +
          '</span><span class="label">' +
          c.name +
          '</span></a>';
      });
      gridEl.innerHTML = html;
      var allLink = document.getElementById('catBrowseAll');
      if (allLink) allLink.textContent = 'All ' + cats.length + ' \u2192';
    }

    var chipWrap = document.getElementById('chipScroll');
    if (chipWrap && !chipWrap.dataset.mmCats) {
      chipWrap.dataset.mmCats = '1';
      var p = pagePrefix();
      var chipHTML =
        '<a class="chip active" href="' + p + 'games-catalogue.html">All</a>';
      cats.slice(0, 20).forEach(function (c) {
        chipHTML += '<a class="chip" href="' + c.url + '">' + c.name + '</a>';
      });
      chipWrap.innerHTML = chipHTML;
    }
  }

  window.MM_CATEGORIES = {
    buildList: buildList,
    catSlug: catSlug,
    catSlugLoose: catSlugLoose,
    gameMatchesSlug: gameMatchesSlug,
    labelForSlug: labelForSlug,
    formatCount: formatCount,
    catalogUrl: catalogUrl,
    wireChromeCategories: wireChromeCategories,
    NATIVE_FILTERS: NATIVE_FILTERS,
  };

  window.MM_buildWgCategories = buildWgCategories;
})();
