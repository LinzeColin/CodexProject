#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S15-P2 performance review evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any, Iterator

from KMFA.tools import v014_s15_p2_post_remediation_performance_review_list as phase


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
    "person_name_plaintext",
    "salary_value",
    "bonus_value",
}
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "/Users/linzezhang/Downloads/",
    "KMFA_MetaData",
    "-----" "BEGIN PRIVATE KEY-----",
)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain an object")
    return value


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
    result = subprocess.run(
        ["git", "check-ignore", "-q", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _git_tracked(path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _walk(value: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _generated_public_paths() -> tuple[Path, ...]:
    return (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.FACT_SCHEMA_PATH,
        phase.FACT_TABLE_PATH,
        phase.ABNORMAL_METHOD_PATH,
        phase.REVIEW_ITEMS_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_FACT_SCHEMA_PATH,
        phase.METADATA_FACT_TABLE_PATH,
        phase.METADATA_ABNORMAL_METHOD_PATH,
        phase.METADATA_REVIEW_ITEMS_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _scan_public(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"public evidence missing: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    data = path.read_bytes()
    _require(b"\x00" not in data, f"binary public evidence: {path}", errors)
    text = data.decode("utf-8")
    for token in FORBIDDEN_PUBLIC_TEXT:
        _require(token not in text, f"forbidden public text in {path}: {token}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like text in {path}", errors)
    if path.suffix == ".json":
        payload = json.loads(text)
        for key, value in _walk(payload):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key in {path}: {key}", errors)
            if isinstance(value, float):
                errors.append(f"public float value in {path}: {key}")


def _expected_summary() -> dict[str, Any]:
    return {
        "required_field_count": 6,
        "s15_p1_manual_review_required_field_count": 6,
        "s15_p1_materialized_performance_fact_count": 0,
        "performance_fact_table_schema_count": 1,
        "performance_fact_table_column_count": 6,
        "performance_fact_row_count": 0,
        "authoritative_project_row_count": 0,
        "authoritative_value_binding_count": 0,
        "synthetic_project_row_count": 0,
        "public_business_value_count": 0,
        "abnormal_project_method_count": 1,
        "abnormal_project_rule_count": 6,
        "actual_abnormal_project_count": 0,
        "field_review_item_count": 6,
        "manual_review_required_item_count": 6,
        "project_specific_review_item_count": 0,
        "raw_source_file_count": 5,
        "private_xlsx_container_count": 48,
        "private_parseable_xlsx_count": 25,
        "private_unparseable_xlsx_count": 23,
        "private_parseable_sheet_count": 4198,
        "private_unique_candidate_sheet_count": 13,
        "private_multi_field_candidate_sheet_count": 3,
        "private_candidate_covered_field_count": 6,
        "private_probe_roundtrip_mismatch_count": 0,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "browser_status": "PASS",
        "baseline_html_control_row_count": 54,
        "baseline_html_pass_count": 54,
        "browser_viewport_check_count": 2,
        "review_item_interaction_check_count": 12,
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
        "decision": "NO_GO",
        "s15_p1_performed": True,
        "s15_p2_performed": True,
        "s15_p3_performed": False,
        "stage15_review_performed": False,
        "salary_calculation_performed": False,
        "bonus_approval_performed": False,
        "payroll_export_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_release_performed": False,
        "business_execution_performed": False,
    }


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _generated_public_paths():
        _scan_public(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    schema = _read_json(phase.FACT_SCHEMA_PATH)
    table = _read_json(phase.FACT_TABLE_PATH)
    abnormal = _read_json(phase.ABNORMAL_METHOD_PATH)
    review_document = _read_json(phase.REVIEW_ITEMS_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)

    _require(manifest.get("phase_id") == phase.PHASE_ID, "phase identity drift", errors)
    _require(manifest.get("roadmap_phase_id") == "S15-P2", "roadmap phase drift", errors)
    _require(manifest.get("task_id") == phase.TASK_ID, "task drift", errors)
    _require(manifest.get("acceptance_id") == phase.ACCEPTANCE_ID, "acceptance drift", errors)
    _require(manifest.get("version") == phase.VERSION, "version drift", errors)
    _require(manifest.get("status") == phase.STATUS, "status drift", errors)
    _require(manifest.get("decision") == "NO_GO", "decision drift", errors)
    _require(manifest.get("formula_id") == phase.FORMULA_ID, "formula identity drift", errors)
    _require(manifest.get("parameter_ids") == list(phase.PARAMETER_IDS), "parameter identities drift", errors)
    _require(manifest.get("model_registry_key") == phase.MODEL_REGISTRY_KEY, "model identity drift", errors)
    _require(manifest.get("summary") == summary, "summary mirror drift", errors)
    _require(manifest.get("performance_fact_table") == table, "fact table mirror drift", errors)
    _require(manifest.get("abnormal_project_method") == abnormal, "abnormal method mirror drift", errors)
    _require(manifest.get("review_items") == review_document.get("items"), "review item mirror drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "acceptance matrix mirror drift", errors)
    _require(manifest.get("go_no_go") == go_no_go, "go/no-go mirror drift", errors)
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundaries drift", errors)
    _require(manifest.get("raw_boundary") == phase._raw_boundary(), "raw boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety drift", errors)
    _require(manifest.get("next_phase") == "S15-P3", "next phase drift", errors)
    _require(manifest.get("s15_p1_post_remediation_dependency_validated") is True, "S15-P1 dependency missing", errors)
    _require(manifest.get("historical_s15_p2_fixture_validated") is True, "legacy fixture missing", errors)
    _require(
        manifest.get("historical_s15_p2_dynamic_rows_are_authoritative") is False,
        "legacy dynamic rows not quarantined",
        errors,
    )
    _require(manifest.get("historical_four_fact_rows_quarantined") is True, "legacy fact rows not quarantined", errors)
    _require(
        manifest.get("historical_sixteen_review_items_quarantined") is True,
        "legacy review items not quarantined",
        errors,
    )
    for key, value in _expected_summary().items():
        _require(summary.get(key) == value, f"summary {key} drift", errors)
    _require(summary.get("current_html_control_row_count", 0) >= 14, "current HTML audit too small", errors)
    _require(
        summary.get("current_html_control_row_count") == summary.get("current_html_pass_count"),
        "current HTML audit incomplete",
        errors,
    )

    _require(schema.get("column_count") == 6, "schema column count drift", errors)
    _require(schema.get("columns") == table.get("columns"), "schema/table columns drift", errors)
    _require([row.get("field_key") for row in schema.get("columns", [])] == list(phase.FIELD_KEYS), "column order drift", errors)
    _require(table.get("row_count") == 0 and table.get("rows") == [], "fact table must remain empty", errors)
    _require(table.get("row_materialization_allowed") is False, "fact row materialization opened", errors)
    _require(table.get("synthetic_project_row_count") == 0, "synthetic rows detected", errors)
    _require(abnormal.get("method_count") == 1, "abnormal method count drift", errors)
    _require(abnormal.get("rule_count") == 6, "abnormal rule count drift", errors)
    _require(abnormal.get("actual_abnormal_project_count") == 0, "actual abnormal projects detected", errors)
    _require(
        abnormal.get("current_output_status") == "blocked_no_authoritative_project_rows",
        "abnormal method status drift",
        errors,
    )
    reviews = review_document.get("items", [])
    _require(review_document.get("review_item_count") == 6 and len(reviews) == 6, "review count drift", errors)
    _require([row.get("field_key") for row in reviews] == list(phase.FIELD_KEYS), "review order drift", errors)
    for row in reviews:
        key = str(row.get("field_key"))
        _require(row.get("scope_type") == "field_level_authoritative_binding_review", f"{key} scope drift", errors)
        _require(row.get("manual_review_required") is True, f"{key} manual flag missing", errors)
        _require(row.get("current_status") == "pending_authoritative_binding", f"{key} status drift", errors)
        _require("project_ref" not in row, f"{key} project ref exposed", errors)
        _require(row.get("abnormal_project_claimed") is False, f"{key} abnormal claim drift", errors)
        _require(row.get("salary_or_bonus_action_allowed") is False, f"{key} compensation gate opened", errors)
    _require(matrix.get("check_count") == 20, "acceptance check count drift", errors)
    _require(matrix.get("check_pass_count") == 20, "acceptance pass count drift", errors)
    _require(matrix.get("check_fail_count") == 0, "acceptance failures detected", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision drift", errors)
    _require(go_no_go.get("performance_fact_release_allowed") is False, "fact release gate opened", errors)

    mirrors = (
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_FACT_SCHEMA_PATH, schema),
        (phase.METADATA_FACT_TABLE_PATH, table),
        (phase.METADATA_ABNORMAL_METHOD_PATH, abnormal),
        (phase.METADATA_REVIEW_ITEMS_PATH, review_document),
        (phase.METADATA_MATRIX_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    )
    for path, expected in mirrors:
        _require(_read_json(path) == expected, f"metadata mirror drift: {path}", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    if not phase.HTML_PATH.is_file():
        return
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "绩效复核清单工作台",
        "Q4 / D",
        "NO_GO",
        "事实行 0",
        "实际异常项目",
        "6 项复核",
        "暂无权威项目事实行",
        "不得自动填值，不得生成绩效分数、工资或奖金结论",
        "S15-P3",
        "table-layout:fixed",
        "overflow-x:auto",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    for spec in phase.FIELD_SPECS:
        _require(spec["label"] in text, f"field label missing: {spec['field_key']}", errors)
        _require(spec["reason_zh"] in text, f"Chinese reason missing: {spec['field_key']}", errors)
        _require(spec["reason_code"] not in text, f"internal reason exposed: {spec['field_key']}", errors)
    _require(text.count("data-review-button=") == 6, "review button count drift", errors)
    _require(text.count("data-review-panel=") == 6, "review panel count drift", errors)
    _require(text.count("data-dependency-link=") == 8, "dependency link count drift", errors)


def _expected_parameter_values(manifest: dict[str, Any]) -> dict[str, str]:
    summary = manifest["summary"]
    return {
        "PARAM-KMFA-1769": "1;6;0;0;0;0;0;1;6;0;6;6;0;4;16;Q4;D;NO_GO",
        "PARAM-KMFA-1770": "5;48;25;23;4198;13;6;0;3;9;2;1",
        "PARAM-KMFA-1771": (
            f"6;54;54;0;0;1;{summary['current_html_control_row_count']};"
            f"{summary['current_html_pass_count']};0;0;2;12;4;4;0;0"
        ),
        "PARAM-KMFA-1772": (
            "true;true;true;true;true;true;true;true;true;false;false;false;false;false;"
            "false;false;false;true;true;Q4;D;NO_GO"
        ),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "performance_fact_table_column_count == 6",
        "performance_fact_row_count == 0",
        "actual_abnormal_project_count == 0",
        "field_review_item_count == 6",
        "public_business_value_count == 0",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)

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
    if f'current_phase: "{phase.PHASE_ID}"' in version_matrix:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 S15-P3" in handoff, "HANDOFF S15-P3 route missing", errors)
        _require("不得执行 Stage 15 整体复审" in handoff, "HANDOFF Stage 15 boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S15-P2" in agents and "S15-P3" in agents, "AGENTS scope drift", errors)

    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in trace and phase.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery missing", errors)
    _require(f'snapshot_event_time: "{manifest["generated_at"]}"' in assurance, "assurance time drift", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "S15-P2 修补后绩效复核清单"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)

    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        matches = [row for row in rows if row.get("phase_id") == phase.PHASE_ID]
        _require(len(matches) == 1, f"governance JSONL row count drift: {path}", errors)
        if matches:
            _require(matches[0].get("status") == phase.STATUS, f"governance JSONL status drift: {path}", errors)


def _read_audit(path: Path, expected_files: int, expected_rows: int, errors: list[str]) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count drift: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"audit file count drift: {path}", errors)
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
        phase.PRIVATE_DIAGNOSTIC_PATH,
        phase.PRIVATE_REPORT_PATH,
    )
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p1.PRIVATE_RAW_AFTER_PATH)
        helper = phase.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
        current = helper._raw_snapshot("validate_v014_s15_p2_post_remediation_performance_review_list")
        normalize = helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-S15-P1 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
        expected = {
            "raw_source_file_count": 5,
            "private_xlsx_container_count": 48,
            "private_parseable_sheet_count": 4198,
            "private_unique_candidate_sheet_count": 13,
            "private_multi_field_candidate_sheet_count": 3,
            "private_candidate_covered_field_count": 6,
            "private_probe_roundtrip_mismatch_count": 0,
            "authoritative_project_row_count": 0,
            "authoritative_value_binding_count": 0,
            "performance_fact_row_count": 0,
            "actual_abnormal_project_count": 0,
            "field_review_item_count": 6,
            "legacy_fact_rows_quarantined": 4,
            "legacy_review_items_quarantined": 16,
            "raw_snapshot_exact_match": True,
            "raw_cross_phase_snapshot_exact_match": True,
        }
        for key, value in expected.items():
            _require(diagnostic.get(key) == value, f"private diagnostic {key} drift", errors)
        report = phase.PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("当前事实表只能输出结构", "六项字段级复核事项", "全中文最终差异报告"):
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
        _require(len(browser.get("review_item_interaction_checks", [])) == 12, "review interaction drift", errors)
        _require(len(browser.get("dependency_link_http_checks", [])) == 4, "HTTP count drift", errors)
        _require(len(browser.get("dependency_navigation_checks", [])) == 4, "navigation count drift", errors)
        _require(
            all(
                row.get("marker_visible")
                and row.get("quality_visible")
                and row.get("zero_fact_rows_visible")
                and row.get("six_review_items_visible")
                and row.get("stage_boundary_visible")
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow")
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / f"performance_review_{mode}.png"
        _require(path.is_file(), f"screenshot missing: {path}", errors)
        _require(_git_ignored(path), f"screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width drift: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


def validate_v014_s15_p2_post_remediation_performance_review_list(
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
    manifest = validate_v014_s15_p2_post_remediation_performance_review_list(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S15-P2 strict validation PASS: "
        f"columns={summary['performance_fact_table_column_count']} "
        f"fact_rows={summary['performance_fact_row_count']} "
        f"abnormal_projects={summary['actual_abnormal_project_count']} "
        f"review_items={summary['field_review_item_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
