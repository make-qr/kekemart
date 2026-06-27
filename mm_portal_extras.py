"""GA, AdSense, games CDN rewrite, footer links — MonkeyMart portal deploy extras."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WG_GA_ID = "G-NCZQQEEXB6"


def load_brand() -> dict:
    return json.loads((ROOT / "brand/monkeymart.json").read_text(encoding="utf-8"))


def patch_wg_ga(html: str, measurement_id: str) -> str:
    """Replace WG default GA id with MonkeyMart property."""
    if not measurement_id:
        return html
    return html.replace(WG_GA_ID, measurement_id)


def inject_ga(html: str, measurement_id: str) -> str:
    if not measurement_id:
        return html
    html = patch_wg_ga(html, measurement_id)
    if measurement_id in html and f"gtag/js?id={measurement_id}" in html:
        return html
    snippet = f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{measurement_id}');
</script>
"""
    return html.replace("</head>", snippet + "</head>", 1)


def inject_adsense(html: str, client_id: str) -> str:
    if not client_id or "pagead2.googlesyndication.com" in html:
        return html
    snippet = f"""<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client_id}"
     crossorigin="anonymous"></script>
"""
    return html.replace("</head>", snippet + "</head>", 1)


def rewrite_games_cdn(html: str, cdn: str) -> str:
    if not cdn:
        return html
    base = cdn.rstrip("/")
    html = html.replace("https://monkeymart.one/hosted-games/", f"{base}/projects/")
    html = re.sub(r"\.\./hosted-games/", f"{base}/projects/", html)
    html = re.sub(r'(?<=[\"\'(])hosted-games/', f"{base}/projects/", html)
    html = re.sub(rf"{re.escape(base)}/{re.escape(base)}/", f"{base}/", html)
    html = fix_cdn_project_paths(html, base)
    return html


def fix_cdn_project_paths(html: str, cdn: str) -> str:
    """Ensure games CDN asset/play URLs include /projects/{slug}/."""
    if not cdn or f"{cdn}/projects/" not in html and not re.search(
        rf"{re.escape(cdn)}/(?!projects/)[a-zA-Z0-9._-]+/", html
    ):
        return html
    return re.sub(
        rf"({re.escape(cdn)})/(?!projects/)([a-zA-Z0-9._-]+)/",
        r"\1/projects/\2/",
        html,
    )


def is_game_play_url(url: str) -> bool:
    return bool(re.search(r"/(index|frame|poker)\.html(\?|#|$)", url, re.I))


def cdn_thumbs_to_bundled(html: str, cdn: str, *, prefix: str = "") -> str:
    """Map CDN image URLs to bundled mm-native thumbs (keep play URLs on CDN)."""
    if not cdn:
        return html
    base = cdn.rstrip("/")
    p = prefix or ""

    def repl(m: re.Match[str]) -> str:
        url = m.group(0)
        if is_game_play_url(url):
            return url
        rel = ""
        if url.startswith(base + "/projects/"):
            rel = url[len(base + "/projects/") :]
        elif url.startswith(base + "/"):
            rel = url[len(base + "/") :]
        if not rel:
            return url
        return f"{p}assets/images/mm-native/{rel}"

    return re.sub(rf"{re.escape(base)}/projects/[^\s\"'<>]+", repl, html)


def canonical_url_for(html_path: Path, root: Path, domain: str) -> str:
    base = domain.rstrip("/")
    try:
        rel = html_path.relative_to(root)
    except ValueError:
        return base + "/"
    if rel == Path("index.html"):
        return base + "/"
    return f"{base}/{rel.as_posix()}"


