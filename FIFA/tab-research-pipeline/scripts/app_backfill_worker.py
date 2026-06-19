#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PIPELINE_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe TAB FIFA backfill, then refresh Downloads app assets.")
    parser.add_argument("--max-backfill-runs", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backfill = subprocess.run(
        [
            sys.executable,
            "scripts/active_timeline_check.py",
            "--json",
            "--write-latest",
            "--backfill-missing",
            "--max-backfill-runs",
            str(max(args.max_backfill_runs, 0)),
        ],
        cwd=PIPELINE_ROOT,
        check=False,
    )
    refresh = subprocess.run(
        [sys.executable, "scripts/build_downloads_app_entry.py"],
        cwd=PIPELINE_ROOT,
        check=False,
    )
    return backfill.returncode if backfill.returncode != 0 else refresh.returncode


if __name__ == "__main__":
    raise SystemExit(main())
