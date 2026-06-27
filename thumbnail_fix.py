"""Fix broken game thumbnail URLs in HTML and JS."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE_MAP = ROOT / "assets/images/image-map.json"

OG_JPG_RE = re.compile(
    r"(background-image:url\(['\"])(assets/images/games/[^'\"]+/)og\.jpg(['\"]\))",
    re.I,
)
INLINE_URL_RE = re.compile(
    r"(background-image:url\(['\"])([^'\"]+)(['\"]\))",
    re.I,
)
SCOUT_RE = re.compile(
    r"https://scout\.wgimager\.com/[^\"'\s)]+/(https://static\.wgplayground\.com/[^\"'\s)>?]+)",
    re.I,
)
STATIC_HASH_RE = re.compile(
    r"https://static\.wgplayground\.com/([a-f0-9]{32})/",
    re.I,
)


def _prefix(depth: int) -> str:
    return "../" * depth


def load_image_map() -> dict:
    if not IMAGE_MAP.exists():
        return {}
    return json.loads(IMAGE_MAP.read_text(encoding="utf-8"))


def resolve_local_image(url: str, image_map: dict) -> str:
    if not url or url.startswith("data:"):
        return url
    if url.startswith("http://") or url.startswith("https://"):
        scout = SCOUT_RE.search(url)
        if scout:
            url = scout.group(1)
        hash_m = STATIC_HASH_RE.search(url)
        if hash_m and hash_m.group(1) in image_map:
            return image_map[hash_m.group(1)]["thumbnail"]
        vendor = re.search(r"assets/vendor/wgp/static/([a-f0-9]{32})/", url, re.I)
        if vendor and vendor.group(1) in image_map:
            return image_map[vendor.group(1)]["thumbnail"]
        return url

    clean = url.lstrip("/")
    if clean.startswith("../"):
        clean = clean[3:]

    path = ROOT / clean
    if path.exists():
        return url

    if "/og.jpg" in clean.lower():
        for alt in (clean.replace("/og.jpg", "/og.webp"), clean.replace("/og.jpg", "/thumbnail.webp")):
            if (ROOT / alt).exists():
                if url.startswith("../"):
                    return "../" + alt
                return alt

    if clean.endswith("/og.webp"):
        thumb = clean.replace("/og.webp", "/thumbnail.webp")
        if (ROOT / thumb).exists():
            if url.startswith("../"):
                return "../" + thumb
            return thumb

    return url


def with_depth(url: str, depth: int) -> str:
    if not url or url.startswith("http://") or url.startswith("https://"):
        return url
    p = _prefix(depth)
    clean = url.lstrip("/")
    while clean.startswith("../"):
        clean = clean[3:]
    if not p:
        return clean
    return p + clean


def patch_html_thumbnails(html: str, *, depth: int = 0, image_map: dict | None = None) -> str:
    if image_map is None:
        image_map = load_image_map()

    def repl_url(m: re.Match[str]) -> str:
        prefix, raw, suffix = m.group(1), m.group(2), m.group(3)
        fixed = resolve_local_image(raw, image_map)
        fixed = with_depth(fixed, depth)
        return f"{prefix}{fixed}{suffix}"

    html = INLINE_URL_RE.sub(repl_url, html)

    # img src without ../ on nested pages
    if depth > 0:

        def repl_src(m: re.Match[str]) -> str:
            attr, path = m.group(1), m.group(2)
            if path.startswith("../") or path.startswith("http"):
                return m.group(0)
            fixed = resolve_local_image(path, image_map)
            return f'{attr}{with_depth(fixed, depth)}"'

        html = re.sub(
            r'((?:src|content)=["\'])(assets/(?:images|vendor)[^"\']*)(["\'])',
            lambda m: m.group(1) + with_depth(resolve_local_image(m.group(2), image_map), depth) + m.group(3),
            html,
        )

    return html


def patch_file(path: Path, *, depth: int | None = None) -> bool:
    if depth is None:
        rel = path.relative_to(ROOT).as_posix()
        depth = 1 if rel.startswith("games/") else 0
    text = path.read_text(encoding="utf-8")
    patched = patch_html_thumbnails(text, depth=depth)
    if patched != text:
        path.write_text(patched, encoding="utf-8")
        return True
    return False


def main() -> None:
    image_map = load_image_map()
    targets: list[Path] = []
    targets.extend(ROOT.glob("*.html"))
    targets.extend(ROOT.glob("games/*.html"))
    if (ROOT / "perfect-match-3d.html").exists():
        targets.append(ROOT / "perfect-match-3d.html")

    changed = 0
    for path in sorted(set(targets)):
        rel = path.relative_to(ROOT).as_posix()
        depth = 1 if rel.startswith("games/") else 0
        if patch_file(path, depth=depth):
            changed += 1
    print(f"Patched thumbnails in {changed}/{len(targets)} HTML files (image-map: {len(image_map)} games)")


if __name__ == "__main__":
    main()
