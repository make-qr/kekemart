#!/usr/bin/env bash
# Build MonkeyMart.one portal (HTML) — games on games.monkeymart.one CDN
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-$SRC/../monkeymart.one/portal/dist}"
LEGACY_3T="${LEGACY_3T:-$HOME/NAS/projects/personal/papasgames-3d/3t}"
NATIVE_SRC="${NATIVE_SRC:-$SRC/../monkeymart.one/source_game.monkeymart.one}"

echo "=== Source: $SRC"
echo "=== Dest:   $DEST"
echo "=== Legacy: $LEGACY_3T"

cd "$SRC"
python3 import-monkeymart-games.py --source "$NATIVE_SRC"
python3 build-seo-assets.py
python3 build-404-page.py
python3 build-wg-grids-data.py
python3 patch-game-bottom-section.py

mkdir -p "$DEST"
rsync -a --delete \
  --exclude '.fetch-catalog-offset' \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude 'hosted-games' \
  "$SRC/" "$DEST/"

# Symlink for local dev only (production uses games.monkeymart.one CDN)
if [[ ! -e "$DEST/hosted-games" ]] && [[ -d "$NATIVE_SRC/projects" ]]; then
  ln -sfn "$NATIVE_SRC/projects" "$DEST/hosted-games"
fi

cd "$DEST"
python3 migrate-legacy-from-3t.py --dest "$DEST" --legacy "$LEGACY_3T"
python3 apply-monkeymart-brand.py

echo "monkeymart.one" > "$DEST/CNAME"

echo ""
echo "Portal ready at: $DEST"
echo "  (hosted-games → games.monkeymart.one — run build-monkeymart-games-cdn.sh)"
echo "Test:  cd $DEST && python3 -m http.server 8765"
