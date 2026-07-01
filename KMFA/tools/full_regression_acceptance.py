#!/usr/bin/env python3
"""Build KMFA S18-P2 public-safe full-regression acceptance artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "quality" / "full_regression_acceptance_manifest.json"
DEFAULT_OUTPUT_CHECKS = ROOT / "metadata" / "quality" / "full_regression_check_results.jsonl"
DEFAULT_OUTPUT_STAGE_EVIDENCE = ROOT / "metadata" / "quality" / "stage_acceptance_evidence_index.jsonl"
DEFAULT_OUTPUT_GO_NO_GO = ROOT / "metadata" / "quality" / "go_no_go_report.json"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S18_P2_full_regression_acceptance"
    / "machine"
    / "s18_p2_manifest.json"
)

POLICY_VERSION = "KMFA-S18P2-FULL-REGRESSION-ACCEPTANCE-001"
ITERATION_ID = "ITER-20260701-KMFA-S18P2-FULL-REGRESSION"

REQUIRED_CHECK_CATEGORIES = ("no_omission", "zero_delta", "schema", "lineage", "ui")
REQUIRED_STAGE_IDS = tuple(f"S{number:02d}" for number in range(1, 19))

CORE_HTML_SAMPLE_REFS = (
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/00_HTML总入口_KMFA_v1_2.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Resolution_Workbench_v0_4.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_Ring5_Final_Task_Control_Board.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_数据源检查板_v0_5_blue.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_系统首页预览_v4_blue.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_经营分析报告预览_v3_blue.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_阶段三任务控制台预览_v1_0.html",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html",
)

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "private_ref://",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)


class FullRegressionAcceptanceError(ValueError):
    """Raised when S18-P2 acceptance artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FullRegressionAcceptanceError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise FullRegressionAcceptanceError(f"{path} contains a non-object JSONL record")
        rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "private_tabular_material_committed": False,
        "source_document_committed": False,
        "field_text_committed": False,
        "true_money_committed": False,
        "true_customer_project_committed": False,
        "true_account_committed": False,
        "credential_committed": False,
        "private_document_committed": False,
        "raw_file_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "no_omission_check_passed": True,
        "zero_delta_check_ran": True,
        "zero_delta_or_difference_queue_gate_passed": True,
        "schema_check_passed": True,
        "lineage_check_ran": True,
        "lineage_full_check_complete": False,
        "ui_check_passed": True,
        "stage_evidence_confirmed": True,
        "go_no_go_report_generated": True,
        "official_report_release_allowed": False,
        "business_decision_basis_allowed": False,
        "quality_not_passed_must_not_deliver": True,
        "s09_pending_reconciliation_count": 12,
        "maximum_report_grade": "D",
        "raw_business_data_used": False,
        "raw_business_data_committed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "s18_p3_scope_included": False,
        "stage18_review_allowed": False,
        "external_connector_allowed": False,
        "production_restore_allowed": False,
        "business_execution_allowed": False,
        "release_block_reason": "no_go_lineage_full_check_and_official_report_release_not_complete",
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s18_p1_scope_included": False,
        "s18_p2_scope_included": True,
        "s18_p3_scope_included": False,
        "stage18_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "business_execution_scope_included": False,
    }


