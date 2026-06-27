#!/usr/bin/env python3
"""Copy SEO/legal pages from papasgames-3d/3t + generate /game/ redirects."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_LEGACY = Path.home() / "NAS/projects/personal/papasgames-3d/3t"
ROUTES_JS = ROOT / "assets/js/mm-native-routes.js"

LEGAL_ROOT_FILES = (
    "about.html",
    "privacy.html",
    "terms.html",
    "faq.html",
    "contact.html",
    "disclaimer.html",
    "cookie-policy.html",
)

SEO_DIRS = (
    "how-to-play-monkey-mart",
    "monkey-mart-tips",
    "monkey-mart-unblocked",
)

# old game filename stem -> native catalog slug
GAME_ALIASES: dict[str, str] = {
    "1v1-lol": "1v1.lol",
    "ducklife-4": "ducklife4",
    "motox3m": "moto-x3m",
    "motox3m-2": "moto-x3m-2",
    "moto-x3m-4-winter": "moto-x3m-winter",
    "moto-x3m-5-pool-party": "moto-x3m-pool-party",
    "moto-x3m-spooky-land": "moto-x3m-spooky-land",
    "fireboy-and-watergirl-1": "fireboy-and-watergirl-1",
    "monkey-mart": "monkey-mart",
}


def load_native_routes() -> dict[str, str]:
    text = ROUTES_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.MM_NATIVE_ROUTES\s*=\s*(\{.*?\});", text, re.S)
    if not m:
        return {}
    return json.loads(m.group(1))


def resolve_game_redirect(old_stem: str, routes: dict[str, str]) -> str:
    candidates = [
        old_stem,
        GAME_ALIASES.get(old_stem, ""),
        old_stem.replace("-", "."),
        old_stem.replace(".", "-"),
    ]
    for slug in candidates:
        if slug and slug in routes:
            return "/" + routes[slug]
    if old_stem == "monkey-mart":
        return "/monkey-mart.html"
    return "/games-catalogue.html"


def redirect_html(target: str, title: str = "Redirecting…") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta http-equiv="refresh" content="0; url={target}"/>
<link rel="canonical" href="https://monkeymart.one{target}"/>
<title>{title}</title>
</head>
<body>
<p>Moved — <a href="{target}">continue to MonkeyMart.one</a></p>
</body>
</html>
"""


def copy_tree(src: Path, dest: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    elif src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def migrate(dest: Path, legacy_root: Path) -> dict[str, int]:
    stats = {"legal": 0, "seo_dirs": 0, "blog": 0, "game_redirects": 0, "assets": 0}
    if not legacy_root.is_dir():
        raise FileNotFoundError(f"Legacy site not found: {legacy_root}")

    ads = legacy_root / "ads.txt"
    if ads.is_file():
        shutil.copy2(ads, dest / "ads.txt")

    for name in LEGAL_ROOT_FILES:
        src = legacy_root / name
        if src.is_file():
            shutil.copy2(src, dest / name)
            stats["legal"] += 1

    for dirname in SEO_DIRS:
        src = legacy_root / dirname
        if src.is_dir():
            copy_tree(src, dest / dirname)
            stats["seo_dirs"] += 1

    blog_src = legacy_root / "blog"
    if blog_src.is_dir():
        copy_tree(blog_src, dest / "blog")
        stats["blog"] = len(list((dest / "blog").glob("*.html")))

    for sub in ("css", "img"):
        src = legacy_root / "assets" / sub
        if src.is_dir():
            copy_tree(src, dest / "assets" / sub)
            stats["assets"] += 1

    routes = load_native_routes()
    game_dir = dest / "game"
    game_dir.mkdir(parents=True, exist_ok=True)
    old_games = legacy_root / "game"
    if old_games.is_dir():
        for old in old_games.glob("*.html"):
            stem = old.stem
            target = resolve_game_redirect(stem, routes)
            out = game_dir / old.name
            out.write_text(redirect_html(target, title=f"Play {stem} — MonkeyMart.one"), encoding="utf-8")
            stats["game_redirects"] += 1

    manifest = dest / "legacy-urls.json"
    legacy_urls: list[str] = []
    for dirname in SEO_DIRS:
        legacy_urls.append(f"/{dirname}/")
    legacy_urls.extend(f"/{f}" for f in LEGAL_ROOT_FILES)
    for p in sorted((dest / "blog").glob("*.html")) if (dest / "blog").is_dir() else []:
        legacy_urls.append(f"/blog/{p.name}")
    for p in sorted(game_dir.glob("*.html")):
        legacy_urls.append(f"/game/{p.name}")
    manifest.write_text(json.dumps(sorted(legacy_urls), indent=2) + "\n", encoding="utf-8")

    return stats


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=Path, default=ROOT)
    parser.add_argument("--legacy", type=Path, default=DEFAULT_LEGACY)
    args = parser.parse_args()
    stats = migrate(args.dest.resolve(), args.legacy.resolve())
    print("Legacy migrate:", stats)


if __name__ == "__main__":
    main()
