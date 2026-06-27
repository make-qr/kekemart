#!/usr/bin/env python3
"""Build games-catalogue.html from index.html shell + WGP catalog browser."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
OUT = ROOT / "games-catalogue.html"

FOOTER = """
    <footer>
      <div class="foot-grid">
        <div>
          <a class="brand" href="index.html" style="margin-bottom: 14px;" aria-label="WGPlayground home">
            <span class="brand-text">WG<span>Playground</span></span>
          </a>
          <p style="max-width: 38ch; color: var(--ink-soft); margin-top: 14px; font-size: 14px; line-height: 1.55;">
            Free HTML5 games — local clone with iframe embed.
          </p>
        </div>
        <div><h5>Browse</h5><ul><li><a href="games-catalogue.html">All games</a></li><li><a href="index.html">Home</a></li></ul></div>
      </div>
      <div class="foot-bottom">
        <span>© 2026 WGPlayground clone</span>
        <span>Free HTML5 games · No installs</span>
      </div>
    </footer>
"""

MAIN = """
    <section class="catalog-hero" aria-label="Game catalogue">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href="index.html">Home</a>
        <span aria-hidden="true">›</span>
        <span aria-current="page">All games</span>
      </nav>
      <h1>All games</h1>
      <p class="catalog-sub" id="catalogSubtitle">Browse free HTML5 games</p>
      <form class="catalog-search" id="catalogSearchForm" role="search" aria-label="Search games" onsubmit="return false;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
        <input type="search" id="catalogSearchInput" placeholder="Search games…" autocomplete="off" />
      </form>
    </section>

    <div class="catalog-chips" id="catalogChips" aria-label="Filter by category"></div>

    <div class="section-head catalog-results-head">
      <h2 id="catalogResultsTitle">All games</h2>
      <span class="catalog-count" id="catalogCount"></span>
    </div>

    <div class="grid" id="catalogGrid" aria-live="polite"></div>
    <div class="load-more">
      <button type="button" id="catalogLoadMore" hidden>Load more games</button>
    </div>
    <p class="catalog-empty" id="catalogEmpty" hidden>No games match your search.</p>
""" + FOOTER

SCRIPTS = """
<script src="assets/images/image-map.js"></script>
<script src="assets/js/game-routes.js"></script>
<script src="assets/js/wg-catalog.js"></script>
<script src="assets/js/browse-catalog.js"></script>
<script src="assets/vendor/wgp/public/v6/js/chrome.min.js"></script>
<script src="assets/js/local-patch.js"></script>
"""


def build(html: str) -> str:
    html = re.sub(r"<title>[^<]*</title>", "<title>All games — WGPlayground</title>", html, count=1)
    html = html.replace('data-page="home"', 'data-page="catalogue"', 1)
    html = re.sub(
        r'<form class="search"[^>]*>.*?</form>',
        '<form class="search" action="games-catalogue.html" method="get" role="search" aria-label="Search games">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">'
        '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
        '<input type="search" name="q" placeholder="Search games…" autocomplete="off" />'
        '<kbd>/</kbd></form>',
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace(
        'href="https://www.wgplayground.com/games-catalogue"',
        'href="games-catalogue.html"',
    )
    html = re.sub(
        r"<main class=\"main\" id=\"main\">.*?</main>",
        "<main class=\"main\" id=\"main\">" + MAIN + "\n  </main>",
        html,
        count=1,
        flags=re.S,
    )

    shell_end = html.find("</main>\n</div>")
    if shell_end != -1:
        tail_start = shell_end + len("</main>\n</div>")
        body_end = html.rfind("</body>")
        if body_end > tail_start:
            html = html[:tail_start] + "\n" + SCRIPTS.strip() + "\n\n" + html[body_end:]

    html = re.sub(r"<script>\s*window\.WG_DATA = \{.*?\};\s*</script>\s*", "", html, count=1, flags=re.S)
    return html


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"Missing {INDEX}")
    out = build(INDEX.read_text(encoding="utf-8"))
    OUT.write_text(out, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
