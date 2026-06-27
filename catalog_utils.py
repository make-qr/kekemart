#!/usr/bin/env python3
"""Shared helpers for reading wg-catalog.js."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG_JS = ROOT / "assets/js/wg-catalog.js"


def loads_lenient(s: str) -> dict:
    """Parse JSON that may contain raw newlines inside strings."""
    out: list[str] = []
    in_str = False
    esc = False
    for ch in s:
        if esc:
            out.append(ch)
            esc = False
            continue
        if ch == "\\":
            out.append(ch)
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            out.append(ch)
            continue
        if in_str and ch in "\n\r":
            out.append(" ")
            continue
        out.append(ch)
    return json.loads("".join(out))


def extract_json_object(text: str, marker: str) -> dict:
    start = text.find(marker)
    if start == -1:
        raise ValueError(f"{marker!r} not found")
    i = text.find("{", start)
    if i == -1:
        raise ValueError(f"JSON object missing after {marker!r}")
    depth = 0
    for j in range(i, len(text)):
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[i : j + 1])
                except json.JSONDecodeError:
                    return loads_lenient(text[i : j + 1])
    raise ValueError(f"Unclosed JSON object for {marker!r}")


def sanitize_catalog(catalog: dict) -> dict:
    for entry in catalog.values():
        for key, val in list(entry.items()):
            if isinstance(val, str):
                entry[key] = val.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
            elif isinstance(val, list):
                entry[key] = [
                    v.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
                    if isinstance(v, str)
                    else v
                    for v in val
                ]
    return catalog


def write_catalog_js(catalog: dict, by_pub: dict, path: Path | None = None) -> None:
    path = path or CATALOG_JS
    sanitize_catalog(catalog)
    path.write_text(
        "window.WGP_CATALOG = "
        + json.dumps(catalog, ensure_ascii=False)
        + ";\nwindow.WGP_BY_PUBLISHER = "
        + json.dumps(by_pub, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )


def parse_catalog_file(path: Path | None = None) -> tuple[dict, dict]:
    path = path or CATALOG_JS
    text = path.read_text(encoding="utf-8")
    catalog = extract_json_object(text, "window.WGP_CATALOG = ")
    try:
        by_pub = extract_json_object(text, "window.WGP_BY_PUBLISHER = ")
    except ValueError:
        by_pub = {}
    return catalog, by_pub


def slug_from_path(path: str) -> str:
    return path.strip("/").replace("/", "-")
