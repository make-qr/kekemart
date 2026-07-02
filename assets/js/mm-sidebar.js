(function () {
  'use strict';

  var prefix = location.pathname.indexOf('/games/') !== -1 ? '../' : '';

  var NATIVE_CATS = [
    { slug: 'monkeymart-classics', label: 'All classics', match: function () { return true; } },
    { slug: 'fnaf', label: 'FNAF', match: function (cats) { return (cats || []).indexOf('FNAF') !== -1; } },
    { slug: 'moto-x3m', label: 'Moto X3M', match: function (cats) { return (cats || []).indexOf('Moto X3M') !== -1; } },
    { slug: 'vex', label: 'Vex', match: function (cats) { return (cats || []).indexOf('Vex') !== -1; } },
    { slug: 'fireboy-and-watergirl', label: 'Fireboy & Watergirl', match: function (cats) {
      return (cats || []).indexOf('Fireboy & Watergirl') !== -1;
    }},
    { slug: 'snail-bob', label: 'Snail Bob', match: function (cats) { return (cats || []).indexOf('Snail Bob') !== -1; } },
    { slug: 'racing', label: 'Racing', match: function (cats) { return (cats || []).indexOf('Racing') !== -1; } },
    { slug: 'puzzle', label: 'Puzzle', match: function (cats) { return (cats || []).indexOf('Puzzle') !== -1; } },
  ];

  var DISCOVER_HIDE_IDS = [
    'challengeRailBtn',
    'trendingRailBtn',
    'playedRailBtn',
    'hotnotRailBtn',
    'myPicksRailBtn',
  ];

  function discoverSection() {
    var rail = document.getElementById('rail');
    if (!rail) return null;
    var sections = rail.querySelectorAll('.rail-section');
    for (var i = 0; i < sections.length; i++) {
      var h = sections[i].querySelector('h4');
      if (h && /discover/i.test(h.textContent || '')) return sections[i];
    }
    return rail.querySelector('.rail-section:not(.rail-section--business):not(.rail-section--you):not(.rail-section--mm)');
  }

  function removeClassicsRail() {
    document.querySelectorAll('.rail-section--mm').forEach(function (el) {
      el.remove();
    });
  }

  function trimDiscoverRail() {
    var rail = document.getElementById('rail');
    if (!rail) return;

    removeClassicsRail();

    var biz = rail.querySelector('.rail-section--business');
    if (biz) biz.hidden = true;

    DISCOVER_HIDE_IDS.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.hidden = true;
    });

    ensureMonkeyMartLink();
  }

  function ensureMonkeyMartLink() {
    if (document.getElementById('mmRailMonkeyMart')) return;
    var discover = discoverSection();
    if (!discover) return;

    var home =
      discover.querySelector('a.rail-item[href*="index"]') ||
      discover.querySelector('a.rail-item');
    if (!home) return;

    var mm = document.createElement('a');
    mm.className = 'rail-item rail-item--monkeymart';
    mm.id = 'mmRailMonkeyMart';
    mm.href = prefix + 'monkey-mart.html';
    mm.setAttribute('aria-label', 'Play Monkey Mart');
    mm.innerHTML =
      '<span class="ico" style="color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z"/><path d="M3 9l2-5h14l2 5"/><path d="M9 21v-6h6v6"/></svg></span>' +
      '<span class="label">Monkey Mart</span>';

    home.insertAdjacentElement('afterend', mm);
  }

  function patchCatalogChips() {
    if (!document.getElementById('catalogChips')) return;
    var params = new URLSearchParams(location.search);
    var cat = (params.get('cat') || '').toLowerCase();
    NATIVE_CATS.forEach(function (c) {
      if (cat === c.slug && document.title.indexOf(c.label) === -1) {
        document.title = c.label + ' — MonkeyMart.one';
      }
    });
  }

  function wireCategories() {
    if (window.MM_CATEGORIES && window.MM_CATEGORIES.wireChromeCategories) {
      window.MM_CATEGORIES.wireChromeCategories();
    }
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
    s.src = prefix + 'assets/js/mm-native-catalog.js';
    s.onload = done;
    s.onerror = done;
    document.head.appendChild(s);
  }

  function run() {
    trimDiscoverRail();
    loadNativeCatalog(function () {
      trimDiscoverRail();
      wireCategories();
      patchCatalogChips();
      if (window.MM_RAIL_SYNC && window.MM_RAIL_SYNC.sync) {
        window.MM_RAIL_SYNC.sync();
      }
      setTimeout(function () {
        trimDiscoverRail();
        wireCategories();
        if (window.MM_RAIL_SYNC && window.MM_RAIL_SYNC.syncCounts) {
          window.MM_RAIL_SYNC.syncCounts();
        }
      }, 120);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run, { once: true });
  } else {
    run();
  }
})();
