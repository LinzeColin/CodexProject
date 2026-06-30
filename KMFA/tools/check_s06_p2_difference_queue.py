#!/usr/bin/env python3
"""Validate KMFA S06-P2 cross-source difference queue evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.cross_source_difference_queue import CrossSourceDifferenceQueueError, validate_queue_item


DEFAULT_QUEUE_PATH = Path("KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl")
DEFAULT_GATE_PATH = Path("KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json")


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_queue(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        fail(f"queue evidence missing: {path}")
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        fail("queue evidence must contain at least one item")
    return records


def check_queue_and_gate(queue_path: Path, gate_path: Path) -> str:
    queue_items = load_queue(queue_path)
    for item in queue_items:
        try:
            validate_queue_item(item)
        except CrossSourceDifferenceQueueError as exc:
            fail(str(exc))

    if not gate_path.exists():
        fail(f"report grade gate evidence missing: {gate_path}")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    blocking_ids = [item["queue_id"] for item in queue_items if item.get("status") != "resolved"]
    if gate.get("stage_phase") != "S06-P2":
        fail("gate stage_phase mismatch")
    if blocking_ids:
        if gate.get("report_grade_a_allowed") is not False:
            fail("unclosed differences must block report grade A")
        if gate.get("maximum_report_grade") == "A":
            fail("maximum_report_grade must not be A while differences are unclosed")
        if gate.get("blocking_queue_ids") != blocking_ids:
            fail("blocking_queue_ids mismatch")
    return (
        "PASS: KMFA S06-P2 difference queue check passed "
        f"(queue_items={len(queue_items)}, report_grade_a_allowed={gate.get('report_grade_a_allowed')})"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA S06-P2 difference queue evidence.")
    parser.add_argument("--queue-jsonl", type=Path, default=DEFAULT_QUEUE_PATH)
    parser.add_argument("--gate-json", type=Path, default=DEFAULT_GATE_PATH)
    args = parser.parse_args(argv)
    print(check_queue_and_gate(args.queue_jsonl, args.gate_json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
