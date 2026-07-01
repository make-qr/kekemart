#!/usr/bin/env python3
"""Import self-hosted games from monkeymart.one source into the WGPlayground portal."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT.parent / "monkeymart.one/source_game.monkeymart.one"
DETAIL_DIR = ROOT.parent / "monkeymart.one/source_monkeymart.one/slopemain/detail"
HOSTED_LINK = ROOT / "hosted-games"
CATALOG_JS = ROOT / "assets/js/mm-native-catalog.js"
ROUTES_JS = ROOT / "assets/js/mm-native-routes.js"
GAMES_DIR = ROOT / "games"
WG_SHELL = ROOT / "perfect-match-3d.html"

MONKEY_MART_EMBED = "https://monkeymartfree.com/play/monkey-mart/"

# Prefer games.monkeymart.one CDN; external mirrors only as last resort.
EMBED_OVERRIDES: dict[str, str] = {}

# Papas slopemain detail slug aliases -> native catalog slug
DETAIL_SLUG_ALIASES: dict[str, str] = {
    "ducklife-4": "ducklife4",
    "motox3m": "moto-x3m",
    "motox3m-2": "moto-x3m-2",
    "motox3m-3": "moto-x3m-2",
    "moto-x3m-4-winter": "moto-x3m-winter",
    "moto-x3m-5-pool-party": "moto-x3m-pool-party",
    "moto-x3m-spooky-land": "moto-x3m-spooky-land",
    "fireboy-and-watergirl-1": "fireboy-and-watergirl-1",
    "monkey-mart": "monkey-mart",
}

SERIES_RULES: list[tuple[str, list[str]]] = [
    (r"^fnaf", ["FNAF", "Horror"]),
    (r"^moto-x3m", ["Racing", "Moto X3M"]),
    (r"^vex", ["Platformer", "Vex"]),
    (r"^fireboy-and-watergirl", ["Puzzle", "Fireboy & Watergirl"]),
    (r"^snail-bob", ["Adventure", "Snail Bob"]),
    (r"^subway-surfers", ["Arcade", "Runner"]),
    (r"^slope", ["Arcade", "Racing"]),
    (r"^retro-bowl", ["Sports", "Retro"]),
    (r"^minecraft", ["Sandbox"]),
    (r"^mario", ["Platformer", "Retro"]),
    (r"^cookie-clicker", ["Casual", "Idle"]),
    (r"^2048", ["Puzzle"]),
    (r"^minesweeper", ["Puzzle"]),
    (r"^solitaire|ms-solitaire", ["Card"]),
    (r"^pacman", ["Arcade", "Retro"]),
    (r"^flappy", ["Arcade"]),
    (r"^among-us", ["Action"]),
    (r"^idle-breakout", ["Casual", "Idle"]),
    (r"^poker", ["Card"]),
    (r"random$", ["2 Players", "Random"]),
    (r"^1v1", ["Action", "2 Players"]),
]

COLORS = [
    "#16a34a", "#3b82f6", "#ef4444", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#22c55e",
]


def slug_from_href(href: str) -> str:
    m = re.match(r"projects/([^/]+)/(?:index|frame|[^/]+)\.html", href)
    return m.group(1) if m else ""


def entry_relpath(href: str) -> str:
    """Return path under projects/ e.g. slope/index.html or poker/poker.html."""
    m = re.match(r"projects/(.+)", href)
    return m.group(1) if m else ""


def resolve_entry_file(source: Path, slug: str, href: str = "") -> Path | None:
    proj = source / "projects" / slug
    if href:
        rel = entry_relpath(href)
        candidate = source / "projects" / rel
        if candidate.is_file():
            return candidate
    for name in ("index.html", "frame.html", "poker.html"):
        candidate = proj / name
        if candidate.is_file():
            return candidate
    return None


def infer_cats(slug: str) -> list[str]:
    cats = ["MonkeyMart Classics"]
    for pattern, extra in SERIES_RULES:
        if re.search(pattern, slug, re.I):
            cats.extend(extra)
            break
    return list(dict.fromkeys(cats))


def pick_color(slug: str) -> str:
    n = sum(ord(c) for c in slug)
    return COLORS[n % len(COLORS)]


def parse_index_html(path: Path) -> list[dict]:
    html = path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(
        r'<a href="(projects/[^"]+\.html)"[^>]*class="game-link[^"]*"[^>]*>'
        r"(.*?)</a>",
        re.S,
    )
    games: list[dict] = []
    seen: set[str] = set()
    for m in pattern.finditer(html):
        href = m.group(1)
        block = m.group(2)
        slug = slug_from_href(href)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        title_m = re.search(r'<h1 class="game-title">([^<]+)</h1>', block)
        img_m = re.search(r'<img class="game-icon" src="([^"]+)"', block)
        popular = "game-tile-popular" in block
        icon_src = img_m.group(1) if img_m else ""
        name = title_m.group(1).strip() if title_m else slug.replace("-", " ").title()
        games.append(
            {
                "slug": slug,
                "name": name,
                "href": href,
                "entry": entry_relpath(href),
                "icon": icon_src,
                "popular": popular,
                "cats": infer_cats(slug),
                "c": pick_color(slug),
            }
        )
    return games


def normalize_embed_url(url: str) -> str:
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if "monkeymart.lol/play" in url:
        return MONKEY_MART_EMBED
    return url


def load_external_urls() -> dict[str, str]:
    urls: dict[str, str] = {}
    if not DETAIL_DIR.is_dir():
        return urls
    for path in DETAIL_DIR.glob("*.html"):
        html = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'data-url="([^"]+)"', html)
        if not m:
            continue
        url = normalize_embed_url(m.group(1))
        stem = path.stem
        urls[stem] = url
        alias = DETAIL_SLUG_ALIASES.get(stem)
        if alias:
            urls[alias] = url
    return urls


def lookup_external(slug: str, ext_map: dict[str, str]) -> str:
    if slug in EMBED_OVERRIDES:
        return EMBED_OVERRIDES[slug]
    if slug in ext_map:
        return ext_map[slug]
    slug_norm = slug.replace(".", "").replace("-", "")
    for key, url in ext_map.items():
        kn = key.replace(".", "").replace("-", "")
        if kn == slug_norm or slug in key or key in slug:
            return url
    return ""


def has_unity_payload(proj: Path) -> bool:
    build = proj / "Build"
    if build.is_dir() and any(build.iterdir()):
        return True
    if list(proj.glob("*.unityweb")) or list(proj.glob("*.data.unityweb")):
        return True
    unity_dir = proj / "unity"
    if unity_dir.is_dir() and list(unity_dir.glob("*.unityweb")):
        return True
    return False


def _unity_json_asset_keys() -> tuple[str, ...]:
    return (
        "dataUrl",
        "wasmCodeUrl",
        "wasmFrameworkUrl",
        "asmCodeUrl",
        "asmMemoryUrl",
        "asmFrameworkUrl",
        "codeUrl",
        "frameworkUrl",
    )


def local_unity_assets_complete(proj: Path) -> bool:
    """True when local Unity/WebGL binaries referenced by *.json actually exist."""
    configs: list[Path] = list(proj.glob("*.json"))
    build = proj / "Build"
    if build.is_dir():
        configs.extend(build.glob("*.json"))
    for cfg in configs:
        try:
            text = cfg.read_text(encoding="utf-8", errors="replace")
            low = text.lower()
            if "unityweb" not in low and "wasm" not in low:
                continue
            data = json.loads(text)
        except (OSError, json.JSONDecodeError):
            continue
        refs = [
            data[key]
            for key in _unity_json_asset_keys()
            if isinstance(data.get(key), str) and data[key]
        ]
        if not refs:
            continue

        def asset_exists(ref: str) -> bool:
            name = Path(ref).name
            return any(
                [
                    (proj / ref).is_file(),
                    (proj / name).is_file(),
                    (build / ref).is_file() if build.is_dir() else False,
                    (build / name).is_file() if build.is_dir() else False,
                ]
            )

        return all(asset_exists(ref) for ref in refs)
    return has_unity_payload(proj)


def unity_uses_remote_cdn(html: str) -> bool:
    if re.search(r"https?://[^\s\"']+\.json", html):
        return True
    return bool(re.search(r"UnityLoader\.instantiate\([^,]+,\s*[\"']https?://", html))


def has_poki_unity_loader(proj: Path, html: str) -> bool:
    if not re.search(r"loader:\s*['\"]unity", html):
        return False
    scripts = proj / "scripts"
    loaders = proj / "loaders"
    return (
        (loaders.is_dir() and any(loaders.rglob("*.js")))
        or (scripts.is_dir() and any(scripts.rglob("*.js")))
    )


def verify_embed_url(url: str, timeout: float = 8.0) -> bool:
    if not url.startswith("http"):
        return True
    import urllib.error
    import urllib.request

    headers = {"User-Agent": "Mozilla/5.0 (compatible; MonkeyMartImport/1.0)"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= resp.status < 400
        except urllib.error.HTTPError as exc:
            if exc.code in (405, 501) and method == "HEAD":
                continue
            return False
        except Exception:
            if method == "HEAD":
                continue
            return False
    return False


def embed_fallback_candidates(slug: str) -> list[str]:
    variants = list(
        dict.fromkeys(
            [
                slug,
                slug.replace(".", "-"),
                slug.replace(".", ""),
                slug.replace("-", ""),
            ]
        )
    )
    out: list[str] = []
    for variant in variants:
        out.append(f"https://ubggo.github.io/ub-games/{variant}/")
    out.append(f"https://3kh0.github.io/projects/{slug}/")
    return out


def patch_hosted_index(source: Path, slug: str) -> None:
    """Fix papas template paths that 404 when self-hosted (e.g. /js/main.js)."""
    proj = source / "projects" / slug
    idx = proj / "index.html"
    if not idx.exists():
        return
    html = idx.read_text(encoding="utf-8", errors="replace")
    orig = html
    if "/js/main.js" in html and not (proj / "js" / "main.js").exists():
        html = re.sub(
            r'\s*<script[^>]+src=["\']/js/main\.js["\'][^>]*>\s*</script>',
            "",
            html,
            flags=re.I,
        )
    if html != orig:
        idx.write_text(html, encoding="utf-8")


def local_play_path(source: Path, slug: str, href: str = "") -> str:
    entry = resolve_entry_file(source, slug, href)
    if not entry:
        proj = source / "projects" / slug
        if (proj / "frame.html").is_file():
            return f"projects/{slug}/frame.html"
        return f"projects/{slug}/index.html"
    rel = entry.relative_to(source / "projects").as_posix()
    return f"projects/{rel}"


def is_local_playable(source: Path, slug: str, href: str = "") -> bool:
    entry = resolve_entry_file(source, slug, href)
    if not entry:
        return False
    html = entry.read_text(encoding="utf-8", errors="replace")
    proj = source / "projects" / slug

    if has_poki_unity_loader(proj, html):
        return local_unity_assets_complete(proj)

    if "createUnityInstance" in html:
        return local_unity_assets_complete(proj)

    if (
        "UnityLoader" in html
        or "unityWebglBuildUrl" in html
        or "buildUrl" in html
    ):
        if unity_uses_remote_cdn(html):
            return True
        if local_unity_assets_complete(proj):
            return True
        for m in re.finditer(
            r'UnityLoader\.instantiate\([^,]+,\s*["\']([^"\']+\.json)',
            html,
        ):
            ref = m.group(1)
            if ref.startswith("http"):
                return True
            if (proj / ref).is_file() or (proj / Path(ref).name).is_file():
                return local_unity_assets_complete(proj)
        return False

    return True


def resolve_embed(source: Path, slug: str, ext_map: dict[str, str], href: str = "") -> tuple[str, str]:
    patch_hosted_index(source, slug)
    local = local_play_path(source, slug, href)

    # Source ships this game under projects/ — CDN mirrors the same path.
    if resolve_entry_file(source, slug, href):
        return local, "local"

    candidates: list[str] = []
    override = EMBED_OVERRIDES.get(slug)
    if override:
        candidates.append(override)
    external = lookup_external(slug, ext_map)
    if external and external not in candidates:
        candidates.append(external)
    for url in embed_fallback_candidates(slug):
        if url not in candidates:
            candidates.append(url)

    for url in candidates:
        if verify_embed_url(url):
            return url, "embed"

    return local, "fallback"


def iframe_src_for_page(embed: str) -> str:
    if embed.startswith("http://") or embed.startswith("https://"):
        return embed
    brand_path = ROOT / "brand/monkeymart.json"
    cdn = "https://games.monkeymart.one"
    if brand_path.is_file():
        cdn = json.loads(brand_path.read_text(encoding="utf-8")).get("gamesCdn", cdn)
    base = cdn.rstrip("/")
    path = embed.lstrip("/")
    if path.startswith("hosted-games/"):
        path = "projects/" + path[len("hosted-games/") :]
    if path.startswith("projects/"):
        return f"{base}/{path}"
    return "../" + path


FALLBACK_ICON = "assets/images/site/game-fallback.png"
NATIVE_THUMBS_DIR = ROOT / "assets/images/mm-native"

ICON_NAME_SCORE = (
    ("perfectcookie", 120),
    ("goldcookie", 110),
    ("thumb", 100),
    ("splash", 95),
    ("og-icon", 90),
    ("logo", 85),
    ("icon", 70),
    ("cookie", 65),
    ("banner", 60),
    ("cover", 55),
)
ICON_NAME_BAD = ("imperfect", "broken", "burnt", "raw", "small", "off", "halo")


def _icon_name_score(name: str) -> int:
    low = name.lower()
    if low.endswith("off.png") or low == "thumbs.db":
        return -100
    for bad in ICON_NAME_BAD:
        if bad in low:
            return -50
    score = 0
    for needle, pts in ICON_NAME_SCORE:
        if needle not in low:
            continue
        if needle == "perfectcookie" and "imperfect" in low:
            continue
        if needle == "cookie" and any(b in low for b in ("imperfect", "broken", "burnt", "raw", "small", "wrath", "spooky")):
            continue
        score = max(score, pts)
    if low.endswith((".png", ".webp")):
        score += 10
    return score


def _image_whitespace_ratio(path: Path) -> float:
    try:
        from PIL import Image

        im = Image.open(path).convert("RGB")
        data = list(im.getdata())[:: max(1, (im.size[0] * im.size[1]) // 400)]
        if not data:
            return 1.0
        white = sum(1 for r, g, b in data if r > 245 and g > 245 and b > 245)
        return white / len(data)
    except Exception:
        return 0.0


def pick_best_icon(source: Path, slug: str, icon_rel: str) -> str:
    proj = source / "projects" / slug
    candidates: list[tuple[int, str, Path]] = []

    def add(path: Path) -> None:
        if not path.is_file() or path.stat().st_size < 200:
            return
        rel = path.relative_to(source / "projects").as_posix()
        name = path.name
        score = _icon_name_score(name)
        if score < 0:
            return
        white = _image_whitespace_ratio(path)
        if white > 0.92:
            score -= 80
        elif white > 0.75:
            score -= 35
        try:
            from PIL import Image

            w, h = Image.open(path).size
            if min(w, h) >= 96:
                score += 8
            if min(w, h) >= 256:
                score += 6
        except Exception:
            pass
        candidates.append((score, rel, path))

    if icon_rel:
        rel = icon_rel.lstrip("/")
        if rel.startswith("projects/"):
            rel = rel[len("projects/") :]
        add(source / "projects" / rel)

    for guess in (
        f"{slug}/img/perfectCookie.png",
        f"{slug}/img/goldCookie.png",
        f"{slug}/thumb.png",
        f"{slug}/thumb.jpg",
        f"{slug}/splash.png",
        f"{slug}/icons/icon-256.png",
        f"{slug}/logo.png",
        f"{slug}/logo.jpg",
        f"{slug}/img/logo.png",
        f"{slug}/img/og-icon.png",
        f"{slug}/img/icon.png",
        f"{slug}/assets/icon.jpg",
    ):
        add(source / "projects" / guess)

    if proj.is_dir():
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            for sub in ("", "img", "assets", "icons"):
                base = proj / sub if sub else proj
                if not base.is_dir():
                    continue
                for f in sorted(base.glob(pattern)):
                    if f.name.lower() in ("index.html", "style.css"):
                        continue
                    add(f)

    if not candidates:
        return FALLBACK_ICON
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return f"hosted-games/{candidates[0][1]}"


def resolve_icon(source: Path, icon_rel: str, slug: str) -> str:
    return pick_best_icon(source, slug, icon_rel)


def ensure_hosted_link(source: Path) -> None:
    projects = source / "projects"
    if not projects.is_dir():
        raise SystemExit(f"Missing projects dir: {projects}")
    if HOSTED_LINK.is_symlink():
        HOSTED_LINK.unlink()
    elif HOSTED_LINK.exists():
        if HOSTED_LINK.is_dir() and not any(HOSTED_LINK.iterdir()):
            HOSTED_LINK.rmdir()
        else:
            raise SystemExit(f"hosted-games exists and is not a symlink: {HOSTED_LINK}")
    HOSTED_LINK.symlink_to(projects.resolve(), target_is_directory=True)
    print(f"Linked {HOSTED_LINK} -> {projects}")


def sync_native_thumbs(source: Path, games: list[dict]) -> int:
    """Copy native game icons into portal bundle (works without games CDN)."""
    count = 0
    for g in games:
        img = g.get("img", "")
        if not img.startswith("hosted-games/"):
            continue
        rel = img[len("hosted-games/") :]
        src = source / "projects" / rel
        if not src.is_file():
            continue
        dest = NATIVE_THUMBS_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dest)
        g["img"] = f"assets/images/mm-native/{rel}"
        count += 1
    if count:
        print(f"Bundled {count} native thumbs under assets/images/mm-native/")
    return count


def write_catalog(games: list[dict]) -> None:
    catalog = {}
    for g in games:
        slug = g["slug"]
        catalog[slug] = {
            "name": g["name"],
            "by": "MonkeyMart.one",
            "img": g.get("img", ""),
            "play": g.get("embed", f"hosted-games/{slug}/index.html"),
            "embedMode": g.get("embedMode", "local"),
            "cats": g["cats"],
            "c": g["c"],
            "popular": g.get("popular", False),
            "native": True,
        }
    CATALOG_JS.write_text(
        "window.MM_NATIVE_CATALOG = " + json.dumps(catalog, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    routes = {slug: f"games/mm-{slug}.html" for slug in catalog}
    ROUTES_JS.write_text(
        "window.MM_NATIVE_ROUTES = " + json.dumps(routes, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {CATALOG_JS.name} ({len(catalog)} games)")


def generate_pages(games: list[dict]) -> int:
    from native_game_page import apply_brand_to_page, apply_seo_to_native_page, build_native_page

    brand = json.loads((ROOT / "brand/monkeymart.json").read_text(encoding="utf-8"))
    if not WG_SHELL.exists():
        raise SystemExit(f"Missing WG shell template: {WG_SHELL}")
    template = WG_SHELL.read_text(encoding="utf-8")
    GAMES_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for g in games:
        slug = g["slug"]
        iframe = iframe_src_for_page(g.get("embed", f"hosted-games/{slug}/index.html"))
        page = build_native_page(template, g, games, iframe_src=iframe)
        page = apply_brand_to_page(page)
        page = apply_seo_to_native_page(page, g, brand)
        out = GAMES_DIR / f"mm-{slug}.html"
        out.write_text(page, encoding="utf-8")
        count += 1
    print(f"Generated {count} WG-shell play pages in games/mm-*.html")
    return count


def copy_site_logo(source: Path) -> None:
    dest_dir = ROOT / "assets/images/site"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "monkey-mart-logo.png"
    if dest.exists():
        return
    for candidate in (
        source / "games-site-logo.png",
        ROOT / "assets/images/site/logo-square.svg",
    ):
        if candidate.exists():
            if candidate.suffix == ".png":
                shutil.copy2(candidate, dest)
            else:
                shutil.copy2(candidate, dest_dir / "monkey-mart-logo.svg")
            print(f"Site logo from {candidate.name}")
            return


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--skip-link", action="store_true")
    parser.add_argument("--skip-pages", action="store_true")
    args = parser.parse_args()
    source: Path = args.source.resolve()

    index = source / "index.html"
    if not index.exists():
        raise SystemExit(f"Not found: {index}")

    games = parse_index_html(index)
    ext_map = load_external_urls()
    embed_count = 0
    local_count = 0
    for g in games:
        g["img"] = resolve_icon(source, g.get("icon", ""), g["slug"])
        href = g.get("href", "")
        if not resolve_entry_file(source, g["slug"], href):
            print(f"  skip missing: {g['slug']}")
            g["_skip"] = True
            continue
        embed, mode = resolve_embed(source, g["slug"], ext_map, href)
        g["embed"] = embed
        g["embedMode"] = mode
        if mode == "embed":
            embed_count += 1
        else:
            local_count += 1
    games = [g for g in games if not g.get("_skip")]

    if not args.skip_link:
        ensure_hosted_link(source)

    sync_native_thumbs(source, games)
    write_catalog(games)
    copy_site_logo(source)

    if not args.skip_pages:
        generate_pages(games)

    popular = sum(1 for g in games if g.get("popular"))
    print(f"Imported {len(games)} native games ({popular} popular, {local_count} local, {embed_count} embed)")


if __name__ == "__main__":
    main()