def strip_wg_visible_text(html: str, brand: dict) -> str:
    """Replace user-visible WG copy only — keep game iframe/CDN URLs intact."""
    site = brand.get("siteName", "MonkeyMart.one")
    short = brand.get("brandShort", "MonkeyMart")

    pairs = [
        (
            r'<span class="brag-live-wordmark"><b>WG</b><span>Playground</span></span>',
            '<span class="brag-live-wordmark"><b>Monkey</b><span>Mart</span></span>',
        ),
        (
            r'<span class="brand-text">WG<span>Playground</span></span>',
            f'<span class="brand-text">{brand.get("brandHtml", "Monkey<span>Mart</span>")}</span>',
        ),
        ("Search 2,800+ games…", brand.get("searchPlaceholder", "Search games…")),
        ("Search 2800+ games…", brand.get("searchPlaceholder", "Search games…")),
        ("Embed all 2,800+ games instantly", "Embed hundreds of free games instantly"),
        ("Embed all 2800+ games instantly", "Embed hundreds of free games instantly"),
        ("Not on WGPlayground yet?", f"Not on {short} yet?"),
        ("Highly rated on WGPlayground", f"Highly rated on {short}"),
        ("Standard WGPlayground branding", f"Standard {short} branding"),
        ("Sign in to WGPlayground", f"Sign in to {short}"),
        ("Your WGPlayground streak", f"Your {short} streak"),
        ("Your week on WGPlayground", f"Your week on {short}"),
        ("This week on WGPlayground", f"This week on {short}"),
        ("Days in a row you've visited WGPlayground (this device)", f"Days in a row you've visited {short} (this device)"),
        ("Counts days you visit WGPlayground. Saved on this device.", f"Counts days you visit {short}. Saved on this device."),
        ("WGPlayground <code>ads.txt</code>", f"{short} <code>ads.txt</code>"),
        ("More games from this publisher on WGPlayground.", f"More free games on {site}."),
        ("Reports require WGPlayground backend — disabled in local clone.", "Reports are disabled on this site."),
        ("© 2026 WGPlayground clone", f"© 2026 {site}"),
        ("WGPlayground clone", site),
        (" on WGPlayground - ", f" on {short} - "),
        (" on WGPlayground.", f" on {site}."),
        ("Play free on WGPlayground", f"Play free on {site}"),
        (" — WGPlayground", f" — {site}"),
        (" — WGPlayGround", f" — {site}"),
        ("All games — WGPlayground", f"All games — {site}"),
        ("Play game — WGPlayground", f"Play game — {site}"),
        ("@wgplayground", "@monkeymartone"),
    ]
    for old, new in pairs:
        html = html.replace(old, new)

    html = re.sub(r"Play ([^<\[]+) on WGPlayground", rf"Play \1 on {short}", html)
    return html


def patch_wg_rebrand(html: str, brand: dict, *, html_path: Path | None = None, root: Path | None = None) -> str:
    """Replace WGPlayground branding with MonkeyMart (meta, titles, visible copy)."""
    site = brand.get("siteName", "MonkeyMart.one")
    short = brand.get("brandShort", "MonkeyMart")
    domain = brand.get("domain", "https://monkeymart.one")

    html = strip_wg_visible_text(html, brand)
    html = re.sub(
        r'(<meta property="og:site_name" content=")WGPlayground(")',
        rf"\1{site}\2",
        html,
    )
    html = html.replace('content="@wgplayground"', 'content="@monkeymartone"')
    html = re.sub(
        r"var BASE_URL = 'https://www\.wgplayground\.com/';",
        "var BASE_URL = '/';",
        html,
        count=1,
    )
    html = re.sub(
        r'<link rel="manifest" href="https://www\.wgplayground\.com[^"]*" />\s*\n?',
        "",
        html,
    )
    html = re.sub(
        r"<script>\s*\n\s*if \('serviceWorker' in navigator\)[\s\S]*?</script>\s*\n",
        "",
        html,
        count=1,
    )

    if html_path and root:
        url = canonical_url_for(html_path, root, domain)
        html = re.sub(
            r'(<meta property="og:url" content=")[^"]+(")',
            rf"\1{url}\2",
            html,
            count=1,
        )

    html = html.replace("WGPlayground", short)
    html = html.replace("WGPlayGround", short)
    html = html.replace("https://www.wgplayground.com/games-catalogue", "games-catalogue.html")
    html = html.replace("https://www.wgplayground.com/search", "games-catalogue.html")
    return html


def ensure_theme_css_last(html: str, prefix: str = "") -> str:
    """Load monkeymart-theme.css after Google Fonts so WG rules cannot win later."""
    href = f'{prefix}assets/css/monkeymart-theme.css'
    m = re.search(rf'(<link rel="stylesheet" href="{re.escape(href)}"[^>]*/>\s*)', html)
    if not m:
        return html
    link = m.group(1)
    html = html.replace(link, "", 1)
    font_needle = "fonts.googleapis.com/css2?family=Inter"
    if font_needle in html:
        idx = html.find(font_needle)
        end = html.find("</head>", idx)
        line_end = html.rfind("\n", idx, end)
        insert_at = end if line_end == -1 else line_end + 1
        return html[:insert_at] + link + html[insert_at:]
    return html.replace("</head>", link + "</head>", 1)


def patch_favicon_links(html: str, prefix: str = "") -> str:
    """Ensure favicon + apple-touch point at MonkeyMart site assets."""
    icon = f'{prefix}assets/images/site/favicon.ico'
    touch = f'{prefix}assets/images/site/apple-touch-icon.png'
    html = re.sub(
        r'<link rel="icon"[^>]*href="[^"]*"[^>]*>\s*',
        f'<link rel="icon" type="image/x-icon" href="{icon}">\n',
        html,
        count=1,
    )
    if 'rel="apple-touch-icon"' not in html:
        html = html.replace(
            f'<link rel="icon" type="image/x-icon" href="{icon}">',
            f'<link rel="icon" type="image/x-icon" href="{icon}">\n<link rel="apple-touch-icon" href="{touch}" />',
            1,
        )
    else:
        html = re.sub(
            r'(<link rel="apple-touch-icon" href=")[^"]+(")',
            rf"\1{touch}\2",
            html,
            count=1,
        )
    return html


