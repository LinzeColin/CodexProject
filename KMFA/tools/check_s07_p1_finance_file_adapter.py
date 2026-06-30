#!/usr/bin/env python3
"""Validate KMFA S07-P1 finance file adapter artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.finance_file_adapter import (
    DEFAULT_OUTPUT_CANDIDATES,
    DEFAULT_OUTPUT_FIELD_REPORT,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_REGISTRY,
    validate_finance_adapter,
)


def read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_no} must contain a JSON object")
        records.append(payload)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S07-P1 finance file adapter artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_OUTPUT_CANDIDATES)
    parser.add_argument("--registry", type=Path, default=DEFAULT_OUTPUT_REGISTRY)
    parser.add_argument("--field-report", type=Path, default=DEFAULT_OUTPUT_FIELD_REPORT)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    candidates = read_jsonl(args.candidates)
    registry = read_json(args.registry)
    field_report = read_jsonl(args.field_report)
    validate_finance_adapter(manifest, candidates, field_report, registry=registry)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S07-P1 finance file adapter check passed "
        f"(categories={summary['source_category_count']}, "
        f"field_candidates={summary['field_candidate_count']}, "
        f"field_reports={summary['field_report_count']}, "
        f"source_header_hashes={summary['source_header_hash_count']}, "
        "wps_scope=false, redcircle_scope=false, formal_report_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
