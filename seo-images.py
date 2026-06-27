#!/usr/bin/env python3
"""Mirror game images with SEO-friendly paths + alt text map."""
from __future__ import annotations

import json
import re
import shutil
import ssl
import urllib.error
import urllib.request
from pathlib import Path

from catalog_utils import parse_catalog_file, slug_from_path, write_catalog_js

ROOT = Path(__file__).resolve().parent
CATALOG_JS = ROOT / "assets/js/wg-catalog.js"
IMAGES_ROOT = ROOT / "assets/images/games"
SITE_IMAGES = ROOT / "assets/images/site"
IMAGE_MAP = ROOT / "assets/images/image-map.json"

STATIC_RE = re.compile(
    r"https://static\.wgplayground\.com/([a-f0-9]{32})/wgplayground/([a-f0-9]{32})\.(jpg|jpeg|png|webp)",
    re.I,
)
SCOUT_RE = re.compile(
    r"https://scout\.wgimager\.com/[^\"'\s)]+/(https://static\.wgplayground\.com/[^\"'\s)>?]+)",
    re.I,
)


def alt_text(name: str, cats: list[str]) -> str:
    cat = cats[0] if cats else "HTML5"
    return f"{name} — free online {cat.lower()} game"


def parse_catalog() -> dict:
    if not CATALOG_JS.exists():
        raise SystemExit(f"Missing {CATALOG_JS} — run build-game-page.py first")
    catalog, _ = parse_catalog_file(CATALOG_JS)
    return catalog


def static_url_from_img(img_url: str) -> tuple[str, str, str] | None:
    """Return (game_hash, file_id, ext) from scout or static URL."""
    if not img_url:
        return None
    scout = SCOUT_RE.search(img_url)
    if scout:
        img_url = scout.group(1)
    m = STATIC_RE.search(img_url)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3).lower()


def fetch(url: str, dest: Path, ctx: ssl.SSLContext) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "WGP-SEO-Images/1.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=90) as resp:
            dest.write_bytes(resp.read())
        return dest.stat().st_size > 0
    except (urllib.error.HTTPError, OSError) as e:
        print(f"  ✗ {dest.name}: {e}")
        return False


def mirror_site_branding(ctx: ssl.SSLContext) -> None:
    SITE_IMAGES.mkdir(parents=True, exist_ok=True)
    items = [
        ("https://www.wgplayground.com/public/new/images/favicon.ico", "favicon.ico"),
        ("https://www.wgplayground.com/public/new/images/logo.svg", "logo.svg"),
        ("https://www.wgplayground.com/public/new/images/logo-square.svg", "logo-square.svg"),
        ("https://www.wgplayground.com/public/new/images/logo_wgp_og.png", "og-default.png"),
    ]
    for url, name in items:
        dest = SITE_IMAGES / name
        if not dest.exists():
            fetch(url, dest, ctx)


