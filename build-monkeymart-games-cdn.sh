#!/usr/bin/env bash
# Build game CDN for games.monkeymart.one — mirrors source site layout (projects/ prefix).
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
NATIVE_SRC="${NATIVE_SRC:-$SRC/../monkeymart.one/source_game.monkeymart.one}"
GAMES_DEST="${1:-$SRC/../monkeymart.one/portal/games-cdn}"

echo "=== Games CDN build ==="
echo "=== Source: $NATIVE_SRC"
echo "=== Dest:   $GAMES_DEST"

mkdir -p "$GAMES_DEST"

# Full site mirror (index, styles, projects/) — matches live games.monkeymart.one URLs.
rsync -a --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  "$NATIVE_SRC/" "$GAMES_DEST/"

echo "games.monkeymart.one" > "$GAMES_DEST/CNAME"

if [[ -f "$SRC/ads.txt" ]]; then
  cp "$SRC/ads.txt" "$GAMES_DEST/ads.txt"
fi

cat > "$GAMES_DEST/robots.txt" <<'EOF'
User-agent: *
Allow: /

Sitemap: https://monkeymart.one/sitemap.xml
EOF

echo ""
echo "Games CDN ready: $GAMES_DEST"
echo "  Project dirs: $(find "$GAMES_DEST/projects" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)"
echo "Deploy to games.monkeymart.one GitHub Pages (custom domain)"