def strip_search_kbd(html: str) -> str:
    return re.sub(r"\s*<kbd>/</kbd>", "", html)


def strip_topbar_chrome(html: str) -> str:
    """Remove WG sign-in / business controls from topbar HTML (cleaner flex layout)."""
    html = re.sub(
        r'\s*<div class="auth-control" id="authControl">[\s\S]*?\n  </div>\s*(?=\n\s*<div class="business-control")',
        "\n",
        html,
        count=1,
    )
    html = re.sub(
        r'\s*<div class="business-control" id="businessControl">[\s\S]*?\n  </div>\s*(?=\n\s*<button class="theme-btn")',
        "\n",
        html,
        count=1,
    )
    return html


def patch_topbar_layout(html: str) -> str:
    """Wrap search + nav + theme in .topbar-end so WG flex rules cannot pull them left."""
    if 'class="topbar-end"' in html:
        return html
    pattern = (
        r'\s*<div class="top-spacer"></div>\s*'
        r'(<form class="search"[\s\S]*?</form>\s*)'
        r'(<nav class="top-nav"[\s\S]*?</nav>\s*)'
        r'(<button class="theme-btn"[\s\S]*?</button>)'
    )
    repl = (
        '\n  <div class="topbar-end">\n    \\1    \\2    \\3  </div>'
    )
    patched, n = re.subn(pattern, repl, html, count=1)
    return patched if n else html


def patch_footer_links(html: str, prefix: str = "") -> str:
    reps = {
        "https://www.wgplayground.com/contact": f"{prefix}contact.html",
        "https://www.wgplayground.com/privacy-policy": f"{prefix}privacy.html",
        "https://www.wgplayground.com/terms-and-conditions": f"{prefix}terms.html",
        "https://www.wgplayground.com/copyright": f"{prefix}disclaimer.html",
        "https://www.wgplayground.com/content-guidelines": f"{prefix}faq.html",
        'href="/contact.html"': f'href="{prefix}contact.html"',
        'href="/privacy.html"': f'href="{prefix}privacy.html"',
        'href="/terms.html"': f'href="{prefix}terms.html"',
        'href="/disclaimer.html"': f'href="{prefix}disclaimer.html"',
        'href="/faq.html"': f'href="{prefix}faq.html"',
        'href="/about.html"': f'href="{prefix}about.html"',
    }
    for old, new in reps.items():
        html = html.replace(old, new)
    return html


def patch_brand_mark(html: str, prefix: str, brand: dict) -> str:
    site = brand.get("siteName", "MonkeyMart.one")
    brand_html = brand.get("brandHtml", 'Monkey<span>Mart</span>')
    logo = f"{prefix}assets/images/site/monkey-mart-logo.png"
    img_mark = (
        f'<span class="brand-mark mm-logo-wrap" aria-hidden="true">'
        f'<img class="mm-logo" src="{logo}" alt="MonkeyMart" width="40" height="40" loading="eager">'
        f"</span>"
    )
    html = re.sub(
        r'<span class="brand-mark" aria-hidden="true">\s*<svg[\s\S]*?</svg>\s*</span>',
        img_mark,
        html,
    )
    html = html.replace(
        '<span class="brand-text">WG<span>Playground</span></span>',
        f'<span class="brand-text">{brand_html}</span>',
    )
    html = html.replace('aria-label="WGPlayground home"', f'aria-label="{site} home"')
    html = re.sub(
        r"Your premier HTML5 game distribution network[^<]*</p>",
        f'<p class="mm-foot-tagline">{brand.get("footerTagline", "")}</p>',
        html,
        count=1,
    )
    return html


