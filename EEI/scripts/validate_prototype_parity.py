#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_DIR = ROOT / "prototype"
INDEX_HTML = PROTOTYPE_DIR / "index.html"
STANDALONE_HTML = PROTOTYPE_DIR / "standalone.html"


class PrototypeHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.external_scripts: list[str] = []
        self.external_stylesheets: list[str] = []
        self.inline_script_count = 0
        self.inline_style_count = 0
        self.view_keys: set[str] = set()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if "id" in attributes and attributes["id"]:
            self.ids.add(attributes["id"])
        if "data-view" in attributes and attributes["data-view"]:
            self.view_keys.add(attributes["data-view"])
        if tag == "script":
            src = attributes.get("src")
            if src:
                self.external_scripts.append(src)
            else:
                self.inline_script_count += 1
        if tag == "style":
            self.inline_style_count += 1
        if tag == "link" and attributes.get("rel") == "stylesheet":
            href = attributes.get("href")
            if href:
                self.external_stylesheets.append(href)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_html(content: str) -> PrototypeHtmlParser:
    parser = PrototypeHtmlParser()
    parser.feed(content)
    return parser


def main() -> int:
    index_bytes = INDEX_HTML.read_bytes()
    standalone_bytes = STANDALONE_HTML.read_bytes()
    if index_bytes != standalone_bytes:
        raise AssertionError("prototype/index.html and prototype/standalone.html are not identical")

    html = standalone_bytes.decode("utf-8")
    parser = parse_html(html)

    required_views = {
        "map",
        "watchlist",
        "industries",
        "changes",
        "data",
        "evidence",
        "sync",
        "taxonomy",
        "models",
        "calibration",
        "architecture",
        "delivery",
        "ops",
        "governance",
    }
    missing_views = sorted(required_views - parser.view_keys)
    if missing_views:
        raise AssertionError(f"prototype missing views: {missing_views}")

    required_ids = {"nodeLayer", "edgeLayer", "focusTitle", "activeModelVersion"}
    missing_ids = sorted(required_ids - parser.ids)
    if missing_ids:
        raise AssertionError(f"prototype missing DOM anchors: {missing_ids}")

    if parser.external_scripts or parser.external_stylesheets:
        raise AssertionError(
            "canonical prototype must be standalone; stale external JS/CSS references found: "
            + json.dumps(
                {
                    "scripts": parser.external_scripts,
                    "stylesheets": parser.external_stylesheets,
                },
                ensure_ascii=False,
            )
        )

    if parser.inline_script_count < 1 or parser.inline_style_count < 1:
        raise AssertionError("prototype must contain inline script and style blocks")

    result = {
        "valid": True,
        "canonical_hash": sha256_bytes(standalone_bytes),
        "index_hash": sha256_bytes(index_bytes),
        "standalone_hash": sha256_bytes(standalone_bytes),
        "byte_count": len(standalone_bytes),
        "view_count": len(parser.view_keys),
        "inline_script_count": parser.inline_script_count,
        "inline_style_count": parser.inline_style_count,
        "external_scripts": parser.external_scripts,
        "external_stylesheets": parser.external_stylesheets,
    }
    print("Prototype parity validation: PASS")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, UnicodeDecodeError) as exc:
        print(f"Prototype parity validation: FAIL - {exc}")
        raise SystemExit(1) from None
