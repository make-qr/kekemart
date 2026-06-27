"""Build MonkeyMart native game pages using the WGPlayground game shell."""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WG_SHELL = ROOT / "perfect-match-3d.html"

CAT_SLUGS = {
    "MonkeyMart Classics": "monkeymart-classics",
    "FNAF": "fnaf",
    "Moto X3M": "moto-x3m",
    "Vex": "vex",
    "Fireboy & Watergirl": "fireboy-and-watergirl",
    "Snail Bob": "snail-bob",
    "Racing": "racing",
    "Puzzle": "puzzle",
    "2 Players": "2-players",
}


def replace_block(text: str, start_marker: str, end_marker: str, new_content: str) -> str:
    i = text.find(start_marker)
    if i == -1:
        return text
    j = text.find(end_marker, i)
    if j == -1:
        return text
    return text[:i] + new_content + text[j + len(end_marker) :]


def stable_hash(slug: str) -> str:
    return hashlib.md5(f"mm-native:{slug}".encode()).hexdigest()


def _prefix(depth: int) -> str:
    return "../" if depth > 0 else ""


def asset_url(path: str, depth: int = 1) -> str:
    p = _prefix(depth)
    if not path:
        return f"{p}assets/images/site/logo-square.svg"
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if path.startswith(p) or (depth == 0 and path.startswith("assets/")):
        return path
    return p + path.lstrip("/")


def cat_catalog_href(cat_name: str, depth: int = 1) -> str:
    slug = CAT_SLUGS.get(cat_name)
    if not slug:
        slug = (
            cat_name.lower()
            .replace("&", "and")
            .replace("'", "")
            .strip()
        )
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return f"{_prefix(depth)}games-catalogue.html?cat={slug}"


def play_url_for(slug: str, depth: int = 1) -> str:
    p = _prefix(depth)
    if slug == "monkey-mart":
        return f"{p}monkey-mart.html"
    return f"{p}games/mm-{slug}.html"


def pick_breadcrumb_cat(cats: list[str]) -> str:
    for cat in cats:
        if cat != "MonkeyMart Classics":
            return cat
    return "MonkeyMart Classics"


def pick_related(games: list[dict], current: dict, limit: int = 6) -> list[dict]:
    slug = current["slug"]
    cats = set(current.get("cats") or []) - {"MonkeyMart Classics"}
    scored: list[tuple[int, str, dict]] = []
    for g in games:
        if g["slug"] == slug:
            continue
        gcats = set(g.get("cats") or [])
        score = len(cats & gcats) * 2
        if g.get("popular"):
            score += 1
        scored.append((score, g["name"].lower(), g))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [g for _, _, g in scored[:limit]]


def native_cards(games: list[dict], *, source: str = "similar", depth: int = 1) -> str:
    items = []
    for g in games:
        items.append(
            {
                "name": g["name"],
                "url": play_url_for(g["slug"], depth),
                "image": asset_url(g.get("img") or "", depth),
                "c": g.get("c") or "#16a34a",
                "by": "MonkeyMart.one",
                "preview": "",
                "source": source,
            }
        )
    return json.dumps(items, ensure_ascii=False)


def embed_iframe_code(src: str, title: str) -> str:
    return (
        f"&lt;iframe src=&quot;{html.escape(src, quote=True)}&quot;\n"
        '        width=&quot;100%&quot; height=&quot;600&quot; frameborder=&quot;0&quot;\n'
        '        allow=&quot;fullscreen; autoplay; gamepad&quot;\n'
        f'        title=&quot;{html.escape(title)}&quot;&gt;&lt;/iframe&gt;'
    )


def render_side_cards(games: list[dict], depth: int = 1) -> str:
    lines: list[str] = []
    for g in games:
        img = asset_url(g.get("img") or "", depth)
        url = play_url_for(g["slug"], depth)
        color = g.get("c") or "#16a34a"
        safe_img = img.replace("'", "%27")
        lines.append(
            f'                          <a class="side-card" href="{url}" style="--c:{color};">\n'
            f"                <span class=\"side-card-art\" style=\"background-image:url('{safe_img}'); "
            f'background-size:cover; background-position:center;"></span>\n'
            f'                <span class="side-card-meta">\n'
            f'                  <span class="nm">{html.escape(g["name"])}</span>\n'
            f'                  <span class="by">MonkeyMart.one</span>\n'
            f"                </span>\n"
            f"              </a>"
        )
    return "\n".join(lines)


def patch_related_sidebar(
    page: str, game: dict, related: list[dict], popular: list[dict], *, depth: int = 1
) -> str:
    cat = pick_breadcrumb_cat(game.get("cats") or [])
    similar_html = render_side_cards(related, depth)
    publisher_html = render_side_cards(popular, depth)

    page = re.sub(
        r'(<div class="list-card list-editorial">.*?<div class="list-items">).*?'
        r'(</div>\s*</div>\s*<div class="list-card list-social">)',
        rf"\1\n{similar_html}\n                      \2",
        page,
        count=1,
        flags=re.S,
    )
    page = re.sub(
        r'(<div class="list-card list-social">.*?<div class="list-items">).*?'
        r'(</div>\s*</div>)',
        rf"\1\n{publisher_html}\n                      \2",
        page,
        count=1,
        flags=re.S,
    )
    page = page.replace("More Casual games", f"More {cat} games")
    page = page.replace("<h4>by GAMEPUSH</h4>", "<h4>by MonkeyMart.one</h4>")
    page = page.replace("More from GAMEPUSH", "More MonkeyMart classics")
    return page


