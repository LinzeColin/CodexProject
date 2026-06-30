#!/usr/bin/env python3
"""Validate and normalize a Codex result pack artifact."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_SECTIONS = [
    "Summary",
    "Files Changed",
    "Acceptance Criteria",
    "Validation Commands",
    "Changed Files Policy",
    "Review",
    "Autofix",
    "Merge Policy",
    "Known Risks",
    "Rollback Plan",
]


def has_section(text: str, heading: str) -> bool:
    return bool(re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.I | re.M))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-pack", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    text = Path(args.result_pack).read_text(encoding="utf-8", errors="ignore")
    missing = [section for section in REQUIRED_SECTIONS if not has_section(text, section)]
    if missing:
        print("RESULT_PACK_VALIDATION=FAIL")
        for section in missing:
            print(f"- missing section: {section}")
        return 1

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print("RESULT_PACK_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
