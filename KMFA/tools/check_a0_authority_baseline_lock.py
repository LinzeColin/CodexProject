#!/usr/bin/env python3
"""Validate KMFA S05-P3 public-safe A0 authority baseline lock artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.a0_authority_baseline_lock import (
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RECORDS,
    validate_authority_baseline_lock,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S05-P3 authority baseline lock artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    args = parser.parse_args(argv)

    manifest = load_json(args.manifest)
    records = load_jsonl(args.records)
    validate_authority_baseline_lock(manifest, records)
    summary = manifest["lock_summary"]
    print(
        "PASS: KMFA S05-P3 authority baseline lock check passed "
        f"(q5_locked_fields={summary['q5_locked_field_count']}, "
        f"excluded_fields={summary['excluded_field_count']}, "
        f"authority_records={summary['authority_records']}, "
        f"formal_report_allowed={summary['formal_report_allowed']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
