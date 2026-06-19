#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tab_research.paths import resolve_output_dir
from tab_research.public_snapshot_importer import publish_public_snapshot_raw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Publish a manually signed Public Snapshot preview into the formal Matches raw slot. "
            "This is scope-only, writes no 5-board batch manifest, and never unlocks betting execution."
        )
    )
    parser.add_argument("--output-dir", type=Path, default=resolve_output_dir(Path(__file__)))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = publish_public_snapshot_raw(args.output_dir)
    stream = sys.stdout if payload.get("ok") else sys.stderr
    print(json.dumps(payload, indent=2, ensure_ascii=False), file=stream)
    return 0 if payload.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
