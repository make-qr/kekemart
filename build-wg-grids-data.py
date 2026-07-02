#!/usr/bin/env python3
"""Export WG_DATA.grids (trending + new) from index.html to a shared JS file."""
from __future__ import annotations

import json
from pathlib import Path

from catalog_utils import extract_json_object

ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "index.html"
OUT_JS = ROOT / "assets/js/wg-grids-data.js"


def load_grids() -> dict[str, list[dict]]:
    if not INDEX_HTML.is_file():
        return {"trending": [], "new": []}
    html = INDEX_HTML.read_text(encoding="utf-8")
    data = extract_json_object(html, "window.WG_DATA = ")
    grids = data.get("grids") or {}
    return {
        "trending": list(grids.get("trending") or []),
        "new": list(grids.get("new") or []),
    }


def write_grids_js(grids: dict[str, list[dict]], *, out: Path | None = None) -> Path:
    out = out or OUT_JS
    payload = json.dumps(grids, ensure_ascii=False, separators=(",", ":"))
    content = (
        "/* Auto-generated from index.html — run: python3 build-wg-grids-data.py */\n"
        "(function () {\n"
        f"  var grids = {payload};\n"
        "  window.__WG_GRIDS__ = grids;\n"
        "  window.WG_DATA = window.WG_DATA || {};\n"
        "  window.WG_DATA.grids = grids;\n"
        "})();\n"
    )
    out.write_text(content, encoding="utf-8")
    return out


def main() -> None:
    grids = load_grids()
    path = write_grids_js(grids)
    print(
        f"Wrote {path} — "
        f"{len(grids['trending'])} trending, {len(grids['new'])} new releases"
    )


if __name__ == "__main__":
    main()
