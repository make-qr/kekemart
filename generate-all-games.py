#!/usr/bin/env python3
"""Generate one localized game page per catalog entry from perfect-match-3d.html template."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from catalog_utils import parse_catalog_file, slug_from_path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "perfect-match-3d.html"
CATALOG_JS = ROOT / "assets/js/wg-catalog.js"
OUT_DIR = ROOT / "games"
INDEX_MAP = ROOT / "assets/js/game-routes.js"


def local_page(path: str, *, in_games_dir: bool = False) -> str:
    slug = slug_from_path(path)
    return f"{slug}.html" if in_games_dir else f"games/{slug}.html"


def parse_catalog() -> tuple[dict, dict]:
    return parse_catalog_file(CATALOG_JS)


def game_cards(
    paths: list[str], catalog: dict, source: str, limit: int = 6, *, in_games_dir: bool = False
) -> str:
    items = []
    seen = set()
    for p in paths:
        if p in seen:
            continue
        g = catalog.get(p)
        if not g:
            continue
        seen.add(p)
        slug = slug_from_path(p)
        og = g.get("img_og") or f"assets/images/games/{slug}/og.webp"
        if in_games_dir and not og.startswith("../"):
            og = "../" + og.lstrip("/")
        if not (ROOT / og.lstrip("../")).exists():
            thumb = g.get("img") or og.replace("/og.webp", "/thumbnail.webp")
            if in_games_dir and thumb.startswith("assets/"):
                thumb = "../" + thumb
            og = thumb
        items.append(
            {
                "name": g["name"],
                "url": local_page(p, in_games_dir=in_games_dir),
                "image": og,
                "c": g.get("c") or "#8b5cf6",
                "by": g["by"],
                "preview": "",
                "source": source,
            }
        )
        if len(items) >= limit:
            break
    return json.dumps(items, ensure_ascii=False)


def embed_iframe(ifr: str) -> str:
    return (
        f'&lt;iframe src=&quot;https://play.wgplayground.com/ifr/{ifr}&quot;\n'
        '        width=&quot;100%&quot; height=&quot;600&quot; frameborder=&quot;0&quot;\n'
        '        allow=&quot;fullscreen; autoplay&quot;\n'
        '        loading=&quot;lazy&quot;&gt;&lt;/iframe&gt;'
    )


def embed_widget(ifr: str) -> str:
    return (
        '&lt;div id=&quot;wgp-widget&quot;&gt;&lt;/div&gt;\n'
        '&lt;script\n'
        '  src=&quot;https://www.wgplayground.com/public/widget.js&quot;\n'
        '  data-container=&quot;#wgp-widget&quot;\n'
        f'  data-games=&quot;{ifr}&quot;\n'
        '  data-layout=&quot;grid-1x1&quot;\n'
        '  data-caption=&quot;title-by&quot;\n'
        '  async&gt;&lt;/script&gt;'
    )


def replace_block(text: str, start_marker: str, end_marker: str, new_content: str) -> str:
    i = text.find(start_marker)
    if i == -1:
        return text
    j = text.find(end_marker, i)
    if j == -1:
        return text
    return text[:i] + new_content + text[j + len(end_marker) :]


def build_page(template: str, path: str, game: dict, catalog: dict, by_pub: dict) -> str:
    slug = slug_from_path(path)
    ifr = game["ifr"]
    name = game["name"]
    pub = game["by"]
    og = game.get("img_og") or f"assets/images/games/{slug}/og.webp"
    thumb = game.get("img") or f"assets/images/games/{slug}/thumbnail.webp"
    desc = (
        game.get("copy")
        or game.get("meta")
        or f"Play {name} free in your browser — no download required."
    )
    desc = desc.replace("\n", " ").strip()[:300]
    pub_initial = (pub[0] if pub else "G").upper()
    local_url = local_page(path)

    # Similar: same publisher first, then same category
    pub_paths = [p for p in by_pub.get(pub, []) if p != path]
    cat = (game.get("cats") or [None])[0]
    cat_paths = []
    if cat:
        for p, g in catalog.items():
            if p != path and cat in (g.get("cats") or []):
                cat_paths.append(p)
    related_paths = pub_paths + [p for p in cat_paths if p not in pub_paths]

    related_json = game_cards(related_paths, catalog, "similar", in_games_dir=True)
    publisher_json = game_cards(pub_paths, catalog, "publisher", in_games_dir=True)

    page = template
  # Drop dynamic bootstrap — each page is static
    page = page.replace(
        '<script src="assets/js/wg-catalog.js"></script>\n<script src="assets/js/game-bootstrap.js"></script>\n',
        "",
    )

    # Path prefix: games/*.html lives one level deep
    page = page.replace('href="index.html"', 'href="../index.html"')
    page = page.replace('href="assets/', 'href="../assets/')
    page = page.replace('src="assets/', 'src="../assets/')

    replacements = [
        ("Perfect Match 3D", name),
        ("8d9b960c0aa7983cc87c3303ac28d1ff", ifr),
        ("gamepush/perfect-match-3d", path),
        ("gamepush-perfect-match-3d", slug),
        (
            "Find matching objects, collect triples, and clear the board in a fun D puzzle adventure.",
            desc,
        ),
        ("<h1>Perfect Match 3D</h1>", f"<h1>{html.escape(name)}</h1>"),
        ("Install Perfect Match 3D", f"Install {name}"),
        ("Embed Perfect Match 3D", f"Embed {name}"),
    ]
    for old, new in replacements:
        page = page.replace(old, new)

    page = page.replace(
        '<span aria-current="page">Perfect Match 3D</span>',
        f'<span aria-current="page">{html.escape(name)}</span>',
    )
    page = page.replace("<strong>GAMEPUSH</strong>", f"<strong>{html.escape(pub)}</strong>")
    page = page.replace('>G</span>\n            <span>by', f'>{pub_initial}</span>\n            <span>by', 1)
    page = page.replace(
        'data-game-url="https://www.wgplayground.com/game/gamepush/perfect-match-3d"',
        f'data-game-url="../{local_url}"',
    )
    page = page.replace(
        'content="https://www.wgplayground.com/game/gamepush/perfect-match-3d"',
        f'content="../{local_url}"',
    )

    page = re.sub(
        r'<iframe id="playerIframe"[^>]*src="[^"]*"',
        f'<iframe id="playerIframe"\n                src="https://play.wgplayground.com/ifr/{ifr}"',
        page,
        count=1,
    )

    wg_game = f"""window.WG_GAME = {{
  hash:  '{ifr}',
  name:  {json.dumps(name)},
  slug:  {json.dumps(path)},
  url:   {json.dumps('../' + local_url)},
  image: {json.dumps('../' + og)},
  by:    {json.dumps('by ' + pub)}
}};"""
    page = replace_block(page, "window.WG_GAME = {", "};", wg_game)

    page = replace_block(
        page,
        "window.WG_RELATED_GAMES = [",
        "];",
        f"window.WG_RELATED_GAMES = {related_json};",
    )
    page = replace_block(
        page,
        "window.WG_PUBLISHER_GAMES = [",
        "];",
        f"window.WG_PUBLISHER_GAMES = {publisher_json};",
    )

    page = replace_block(
        page,
        '<pre data-embed-code="iframe">',
        "</pre>",
        f'<pre data-embed-code="iframe">{embed_iframe(ifr)}</pre>',
    )
    page = replace_block(
        page,
        '<pre data-embed-code="widget">',
        "</pre>",
        f'<pre data-embed-code="widget">{embed_widget(ifr)}</pre>',
    )
    page = replace_block(
        page,
        '<pre data-embed-code="markdown">',
        "</pre>",
        f'<pre data-embed-code="markdown">[Play {html.escape(name)} on MonkeyMart](../{local_url})</pre>',
    )

    i = page.find("<title>")
    j = page.find("</title>", i)
    if i != -1 and j != -1:
        page = page[: i + len("<title>")] + f"{html.escape(name)} — MonkeyMart.one" + page[j:]

    from thumbnail_fix import patch_html_thumbnails

    page = patch_html_thumbnails(page, depth=1)
    return page


def write_routes_map(catalog: dict) -> None:
    routes = {g["url"]: local_page(path) for path, g in catalog.items()}
    INDEX_MAP.write_text(
        "window.WGP_GAME_ROUTES = " + json.dumps(routes, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    if not TEMPLATE.exists():
        raise SystemExit(f"Missing template {TEMPLATE}")
    catalog, by_pub = parse_catalog()
    template = TEMPLATE.read_text(encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for path, game in sorted(catalog.items()):
        if not game.get("ifr"):
            print(f"  skip (no ifr): {path}")
            continue
        out = OUT_DIR / f"{slug_from_path(path)}.html"
        out.write_text(build_page(template, path, game, catalog, by_pub), encoding="utf-8")
        count += 1

    write_routes_map(catalog)
    print(f"Generated {count} game pages in {OUT_DIR}/")
    print(f"Routes map: {INDEX_MAP}")


if __name__ == "__main__":
    main()
