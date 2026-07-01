#!/usr/bin/env python3
"""Validate KMFA whole-project final review evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_lineage_completeness import validate_lineage_completeness_review
from KMFA.tools.zero_delta_validator import validate_fixture_file


DEFAULT_MANIFEST = Path("KMFA/stage_artifacts/WHOLE_PROJECT_FINAL_REVIEW/machine/whole_project_final_review_manifest.json")
DEFAULT_GO_NO_GO = Path("KMFA/metadata/quality/whole_project_go_no_go_review.json")

PART_REVIEW_MANIFESTS = (
    "KMFA/stage_artifacts/PART1_STAGES_01_03_REVIEW/machine/part1_review_manifest.json",
    "KMFA/stage_artifacts/PART2_STAGES_04_06_REVIEW/machine/part2_review_manifest.json",
    "KMFA/stage_artifacts/PART3_STAGES_07_09_REVIEW/machine/part3_review_manifest.json",
    "KMFA/stage_artifacts/PART4_STAGES_10_12_REVIEW/machine/part4_review_manifest.json",
    "KMFA/stage_artifacts/PART5_STAGES_13_15_REVIEW/machine/part5_review_manifest.json",
    "KMFA/stage_artifacts/PART6_STAGES_16_18_REVIEW/machine/part6_review_manifest.json",
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


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, actual: Any) -> None:
    if actual is not True:
        raise ValueError(f"{label}: expected true, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        raise ValueError(f"{label}: expected false, got {actual!r}")


def _require_false_flags(label: str, payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or not payload:
        raise ValueError(f"{label}: expected non-empty object")
    for key, value in payload.items():
        _require_false(f"{label}.{key}", value)


def _require_existing_refs(refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        raise ValueError("evidence_refs: expected non-empty list")
    missing = [ref for ref in refs if not isinstance(ref, str) or not Path(ref).exists()]
    if missing:
        raise ValueError("missing evidence refs: " + ", ".join(map(str, missing)))


def _validate_no_forbidden_public_text(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for text in FORBIDDEN_PUBLIC_TEXT:
        if text in encoded:
            raise ValueError(f"forbidden public text found: {text}")


def _validate_part_manifests() -> None:
    expected_statuses = [
        "part_review_passed_local_only",
        "part_review_passed_local_only",
        "part_review_passed_local_only",
        "part_review_passed_local_only",
        "part_review_passed_local_only",
        "part_review_passed_local_only_no_go",
    ]
    for path_text, expected_status in zip(PART_REVIEW_MANIFESTS, expected_statuses):
        payload = _read_json(Path(path_text))
        _require_equal(f"{path_text}.schema_version", payload.get("schema_version"), "kmfa.part_review_manifest.v1")
        _require_equal(f"{path_text}.status", payload.get("status"), expected_status)
        _require_false(f"{path_text}.github_upload_performed", payload.get("github_upload_performed"))


def _validate_current_go_no_go(path: Path) -> dict[str, Any]:
    go_no_go = _read_json(path)
    _require_equal("go_no_go.schema_version", go_no_go.get("schema_version"), "kmfa.whole_project_go_no_go_review.v1")
    _require_equal("go_no_go.decision", go_no_go.get("status"), "no_go_delivery_blocked")
    _require_equal("go_no_go.project_id", go_no_go.get("project_id"), "KMFA")
    _require_equal("go_no_go.review_id", go_no_go.get("review_id"), "KMFA-WHOLE-PROJECT-FINAL-REVIEW-20260702")
    _require_false("go_no_go.delivery_allowed", go_no_go.get("delivery_allowed"))
    _require_false("go_no_go.official_report_release_allowed", go_no_go.get("official_report_release_allowed"))
    _require_false("go_no_go.github_upload_allowed", go_no_go.get("github_upload_allowed"))
    _require_false("go_no_go.external_connector_allowed", go_no_go.get("external_connector_allowed"))
    _require_false("go_no_go.business_decision_basis_allowed", go_no_go.get("business_decision_basis_allowed"))
    _require_false("go_no_go.business_execution_allowed", go_no_go.get("business_execution_allowed"))
    _require_false("go_no_go.lineage_full_check_complete", go_no_go.get("lineage_full_check_complete"))
    _require_true("go_no_go.quality_not_passed_must_not_deliver", go_no_go.get("quality_not_passed_must_not_deliver"))
    _require_true("go_no_go.stage18_github_upload_completed", go_no_go.get("stage18_github_upload_completed"))
    _require_true("go_no_go.stage18_upload_pending_blocker_removed", go_no_go.get("stage18_upload_pending_blocker_removed"))
    blockers = set(go_no_go.get("blocker_ids", []))
    _require_equal(
        "go_no_go.blocker_ids",
        blockers,
        {"LINEAGE_FULL_CHECK_NOT_COMPLETE", "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED", "S09_PENDING_RECONCILIATION_12"},
    )
    if "STAGE18_GITHUB_UPLOAD_PENDING" in blockers:
        raise ValueError("current Go/No-Go must not keep historical Stage 18 upload pending blocker")
    resolved = set(go_no_go.get("resolved_blocker_ids", []))
    if "STAGE18_GITHUB_UPLOAD_PENDING" not in resolved:
        raise ValueError("current Go/No-Go must record Stage 18 upload pending blocker as resolved")
    return go_no_go


def validate_whole_project_final_review(
    manifest_path: Path = DEFAULT_MANIFEST,
    go_no_go_path: Path = DEFAULT_GO_NO_GO,
) -> dict[str, int]:
    manifest = _read_json(manifest_path)
    go_no_go = _validate_current_go_no_go(go_no_go_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.whole_project_final_review_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-WHOLE-PROJECT-FINAL-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "whole_project_review_passed_local_only_no_go")
    _require_false("delivery_allowed", manifest.get("delivery_allowed"))
    _require_false("lineage_full_check_complete", manifest.get("lineage_full_check_complete"))
    _require_false("lineage_full_check_performed", manifest.get("lineage_full_check_performed"))
    _require_false("formal_report_generated", manifest.get("formal_report_generated"))
    _require_false("github_upload_performed_in_whole_review", manifest.get("github_upload_performed_in_whole_review"))
    _require_true("stage18_github_upload_completed", manifest.get("stage18_github_upload_completed"))
    _require_equal("open_review_finding_count", manifest.get("open_review_finding_count"), 0)
    _require_equal("open_launch_blocker_ids", set(manifest.get("open_launch_blocker_ids", [])), set(go_no_go["blocker_ids"]))
    _require_existing_refs(manifest.get("evidence_refs"))
    _require_false_flags("public_repo_safety", manifest.get("public_repo_safety", {}))

    counts = manifest.get("review_counts")
    if not isinstance(counts, dict):
        raise ValueError("review_counts: expected object")
    expected_counts = {
        "part_count": 6,
        "stage_count": 18,
        "phase_count": 54,
        "task_count": 162,
        "part_review_manifest_count": 6,
        "full_kmfa_unit_tests": 276,
        "taskpack_zero_delta_fixture_count": 1,
        "field_lineage_records": 1,
        "metric_lineage_records": 1,
        "report_lineage_records": 1,
        "manual_rerun_steps": 8,
        "manual_rerun_consistency_checks": 2,
        "s18_stage_acceptance_evidence": 18,
        "pending_reconciliation_count": 12,
        "open_launch_blocker_count": 3,
        "resolved_blocker_count": 3,
        "delivery_allowed_count": 0,
        "formal_report_count": 0,
        "github_upload_performed_in_whole_review_count": 0,
        "lineage_full_check_complete_count": 0,
    }
    for key, expected in expected_counts.items():
        _require_equal(f"review_counts.{key}", counts.get(key), expected)

    validators = manifest.get("validators_rerun")
    if not isinstance(validators, dict):
        raise ValueError("validators_rerun: expected object")
    for key, value in validators.items():
        _require_true(f"validators_rerun.{key}", value)

    _validate_part_manifests()
    validate_lineage_completeness_review()
    zero_delta = validate_fixture_file(Path("KMFA/metadata/fixtures/a0_project_cost_fixture.json"))
    _require_true("zero_delta.fixture.zero_delta_passed", zero_delta.get("zero_delta_passed"))
    _validate_no_forbidden_public_text([manifest, go_no_go])
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA whole-project final review evidence.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--go-no-go", type=Path, default=DEFAULT_GO_NO_GO)
    args = parser.parse_args(argv)

    try:
        counts = validate_whole_project_final_review(args.manifest, args.go_no_go)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA whole-project final review gate passed local-only with delivery NO_GO "
        f"(parts={counts['part_count']}, stages={counts['stage_count']}, "
        f"tests={counts['full_kmfa_unit_tests']}, blockers={counts['open_launch_blocker_count']}, "
        "delivery_allowed=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