def resize_save(src: Path, dest: Path, size: tuple[int, int]) -> bool:
    try:
        from PIL import Image

        im = Image.open(src)
        im = im.convert("RGB")
        im.thumbnail(size, Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.suffix.lower() == ".webp":
            im.save(dest, "WEBP", quality=82, method=6)
        else:
            im.save(dest, "JPEG", quality=85, optimize=True)
        return dest.exists()
    except ImportError:
        if src != dest:
            shutil.copy2(src, dest)
        return dest.exists()
    except Exception as e:
        print(f"  ⚠ resize {dest.name}: {e}")
        return False


def process_game(path: str, entry: dict, ctx: ssl.SSLContext, image_map: dict) -> dict:
    parsed = static_url_from_img(entry.get("img", ""))
    game_hash = entry.get("ifr", "")
    file_id = ""
    ext = "jpg"
    if parsed:
        game_hash, file_id, ext = parsed
    elif game_hash and game_hash in image_map:
        return entry  # already processed
    elif game_hash:
        # Re-fetch: look up original static file from vendor mirror or image-map
        vendor_glob = list((ROOT / "assets/vendor/wgp/static" / game_hash / "wgplayground").glob("*.*"))
        if vendor_glob:
            vf = vendor_glob[0]
            file_id = vf.stem
            ext = vf.suffix.lstrip(".").lower()
        else:
            print(f"  ✗ skip {slug_from_path(path)} (no source)")
            return entry
    else:
        return entry
    slug = slug_from_path(path)
    game_dir = IMAGES_ROOT / slug
    game_dir.mkdir(parents=True, exist_ok=True)

    static_url = f"https://static.wgplayground.com/{game_hash}/wgplayground/{file_id}.{ext}"
    raw = game_dir / f"source.{ext if ext != 'jpeg' else 'jpg'}"
    if not raw.exists():
        if not fetch(static_url, raw, ctx):
            print(f"  ✗ skip {slug}")
            return entry

    thumb_webp = game_dir / "thumbnail.webp"
    og_webp = game_dir / "og.webp"
    thumb_jpg = game_dir / "thumbnail.jpg"
    og_jpg = game_dir / "og.jpg"

    if not thumb_webp.exists() and not thumb_jpg.exists():
        resize_save(raw, thumb_webp, (480, 360))
        if not thumb_webp.exists():
            resize_save(raw, thumb_jpg, (480, 360))

    if not og_webp.exists() and not og_jpg.exists():
        resize_save(raw, og_webp, (1280, 720))
        if not og_webp.exists():
            resize_save(raw, og_jpg, (1280, 720))

    thumb_out = thumb_webp if thumb_webp.exists() else thumb_jpg
    og_out = og_webp if og_webp.exists() else og_jpg
    if not thumb_out.exists():
        return entry

    rel_thumb = str(thumb_out.relative_to(ROOT)).replace("\\", "/")
    rel_og = str(og_out.relative_to(ROOT)).replace("\\", "/")
    name = entry.get("name", slug)
    cats = entry.get("cats") or []
    alt = alt_text(name, cats)

    image_map[game_hash] = {
        "slug": slug,
        "path": path,
        "name": name,
        "thumbnail": rel_thumb,
        "og": rel_og,
        "alt": alt,
    }

    entry["img"] = rel_thumb
    entry["img_og"] = rel_og
    entry["img_alt"] = alt
    if entry.get("bg"):
        entry["bg"] = rel_og
    return entry


def rewrite_catalog_js(catalog: dict, by_pub: dict) -> None:
    write_catalog_js(catalog, by_pub, CATALOG_JS)


def patch_html_images() -> int:
    if not IMAGE_MAP.exists():
        return 0
    image_map = json.loads(IMAGE_MAP.read_text(encoding="utf-8"))
    count = 0
    for html in ROOT.glob("*.html"):
        text = html.read_text(encoding="utf-8")
        orig = text
        for h, meta in image_map.items():
            og = meta["og"]
            thumb = meta["thumbnail"]
            alt = meta.get("alt", meta.get("name", ""))
            text = re.sub(
                rf"assets/vendor/wgp/static/{re.escape(h)}/wgplayground/[a-f0-9]{{32}}\.[a-zA-Z]+",
                og,
                text,
                flags=re.I,
            )
            text = re.sub(
                rf"https://scout\.wgimager\.com/[^\"'\s)]+/https://static\.wgplayground\.com/{re.escape(h)}/[^\"'\s)>]+",
                og,
                text,
                flags=re.I,
            )
            # og/twitter meta
            text = text.replace(f'content="{og}"', f'content="{og}"')  # noop if already set
        # img alt for game covers missing alt
        for meta in image_map.values():
            alt = meta.get("alt", "")
            thumb = meta.get("thumbnail", "")
            if thumb and alt:
                text = re.sub(
                    rf'(<img[^>]+src="{re.escape(thumb)}"[^>]*)(/?>)',
                    lambda m: m.group(1) + (f' alt="{alt}"' if 'alt=' not in m.group(1) else '') + m.group(2),
                    text,
                    count=1,
                )
        if text != orig:
            html.write_text(text, encoding="utf-8")
            count += 1
    return count


def main() -> None:
    ctx = ssl.create_default_context()
    catalog = parse_catalog()
    _, by_pub = parse_catalog_file(CATALOG_JS)

    print("=== Site branding ===")
    mirror_site_branding(ctx)

    print(f"=== SEO images for {len(catalog)} games ===")
    image_map: dict = {}
    if IMAGE_MAP.exists():
        image_map = json.loads(IMAGE_MAP.read_text(encoding="utf-8"))

    for path, entry in catalog.items():
        slug = slug_from_path(path)
        print(f"  {slug}")
        process_game(path, entry, ctx, image_map)

    IMAGE_MAP.write_text(json.dumps(image_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    js_path = ROOT / "assets/images/image-map.js"
    js_path.write_text(
        "window.WGP_IMAGE_MAP = " + json.dumps(image_map, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    rewrite_catalog_js(catalog, by_pub)
    patched = patch_html_images()
    print(f"\nWrote {IMAGE_MAP} ({len(image_map)} games)")
    print(f"Patched {patched} HTML file(s)")
    print("Catalog img fields → assets/images/games/<slug>/thumbnail.webp|jpg")


if __name__ == "__main__":
    main()