def build_footer_grid(prefix: str, brand: dict) -> str:
    site = brand.get("siteName", "MonkeyMart.one")
    brand_html = brand.get("brandHtml", 'Monkey<span>Mart</span>')
    tagline = brand.get(
        "footerTagline",
        "Play Monkey Mart and hundreds of free browser games — no install, no sign-in.",
    )
    logo = f"{prefix}assets/images/site/monkey-mart-logo.png"
    return f"""      <div class="foot-grid" data-mm-foot="1">
        <div>
          <a class="brand" href="{prefix}index.html" aria-label="{site} home">
            <span class="brand-mark mm-logo-wrap" aria-hidden="true">
              <img class="mm-logo" src="{logo}" alt="MonkeyMart" width="40" height="40" loading="lazy">
            </span>
            <span class="brand-text">{brand_html}</span>
          </a>
          <p class="mm-foot-tagline">{tagline}</p>
        </div>
        <div><h5>Play</h5><ul>
          <li><a href="{prefix}monkey-mart.html">Monkey Mart</a></li>
          <li><a href="{prefix}games-catalogue.html">All games</a></li>
          <li><a href="{prefix}blog/index.html">Blog</a></li>
        </ul></div>
        <div><h5>Guides</h5><ul>
          <li><a href="{prefix}how-to-play-monkey-mart/index.html">How to play</a></li>
          <li><a href="{prefix}monkey-mart-tips/index.html">Tips &amp; tricks</a></li>
          <li><a href="{prefix}monkey-mart-unblocked/index.html">Unblocked</a></li>
          <li><a href="{prefix}about.html">About</a></li>
        </ul></div>
        <div><h5>Legal</h5><ul>
          <li><a href="{prefix}contact.html">Contact</a></li>
          <li><a href="{prefix}privacy.html">Privacy</a></li>
          <li><a href="{prefix}terms.html">Terms</a></li>
          <li><a href="{prefix}disclaimer.html">Copyright</a></li>
          <li><a href="{prefix}faq.html">FAQ</a></li>
        </ul></div>
      </div>"""


def patch_footer_shell(html: str, prefix: str, brand: dict) -> str:
    if '<div class="foot-grid"' not in html:
        return html
    grid = build_footer_grid(prefix, brand)
    html = re.sub(
        r'<div class="foot-grid"[\s\S]*?(?=\s*<div class="foot-bottom">)',
        grid.rstrip(),
        html,
        count=1,
    )
    html = re.sub(
        r'<div class="foot-bottom">[\s\S]*?</div>',
        '<div class="foot-bottom">\n'
        "        <span>© 2026 MonkeyMart.one</span>\n"
        "        <span>Free browser games · Saved on this device</span>\n"
        "      </div>",
        html,
        count=1,
    )
    return html


def prefix_for_html_path(path: Path, root: Path) -> str:
    try:
        rel = path.parent.relative_to(root)
    except ValueError:
        return ""
    if rel == Path("."):
        return ""
    return "../" * len(rel.parts)


def apply_site_extras(
    html: str,
    brand: dict,
    *,
    prefix: str = "",
    html_path: Path | None = None,
    root: Path | None = None,
) -> str:
    analytics = brand.get("analytics") or {}
    html = inject_ga(html, analytics.get("gaMeasurementId", ""))
    html = inject_adsense(html, analytics.get("adsenseClient", ""))
    html = rewrite_games_cdn(html, brand.get("gamesCdn", ""))
    html = cdn_thumbs_to_bundled(html, brand.get("gamesCdn", ""), prefix=prefix)
    html = patch_wg_rebrand(html, brand, html_path=html_path, root=root)
    html = strip_search_kbd(html)
    html = strip_topbar_chrome(html)
    html = patch_topbar_layout(html)
    html = ensure_theme_css_last(html, prefix)
    html = patch_favicon_links(html, prefix)
    html = patch_brand_mark(html, prefix, brand)
    html = patch_footer_links(html, prefix)
    html = patch_footer_shell(html, prefix, brand)
    return html


def patch_native_catalog_js(cdn: str) -> None:
    """Rewrite play/embed URLs to CDN; keep bundled thumb paths local."""
    if not cdn:
        return
    base = cdn.rstrip("/")
    play_re = re.compile(r'("play":\s*")hosted-games/')
    missing_projects = re.compile(
        rf'("play":\s*"{re.escape(base)}/)(?!projects/)([a-zA-Z0-9._-]+/)'
    )
    for name in ("mm-native-catalog.js", "mm-home-classics.js"):
        path = ROOT / "assets/js" / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        patched = play_re.sub(rf"\1{base}/projects/", text)
        patched = missing_projects.sub(rf"\1projects/\2", patched)
        if patched != text:
            path.write_text(patched, encoding="utf-8")
            print(f"Patched play CDN paths in {name}")


def patch_all_html_under(root: Path, brand: dict) -> int:
    count = 0
    for path in root.rglob("*.html"):
        if "assets/vendor" in str(path):
            continue
        prefix = prefix_for_html_path(path, root)
        html = path.read_text(encoding="utf-8", errors="replace")
        patched = apply_site_extras(html, brand, prefix=prefix, html_path=path, root=root)
        if patched != html:
            path.write_text(patched, encoding="utf-8")
            count += 1
    return count
