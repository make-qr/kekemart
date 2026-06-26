(function () {
  'use strict';

  var CFG = window.MM_BRAND || {};
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

  function countNative(filter) {
    var cat = window.MM_NATIVE_CATALOG || {};
    var n = 0;
    Object.keys(cat).forEach(function (slug) {
      var g = cat[slug];
      if (!g) return;
      if (!filter || filter(g.cats || [])) n++;
    });
    return n;
  }

  function injectRailSection() {
    var rail = document.getElementById('rail');
    if (!rail || document.getElementById('mmRailClassics')) return false;

    var nativeTotal = countNative();
    if (!nativeTotal) return false;

    var section = document.createElement('div');
    section.className = 'rail-section rail-section--mm';
    section.innerHTML =
      '<h4>MonkeyMart classics</h4>' +
      '<a class="rail-item" id="mmRailClassics" href="' + prefix + 'games-catalogue.html?cat=monkeymart-classics">' +
      '<span class="ico" style="color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg></span>' +
      '<span class="label">All classics</span><span class="count">' + nativeTotal + '</span></a>';

    NATIVE_CATS.slice(1).forEach(function (c) {
      var n = countNative(c.match);
      if (n < 2) return;
      section.innerHTML +=
        '<a class="rail-item rail-item--mm-cat" href="' + prefix + 'games-catalogue.html?cat=' + encodeURIComponent(c.slug) + '">' +
        '<span class="ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg></span>' +
        '<span class="label">' + c.label + '</span><span class="count">' + n + '</span></a>';
    });

    var discover = rail.querySelector('.rail-section:not(.rail-section--business):not(.rail-section--you):not(.rail-section--mm)');
    var you = rail.querySelector('.rail-section--you');
    if (you) {
      rail.insertBefore(section, you);
    } else if (discover) {
      discover.parentNode.insertBefore(section, discover.nextSibling);
    } else {
      rail.appendChild(section);
    }
    return true;
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
    s.onload = function () {
      done();
    };
    s.onerror = function () {
      done();
    };
    document.head.appendChild(s);
  }

  function ensureClassicsRail() {
    if (injectRailSection()) return;
    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      if (injectRailSection() || tries >= 30) clearInterval(timer);
    }, 150);
  }

  function run() {
    loadNativeCatalog(function () {
      ensureClassicsRail();
      wireCategories();
      patchCatalogChips();
      if (window.MM_RAIL_SYNC && window.MM_RAIL_SYNC.sync) {
        window.MM_RAIL_SYNC.sync();
      }
      setTimeout(function () {
        ensureClassicsRail();
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
