# WGPlayground clone — self-hosted shell

Site chrome (CSS, JS, icons, thumbnails) chạy trên **host của anh**.  
Game chạy qua **iframe embed** (giống nút Embed trên WG):

```html
<iframe src="https://play.wgplayground.com/ifr/8d9b960c0aa7983cc87c3303ac28d1ff"
        width="100%" height="600" frameborder="0"
        allow="fullscreen; autoplay" loading="lazy"></iframe>
```

## Setup (1 lần / khi cập nhật HTML gốc)

```bash
cd he-thong-du-an/01_Game/wgplayground-clone
chmod +x setup-local.sh mirror-assets.py localize-html.py
./setup-local.sh
```

| Script | Việc |
|--------|------|
| `mirror-assets.py` | Tải CSS/JS/icon + ảnh game → `assets/vendor/wgp/` |
| `localize-html.py` | Đổi URL trong HTML sang local, bỏ tracker/ads |
| `generate-all-games.py` | Sinh **76 trang game** trong `games/` từ template `perfect-match-3d.html` |
| `setup-local.sh` | Chạy cả pipeline |

## Cấu trúc

```
games/                              # 76 trang game (iframe embed)
  gamepush-perfect-match-3d.html
  freezenova-stunt-cars-pro.html
  ...
assets/js/game-routes.js            # Map URL gốc → trang local
assets/vendor/wgp/public/v6/css|js/
assets/images/games/<slug>/         # thumbnail.webp + og.webp
perfect-match-3d.html               # Template gốc (reference)
game.html                           # Fallback generic (?ifr=)
index.html                          # Trang chủ catalog
```

## Ảnh SEO (chuẩn)

```
assets/images/games/gamepush-perfect-match-3d/
  thumbnail.webp   # 480×360 — card catalog
  og.webp          # 1280×720 — og:image / twitter
  source.jpg       # bản gốc (không deploy cũng được)

assets/images/site/
  favicon.ico, logo.svg, og-default.png

assets/images/image-map.json   # hash → path + alt
assets/images/image-map.js     # load trong HTML
```

- **Tên file:** slug game (`publisher-game-name`), không dùng hash WG
- **Alt:** `"Perfect Match 3D — free online puzzles game"`
- **Format:** WebP (fallback JPG nếu không có Pillow)

Chạy `python3 seo-images.py` sau `build-game-page.py`.


Upload **toàn bộ thư mục** lên static host (nginx, GitHub Pages, NAS…).

```nginx
# ví dụ nginx
root /var/www/games;
index index.html;
try_files $uri $uri/ =404;
```

## Lưu ý

- **Iframe game** vẫn từ `play.wgplayground.com` — đây là runtime GamePush; mirror full game cần license từ publisher.
- Login Google / backend WG (favourites, streak…) **không hoạt động** offline — đã ẩn trong `local.css`.
- Ảnh catalog: mirror ~80 cover đầu; chạy lại `mirror-assets.py` nếu thiếu thumb.
- Font: dùng Google Fonts Inter (nhẹ hơn mirror 30 file woff2).

## Chạy local

```bash
cd he-thong-du-an/01_Game/wgplayground-clone
python3 -m http.server 8765
# Trang chủ:  http://localhost:8765/index.html
# Game:       http://localhost:8765/games/gamepush-perfect-match-3d.html
```

Click bất kỳ game nào trên trang chủ → mở `games/<publisher>-<slug>.html` với iframe embed.
