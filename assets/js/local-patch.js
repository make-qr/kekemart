(function () {
  'use strict';

  function hashFromImg(url) {
    if (!url) return '';
    var m = url.match(/static\.wgplayground\.com\/([a-f0-9]{32})\//i);
    return m ? m[1] : '';
  }

  function hashFromGame(item) {
    if (!item) return '';
    return hashFromImg(item.img) || hashFromImg(item.bg) || '';
  }

  function slugFromPath(path) {
    return path.replace(/\//g, '-');
  }

  function pagePrefix() {
    return location.pathname.indexOf('/games/') !== -1 ? '../' : '';
  }

  /** Prefix ../ when viewing a page under /games/ so root-relative hrefs resolve correctly. */
  function normalizeRootHref(url) {
    if (!url || url.indexOf('http://') === 0 || url.indexOf('https://') === 0) return url;
    if (url.indexOf('../') === 0 || url.charAt(0) === '/') return url;
    var p = pagePrefix();
    return p ? p + url : url;
  }

  function localCatalogueUrl(href) {
    if (!href || href.indexOf('games-catalogue') === -1) return href;
    var local = href;
    var byPath = href.match(/games-catalogue(?:\.html)?\/games\/([^/?#]+)/i);
    var byPublisher = href.match(/games-catalogue(?:\.html)?\/games-by\/([^/?#]+)/i);
    var byTag = href.match(/games-catalogue(?:\.html)?\/tags\/([^/?#]+)/i);
    if (byPath) {
      local = 'games-catalogue.html?cat=' + encodeURIComponent(byPath[1].toLowerCase());
    } else if (byPublisher) {
      local = 'games-catalogue.html?q=' + encodeURIComponent(byPublisher[1].replace(/-/g, ' '));
    } else if (byTag) {
      local = 'games-catalogue.html?q=' + encodeURIComponent(byTag[1].replace(/-/g, ' '));
    } else if (href.indexOf('wgplayground.com') !== -1) {
      var m = href.match(/games-catalogue\/games\/([^/?#]+)/i);
      local = m
        ? 'games-catalogue.html?cat=' + encodeURIComponent(m[1].toLowerCase())
        : 'games-catalogue.html';
    } else if (href.indexOf('games-catalogue.html') === -1) {
      return href;
    }
    return normalizeRootHref(local);
  }

  function localGameUrl(wgpUrl, hash) {
    var routes = window.WGP_GAME_ROUTES || {};
    var path;
    if (wgpUrl && routes[wgpUrl]) path = routes[wgpUrl];
    else {
      var m = (wgpUrl || '').match(/\/game\/(.+?)\/?$/);
      if (m) path = 'games/' + slugFromPath(m[1]) + '.html';
      else if (hash) path = 'game.html?ifr=' + encodeURIComponent(hash);
      else if (wgpUrl && wgpUrl.indexOf('monkey-mart') !== -1) path = 'monkey-mart.html';
      else path = 'index.html';
    }
    return normalizeRootHref(path);
  }

  function fixOgExtension(url) {
    if (!url || url.indexOf('/og.jpg') === -1) return url;
    return url.replace(/\/og\.jpg$/i, '/og.webp');
  }

  function withPagePrefix(url) {
    if (!url || url.indexOf('http://') === 0 || url.indexOf('https://') === 0) return url;
    if (url.indexOf('../') === 0) return url;
    var p = pagePrefix();
    if (!p) return url;
    if (url.indexOf('assets/') === 0 || url.indexOf('hosted-games/') === 0) return p + url;
    return url;
  }

  function isGamePlayUrl(url) {
    if (!url) return false;
    return /\/(index|frame)\.html(\?|#|$)/i.test(url);
  }

  function cdnRelativePath(url) {
    var base = ((window.MM_BRAND && window.MM_BRAND.gamesCdn) || 'https://games.monkeymart.one').replace(
      /\/$/,
      ''
    );
    if (url.indexOf(base + '/projects/') === 0) {
      return url.slice((base + '/projects/').length);
    }
    if (url.indexOf(base + '/') === 0) {
      return url.slice((base + '/').length);
    }
    return '';
  }

  function gamesCdnToBundledThumb(url) {
    if (window.MM_gamesCdnToBundledThumb) return window.MM_gamesCdnToBundledThumb(url);
    if (!url || isGamePlayUrl(url)) return url;
    var base = ((window.MM_BRAND && window.MM_BRAND.gamesCdn) || 'https://games.monkeymart.one').replace(
      /\/$/,
      ''
    );
    if (url.indexOf(base + '/') === 0) {
      return withPagePrefix('assets/images/mm-native/' + url.slice(base.length + 1));
    }
    if (url.indexOf('hosted-games/') >= 0) {
      return withPagePrefix(url.replace(/hosted-games\//g, 'assets/images/mm-native/'));
    }
    return url;
  }

  function gamesCdnToLocal(url) {
    if (window.MM_gamesCdnToLocal) return window.MM_gamesCdnToLocal(url);
    if (!url) return url;
    if (isGamePlayUrl(url)) {
      var h = location.hostname;
      if (h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0') {
        var rel = cdnRelativePath(url);
        if (rel) return withPagePrefix('hosted-games/' + rel);
        if (url.indexOf('hosted-games/') >= 0) return withPagePrefix(url.replace(/^\.\.\//, ''));
      }
      return url;
    }
    var h = location.hostname;
    if (h !== 'localhost' && h !== '127.0.0.1' && h !== '0.0.0.0') {
      return gamesCdnToBundledThumb(url);
    }
    var base = ((window.MM_BRAND && window.MM_BRAND.gamesCdn) || 'https://games.monkeymart.one').replace(
      /\/$/,
      ''
    );
    if (url.indexOf(base + '/') === 0) {
      var relPath = cdnRelativePath(url);
      return withPagePrefix('hosted-games/' + (relPath || url.slice(base.length + 1)));
    }
    return gamesCdnToBundledThumb(url);
  }

  function styleArtThumb(el) {
    if (!el) return;
    el.style.backgroundSize = 'cover';
    el.style.backgroundPosition = 'center';
    el.style.backgroundRepeat = 'no-repeat';
  }

  function localImg(url) {
    if (!url) return url;
    url = fixOgExtension(url);
    url = gamesCdnToBundledThumb(url);
    url = gamesCdnToLocal(url);
    if (url.indexOf('assets/images/') === 0 || url.indexOf('../assets/images/') === 0) {
      return withPagePrefix(url.replace(/^\.\.\//, ''));
    }
    if (url.indexOf('hosted-games/') === 0 || url.indexOf('../hosted-games/') === 0) {
      return withPagePrefix(url.replace(/^\.\.\//, ''));
    }
    var map = window.WGP_IMAGE_MAP || {};
    var hashM = url.match(/static\.wgplayground\.com\/([a-f0-9]{32})\//i);
    if (hashM && map[hashM[1]]) return withPagePrefix(map[hashM[1]].thumbnail);
    var vendorM = url.match(/assets\/vendor\/wgp\/static\/([a-f0-9]{32})\//i);
    if (vendorM && map[vendorM[1]]) return withPagePrefix(map[vendorM[1]].thumbnail);
    var m = url.match(/static\.wgplayground\.com\/(.+?)(?:\?|$)/i);
    if (m) return withPagePrefix('assets/vendor/wgp/static/' + m[1]);
    var s = url.match(/scout\.wgimager\.com\/[^/]+\/[^/]+\/[^/]+\/(https:\/\/static\.wgplayground\.com\/.+)/i);
    if (s) return localImg(s[1]);
    return withPagePrefix(url);
  }

  function localOg(hash) {
    var map = window.WGP_IMAGE_MAP || {};
    return (map[hash] && map[hash].og) || '';
  }

  function patchItemImages(item) {
    if (!item) return;
    if (item.img) item.img = localImg(item.img);
    if (item.bg) item.bg = localImg(item.bg);
    if (item.preview) item.preview = localImg(item.preview);
  }

  function buildHashMap() {
    var map = {};
    if (!window.WG_DATA) return map;
    function add(item) {
      if (!item || !item.url) return;
      var h = hashFromGame(item);
      if (h) map[item.url] = h;
    }
    (WG_DATA.hero || []).forEach(add);
    var grids = WG_DATA.grids || {};
    Object.keys(grids).forEach(function (k) {
      (grids[k] || []).forEach(add);
    });
    return map;
  }

  function patchWgDataUrls() {
    if (!window.WG_DATA) return;
    var map = buildHashMap();
    window.WGP_IFR_MAP = map;

    function patchItem(item) {
      if (!item || !item.url) return;
      patchItemImages(item);
      var h = map[item.url] || hashFromGame(item);
      item.url = localGameUrl(item.url, h);
    }

    (WG_DATA.hero || []).forEach(patchItem);
    var grids = WG_DATA.grids || {};
    Object.keys(grids).forEach(function (k) {
      (grids[k] || []).forEach(patchItem);
    });
  }

  function rewriteAnchors() {
    if (!document.body) return;
    document.querySelectorAll('a[href*="games-catalogue"]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href || a.dataset.localCatalogue) return;
      var local = localCatalogueUrl(href);
      if (local !== href) {
        a.setAttribute('href', local);
        a.dataset.localCatalogue = '1';
      }
    });
    document.querySelectorAll('a[href*="wgplayground.com/game/"]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href || a.dataset.localGame) return;
      var map = window.WGP_IFR_MAP || {};
      var h = map[href] || hashFromImg(href);
      a.setAttribute('href', localGameUrl(href, h));
      a.dataset.localGame = '1';
    });
    document.querySelectorAll('a[href^="games/"], a[href^="game.html"], a[href="monkey-mart.html"]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href || a.dataset.localGamePrefixed) return;
      var fixed = normalizeRootHref(href);
      if (fixed !== href) {
        a.setAttribute('href', fixed);
        a.dataset.localGamePrefixed = '1';
      }
    });
    document.querySelectorAll('a[href*="games-catalogue.html/"]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href || a.dataset.localCataloguePath) return;
      var fixed = localCatalogueUrl(href);
      if (fixed !== href) {
        a.setAttribute('href', fixed);
        a.dataset.localCataloguePath = '1';
      }
    });
    document.querySelectorAll('img[src*="static.wgplayground.com"], img[src*="scout.wgimager.com"], img[src*="assets/vendor/wgp/static/"], img[src*="/og.jpg"]').forEach(function (img) {
      var src = localImg(img.getAttribute('src'));
      img.setAttribute('src', src);
      if (!img.getAttribute('alt')) {
        var map = window.WGP_IMAGE_MAP || {};
        Object.keys(map).forEach(function (h) {
          if (map[h].thumbnail === src || map[h].og === src) {
            img.setAttribute('alt', map[h].alt || map[h].name || '');
          }
        });
      }
    });
    document
      .querySelectorAll(
        '.art[style*="background-image"], .side-card-art[style*="background-image"], [style*="background-image:url"]'
      )
      .forEach(function (el) {
        var style = el.getAttribute('style') || '';
        var m = style.match(/background-image:\s*url\(['"]?([^'")]+)['"]?\)/i);
        if (!m) return;
        var fixed = localImg(m[1]);
        if (fixed !== m[1]) {
          el.setAttribute('style', style.replace(m[1], fixed));
        }
        styleArtThumb(el);
      });
  }

  function patchRelatedGamesImages() {
    function fixItem(item) {
      if (!item || !item.image) return;
      item.image = localImg(item.image);
    }
    (window.WG_RELATED_GAMES || []).forEach(fixItem);
    (window.WG_PUBLISHER_GAMES || []).forEach(fixItem);
  }

  function absPageUrl(url) {
    if (!url) return '';
    if (url.indexOf('http://') === 0 || url.indexOf('https://') === 0) return url;
    try {
      return new URL(url, location.href).href;
    } catch (e) {
      return url;
    }
  }

  // WG game.min.css applies --hero-grad on ::before; url() inside that variable
  // resolves against the stylesheet path, so hosted-games/... becomes a 404.
  function fixRailHeroThumb() {
    var art = document.querySelector('#railHero .hero-art, .rail-hero-wrap .hero-art');
    if (!art) return;

    var url = '';
    var grad = art.style.getPropertyValue('--hero-grad') || '';
    var m = grad.match(/url\(['"]?([^'")]+)['"]?\)/i);
    if (m && m[1]) url = absPageUrl(localImg(m[1]));

    if (!url) {
      var pool = window.WG_RELATED_GAMES || window.WG_PUBLISHER_GAMES || [];
      for (var i = 0; i < pool.length; i++) {
        if (pool[i] && pool[i].image) {
          url = absPageUrl(pool[i].image);
          break;
        }
      }
    }
    if (!url) return;

    art.classList.add('mm-has-thumb');
    art.style.setProperty(
      'background-image',
      "url('" + String(url).replace(/'/g, "\\'") + "')"
    );
    art.style.setProperty('background-size', 'cover');
    art.style.setProperty('background-position', 'center');
    art.style.setProperty('--hero-grad', 'none');
  }

  function gamesCdnBase() {
    return ((window.MM_BRAND && window.MM_BRAND.gamesCdn) || 'https://games.monkeymart.one').replace(
      /\/$/,
      ''
    );
  }

  /** Turn data-mm-play / relative paths into absolute games CDN play URLs. */
  function resolvePlayUrl(url) {
    if (!url || url === 'about:blank') return '';
    url = String(url).trim();
    var base = gamesCdnBase();
    if (/^https?:\/\//i.test(url)) {
      if (url.indexOf(base + '/') === 0) {
        var tail = url.slice(base.length + 1);
        if (tail.indexOf('projects/') !== 0 && /^[a-zA-Z0-9._-]+\//.test(tail)) {
          return base + '/projects/' + tail;
        }
      }
      return url;
    }
    var hosted = url.match(/(?:^|\/)hosted-games\/(.+)$/);
    if (hosted) return base + '/projects/' + hosted[1];
    var rel = url.match(/(?:\.\.\/)*(?:projects\/)?([^/?#]+)\/((?:index|frame|poker)\.html?.*)$/i);
    if (rel) return base + '/projects/' + rel[1] + '/' + rel[2];
    return url;
  }

  function fixNativeGameIframe() {
    var iframe = document.getElementById('playerIframe');
    if (!iframe || iframe.dataset.mmPlayReady) return;
    var src =
      iframe.getAttribute('data-mm-play') ||
      iframe.getAttribute('src') ||
      '';
    if (!src || src === 'about:blank') return;
    var playUrl;
    if (/hosted-games\//i.test(src) || /^play\//i.test(src)) {
      playUrl = gamesCdnToLocal(src) || withPagePrefix(src.replace(/^\.\.\//, ''));
    } else {
      var resolved = resolvePlayUrl(src) || src;
      playUrl = gamesCdnToLocal(resolved) || resolved;
    }
    iframe.dataset.mmPlayReady = '1';
    iframe.setAttribute('src', playUrl);
  }

  patchWgDataUrls();
  patchRelatedGamesImages();

  // Native game iframe: set src after CDN→local rewrite (avoids broken CDN fetch on localhost).
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixNativeGameIframe, { once: true });
  } else {
    fixNativeGameIframe();
  }

  function onReady() {
    patchRelatedGamesImages();
    fixNativeGameIframe();
    rewriteAnchors();
    document.addEventListener('wgp:taste:change', function () {
      setTimeout(fixRailHeroThumb, 0);
    });
    document.dispatchEvent(new CustomEvent('wgp:taste:change'));
    fixRailHeroThumb();
    setTimeout(fixRailHeroThumb, 0);
    setTimeout(fixRailHeroThumb, 120);
    new MutationObserver(rewriteAnchors).observe(document.body, { childList: true, subtree: true });

    document.body.addEventListener('click', function (e) {
      var a = e.target.closest('a[href*="wgplayground.com/game/"]');
      if (!a) return;
      e.preventDefault();
      var href = a.getAttribute('href');
      var map = window.WGP_IFR_MAP || {};
      window.location.href = localGameUrl(href, map[href] || '');
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }

  window.MM_normalizeGameHref = normalizeRootHref;
})();
