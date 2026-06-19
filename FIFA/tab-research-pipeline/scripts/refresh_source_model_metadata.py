#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tab_research.paths import resolve_output_dir
from tab_research.source_model_metadata import write_source_model_github_metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh public GitHub metadata for TAB FIFA open-source model references.")
    parser.add_argument("--output-dir", type=Path, default=resolve_output_dir(Path(__file__)))
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = write_source_model_github_metadata(args.output_dir, timeout_seconds=args.timeout_seconds)
    print(
        json.dumps(
            {
                "status": payload.get("status"),
                "artifact": "source_model_github_metadata_latest.json",
                "output_dir": str(args.output_dir),
                "source_count": payload.get("source_count"),
                "fetched_count": payload.get("fetched_count"),
                "failed_count": payload.get("failed_count"),
                "stars_total": payload.get("stars_total"),
                "open_issues_total": payload.get("open_issues_total"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload.get("fetched_count", 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
