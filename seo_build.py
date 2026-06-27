"""SEO helpers — meta tags, JSON-LD, on-page copy, sitemap & robots."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def abs_url(domain: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    stack: list[str] = []
    for part in path.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
        else:
            stack.append(part)
    clean = "/".join(stack)
    return f"{domain.rstrip('/')}/{clean}" if clean else domain.rstrip("/")


def _prefix(depth: int) -> str:
    return "../" * depth


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def strip_wg_duplicate_og(html_text: str) -> str:
    """Remove second OG block injected by WG home template."""
    html_text = re.sub(
        r"\n\s*<meta property=\"og:title\" content=\"MonkeyMart\.com\" />.*?"
        r"<meta property=\"og:image\"[^>]+>\n",
        "\n",
        html_text,
        count=1,
        flags=re.S,
    )
    return html_text


def inject_canonical(html_text: str, url: str) -> str:
    tag = f'<link rel="canonical" href="{_esc(url)}" />'
    html_text = re.sub(r'<link rel="canonical"[^>]*>\s*', "", html_text)
    return html_text.replace("</head>", f"{tag}\n</head>", 1)


def inject_json_ld(html_text: str, schemas: list[dict]) -> str:
    html_text = re.sub(
        r'<script type="application/ld\+json" id="mm-jsonld">.*?</script>\s*',
        "",
        html_text,
        flags=re.S,
    )
    payload = json.dumps(schemas if len(schemas) > 1 else schemas[0], ensure_ascii=False)
    block = f'<script type="application/ld+json" id="mm-jsonld">{payload}</script>\n'
    return html_text.replace("</head>", block + "</head>", 1)


def set_head_meta(
    html_text: str,
    *,
    title: str,
    description: str,
    og_image: str,
    canonical: str,
    domain: str,
    og_type: str = "website",
    site_name: str = "MonkeyMart.one",
    twitter_site: str = "@monkeymartone",
    keywords: str | None = None,
) -> str:
    og_image_abs = og_image if og_image.startswith("http") else abs_url(domain, og_image)

    html_text = re.sub(r"<title>[^<]*</title>", f"<title>{_esc(title)}</title>", html_text, count=1)
    html_text = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{_esc(description)}"',
        html_text,
        count=1,
    )
    if keywords:
        if 'name="keywords"' in html_text:
            html_text = re.sub(
                r'<meta name="keywords" content="[^"]*"',
                f'<meta name="keywords" content="{_esc(keywords)}"',
                html_text,
                count=1,
            )
        else:
            html_text = html_text.replace(
                f'<meta name="description" content="{_esc(description)}"',
                f'<meta name="description" content="{_esc(description)}" />\n'
                f'<meta name="keywords" content="{_esc(keywords)}"',
                1,
            )

    pairs = [
        ("og:type", og_type, True),
        ("og:title", title, True),
        ("og:description", description, True),
        ("og:image", og_image_abs, True),
        ("og:url", canonical, True),
        ("og:site_name", site_name, True),
        ("twitter:card", "summary_large_image", False),
        ("twitter:title", title, False),
        ("twitter:description", description, False),
        ("twitter:image", og_image_abs, False),
        ("twitter:site", twitter_site, False),
    ]
    for key, val, is_og in pairs:
        attr = "property" if is_og else "name"
        pat = rf'(<meta {attr}="{re.escape(key)}"[^>]*content=")[^"]*(")'
        if re.search(pat, html_text):
            html_text = re.sub(
                pat,
                lambda m, v=val: f"{m.group(1)}{_esc(v)}{m.group(2)}",
                html_text,
                count=1,
            )
        else:
            html_text = html_text.replace(
                "</head>",
                f'<meta {attr}="{key}" content="{_esc(val)}" />\n</head>',
                1,
            )

    html_text = inject_canonical(html_text, canonical)
    return html_text


def patch_about_section(html_text: str, paragraphs: list[str]) -> str:
    body = "".join(f"<p>{_esc(p)}</p>" for p in paragraphs)

    def _repl(m: re.Match[str]) -> str:
        return f"{m.group(1)}\n          {body}\n        {m.group(2)}"

    return re.sub(
        r'(<section class="game-section" id="about">\s*<h3>About this game</h3>\s*).*?(</section>)',
        _repl,
        html_text,
        count=1,
        flags=re.S,
    )


def patch_how_to_play(html_text: str, steps: list[str]) -> str:
    lines = "<br />\n".join(_esc(s) for s in steps)
    return re.sub(
        r'(<section class="game-section game-instructions">\s*<h3>How to play</h3>\s*'
        r'<div class="instr-block">\s*<p>).*?(</p>\s*</div>\s*</section>)',
        rf"\1{lines}\2",
        html_text,
        count=1,
        flags=re.S,
    )


def patch_specifications(html_text: str, specs: dict[str, str]) -> str:
    icons = {
        "Technology": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6 8.5 8.5M15.5 15.5l2.9 2.9M5.6 18.4l2.9-2.9M15.5 8.5l2.9-2.9"/></svg>',
        "Dimensions": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>',
        "Controls": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="3" width="12" height="18" rx="6"/><path d="M12 3v6"/></svg>',
        "Gameplay": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/></svg>',
        "Language": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
        "Features": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>',
    }
    rows = []
    for label, value in specs.items():
        ico = icons.get(label, icons["Features"])
        rows.append(
            f"""                          <div>
                <dt>
                  {ico}                  {label}
                </dt>
                <dd>{_esc(value)}</dd>
              </div>"""
        )
    block = "\n".join(rows)
    return re.sub(
        r'(<section class="game-section spec-card" id="specifications">\s*<h3>Specifications</h3>\s*'
        r'<dl class="spec-list">).*?(</dl>\s*</section>)',
        rf"\1\n{block}\n                      \2",
        html_text,
        count=1,
        flags=re.S,
    )


def patch_tag_chips(html_text: str, tags: list[str], *, depth: int = 0) -> str:
    p = _prefix(depth)

    def slugify(tag: str) -> str:
        s = tag.lower().replace("&", "and").replace("'", "")
        return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

    chips = []
    for tag in tags:
        href = f"{p}games-catalogue.html?cat={slugify(tag)}"
        cls = "tag-chip tag-chip--genre"
        chips.append(f'<a class="{cls}" href="{href}">{_esc(tag)}</a>')
    chip_html = "\n                      ".join(chips)
    return re.sub(
        r'(<div class="tag-chips">).*?(</div>)',
        rf"\1\n                      {chip_html}\n                    \2",
        html_text,
        count=1,
        flags=re.S,
    )


def inject_faq_section(html_text: str, faq: list[dict[str, str]]) -> str:
    if not faq or 'id="mm-faq"' in html_text:
        return html_text
    items = []
    for item in faq:
        items.append(
            f"""        <details class="mm-faq-item">
          <summary>{_esc(item["q"])}</summary>
          <p>{_esc(item["a"])}</p>
        </details>"""
        )
    section = f"""
        <section class="game-section mm-faq" id="mm-faq">
          <h3>Monkey Mart — frequently asked questions</h3>
{chr(10).join(items)}
        </section>
