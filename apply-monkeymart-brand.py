#!/usr/bin/env python3
"""Apply MonkeyMart.one branding to WGPlayground clone (pre-deploy polish)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BRAND = ROOT / "brand/monkeymart.json"
GAMES_DIR = ROOT / "games"
RAIL_MODALS = ROOT / "templates/mm-rail-modals.html"

THEME_CSS = '<link rel="stylesheet" href="{prefix}assets/css/monkeymart-theme.css" />\n'
BRAND_JS = (
    '<script src="{prefix}assets/js/mm-diagnostics.js"></script>\n'
    '<script src="{prefix}assets/js/monkeymart-config.js" defer></script>\n'
    '<script src="{prefix}assets/js/mm-sidebar.js" defer></script>\n'
    '<script src="{prefix}assets/js/monkeymart-brand.js" defer></script>\n'
)

CATEGORY_PRELOAD = """
<script src="{prefix}assets/js/wg-catalog.js"></script>
<script src="{prefix}assets/js/mm-native-catalog.js"></script>
<script src="{prefix}assets/js/mm-categories.js"></script>
<script>
(function () {{
  window.WG_DATA = window.WG_DATA || {{}};
  if (window.MM_buildWgCategories) {{
    window.WG_DATA.categories = MM_buildWgCategories();
  }}
}})();
</script>
"""

HERO_PATCH = """
<script>
(function () {
  var hero = {
    name: 'Monkey Mart',
    by: 'MonkeyMart.one',
    tag: 'PLAY NOW',
    meta: 'Casual · Simulation · Idle',
    copy: 'Run your own monkey supermarket! Harvest bananas, stock shelves, serve customers, and expand your store.',
    bg: 'assets/images/site/monkey-mart-logo.png',
    img: 'assets/images/site/monkey-mart-logo.png',
    url: 'monkey-mart.html',
    c1: '#16a34a',
    c2: '#14532d'
  };
  if (!window.WG_DATA || !WG_DATA.hero) return;
  var exists = WG_DATA.hero.some(function (s) {
    return (s.name || '').toLowerCase() === 'monkey mart';
  });
  if (!exists) WG_DATA.hero.unshift(hero);
})();
</script>
"""


def strip_head_brand_js(html: str) -> str:
    for name in (
        "mm-diagnostics.js",
        "monkeymart-config.js",
        "monkeymart-brand.js",
        "mm-native-catalog.js",
        "mm-sidebar.js",
        "mm-home-classics.js",
    ):
        html = re.sub(
            rf'<script src="[^"]*{re.escape(name)}"[^>]*></script>\s*',
            "",
            html,
        )
    return html


def inject_brand_assets(html: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    html = strip_head_brand_js(html)
    if "monkeymart-theme.css" not in html:
        css_line = THEME_CSS.format(prefix=prefix)
        if f'href="{prefix}assets/css/local.css"' in html:
            html = html.replace(
                f'<link rel="stylesheet" href="{prefix}assets/css/local.css" />',
                f'<link rel="stylesheet" href="{prefix}assets/css/local.css" />\n{css_line.rstrip()}',
                1,
            )
        elif '<link rel="stylesheet" href="assets/vendor/wgp/public/v6/css/style.min.css"' in html:
            # Never inject theme before WG CSS — overrides would be lost when style.min loads.
            pass
    if "monkeymart-brand.js" not in html:
        html = html.replace("</body>", BRAND_JS.format(prefix=prefix) + "\n</body>", 1)
    return html


def inject_hero_patch(html: str) -> str:
    if "monkey-mart.html" in html and "WG_DATA.hero.unshift" in html:
        return html
    return html.replace(
        "</script>\n<script src=\"assets/images/image-map.js\">",
        "</script>\n" + HERO_PATCH.strip() + "\n<script src=\"assets/images/image-map.js\">",
        1,
    )


def load_brand() -> dict:
    return json.loads(BRAND.read_text(encoding="utf-8"))


def patch_meta(html: str, brand: dict) -> str:
    title = brand["title"]
    desc = brand["description"]
    html = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", html, count=1)
    html = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{desc}"',
        html,
        count=1,
    )
    for prop in ("og:title", "og:description", "twitter:title", "twitter:description"):
        if prop.endswith("title"):
            val = title
        else:
            val = desc
        html = re.sub(
            rf'(<meta (?:property|name)="{re.escape(prop)}"[^>]*content=")[^"]*(")',
            rf"\1{val}\2",
            html,
            count=1,
        )
    html = re.sub(
        r'(<meta property="og:site_name" content=")[^"]*(")',
        rf'\1{brand["siteName"]}\2',
        html,
        count=1,
    )
    html = re.sub(
        r'content="assets/images/site/og-default.png"',
        'content="assets/images/site/monkey-mart-logo.png"',
        html,
    )
    html = html.replace("WGPlayground", brand["brandShort"])
    html = html.replace("WGPlayGround", brand["brandShort"])
    html = re.sub(
        r"var BASE_URL = 'https://www\.wgplayground\.com/';",
        "var BASE_URL = '/';",
        html,
        count=1,
    )
    html = re.sub(
        r'(<meta property="og:url" content=")https://www\.wgplayground\.com(")',
        rf'\1{brand["domain"]}\2',
        html,
        count=1,
    )
    return html


def patch_search_placeholder(html: str, brand: dict) -> str:
    return html.replace(
        'placeholder="Search 2,800+ games…"',
        f'placeholder="{brand["searchPlaceholder"]}"',
    )


def inject_native_catalog(html: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    script = f'<script src="{prefix}assets/js/mm-native-catalog.js"></script>\n'
    if "mm-native-catalog.js" in html:
        return html
    needles = [
        f'<script src="{prefix}assets/js/mm-categories.js">',
        f'<script src="{prefix}assets/js/mm-sidebar.js"',
        f'<script src="{prefix}assets/js/mm-rail-sync.js">',
        f'<script src="{prefix}assets/js/monkeymart-config.js"',
    ]
    for needle in needles:
        if needle in html:
            return html.replace(needle, script + needle, 1)
    return html


def inject_rail_modals(html: str) -> str:
    if 'id="favouritesModal"' in html:
        return html
    if not RAIL_MODALS.exists():
        return html
    block = RAIL_MODALS.read_text(encoding="utf-8")
    markers = [
        '<script src="assets/vendor/wgp/public/v6/js/chrome.min.js">',
        '<script src="../assets/vendor/wgp/public/v6/js/chrome.min.js">',
        '<script src="assets/images/image-map.js">',
        '<script src="../assets/images/image-map.js">',
    ]
    for needle in markers:
        if needle in html:
            return html.replace(needle, block + "\n" + needle, 1)
    return html.replace("</body>", block + "\n</body>", 1)


def inject_rail_scripts(html: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    if "mm-rail-sync.js" in html and "modals.min.js" in html:
        return html

    bundle = ""
    if f'{prefix}assets/vendor/wgp/public/v6/js/modals.min.js' not in html:
        bundle = (
            f'<script src="{prefix}assets/vendor/wgp/public/v6/js/modals.min.js"></script>\n'
            f'<script src="{prefix}assets/vendor/wgp/public/v6/js/surprise.min.js"></script>\n'
            f'<script src="{prefix}assets/vendor/wgp/public/v6/js/foryou.min.js"></script>\n'
            f'<script src="{prefix}assets/vendor/wgp/public/v6/js/personal-best.min.js"></script>\n'
        )

    sync = f'<script src="{prefix}assets/js/mm-rail-sync.js"></script>\n'
    brand_needle = f'<script src="{prefix}assets/js/monkeymart-config.js" defer>'
    if brand_needle in html:
        if bundle:
            html = html.replace(brand_needle, bundle + sync + brand_needle, 1)
        elif "mm-rail-sync.js" not in html:
            html = html.replace(brand_needle, sync + brand_needle, 1)
        return html

    chrome = f'<script src="{prefix}assets/vendor/wgp/public/v6/js/chrome.min.js">'
    if chrome in html and bundle:
        html = html.replace(chrome, chrome + "\n" + bundle, 1)
    if sync not in html:
        html = html.replace("</body>", sync + "</body>", 1)
    return html


def inject_rail_features(html: str, *, depth: int = 0) -> str:
    html = inject_native_catalog(html, depth=depth)
    html = inject_rail_modals(html)
    html = inject_rail_scripts(html, depth=depth)
    html = inject_game_bottom_scripts(html, depth=depth)
    return html


def inject_game_bottom_scripts(html: str, *, depth: int = 0) -> str:
    """Shared trending/new grids + favourites-based recommendations on game pages."""
    if 'id="mmGameBottom"' not in html and 'data-page="game"' not in html:
        return html
    prefix = "../" * depth
    grids_tag = f'<script src="{prefix}assets/js/wg-grids-data.js"></script>\n'
    bottom_tag = f'<script src="{prefix}assets/js/mm-game-bottom.js" defer></script>\n'
    catalog_tag = f'<script src="{prefix}assets/js/wg-catalog.js"></script>\n'

    patch_needle = f'<script src="{prefix}assets/js/local-patch.js">'
    if patch_needle in html and "wg-grids-data.js" not in html:
        html = html.replace(patch_needle, grids_tag + patch_needle, 1)

    chrome = f'<script src="{prefix}assets/vendor/wgp/public/v6/js/chrome.min.js">'
    if chrome in html and "wg-catalog.js" not in html:
        html = html.replace(chrome, catalog_tag + chrome, 1)

    brand_needle = f'<script src="{prefix}assets/js/monkeymart-config.js" defer>'
    if brand_needle in html and "mm-game-bottom.js" not in html:
        html = html.replace(brand_needle, bottom_tag + brand_needle, 1)
    elif "mm-game-bottom.js" not in html:
        html = html.replace("</body>", bottom_tag + "</body>", 1)
    return html


def inject_category_preload(html: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    if "mm-categories.js" in html:
        return html
    needle = f'<script src="{prefix}assets/vendor/wgp/public/v6/js/chrome.min.js">'
    if needle not in html:
        return html
    inline = (
        "<script>\n(function () {\n"
        "  window.WG_DATA = window.WG_DATA || {};\n"
        "  if (window.MM_buildWgCategories) {\n"
        "    window.WG_DATA.categories = MM_buildWgCategories();\n"
        "  }\n})();\n</script>\n"
    )
    wg = f'<script src="{prefix}assets/js/wg-catalog.js"></script>'
    native = f'<script src="{prefix}assets/js/mm-native-catalog.js"></script>'
    cats = f'<script src="{prefix}assets/js/mm-categories.js"></script>'
    parts = []
    if wg not in html:
        parts.append(wg)
    if native not in html:
        parts.append(native)
    parts.extend([cats, inline])
    block = "\n".join(parts)
    return html.replace(needle, block + needle, 1)


def inject_mm_images(html: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    tag = f'<script src="{prefix}assets/js/mm-images.js"></script>\n'
    if "mm-images.js" in html:
        return html
    for needle in (
        f'<script src="{prefix}assets/js/browse-catalog.js">',
        f'<script src="{prefix}assets/js/mm-home-classics.js"',
        f'<script src="{prefix}assets/js/local-patch.js">',
    ):
        if needle in html:
            return html.replace(needle, tag + needle, 1)
    return html


def inject_mm_native_player(html: str, *, depth: int = 0) -> str:
    if 'data-native-game="1"' not in html and "data-mm-play=" not in html:
        return html
    prefix = "../" * depth
    tag = f'<script src="{prefix}assets/js/mm-native-player.js" defer></script>\n'
    if "mm-native-player.js" in html:
        return html
    needle = f'<script src="{prefix}assets/vendor/wgp/public/v6/js/game.min.js">'
    if needle in html:
        return html.replace(needle, tag + needle, 1)
    needle = f'<script src="{prefix}assets/js/local-patch.js">'
    if needle in html:
        return html.replace(needle, needle + "\n" + tag, 1)
    return html


def inject_catalog_scripts(html: str, *, depth: int = 0) -> str:
    prefix = "../" * depth
    if "mm-native-catalog.js" in html and "browse-catalog.js" in html:
        html = inject_category_preload(html, depth=depth)
        return inject_mm_images(html, depth=depth)
    if f'<script src="{prefix}assets/js/browse-catalog.js">' in html:
        html = html.replace(
            f'<script src="{prefix}assets/js/browse-catalog.js">',
            f'<script src="{prefix}assets/js/mm-native-catalog.js"></script>\n'
            f'<script src="{prefix}assets/js/browse-catalog.js">',
            1,
        )
    html = inject_category_preload(html, depth=depth)
    return inject_mm_images(html, depth=depth)


def patch_search_form(html: str) -> str:
    return re.sub(
        r'<form class="search" action="https://www\.wgplayground\.com/search" method="get"',
        '<form class="search" action="games-catalogue.html" method="get"',
        html,
        count=1,
    )


def patch_top_nav(html: str, *, page: str = "index") -> str:
    """Restore WG-style top nav: single Games pill (Home stays in sidebar only)."""
    depth = 1 if page == "games" else 0
    prefix = "../" * depth
    cat_href = f"{prefix}games-catalogue.html"

    html = html.replace(
        'href="https://www.wgplayground.com/games-catalogue" class="active">Games',
        f'href="{cat_href}" class="active">Games',
    )
    html = html.replace(
        'href="https://www.wgplayground.com/games-catalogue">Games',
        f'href="{cat_href}">Games',
    )

    # Undo earlier Home + All games double nav
    html = re.sub(
        r'<nav class="top-nav" aria-label="Primary">\s*'
        r'<a href="(?:\.\./)?index\.html" class="active">Home</a>\s*'
        r'<a href="(?:\.\./)?games-catalogue\.html">All games</a>\s*</nav>',
        f'<nav class="top-nav" aria-label="Primary">\n'
        f'    <a href="{cat_href}">Games</a>\n'
        f"  </nav>",
        html,
        count=1,
    )
    html = re.sub(
        r'<nav class="top-nav" aria-label="Primary">\s*'
        r'<a href="(?:\.\./)?index\.html">Home</a>\s*'
        r'<a href="(?:\.\./)?games-catalogue\.html" class="active">All games</a>\s*</nav>',
        f'<nav class="top-nav" aria-label="Primary">\n'
        f'    <a href="{cat_href}">Games</a>\n'
        f"  </nav>",
        html,
        count=1,
    )

    if page == "games-catalogue":
        html = re.sub(
            r'<nav class="top-nav" aria-label="Primary">[\s\S]*?</nav>',
            '<nav class="top-nav" aria-label="Primary">\n'
            '    <a href="games-catalogue.html" class="active">Games</a>\n'
            "  </nav>",
            html,
            count=1,
        )
    elif page in ("index", "game", "monkey-mart", "a"):
        html = re.sub(
            r'<nav class="top-nav" aria-label="Primary">[\s\S]*?</nav>',
            '<nav class="top-nav" aria-label="Primary">\n'
            '    <a href="games-catalogue.html">Games</a>\n'
            "  </nav>",
            html,
            count=1,
        )
    elif page == "games":
        html = re.sub(
            r'<nav class="top-nav" aria-label="Primary">[\s\S]*?</nav>',
            '<nav class="top-nav" aria-label="Primary">\n'
            f'    <a href="{cat_href}">Games</a>\n'
            "  </nav>",
            html,
            count=1,
        )

    return html


def patch_catalogue_links(html: str) -> str:
    html = html.replace('href="https://www.wgplayground.com/games-catalogue"', 'href="games-catalogue.html"')
    html = html.replace('href="https://www.wgplayground.com/games-catalogue/sort-2/"', 'href="games-catalogue.html?sort=2"')
    html = html.replace('href="https://www.wgplayground.com/games-catalogue/sort-1/"', 'href="games-catalogue.html?sort=1"')
    html = html.replace('href="https://www.wgplayground.com/games-catalogue/sort-3/"', 'href="games-catalogue.html?sort=3"')
    html = html.replace('href="https://www.wgplayground.com/selection/exclusive"', 'href="games-catalogue.html"')
    html = html.replace('href="https://www.wgplayground.com/selection/ourpicks"', 'href="games-catalogue.html"')
    return html


def reorder_home_sections(html: str) -> str:
    """Home: MonkeyMart classics after chips; WG blocks trending before new releases."""
    classics_block = """    <section id="mmClassicsSection" class="mm-home-classics" aria-label="MonkeyMart classics">
      <div class="section-head">
        <h2><span class="dot" style="background:#16a34a"></span>MonkeyMart classics</h2>
        <a class="more" href="games-catalogue.html?cat=monkeymart-classics">See all →</a>
      </div>
      <div class="grid grid-dense mm-classics-grid" id="mmClassicsGrid"></div>
    </section>

    <div class="section-head">
      <h2><span class="dot hot"></span>Trending now</h2>
      <a class="more" href="games-catalogue.html?sort=1">See all →</a>
    </div>

    <div class="grid grid-dense" id="grid-trending"></div>

    <div class="section-head">
      <h2><span class="dot new"></span>New releases</h2>
      <a class="more" href="games-catalogue.html?sort=2">See all →</a>
    </div>

    <div class="grid grid-dense" id="grid-new"></div>"""

    if classics_block in html:
        return html

    # Legacy WG order: new releases before trending (classics injected by JS).
    legacy = """    <div class="section-head">
      <h2><span class="dot new"></span>New releases</h2>
      <a class="more" href="games-catalogue.html?sort=2">See all →</a>
    </div>

    <div class="grid" id="grid-new"></div>

    
    <div class="section-head">
      <h2><span class="dot hot"></span>Trending now</h2>
      <a class="more" href="games-catalogue.html?sort=1">See all →</a>
    </div>

    <div class="grid grid-dense" id="grid-trending"></div>"""

    if legacy in html:
        chips_end = '<div class="chips" id="chipScroll" role="tablist"></div>'
        if chips_end in html:
            return html.replace(
                chips_end,
                chips_end + "\n\n" + classics_block,
                1,
            ).replace(legacy, "", 1)

    return html


def write_monkey_mart_page(brand: dict) -> None:
    from native_game_page import apply_brand_to_page, build_monkey_mart_page
    from seo_build import patch_monkey_mart_page

    out = ROOT / "monkey-mart.html"
    html = build_monkey_mart_page(brand)
    html = apply_brand_to_page(html, depth=0)
    html = patch_monkey_mart_page(html, brand, depth=0)
    from thumbnail_fix import patch_html_thumbnails

    html = patch_html_thumbnails(html, depth=0)
    html = html.replace('content="@wgplayground"', 'content="@monkeymartone"')
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out}")


def main() -> None:
    from seo_build import collect_sitemap_urls, patch_catalog_page, patch_home_page, write_robots_txt, write_sitemap_xml

    brand = load_brand()
    import subprocess
    import sys

    subprocess.run([sys.executable, str(ROOT / "build-404-page.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "build-wg-grids-data.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "patch-game-bottom-section.py")], cwd=ROOT, check=True)
    pages = [ROOT / "index.html", ROOT / "games-catalogue.html", ROOT / "404.html"]
    for path in pages:
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        html = inject_brand_assets(html, depth=0)
        html = patch_meta(html, brand)
        html = patch_search_placeholder(html, brand)
        html = patch_search_form(html)
        html = patch_catalogue_links(html)
        html = patch_top_nav(html, page=path.stem)
        html = html.replace('content="@wgplayground"', 'content="@monkeymartone"')
        if path.name == "index.html":
            html = inject_hero_patch(html)
            html = reorder_home_sections(html)
            if "mm-home-classics.js" not in html:
                html = html.replace(
                    '<script src="assets/js/monkeymart-brand.js" defer></script>',
                    '<script src="assets/js/mm-home-classics.js" defer></script>\n'
                    '<script src="assets/js/monkeymart-brand.js" defer></script>',
                    1,
                )
            html = inject_category_preload(html, depth=0)
            html = inject_mm_images(html, depth=0)
            html = patch_home_page(html, brand)
        if path.name == "games-catalogue.html":
            html = patch_catalog_page(html, brand)
            html = inject_catalog_scripts(html, depth=0)
            html = inject_rail_features(html, depth=0)
        if path.name == "index.html":
            html = inject_rail_features(html, depth=0)
        from mm_portal_extras import apply_site_extras

        html = apply_site_extras(html, brand, prefix="", html_path=path, root=ROOT)
        path.write_text(html, encoding="utf-8")
        print(f"Patched {path.name}")

    write_monkey_mart_page(brand)
    write_robots_txt(brand)
    write_sitemap_xml(brand)
    print(f"Wrote robots.txt + sitemap.xml ({len(collect_sitemap_urls(brand))} URLs)")

    from thumbnail_fix import main as fix_thumbnails

    fix_thumbnails()

    from mm_portal_extras import apply_site_extras, patch_all_html_under, patch_native_catalog_js

    patch_native_catalog_js(brand.get("gamesCdn", ""))

    game_count = 0
    for path in GAMES_DIR.glob("*.html"):
        html = path.read_text(encoding="utf-8")
        html2 = inject_brand_assets(html, depth=1)
        html2 = inject_mm_images(html2, depth=1)
        html2 = inject_mm_native_player(html2, depth=1)
        html2 = inject_rail_features(html2, depth=1)
        html2 = patch_search_placeholder(html2, brand)
        html2 = patch_top_nav(html2, page="games")
        html2 = html2.replace(
            'aria-label="WGPlayground home"',
            f'aria-label="{brand["siteName"]} home"',
        )
        html2 = html2.replace(
            '<span class="brand-text">WG<span>Playground</span></span>',
            f'<span class="brand-text">{brand["brandHtml"]}</span>',
        )
        html2 = apply_site_extras(html2, brand, prefix="../", html_path=path, root=ROOT)
        if html2 != html:
            path.write_text(html2, encoding="utf-8")
            game_count += 1
    print(f"Injected theme into {game_count} game pages")

    n = patch_all_html_under(ROOT, brand)
    print(f"Applied GA/AdSense/CDN/footer on {n} HTML files")

    from seo_build import patch_all_seo_under

    seo_n = patch_all_seo_under(ROOT, brand)
    print(f"Applied JSON-LD / SEO meta on {seo_n} HTML files")

    # Re-apply top-nav after bulk passes
    nav_n = 0
    for path in ROOT.rglob("*.html"):
        if "assets/vendor" in str(path) or "templates/" in str(path):
            continue
        if '<nav class="top-nav"' not in path.read_text(encoding="utf-8", errors="replace"):
            continue
        rel = path.relative_to(ROOT)
        if rel.parts[:1] == ("games",):
            page = "games"
        elif rel.name == "games-catalogue.html":
            page = "games-catalogue"
        elif rel.name in ("index.html", "game.html", "monkey-mart.html", "a.html", "404.html"):
            page = rel.stem if rel.name not in ("index.html", "404.html") else (
                "index" if rel.name == "index.html" else "404"
            )
        else:
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        patched = patch_top_nav(html, page=page)
        if patched != html:
            path.write_text(patched, encoding="utf-8")
            nav_n += 1
    print(f"Normalized top-nav on {nav_n} HTML files")
    print("MonkeyMart branding ready — test index.html & monkey-mart.html")


if __name__ == "__main__":
    main()
