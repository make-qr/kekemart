#!/usr/bin/env python3
"""Rewrite saved WGPlayground HTML to use local vendor assets + keep game iframe embed."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR_PREFIX = "assets/vendor/wgp"

# Strip third-party trackers / ads
STRIP_PATTERNS = [
    re.compile(r'<link rel="dns-prefetch" href="https://universal\.wgplayer\.com"/>?\s*', re.I),
    re.compile(
        r'<script[^>]*>!function\(e,t\).*?universal\.wgplayer\.com.*?</script>\s*',
        re.S | re.I,
    ),
    re.compile(r'<script async src="https://fundingchoicesmessages\.google\.com[^"]*"></script>\s*', re.I),
    re.compile(r'<script async src="https://www\.googletagmanager\.com[^"]*"></script>\s*', re.I),
    re.compile(r"<script>window\.dataLayer.*?</script>\s*", re.S),
    re.compile(r'<script>\(function\(\)\{function c\(\).*?cdn-cgi/challenge-platform.*?</script>\s*', re.S),
]

REPLACEMENTS = [
    # WG public → local vendor
    (
        re.compile(r"https://www\.wgplayground\.com(/public/[^\"'?>\s]+)(\?v=\d+)?", re.I),
        lambda m: f"{VENDOR_PREFIX}{m.group(1)}",
    ),
    # scout CDN → local static mirror
    (
        re.compile(
            r"https://scout\.wgimager\.com/[^\"'\s)]+/https://static\.wgplayground\.com/([^\"'\s)>?]+)",
            re.I,
        ),
        lambda m: f"{VENDOR_PREFIX}/static/{m.group(1).split('?')[0]}",
    ),
    (
        re.compile(r"https://static\.wgplayground\.com/([^\"'\s)>?]+)", re.I),
        lambda m: f"{VENDOR_PREFIX}/static/{m.group(1).split('?')[0]}",
    ),
    # cf-fonts → Google Fonts (lighter than mirroring 30 woff2)
    (
        re.compile(r"url\(/cf-fonts/[^)]+\)", re.I),
        "/* fonts: see link in head */",
    ),
    (
        re.compile(r"assets/vendor/wgp/public/new/images/favicon\.ico", re.I),
        "assets/images/site/favicon.ico",
    ),
    (
        re.compile(r"assets/vendor/wgp/public/new/images/logo-square\.svg", re.I),
        "assets/images/site/logo-square.svg",
    ),
    (
        re.compile(r"assets/vendor/wgp/public/new/images/logo\.svg", re.I),
        "assets/images/site/logo.svg",
    ),
    (
        re.compile(r"assets/vendor/wgp/public/new/images/logo_wgp_og\.png", re.I),
        "assets/images/site/og-default.png",
    ),
    (re.compile(r'href="/"', re.I), 'href="index.html"'),
    (re.compile(r'href="/games-catalogue"', re.I), 'href="games-catalogue.html"'),
]

FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
)

LOCAL_PATCH = '<script src="assets/images/image-map.js"></script>\n<script src="assets/js/game-routes.js"></script>\n<script src="assets/js/local-patch.js"></script>\n'
LOCAL_CSS = '<link rel="stylesheet" href="assets/css/local.css" />\n'


def localize(text: str, *, is_game_page: bool = False) -> str:
    for pat in STRIP_PATTERNS:
        text = pat.sub("", text)

    for item in REPLACEMENTS:
        if isinstance(item[0], re.Pattern):
            text = item[0].sub(item[1], text)
        else:
            text = text.replace(item[0], item[1])

    # Remove inline @font-face blob (replaced by Google Fonts)
    text = re.sub(
        r"<style type=\"text/css\">@font-face \{font-family:Inter.*?</style>\s*",
        "",
        text,
        count=1,
        flags=re.S,
    )
    if "fonts.googleapis.com/css2?family=Inter" not in text:
        text = text.replace("</head>", f"{FONT_LINK}\n</head>", 1)

    if "assets/css/local.css" not in text:
        text = re.sub(
            r"(<link rel=\"stylesheet\" href=\"assets/vendor/wgp/public/v6/css/[^\"]+\.css\" />\s*)+",
            lambda m: m.group(0) + LOCAL_CSS,
            text,
            count=1,
        )

    if "local-patch.js" not in text:
        text = text.replace("<body", f"{LOCAL_PATCH}<body", 1)
    else:
        if "game-routes.js" not in text:
            text = text.replace(
                '<script src="assets/js/local-patch.js"></script>',
                '<script src="assets/images/image-map.js"></script>\n'
                '<script src="assets/js/game-routes.js"></script>\n'
                '<script src="assets/js/local-patch.js"></script>',
                1,
            )
        elif "image-map.js" not in text:
            text = text.replace(
                '<script src="assets/js/local-patch.js"></script>',
                '<script src="assets/images/image-map.js"></script>\n'
                '<script src="assets/js/local-patch.js"></script>',
                1,
            )

    # Game iframe — keep embed URL (runtime on play.wgplayground.com)
    # Already present in saved HTML; ensure embed modal uses same

    if is_game_page and "game-bootstrap.js" not in text:
        bootstrap = '<script src="assets/js/wg-catalog.js"></script>\n<script src="assets/js/game-bootstrap.js"></script>\n'
        text = text.replace(
            '<script src="assets/js/local-patch.js"></script>',
            f'<script src="assets/js/local-patch.js"></script>\n{bootstrap}',
            1,
        )

    return text


def process_file(path: Path, out: Path | None = None) -> Path:
    out = out or path
    is_game = "perfect-match" in path.name or path.name == "game.html"
    text = path.read_text(encoding="utf-8", errors="replace")
    text = localize(text, is_game_page=is_game)
    out.write_text(text, encoding="utf-8")
    return out


def main() -> int:
    targets = sys.argv[1:] or ["index.html", "perfect-match-3d.html", "game.html"]
    for name in targets:
        p = ROOT / name
        if not p.exists():
            print(f"Skip (missing): {name}")
            continue
        process_file(p)
        print(f"Localized: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
