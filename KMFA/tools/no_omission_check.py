#!/usr/bin/env python3
"""KMFA no-omission baseline check.

This check is intentionally local and deterministic. It verifies that the
imported TaskPack requirements bind P0/P1 items to Stage/Phase/Task status,
acceptance gates, tests, and evidence references without relying on external
services or raw sensitive business data.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "metadata" / "traceability" / "requirements.csv"
STAGE_STATUS = ROOT / "metadata" / "stage_status.jsonl"

REQUIRED_REQUIREMENT_COLUMNS = {
    "requirement_id",
    "priority",
    "theme",
    "requirement",
    "covered_stages",
    "task_ids",
    "acceptance_gate",
    "test_or_evidence",
    "evidence_ref",
    "status",
    "source_file",
}

REQUIRED_STATUS_FIELDS = {"record_type", "status", "updated_at", "fact_level"}
EXPECTED_COUNTS = {"P0": 9, "P1": 8}
PUBLIC_REPO_FORBIDDEN_SUFFIXES = {
    ".zip",
    ".xls",
    ".xlsx",
    ".pdf",
    ".sqlite",
    ".db",
    ".sqlite-shm",
    ".sqlite-wal",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def split_values(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").replace(",", ";").split(";") if item.strip()]


def load_requirements() -> list[dict[str, str]]:
    if not REQUIREMENTS.exists():
        fail(f"missing requirements matrix: {REQUIREMENTS.relative_to(ROOT)}")
    with REQUIREMENTS.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_REQUIREMENT_COLUMNS - columns)
        if missing:
            fail("requirements.csv missing columns: " + ", ".join(missing))
        rows = list(reader)
    if not rows:
        fail("requirements.csv has no rows")
    return rows


def load_status_records() -> tuple[set[str], set[str], set[str], list[dict[str, object]]]:
    if not STAGE_STATUS.exists():
        fail(f"missing stage status registry: {STAGE_STATUS.relative_to(ROOT)}")
    records: list[dict[str, object]] = []
    for line_no, line in enumerate(STAGE_STATUS.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSONL at stage_status.jsonl:{line_no}: {exc}")
        missing = sorted(REQUIRED_STATUS_FIELDS - set(record))
        if missing:
            fail(f"stage_status.jsonl:{line_no} missing fields: {', '.join(missing)}")
        records.append(record)
    if not records:
        fail("stage_status.jsonl has no records")

    roadmap_stage_ids: set[str] = set()
    governance_stage_ids: set[str] = set()
    stage_ids: set[str] = set()
    phase_ids: set[str] = set()
    task_ids: set[str] = set()
    for record in records:
        if record.get("record_type") == "stage":
            if record.get("roadmap_stage_id"):
                roadmap_stage_ids.add(str(record["roadmap_stage_id"]))
                stage_ids.add(str(record["roadmap_stage_id"]))
            if record.get("governance_stage_id"):
                governance_stage_ids.add(str(record["governance_stage_id"]))
                stage_ids.add(str(record["governance_stage_id"]))
        elif record.get("record_type") == "phase" and record.get("phase_id"):
            phase_ids.add(str(record["phase_id"]))
        elif record.get("record_type") == "task" and record.get("task_id"):
            task_ids.add(str(record["task_id"]))

    if len(roadmap_stage_ids) != 18:
        fail(f"expected 18 roadmap stage ids, found {len(roadmap_stage_ids)}")
    if len(governance_stage_ids) != 18:
        fail(f"expected 18 governance stage ids, found {len(governance_stage_ids)}")
    if len(phase_ids) != 54:
        fail(f"expected 54 phase records, found {len(phase_ids)}")
    if len(task_ids) != 162:
        fail(f"expected 162 task records, found {len(task_ids)}")
    return stage_ids, phase_ids, task_ids, records


def check_requirements(rows: list[dict[str, str]], stage_ids: set[str], task_ids: set[str]) -> None:
    ids = [row["requirement_id"].strip() for row in rows]
    duplicates = [req_id for req_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        fail("duplicate requirement_id values: " + ", ".join(sorted(duplicates)))

    priority_counts = Counter(row["priority"].strip() for row in rows)
    for priority, expected in EXPECTED_COUNTS.items():
        actual = priority_counts.get(priority, 0)
        if actual != expected:
            fail(f"expected {expected} {priority} requirements, found {actual}")

    for row in rows:
        req_id = row["requirement_id"].strip()
        priority = row["priority"].strip()
        if priority not in {"P0", "P1", "P2"}:
            fail(f"{req_id}: invalid priority {priority!r}")
        if priority not in {"P0", "P1"}:
            continue

        for field in ("theme", "requirement", "covered_stages", "task_ids", "acceptance_gate", "test_or_evidence", "evidence_ref", "status"):
            if not str(row.get(field, "")).strip():
                fail(f"{req_id}: missing {field}")

        covered_stages = split_values(row["covered_stages"])
        missing_stages = [stage_id for stage_id in covered_stages if stage_id not in stage_ids]
        if missing_stages:
            fail(f"{req_id}: covered stages missing from stage registry: {', '.join(missing_stages)}")

        bound_tasks = split_values(row["task_ids"])
        missing_tasks = [task_id for task_id in bound_tasks if task_id not in task_ids]
        if missing_tasks:
            fail(f"{req_id}: task bindings missing from stage registry: {', '.join(missing_tasks[:10])}")

        if len(bound_tasks) < len(covered_stages):
            fail(f"{req_id}: fewer task bindings than covered stages")


def check_no_raw_sensitive_files() -> None:
    matches = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in PUBLIC_REPO_FORBIDDEN_SUFFIXES:
            matches.append(str(path.relative_to(ROOT)))
    if matches:
        fail("forbidden raw/sensitive file-like artifacts under KMFA: " + ", ".join(matches[:20]))


def main() -> int:
    rows = load_requirements()
    stage_ids, _phase_ids, task_ids, records = load_status_records()
    check_requirements(rows, stage_ids, task_ids)
    check_no_raw_sensitive_files()
    priority_counts = Counter(row["priority"].strip() for row in rows)
    print(
        "PASS: KMFA no omission check passed "
        f"(requirements={len(rows)}, P0={priority_counts.get('P0', 0)}, "
        f"P1={priority_counts.get('P1', 0)}, status_records={len(records)}, tasks={len(task_ids)})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
