#!/usr/bin/env python3
"""Simple repository guard for accidental runtime payload leakage.

This is not a privacy module; it protects deterministic repo state and avoids
mixing runtime evidence into code commits.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    re.compile("access" + r"_token", re.I),
    re.compile("app" + "secret", re.I),
    re.compile(r"webhook", re.I),
    re.compile(r"openDingTalkId", re.I),
    re.compile(r"userLatitude|userLongitude|baseLatitude|baseLongitude"),
]
SKIP_DIRS = {".git", "metadata", "private_runtime", "node_modules", ".venv", "venv"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("root", nargs="?", default=".")
    args = p.parse_args()
    root = Path(args.root)
    hits = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in PATTERNS:
            if pat.search(text):
                hits.append(str(path))
                break
    if hits:
        print("integrity_guard_hits:")
        for h in hits:
            print(f"- {h}")
        return 2
    print("integrity_guard_pass")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