"""
    return html_text.replace(
        '<section class="game-section spec-card" id="specifications">',
        section + '        <section class="game-section spec-card" id="specifications">',
        1,
    )


def video_game_schema(
    *,
    name: str,
    description: str,
    url: str,
    image: str,
    domain: str,
    genre: list[str],
) -> dict:
    img = image if image.startswith("http") else abs_url(domain, image)
    return {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": name,
        "description": description,
        "url": url,
        "image": img,
        "genre": genre,
        "gamePlatform": ["Web browser", "Android", "iOS"],
        "applicationCategory": "Game",
        "operatingSystem": "Any",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "publisher": {"@type": "Organization", "name": "MonkeyMart.one", "url": domain},
    }


def breadcrumb_schema(items: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": url,
            }
            for i, (name, url) in enumerate(items)
        ],
    }


def faq_schema(faq: list[dict[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
            }
            for item in faq
        ],
    }


def website_schema(domain: str, description: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "MonkeyMart.one",
        "url": domain,
        "description": description,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{domain}/games-catalogue.html?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def organization_schema(domain: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "MonkeyMart.one",
        "url": domain,
        "logo": abs_url(domain, "assets/images/site/monkey-mart-logo.png"),
    }


def patch_monkey_mart_page(html_text: str, brand: dict, *, depth: int = 0) -> str:
    seo = brand["seo"]["monkeyMart"]
    domain = brand["domain"]
    p = _prefix(depth)
    page_path = f"{p}monkey-mart.html".lstrip("/")
    canonical = abs_url(domain, page_path)
    og_image = seo.get("ogImage") or brand["heroGame"].get("img") or "assets/images/site/monkey-mart-logo.png"

    html_text = set_head_meta(
        html_text,
        title=seo["title"],
        description=seo["description"],
        og_image=og_image,
        canonical=canonical,
        domain=domain,
        og_type="website",
        site_name=brand["siteName"],
        keywords=seo.get("keywords"),
    )
    html_text = patch_about_section(html_text, seo["about"])
    html_text = patch_how_to_play(html_text, seo["howToPlay"])
    html_text = patch_specifications(html_text, seo["specs"])
    html_text = patch_tag_chips(html_text, seo["tags"], depth=depth)
    html_text = inject_faq_section(html_text, seo.get("faq", []))

    crumbs = breadcrumb_schema(
        [
            ("Home", abs_url(domain, "")),
            ("All games", abs_url(domain, "games-catalogue.html")),
            ("Monkey Mart", canonical),
        ]
    )
    schemas = [
        video_game_schema(
            name=brand["heroGame"]["name"],
            description=seo["description"],
            url=canonical,
            image=og_image,
            domain=domain,
            genre=seo["tags"],
        ),
        crumbs,
    ]
    if seo.get("faq"):
        schemas.append(faq_schema(seo["faq"]))
    html_text = inject_json_ld(html_text, schemas)

    html_text = html_text.replace(
        'data-game-url="https://www.wgplayground.com/game/monkey-mart"',
        f'data-game-url="{canonical}"',
    )
    return inject_apple_touch_icon(html_text, depth=depth)


def inject_apple_touch_icon(html_text: str, *, depth: int = 0) -> str:
    p = "../" * depth
    href = f"{p}assets/images/site/apple-touch-icon.png"
    tag = f'<link rel="apple-touch-icon" href="{href}" />'
    if "apple-touch-icon" in html_text:
        return html_text
    return html_text.replace("</head>", f"{tag}\n</head>", 1)


def native_game_description(name: str, cats: list[str]) -> str:
    primary = next((c for c in cats if c != "MonkeyMart Classics"), cats[0] if cats else "arcade")
    primary_l = primary.lower()
    article = "an" if primary_l[:1] in "aeiou" else "a"
    return (
        f"Play {name} free online — {article} {primary_l} browser game on MonkeyMart.one. "
        f"No download, no install. Works on desktop and mobile."
    )[:165]


def relocate_home_seo(html_text: str) -> str:
    """Keep the home SEO blurb above the footer, not above the hero."""
    pattern = re.compile(
        r"\s*<section class=\"mm-home-seo\"[^>]*>.*?</section>\s*",
        re.S | re.I,
    )
    match = pattern.search(html_text)
    if not match:
        return html_text

    block = match.group(0)
    without = html_text[: match.start()] + html_text[match.end() :]
    footer_anchor = "\n\n    <footer>"
    if footer_anchor not in without:
        footer_anchor = "    <footer>"
    if footer_anchor not in without:
        return html_text

    footer_idx = without.rfind(footer_anchor)
    before_footer = without[max(0, footer_idx - 600) : footer_idx]
    if "mm-home-seo" in before_footer:
        return html_text

    return without.replace(footer_anchor, "\n" + block + footer_anchor, 1)


def patch_home_page(html_text: str, brand: dict) -> str:
    seo = brand["seo"]["home"]
    domain = brand["domain"]
    html_text = strip_wg_duplicate_og(html_text)
    html_text = set_head_meta(
        html_text,
        title=seo["title"],
        description=seo["description"],
        og_image=seo.get("ogImage", "assets/images/site/monkey-mart-logo.png"),
        canonical=domain,
        domain=domain,
        og_type="website",
        site_name=brand["siteName"],
        keywords="monkey mart, monkey mart game, play monkey mart free, monkey mart online, free browser games, monkeymart.one",
    )
    html_text = inject_json_ld(
        html_text,
        [
            website_schema(domain, seo["description"]),
            organization_schema(domain),
        ],
    )
    intro = f"""
    <section class="mm-home-seo" aria-label="About MonkeyMart.one">
      <h1 class="mm-home-seo__title">{_esc(seo["h1"])}</h1>
      <p class="mm-home-seo__intro">{_esc(seo["intro"])}</p>
      <p class="mm-home-seo__cta"><a href="monkey-mart.html">▶ Play Monkey Mart now</a> · <a href="games-catalogue.html">Browse all games</a></p>
    </section>
