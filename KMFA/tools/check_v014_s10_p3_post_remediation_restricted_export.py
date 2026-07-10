#!/usr/bin/env python3
"""Validate the KMFA v0.1.4 S10-P3 post-remediation restricted exports."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s10_p3_post_remediation_restricted_export as phase
from KMFA.tools.check_v014_s10_p3_report_export import validate_v014_s10_p3_report_export


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "business_value",
    "amount_cents",
    "amount_yuan",
    "row_value",
    "cell_value",
    "sheet_name",
    "member_name",
    "original_filename",
    "file_hash",
    "field_key",
    "field_label",
    "source_header_text",
    "project_name_plaintext",
    "customer_name_plaintext",
    "authoritative_value_cents",
    "system_value_cents",
}
RAW_ROOT_TOKEN = "KMFA" + "_MetaData"
LOCAL_DOWNLOADS_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)
BUSINESS_AMOUNT_PATTERN = re.compile(r"(?:¥|￥|\bCNY\b|\bRMB\b|\d{1,3}(?:,\d{3})+\.\d{2})")
VISIBLE_TECHNICAL_TOKENS = ("validator", "manifest", "metadata", "source_ref", "private_ref", "S10-P3")
REQUIRED_HARD_BLOCKS = (
    "zero_delta_failed",
    "unresolved_critical_difference",
    "incomplete_reconciliation",
    "missing_required_lineage",
    "missing_human_confirmation_for_A",
    "full_business_value_consistency_not_verified",
)
VERSION_FIELDS = (
    "report_export_version",
    "report_entry_version",
    "report_grade_record_version",
    "template_version",
    "formula_version",
    "mapping_version",
    "field_mapping_version",
    "html_template_version",
    "csv_appendix_schema_version",
    "pdf_export_policy_version",
)
CSV_HEADERS = [
    "报告名称",
    "报告等级",
    "发布状态",
    "最终接受未决数",
    "非零差异数",
    "零差异数",
    "未完成比较数",
    "使用限制",
]


class ValidationError(Exception):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} must contain objects")
            rows.append(value)
    return rows


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked in {path}", errors)
    _require(LOCAL_DOWNLOADS_PATTERN.search(text) is None, f"local Downloads path leaked in {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        for key in _walk_keys(value):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key {key!r} in {path}", errors)


def _git_check_ignore(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", path.as_posix()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _validate_html(entry_id: str, text: str, errors: list[str]) -> None:
    _require(text.startswith("<!doctype html>"), f"HTML doctype missing: {entry_id}", errors)
    for token in (
        "D级",
        "未放行",
        "仅供内部复核",
        "关键现金数据缺失",
        "九项非零差异",
        "一项比较未完成",
        "下载CSV附表",
        "PDF导出未执行",
        "报告章节",
    ):
        _require(token in text, f"HTML visible token missing: {entry_id}:{token}", errors)
    if "D级" in text and "报告章节" in text:
        _require(text.index("D级") < text.index("报告章节"), f"D grade not first-view visible: {entry_id}", errors)
    for token in ("B级", "报告等级 B", *VISIBLE_TECHNICAL_TOKENS):
        _require(token not in text, f"forbidden visible token in HTML: {entry_id}:{token}", errors)
    _require(BUSINESS_AMOUNT_PATTERN.search(text) is None, f"business amount-like text in HTML: {entry_id}", errors)
    expected_href = "../csv/" + phase.CSV_PATHS[entry_id].name
    _require(f'href="{expected_href}"' in text, f"CSV download href mismatch: {entry_id}", errors)
    _require("window.print" not in text, f"public PDF execution leaked: {entry_id}", errors)


def _validate_csv(entry_id: str, text: str, errors: list[str]) -> None:
    _require(text.startswith("\ufeff"), f"CSV BOM missing: {entry_id}", errors)
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    _require(reader.fieldnames == CSV_HEADERS, f"CSV headers mismatch: {entry_id}", errors)
    rows = list(reader)
    _require(len(rows) == 1, f"CSV row count mismatch: {entry_id}", errors)
    if len(rows) != 1:
        return
    row = rows[0]
    expected = {
        "报告等级": "D级",
        "发布状态": "未放行",
        "最终接受未决数": "3",
        "非零差异数": "9",
        "零差异数": "2",
        "未完成比较数": "1",
    }
    for key, value in expected.items():
        _require(row.get(key) == value, f"CSV value mismatch: {entry_id}:{key}", errors)
    _require("仅供内部复核" in row.get("使用限制", ""), f"CSV usage limit missing: {entry_id}", errors)
    for token in VISIBLE_TECHNICAL_TOKENS:
        _require(token not in text, f"technical token in CSV: {entry_id}:{token}", errors)
    _require(BUSINESS_AMOUNT_PATTERN.search(text) is None, f"business amount-like text in CSV: {entry_id}", errors)


def validate_payloads(payloads: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    summary = payloads.get("summary", {})
    manifest = payloads.get("manifest", {})
    policy_document = payloads.get("policy", {})
    records_document = payloads.get("records", {})
    go_no_go = payloads.get("go_no_go", {})
    html_outputs = payloads.get("html_outputs", {})
    csv_outputs = payloads.get("csv_outputs", {})

    _require(
        manifest.get("schema_version") == "kmfa.v014.s10_p3.post_remediation_restricted_export_manifest.v1",
        "manifest schema mismatch",
        errors,
    )
    _require(manifest.get("stage_id") == "S10", "stage id mismatch", errors)
    _require(manifest.get("phase_id") == phase.PHASE_ID, "phase id mismatch", errors)
    _require(manifest.get("roadmap_phase_id") == "S10-P3", "roadmap phase mismatch", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "task id mismatch", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "acceptance id mismatch", errors)
    _require(manifest.get("status") == phase.STATUS, "status mismatch", errors)
    _require(manifest.get("decision") == "NO_GO", "decision mismatch", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("export_policy") == policy_document, "policy artifact drift", errors)
    _require(
        manifest.get("export_records") == records_document.get("export_records"),
        "records artifact drift",
        errors,
    )

    expected_summary = {
        "report_template_count": 2,
        "report_export_record_count": 2,
        "grade_distribution": {"D": 2},
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "html_restricted_preview_count": 2,
        "csv_restricted_appendix_count": 2,
        "excel_compatible_csv_download_count": 2,
        "committed_public_export_artifact_count": 4,
        "committed_pdf_file_count": 0,
        "committed_excel_workbook_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "raw_source_file_count": 5,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending count leaked into current summary", errors)
    for key in ("raw_snapshot_exact_match", "raw_cross_phase_snapshot_exact_match"):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)

    policy = manifest.get("export_policy", {})
    true_policy = (
        "html_restricted_preview_allowed",
        "csv_restricted_appendix_allowed",
        "excel_compatible_csv_download_allowed",
        "pdf_private_runtime_policy_available",
        "pdf_private_runtime_only",
    )
    false_policy = (
        "pdf_export_performed",
        "formal_report_export_allowed",
        "complete_trusted_report_display_allowed",
        "business_decision_basis_allowed",
        "delivery_allowed",
    )
    for key in true_policy:
        _require(policy.get(key) is True, f"export policy {key} must be true", errors)
    for key in false_policy:
        _require(policy.get(key) is False, f"export policy {key} must be false", errors)
    _require(policy.get("excel_download_mode") == "excel_compatible_csv_no_workbook", "Excel mode mismatch", errors)

    bindings = manifest.get("version_binding_requirements", {})
    expected_bindings = {
        "report_export_version": phase.REPORT_EXPORT_VERSION,
        "report_grade_record_version": p2_record_version(),
        "formula_version": phase.FORMULA_VERSION,
        "mapping_version": phase.MAPPING_VERSION,
        "html_template_version": phase.HTML_TEMPLATE_VERSION,
        "csv_appendix_schema_version": phase.CSV_APPENDIX_SCHEMA_VERSION,
        "pdf_export_policy_version": phase.PDF_EXPORT_POLICY_VERSION,
        "record_version_binding_count": 2,
    }
    for key, expected in expected_bindings.items():
        _require(bindings.get(key) == expected, f"version binding {key} mismatch", errors)
    for key in VERSION_FIELDS:
        _require(bool(bindings.get(key)), f"version binding missing: {key}", errors)

    records = manifest.get("export_records", [])
    _require(len(records) == 2, "export record count mismatch", errors)
    _require(len({record.get("report_entry_id") for record in records}) == 2, "export record ids not unique", errors)
    for record in records:
        entry_id = str(record.get("report_entry_id"))
        _require(record.get("report_grade") == "D", f"record grade mismatch: {entry_id}", errors)
        _require(record.get("visible_status_label") == "D级（未放行）", f"record status mismatch: {entry_id}", errors)
        _require(record.get("export_mode") == "restricted_internal_review_preview", f"record mode mismatch: {entry_id}", errors)
        _require(record.get("hard_blocks") == list(REQUIRED_HARD_BLOCKS), f"record blockers mismatch: {entry_id}", errors)
        _require(record.get("restricted_preview_export_allowed") is True, f"restricted export blocked: {entry_id}", errors)
        for key in (
            "complete_trusted_report_display_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
        ):
            _require(record.get(key) is False, f"record gate {key} must be false: {entry_id}", errors)
        for key in VERSION_FIELDS:
            _require(record.get(key) == bindings.get(key), f"record version drift: {entry_id}:{key}", errors)
        formats = record.get("export_formats", {})
        _require(formats.get("html", {}).get("status") == "restricted_public_safe_preview", f"HTML status mismatch: {entry_id}", errors)
        _require(formats.get("csv", {}).get("status") == "restricted_public_safe_download", f"CSV status mismatch: {entry_id}", errors)
        _require(formats.get("excel", {}).get("status") == "excel_compatible_csv_only", f"Excel status mismatch: {entry_id}", errors)
        _require(formats.get("excel", {}).get("workbook_committed") is False, f"workbook committed: {entry_id}", errors)
        _require(formats.get("pdf", {}).get("export_performed") is False, f"PDF performed: {entry_id}", errors)
        _require(formats.get("pdf", {}).get("file_committed") is False, f"PDF committed: {entry_id}", errors)
        safety = record.get("public_repo_safety", {})
        _require(safety.get("aggregate_only") is True, f"record not aggregate-only: {entry_id}", errors)
        _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), f"record safety drift: {entry_id}", errors)

    expected_ids = {"project_cost_special_report", "business_overview_report"}
    _require(set(html_outputs) == expected_ids, "HTML output ids mismatch", errors)
    _require(set(csv_outputs) == expected_ids, "CSV output ids mismatch", errors)
    for entry_id in expected_ids:
        if entry_id in html_outputs:
            _validate_html(entry_id, html_outputs[entry_id], errors)
        if entry_id in csv_outputs:
            _validate_csv(entry_id, csv_outputs[entry_id], errors)

    dependencies = manifest.get("dependencies", {})
    for key in (
        "current_s10_p1_entry_validated",
        "current_s10_p2_grade_lock_validated",
        "historical_s10_p3_export_framework_validated",
        "human_flow_baseline_validated",
        "current_s10_p2_state_authoritative",
    ):
        _require(dependencies.get(key) is True, f"dependency {key} must be true", errors)
    for key in (
        "historical_dynamic_state_reused",
        "human_flow_sample_dynamic_state_reused",
        "human_flow_sample_business_values_reused",
    ):
        _require(dependencies.get(key) is False, f"dependency {key} must be false", errors)

    boundaries = manifest.get("phase_boundaries", {})
    for key in ("s10_p1_performed", "s10_p2_performed", "s10_p3_performed"):
        _require(boundaries.get(key) is True, f"boundary {key} must be true", errors)
    for key in (
        "stage10_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)

    raw = manifest.get("raw_boundary", {})
    _require(raw.get("raw_read_authorized") is True, "raw authorization missing", errors)
    _require(raw.get("raw_snapshot_validation_performed") is True, "raw validation missing", errors)
    for key in (
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
        "raw_mutation_performed",
    ):
        _require(raw.get(key) is False, f"raw boundary {key} must be false", errors)

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence must be aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety drift", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("restricted_preview_exports_created") is True, "restricted exports missing", errors)
    for key in ("formal_report_allowed", "business_decision_basis_allowed", "stage10_review_performed", "github_upload_performed"):
        _require(go_no_go.get(key) is False, f"go/no-go {key} must be false", errors)

    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def p2_record_version() -> str:
    return phase.p2_phase.REPORT_RECORD_VERSION


def _load_public_payloads(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.POLICY_PATH,
        phase.RECORDS_PATH,
        phase.GO_NO_GO_PATH,
        phase.COMPLETION_PATH,
        phase.MANAGEMENT_README_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_POLICY_PATH,
        phase.METADATA_RECORDS_PATH,
        phase.METADATA_GO_NO_GO_PATH,
        *phase.HTML_PATHS.values(),
        *phase.CSV_PATHS.values(),
    )
    for path in public_paths:
        _check_public_file(path, errors)
    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    policy = _read_json(phase.POLICY_PATH)
    records = _read_json(phase.RECORDS_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(policy == _read_json(phase.METADATA_POLICY_PATH), "policy mirror drift", errors)
    _require(records == _read_json(phase.METADATA_RECORDS_PATH), "records mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    html_outputs = {entry_id: path.read_text(encoding="utf-8") for entry_id, path in phase.HTML_PATHS.items()}
    csv_outputs = {entry_id: path.read_text(encoding="utf-8") for entry_id, path in phase.CSV_PATHS.items()}
    forbidden_outputs = [
        path
        for path in phase.OUTPUT_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".xls", ".xlsx", ".zip", ".db", ".sqlite"}
    ]
    _require(not forbidden_outputs, f"forbidden export files found: {forbidden_outputs}", errors)
    return {
        "summary": summary,
        "manifest": manifest,
        "policy": policy,
        "records": records,
        "go_no_go": go_no_go,
        "html_outputs": html_outputs,
        "csv_outputs": csv_outputs,
    }


def _validate_dependencies(manifest: dict[str, Any], errors: list[str]) -> None:
    p1 = phase.p2_phase.validate_s10_p1_dependency()
    p2 = phase.validate_s10_p2_dependency()
    historical = validate_v014_s10_p3_report_export()
    baseline = phase._validate_human_flow_baseline()
    summary = manifest.get("summary", {})
    p2_summary = p2.get("summary", {})
    for key in (
        "open_final_difference_accepted_count",
        "nonzero_delta_reconciliation_count",
        "zero_delta_reconciliation_count",
        "incomplete_reconciliation_count",
        "hard_block_count",
        "current_data_quality_grade",
        "current_report_grade",
        "raw_source_file_count",
    ):
        _require(summary.get(key) == p2_summary.get(key), f"current S10-P2 dependency drift: {key}", errors)
    _require(len(p1.get("report_entries", [])) == 2, "current S10-P1 entry count drift", errors)
    historical_summary = historical.get("report_export_summary", {})
    _require(historical_summary.get("html_export_count") == 2, "historical HTML framework drift", errors)
    _require(historical_summary.get("csv_appendix_count") == 2, "historical CSV framework drift", errors)
    _require(baseline.get("structure_validated") is True, "human-flow baseline drift", errors)


def _validate_governance(errors: list[str]) -> None:
    events = _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
    stage_rows = _read_jsonl(phase.STAGE_STATUS_PATH)
    task_rows = _read_jsonl(phase.TASK_STATUS_PATH)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in events) == 1, "development event missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in stage_rows) == 1, "stage status missing or duplicated", errors)
    _require(sum(row.get("phase_id") == phase.PHASE_ID for row in task_rows) == 1, "task status missing or duplicated", errors)
    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    model_text = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    metadata_model_text = Path("KMFA/metadata/model_registry.yaml").read_text(encoding="utf-8")
    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameter_rows = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "restricted_html_count == 2",
        "restricted_csv_count == 2",
        "current_grade == D",
        "pdf_export_performed == false",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    _require(phase.MODEL_REGISTRY_KEY in model_text, "model registry record missing", errors)
    _require(phase.MODEL_REGISTRY_KEY in metadata_model_text, "metadata model registry record missing", errors)
    expected_values = {
        "PARAM-KMFA-1702": "2;2;2;2;4;Q4;D;3;9;2;1;12;0;0;0;0;5;NO_GO",
        "PARAM-KMFA-1703": "true;true;true;true;true;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1704": "true;true;true;true;false;true;true;true;false;false;false;false;false;false;false;false;false;false;NO_GO",
    }
    for parameter_id, expected in expected_values.items():
        row = parameter_rows.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)
    _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(f'current_phase: "{phase.PHASE_ID}"' in version_matrix, "VERSION_MATRIX current phase drift", errors)
    handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
    _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF current phase drift", errors)
    _require("Stage 10 整体复审" in handoff, "HANDOFF next review drift", errors)


def _read_audit(path: Path, errors: list[str], *, expected_files: int) -> None:
    _require(path.is_file(), f"browser audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(bool(rows), f"browser audit empty: {path}", errors)
    _require(sum(row.get("status") == "FAIL" for row in rows) == 0, f"browser audit failure: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"browser audit file count mismatch: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private_evidence(errors: list[str]) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_VALIDATION_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if any(not path.is_file() for path in private_paths):
        return
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(phase.p2_phase.PRIVATE_RAW_AFTER_PATH)
    current = phase._raw_snapshot("validate_v014_s10_p3_post_remediation_restricted_export")
    normalize = phase._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
    _require(normalize(after) == normalize(current), "raw current mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count mismatch", errors)


def _validate_browser_evidence(errors: list[str]) -> None:
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, expected_files=1)
    _read_audit(phase.PRIVATE_EXPORT_AUDIT_PATH, errors, expected_files=2)
    expected_screenshots = {
        "project_cost_special_report_desktop.png": (1440, None),
        "project_cost_special_report_mobile.png": (390, None),
        "business_overview_report_desktop.png": (1440, None),
        "business_overview_report_mobile.png": (390, None),
    }
    for name, (expected_width, _) in expected_screenshots.items():
        path = phase.PRIVATE_SCREENSHOT_DIR / name
        _require(path.is_file(), f"browser screenshot missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser screenshot tracked: {path}", errors)
        if path.is_file():
            try:
                width, height = _png_dimensions(path)
            except ValidationError as exc:
                errors.append(str(exc))
                continue
            _require(width == expected_width, f"screenshot width mismatch: {path}:{width}", errors)
            _require(height >= 700, f"screenshot height too small: {path}:{height}", errors)


def validate_v014_s10_p3_post_remediation_restricted_export(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    payloads = _load_public_payloads(errors)
    try:
        manifest = validate_payloads(payloads)
    except ValidationError as exc:
        errors.append(str(exc))
        manifest = payloads.get("manifest", {})
    _validate_dependencies(manifest, errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private_evidence(errors)
    if require_browser_evidence:
        _validate_browser_evidence(errors)
    if require_final_evidence:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in ("focused_tests", "strict_validator", "browser_desktop_mobile", "governance_and_safety_scans"):
            _require(validation.get(key) == "PASS", f"final validation status mismatch: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    try:
        manifest = validate_v014_s10_p3_post_remediation_restricted_export(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S10-P3 post-remediation restricted export "
        f"records={summary['report_export_record_count']} html={summary['html_restricted_preview_count']} "
        f"csv={summary['csv_restricted_appendix_count']} grade={summary['current_report_grade']} "
        f"decision={manifest['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
