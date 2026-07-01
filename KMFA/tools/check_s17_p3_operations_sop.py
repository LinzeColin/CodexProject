#!/usr/bin/env python3
"""Validate KMFA S17-P3 operations SOP public-safe artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.operations_sop import (
    DEFAULT_OUTPUT_DRILL_LOG,
    DEFAULT_OUTPUT_KNOWLEDGE_INDEX,
    DEFAULT_OUTPUT_MANIFEST,
    DEFAULT_OUTPUT_RUNBOOKS,
    read_json,
    read_jsonl,
    validate_operations_sop_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S17-P3 operations SOP artifacts.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--runbooks", type=Path, default=DEFAULT_OUTPUT_RUNBOOKS)
    parser.add_argument("--knowledge-index", type=Path, default=DEFAULT_OUTPUT_KNOWLEDGE_INDEX)
    parser.add_argument("--drill-log", type=Path, default=DEFAULT_OUTPUT_DRILL_LOG)
    args = parser.parse_args(argv)

    manifest = read_json(args.manifest)
    runbooks = read_jsonl(args.runbooks)
    knowledge_items = read_jsonl(args.knowledge_index)
    drill_logs = read_jsonl(args.drill_log)

    validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, drill_logs)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S17-P3 operations SOP check passed "
        f"(runbooks={summary['operation_runbook_count']}, "
        f"knowledge_items={summary['knowledge_item_count']}, "
        f"drill_logs={summary['drill_log_count']}, "
        "metadata_only=true, manual_execution_only=true, "
        "stage17_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