def _check_rows() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "s18_p2_regression_check_result",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PB",
            "stage_phase": "S18-P2",
            "check_category": "no_omission",
            "check_id": "S18P2-CHECK-NO-OMISSION",
            "command_ref": "PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py",
            "result": "passed",
            "acceptance_effect": "all P0/P1 and stage status records remain bound",
            "execution_mode": "public_safe_local_validation",
            "raw_business_data_used": False,
            "external_service_called": False,
            "github_upload_performed": False,
        },
        {
            "record_type": "s18_p2_regression_check_result",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PB",
            "stage_phase": "S18-P2",
            "check_category": "zero_delta",
            "check_id": "S18P2-CHECK-ZERO-DELTA",
            "command_ref": "PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py",
            "result": "passed_with_report_grade_block",
            "acceptance_effect": "zero-delta evidence exists and unresolved differences continue to block A-grade reports",
            "execution_mode": "public_safe_local_validation",
            "raw_business_data_used": False,
            "external_service_called": False,
            "github_upload_performed": False,
        },
        {
            "record_type": "s18_p2_regression_check_result",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PB",
            "stage_phase": "S18-P2",
            "check_category": "schema",
            "check_id": "S18P2-CHECK-SCHEMA",
            "command_ref": "json/jsonl/csv/yaml parse plus governance sync validators",
            "result": "passed",
            "acceptance_effect": "metadata, governance and schema-shaped artifacts parse and remain synchronized",
            "execution_mode": "public_safe_local_validation",
            "raw_business_data_used": False,
            "external_service_called": False,
            "github_upload_performed": False,
        },
        {
            "record_type": "s18_p2_regression_check_result",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PB",
            "stage_phase": "S18-P2",
            "check_category": "lineage",
            "check_id": "S18P2-CHECK-LINEAGE",
            "command_ref": "PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s12_p3_manual_rerun_mechanism.py",
            "result": "blocked_not_complete",
            "acceptance_effect": "manual rerun lineage evidence exists but full lineage completeness remains not implemented",
            "execution_mode": "public_safe_local_validation",
            "raw_business_data_used": False,
            "external_service_called": False,
            "github_upload_performed": False,
        },
        {
            "record_type": "s18_p2_regression_check_result",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "phase_id": "S18PB",
            "stage_phase": "S18-P2",
            "check_category": "ui",
            "check_id": "S18P2-CHECK-UI",
            "command_ref": "PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py",
            "result": "passed",
            "acceptance_effect": "v1.2 HTML/UIUX/report acceptance samples are present and inherited as acceptance baseline",
            "execution_mode": "public_safe_local_validation",
            "raw_business_data_used": False,
            "external_service_called": False,
            "github_upload_performed": False,
        },
    ]


def _stage_rows() -> list[dict[str, Any]]:
    uploaded_evidence = {
        "S01": "KMFA/stage_artifacts/S01_STAGE_REVIEW/human/stage1_review_report.md",
        "S02": "KMFA/stage_artifacts/S02_STAGE_REVIEW/human/test_results.md",
        "S03": "KMFA/stage_artifacts/S03_STAGE_REVIEW/human/github_upload_record.md",
        "S04": "KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md",
        "S05": "KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md",
        "S06": "KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md",
        "S07": "KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md",
        "S08": "KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md",
        "S09": "KMFA/stage_artifacts/S09_STAGE_REVIEW/human/github_upload_record.md",
        "S10": "KMFA/stage_artifacts/S10_STAGE_REVIEW/human/github_upload_record.md",
        "S11": "KMFA/stage_artifacts/S11_STAGE_REVIEW/human/github_upload_record.md",
        "S12": "KMFA/stage_artifacts/S12_GITHUB_UPLOAD/human/github_upload_record.md",
        "S13": "KMFA/stage_artifacts/S13_GITHUB_UPLOAD/human/github_upload_record.md",
        "S14": "KMFA/stage_artifacts/S14_GITHUB_UPLOAD/human/github_upload_record.md",
        "S15": "KMFA/stage_artifacts/S15_GITHUB_UPLOAD/human/github_upload_record.md",
        "S16": "KMFA/stage_artifacts/S16_GITHUB_UPLOAD/human/github_upload_record.md",
        "S17": "KMFA/stage_artifacts/S17_GITHUB_UPLOAD/human/github_upload_record.md",
    }
    rows: list[dict[str, Any]] = []
    for stage_id in REQUIRED_STAGE_IDS[:17]:
        rows.append(
            {
                "record_type": "s18_p2_stage_acceptance_evidence",
                "policy_version": POLICY_VERSION,
                "stage_id": stage_id,
                "stage_phase": "S18-P2",
                "status": "uploaded_to_github_main" if stage_id != "S01" else "completed",
                "review_or_phase_evidence_ref": uploaded_evidence[stage_id],
                "evidence_refs": [uploaded_evidence[stage_id]],
                "acceptance_confirmed": True,
                "raw_business_data_committed": False,
                "github_upload_performed_in_s18_p2": False,
            }
        )
    rows.append(
        {
            "record_type": "s18_p2_stage_acceptance_evidence",
            "policy_version": POLICY_VERSION,
            "stage_id": "S18",
            "stage_phase": "S18-P2",
            "status": "in_progress_s18p2_local_acceptance",
            "completed_phase_ids": ["S18-P1", "S18-P2"],
            "pending_phase_ids": ["S18-P3"],
            "review_or_phase_evidence_ref": "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/human/s18_p2_completion_record.md",
            "evidence_refs": [
                "KMFA/stage_artifacts/S18_P1_precision_stress/human/s18_p1_completion_record.md",
                "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/human/s18_p2_completion_record.md",
            ],
            "acceptance_confirmed": True,
            "raw_business_data_committed": False,
            "github_upload_performed_in_s18_p2": False,
        }
    )
    return rows


