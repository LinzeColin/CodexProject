#!/usr/bin/env python3
"""Validate current public-safe KMFA v0.1.4 S13-P3 cross-table evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s13_p3_post_remediation_cross_table_review as phase
from KMFA.tools.check_v014_s13_p2_post_remediation_collection_receivable_aging import (
    validate_v014_s13_p2_post_remediation_collection_receivable_aging,
)


FORBIDDEN_PUBLIC_SUFFIXES = {
    ".zip",
    ".xls",
    ".xlsx",
    ".pdf",
    ".csv",
    ".db",
    ".sqlite",
    ".sqlite3",
}
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "business_value",
    "amount_yuan",
    "row_value",
    "cell_value",
    "sheet_name",
    "member_name",
    "private_member_name",
    "private_filename",
    "private_path",
    "original_filename",
    "file_hash",
    "field_key",
    "field_label",
    "source_header_text",
    "project_name_plaintext",
    "customer_name_plaintext",
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
PUBLIC_BUSINESS_AMOUNT_MARKERS = ("￥", "¥", "CNY", "RMB", "万元", "元整")
REQUIRED_QUEUE_KEYS = {
    "difference_id",
    "source_a",
    "source_b",
    "field_name",
    "amount_a_cents",
    "amount_b_cents",
    "delta_cents",
    "reason_candidate",
    "impact_scope",
    "resolution_status",
    "reviewer",
    "created_at",
    "closed_at",
}


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
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _walk_floats(value: Any):
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _walk_floats(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_floats(child)


def _git_check_ignore(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", path.as_posix()],
        check=False,
    ).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _phase_is_current(version_matrix_text: str) -> bool:
    match = re.search(r'^current_phase:\s*"([^"]+)"', version_matrix_text, re.MULTILINE)
    return bool(match and match.group(1) == phase.PHASE_ID)


def _check_public_file(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"missing public artifact: {path}", errors)
    if not path.is_file():
        return
    _require(
        path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES,
        f"forbidden public suffix: {path}",
        errors,
    )
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked in {path}", errors)
    _require(
        LOCAL_DOWNLOADS_PATTERN.search(text) is None,
        f"local Downloads path leaked in {path}",
        errors,
    )
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        _require(not list(_walk_floats(value)), f"float value found in {path}", errors)
        for key in _walk_keys(value):
            _require(
                key not in FORBIDDEN_PUBLIC_KEYS,
                f"forbidden public key {key!r} in {path}",
                errors,
            )


def _validate_public(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.CHECKS_PATH,
        phase.DIFFERENCE_QUEUE_PATH,
        phase.QUALITY_REPORT_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_CHECKS_PATH,
        phase.METADATA_DIFFERENCE_QUEUE_PATH,
        phase.METADATA_QUALITY_REPORT_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    checks_wrapper = _read_json(phase.CHECKS_PATH)
    queue_wrapper = _read_json(phase.DIFFERENCE_QUEUE_PATH)
    quality = _read_json(phase.QUALITY_REPORT_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(checks_wrapper == _read_json(phase.METADATA_CHECKS_PATH), "check mirror drift", errors)
    _require(queue_wrapper == _read_json(phase.METADATA_DIFFERENCE_QUEUE_PATH), "queue mirror drift", errors)
    _require(quality == _read_json(phase.METADATA_QUALITY_REPORT_PATH), "quality mirror drift", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("review_checks") == checks_wrapper.get("checks"), "manifest checks drift", errors)
    _require(manifest.get("difference_queue") == queue_wrapper.get("queue"), "manifest queue drift", errors)
    _require(manifest.get("quality_report") == quality, "manifest quality drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "manifest matrix drift", errors)

    expected = {
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S13-P3",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "s13_p2_dependency_validated": True,
        "review_dimension_count": 4,
        "comparable_dimension_count": 0,
        "exact_comparison_performed_count": 0,
        "proven_match_dimension_count": 0,
        "proven_mismatch_dimension_count": 0,
        "not_comparable_dimension_count": 4,
        "difference_queue_count": 4,
        "difference_queue_is_non_additive": True,
        "quality_report_count": 1,
        "quality_html_count": 1,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "raw_source_file_count": 5,
        "private_dimension_diagnostic_count": 4,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "browser_status": "PASS",
        "browser_viewport_check_count": 2,
        "dimension_interaction_check_count": 4,
        "dependency_link_http_check_count": 3,
        "dependency_navigation_check_count": 3,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "stage13_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require(
        "pending_reconciliation_count" not in summary,
        "historical pending count leaked into current summary",
        errors,
    )

    checks = manifest.get("review_checks", [])
    expected_dimensions = {row["review_dimension"] for row in phase.DIMENSION_SPECS}
    _require(len(checks) == 4, "review check count mismatch", errors)
    _require(
        {row.get("review_dimension") for row in checks} == expected_dimensions,
        "review dimensions mismatch",
        errors,
    )
    for row in checks:
        expected_row = {
            "public_structure_evidence_present": True,
            "candidate_key_class_observed_privately": True,
            "shared_row_binding_proven": False,
            "shared_period_binding_proven": False,
            "exact_comparison_performed": False,
            "review_result": "NOT_COMPARABLE",
            "difference_queue_required": True,
            "one_cent_difference_ignored": False,
            "business_conclusion_allowed": False,
            "contains_source_identity": False,
            "contains_field_plaintext": False,
            "contains_business_amounts": False,
        }
        for key, value in expected_row.items():
            _require(row.get(key) == value, f"review check {key} mismatch", errors)
    amount_check = next(
        (row for row in checks if row.get("review_dimension") == "amount_consistency"),
        {},
    )
    _require(amount_check.get("money_tolerance_minor_units") == 0, "money tolerance mismatch", errors)

    queue = manifest.get("difference_queue", [])
    _require(len(queue) == 4, "difference queue count mismatch", errors)
    _require(queue_wrapper.get("queue_is_non_additive") is True, "queue wrapper additive drift", errors)
    for row in queue:
        _require(REQUIRED_QUEUE_KEYS.issubset(row), "difference queue contract incomplete", errors)
        for key in ("amount_a_cents", "amount_b_cents", "delta_cents", "closed_at"):
            _require(row.get(key) is None, f"queue {key} must be null", errors)
        expected_row = {
            "resolution_status": "pending_evidence_not_comparable",
            "queue_item_is_additive_to_global_difference_counts": False,
            "auto_resolution_allowed": False,
            "auto_source_selection_allowed": False,
            "business_action_allowed": False,
            "contains_source_identity": False,
            "contains_field_plaintext": False,
            "contains_business_amounts": False,
        }
        for key, value in expected_row.items():
            _require(row.get(key) == value, f"difference queue {key} mismatch", errors)

    expected_quality = {
        "cross_table_review_status": "insufficient_row_level_evidence",
        "review_dimension_count": 4,
        "comparable_dimension_count": 0,
        "not_comparable_dimension_count": 4,
        "comparison_completion_ratio_bps": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "difference_closure_allowed": False,
        "business_execution_allowed": False,
    }
    for key, value in expected_quality.items():
        _require(quality.get(key) == value, f"quality report {key} mismatch", errors)
    _require(matrix.get("check_fail_count") == 0, "acceptance matrix failure", errors)
    _require(matrix.get("check_count") == matrix.get("check_pass_count"), "acceptance matrix incomplete", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)

    quality_gate = manifest.get("quality_gate", {})
    for key in (
        "cross_table_review_evidence_allowed",
        "difference_queue_output_allowed",
        "operating_report_quality_report_allowed",
    ):
        _require(quality_gate.get(key) is True, f"quality gate {key} mismatch", errors)
    for key in (
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "difference_auto_resolution_allowed",
        "difference_closure_allowed",
        "stage13_review_allowed",
        "github_upload_allowed",
        "app_reinstall_allowed",
        "business_execution_allowed",
    ):
        _require(quality_gate.get(key) is False, f"quality gate {key} mismatch", errors)

    boundaries = manifest.get("phase_boundaries", {})
    for key in ("s13_p1_performed", "s13_p2_performed", "s13_p3_performed"):
        _require(boundaries.get(key) is True, f"phase boundary {key} mismatch", errors)
    for key in (
        "stage13_review_performed",
        "s14_p1_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "business_execution_performed",
        "persistent_business_write_performed",
    ):
        _require(boundaries.get(key) is False, f"phase boundary {key} mismatch", errors)
    _require(manifest.get("historical_s13_p3_policy_fixture_validated") is True, "historical fixture invalid", errors)
    _require(manifest.get("historical_s13_p3_dynamic_state_is_authoritative") is False, "historical state became authoritative", errors)
    _require(manifest.get("historical_pending_twelve_quarantined") is True, "historical pending state not quarantined", errors)
    _require(manifest.get("historical_completed_review_claim_quarantined") is True, "historical completed claim not quarantined", errors)
    _require(manifest.get("next_phase") == "S13-REVIEW", "next phase mismatch", errors)
    _require(all(value is False for value in manifest.get("public_repo_safety", {}).values()), "public safety flag mismatch", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    if not phase.HTML_PATH.is_file():
        return
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "跨表复核质量工作台",
        "Q4 / D",
        "NO_GO",
        "项目一致性",
        "客户一致性",
        "金额一致性",
        "时间一致性",
        "NOT_COMPARABLE",
        "非累加差异队列",
        "0 分容差",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    _require(text.count("data-dimension-button=") == 4, "HTML dimension button count mismatch", errors)
    _require(text.count("data-dimension-panel=") == 4, "HTML dimension panel count mismatch", errors)
    _require(text.count("data-dependency-link=") == 3, "HTML dependency link count mismatch", errors)
    for href in (phase.WEEKLY_HREF, phase.MONTHLY_HREF, phase.RECEIVABLE_HREF):
        _require(href in text, f"HTML dependency href missing: {href}", errors)
        _require((phase.HTML_PATH.parent / href).resolve().is_file(), f"HTML dependency target missing: {href}", errors)
    _require("gradient(" not in text, "gradient surface found", errors)
    _require("pending_reconciliation_count" not in text, "historical pending leaked", errors)
    for marker in PUBLIC_BUSINESS_AMOUNT_MARKERS:
        _require(marker not in text, f"business amount marker leaked in HTML: {marker}", errors)


def _validate_dependencies(errors: list[str]) -> None:
    try:
        dependency = validate_v014_s13_p2_post_remediation_collection_receivable_aging(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
    except Exception as exc:
        errors.append(f"current S13-P2 dependency failed: {exc}")
        return
    summary = dependency.get("summary", {})
    expected = {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "structure_connected_lane_count": 5,
        "private_raw_parseable_lane_count": 3,
        "row_level_binding_proven_lane_count": 0,
        "identified_business_item_count": 0,
        "raw_source_file_count": 5,
        "s13_p3_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"S13-P2 dependency {key} mismatch", errors)
    try:
        manifest = _read_json(phase.MANIFEST_PATH)
        _require(manifest.get("review_checks") == phase._build_review_checks(), "current review checks drift", errors)
        _require(
            [row.get("review_dimension") for row in manifest.get("difference_queue", [])]
            == [row["review_dimension"] for row in phase.DIMENSION_SPECS],
            "current queue dimension order drift",
            errors,
        )
    except Exception as exc:
        errors.append(f"current public-safe S13-P3 build failed: {exc}")


def _validate_governance(errors: list[str]) -> None:
    events = [
        row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID
    ]
    statuses = [
        row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID
    ]
    tasks = [
        row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID
    ]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("status") == phase.STATUS, "development status mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "development upload flag mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status mismatch", errors)
        _require(statuses[0].get("derived_percent") == "100.00", "stage progress mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)
        _require(tasks[0].get("completed_task_units") == 3, "task completion mismatch", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "review_dimension_count == 4",
        "comparable_dimension_count == 0",
        "exact_comparison_performed_count == 0",
        "not_comparable_dimension_count == 4",
        "difference_queue_count == 4",
        "difference_queue_is_non_additive == true",
        "current_grade == D",
        "decision == NO_GO",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)

    for path in (
        Path("KMFA/docs/governance/model_registry.yaml"),
        Path("KMFA/metadata/model_registry.yaml"),
    ):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model registry key missing: {path}", errors)
        _require(phase.FORMULA_ID in text, f"model formula ref missing: {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"model parameter ref missing: {path}:{parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    expected_parameter_values = {
        "PARAM-KMFA-1743": "4;0;0;0;0;4;4;true;1;1;5;4;Q4;D;NO_GO",
        "PARAM-KMFA-1744": "6;54;54;0;0;1;2;4;3;3;0;0",
        "PARAM-KMFA-1745": "true;true;true;true;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1746": "insufficient_row_level_evidence;0;0;0;0;false;false;false;false;D;NO_GO",
    }
    for parameter_id, expected_value in expected_parameter_values.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix_path = Path("KMFA/docs/governance/VERSION_MATRIX.yaml")
    version_matrix = version_matrix_path.read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX model missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX version missing", errors)
    if _phase_is_current(version_matrix):
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF current phase drift", errors)
        _require("下一步只能执行 Stage 13 整体复审" in handoff, "HANDOFF next phase boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S13-P3" in agents and "Stage 13 整体复审" in agents, "AGENTS phase scope drift", errors)

    traceability = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in traceability and phase.ACCEPTANCE_ID in traceability, "traceability record missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula ref missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter ref missing: {parameter_id}", errors)

    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "v0.1.4 S13-P3 修补后跨表复核"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int | None = None) -> None:
    _require(path.is_file(), f"browser audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if expected_rows is not None:
        _require(len(rows) == expected_rows, f"browser audit row count mismatch: {path}", errors)
    else:
        _require(len(rows) > 0, f"browser audit is empty: {path}", errors)
    _require(len({row.get("file") for row in rows}) == expected_files, f"browser audit file count mismatch: {path}", errors)
    _require(sum(row.get("status") == "FAIL" for row in rows) == 0, f"browser audit failure: {path}", errors)
    _require(sum(row.get("status") == "WARN" for row in rows) == 0, f"browser audit warning: {path}", errors)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError(f"invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _validate_private(errors: list[str], require_browser_evidence: bool) -> None:
    private_paths = (
        phase.PRIVATE_RAW_BEFORE_PATH,
        phase.PRIVATE_RAW_AFTER_PATH,
        phase.PRIVATE_DIAGNOSTIC_PATH,
        phase.PRIVATE_DIFFERENCE_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.s13_p2.PRIVATE_RAW_AFTER_PATH)
        raw_helper = phase.s13_p2.s13_p1.s12_review.p1.s11_project
        current = raw_helper._raw_snapshot("validate_v014_s13_p3_post_remediation_cross_table_review")
        normalize = raw_helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-S13-P2 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)

        diagnostic = _read_json(phase.PRIVATE_DIAGNOSTIC_PATH)
        expected_diagnostic = {
            "classification": "PRIVATE_RUNTIME_ONLY",
            "raw_source_file_count": 5,
            "private_dimension_diagnostic_count": 4,
            "workbook_candidate_count": 26,
            "openable_workbook_count": 25,
            "private_candidate_signal_is_authoritative_business_item": False,
            "row_level_binding_proven": False,
            "exact_business_value_comparison_performed": False,
            "mutation_performed": False,
            "public_commit_allowed": False,
        }
        for key, value in expected_diagnostic.items():
            _require(diagnostic.get(key) == value, f"private diagnostic {key} mismatch", errors)
        dimensions = diagnostic.get("dimensions", [])
        _require(len(dimensions) == 4, "private diagnostic dimension count mismatch", errors)
        _require(
            {row.get("private_key_class") for row in dimensions}
            == {"project_key", "customer_key", "amount_key", "date_key"},
            "private diagnostic key classes mismatch",
            errors,
        )
        _require(
            all(
                row.get("candidate_key_class_observed") is True
                and row.get("shared_row_binding_proven") is False
                and row.get("shared_period_binding_proven") is False
                and row.get("exact_business_value_comparison_performed") is False
                and row.get("result") == "NOT_COMPARABLE"
                for row in dimensions
            ),
            "private dimension diagnostic mismatch",
            errors,
        )
        private_report = phase.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
        for token in (
            "候选标签或信号",
            "同一业务行",
            "金额容差为 0 分",
            "未忽略 0.01 元差异",
            "全中文最终差异报告",
        ):
            _require(token in private_report, f"private difference report token missing: {token}", errors)

    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BROWSER_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, 1)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser evidence status mismatch", errors)
        expected_counts = {
            "viewport_checks": 2,
            "dimension_interaction_checks": 4,
            "dependency_link_http_checks": 3,
            "dependency_navigation_checks": 3,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} count mismatch", errors)
        for key in (
            "dimension_interaction_checks",
            "dependency_link_http_checks",
            "dependency_navigation_checks",
        ):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("workbench_visible") is True
                and row.get("d_no_go_visible") is True
                and row.get("not_comparable_visible") is True
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for mode, width in (("desktop", 1440), ("mobile", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / f"workbench_{mode}.png"
        _require(path.is_file(), f"browser screenshot missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s13_p3_post_remediation_cross_table_review(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_html(errors)
    _validate_dependencies(errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
    if require_final_evidence:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "browser_desktop_mobile",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
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
    manifest = validate_v014_s13_p3_post_remediation_cross_table_review(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S13-P3 strict validation PASS: "
        f"dimensions={summary['review_dimension_count']} "
        f"not_comparable={summary['not_comparable_dimension_count']} "
        f"queue={summary['difference_queue_count']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
