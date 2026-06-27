#!/usr/bin/env python3
"""Generate SEO images (OG 1200×630, apple-touch-icon) for MonkeyMart.one."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "assets/images/site"
BRAND = ROOT / "brand/monkeymart.json"

W, H = 1280, 720  # OG standard; displays well as 1200×630 crop


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    t = ImageColor_to_rgb(top)
    b = ImageColor_to_rgb(bottom)
    for y in range(size[1]):
        r = t[0] + (b[0] - t[0]) * y // size[1]
        g = t[1] + (b[1] - t[1]) * y // size[1]
        bl = t[2] + (b[2] - t[2]) * y // size[1]
        draw.line([(0, y), (size[0], y)], fill=(r, g, bl))
    return img


def ImageColor_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def load_logo(max_side: int = 280) -> Image.Image:
    logo_path = SITE / "monkey-mart-logo.png"
    if not logo_path.exists():
        for alt in (SITE / "logo-square.svg", SITE / "og-default.png"):
            if alt.exists() and alt.suffix != ".svg":
                logo_path = alt
                break
    if not logo_path.exists():
        im = Image.new("RGBA", (max_side, max_side), (255, 255, 255, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((8, 8, max_side - 8, max_side - 8), fill="#16a34a")
        d.text((max_side // 2 - 20, max_side // 2 - 20), "MM", fill="white", font=_font(48, True))
        return im
    im = Image.open(logo_path).convert("RGBA")
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return im


def draw_card(
    title: str,
    subtitle: str,
    badge: str,
    out: Path,
    *,
    accent: str = "#16a34a",
    accent_deep: str = "#14532d",
) -> None:
    base = _gradient((W, H), accent, accent_deep)
    draw = ImageDraw.Draw(base)
    logo = load_logo(300)
    lx, ly = 80, (H - logo.height) // 2
    if logo.mode == "RGBA":
        base.paste(logo, (lx, ly), logo)
    else:
        base.paste(logo, (lx, ly))

  # badge pill
    badge_font = _font(22, True)
    bx, by = 80, 56
    tw = draw.textlength(badge, font=badge_font)
    draw.rounded_rectangle((bx, by, bx + tw + 36, by + 40), radius=20, fill=(255, 255, 255, 40))
    draw.text((bx + 18, by + 8), badge, fill="white", font=badge_font)

    tx = lx + logo.width + 56
    draw.text((tx, H // 2 - 90), title, fill="white", font=_font(64, True))
    draw.text((tx, H // 2 - 10), subtitle, fill=(230, 255, 230), font=_font(30))
    draw.text((tx, H - 72), "monkeymart.one", fill=(200, 240, 200), font=_font(26, True))

    out.parent.mkdir(parents=True, exist_ok=True)
    base.save(out.with_suffix(".webp"), "WEBP", quality=88, method=6)
    base.save(out.with_suffix(".jpg"), "JPEG", quality=90, optimize=True)
    print(f"  ✓ {out.name}")


def apple_touch_icon(out: Path) -> None:
    logo = load_logo(160)
    im = Image.new("RGB", (180, 180), "#16a34a")
    ox = (180 - logo.width) // 2
    oy = (180 - logo.height) // 2
    if logo.mode == "RGBA":
        im.paste(logo, (ox, oy), logo)
    else:
        im.paste(logo, (ox, oy))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "PNG")
    print(f"  ✓ {out.name}")


def game_fallback_icon(out: Path) -> None:
    im = _gradient((480, 360), "#16a34a", "#14532d")
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle((196, 118, 284, 242), radius=18, outline=(255, 255, 255), width=4)
    draw.polygon([(210, 200), (210, 170), (255, 185), (255, 215)], fill=(255, 255, 255))
    draw.text((168, 248), "GAME", fill=(230, 255, 230), font=_font(28, True))
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "PNG")
    print(f"  ✓ {out.name}")


def ensure_logo_from_source() -> None:
    dest = SITE / "monkey-mart-logo.png"
    if dest.exists():
        return
    src = ROOT.parent / "monkeymart.one/source_game.monkeymart.one/games-site-logo.png"
    if src.exists():
        import shutil

        shutil.copy2(src, dest)
        print(f"  ✓ copied logo → {dest.name}")


def main() -> None:
    ensure_logo_from_source()
    brand = json.loads(BRAND.read_text(encoding="utf-8"))
    accent = brand.get("accent", "#16a34a")
    deep = brand.get("accentDeep", "#14532d")

    print("=== SEO images ===")
    draw_card(
        "Monkey Mart",
        "Play free online — no download",
        "PLAY NOW",
        SITE / "og-monkey-mart",
        accent=accent,
        accent_deep=deep,
    )
    draw_card(
        "MonkeyMart.one",
        "500+ free browser games",
        "FREE TO PLAY",
        SITE / "og-home",
        accent=accent,
        accent_deep=deep,
    )
    apple_touch_icon(SITE / "apple-touch-icon.png")
    game_fallback_icon(SITE / "game-fallback.png")
    print("Done — og-home.webp, og-monkey-mart.webp, apple-touch-icon.png, game-fallback.png")


if __name__ == "__main__":
    main()
