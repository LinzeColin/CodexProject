#!/usr/bin/env python3
"""Build KMFA S10-P2 public-safe report grade runtime metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_TEMPLATE_MANIFEST = ROOT / "metadata" / "reports" / "report_template_manifest.json"
DEFAULT_SCOPE_RECONCILIATION_MANIFEST = ROOT / "metadata" / "reports" / "project_scope_reconciliation_manifest.json"
DEFAULT_DATA_QUALITY_RESULTS = ROOT / "metadata" / "quality" / "data_quality_results.jsonl"
DEFAULT_ZERO_DELTA_RESULTS = ROOT / "metadata" / "quality" / "zero_delta_results.jsonl"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "report_grade_runtime_manifest.json"
DEFAULT_OUTPUT_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S10_P2_report_grade_runtime" / "machine" / "s10_p2_manifest.json"
)

REQUIRED_TEMPLATE_IDS = (
    "project_cost_special_report",
    "business_overview_report",
)

REPORT_RECORD_VERSION = "RPTREC-KMFA-S10P2-REPORT-GRADE-001"
FORMULA_VERSION = "FORM-KMFA-S10P2-REPORT-GRADE-RUNTIME-001"
MAPPING_VERSION = "MAP-KMFA-S10P2-PUBLIC-SAFE-v1"
FIELD_MAPPING_VERSION = "MAP-KMFA-S10P1-PUBLIC-SAFE-v1"
GRADE_POLICY_VERSION = "kmfa.report_grade_policy.v1"
RELEASE_GATE_VERSION = "kmfa.report_release_gate.v1"

QUALITY_RANK = {"Q0": 0, "Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4, "Q5": 5}
QUALITY_TO_MAX_REPORT_GRADE = {
    "Q0": "D",
    "Q1": "D",
    "Q2": "D",
    "Q3": "C",
    "Q4": "B",
    "Q5": "A",
}
GRADE_TO_RELEASE_PERMISSION = {
    "A": "formal_internal_report",
    "B": "internal_review_report",
    "C": "preview_only",
    "D": "blocked_decision_use",
}

FORBIDDEN_PUBLIC_KEYS = {
    "amount_cents",
    "amount_yuan",
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "raw_file_bytes",
    "original_filename",
    "private_csv",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "password",
    "token",
    "api_key",
    "private_key",
}

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db")

SOURCE_TASKPACK_REFS = {
    "roadmap_s10_p2": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S10-P2",
    "human_readable_report_spec": "KMFA/taskpack/v1_2/09_KMFA_前端交互与人类可读报告规范_v1_1.md:4",
    "data_quality_governance": "KMFA/taskpack/v1_2/05_KMFA_数据治理与质量门禁_v1_1.md:4",
}

UPSTREAM_METADATA_REFS = {
    "report_template_manifest": "source_ref://KMFA/S10-P1/report_template_manifest",
    "scope_reconciliation_manifest": "source_ref://KMFA/S09-P3/project_scope_reconciliation_manifest",
    "data_quality_results": "source_ref://KMFA/S06-P3/data_quality_results",
    "zero_delta_results": "source_ref://KMFA/S06-P3/zero_delta_results",
    "report_grade_policy": "source_ref://KMFA/S02-P3/report_grade_policy",
    "report_release_gate": "source_ref://KMFA/S02-P3/report_release_gate",
}


class ReportGradeRuntimeError(ValueError):
    """Raised when S10-P2 report grade runtime artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_values_committed": False,
        "normalized_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s10_p1_report_template_scope_included": False,
        "s10_p2_report_grade_scope_included": True,
        "s10_p3_export_scope_included": False,
        "report_grade_runtime_scope_included": True,
        "formal_report_runtime_scope_included": False,
        "full_trusted_report_scope_included": False,
        "lineage_full_check_scope_included": False,
        "ui_scope_included": False,
        "external_connector_scope_included": False,
        "stage10_review_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int) -> dict[str, Any]:
    return {
        "raw_layer_write_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_runtime_completed": True,
        "s10_p2_report_grade_runtime_allowed": True,
        "s10_p3_export_allowed": False,
        "html_export_allowed": False,
        "csv_excel_export_allowed": False,
        "pdf_export_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage10_review_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "unclosed_scope_reconciliations_and_missing_full_trust_evidence",
    }


def _load_default_inputs() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        read_json(DEFAULT_TEMPLATE_MANIFEST),
        read_json(DEFAULT_SCOPE_RECONCILIATION_MANIFEST),
        read_jsonl(DEFAULT_DATA_QUALITY_RESULTS),
        read_jsonl(DEFAULT_ZERO_DELTA_RESULTS),
    )


