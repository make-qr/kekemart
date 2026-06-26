#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== 1/4 Mirror CSS + JS shell ==="
python3 mirror-assets.py

echo ""
echo "=== 2/6 Build catalog + game.html ==="
python3 build-game-page.py

echo ""
echo "=== 3/6 Fetch API catalog (target ~500 games) ==="
python3 fetch-catalog.py

echo ""
echo "=== 4/6 SEO images (slug paths, og, webp, alt) ==="
python3 seo-images.py

echo ""
echo "=== 5/6 Localize HTML ==="
python3 localize-html.py index.html perfect-match-3d.html game.html 2>/dev/null || \
  python3 localize-html.py index.html perfect-match-3d.html

echo ""
echo "=== 6/7 Generate all game pages ==="
python3 generate-all-games.py

echo ""
echo "=== 7/7 Build catalogue browse page ==="
python3 build-catalogue-page.py

echo ""
echo "=== 8/8 MonkeyMart branding (optional) ==="
python3 apply-monkeymart-brand.py 2>/dev/null || true

echo ""
echo "Done."
echo "  Home:       index.html"
echo "  Monkey Mart: monkey-mart.html"
echo "  Catalogue:  games-catalogue.html"
echo "  Games:      games/<publisher>-<slug>.html"
