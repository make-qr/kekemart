(function () {
  'use strict';

  function pagePrefix() {
    return location.pathname.indexOf('/games/') !== -1 ? '../' : '';
  }

  function gamesCdnBase() {
    var b = (window.MM_BRAND && window.MM_BRAND.gamesCdn) || 'https://games.monkeymart.one';
    return b.replace(/\/$/, '');
  }

  function useLocalHostedGames() {
    var h = location.hostname;
    return h === 'localhost' || h === '127.0.0.1' || h === '0.0.0.0';
  }

  function gamesCdnToBundledThumb(url) {
    if (!url) return url;
    var base = gamesCdnBase();
    if (url.indexOf(base + '/') === 0) {
      return pagePrefix() + 'assets/images/mm-native/' + url.slice(base.length + 1);
    }
    if (url.indexOf('hosted-games/') >= 0) {
      return pagePrefix() + url.replace(/hosted-games\//g, 'assets/images/mm-native/');
    }
    return url;
  }

  function gamesCdnToLocal(url) {
    if (!url || !useLocalHostedGames()) return gamesCdnToBundledThumb(url);
    var base = gamesCdnBase();
    if (url.indexOf(base + '/') === 0) {
      return pagePrefix() + 'hosted-games/' + url.slice(base.length + 1);
    }
    return gamesCdnToBundledThumb(url);
  }

  function resolveImg(url) {
    if (!url) return '';
    url = gamesCdnToBundledThumb(url);
    url = gamesCdnToLocal(url);
    if (url.indexOf('http://') === 0 || url.indexOf('https://') === 0) return url;
    var p = pagePrefix();
    if (url.indexOf('../') === 0) return url;
    if (p && (url.indexOf('assets/') === 0 || url.indexOf('hosted-games/') === 0)) {
      return p + url;
    }
    return url;
  }

  window.MM_resolveImg = resolveImg;
  window.MM_gamesCdnToLocal = gamesCdnToLocal;
  window.MM_gamesCdnToBundledThumb = gamesCdnToBundledThumb;
})();