def _quality_grade_from_results(data_quality_results: list[dict[str, Any]]) -> str:
    grades = [
        str(record.get("quality_grade"))
        for record in data_quality_results
        if record.get("record_type") == "data_quality_result" and str(record.get("quality_grade")) in QUALITY_RANK
    ]
    if not grades:
        return "Q0"
    return min(grades, key=lambda grade: QUALITY_RANK[grade])


def _zero_delta_passed(zero_delta_results: list[dict[str, Any]]) -> tuple[bool, str]:
    result_records = [record for record in zero_delta_results if record.get("record_type") == "zero_delta_result"]
    if not result_records:
        return False, "missing"
    if any(record.get("zero_delta_passed") is False or record.get("status") != "passed" for record in result_records):
        return False, "failed"
    return True, "passed"


def _human_confirmation_status(scope_reconciliation_manifest: dict[str, Any]) -> str:
    summary = scope_reconciliation_manifest.get("summary", {})
    confirmed = int(summary.get("confirmed_resolution_count", 0))
    total = int(summary.get("reconciliation_record_count", 0))
    if total > 0 and confirmed >= total:
        return "complete"
    return "missing"


def _lineage_status(template_manifest: dict[str, Any]) -> str:
    if template_manifest.get("stage_scope", {}).get("lineage_full_check_scope_included") is True:
        return "available"
    return "missing_required_lineage"


def _hard_blocks(
    *,
    pending_reconciliation_count: int,
    zero_delta_passed: bool,
    human_confirmation_status: str,
    lineage_status: str,
) -> list[str]:
    blocks: list[str] = []
    if not zero_delta_passed:
        blocks.append("zero_delta_failed")
    if pending_reconciliation_count > 0:
        blocks.append("unresolved_critical_difference")
    if lineage_status != "available":
        blocks.append("missing_required_lineage")
    if human_confirmation_status != "complete":
        blocks.append("missing_human_confirmation_for_A")
    return blocks


def _compute_grade(*, source_quality_grade: str, hard_blocks: list[str]) -> tuple[str, str]:
    maximum_report_grade = QUALITY_TO_MAX_REPORT_GRADE.get(source_quality_grade, "D")
    if hard_blocks:
        return "D", maximum_report_grade
    return maximum_report_grade, maximum_report_grade


def _grade_record(
    *,
    template_id: str,
    template_manifest: dict[str, Any],
    source_quality_grade: str,
    zero_delta_passed: bool,
    zero_delta_status: str,
    pending_reconciliation_count: int,
    confirmed_resolution_count: int,
    human_confirmation_status: str,
    lineage_status: str,
    generated_at: str,
) -> dict[str, Any]:
    blocks = _hard_blocks(
        pending_reconciliation_count=pending_reconciliation_count,
        zero_delta_passed=zero_delta_passed,
        human_confirmation_status=human_confirmation_status,
        lineage_status=lineage_status,
    )
    computed_grade, maximum_report_grade = _compute_grade(
        source_quality_grade=source_quality_grade,
        hard_blocks=blocks,
    )
    full_trusted_allowed = computed_grade == "A" and not blocks
    business_decision_allowed = full_trusted_allowed
    return {
        "schema_version": "kmfa.report_grade_runtime_record.v1",
        "record_type": "report_grade_runtime_record",
        "project_id": "KMFA",
        "stage_phase": "S10-P2",
        "report_record_id": f"S10P2-GRADE-{template_id.upper().replace('_', '-')}",
        "report_record_version": REPORT_RECORD_VERSION,
        "template_id": template_id,
        "template_version": str(template_manifest.get("template_version")),
        "template_content_hash": str(template_manifest.get("content_hash")),
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "field_mapping_version": FIELD_MAPPING_VERSION,
        "grade_policy_version": GRADE_POLICY_VERSION,
        "release_gate_version": RELEASE_GATE_VERSION,
        "generated_at": generated_at,
        "grade_inputs": {
            "source_quality_grade": source_quality_grade,
            "zero_delta_passed": zero_delta_passed,
            "zero_delta_status": zero_delta_status,
            "unresolved_critical_difference_count": pending_reconciliation_count,
            "pending_reconciliation_count": pending_reconciliation_count,
            "confirmed_resolution_count": confirmed_resolution_count,
            "human_confirmation_status": human_confirmation_status,
            "lineage_status": lineage_status,
            "timeliness_status": "current_metadata_timestamp_present_no_stale_signal",
        },
        "maximum_report_grade_before_hard_blocks": maximum_report_grade,
        "computed_report_grade": computed_grade,
        "release_permission": GRADE_TO_RELEASE_PERMISSION[computed_grade],
        "hard_blocks": blocks,
        "complete_trusted_report_display_allowed": full_trusted_allowed,
        "full_trusted_report_allowed": full_trusted_allowed,
        "formal_report_allowed": full_trusted_allowed,
        "business_decision_basis_allowed": business_decision_allowed,
        "report_runtime_scope_included": True,
        "s10_p2_scope_included": True,
        "s10_p3_scope_included": False,
        "export_scope_included": False,
        "ui_scope_included": False,
        "lineage_full_check_included": False,
        "external_connector_included": False,
        "source_metadata_refs": list(UPSTREAM_METADATA_REFS.values()),
        "public_repo_safety": _public_repo_safety(),
        "limitations": [
            "存在未关闭授权复核差异时，不允许显示为完整可信报告。",
            "zero-delta 未通过时，不允许作为正式经营报告或经营决策依据。",
            "缺少完整 lineage 和人工确认时，只能保留阻断等级证据。",
        ],
    }


