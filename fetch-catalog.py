#!/usr/bin/env python3
"""Fetch games from WGPlayground API and merge into wg-catalog.js (200–300 games)."""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

from catalog_utils import parse_catalog_file, write_catalog_js

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
CATALOG_JS = ROOT / "assets/js/wg-catalog.js"
API_BASE = "https://www.wgplayground.com/api/games_api/get_games"
TARGET = 500
BATCH = 50
SLEEP_SEC = 2.5
OFFSET_STATE = ROOT / ".fetch-catalog-offset"


def extract_wg_data(html: str) -> dict:
    m = re.search(r"window\.WG_DATA = (\{.*?\});\s*\n", html, re.S)
    if not m:
        raise SystemExit("WG_DATA not found in index.html")
    return json.loads(m.group(1))


def hash_from_item(item: dict) -> str:
    for field in ("img", "bg", "preview"):
        val = item.get(field) or ""
        m = re.search(r"static\.wgplayground\.com/([a-f0-9]{32})/", val)
        if m:
            return m.group(1)
    return ""


def catalog_from_wg_data(data: dict) -> dict[str, dict]:
    catalog: dict[str, dict] = {}

    def add(item: dict) -> None:
        url = item.get("url", "")
        if "/game/" not in url:
            return
        path = url.split("/game/")[-1].rstrip("/")
        catalog[path] = {
            "name": item.get("name", ""),
            "by": item.get("by", ""),
            "img": item.get("img") or item.get("bg", ""),
            "url": url,
            "ifr": hash_from_item(item),
            "cats": item.get("cats")
            or ([item["meta"].split("·")[0].strip()] if item.get("meta") else []),
            "copy": item.get("copy", ""),
            "meta": item.get("meta", ""),
            "c": item.get("c", ""),
        }

    for item in data.get("hero", []):
        add(item)
    for items in data.get("grids", {}).values():
        for item in items:
            add(item)
    return catalog


def api_fetch(limit: int, offset: int) -> list[dict]:
    url = f"{API_BASE}/{limit}/{offset}"
    proc = subprocess.run(
        [
            "curl",
            "-sL",
            "-A",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
            "-H",
            "Referer: https://www.wgplayground.com/games-catalogue",
            "-H",
            "Accept: application/json",
            url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed offset={offset}: {proc.stderr[:200]}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON offset={offset}: {proc.stdout[:120]}") from e
    return data.get("param", {}).get("games", [])


def api_to_entry(game: dict) -> tuple[str, dict] | None:
    site_url = game.get("site_url") or ""
    if "/game/" not in site_url:
        return None
    path = site_url.split("/game/")[-1].rstrip("/")
    dev = game.get("developer") or {}
    return path, {
        "name": game.get("name", ""),
        "by": dev.get("public_name") or dev.get("slug", "").replace("-", " ").title(),
        "img": game.get("image", ""),
        "url": site_url,
        "ifr": game.get("hash") or "",
        "cats": [c.get("name", "") for c in game.get("categories", []) if c.get("name")],
        "copy": (game.get("description") or "").replace("\n", " ").strip(),
        "meta": "",
        "c": "",
    }


def rebuild_by_publisher(catalog: dict[str, dict]) -> dict[str, list[str]]:
    by_pub: dict[str, list[str]] = {}
    for path, entry in catalog.items():
        pub = entry.get("by") or "Unknown"
        by_pub.setdefault(pub, []).append(path)
    return by_pub


def load_existing_catalog() -> dict[str, dict]:
    if not CATALOG_JS.exists():
        return {}
    try:
        catalog, _ = parse_catalog_file(CATALOG_JS)
        return catalog
    except (ValueError, json.JSONDecodeError):
        return {}


def read_offset() -> int:
    if OFFSET_STATE.exists():
        try:
            return max(0, int(OFFSET_STATE.read_text().strip()))
        except ValueError:
            pass
    return 0


def write_offset(offset: int) -> None:
    OFFSET_STATE.write_text(str(offset), encoding="utf-8")


def write_catalog(catalog: dict[str, dict], by_pub: dict[str, list[str]]) -> None:
    write_catalog_js(catalog, by_pub, CATALOG_JS)


def main() -> None:
    index_html = INDEX.read_text(encoding="utf-8")
    wg_data = extract_wg_data(index_html)
    homepage = catalog_from_wg_data(wg_data)
    catalog = load_existing_catalog()
    for path, entry in homepage.items():
        if path not in catalog:
            catalog[path] = dict(entry)
            continue
        for key, val in entry.items():
            if key in ("img", "img_og", "img_alt") and str(catalog[path].get("img", "")).startswith("assets/"):
                continue
            if val:
                catalog[path][key] = val
    print(f"Catalog: {len(catalog)} games (homepage {len(homepage)})")

    offset = read_offset()
    if offset == 0 and len(catalog) > len(homepage):
        offset = max(0, ((len(catalog) - len(homepage)) // BATCH) * BATCH)
    added = 0
    retries = 0
    while len(catalog) < TARGET:
        print(f"  API batch offset={offset} limit={BATCH} …")
        try:
            games = api_fetch(BATCH, offset)
        except RuntimeError as e:
            retries += 1
            print(f"  ⚠ {e}")
            time.sleep(min(8 + retries * 2, 20))
            if retries > 8:
                print("  Too many API errors — stopping early")
                break
            continue
        retries = 0
        if not games:
            print("  No more games from API")
            break
        for game in games:
            parsed = api_to_entry(game)
            if not parsed:
                continue
            path, entry = parsed
            if not entry.get("ifr"):
                continue
            if path in catalog:
                continue
            catalog[path] = entry
            added += 1
            if len(catalog) >= TARGET:
                break
        offset += len(games)
        write_offset(offset)
        if len(games) < BATCH:
            break
        time.sleep(SLEEP_SEC)

    by_pub = rebuild_by_publisher(catalog)
    write_catalog(catalog, by_pub)
    with_ifr = sum(1 for g in catalog.values() if g.get("ifr"))
    print(f"Wrote {CATALOG_JS}: {len(catalog)} games ({with_ifr} with iframe hash), +{added} from API")


if __name__ == "__main__":
    main()
