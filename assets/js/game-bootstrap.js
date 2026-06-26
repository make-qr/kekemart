(function () {
  'use strict';

  function parseParams() {
    var p = new URLSearchParams(location.search);
    var wgpUrl = p.get('url') || '';
    var ifr = p.get('ifr') || '';
    var path = '';
    if (wgpUrl) {
      var m = wgpUrl.match(/\/game\/(.+)$/);
      path = m ? m[1].replace(/\/$/, '') : '';
    }
    if (!path && p.get('path')) path = p.get('path').replace(/^\//, '');
    return { wgpUrl: wgpUrl, ifr: ifr, path: path };
  }

  function hashFromImg(url) {
    if (!url) return '';
    var m = url.match(/static\.wgplayground\.com\/([a-f0-9]{32})\//i);
    return m ? m[1] : '';
  }

  function slugFromPath(path) {
    return path.replace(/\//g, '-');
  }

  function localGameUrl(wgpUrl, hash) {
    var routes = window.WGP_GAME_ROUTES || {};
    if (wgpUrl && routes[wgpUrl]) return routes[wgpUrl];
    var m = (wgpUrl || '').match(/\/game\/(.+?)\/?$/);
    if (m) return 'games/' + slugFromPath(m[1]) + '.html';
    if (hash) return 'game.html?ifr=' + encodeURIComponent(hash);
    return 'index.html';
  }

  function slugTitle(slug) {
    return slug.replace(/-/g, ' ').replace(/\b\w/g, function (c) {
      return c.toUpperCase();
    });
  }

  function setText(id, text) {
    var el = document.getElementById(id);
    if (el && text != null) el.textContent = text;
  }

  function setHtml(id, html) {
    var el = document.getElementById(id);
    if (el && html != null) el.innerHTML = html;
  }

  function fakeCount(seed) {
    var n = 0;
    for (var i = 0; i < seed.length; i++) n += seed.charCodeAt(i);
    return 40 + (n % 420);
  }

  function fakeRating(seed) {
    var n = 0;
    for (var i = 0; i < seed.length; i++) n += seed.charCodeAt(i);
    return (3.8 + (n % 12) / 10).toFixed(1);
  }

  function localImg(url) {
    if (!url) return url;
    if (url.indexOf('assets/images/') === 0) return url;
    var map = window.WGP_IMAGE_MAP || {};
    var hashM = url.match(/static\.wgplayground\.com\/([a-f0-9]{32})\//i);
    if (hashM && map[hashM[1]]) return map[hashM[1]].thumbnail;
    var m = url.match(/static\.wgplayground\.com\/(.+?)(?:\?|$)/i);
    if (m) return 'assets/vendor/wgp/static/' + m[1];
    return url;
  }

  function buildEmbedCodes(game, ifr) {
    var iframeSrc = 'https://play.wgplayground.com/ifr/' + ifr;
    var pageUrl = location.origin + location.pathname.replace(/[^/]+$/, '') + 'game.html?ifr=' + ifr;
    return {
      iframe:
        '<iframe src="' +
        iframeSrc +
        '"\n        width="100%" height="600" frameborder="0"\n        allow="fullscreen; autoplay"\n        loading="lazy"></iframe>',
      widget:
        '<div id="wgp-widget"></div>\n<script\n  src="https://www.wgplayground.com/public/widget.js"\n  data-container="#wgp-widget"\n  data-games="' +
        ifr +
        '"\n  data-layout="grid-1x1"\n  data-caption="title-by"\n  async><\/script>',
      link: '[Play ' + game.name + ' on WGPlayground](' + pageUrl + ')',
    };
  }

  function renderMoreGames(pub, currentPath) {
    var paths = (window.WGP_BY_PUBLISHER || {})[pub] || [];
    var grid = document.getElementById('morePublisherGrid');
    var section = document.getElementById('moreFromPublisher');
    if (!grid || !section) return;
    var items = paths
      .filter(function (p) {
        return p !== currentPath;
      })
      .slice(0, 8)
      .map(function (p) {
        return (window.WGP_CATALOG || {})[p];
      })
      .filter(Boolean);
    if (!items.length) return;
    section.hidden = false;
    setText('morePublisherName', pub);
    grid.innerHTML = items
      .map(function (g) {
        var path = g.url.split('/game/')[1];
        var href = localGameUrl(g.url, g.ifr);
        var img = localImg(g.img || '');
        return (
          '<a class="card" href="' +
          href +
          '">' +
          '<div class="thumb"><img src="' +
          img +
          '" alt="' +
          (g.img_alt || g.name).replace(/"/g, '&quot;') +
          '" loading="lazy" width="360" height="270"></div>' +
          '<div class="card-body"><strong>' +
          g.name +
          '</strong><span>by ' +
          g.by +
          '</span></div></a>'
        );
      })
      .join('');
  }

  function startPlayer(ifr) {
    var iframe = document.getElementById('playerIframe');
    var launcher = document.getElementById('playerLauncher');
    var cover = document.getElementById('playerCover');
    if (!iframe || !ifr) return;
    iframe.src = 'https://play.wgplayground.com/ifr/' + ifr;
    if (launcher) launcher.style.display = 'none';
    if (cover) cover.style.display = 'none';
    iframe.style.display = 'block';
    document.getElementById('playerFrame').classList.add('is-playing');
  }

  function init() {
    var params = parseParams();
    var catalog = window.WGP_CATALOG || {};
    var game = params.path ? catalog[params.path] : null;

    if (!game && params.wgpUrl) {
      var m = params.wgpUrl.match(/\/game\/(.+)$/);
      if (m) game = catalog[m[1].replace(/\/$/, '')];
    }

    var ifr = params.ifr || (game && game.ifr) || '';
    var wgpUrl =
      params.wgpUrl || (game && game.url) || 'https://www.wgplayground.com/game/' + (params.path || '');
    var name = (game && game.name) || slugTitle((params.path || 'game').split('/').pop());
    var pub = (game && game.by) || 'Unknown';
    var img = localImg((game && game.img) || '');
    var cats = (game && game.cats) || [];
    var about =
      (game && game.copy) ||
      'Play ' +
        name +
        ' free in your browser on WGPlayground. No download or install required — click play and start instantly.';
    var rating = fakeRating(name + pub);
    var live = fakeCount(ifr || name);

    window.WG_GAME = {
      url: wgpUrl,
      name: name,
      by: pub,
      image: img,
      ifr: ifr,
    };

    document.title = name + ' — WGPlayground';
    setText('gameTitle', name);
    setText('gameBreadcrumbName', name);
    setText('gamePublisher', pub);
    setText('brandName', pub);
    setText('gameAbout', about);
    setText('livePlayersCount', String(live));
    setText('gameRatingValue', rating);
    setText('gameRatingCount', '· ' + Math.round(live * 8.5) + ' ratings');
    setText('reviewsScore', rating);
    setText('reviewsTotal', Math.round(live * 8.5).toLocaleString() + ' ratings');

    if (cats.length) {
      setText('gameBreadcrumbCat', cats[0]);
      var chips = document.getElementById('gameTagChips');
      if (chips) {
        chips.innerHTML = cats
          .map(function (c) {
            return '<a class="tag-chip" href="index.html">' + c + '</a>';
          })
          .join('');
      }
    }

    var cover = document.getElementById('playerCover');
    if (cover && img) {
      cover.style.backgroundImage = 'url("' + img + '")';
      cover.style.backgroundSize = 'cover';
      cover.style.backgroundPosition = 'center';
    }

    var iframe = document.getElementById('playerIframe');
    if (iframe) iframe.title = name;

    var specList = document.getElementById('specList');
    if (specList) {
      var specs = [
        ['Developer', pub],
        ['Category', cats.join(', ') || 'Casual'],
        ['Technology', 'HTML5'],
        ['Platform', 'Browser'],
        ['Mobile', 'Yes'],
      ];
      specList.innerHTML = specs
        .map(function (row) {
          return '<div class="spec-row"><dt>' + row[0] + '</dt><dd>' + row[1] + '</dd></div>';
        })
        .join('');
    }

    if (ifr) {
      var codes = buildEmbedCodes({ name: name, url: wgpUrl }, ifr);
      ['iframe', 'widget', 'link'].forEach(function (key) {
        var pre = document.querySelector('pre[data-embed-code="' + key + '"]');
        if (pre) pre.textContent = codes[key];
      });
      document.getElementById('reportHash').value = ifr;

      var playBtn = document.getElementById('playerPlayBtn');
      if (playBtn) {
        playBtn.addEventListener('click', function () {
          startPlayer(ifr);
        });
      }
      // Auto-start player like WGPlayground game page
      startPlayer(ifr);
    }

    renderMoreGames(pub, params.path);

    var shareBtn = document.getElementById('shareBtn');
    if (shareBtn) {
      shareBtn.addEventListener('click', function () {
        var url = location.href;
        if (navigator.share) {
          navigator.share({ title: name, url: url }).catch(function () {});
        } else if (navigator.clipboard) {
          navigator.clipboard.writeText(url);
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
