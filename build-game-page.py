#!/usr/bin/env python3
"""Generate wg-catalog.js and game.html from index.html WG_DATA."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
CATALOG_JS = ROOT / "assets/js/wg-catalog.js"
GAME_HTML = ROOT / "game.html"

GAME_MAIN = r"""
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="index.html">Games</a>
      <span aria-hidden="true">›</span>
      <a href="index.html" id="gameBreadcrumbCat">Category</a>
      <span aria-hidden="true">›</span>
      <span aria-current="page" id="gameBreadcrumbName">Game</span>
    </nav>

    <header class="game-header">
      <div class="game-head">
        <div class="live-players" id="livePlayers">
          <span class="live-players-dot" aria-hidden="true"></span>
          <span class="live-players-count" id="livePlayersCount">128</span>
          <span class="live-players-label">playing now</span>
        </div>
      </div>
    </header>

    <section class="game-player" aria-label="Game player">
      <div class="player-frame" id="playerFrame">
        <div class="player-cover" id="playerCover">
          <div class="player-vignette" aria-hidden="true"></div>
          <div class="player-launcher" id="playerLauncher">
            <div class="player-launcher-content">
              <div class="player-launcher-meta">
                <span class="player-tag" id="playerTag"></span>
              </div>
              <button type="button" class="player-play" id="playerPlayBtn" aria-label="Play game">
                <span class="player-play-ic" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28"><path d="M8 5v14l11-7z"/></svg>
                </span>
              </button>
            </div>
          </div>
        </div>
        <iframe id="playerIframe" title="Game" allow="fullscreen; autoplay" loading="lazy" style="width:100%;height:100%;border:0;display:block"></iframe>
        <div class="player-controls">
          <button type="button" class="player-sec-btn" id="fullscreenTopBtn" aria-label="Fullscreen" title="Fullscreen (F)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>
            <span>Fullscreen</span>
          </button>
        </div>
      </div>
      <div class="player-sec-row">
        <button type="button" class="player-sec-btn" data-scroll-target="aboutSection">About</button>
        <button type="button" class="player-sec-btn" data-scroll-target="specSection">Specs</button>
        <button type="button" class="player-sec-btn" data-scroll-target="reviewsSection">Reviews</button>
      </div>
    </section>

    <div class="game-title-row">
      <div>
        <h1 class="game-title-text" id="gameTitle">Game</h1>
        <p class="game-byline" id="gameByline">by <strong id="gamePublisher">Publisher</strong></p>
      </div>
      <div class="game-actions">
        <button type="button" class="game-action game-action--embed" id="embedBtn">
          <span class="game-action-ic" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M16 8V5a2 2 0 0 0-2-2h-5a2 2 0 0 0-2 2v3M8 21v-3a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v3M3 12h18"/></svg>
          </span>
          <span class="game-action-label">Embed</span>
        </button>
        <button type="button" class="game-action" id="shareBtn">
          <span class="game-action-ic" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13"/></svg>
          </span>
          <span class="game-action-label">Share</span>
        </button>
        <button type="button" class="game-action" id="favBtn" aria-pressed="false">
          <span class="game-action-ic" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
          </span>
          <span class="game-action-label">Save</span>
        </button>
        <button type="button" class="game-action game-action--icon-only" id="moreBtn" aria-haspopup="menu" aria-expanded="false" aria-label="More options">
          <span class="game-action-ic" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>
          </span>
        </button>
        <div class="more-menu" id="moreMenu" role="menu" hidden aria-hidden="true">
          <button type="button" class="more-menu-item" id="moreMenuReport" role="menuitem">Report a problem</button>
          <button type="button" class="more-menu-item" id="moreMenuAds" role="menuitem">Ad settings</button>
        </div>
      </div>
    </div>

    <div class="info-strip">
      <div class="info-strip-left">
        <div class="tag-chips" id="gameTagChips"></div>
        <div class="rating-block" id="gameRating">
          <span aria-hidden="true">★</span>
          <strong id="gameRatingValue">4.5</strong>
          <span id="gameRatingCount">· 1,200 ratings</span>
        </div>
      </div>
      <div class="info-strip-right">
        <button type="button" class="publisher-chip" id="brandChip" aria-haspopup="dialog" aria-expanded="false">
          <span class="pub-avatar" id="brandAvatar" aria-hidden="true"></span>
          <span>by <strong id="brandName">Publisher</strong></span>
        </button>
        <div class="brand-popover" id="brandPopover" hidden>
          <p id="brandPopoverText">More games from this publisher on WGPlayground.</p>
        </div>
      </div>
    </div>

    <div class="why-panel" id="whyPanel">
      <div class="why-panel-header">
        <span class="why-panel-icon" aria-hidden="true">✨</span>
        <strong class="game-lead" id="whyLead">Why players love this game</strong>
      </div>
      <ul class="why-bullets" id="whyBullets">
        <li class="why-bullet why-bullet--quick"><span class="why-bullet-emoji">⚡</span><span class="why-bullet-text">Instant play — no download</span></li>
        <li class="why-bullet why-bullet--rated"><span class="why-bullet-emoji">★</span><span class="why-bullet-text">Highly rated on WGPlayground</span></li>
      </ul>
    </div>

    <div class="game-content">
      <div class="game-content-main">
        <section class="game-section" id="aboutSection">
          <h2>About this game</h2>
          <p id="gameAbout">Loading…</p>
        </section>
        <section class="game-section" id="howToSection">
          <h2>How to play</h2>
          <div class="game-instructions" id="gameInstructions">
            <p>Use your mouse or touch to play. Press <kbd>F</kbd> for fullscreen and <kbd>R</kbd> to restart.</p>
          </div>
        </section>
        <section class="spec-card" id="specSection">
          <h3>Specifications</h3>
          <dl class="spec-list" id="specList"></dl>
        </section>
        <section class="game-section" id="reviewsSection">
          <div class="reviews-head">
            <div>
              <h2>Ratings &amp; reviews</h2>
              <div class="reviews-summary">
                <div class="reviews-score" id="reviewsScore">4.5</div>
                <div>
                  <div class="reviews-total" id="reviewsTotal">1,200 ratings</div>
                  <button type="button" class="write-review-btn" id="writeReviewBtn">Write a review</button>
                </div>
              </div>
            </div>
          </div>
          <div class="reviews-list" id="reviewsList"></div>
        </section>
      </div>
      <aside class="game-content-side">
        <div class="embed-card" id="embedPlanSelf">
          <span class="embed-badge">FOR PUBLISHERS</span>
          <h3>Embed this game</h3>
          <p>Add this game to your site with a simple iframe or widget.</p>
          <div class="embed-perks">
            <div class="embed-perk"><span>✓</span> Free to embed</div>
            <div class="embed-perk"><span>✓</span> Responsive player</div>
            <div class="embed-perk"><span>✓</span> Revenue share available</div>
          </div>
          <button type="button" class="embed-cta" id="embedPlanSelfBtn">
            Get embed code <span class="embed-cta-arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </aside>
    </div>

    <section class="more-from-publisher" id="moreFromPublisher" hidden>
      <div class="section-head">
        <h2>More from <span id="morePublisherName">Publisher</span></h2>
      </div>
      <div class="grid" id="morePublisherGrid"></div>
    </section>

    <section class="pub-strip" id="pubStrip" hidden>
      <div class="pub-strip-head">
        <h2>From <span id="pubStripName">Publisher</span></h2>
        <a class="pub-strip-more" id="pubStripMore" href="#">See all →</a>
      </div>
      <div class="pub-strip-track" id="pubStripTrack"></div>
    </section>
