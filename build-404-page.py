#!/usr/bin/env python3
"""Build 404.html with Trending + New releases from index.html WG_DATA."""
from __future__ import annotations

import json
from pathlib import Path

from catalog_utils import extract_json_object

ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "index.html"
TEMPLATE = ROOT / "templates/page-404.html"
OUT_HTML = ROOT / "404.html"
MAX_PER_GRID = 8


def _dedupe(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        url = (item.get("url") or "").rstrip("/")
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(item)
    return out


def load_home_grids() -> dict[str, list[dict]]:
    if not INDEX_HTML.is_file():
        return {"trending": [], "new": []}
    html = INDEX_HTML.read_text(encoding="utf-8")
    data = extract_json_object(html, "window.WG_DATA = ")
    grids = data.get("grids") or {}
    trending = _dedupe(list(grids.get("trending") or []))[:MAX_PER_GRID]
    new = _dedupe(list(grids.get("new") or []))[:MAX_PER_GRID]
    return {"trending": trending, "new": new}


def build_404_page(*, root: Path | None = None) -> Path:
    root = root or ROOT
    template_path = root / "templates/page-404.html"
    index_path = root / "index.html"
    out_path = root / "404.html"

    if not template_path.is_file():
        raise FileNotFoundError(template_path)

    if index_path.is_file():
        html_src = index_path.read_text(encoding="utf-8")
        data = extract_json_object(html_src, "window.WG_DATA = ")
        grids = data.get("grids") or {}
        payload = {
            "trending": _dedupe(list(grids.get("trending") or []))[:MAX_PER_GRID],
            "new": _dedupe(list(grids.get("new") or []))[:MAX_PER_GRID],
        }
    else:
        payload = {"trending": [], "new": []}

    blob = "window.WG_404_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";"
    shell = template_path.read_text(encoding="utf-8")
    if "__WG_404_DATA__" not in shell:
        raise ValueError("page-404 template missing __WG_404_DATA__ placeholder")
    out = shell.replace("__WG_404_DATA__", blob)
    out_path.write_text(out, encoding="utf-8")
    return out_path


def main() -> None:
    path = build_404_page()
    grids = load_home_grids()
    print(
        f"Wrote {path} — "
        f"{len(grids['trending'])} trending, {len(grids['new'])} new releases"
    )


if __name__ == "__main__":
    main()