def _go_no_go() -> dict[str, Any]:
    return {
        "record_type": "s18_p2_go_no_go_report",
        "policy_version": POLICY_VERSION,
        "stage_id": "S18",
        "phase_id": "S18PB",
        "stage_phase": "S18-P2",
        "decision": "NO_GO",
        "decision_reason": "quality gates remain intentionally blocked until lineage full check, official report release and S18-P3 are complete",
        "blocker_ids": [
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "S09_PENDING_RECONCILIATION_12",
            "S18_P3_PENDING",
            "STAGE18_REVIEW_PENDING",
        ],
        "passed_check_categories": ["no_omission", "zero_delta", "schema", "ui"],
        "blocked_check_categories": ["lineage"],
        "delivery_allowed": False,
        "business_decision_basis_allowed": False,
        "official_report_release_allowed": False,
        "github_upload_allowed": False,
        "external_connector_allowed": False,
        "business_execution_allowed": False,
        "quality_not_passed_must_not_deliver": True,
        "next_required_phase": "S18-P3",
    }


def build_default_full_regression_acceptance_suite(
    *, generated_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    check_results = _check_rows()
    stage_evidence = _stage_rows()
    go_no_go = _go_no_go()
    manifest: dict[str, Any] = {
        "record_type": "s18_p2_full_regression_acceptance_manifest",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": "S18PB",
        "stage_phase": "S18-P2",
        "policy_version": POLICY_VERSION,
        "iteration_id": ITERATION_ID,
        "generated_at": generated_at,
        "fact_level": "EXTRACTED",
        "required_check_categories": list(REQUIRED_CHECK_CATEGORIES),
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "html_sample_acceptance": {
            "s18_samples_read": True,
            "core_sample_refs": list(CORE_HTML_SAMPLE_REFS),
            "reading_record_ref": "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/human/html_ui_regression_record.md",
        },
        "go_no_go": {
            "decision": go_no_go["decision"],
            "delivery_allowed": go_no_go["delivery_allowed"],
            "blocker_count": len(go_no_go["blocker_ids"]),
        },
        "metadata_outputs": {
            "full_regression_acceptance_manifest": "KMFA/metadata/quality/full_regression_acceptance_manifest.json",
            "full_regression_check_results": "KMFA/metadata/quality/full_regression_check_results.jsonl",
            "stage_acceptance_evidence_index": "KMFA/metadata/quality/stage_acceptance_evidence_index.jsonl",
            "go_no_go_report": "KMFA/metadata/quality/go_no_go_report.json",
        },
        "stage_artifact_ref": "KMFA/stage_artifacts/S18_P2_full_regression_acceptance/machine/s18_p2_manifest.json",
        "summary": {
            "check_category_count": len(check_results),
            "stage_evidence_count": len(stage_evidence),
            "go_no_go_decision": go_no_go["decision"],
            "blocker_count": len(go_no_go["blocker_ids"]),
            "html_sample_count": len(CORE_HTML_SAMPLE_REFS),
        },
    }
    content_for_hash = {
        "manifest_without_hash": manifest,
        "check_results": check_results,
        "stage_evidence": stage_evidence,
        "go_no_go": go_no_go,
    }
    manifest["content_hash"] = _sha256_json(content_for_hash)
    return manifest, check_results, stage_evidence, go_no_go


def _validate_no_forbidden_public_text(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden_text in FORBIDDEN_PUBLIC_TEXT:
        if forbidden_text in encoded:
            raise FullRegressionAcceptanceError(f"forbidden public text found: {forbidden_text}")


def validate_full_regression_acceptance_artifacts(
    manifest: dict[str, Any],
    check_results: list[dict[str, Any]],
    stage_evidence: list[dict[str, Any]],
    go_no_go: dict[str, Any],
) -> None:
    if manifest.get("stage_phase") != "S18-P2":
        raise FullRegressionAcceptanceError("manifest stage_phase must be S18-P2")
    if tuple(manifest.get("required_check_categories", ())) != REQUIRED_CHECK_CATEGORIES:
        raise FullRegressionAcceptanceError("manifest required_check_categories mismatch")
    categories = {row.get("check_category") for row in check_results}
    if categories != set(REQUIRED_CHECK_CATEGORIES):
        raise FullRegressionAcceptanceError(f"check categories mismatch: {sorted(categories)}")
    if len(check_results) != len(REQUIRED_CHECK_CATEGORIES):
        raise FullRegressionAcceptanceError("check result count mismatch")
    for row in check_results:
        if row.get("record_type") != "s18_p2_regression_check_result":
            raise FullRegressionAcceptanceError("invalid check record_type")
        if row.get("stage_phase") != "S18-P2":
            raise FullRegressionAcceptanceError("check row stage_phase must be S18-P2")
        if row.get("execution_mode") != "public_safe_local_validation":
            raise FullRegressionAcceptanceError("check row execution mode must be local public-safe")
        for flag in ("raw_business_data_used", "external_service_called", "github_upload_performed"):
            if row.get(flag) is not False:
                raise FullRegressionAcceptanceError(f"check row {row.get('check_id')} must keep {flag}=false")

    stage_ids = {row.get("stage_id") for row in stage_evidence}
    if stage_ids != set(REQUIRED_STAGE_IDS):
        raise FullRegressionAcceptanceError(f"stage evidence mismatch: {sorted(stage_ids)}")
    if len(stage_evidence) != len(REQUIRED_STAGE_IDS):
        raise FullRegressionAcceptanceError("stage evidence count mismatch")
    for row in stage_evidence:
        if row.get("record_type") != "s18_p2_stage_acceptance_evidence":
            raise FullRegressionAcceptanceError("invalid stage evidence record_type")
        if row.get("stage_phase") != "S18-P2":
            raise FullRegressionAcceptanceError("stage evidence stage_phase must be S18-P2")
        if row.get("acceptance_confirmed") is not True:
            raise FullRegressionAcceptanceError(f"{row.get('stage_id')} acceptance must be confirmed")
        if row.get("raw_business_data_committed") is not False:
            raise FullRegressionAcceptanceError(f"{row.get('stage_id')} must keep raw_business_data_committed=false")
        if row.get("github_upload_performed_in_s18_p2") is not False:
            raise FullRegressionAcceptanceError(f"{row.get('stage_id')} must not upload during S18-P2")

    if go_no_go.get("decision") != "NO_GO":
        raise FullRegressionAcceptanceError("S18-P2 Go/No-Go decision must remain NO_GO")
    if go_no_go.get("delivery_allowed") is not False:
        raise FullRegressionAcceptanceError("delivery_allowed must be false")
    if go_no_go.get("business_decision_basis_allowed") is not False:
        raise FullRegressionAcceptanceError("business_decision_basis_allowed must be false")
    if go_no_go.get("github_upload_allowed") is not False:
        raise FullRegressionAcceptanceError("github_upload_allowed must be false for intermediate phase")
    required_blockers = {
        "LINEAGE_FULL_CHECK_NOT_COMPLETE",
        "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
        "S09_PENDING_RECONCILIATION_12",
    }
    if not required_blockers.issubset(set(go_no_go.get("blocker_ids", []))):
        raise FullRegressionAcceptanceError("Go/No-Go blockers are incomplete")
    if manifest.get("summary", {}).get("check_category_count") != len(REQUIRED_CHECK_CATEGORIES):
        raise FullRegressionAcceptanceError("manifest summary check count mismatch")
    if manifest.get("summary", {}).get("stage_evidence_count") != len(REQUIRED_STAGE_IDS):
        raise FullRegressionAcceptanceError("manifest summary stage evidence count mismatch")
    if manifest.get("quality_gate", {}).get("lineage_full_check_complete") is not False:
        raise FullRegressionAcceptanceError("lineage_full_check_complete must remain false")
    if manifest.get("quality_gate", {}).get("official_report_release_allowed") is not False:
        raise FullRegressionAcceptanceError("official_report_release_allowed must remain false")
    for key in ("s18_p3_scope_included", "stage18_review_scope_included", "github_upload_scope_included"):
        if manifest.get("stage_scope", {}).get(key) is not False:
            raise FullRegressionAcceptanceError(f"{key} must remain false")
    _validate_no_forbidden_public_text([manifest, check_results, stage_evidence, go_no_go])


def write_full_regression_acceptance_artifacts(
    *,
    generated_at: str,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    checks_path: Path = DEFAULT_OUTPUT_CHECKS,
    stage_evidence_path: Path = DEFAULT_OUTPUT_STAGE_EVIDENCE,
    go_no_go_path: Path = DEFAULT_OUTPUT_GO_NO_GO,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    manifest, check_results, stage_evidence, go_no_go = build_default_full_regression_acceptance_suite(
        generated_at=generated_at
    )
    validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, go_no_go)
    write_json(manifest_path, manifest)
    write_jsonl(checks_path, check_results)
    write_jsonl(stage_evidence_path, stage_evidence)
    write_json(go_no_go_path, go_no_go)
    write_json(stage_manifest_path, manifest)
    return manifest, check_results, stage_evidence, go_no_go


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S18-P2 full-regression acceptance artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:59:59+10:00")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--checks", type=Path, default=DEFAULT_OUTPUT_CHECKS)
    parser.add_argument("--stage-evidence", type=Path, default=DEFAULT_OUTPUT_STAGE_EVIDENCE)
    parser.add_argument("--go-no-go", type=Path, default=DEFAULT_OUTPUT_GO_NO_GO)
    parser.add_argument("--stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    if args.check_only:
        manifest = read_json(args.manifest)
        check_results = read_jsonl(args.checks)
        stage_evidence = read_jsonl(args.stage_evidence)
        go_no_go = read_json(args.go_no_go)
        validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, go_no_go)
    else:
        manifest, check_results, stage_evidence, go_no_go = write_full_regression_acceptance_artifacts(
            generated_at=args.generated_at,
            manifest_path=args.manifest,
            checks_path=args.checks,
            stage_evidence_path=args.stage_evidence,
            go_no_go_path=args.go_no_go,
            stage_manifest_path=args.stage_manifest,
        )
    print(
        "PASS: generated S18-P2 full-regression acceptance artifacts "
        f"(checks={len(check_results)}, "
        f"stages={len(stage_evidence)}, "
        f"decision={go_no_go['decision']}, "
        "delivery_allowed=false, s18_p3=false, stage18_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