"""

EMBED_MODAL = r"""
<div class="embed-modal" id="embedModal" role="dialog" aria-modal="true" aria-labelledby="embedModalTitle" hidden aria-hidden="true">
  <div class="embed-frame" role="document">
    <div class="embed-modal-header">
      <div>
        <div class="embed-modal-title" id="embedModalTitle">Embed game</div>
        <div class="embed-modal-sub" id="embedModalSub">Copy and paste on your site</div>
      </div>
      <button type="button" class="embed-modal-close" data-embed-close aria-label="Close">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" width="18" height="18"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="embed-modal-body">
      <div class="embed-snippet">
        <div class="embed-snippet-bar">
          <div class="embed-tabs" role="tablist">
            <button type="button" class="embed-tab is-active" data-embed-tab="iframe" role="tab" aria-selected="true">iframe</button>
            <button type="button" class="embed-tab" data-embed-tab="widget" role="tab" aria-selected="false">Widget</button>
            <button type="button" class="embed-tab" data-embed-tab="link" role="tab" aria-selected="false">Link</button>
          </div>
        </div>
        <div class="embed-snippet-box is-active" data-embed-panel="iframe">
          <button type="button" class="embed-copy" data-embed-copy="iframe" aria-label="Copy iframe code"><span>Copy</span></button>
          <pre class="embed-snippet-code" data-embed-code="iframe"></pre>
        </div>
        <div class="embed-snippet-box" data-embed-panel="widget">
          <button type="button" class="embed-copy" data-embed-copy="widget" aria-label="Copy widget code"><span>Copy</span></button>
          <pre class="embed-snippet-code" data-embed-code="widget"></pre>
        </div>
        <div class="embed-snippet-box" data-embed-panel="link">
          <button type="button" class="embed-copy" data-embed-copy="link" aria-label="Copy link"><span>Copy</span></button>
          <pre class="embed-snippet-code" data-embed-code="link"></pre>
        </div>
      </div>
    </div>
  </div>