"""
    footer_anchor = "\n\n    <footer>"
    if footer_anchor not in html_text:
        footer_anchor = "    <footer>"
    if 'class="mm-home-seo"' not in html_text:
        html_text = html_text.replace(
            footer_anchor,
            "\n" + intro + footer_anchor,
            1,
        )
    return inject_apple_touch_icon(relocate_home_seo(html_text), depth=0)


def patch_catalog_page(html_text: str, brand: dict) -> str:
    seo = brand["seo"]["catalog"]
    domain = brand["domain"]
    canonical = abs_url(domain, "games-catalogue.html")
    html_text = set_head_meta(
        html_text,
        title=seo["title"],
        description=seo["description"],
        og_image=seo.get("ogImage", "assets/images/site/monkey-mart-logo.png"),
        canonical=canonical,
        domain=domain,
        og_type="website",
        site_name=brand["siteName"],
        keywords="monkey mart, free online games, browser games, game catalogue, monkeymart.one",
    )
    if 'id="mm-jsonld"' not in html_text:
        html_text = inject_json_ld(
            html_text,
            [
                collection_page_schema(domain, seo["title"], seo["description"], canonical),
                breadcrumb_schema(
                    [
                        ("Home", abs_url(domain, "")),
                        ("Monkey Mart", abs_url(domain, "monkey-mart.html")),
                        ("All games", canonical),
                    ]
                ),
            ],
        )
    return inject_apple_touch_icon(html_text, depth=0)


def patch_native_game_seo(
    html_text: str,
    *,
    name: str,
    description: str,
    slug: str,
    image: str,
    cats: list[str],
    brand: dict,
    depth: int = 1,
) -> str:
    domain = brand["domain"]
    p = _prefix(depth)
    if slug == "monkey-mart":
        return patch_monkey_mart_page(html_text, brand, depth=depth)
    page = f"games/mm-{slug}.html"
    canonical = abs_url(domain, page)
    title = f"{name} — Play Free Online | MonkeyMart.one"
    desc = description or native_game_description(name, cats)

    html_text = set_head_meta(
        html_text,
        title=title,
        description=desc,
        og_image=image,
        canonical=canonical,
        domain=domain,
        og_type="website",
        site_name=brand["siteName"],
    )
    html_text = patch_about_section(html_text, [desc])
    genres = [c for c in cats if c != "MonkeyMart Classics"] or cats
    html_text = inject_json_ld(
        html_text,
        [
            video_game_schema(
                name=name,
                description=desc,
                url=canonical,
                image=image,
                domain=domain,
                genre=genres[:4],
            ),
            breadcrumb_schema(
                [
                    ("Home", abs_url(domain, "")),
                    ("All games", abs_url(domain, "games-catalogue.html")),
                    (name, canonical),
                ]
            ),
        ],
    )
    return inject_apple_touch_icon(html_text, depth=depth)


def collection_page_schema(domain: str, title: str, description: str, url: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": description,
        "url": url,
        "isPartOf": {
            "@type": "WebSite",
            "name": "MonkeyMart.one",
            "url": domain,
            "about": {
                "@type": "VideoGame",
                "name": "Monkey Mart",
                "url": abs_url(domain, "monkey-mart.html"),
            },
        },
    }


def web_page_schema(name: str, description: str, url: str, domain: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "description": description,
        "url": url,
        "isPartOf": {"@type": "WebSite", "name": "MonkeyMart.one", "url": domain},
    }


def _title_name(html_text: str) -> str:
    m = re.search(r"<title>([^<]+)</title>", html_text)
    if not m:
        return "Game"
    title = m.group(1).strip()
    for sep in (" — ", " - ", " | "):
        if sep in title:
            return title.split(sep)[0].strip()
    return title


def _meta_content(html_text: str, key: str, *, og: bool = False) -> str:
    attr = "property" if og else "name"
    m = re.search(rf'<meta {attr}="{re.escape(key)}"[^>]*content="([^"]*)"', html_text)
    return m.group(1) if m else ""


def mm_game_description(name: str, raw_desc: str) -> str:
    desc = (raw_desc or "").strip()
    if not desc:
        desc = f"Play {name} free in your browser on MonkeyMart.one."
    if "monkey mart" not in desc.lower():
        tail = " Free on MonkeyMart.one — home of Monkey Mart and 500+ browser games."
        desc = (desc.rstrip(".") + "." + tail) if desc else tail.strip()
    return desc[:165]


def patch_wg_game_page_seo(html_text: str, path: Path, brand: dict, root: Path) -> str:
    if 'id="mm-jsonld"' in html_text:
        return html_text
    domain = brand["domain"]
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return html_text
    if not rel.startswith("games/") or rel.startswith("games/mm-"):
        return html_text

    name = _title_name(html_text)
    raw_desc = _meta_content(html_text, "description")
    desc = mm_game_description(name, raw_desc)
    og_image = _meta_content(html_text, "og:image", og=True) or "assets/images/site/og-home.webp"
    canonical = abs_url(domain, rel)
    title = f"{name} — Play Free Online | MonkeyMart.one"
    keywords = f"{name.lower()}, {name.lower()} game, play {name.lower()} free, monkey mart, free online games, monkeymart.one"

    html_text = set_head_meta(
        html_text,
        title=title,
        description=desc,
        og_image=og_image,
        canonical=canonical,
        domain=domain,
        og_type="website",
        site_name=brand["siteName"],
        keywords=keywords,
    )
    genres = ["Browser game", "Free online game"]
    return inject_json_ld(
        html_text,
        [
            video_game_schema(
                name=name,
                description=desc,
                url=canonical,
                image=og_image,
                domain=domain,
                genre=genres,
            ),
            breadcrumb_schema(
                [
                    ("Home", abs_url(domain, "")),
                    ("Monkey Mart", abs_url(domain, "monkey-mart.html")),
                    ("All games", abs_url(domain, "games-catalogue.html")),
                    (name, canonical),
                ]
            ),
        ],
    )


def patch_page_seo_if_missing(html_text: str, path: Path, brand: dict, root: Path) -> str:
    if 'id="mm-jsonld"' in html_text:
        return html_text
    domain = brand["domain"]
    try:
        rel = path.relative_to(root)
    except ValueError:
        return html_text

    name = _title_name(html_text)
    raw_desc = _meta_content(html_text, "description") or brand.get("description", "")
    rel_posix = rel.as_posix()

    if rel_posix == "games-catalogue.html":
        seo = brand["seo"]["catalog"]
        canonical = abs_url(domain, rel_posix)
        desc = seo["description"]
        html_text = set_head_meta(
            html_text,
            title=seo["title"],
            description=desc,
            og_image=seo.get("ogImage", "assets/images/site/og-home.webp"),
            canonical=canonical,
            domain=domain,
            site_name=brand["siteName"],
            keywords="monkey mart, free online games, browser games, game catalogue, monkeymart.one",
        )
        return inject_json_ld(
            html_text,
            [
                collection_page_schema(domain, seo["title"], desc, canonical),
                breadcrumb_schema(
                    [
                        ("Home", abs_url(domain, "")),
                        ("Monkey Mart", abs_url(domain, "monkey-mart.html")),
                        ("All games", canonical),
                    ]
                ),
            ],
        )

    if rel_posix.startswith("games/"):
        return patch_wg_game_page_seo(html_text, path, brand, root)

    static_pages = {
        "about.html": ("About MonkeyMart.one", "Learn about MonkeyMart.one — play Monkey Mart free and browse 500+ browser games."),
        "privacy.html": ("Privacy Policy", "Privacy policy for MonkeyMart.one — free Monkey Mart and browser games site."),
        "terms.html": ("Terms of Service", "Terms of use for MonkeyMart.one."),
        "faq.html": ("FAQ", "Frequently asked questions about Monkey Mart and free games on MonkeyMart.one."),
        "contact.html": ("Contact", "Contact MonkeyMart.one."),
        "disclaimer.html": ("Copyright", "Copyright and disclaimer for MonkeyMart.one."),
        "cookie-policy.html": ("Cookie Policy", "Cookie policy for MonkeyMart.one."),
        "game.html": ("Play Games", "Play free browser games on MonkeyMart.one — start with Monkey Mart."),
    }
    if rel_posix in static_pages:
        page_name, page_desc = static_pages[rel_posix]
        canonical = abs_url(domain, rel_posix)
        html_text = set_head_meta(
            html_text,
            title=f"{page_name} | MonkeyMart.one",
            description=page_desc,
            og_image="assets/images/site/og-home.webp",
            canonical=canonical,
            domain=domain,
            site_name=brand["siteName"],
            keywords="monkey mart, monkey mart game, free online games, monkeymart.one",
        )
        return inject_json_ld(
            html_text,
            [
                web_page_schema(page_name, page_desc, canonical, domain),
                breadcrumb_schema([("Home", abs_url(domain, "")), (page_name, canonical)]),
            ],
        )

    if rel.name == "index.html" and len(rel.parts) > 1:
        dir_name = rel.parts[0].replace("-", " ").title()
        canonical = abs_url(domain, rel_posix)
        page_desc = f"{dir_name} — Monkey Mart guides and free games on MonkeyMart.one."
        html_text = set_head_meta(
            html_text,
            title=f"{dir_name} | MonkeyMart.one",
            description=page_desc,
            og_image="assets/images/site/og-home.webp",
            canonical=canonical,
            domain=domain,
            site_name=brand["siteName"],
            keywords="monkey mart, monkey mart game, monkey mart guide, monkeymart.one",
        )
        return inject_json_ld(
            html_text,
            [
                web_page_schema(dir_name, page_desc, canonical, domain),
                breadcrumb_schema([("Home", abs_url(domain, "")), (dir_name, canonical)]),
            ],
        )

    return html_text


def patch_all_seo_under(root: Path, brand: dict) -> int:
    count = 0
    for path in root.rglob("*.html"):
        if "assets/vendor" in str(path) or "templates/" in str(path):
            continue
        html = path.read_text(encoding="utf-8", errors="replace")
        patched = patch_page_seo_if_missing(html, path, brand, root)
        if patched != html:
            path.write_text(patched, encoding="utf-8")
            count += 1
    return count


def collect_sitemap_urls(brand: dict) -> list[tuple[str, str, Path | None]]:
    """Return (loc, changefreq, source_path) for every deployable HTML page."""
    domain = brand["domain"]
    urls: list[tuple[str, str, Path | None]] = []
    seen: set[str] = set()

    def add(loc: str, freq: str, path: Path | None = None) -> None:
        if loc in seen:
            return
        seen.add(loc)
        urls.append((loc, freq, path))

    skip_parts = ("assets/vendor", "hosted-games/", "templates/")
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in str(path) for part in skip_parts):
            continue
        rel = path.relative_to(ROOT)
        if rel == Path("index.html"):
            add(abs_url(domain, ""), "daily", path)
        elif rel.name == "index.html":
            add(abs_url(domain, f"{rel.parent.as_posix()}/"), "monthly", path)
        elif rel.parts[:1] == ("games",):
            freq = "weekly" if rel.name.startswith("mm-") else "monthly"
            add(abs_url(domain, rel.as_posix()), freq, path)
        elif rel.name == "monkey-mart.html":
            add(abs_url(domain, "monkey-mart.html"), "weekly", path)
        elif rel.name == "games-catalogue.html":
            add(abs_url(domain, "games-catalogue.html"), "daily", path)
        else:
            add(abs_url(domain, rel.as_posix()), "monthly", path)

    return urls


def write_robots_txt(brand: dict) -> Path:
    domain = brand["domain"]
    out = ROOT / "robots.txt"
    out.write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {domain}/sitemap.xml\n",
        encoding="utf-8",
    )
    return out


def write_sitemap_xml(brand: dict) -> Path:
    from datetime import datetime, timezone

    out = ROOT / "sitemap.xml"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, freq, src in collect_sitemap_urls(brand):
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        if src and src.is_file():
            mtime = datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
            lines.append(f"    <lastmod>{mtime}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
