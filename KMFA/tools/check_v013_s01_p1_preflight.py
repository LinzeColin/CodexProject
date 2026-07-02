#!/usr/bin/env python3
"""Validate KMFA v0.1.3 S01-P1 current-state preflight evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S01_PRECHECK/machine/s01_p1_preflight_manifest.json")
LINEAGE_REVIEW = Path("KMFA/metadata/quality/lineage_report_release_gate_review.json")
RECONCILIATION_RECORDS = Path("KMFA/metadata/quality/scope_reconciliation_records.jsonl")
REPORT_GRADE_RECORDS = Path("KMFA/metadata/reports/report_grade_runtime_records.jsonl")
LINEAGE_FILES = {
    "field": Path("KMFA/metadata/lineage/field_lineage.jsonl"),
    "metric": Path("KMFA/metadata/lineage/metric_lineage.jsonl"),
    "report": Path("KMFA/metadata/lineage/report_lineage.jsonl"),
}
EVIDENCE_FILES = [
    Path("KMFA/stage_artifacts/V013_S01_PRECHECK/human/status_summary.md"),
    Path("KMFA/stage_artifacts/V013_S01_PRECHECK/human/blocker_inventory.md"),
    Path("KMFA/stage_artifacts/V013_S01_PRECHECK/human/preflight_results.md"),
]
FORBIDDEN_EVIDENCE_TEXT = (
    "raw_value",
    "normalized_value",
    "source_header_text",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "-----BEGIN",
    "sk-",
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path}:{line_no} must contain a JSON object")
        rows.append(value)
    return rows


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def actual_lineage_rows() -> int:
    total = 0
    for path in LINEAGE_FILES.values():
        total += sum(1 for row in read_jsonl(path) if row.get("record_type") != "protocol_header")
    return total


def pending_reconciliation_count() -> int:
    return sum(
        1
        for row in read_jsonl(RECONCILIATION_RECORDS)
        if row.get("resolution_status") == "pending_owner_or_authorized_review"
        and row.get("confirmed_for_rerun") is False
        and row.get("closed_at") is None
    )


def d_grade_report_count() -> int:
    return sum(1 for row in read_jsonl(REPORT_GRADE_RECORDS) if row.get("computed_report_grade") == "D")


def validate_s01_p1_preflight(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    manifest = read_json(manifest_path)
    lineage_review = read_json(LINEAGE_REVIEW)

    require(manifest.get("schema_version") == "kmfa.v013_s01_p1_preflight.v1", "manifest schema mismatch")
    require(manifest.get("project_id") == "KMFA", "manifest project_id mismatch")
    require(manifest.get("stage_phase") == "S01-P1", "manifest stage_phase must be S01-P1")
    require(manifest.get("task_id") == "KMFA-V013-S01-P1-CURRENT-STATE-PREFLIGHT-20260702", "task_id mismatch")
    require(manifest.get("phase_scope") == "current_state_review_only", "phase_scope mismatch")
    require(manifest.get("business_code_modified") is False, "S01-P1 must not modify business code")
    require(manifest.get("github_upload_this_phase") is False, "S01-P1 must not upload GitHub")
    require(manifest.get("delivery_allowed") is False, "delivery_allowed must remain false")
    require(manifest.get("formal_report_allowed") is False, "formal_report_allowed must remain false")
    require(manifest.get("business_execution_allowed") is False, "business_execution_allowed must remain false")

    blockers = manifest.get("blocker_counts", {})
    require(blockers.get("actual_lineage_rows") == actual_lineage_rows() == 0, "actual lineage rows must remain 0")
    require(blockers.get("pending_reconciliation_count") == pending_reconciliation_count() == 12, "pending reconciliation count must be 12")
    require(blockers.get("d_grade_report_count") == d_grade_report_count() == 2, "D grade report count must be 2")
    require(blockers.get("delivery_allowed") is False, "blocker delivery_allowed must be false")

    require(lineage_review.get("delivery_allowed") is False, "lineage report gate delivery_allowed must be false")
    require(lineage_review.get("formal_report_allowed") is False, "lineage report gate formal_report_allowed must be false")
    require(lineage_review.get("business_execution_allowed") is False, "lineage report gate business_execution_allowed must be false")

    for ref in manifest.get("source_evidence_refs", []):
        require(isinstance(ref, str) and Path(ref).exists(), f"missing source evidence ref: {ref}")
    for evidence in EVIDENCE_FILES:
        require(evidence.exists(), f"missing human evidence: {evidence}")
        text = evidence.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_EVIDENCE_TEXT:
            require(forbidden not in text, f"forbidden evidence text {forbidden!r} in {evidence}")

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "task_id": manifest["task_id"],
        "stage_phase": manifest["stage_phase"],
        "current_version_file_value": manifest["current_version_file_value"],
        "governance_product_version": manifest["governance_product_version"],
        "actual_lineage_rows": blockers["actual_lineage_rows"],
        "pending_reconciliation_count": blockers["pending_reconciliation_count"],
        "d_grade_report_count": blockers["d_grade_report_count"],
        "delivery_allowed": manifest["delivery_allowed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 S01-P1 current-state preflight evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_s01_p1_preflight(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S01-P1 preflight validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S01-P1 preflight remains NO_GO "
        f"(version_file={result['current_version_file_value']}, "
        f"governance_version={result['governance_product_version']}, "
        f"actual_lineage_rows={result['actual_lineage_rows']}, "
        f"pending_reconciliation={result['pending_reconciliation_count']}, "
        f"grade_D={result['d_grade_report_count']}, "
        f"delivery_allowed={str(result['delivery_allowed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