</div>
"""

REPORT_MODAL = r"""
<div class="report-modal" id="reportModal" role="dialog" aria-modal="true" aria-labelledby="reportModalTitle" hidden aria-hidden="true">
  <div class="report-modal-panel" role="document">
    <div class="report-modal-head">
      <h2 id="reportModalTitle">Report a problem</h2>
      <button type="button" class="report-modal-close" data-report-close aria-label="Close">×</button>
    </div>
    <form class="report-form" id="reportForm">
      <input type="hidden" name="hash" id="reportHash" value="">
      <p class="report-modal-note">Reports require WGPlayground backend — disabled in local clone.</p>
      <div data-report-status></div>
      <button type="button" class="report-submit" data-report-close>Close</button>
    </form>
  </div>
</div>
"""

FOOTER = r"""
    <footer>
      <div class="foot-grid">
        <div>
          <a class="brand" href="index.html" style="margin-bottom: 14px;" aria-label="WGPlayground home">
            <span class="brand-text">WG<span>Playground</span></span>
          </a>
          <p style="max-width: 38ch; color: var(--ink-soft); margin-top: 14px; font-size: 14px;">Free HTML5 games — no installs</p>
        </div>
      </div>
      <div class="foot-bottom">
        <span>© 2026 WGPlayground clone</span>
      </div>
    </footer>
"""

ADS_MODAL = r"""
<div class="ads-modal" id="adsModal" role="dialog" aria-modal="true" hidden aria-hidden="true">
  <div class="ads-modal-panel" role="document">
    <button type="button" data-ads-close aria-label="Close">×</button>
    <p>Ad settings are managed on wgplayground.com</p>
    <pre data-ads-code>Local clone — no ad SDK</pre>
  </div>
