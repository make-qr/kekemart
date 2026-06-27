#!/usr/bin/env python3
"""Download WGPlayground public CSS/JS/images referenced in local HTML → assets/vendor/wgp/."""
from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "assets" / "vendor" / "wgp"
MANIFEST = ROOT / "assets" / "vendor" / "manifest.json"
BASE = "https://www.wgplayground.com"

# Core static files used across index + game pages
STATIC_PATHS = [
    # CSS
    "/public/v6/css/style.min.css",
    "/public/v6/css/modals.min.css",
    "/public/v6/css/played.min.css",
    "/public/v6/css/hotnot.min.css",
    "/public/v6/css/engagement.min.css",
    "/public/v6/css/taste.min.css",
    "/public/v6/css/quickmatch.min.css",
    "/public/v6/css/personal-best.min.css",
    "/public/v6/css/game.min.css",
    "/public/v6/css/install.min.css",
    # JS — shared
    "/public/v6/js/audio.min.js",
    "/public/v6/js/catalog-export.min.js",
    "/public/v6/js/taste-graph.min.js",
    "/public/v6/js/taste-manager.min.js",
    "/public/v6/js/verdict-match.min.js",
    "/public/v6/js/auth.min.js",
    "/public/v6/js/chrome.min.js",
    "/public/v6/js/tracking.min.js",
    "/public/v6/js/app.min.js",
    "/public/v6/js/game.min.js",
    "/public/v6/js/game-features.min.js",
    "/public/v6/js/rating.min.js",
    "/public/v6/js/brag.min.js",
    "/public/v6/js/install.min.js",
    "/public/v6/js/modals.min.js",
    "/public/v6/js/played.min.js",
    "/public/v6/js/hotnot.min.js",
    "/public/v6/js/surprise.min.js",
    "/public/v6/js/quickmatch.min.js",
    "/public/v6/js/trailer.min.js",
    "/public/v6/js/foryou.min.js",
    "/public/v6/js/tastecard.min.js",
    "/public/v6/js/shared-with-me.min.js",
    "/public/v6/js/verdict-share.min.js",
    "/public/v6/js/challenge-arrival.min.js",
    "/public/v6/js/share.min.js",
    "/public/v6/js/score.min.js",
    "/public/v6/js/engagement.min.js",
    "/public/v6/js/personal-best.min.js",
    "/public/v6/js/daily-collapse.min.js",
    "/public/v6/js/ghost.min.js",
    # Images / icons
    "/public/new/images/favicon.ico",
    "/public/new/images/logo_wgp_og.png",
    "/public/new/images/logo-square.svg",
    "/public/new/images/logo.svg",
]

URL_IN_HTML = re.compile(
    r"https://www\.wgplayground\.com(/public/[^\"'?\s>]+)",
    re.I,
)
URL_IN_CSS = re.compile(
    r"url\((['\"]?)(/public/[^)'\"]+)\1\)",
    re.I,
)
STATIC_IMG = re.compile(
    r"https://static\.wgplayground\.com/([a-f0-9]{32}/wgplayground/[^\"'\s)>]+)",
    re.I,
)
SCOUT_IMG = re.compile(
    r"https://scout\.wgimager\.com/[^/]+/[^/]+/[^/]+/(https://static\.wgplayground\.com/[^\"'\s)>]+)",
    re.I,
)


def fetch(url: str, dest: Path, ctx: ssl.SSLContext) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return True
    req = urllib.request.Request(url, headers={"User-Agent": "WGP-Local-Mirror/1.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            dest.write_bytes(resp.read())
        return True
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP {e.code} {url}")
        return False
    except Exception as e:
        print(f"  ✗ {e} {url}")
        return False


def local_path(pub_path: str) -> Path:
    """/public/v6/css/foo.css → assets/vendor/wgp/public/v6/css/foo.css"""
    return VENDOR / pub_path.lstrip("/")


def collect_urls_from_html() -> set[str]:
    paths: set[str] = set(STATIC_PATHS)
    for html in ROOT.glob("*.html"):
        text = html.read_text(encoding="utf-8", errors="replace")
        for m in URL_IN_HTML.finditer(text):
            paths.add(m.group(1).split("?")[0])
        for m in SCOUT_IMG.finditer(text):
            paths.add("/" + m.group(1).split("static.wgplayground.com", 1)[-1].split("?")[0])
        for m in STATIC_IMG.finditer(text):
            paths.add(f"/static-from-cdn/{m.group(1)}")
    catalog = ROOT / "assets/js/wg-catalog.js"
    if catalog.exists():
        text = catalog.read_text(encoding="utf-8", errors="replace")
        for m in STATIC_IMG.finditer(text):
            paths.add(f"/static-from-cdn/{m.group(1)}")
        for m in SCOUT_IMG.finditer(text):
            inner = m.group(1).replace("https://static.wgplayground.com", "")
            paths.add(f"/static-from-cdn{inner.split('?')[0]}")
    return paths


def download_static_path(pub_path: str, ctx: ssl.SSLContext, manifest: dict) -> None:
    if pub_path.startswith("/static-from-cdn/"):
        rel = pub_path.replace("/static-from-cdn/", "")
        url = f"https://static.wgplayground.com/{rel}"
        dest = VENDOR / "static" / rel
    else:
        url = BASE + pub_path
        dest = local_path(pub_path)
    if fetch(url, dest, ctx):
        manifest[pub_path] = str(dest.relative_to(ROOT)).replace("\\", "/")
        print(f"  ✓ {dest.relative_to(ROOT)}")


def scan_css_assets(ctx: ssl.SSLContext, manifest: dict) -> None:
    for css in VENDOR.rglob("*.css"):
        text = css.read_text(encoding="utf-8", errors="replace")
        for m in URL_IN_CSS.finditer(text):
            pub = m.group(2).split("?")[0]
            if pub not in manifest:
                download_static_path(pub, ctx, manifest)


def mirror_game_covers(ctx: ssl.SSLContext, manifest: dict, limit: int = 80) -> None:
    catalog = ROOT / "assets/js/wg-catalog.js"
    if not catalog.exists():
        return
    text = catalog.read_text(encoding="utf-8")
    hashes = list(dict.fromkeys(re.findall(r"static\.wgplayground\.com/([a-f0-9]{32})/", text)))[:limit]
    for h in hashes:
        # fetch listing page thumb pattern from catalog
        for m in re.finditer(
            rf"static\.wgplayground\.com/{h}/wgplayground/([a-f0-9]{{32}})\.(jpg|png|webp)",
            text,
        ):
            rel = f"{h}/wgplayground/{m.group(1)}.{m.group(2)}"
            pub = f"/static-from-cdn/{rel}"
            if pub not in manifest:
                download_static_path(pub, ctx, manifest)


def main() -> None:
    ctx = ssl.create_default_context()
    VENDOR.mkdir(parents=True, exist_ok=True)
    paths = collect_urls_from_html()
    manifest: dict = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    print(f"=== Mirror {len(paths)} WGPlayground assets ===")
    for pub in sorted(paths):
        download_static_path(pub, ctx, manifest)

    print("=== Scan CSS url() ===")
    scan_css_assets(ctx, manifest)

    print("=== Game cover thumbnails (catalog) ===")
    # Skipped — seo-images.py writes assets/images/games/<slug>/

    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nWrote {MANIFEST} ({len(manifest)} files)")


if __name__ == "__main__":
    main()