def build_default_report_grade_runtime_artifacts(
    *,
    generated_at: str = "2026-06-30T23:59:50+10:00",
    template_manifest: dict[str, Any] | None = None,
    scope_reconciliation_manifest: dict[str, Any] | None = None,
    data_quality_results: list[dict[str, Any]] | None = None,
    zero_delta_results: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if (
        template_manifest is None
        or scope_reconciliation_manifest is None
        or data_quality_results is None
        or zero_delta_results is None
    ):
        loaded_template, loaded_scope, loaded_quality, loaded_zero_delta = _load_default_inputs()
        template_manifest = template_manifest or loaded_template
        scope_reconciliation_manifest = scope_reconciliation_manifest or loaded_scope
        data_quality_results = data_quality_results or loaded_quality
        zero_delta_results = zero_delta_results or loaded_zero_delta

    scope_summary = scope_reconciliation_manifest.get("summary", {})
    pending_reconciliation_count = int(scope_summary.get("pending_resolution_count", 0))
    confirmed_resolution_count = int(scope_summary.get("confirmed_resolution_count", 0))
    source_quality_grade = _quality_grade_from_results(data_quality_results)
    zero_delta_passed, zero_delta_status = _zero_delta_passed(zero_delta_results)
    human_confirmation = _human_confirmation_status(scope_reconciliation_manifest)
    lineage = _lineage_status(template_manifest)

    records = [
        _grade_record(
            template_id=template_id,
            template_manifest=template_manifest,
            source_quality_grade=source_quality_grade,
            zero_delta_passed=zero_delta_passed,
            zero_delta_status=zero_delta_status,
            pending_reconciliation_count=pending_reconciliation_count,
            confirmed_resolution_count=confirmed_resolution_count,
            human_confirmation_status=human_confirmation,
            lineage_status=lineage,
            generated_at=generated_at,
        )
        for template_id in REQUIRED_TEMPLATE_IDS
    ]
    grade_distribution: dict[str, int] = {}
    for record in records:
        grade = str(record["computed_report_grade"])
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

    manifest = {
        "schema_version": "kmfa.report_grade_runtime_manifest.v1",
        "record_type": "report_grade_runtime_manifest",
        "project_id": "KMFA",
        "stage_phase": "S10-P2",
        "runtime_status": "public_safe_report_grades_locked_formal_report_blocked",
        "report_record_version": REPORT_RECORD_VERSION,
        "template_version": str(template_manifest.get("template_version")),
        "upstream_template_content_hash": str(template_manifest.get("content_hash")),
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "field_mapping_version": FIELD_MAPPING_VERSION,
        "grade_policy_version": GRADE_POLICY_VERSION,
        "release_gate_version": RELEASE_GATE_VERSION,
        "generated_at": generated_at,
        "required_template_ids": list(REQUIRED_TEMPLATE_IDS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(pending_reconciliation_count=pending_reconciliation_count),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "report_grade_runtime_manifest": "KMFA/metadata/reports/report_grade_runtime_manifest.json",
            "report_grade_runtime_records": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
            "validator": "KMFA/tools/check_s10_p2_report_grade_runtime.py",
            "completion_record": "KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/s10_p2_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S10_P2_report_grade_runtime/machine/s10_p2_manifest.json",
        },
        "summary": {
            "template_count": len(REQUIRED_TEMPLATE_IDS),
            "report_grade_record_count": len(records),
            "grade_distribution": grade_distribution,
            "pending_reconciliation_count": pending_reconciliation_count,
            "confirmed_resolution_count": confirmed_resolution_count,
            "source_quality_grade": source_quality_grade,
            "zero_delta_passed": zero_delta_passed,
            "full_trusted_report_allowed_count": sum(
                1 for record in records if record["full_trusted_report_allowed"] is True
            ),
            "formal_report_count": sum(1 for record in records if record["formal_report_allowed"] is True),
            "export_artifact_count": 0,
        },
        "limitations": [
            "S10-P2 只锁定报告可信等级，不执行 S10-P3 导出。",
            "存在待 owner 或授权复核差异时，完整可信报告继续阻断。",
            "本阶段不生成 HTML、CSV、Excel 或其他报告导出文件。",
        ],
    }
    manifest["content_hash"] = _sha256_json({"manifest": manifest, "records": records})
    return manifest, records


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ReportGradeRuntimeError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(lowered.endswith(suffix) or suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise ReportGradeRuntimeError(f"forbidden private business file reference found: {value}")


def _validate_record(record: dict[str, Any], manifest: dict[str, Any]) -> None:
    template_id = str(record.get("template_id", ""))
    if template_id not in REQUIRED_TEMPLATE_IDS:
        raise ReportGradeRuntimeError(f"unexpected template_id: {template_id}")
    if record.get("record_type") != "report_grade_runtime_record":
        raise ReportGradeRuntimeError(f"{template_id}.record_type mismatch")
    required_version_fields = (
        "report_record_version",
        "template_version",
        "template_content_hash",
        "formula_version",
        "mapping_version",
        "field_mapping_version",
        "grade_policy_version",
        "release_gate_version",
    )
    for field_name in required_version_fields:
        if not record.get(field_name):
            raise ReportGradeRuntimeError(f"{template_id}.{field_name} is required")
    if record.get("report_record_version") != REPORT_RECORD_VERSION:
        raise ReportGradeRuntimeError(f"{template_id}.report_record_version mismatch")
    for field_name in (
        "template_version",
        "formula_version",
        "mapping_version",
        "field_mapping_version",
        "grade_policy_version",
        "release_gate_version",
    ):
        if record.get(field_name) != manifest.get(field_name):
            raise ReportGradeRuntimeError(f"{template_id}.{field_name} must match manifest")
    if record.get("template_content_hash") != manifest.get("upstream_template_content_hash"):
        raise ReportGradeRuntimeError(f"{template_id}.template_content_hash must match manifest")

    hard_blocks = set(record.get("hard_blocks", []))
    if manifest.get("summary", {}).get("pending_reconciliation_count", 0) > 0:
        if "unresolved_critical_difference" not in hard_blocks:
            raise ReportGradeRuntimeError(f"{template_id} must carry unresolved_critical_difference")
    if record.get("grade_inputs", {}).get("zero_delta_passed") is False and "zero_delta_failed" not in hard_blocks:
        raise ReportGradeRuntimeError(f"{template_id} must carry zero_delta_failed")
    if record.get("grade_inputs", {}).get("lineage_status") != "available" and "missing_required_lineage" not in hard_blocks:
        raise ReportGradeRuntimeError(f"{template_id} must carry missing_required_lineage")
    if record.get("grade_inputs", {}).get("human_confirmation_status") != "complete":
        if "missing_human_confirmation_for_A" not in hard_blocks:
            raise ReportGradeRuntimeError(f"{template_id} must carry missing_human_confirmation_for_A")

    computed_grade = str(record.get("computed_report_grade", ""))
    if computed_grade not in {"A", "B", "C", "D"}:
        raise ReportGradeRuntimeError(f"{template_id}.computed_report_grade must be A/B/C/D")
    if hard_blocks and computed_grade != "D":
        raise ReportGradeRuntimeError(f"{template_id} must be D when hard blocks exist")
    if record.get("release_permission") != GRADE_TO_RELEASE_PERMISSION[computed_grade]:
        raise ReportGradeRuntimeError(f"{template_id}.release_permission mismatch")

    if computed_grade != "A":
        for field_name in (
            "complete_trusted_report_display_allowed",
            "full_trusted_report_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
        ):
            if record.get(field_name) is not False:
                raise ReportGradeRuntimeError(f"{template_id}.{field_name} must be false unless grade A")
    for field_name in (
        "s10_p3_scope_included",
        "export_scope_included",
        "ui_scope_included",
        "lineage_full_check_included",
        "external_connector_included",
    ):
        if record.get(field_name) is not False:
            raise ReportGradeRuntimeError(f"{template_id}.{field_name} must be false")
    if record.get("report_runtime_scope_included") is not True:
        raise ReportGradeRuntimeError(f"{template_id}.report_runtime_scope_included must be true")
    if record.get("s10_p2_scope_included") is not True:
        raise ReportGradeRuntimeError(f"{template_id}.s10_p2_scope_included must be true")
    for safety_key, expected in _public_repo_safety().items():
        if record.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise ReportGradeRuntimeError(f"{template_id}.public_repo_safety {safety_key} must be {expected}")


def validate_report_grade_runtime_artifacts(
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.report_grade_runtime_manifest.v1":
        raise ReportGradeRuntimeError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S10-P2":
        raise ReportGradeRuntimeError("manifest stage_phase must be S10-P2")
    if tuple(manifest.get("required_template_ids", [])) != REQUIRED_TEMPLATE_IDS:
        raise ReportGradeRuntimeError("manifest required_template_ids mismatch")
    if len(records) != len(REQUIRED_TEMPLATE_IDS):
        raise ReportGradeRuntimeError("report grade record count mismatch")

    summary = manifest.get("summary", {})
    expected_summary = {
        "template_count": 2,
        "report_grade_record_count": 2,
        "pending_reconciliation_count": 12,
        "confirmed_resolution_count": 0,
        "source_quality_grade": "Q4",
        "zero_delta_passed": False,
        "full_trusted_report_allowed_count": 0,
        "formal_report_count": 0,
        "export_artifact_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ReportGradeRuntimeError(f"manifest summary {key} must be {expected}")
    if summary.get("grade_distribution") != {"D": 2}:
        raise ReportGradeRuntimeError("manifest grade_distribution must be {'D': 2}")

    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise ReportGradeRuntimeError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12).items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise ReportGradeRuntimeError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise ReportGradeRuntimeError(f"manifest public_repo_safety {safety_key} must be {expected}")

    seen_template_ids: set[str] = set()
    for record in records:
        template_id = str(record.get("template_id", ""))
        if template_id in seen_template_ids:
            raise ReportGradeRuntimeError(f"duplicate template_id: {template_id}")
        seen_template_ids.add(template_id)
        _validate_record(record, manifest)
    if seen_template_ids != set(REQUIRED_TEMPLATE_IDS):
        raise ReportGradeRuntimeError("records do not cover all required templates")

    _ensure_no_forbidden_public_payload({"manifest": manifest, "records": records})


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ReportGradeRuntimeError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ReportGradeRuntimeError(f"{path} contains a non-object JSONL record")
            records.append(value)
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def write_default_report_grade_runtime_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_records: Path = DEFAULT_OUTPUT_RECORDS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    generated_at: str = "2026-06-30T23:59:50+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest, records = build_default_report_grade_runtime_artifacts(generated_at=generated_at)
    validate_report_grade_runtime_artifacts(manifest, records)
    _write_json(output_manifest, manifest)
    _write_jsonl(output_records, records)
    stage_manifest = {
        "schema_version": "kmfa.s10_p2_stage_manifest.v1",
        "record_type": "s10_p2_report_grade_runtime_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S10-P2",
        "generated_at": generated_at,
        "status": "completed_validated_local_only",
        "content_hash": manifest["content_hash"],
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "public_repo_safety": manifest["public_repo_safety"],
    }
    _write_json(output_stage_manifest, stage_manifest)
    return manifest, records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S10-P2 public-safe report grade runtime artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-records", type=Path, default=DEFAULT_OUTPUT_RECORDS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--generated-at", default="2026-06-30T23:59:50+10:00")
    args = parser.parse_args(argv)

    manifest, records = write_default_report_grade_runtime_artifacts(
        output_manifest=args.output_manifest,
        output_records=args.output_records,
        output_stage_manifest=args.output_stage_manifest,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S10-P2 report grade runtime artifacts generated "
        f"(grade_records={len(records)}, grade_distribution={summary['grade_distribution']}, "
        f"pending_reconciliation_count={summary['pending_reconciliation_count']}, "
        "complete_trusted_report_display_allowed=false, formal_report_allowed=false, "
        "s10_p3_scope=false, export_artifact_count=0)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
