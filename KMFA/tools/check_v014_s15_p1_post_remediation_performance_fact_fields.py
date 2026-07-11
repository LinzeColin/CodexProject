#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S15-P1 performance field evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any, Iterator

from KMFA.tools import v014_s15_p1_post_remediation_performance_fact_fields as phase


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".csv", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_root_private",
    "raw_path_private",
    "raw_filename_private",
    "raw_sha256",
    "member_name_private",
    "member_sha256",
    "sheet_name_private",
    "matched_terms_private",
    "preview_rows_private",
    "probe_fingerprint",
    "field_plaintext",
    "header_plaintext",
    "business_value",
    "business_amount",
    "project_name_plaintext",
    "customer_name_plaintext",
    "person_name_plaintext",
    "salary_value",
    "bonus_value",
}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|client[_-]?secret)"
        r"\s*[:=]\s*[\"'][^\"'\r\n]{8,}[\"']"
    ),
)
EXPECTED_CANDIDATE_COUNTS = {
    "invoice_amount": 9,
    "gross_margin_rate": 1,
    "settlement_speed": 2,
    "collection_speed": 4,
    "audit_variance": 2,
    "customer_relationship_rate": 2,
}


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _walk_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _walk_floats(value: Any) -> Iterator[float]:
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_floats(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_floats(item)


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(result.stderr.strip())
    return result.stdout.strip()


def _git_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", str(path)], check=False).returncode == 0


def _git_tracked(path: Path) -> bool:
    return bool(_git_output(["ls-files", "--", str(path)]))


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require("/Users/linzezhang/Downloads" not in text, f"local raw path leaked: {path}", errors)
    _require("KMFA_MetaData" not in text, f"raw root token leaked: {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token: {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        _require(not list(_walk_floats(value)), f"float found: {path}", errors)
        for key in _walk_keys(value):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key {key}: {path}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.FIELD_DEFINITIONS_PATH,
        phase.FIELD_BINDINGS_PATH,
        phase.MANUAL_REVIEW_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_FIELD_DEFINITIONS_PATH,
        phase.METADATA_FIELD_BINDINGS_PATH,
        phase.METADATA_MANUAL_REVIEW_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in paths:
        _check_public_file(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}

    manifest = _read_json(phase.MANIFEST_PATH)
    summary = manifest.get("summary", {})
    identity = {
        "project_id": "KMFA",
        "stage_id": "S15",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S15-P1",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": "NO_GO",
    }
    for key, expected in identity.items():
        _require(manifest.get(key) == expected, f"manifest {key} mismatch", errors)
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)

    expected_summary = {
        "stage14_post_remediation_review_dependency_validated": True,
        "taskpack_contract_validated": True,
        "required_field_count": 6,
        "field_definition_count": 6,
        "field_binding_status_count": 6,
        "manual_review_required_field_count": 6,
        "candidate_covered_field_count": 6,
        "private_candidate_sheet_count_by_field": EXPECTED_CANDIDATE_COUNTS,
        "project_cost_structure_reference_connected_field_count": 6,
        "collection_structure_reference_connected_field_count": 6,
        "authoritative_row_binding_proven_field_count": 0,
        "authoritative_value_binding_proven_field_count": 0,
        "materialized_performance_fact_count": 0,
        "public_business_value_count": 0,
        "workbench_html_count": 1,
        "raw_source_file_count": 5,
        "private_xlsx_container_count": 48,
        "private_parseable_xlsx_count": 25,
        "private_unparseable_xlsx_count": 23,
        "private_parseable_sheet_count": 4198,
        "private_unique_candidate_sheet_count": 13,
        "private_multi_field_candidate_sheet_count": 3,
        "private_probe_roundtrip_mismatch_count": 0,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "browser_status": "PASS",
        "baseline_html_control_row_count": 54,
        "baseline_html_pass_count": 54,
        "browser_viewport_check_count": 2,
        "field_interaction_check_count": 12,
        "dependency_link_http_check_count": 4,
        "dependency_navigation_check_count": 4,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "s15_p1_performed": True,
        "s15_p2_performed": False,
        "s15_p3_performed": False,
        "stage15_review_performed": False,
        "salary_calculation_performed": False,
        "bonus_approval_performed": False,
        "payroll_export_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)
    _require(summary.get("current_html_control_row_count", 0) > 0, "current HTML audit missing", errors)
    _require(
        summary.get("current_html_pass_count") == summary.get("current_html_control_row_count"),
        "current HTML audit incomplete",
        errors,
    )

    definitions_doc = _read_json(phase.FIELD_DEFINITIONS_PATH)
    bindings_doc = _read_json(phase.FIELD_BINDINGS_PATH)
    manual_doc = _read_json(phase.MANUAL_REVIEW_PATH)
    definitions = definitions_doc.get("fields", [])
    bindings = bindings_doc.get("bindings", [])
    manual = manual_doc.get("requirements", [])
    _require(definitions == manifest.get("field_definitions"), "definition mirror drift", errors)
    _require(bindings == manifest.get("field_binding_statuses"), "binding mirror drift", errors)
    _require(manual == manifest.get("manual_review_requirements"), "manual mirror drift", errors)
    _require([row.get("field_key") for row in definitions] == list(phase.FIELD_KEYS), "field order drift", errors)
    _require([row.get("field_key") for row in bindings] == list(phase.FIELD_KEYS), "binding order drift", errors)
    _require([row.get("field_key") for row in manual] == list(phase.FIELD_KEYS), "manual order drift", errors)

    for row in definitions:
        key = row.get("field_key")
        _require(row.get("private_candidate_sheet_count") == EXPECTED_CANDIDATE_COUNTS.get(key), f"{key} candidate count drift", errors)
        for true_key in (
            "required_by_roadmap",
            "project_cost_fact_reference_required",
            "collection_fact_reference_required",
            "private_candidate_structure_observed",
            "authoritative_row_binding_required",
            "authoritative_value_binding_required",
            "manual_review_required",
        ):
            _require(row.get(true_key) is True, f"{key} definition {true_key} must be true", errors)
        for false_key in ("field_value_materialized", "public_business_value_allowed", "salary_or_bonus_use_allowed"):
            _require(row.get(false_key) is False, f"{key} definition {false_key} must be false", errors)

    for row in bindings:
        key = row.get("field_key")
        _require(row.get("project_cost_structure_reference_connected") is True, f"{key} project ref missing", errors)
        _require(row.get("collection_structure_reference_connected") is True, f"{key} collection ref missing", errors)
        _require(row.get("private_candidate_sheet_count") == EXPECTED_CANDIDATE_COUNTS.get(key), f"{key} binding candidate drift", errors)
        _require(row.get("manual_review_required") is True, f"{key} manual flag missing", errors)
        for false_key in (
            "authoritative_row_binding_proven",
            "authoritative_value_binding_proven",
            "performance_fact_materialized",
            "candidate_as_fact_allowed",
            "auto_fill_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "salary_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
        ):
            _require(row.get(false_key) is False, f"{key} binding {false_key} must be false", errors)

    for row in manual:
        key = row.get("field_key")
        _require(row.get("manual_review_required") is True, f"{key} manual review missing", errors)
        _require(row.get("current_resolution_status") == "keep_pending_missing_authoritative_binding", f"{key} resolution drift", errors)
        for false_key in (
            "candidate_as_fact_allowed",
            "auto_fill_allowed",
            "auto_calculation_allowed",
            "auto_approval_allowed",
            "s15_p2_review_list_created",
            "salary_or_bonus_action_allowed",
        ):
            _require(row.get(false_key) is False, f"{key} manual {false_key} must be false", errors)

    _require(manifest.get("historical_s15_p1_fixture_validated") is True, "legacy fixture missing", errors)
    _require(
        manifest.get("historical_s15_p1_dynamic_binding_state_is_authoritative") is False,
        "legacy dynamic state must be false",
        errors,
    )
    _require(manifest.get("historical_two_non_manual_fields_quarantined") is True, "legacy fields not quarantined", errors)
    current = manifest.get("current_source_state", {})
    for key in (
        "financial_raw_value_bound_lane_count",
        "collection_row_level_binding_proven_lane_count",
        "collection_identified_business_item_count",
        "cross_table_comparable_dimension_count",
        "cross_table_exact_comparison_performed_count",
        "invoice_tax_value_binding_proven_lane_count",
    ):
        _require(current.get(key) == 0, f"current source state {key} drift", errors)
    _require(manifest.get("acceptance_matrix", {}).get("check_fail_count") == 0, "acceptance matrix failed", errors)
    _require(manifest.get("go_no_go") == _read_json(phase.GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    if not phase.HTML_PATH.is_file():
        return
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "绩效事实字段工作台",
        "Q4 / D",
        "NO_GO",
        "6 项待补证",
        "0 / 6",
        "S15-P2/P3",
        "不得计算绩效、工资或奖金",
        "table-layout:fixed",
        "overflow-wrap:anywhere",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    for label in phase.FIELD_LABELS.values():
        _require(label in text, f"field label missing: {label}", errors)
    for spec in phase.FIELD_SPECS:
        reason_zh = spec.get("reason_zh", "")
        _require(bool(reason_zh), f"Chinese review reason undefined: {spec['field_key']}", errors)
        _require(reason_zh in text, f"Chinese review reason missing: {spec['field_key']}", errors)
        _require(spec["reason_code"] not in text, f"internal reason code exposed in HTML: {spec['field_key']}", errors)
    _require(text.count("data-field-button=") == 6, "field button count mismatch", errors)
    _require(text.count("data-field-panel=") == 6, "field panel count mismatch", errors)
    _require(text.count("data-dependency-link=") == 8, "dependency link count mismatch", errors)


def _expected_parameter_values(manifest: dict[str, Any]) -> dict[str, str]:
    summary = manifest["summary"]
    return {
        "PARAM-KMFA-1765": (
            "6;6;6;6;6;6;6;0;0;0;0;13;3;3;9;2;1;Q4;D;NO_GO"
        ),
        "PARAM-KMFA-1766": "5;48;25;23;4198;9;1;2;4;2;2;13;3;6;0",
        "PARAM-KMFA-1767": (
            f"6;54;54;0;0;1;{summary['current_html_control_row_count']};"
            f"{summary['current_html_pass_count']};0;0;2;12;4;4;0;0"
        ),
        "PARAM-KMFA-1768": (
            "true;true;true;true;true;true;true;false;false;false;false;false;"
            "false;false;false;false;false;true;true;Q4;D;NO_GO"
        ),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    statuses = [row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    tasks = [row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list mismatch", errors)
        _require(events[0].get("manual_review_required_field_count") == 6, "event field count drift", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status drift", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance drift", errors)

    formula = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula, "formula missing", errors)
    for token in (
        "required_field_count == 6",
        "manual_review_required_field_count == 6",
        "authoritative_row_binding_proven_field_count == 0",
        "authoritative_value_binding_proven_field_count == 0",
        "materialized_performance_fact_count == 0",
        "private_probe_roundtrip_mismatch_count == 0",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula, f"formula control missing: {token}", errors)

    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model missing: {path}", errors)
        _require(phase.FORMULA_ID in text, f"formula ref missing: {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"parameter ref missing: {path}:{parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    for parameter_id, expected in _expected_parameter_values(manifest).items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    current_phase_is_s15_p1 = f'current_phase: "{phase.PHASE_ID}"' in version_matrix
    if current_phase_is_s15_p1:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 S15-P2" in handoff, "HANDOFF S15-P2 route missing", errors)
        _require("不得执行 S15-P3" in handoff, "HANDOFF S15-P3 boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S15-P1" in agents and "S15-P2" in agents, "AGENTS scope drift", errors)

    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in trace and phase.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery missing", errors)
    if current_phase_is_s15_p1:
        _require(
            f'snapshot_event_time: "{manifest["generated_at"]}"' in assurance,
            "assurance snapshot time drift",
            errors,
        )
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "S15-P1 修补后绩效事实字段"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, expected_files: int, expected_rows: int, errors: list[str]) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count mismatch: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"audit file count mismatch: {path}", errors)
    _require(all(row.get("status") == "PASS" for row in rows), f"audit non-pass row: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(manifest: dict[str, Any], errors: list[str], require_browser: bool) -> None:
    paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_PROBE_PATH,
        phase.PRIVATE_REPORT_PATH,
    )
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.s14_review.PRIVATE_RAW_AFTER_PATH)
        helper = phase.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
        current = helper._raw_snapshot("validate_v014_s15_p1_post_remediation_performance_fact_fields")
        normalize = helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-Stage14 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        probe = _read_json(phase.PRIVATE_PROBE_PATH)
        expected = {
            "raw_source_file_count": 5,
            "private_xlsx_container_count": 48,
            "private_parseable_xlsx_count": 25,
            "private_unparseable_xlsx_count": 23,
            "private_parseable_sheet_count": 4198,
            "private_candidate_sheet_count_by_field": EXPECTED_CANDIDATE_COUNTS,
            "private_unique_candidate_sheet_count": 13,
            "private_multi_field_candidate_sheet_count": 3,
            "private_candidate_covered_field_count": 6,
            "private_probe_roundtrip_mismatch_count": 0,
            "authoritative_row_binding_proven_field_count": 0,
            "authoritative_value_binding_proven_field_count": 0,
        }
        for key, value in expected.items():
            _require(probe.get(key) == value, f"private probe {key} drift", errors)
        _require(len(probe.get("candidate_sheets_private", [])) == 13, "private candidate rows drift", errors)
        report = phase.PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("六字段全部保持人工复核", "跨 Stage 14 review", "全中文最终差异报告"):
            _require(token in report, f"private report token missing: {token}", errors)

    if not require_browser:
        return
    summary = manifest["summary"]
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, 6, 54, errors)
    _read_audit(
        phase.PRIVATE_CURRENT_AUDIT_PATH,
        1,
        summary["current_html_control_row_count"],
        errors,
    )
    _require(phase.PRIVATE_BROWSER_PATH.is_file(), "browser evidence missing", errors)
    _require(_git_ignored(phase.PRIVATE_BROWSER_PATH), "browser evidence not ignored", errors)
    _require(not _git_tracked(phase.PRIVATE_BROWSER_PATH), "browser evidence tracked", errors)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status drift", errors)
        _require(len(browser.get("viewport_checks", [])) == 2, "browser viewport count drift", errors)
        _require(len(browser.get("field_interaction_checks", [])) == 12, "field interaction drift", errors)
        _require(len(browser.get("dependency_link_http_checks", [])) == 4, "HTTP count drift", errors)
        _require(len(browser.get("dependency_navigation_checks", [])) == 4, "navigation count drift", errors)
        _require(
            all(
                row.get("marker_visible")
                and row.get("d_no_go_visible")
                and row.get("manual_six_visible")
                and row.get("stage_boundary_visible")
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow")
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / f"performance_fact_fields_{mode}.png"
        _require(path.is_file(), f"screenshot missing: {path}", errors)
        _require(_git_ignored(path), f"screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width drift: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s15_p1_post_remediation_performance_fact_fields(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_html(errors)
    if manifest:
        phase._load_dependency()
        phase._load_contract()
        phase._load_legacy_fixture()
        phase._load_current_source_state()
        _validate_governance(manifest, errors)
    if require_private_evidence and manifest:
        _validate_private(manifest, errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "browser_desktop_mobile",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation {key} drift", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s15_p1_post_remediation_performance_fact_fields(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S15-P1 strict validation PASS: "
        f"fields={summary['field_definition_count']} "
        f"manual={summary['manual_review_required_field_count']} "
        f"bound={summary['authoritative_value_binding_proven_field_count']} "
        f"facts={summary['materialized_performance_fact_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
