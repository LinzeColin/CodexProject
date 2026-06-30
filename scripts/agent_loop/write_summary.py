#!/usr/bin/env python3
"""Write a compact Agent Loop Markdown summary."""

from __future__ import annotations

import argparse
from pathlib import Path


def read(path: str | None) -> str:
    if not path:
        return "N/A\n"
    file_path = Path(path)
    if not file_path.exists():
        return "N/A\n"
    return file_path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--taskpack")
    parser.add_argument("--plan")
    parser.add_argument("--validation")
    parser.add_argument("--review")
    parser.add_argument("--architect")
    parser.add_argument("--merge")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    summary = [
        "# Agent Loop Summary",
        "",
        "## Task Pack",
        read(args.taskpack),
        "## Plan",
        read(args.plan),
        "## Validation",
        read(args.validation),
        "## Codex Review",
        read(args.review),
        "## Architect Review",
        read(args.architect),
        "## Merge Policy",
        read(args.merge),
    ]
    Path(args.output).write_text("\n".join(summary), encoding="utf-8")
    print(f"SUMMARY_WRITTEN={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
