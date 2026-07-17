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
    DEFAULT_PRIVATE_RECEIPT,
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
    parser.add_argument("--private-receipt", type=Path, default=DEFAULT_PRIVATE_RECEIPT)
    args = parser.parse_args(argv)

    manifest = load_json(args.manifest)
    candidates = load_jsonl(args.candidates)
    validate_a0_registration(
        manifest,
        candidates,
        require_member_sha256=args.require_member_sha256,
        private_receipt_path=args.private_receipt if args.require_member_sha256 else None,
    )
    summary = manifest["file_summary"]
    print(
        "PASS: KMFA A0 file registration check passed "
        f"(files={summary['total_files']}, pdf={summary['pdf_files']}, excel={summary['excel_files']}, "
        f"private_binding_verified={summary['private_binding_verified_count']}, "
        f"private_binding_required={summary['private_binding_required_count']}, candidates={len(candidates)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
