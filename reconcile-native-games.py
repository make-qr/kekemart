#!/usr/bin/env python3
"""Compare old MonkeyMart source vs portal native catalog and CDN reachability."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "monkeymart.one/source_game.monkeymart.one"
CATALOG_JS = ROOT / "assets/js/mm-native-catalog.js"
GAMES_DIR = ROOT / "games"
BRAND = json.loads((ROOT / "brand/monkeymart.json").read_text(encoding="utf-8"))
CDN = BRAND.get("gamesCdn", "https://games.monkeymart.one").rstrip("/")


def load_catalog() -> dict:
    text = CATALOG_JS.read_text(encoding="utf-8")
    m = re.search(r"window\.MM_NATIVE_CATALOG = (\{.*\});", text, re.S)
    if not m:
        raise SystemExit("Catalog not found")
    return json.loads(m.group(1))


def source_index_slugs() -> set[str]:
    html = (SOURCE / "index.html").read_text(encoding="utf-8", errors="replace")
    slugs: set[str] = set()
    for href in re.findall(r'href="(projects/[^"]+\.html)"', html):
        m = re.match(r"projects/([^/]+)/", href)
        if m:
            slugs.add(m.group(1))
    return slugs


def head(url: str) -> int | str:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "MM-Reconcile/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception as exc:
        return str(exc)[:40]


def main() -> int:
    catalog = load_catalog()
    source_slugs = source_index_slugs()
    catalog_slugs = set(catalog)

    missing_from_catalog = sorted(source_slugs - catalog_slugs)
    extra_in_catalog = sorted(catalog_slugs - source_slugs)
    missing_pages = [s for s in catalog_slugs if not (GAMES_DIR / f"mm-{s}.html").is_file()]

    broken: list[tuple[str, str, int | str]] = []
    for slug, g in sorted(catalog.items()):
        play = g.get("play", "")
        if play.startswith("http"):
            status = head(play)
            if status != 200:
                broken.append((slug, play, status))

    print(f"Source index slugs:     {len(source_slugs)}")
    print(f"Portal catalog:         {len(catalog_slugs)}")
    print(f"mm-*.html pages:        {len(list(GAMES_DIR.glob('mm-*.html')))}")
    print()
    if missing_from_catalog:
        print(f"Missing from catalog ({len(missing_from_catalog)}): {', '.join(missing_from_catalog)}")
    else:
        print("Missing from catalog:   none")
    if extra_in_catalog:
        print(f"Extra in catalog:       {', '.join(extra_in_catalog)}")
    if missing_pages:
        print(f"Missing pages:          {', '.join(missing_pages)}")
    print()
    embed_modes: dict[str, int] = {}
    for g in catalog.values():
        mode = g.get("embedMode", "?")
        embed_modes[mode] = embed_modes.get(mode, 0) + 1
    print("embedMode:", embed_modes)
    print()
    if broken:
        print(f"Broken play URLs ({len(broken)}):")
        for slug, url, status in broken[:20]:
            print(f"  {slug}: {status} — {url}")
        if len(broken) > 20:
            print(f"  ... and {len(broken) - 20} more")
        return 1
    print("All catalog play URLs:  OK (HTTP 200)")
    return 0 if not missing_from_catalog and not missing_pages else 1


if __name__ == "__main__":
    sys.exit(main())