def build_native_page(
    template: str,
    game: dict,
    all_games: list[dict],
    *,
    iframe_src: str,
    depth: int = 1,
) -> str:
    slug = game["slug"]
    name = game["name"]
    pub = "MonkeyMart.one"
    game_hash = stable_hash(slug)
    p = _prefix(depth)
    local_url = play_url_for(slug, depth).lstrip("/")
    og = asset_url(game.get("img") or "assets/images/site/logo-square.svg", depth)
    desc = game.get("desc") or f"Play {name} free in your browser on MonkeyMart.one — no download."
    breadcrumb_cat = pick_breadcrumb_cat(game.get("cats") or [])
    cat_href = cat_catalog_href(breadcrumb_cat, depth)

    page = template
    page = page.replace("<html lang=\"en\">", '<html lang="en" data-native-game="1">', 1)
    page = page.replace(
        '<script src="assets/js/wg-catalog.js"></script>\n<script src="assets/js/game-bootstrap.js"></script>\n',
        "",
    )
    if depth > 0:
        page = page.replace('href="index.html"', 'href="../index.html"')
        page = page.replace('href="assets/', 'href="../assets/')
        page = page.replace('src="assets/', 'src="../assets/')
    page = re.sub(
        r'<script defer src="https://static\.cloudflareinsights\.com[^<]+</script>\s*',
        "",
        page,
    )

    replacements = [
        ("Perfect Match 3D", name),
        ("8d9b960c0aa7983cc87c3303ac28d1ff", game_hash),
        ("gamepush/perfect-match-3d", slug if slug == "monkey-mart" else f"mm/{slug}"),
        ("gamepush-perfect-match-3d", "monkey-mart" if slug == "monkey-mart" else f"mm-{slug}"),
        (
            "Find matching objects, collect triples, and clear the board in a fun D puzzle adventure.",
            desc,
        ),
        ("<h1>Perfect Match 3D</h1>", f"<h1>{html.escape(name)}</h1>"),
        ("Install Perfect Match 3D", f"Install {name}"),
        ("Embed Perfect Match 3D", f"Embed {name}"),
        ("<strong>GAMEPUSH</strong>", f"<strong>{html.escape(pub)}</strong>"),
        ("&middot; 550 games", f"&middot; {len(all_games)} classics"),
        ('data-game-cover="assets/images/games/gamepush-perfect-match-3d/og.webp"', f'data-game-cover="{og}"'),
    ]
    for old, new in replacements:
        page = page.replace(old, new)

    page = page.replace(
        '<span aria-current="page">Perfect Match 3D</span>',
        f'<span aria-current="page">{html.escape(name)}</span>',
    )
    page = page.replace('>G</span>\n            <span>by', ">M</span>\n            <span>by", 1)

    breadcrumb = f"""<div class="game-head game-head--compact">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href="{p}index.html">Home</a>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 6 6 6-6 6"/></svg>
        <a href="{p}games-catalogue.html">All games</a>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 6 6 6-6 6"/></svg>
        <a href="{cat_href}">{html.escape(breadcrumb_cat)}</a>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 6 6 6-6 6"/></svg>
        <span aria-current="page">{html.escape(name)}</span>
      </nav>
    </div>"""
    page = re.sub(
        r'<div class="game-head game-head--compact">.*?</nav>\s*</div>',
        breadcrumb,
        page,
        count=1,
        flags=re.S,
    )

    page = re.sub(
        r'<iframe id="playerIframe"[^>]*src="[^"]*"',
        f'<iframe id="playerIframe"\n                data-mm-play="{iframe_src}"\n                src="about:blank"',
        page,
        count=1,
    )
    page = re.sub(
        r'(<iframe id="playerIframe"[^>]*title=")[^"]*(")',
        lambda m, n=name: f"{m.group(1)}{html.escape(n)}{m.group(2)}",
        page,
        count=1,
    )

    related = pick_related(all_games, game)
    popular = [g for g in all_games if g.get("popular") and g["slug"] != slug][:6]
    if not popular:
        popular = related

    wg_game = f"""window.WG_GAME = {{
  hash:  '{game_hash}',
  name:  {json.dumps(name)},
  slug:  {json.dumps(slug if slug == "monkey-mart" else f"mm/{slug}")},
  url:   {json.dumps(p + local_url)},
  image: {json.dumps(og)},
  by:    {json.dumps('by ' + pub)},
  native: true
}};"""
    page = replace_block(page, "window.WG_GAME = {", "};", wg_game)
    page = replace_block(
        page,
        "window.WG_RELATED_GAMES = [",
        "];",
        f"window.WG_RELATED_GAMES = {native_cards(related, source='similar', depth=depth)};",
    )
    page = replace_block(
        page,
        "window.WG_PUBLISHER_GAMES = [",
        "];",
        f"window.WG_PUBLISHER_GAMES = {native_cards(popular, source='publisher', depth=depth)};",
    )
    page = patch_related_sidebar(page, game, related, popular, depth=depth)
    page = replace_block(
        page,
        '<pre data-embed-code="iframe">',
        "</pre>",
        f'<pre data-embed-code="iframe">{embed_iframe_code(iframe_src, name)}</pre>',
    )
    page = replace_block(
        page,
        '<pre data-embed-code="markdown">',
        "</pre>",
        f'<pre data-embed-code="markdown">[Play {html.escape(name)} on MonkeyMart.one]({p}{local_url})</pre>',
    )

    page = page.replace(
        'data-game-url="https://www.wgplayground.com/game/gamepush/perfect-match-3d"',
        f'data-game-url="{p}{local_url}"',
    )
    page = page.replace(
        'content="https://www.wgplayground.com/game/gamepush/perfect-match-3d"',
        f'content="{p}{local_url}"',
    )
    page = re.sub(
        r"<title>[^<]*</title>",
        f"<title>{html.escape(name)} — Play Free | MonkeyMart.one</title>",
        page,
        count=1,
    )
    page = re.sub(
        r'content="assets/images/games/gamepush-perfect-match-3d/og\.webp"',
        f'content="{og}"',
        page,
    )
    page = re.sub(
        r'<meta property="og:site_name" content="[^"]*"',
        '<meta property="og:site_name" content="MonkeyMart.one"',
        page,
        count=1,
    )
    page = page.replace('data-page="home"', 'data-page="game"')

    chrome_needle = f'<script src="{p}assets/vendor/wgp/public/v6/js/chrome.min.js">'
    if chrome_needle in page and "mm-categories.js" not in page:
        preload = f"""<script src="{p}assets/js/wg-catalog.js"></script>
<script src="{p}assets/js/mm-native-catalog.js"></script>
<script src="{p}assets/js/mm-categories.js"></script>
<script>
(function () {{
  window.WG_DATA = window.WG_DATA || {{}};
  if (window.MM_buildWgCategories) {{
    window.WG_DATA.categories = MM_buildWgCategories();
  }}
}})();
</script>
"""
        page = page.replace(chrome_needle, preload + chrome_needle, 1)

    sync_needle = f'<script src="{p}assets/js/monkeymart-config.js" defer>'
    sync_script = f'<script src="{p}assets/js/mm-rail-sync.js"></script>\n'
    if sync_needle in page and "mm-rail-sync.js" not in page:
        page = page.replace(sync_needle, sync_script + sync_needle, 1)

    from thumbnail_fix import patch_html_thumbnails

    page = patch_html_thumbnails(page, depth=depth)
    return page


