#!/usr/bin/env bash
# Chạy portal MonkeyMart local — mở trình duyệt sau khi thấy "Serving HTTP"
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8765}"

if command -v ss >/dev/null 2>&1; then
  if ss -tln | grep -q ":${PORT} "; then
    echo "⚠ Port $PORT đang được dùng. Thử port khác:"
    echo "  ./start.sh 8888"
    exit 1
  fi
fi

echo "=============================================="
echo " MonkeyMart portal — local preview"
echo "=============================================="
echo ""
echo " Thư mục: $(pwd)"
echo " Port:    $PORT"
echo ""
echo " Mở trình duyệt:"
echo "   http://127.0.0.1:${PORT}/index.html"
echo "   http://127.0.0.1:${PORT}/monkey-mart.html"
echo "   http://127.0.0.1:${PORT}/games-catalogue.html"
echo ""
echo " Tổng: ~88 MonkeyMart classics (hosted) + 500 WG casual games"
echo ""
echo "⚠ Nếu trang trắng: nhấn Ctrl+Shift+R (hard refresh) để xóa cache JS cũ"
echo "=============================================="
echo ""

exec python3 -m http.server "$PORT" --bind 127.0.0.1
