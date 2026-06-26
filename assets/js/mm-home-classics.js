(function () {
  'use strict';

  var prefix = location.pathname.indexOf('/games/') !== -1 ? '../' : '';
  var HOME_CLASSICS_LIMIT = 24;
  var PRIORITY_SLUGS = [
    'slope',
    'cookie-clicker',
    'fnaf-1',
    'moto-x3m',
    'subway-surfers',
    'retro-bowl',
    '1v1.lol',
    'tunnel-rush',
    'drift-boss',
    'baldis-basics',
    'bitlife',
    'minecraft',
    'mario',
    'among-us',
    'drift-hunters',
    'vex-3',
    'fireboy-and-watergirl-1',
    'snail-bob',
    'totm',
    'papery-planes',
    '2048',
    'pacman',
    'flappy-bird',
    'hextris',
  ];

  function esc(s) {
    var d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }

  function priorityIndex(slug) {
    var i = PRIORITY_SLUGS.indexOf(slug);
    return i === -1 ? 999 : i;
  }

  function ensureSection() {
    var section = document.getElementById('mmClassicsSection');
    if (section) return section;

    var chips = document.getElementById('chipScroll');
    if (!chips) return null;

    section = document.createElement('section');
    section.id = 'mmClassicsSection';
    section.className = 'mm-home-classics';
    section.setAttribute('aria-label', 'MonkeyMart classics');
    section.innerHTML =
      '<div class="section-head">' +
      '<h2><span class="dot" style="background:#16a34a"></span>MonkeyMart classics</h2>' +
      '<a class="more" href="' + prefix + 'games-catalogue.html?cat=monkeymart-classics">See all →</a>' +
      '</div>' +
      '<div class="grid grid-dense mm-classics-grid" id="mmClassicsGrid"></div>';

    var anchor =
      document.querySelector('.mm-home-seo') ||
      document.querySelector('footer') ||
      document.getElementById('moreSections');
    if (anchor) {
      anchor.parentNode.insertBefore(section, anchor);
    } else {
      var chips = document.getElementById('chipScroll');
      if (chips) chips.parentNode.insertBefore(section, chips.nextSibling);
    }
    return section;
  }

  function renderClassics() {
    var cat = window.MM_NATIVE_CATALOG || {};
    var slugs = Object.keys(cat);
    if (!slugs.length) return;

    var items = slugs
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
      .slice(0, HOME_CLASSICS_LIMIT);

    var section = ensureSection();
    if (!section) return;

    var grid = section.querySelector('#mmClassicsGrid');
    if (!grid) return;

    grid.innerHTML = items
      .map(function (item) {
        var g = item.g;
        var raw = g.img || '';
        var img = (window.MM_resolveImg && window.MM_resolveImg(raw)) || raw;
        var art = img ? " style=\"background-image:url('" + img.replace(/'/g, '%27') + "')\"" : '';
        return (
          '<a class="card" href="' + prefix + 'games/mm-' + esc(item.slug) + '.html" style="--c:' + (g.c || '#16a34a') + '">' +
          '<div class="art"' + art + '></div>' +
          '<div class="title-default"><h3>' + esc(g.name) + '</h3></div>' +
          '<div class="veil"></div>' +
          '<div class="body"><h3>' + esc(g.name) + '</h3><span class="by">MonkeyMart.one</span></div>' +
          '</a>'
        );
      })
      .join('');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderClassics, { once: true });
  } else {
    renderClassics();
  }
})();
