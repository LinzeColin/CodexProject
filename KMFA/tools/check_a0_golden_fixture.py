#!/usr/bin/env python3
"""Validate KMFA S05-P2 A0 golden fixture candidate artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from KMFA.tools.a0_golden_fixture import (
    DEFAULT_OUTPUT_CANDIDATES,
    DEFAULT_OUTPUT_MANIFEST,
    validate_a0_golden_fixture,
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
    parser = argparse.ArgumentParser(description="Validate KMFA S05-P2 A0 golden fixture candidates.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--require-private-values", action="store_true")
    args = parser.parse_args(argv)

    manifest = load_json(args.manifest)
    candidates = load_jsonl(args.candidates)
    validate_a0_golden_fixture(manifest, candidates, require_private_values=args.require_private_values)
    summary = manifest["field_summary"]
    print(
        "PASS: KMFA A0 golden fixture check passed "
        f"(fixture_candidates={summary['fixture_candidate_count']}, "
        f"fields_per_candidate={summary['required_fields_per_candidate']}, "
        f"private_value_hash_recorded={summary['private_value_hash_recorded_count']}, "
        f"private_value_pending={summary['private_value_pending_count']}, "
        f"source_anchor_recorded={summary['source_anchor_recorded_count']}, "
        f"source_anchor_pending={summary['source_anchor_pending_count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