</div>
"""

GAME_SCRIPTS = r"""
<script src="assets/images/image-map.js"></script>
<script src="assets/js/wg-catalog.js"></script>
<script src="assets/js/game-bootstrap.js"></script>
<script src="assets/vendor/wgp/public/v6/js/chrome.min.js"></script>
<script src="assets/vendor/wgp/public/v6/js/game.min.js"></script>
"""


def hash_from_item(item):
    for field in ("img", "bg", "preview"):
        val = item.get(field) or ""
        m = re.search(r"static\.wgplayground\.com/([a-f0-9]{32})/", val)
        if m:
            return m.group(1)
    return ""


def build_catalog(data):
    catalog = {}
    by_pub = {}

    def add(item):
        url = item.get("url", "")
        if "/game/" not in url:
            return
        path = url.split("/game/")[-1].rstrip("/")
        entry = {
            "name": item.get("name", ""),
            "by": item.get("by", ""),
            "img": item.get("img") or item.get("bg", ""),
            "url": url,
            "ifr": hash_from_item(item),
            "cats": item.get("cats")
            or (
                [item["meta"].split("·")[0].strip()]
                if item.get("meta")
                else []
            ),
            "copy": item.get("copy", ""),
            "meta": item.get("meta", ""),
            "c": item.get("c", ""),
        }
        catalog[path] = entry
        pub = entry["by"]
        by_pub.setdefault(pub, []).append(path)

    for item in data.get("hero", []):
        add(item)
    for items in data.get("grids", {}).values():
        for item in items:
            add(item)

    return catalog, by_pub


def extract_wg_data(html):
    m = re.search(r"window\.WG_DATA = (\{.*?\});\s*\n", html, re.S)
    if not m:
        raise SystemExit("WG_DATA not found in index.html")
    return json.loads(m.group(1))


def build_game_html(index_html):
    html = index_html
    html = re.sub(
        r"<title>[^<]*</title>",
        "<title>Play game — WGPlayground</title>",
        html,
        count=1,
    )
    html = html.replace('data-page="home"', 'data-page="game"', 1)
    if "game.min.css" not in html:
        html = html.replace(
            '<link rel="stylesheet" href="assets/css/local.css" />',
            '<link rel="stylesheet" href="assets/vendor/wgp/public/v6/css/game.min.css" />\n'
            '<link rel="stylesheet" href="assets/css/local.css" />',
            1,
        )

    html = re.sub(
        r"<main class=\"main\" id=\"main\">.*?</main>",
        "<main class=\"main\" id=\"main\">" + GAME_MAIN + FOOTER + "\n  </main>",
        html,
        count=1,
        flags=re.S,
    )

    # Strip homepage tail (modals, WG_DATA, home scripts) after shell </div>
    shell_end = html.find("</main>\n</div>")
    if shell_end != -1:
        tail_start = shell_end + len("</main>\n</div>")
        markers = [
            html.find('<div class="embed-modal" id="embedModal"', tail_start),
            html.find('<script src="assets/js/wg-catalog.js"', tail_start),
            html.find('<script src="assets/vendor/wgp/public/v6/js/audio.min.js"', tail_start),
        ]
        markers = [m for m in markers if m != -1]
        if markers:
            html = html[:tail_start] + "\n\n" + html[min(markers):]
    html = re.sub(r"<script>\s*window\.WG_DATA = \{.*?\};\s*</script>\s*", "", html, count=1, flags=re.S)
    html = re.sub(r'<script src="assets/js/local-patch\.js"></script>\s*', "", html, count=1)

    modals = EMBED_MODAL + REPORT_MODAL + ADS_MODAL
    html = re.sub(
        r"<script src=\"https://www\.wgplayground\.com/public/v6/js/audio\.min\.js.*?</script>\s*\n<script src=\"https://www\.wgplayground\.com/public/v6/js/ghost\.min\.js.*?</script>",
        modals + "\n" + GAME_SCRIPTS.strip(),
        html,
        count=1,
        flags=re.S,
    )
    # Also handle already-localized index
    html = re.sub(
        r"<script src=\"assets/vendor/wgp/public/v6/js/audio\.min\.js\"></script>\s*\n<script src=\"assets/vendor/wgp/public/v6/js/ghost\.min\.js\"></script>",
        modals + "\n" + GAME_SCRIPTS.strip(),
        html,
        count=1,
        flags=re.S,
    )

    return html


def main():
    index_html = INDEX.read_text(encoding="utf-8")
    data = extract_wg_data(index_html)
    catalog, by_pub = build_catalog(data)

    catalog_js = (
        "window.WGP_CATALOG = "
        + json.dumps(catalog, ensure_ascii=False)
        + ";\nwindow.WGP_BY_PUBLISHER = "
        + json.dumps(by_pub, ensure_ascii=False)
        + ";\n"
    )
    CATALOG_JS.write_text(catalog_js, encoding="utf-8")

    game_html = build_game_html(index_html)
    GAME_HTML.write_text(game_html, encoding="utf-8")
    print(f"Wrote {CATALOG_JS} ({len(catalog)} games)")
    print(f"Wrote {GAME_HTML}")


if __name__ == "__main__":
    main()
