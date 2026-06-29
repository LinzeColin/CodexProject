#!/usr/bin/env python3
"""Validate KMFA S05-P1 A0 file registration artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from KMFA.tools.a0_file_register import (
    DEFAULT_OUTPUT_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    validate_a0_registration,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S05-P1 A0 registration artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--require-member-sha256", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_json(args.manifest)
    candidates = load_jsonl(args.candidates)
    validate_a0_registration(manifest, candidates, require_member_sha256=args.require_member_sha256)
    summary = manifest["file_summary"]
    print(
        "PASS: KMFA A0 file registration check passed "
        f"(files={summary['total_files']}, pdf={summary['pdf_files']}, excel={summary['excel_files']}, "
        f"member_sha256_recorded={summary['member_sha256_recorded_count']}, "
        f"member_sha256_pending={summary['member_sha256_pending_count']}, candidates={len(candidates)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
