#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S14-P1 evidence."""

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

from KMFA.tools import v014_s14_p1_post_remediation_fund_cash_loan_plan as phase


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xls", ".xlsx", ".pdf", ".csv", ".db", ".sqlite", ".sqlite3"}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "raw_sha256",
    "raw_root_private",
    "member_name_private",
    "member_sha256",
    "sheet_name_private",
    "matched_terms_private",
    "preview_rows_private",
    "probe_fingerprint",
    "field_plaintext",
    "header_plaintext",
    "business_amount",
    "account_number",
    "loan_contract_number",
    "original_filename",
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
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValidationError(f"{path} contains a non-object row")
            rows.append(value)
    return rows


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


def _walk_floats(value: Any) -> Iterator[Any]:
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
    result = subprocess.run(["git", "check-ignore", "-q", str(path)], check=False)
    return result.returncode == 0


def _git_tracked(path: Path) -> bool:
    return bool(_git_output(["ls-files", "--", str(path)]))


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
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
        phase.LANES_PATH,
        phase.METHODS_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_LANES_PATH,
        phase.METADATA_METHODS_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in paths:
        _check_public_file(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}

    manifest = _read_json(phase.MANIFEST_PATH)
    summary = manifest.get("summary", {})
    expected_identity = {
        "project_id": "KMFA",
        "stage_id": "S14",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S14-P1",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": "NO_GO",
    }
    for key, expected in expected_identity.items():
        _require(manifest.get(key) == expected, f"manifest {key} mismatch", errors)
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)

    expected_summary = {
        "stage13_post_remediation_review_dependency_validated": True,
        "source_lane_count": 4,
        "structure_connected_lane_count": 4,
        "unique_public_source_ref_count": 4,
        "lane_source_binding_count": 5,
        "unique_structure_candidate_count": 20,
        "lane_structure_candidate_association_count": 25,
        "private_parseable_lane_count": 4,
        "row_level_binding_proven_lane_count": 0,
        "value_binding_proven_lane_count": 0,
        "planning_method_definition_count": 3,
        "identified_cash_pressure_item_count": 0,
        "identified_loan_due_item_count": 0,
        "identified_account_balance_item_count": 0,
        "identified_business_item_count": 0,
        "public_business_amount_count": 0,
        "payment_approval_count": 0,
        "bank_operation_count": 0,
        "loan_management_action_count": 0,
        "raw_source_file_count": 5,
        "private_xlsx_container_count": 48,
        "private_parseable_xlsx_count": 25,
        "private_unparseable_xlsx_count": 23,
        "private_unique_candidate_sheet_count": 180,
        "private_candidate_sheet_count_by_lane": {
            "account_list": 12,
            "monthly_cash": 23,
            "fund_plan": 4,
            "loan_detail": 154,
        },
        "private_probe_roundtrip_mismatch_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "browser_status": "PASS",
        "browser_viewport_check_count": 2,
        "method_interaction_check_count": 6,
        "dependency_link_http_check_count": 4,
        "dependency_navigation_check_count": 4,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "s14_p2_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, expected in expected_summary.items():
        _require(summary.get(key) == expected, f"summary {key} mismatch", errors)

    lanes = manifest.get("source_lanes", [])
    _require(len(lanes) == 4, "source lane count mismatch", errors)
    _require({row.get("lane_id") for row in lanes} == {row["lane_id"] for row in phase.LANE_SPECS}, "lane ids mismatch", errors)
    for row in lanes:
        _require(row.get("structure_connected") is True, "lane structure not connected", errors)
        _require(row.get("private_candidate_structure_parseable") is True, "lane private candidate not parseable", errors)
        _require(row.get("row_level_binding_proven") is False, "lane row binding invented", errors)
        _require(row.get("value_binding_proven") is False, "lane value binding invented", errors)
        for key in (
            "contains_business_amounts",
            "contains_account_identifiers",
            "contains_field_plaintext",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "payment_or_bank_operation_allowed",
            "loan_management_action_allowed",
        ):
            _require(row.get(key) is False, f"lane {key} mismatch", errors)

    methods = manifest.get("planning_methods", [])
    _require(len(methods) == 3, "planning method count mismatch", errors)
    _require({row.get("method_id") for row in methods} == {row["method_id"] for row in phase.METHOD_SPECS}, "method ids mismatch", errors)
    for row in methods:
        _require(row.get("method_definition_complete") is True, "method definition incomplete", errors)
        _require(row.get("identified_business_item_count") == 0, "method business item invented", errors)
        _require(row.get("public_business_amount_count") == 0, "method business amount invented", errors)
        _require(row.get("current_binding_status") == "unproven", "method binding status mismatch", errors)

    quarantine = manifest.get("historical_quarantine", {})
    for key in (
        "legacy_manifest_validated_as_historical_fixture",
        "legacy_pending_twelve_quarantined",
        "legacy_cash_pressure_records_quarantined",
        "legacy_loan_due_alerts_quarantined",
        "legacy_account_balance_summaries_quarantined",
    ):
        _require(quarantine.get(key) is True, f"historical quarantine missing: {key}", errors)
    _require(quarantine.get("legacy_s14_p1_dynamic_state_is_authoritative") is False, "legacy state authoritative", errors)
    _require(quarantine.get("current_identified_business_item_count") == 0, "current historical item count mismatch", errors)

    matrix = manifest.get("acceptance_matrix", {})
    _require(matrix.get("fail_count") == 0, "acceptance matrix failed", errors)
    _require(matrix.get("pass_count") == 11, "acceptance matrix pass count mismatch", errors)
    _require(_read_json(phase.SUMMARY_PATH) == summary, "summary file drift", errors)
    _require(_read_json(phase.METADATA_SUMMARY_PATH) == summary, "metadata summary drift", errors)
    _require(_read_json(phase.METADATA_MANIFEST_PATH) == manifest, "metadata manifest drift", errors)
    _require(_read_json(phase.MATRIX_PATH) == matrix, "matrix drift", errors)
    return manifest


def _validate_dependency(errors: list[str]) -> None:
    try:
        dependency = phase._load_dependency()
    except Exception as exc:
        errors.append(f"current Stage 13 dependency failed: {exc}")
        return
    summary = dependency.get("summary", {})
    _require(summary.get("phase_results") == {"S13-P1": "PASS", "S13-P2": "PASS", "S13-P3": "PASS"}, "Stage 13 phase drift", errors)
    _require(summary.get("cross_table_not_comparable_dimension_count") == 4, "Stage 13 cross-table drift", errors)
    _require(summary.get("cross_table_exact_comparison_count") == 0, "Stage 13 exact comparison drift", errors)
    _require(summary.get("decision") == "NO_GO", "Stage 13 decision drift", errors)


def _validate_html(errors: list[str]) -> None:
    if not phase.HTML_PATH.is_file():
        return
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "资金现金贷款工作台",
        "账户清单",
        "月度现金",
        "资金计划",
        "贷款明细",
        "现金压力",
        "贷款到期",
        "账户余额汇总",
        "Q4 / D",
        "NO_GO",
        "0 / 4",
        "0 项已证明",
        "不形成业务结论",
        "不得据此发起付款审批、银行操作、还款、续贷或其他贷款管理动作",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    _require(text.count("data-method-button=") == 3, "HTML method button count mismatch", errors)
    _require(text.count("data-method-panel=") == 3, "HTML method panel count mismatch", errors)
    _require(text.count("data-dependency-link=") == 8, "HTML dependency link count mismatch", errors)
    for link_id, (href, _) in phase.DEPENDENCY_LINKS.items():
        _require(href in text, f"HTML href missing: {link_id}", errors)
        _require((phase.HTML_PATH.parent / href).resolve().is_file(), f"HTML target missing: {link_id}", errors)
    _require("gradient(" not in text, "gradient found", errors)
    _require("pending_reconciliation_count" not in text, "legacy pending leaked", errors)
    _require("付款审批允许" not in text and "银行操作允许" not in text, "operation permission leaked", errors)


def _validate_boundaries(manifest: dict[str, Any], errors: list[str]) -> None:
    quality = manifest.get("quality_gate", {})
    _require(quality == phase._quality_gate(), "quality gate mismatch", errors)
    boundaries = manifest.get("phase_boundaries", {})
    _require(boundaries == phase._phase_boundaries(), "phase boundary mismatch", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety == phase._public_safety(), "public safety mismatch", errors)
    _require(boundaries.get("s14_p1_performed") is True, "S14-P1 boundary missing", errors)
    for key, value in boundaries.items():
        if key not in {"stage13_post_remediation_review_validated", "s14_p1_performed"}:
            _require(value is False, f"later boundary opened: {key}", errors)


def _phase_is_current(version_matrix: str) -> bool:
    return f'current_phase: "{phase.PHASE_ID}"' in version_matrix


def _validate_governance(errors: list[str]) -> None:
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    statuses = [row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    tasks = [row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("identified_business_item_count") == 0, "event business item mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "event upload mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "source_lane_count == 4",
        "private_parseable_lane_count == 4",
        "row_level_binding_proven_lane_count == 0",
        "value_binding_proven_lane_count == 0",
        "planning_method_definition_count == 3",
        "identified_business_item_count == 0",
        "private_probe_roundtrip_mismatch_count == 0",
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
    manifest = _read_json(phase.MANIFEST_PATH)
    browser = manifest.get("browser_review", {})
    audit = str(browser.get("current_pass_count"))
    expected = {
        "PARAM-KMFA-1750": "4;4;4;5;20;25;4;0;0;3;0;0;0;0;5;48;25;23;180;0;12;23;4;154;3;9;2;1;Q4;D;NO_GO",
        "PARAM-KMFA-1751": f"6;54;54;0;0;1;{audit};{audit};0;0;2;6;4;4;0;0",
        "PARAM-KMFA-1752": "true;true;true;true;true;true;true;true;false;false;false;false;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1753": "structure_and_private_candidates_connected_values_unproven;0;0;0;0;false;false;false;false;false;D;NO_GO",
    }
    for parameter_id, expected_value in expected.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    if _phase_is_current(version_matrix):
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 S14-P2" in handoff, "HANDOFF next phase missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S14-P1" in agents and "S14-P2" in agents, "AGENTS scope drift", errors)

    traceability = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in traceability and phase.ACCEPTANCE_ID in traceability, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "S14-P1 修补后资金现金贷款"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"audit row count mismatch: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"audit file count mismatch: {path}", errors)
    _require(sum(row.get("status") == "FAIL" for row in rows) == 0, f"audit failure: {path}", errors)
    _require(sum(row.get("status") == "WARN" for row in rows) == 0, f"audit warning: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_PROBE_PATH,
        phase.PRIVATE_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.s13_review.PRIVATE_RAW_AFTER_PATH)
        helper = phase.s13_review.p1.s12_review.p1.s11_project
        current = helper._raw_snapshot("validate_v014_s14_p1_post_remediation_fund_cash_loan_plan")
        normalize = helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-Stage13 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        probe = _read_json(phase.PRIVATE_PROBE_PATH)
        expected_probe = {
            "raw_file_count": 5,
            "private_xlsx_container_count": 48,
            "private_parseable_xlsx_count": 25,
            "private_unparseable_xlsx_count": 23,
            "private_unique_candidate_sheet_count": 180,
            "private_candidate_sheet_count_by_lane": {
                "account_list": 12,
                "monthly_cash": 23,
                "fund_plan": 4,
                "loan_detail": 154,
            },
            "private_parseable_lane_count": 4,
            "private_probe_roundtrip_mismatch_count": 0,
            "row_level_binding_proven_lane_count": 0,
            "value_binding_proven_lane_count": 0,
        }
        for key, expected in expected_probe.items():
            _require(probe.get(key) == expected, f"private probe {key} mismatch", errors)
        _require(len(probe.get("candidate_sheets_private", [])) == 180, "private candidate record count mismatch", errors)
        report = phase.PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("二次探针指纹不一致：0", "行级 / 数值权威绑定：0 / 0", "全中文最终差异报告"):
            _require(token in report, f"private report token missing: {token}", errors)

    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BROWSER_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_ignored(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    if phase.MANIFEST_PATH.is_file():
        current_rows = _read_json(phase.MANIFEST_PATH).get("browser_review", {}).get("current_control_row_count", -1)
        _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, 1, current_rows)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        expected_counts = {
            "viewport_checks": 2,
            "method_interaction_checks": 6,
            "dependency_link_http_checks": 4,
            "dependency_navigation_checks": 4,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} mismatch", errors)
        for key in ("method_interaction_checks", "dependency_link_http_checks", "dependency_navigation_checks"):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("marker_visible") is True
                and row.get("d_no_go_visible") is True
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / f"fund_cash_loan_{mode}.png"
        _require(path.is_file(), f"screenshot missing: {path}", errors)
        _require(_git_ignored(path), f"screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s14_p1_post_remediation_fund_cash_loan_plan(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependency(errors)
    _validate_html(errors)
    if manifest:
        _validate_boundaries(manifest, errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "browser_desktop_mobile",
            "raw_candidate_probe",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation {key} mismatch", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-browser-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s14_p1_post_remediation_fund_cash_loan_plan(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S14-P1 strict validation PASS: "
        f"lanes={summary['source_lane_count']} candidates={summary['private_unique_candidate_sheet_count']} "
        f"bound={summary['value_binding_proven_lane_count']} items={summary['identified_business_item_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
