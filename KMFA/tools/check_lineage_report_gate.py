#!/usr/bin/env python3
"""Validate the KMFA lineage/report release gate decision package."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_REVIEW = Path("KMFA/metadata/quality/lineage_report_release_gate_review.json")
DEFAULT_STAGE_MANIFEST = Path(
    "KMFA/stage_artifacts/LINEAGE_REPORT_GATE/machine/lineage_report_gate_manifest.json"
)

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)

LINEAGE_FILES = {
    "field": Path("KMFA/metadata/lineage/field_lineage.jsonl"),
    "metric": Path("KMFA/metadata/lineage/metric_lineage.jsonl"),
    "report": Path("KMFA/metadata/lineage/report_lineage.jsonl"),
}

REPORT_GRADE_RECORDS = Path("KMFA/metadata/reports/report_grade_runtime_records.jsonl")
REPORT_EXPORT_RECORDS = Path("KMFA/metadata/reports/report_export_records.jsonl")
RECONCILIATION_RECORDS = Path("KMFA/metadata/quality/scope_reconciliation_records.jsonl")
RECONCILIATION_MANIFEST = Path("KMFA/metadata/reports/project_scope_reconciliation_manifest.json")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no} must contain a JSON object")
        rows.append(value)
    return rows


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, actual: Any) -> None:
    if actual is not True:
        raise ValueError(f"{label}: expected true, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        raise ValueError(f"{label}: expected false, got {actual!r}")


def _require_non_empty_list(label: str, value: Any) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label}: expected non-empty list")
    return value


def _require_false_flags(label: str, payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{label}: expected non-empty object")
    for key, value in payload.items():
        _require_false(f"{label}.{key}", value)


def _require_existing_refs(label: str, refs: Any) -> None:
    missing = [
        ref
        for ref in _require_non_empty_list(label, refs)
        if not isinstance(ref, str) or not Path(ref).exists()
    ]
    if missing:
        raise ValueError(f"{label}: missing refs: " + ", ".join(map(str, missing)))


def _validate_no_forbidden_public_text(label: str, payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for text in FORBIDDEN_PUBLIC_TEXT:
        if text in encoded:
            raise ValueError(f"{label}: forbidden public text found: {text}")


def _lineage_counts() -> dict[str, int]:
    result: dict[str, int] = {}
    for kind, path in LINEAGE_FILES.items():
        rows = _read_jsonl(path)
        headers = [row for row in rows if row.get("record_type") == "protocol_header"]
        actual = [row for row in rows if row.get("record_type") != "protocol_header"]
        result[f"{kind}_protocol_header_count"] = len(headers)
        result[f"{kind}_actual_lineage_record_count"] = len(actual)
    return result


def _report_grade_summary() -> dict[str, Any]:
    records = _read_jsonl(REPORT_GRADE_RECORDS)
    distribution = Counter(str(row.get("computed_report_grade")) for row in records)
    hard_blocks: set[str] = set()
    for row in records:
        for block in row.get("hard_blocks", []):
            hard_blocks.add(str(block))
    return {
        "runtime_report_count": len(records),
        "report_grade_distribution": dict(sorted(distribution.items())),
        "formal_report_allowed_count": sum(1 for row in records if row.get("formal_report_allowed") is True),
        "business_decision_basis_allowed_count": sum(
            1 for row in records if row.get("business_decision_basis_allowed") is True
        ),
        "complete_trusted_report_display_allowed_count": sum(
            1 for row in records if row.get("complete_trusted_report_display_allowed") is True
        ),
        "hard_blocks": sorted(hard_blocks),
    }


def _report_export_summary() -> dict[str, Any]:
    records = _read_jsonl(REPORT_EXPORT_RECORDS)
    release_permissions = Counter(str(row.get("release_permission")) for row in records)
    return {
        "report_export_record_count": len(records),
        "release_permission_distribution": dict(sorted(release_permissions.items())),
        "formal_report_allowed_count": sum(1 for row in records if row.get("formal_report_allowed") is True),
        "business_decision_basis_allowed_count": sum(
            1 for row in records if row.get("business_decision_basis_allowed") is True
        ),
    }


def _reconciliation_summary() -> dict[str, Any]:
    manifest = _read_json(RECONCILIATION_MANIFEST)
    records = _read_jsonl(RECONCILIATION_RECORDS)
    manifest_summary = manifest.get("summary", {})
    quality_gate = manifest.get("quality_gate", {})
    pending = [
        row
        for row in records
        if row.get("resolution_status") == "pending_owner_or_authorized_review"
        and row.get("confirmed_for_rerun") is False
        and row.get("closed_at") is None
    ]
    return {
        "reconciliation_record_count": len(records),
        "pending_resolution_count": len(pending),
        "confirmed_resolution_count": int(manifest_summary.get("confirmed_resolution_count", -1)),
        "closed_resolution_count": sum(1 for row in records if row.get("closed_at") is not None),
        "derived_metric_rerun_allowed": quality_gate.get("derived_metric_rerun_allowed"),
        "formal_report_allowed": quality_gate.get("formal_report_allowed"),
    }


def _expected_summary() -> dict[str, Any]:
    return {
        "lineage_summary": {
            **_lineage_counts(),
            "lineage_full_check_complete": False,
            "lineage_full_check_performed": False,
            "lineage_protocol_only": True,
        },
        "report_grade_summary": _report_grade_summary(),
        "report_export_summary": _report_export_summary(),
        "reconciliation_summary": _reconciliation_summary(),
    }


def _validate_review(review: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_equal("schema_version", review.get("schema_version"), "kmfa.lineage_report_release_gate_review.v1")
    _require_equal("project_id", review.get("project_id"), "KMFA")
    _require_equal(
        "gate_id",
        review.get("gate_id"),
        "KMFA-LINEAGE-REPORT-GATE-PENDING_OWNER_SCOPE-20260702",
    )
    _require_equal("status", review.get("status"), "blocked_no_go_owner_scope_required")
    _require_false("delivery_allowed", review.get("delivery_allowed"))
    _require_false("official_report_release_allowed", review.get("official_report_release_allowed"))
    _require_false("formal_report_allowed", review.get("formal_report_allowed"))
    _require_false("business_decision_basis_allowed", review.get("business_decision_basis_allowed"))
    _require_false("release_claim_allowed", review.get("release_claim_allowed"))
    _require_false("github_upload_allowed", review.get("github_upload_allowed"))
    _require_false("external_connector_allowed", review.get("external_connector_allowed"))
    _require_false("business_execution_allowed", review.get("business_execution_allowed"))

    backup_policy = review.get("github_backup_upload_policy_under_no_go")
    if not isinstance(backup_policy, dict):
        raise ValueError("github_backup_upload_policy_under_no_go: expected object")
    _require_true(
        "github_backup_upload_policy_under_no_go.allowed_after_rebase_and_validators",
        backup_policy.get("allowed_after_rebase_and_validators"),
    )
    _require_false(
        "github_backup_upload_policy_under_no_go.release_claim_allowed",
        backup_policy.get("release_claim_allowed"),
    )
    _require_false(
        "github_backup_upload_policy_under_no_go.delivery_claim_allowed",
        backup_policy.get("delivery_claim_allowed"),
    )
    if len(_require_non_empty_list("github_backup_upload_policy_under_no_go.conditions", backup_policy.get("conditions"))) < 5:
        raise ValueError("github_backup_upload_policy_under_no_go.conditions: expected at least five conditions")

    for key, value in expected.items():
        _require_equal(key, review.get(key), value)

    blockers = set(review.get("blocker_ids", []))
    _require_equal(
        "blocker_ids",
        blockers,
        {
            "LINEAGE_PROTOCOL_ONLY_NO_FULL_FIELD_METRIC_REPORT_ROWS",
            "S09_PENDING_RECONCILIATION_12",
            "REPORT_GRADE_D_BLOCKED_DECISION_USE",
            "ZERO_DELTA_OR_RECONCILIATION_HARD_BLOCKS_PRESENT",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
        },
    )
    _require_existing_refs("source_refs", review.get("source_refs"))
    _require_existing_refs("evidence_refs", review.get("evidence_refs"))
    _require_false_flags("public_repo_safety", review.get("public_repo_safety", {}))
    _validate_no_forbidden_public_text("lineage_report_release_gate_review", review)


def validate_lineage_report_gate(
    review_path: Path = DEFAULT_REVIEW,
    stage_manifest_path: Path = DEFAULT_STAGE_MANIFEST,
) -> dict[str, Any]:
    review = _read_json(review_path)
    stage_manifest = _read_json(stage_manifest_path)
    expected = _expected_summary()
    _validate_review(review, expected)

    _require_equal("stage_manifest.schema_version", stage_manifest.get("schema_version"), "kmfa.lineage_report_gate_manifest.v1")
    _require_equal("stage_manifest.project_id", stage_manifest.get("project_id"), "KMFA")
    _require_equal("stage_manifest.gate_id", stage_manifest.get("gate_id"), review["gate_id"])
    _require_equal("stage_manifest.status", stage_manifest.get("status"), review["status"])
    _require_equal("stage_manifest.review_ref", stage_manifest.get("review_ref"), str(review_path))
    _require_false("stage_manifest.github_upload_performed", stage_manifest.get("github_upload_performed"))
    _require_false("stage_manifest.delivery_allowed", stage_manifest.get("delivery_allowed"))
    _require_equal("stage_manifest.summary", stage_manifest.get("summary"), expected)
    _require_existing_refs("stage_manifest.evidence_refs", stage_manifest.get("evidence_refs"))
    _require_false_flags("stage_manifest.public_repo_safety", stage_manifest.get("public_repo_safety", {}))
    _validate_no_forbidden_public_text("lineage_report_gate_stage_manifest", stage_manifest)
    return expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA lineage/report gate blocked decision package.")
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--stage-manifest", type=Path, default=DEFAULT_STAGE_MANIFEST)
    args = parser.parse_args(argv)

    try:
        summary = validate_lineage_report_gate(args.review, args.stage_manifest)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    report_count = summary["report_grade_summary"]["runtime_report_count"]
    pending = summary["reconciliation_summary"]["pending_resolution_count"]
    print(
        "PASS: KMFA lineage/report gate remains blocked and public-safe "
        f"(reports={report_count}, grade_D={summary['report_grade_summary']['report_grade_distribution'].get('D')}, "
        f"pending_reconciliation={pending}, actual_lineage_rows=0, delivery_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
