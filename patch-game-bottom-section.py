#!/usr/bin/env python3
"""Replace static More from GAMEPUSH bottom block with dynamic trending/new sections."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAMES_DIR = ROOT / "games"
TEMPLATE = ROOT / "perfect-match-3d.html"

OLD_HEAD = re.compile(
    r'<div class="section-head">\s*'
    r'<h2><span class="dot"[^>]*></span>(?:More from GAMEPUSH|More MonkeyMart classics)</h2>.*?</div>\s*'
    r'<div class="grid grid-dense">.*?(?=\s*<div class="embed-modal report-modal")',
    re.S,
)

# Leftover static cards when the old grid regex stopped at the first inner </div>.
ORPHAN_AFTER_BOTTOM = re.compile(
    r'(id="grid-game-recommend"></div>\s*</section>\s*)'
    r'.*?(?=\s*<div class="embed-modal report-modal")',
    re.S,
)

BROKEN_SOCIAL = re.compile(
    r'(<div class="list-card list-social">\s*'
    r'<div class="list-header">\s*'
    r'<div class="list-header-eyebrow">More from this publisher</div>)\s*'
    r'(?:.*?</aside>)',
    re.S,
)


def bottom_block(*, depth: int = 0) -> str:
    p = "../" if depth else ""
    return f"""    <section class="mm-game-bottom" id="mmGameBottom" aria-label="Discover more games">
      <div class="section-head">
        <h2><span class="dot hot"></span>Trending now</h2>
        <a class="more" href="{p}games-catalogue.html?view=trending">See all &rarr;</a>
      </div>
      <div class="grid grid-dense" id="grid-game-trending"></div>

      <div class="section-head">
        <h2><span class="dot new"></span>New releases</h2>
        <a class="more" href="{p}games-catalogue.html?view=new">See all &rarr;</a>
      </div>
      <div class="grid grid-dense" id="grid-game-new"></div>

      <div class="section-head mm-game-recommend-head" id="mmRecommendHead" hidden>
        <h2><span class="dot" style="background:#a855f7"></span>Recommended for you</h2>
      </div>
      <div class="grid grid-dense" id="grid-game-recommend"></div>
    </section>

"""


def fix_broken_social(html: str, *, depth: int = 0) -> str:
    """Repair truncated list-social sidebar (broken template edit)."""
    if 'list-header-eyebrow">More from this publisher</div>\n            \n              </aside>' not in html:
        return html
    p = "../" if depth else ""
    publisher_cards = f"""            <h4>by GAMEPUSH</h4>
          </div>
          <div class="list-items" id="mmPublisherSideCards">
          </div>
        </div>
              </aside>"""
    return BROKEN_SOCIAL.sub(r"\1\n" + publisher_cards, html, count=1)


def fix_see_all_links(html: str, *, depth: int = 0) -> str:
    p = "../" if depth else ""
    html = html.replace(
        f'href="{p}games-catalogue.html?sort=1"',
        f'href="{p}games-catalogue.html?view=trending"',
    )
    html = html.replace(
        f'href="{p}games-catalogue.html?sort=2"',
        f'href="{p}games-catalogue.html?view=new"',
    )
    return html


def strip_orphan_cards(html: str) -> str:
  if 'id="mmGameBottom"' not in html:
    return html
  return ORPHAN_AFTER_BOTTOM.sub(r"\1\n\n        ", html, count=1)


def patch_html(html: str, *, depth: int = 0) -> str:
    html = fix_broken_social(html, depth=depth)
    html = fix_see_all_links(html, depth=depth)
    if 'id="mmGameBottom"' in html and 'id="grid-game-trending"' in html:
        return strip_orphan_cards(html)
    if OLD_HEAD.search(html):
        html = OLD_HEAD.sub(bottom_block(depth=depth), html, count=1)
    return strip_orphan_cards(html)


def patch_file(path: Path) -> bool:
    depth = 1 if path.parent.name == "games" else 0
    html = path.read_text(encoding="utf-8")
    patched = patch_html(html, depth=depth)
    if patched != html:
        path.write_text(patched, encoding="utf-8")
        return True
    return False


def main() -> None:
    targets = [TEMPLATE, ROOT / "monkey-mart.html"]
    if GAMES_DIR.is_dir():
        targets.extend(sorted(GAMES_DIR.glob("*.html")))

    n = 0
    for path in targets:
        if path.is_file() and patch_file(path):
            n += 1
    print(f"Patched game bottom section in {n} files")


if __name__ == "__main__":
    main()