def apply_seo_to_native_page(page: str, game: dict, brand: dict, *, depth: int = 1) -> str:
    from seo_build import native_game_description, patch_native_game_seo

    cats = game.get("cats") or []
    desc = game.get("desc") or native_game_description(game["name"], cats)
    img = asset_url(game.get("img") or "", depth)
    return patch_native_game_seo(
        page,
        name=game["name"],
        description=desc,
        slug=game["slug"],
        image=img,
        cats=cats,
        brand=brand,
        depth=depth,
    )


def load_native_games_list() -> list[dict]:
    catalog_js = ROOT / "assets/js/mm-native-catalog.js"
    if not catalog_js.exists():
        return []
    text = catalog_js.read_text(encoding="utf-8")
    data = json.loads(text.split("=", 1)[1].rstrip(";\n"))
    return [{"slug": slug, **meta} for slug, meta in data.items()]


def build_monkey_mart_page(brand: dict) -> str:
    hero = brand["heroGame"]
    template = WG_SHELL.read_text(encoding="utf-8")
    game = {
        "slug": "monkey-mart",
        "name": hero["name"],
        "img": hero.get("img", "assets/images/site/monkey-mart-logo.png"),
        "cats": ["Casual", "Simulation", "MonkeyMart Classics"],
        "c": hero.get("c", "#16a34a"),
        "popular": True,
        "desc": brand["seo"]["monkeyMart"]["description"],
    }
    all_games = load_native_games_list()
    return build_native_page(
        template,
        game,
        all_games,
        iframe_src=hero["iframe"],
        depth=0,
    )


def apply_brand_to_page(html: str, *, depth: int = 1) -> str:
    import importlib.util

    path = ROOT / "apply-monkeymart-brand.py"
    spec = importlib.util.spec_from_file_location("apply_monkeymart_brand", path)
    if not spec or not spec.loader:
        return html
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    html = mod.inject_brand_assets(html, depth=depth)
    html = mod.inject_rail_features(html, depth=depth)
    return html
