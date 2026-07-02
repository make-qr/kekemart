#!/usr/bin/env python3
"""Apply data/game-seo-overrides.json to priority game pages."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from seo_build import patch_all_game_seo_overrides, write_robots_txt, write_sitemap_xml

    config_path = ROOT / "brand" / "monkeymart.json"
    brand = json.loads(config_path.read_text(encoding="utf-8"))
    n = patch_all_game_seo_overrides(ROOT, brand)
    write_sitemap_xml(brand)
    write_robots_txt(brand)
    print(f"Patched {n} game page(s); sitemap.xml refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
