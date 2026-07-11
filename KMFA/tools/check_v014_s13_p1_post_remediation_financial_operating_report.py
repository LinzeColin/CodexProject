#!/usr/bin/env python3
"""Validate current public-safe KMFA v0.1.4 S13-P1 report evidence."""

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

from KMFA.tools import v014_s13_p1_post_remediation_financial_operating_report as phase
from KMFA.tools.check_v014_s12_post_remediation_stage_review import (
    validate_v014_s12_post_remediation_stage_review,
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
        phase.LANES_PATH,
        phase.DRAFTS_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.WEEKLY_HTML_PATH,
        phase.MONTHLY_HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_LANES_PATH,
        phase.METADATA_DRAFTS_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    lanes_wrapper = _read_json(phase.LANES_PATH)
    drafts_wrapper = _read_json(phase.DRAFTS_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(lanes_wrapper == _read_json(phase.METADATA_LANES_PATH), "lane mirror drift", errors)
    _require(drafts_wrapper == _read_json(phase.METADATA_DRAFTS_PATH), "draft mirror drift", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("source_lane_status") == lanes_wrapper.get("lanes"), "lane wrapper drift", errors)
    _require(manifest.get("draft_definitions") == drafts_wrapper.get("drafts"), "draft wrapper drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "manifest matrix drift", errors)

    expected = {
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "S13-P1",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "stage12_review_dependency_validated": True,
        "source_lane_count": 4,
        "unique_source_count": 7,
        "lane_source_binding_count": 8,
        "unique_structure_candidate_count": 35,
        "lane_structure_candidate_association_count": 40,
        "structure_connected_lane_count": 4,
        "raw_value_bound_lane_count": 0,
        "draft_report_count": 2,
        "html_draft_count": 2,
        "required_section_count": 7,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "browser_viewport_check_count": 4,
        "section_interaction_check_count": 28,
        "cross_draft_link_http_check_count": 2,
        "cross_draft_navigation_check_count": 2,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "s13_p2_performed": False,
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

    lanes = manifest.get("source_lane_status", [])
    _require(len(lanes) == 4, "source lane count mismatch", errors)
    _require(
        {row.get("lane_id") for row in lanes}
        == {row["lane_id"] for row in phase.LANE_SPECS},
        "source lane IDs mismatch",
        errors,
    )
    for lane in lanes:
        _require(lane.get("structure_connected") is True, "lane structure not connected", errors)
        _require(
            lane.get("current_raw_value_binding_proven") is False,
            "lane raw value binding improperly claimed",
            errors,
        )
        _require(
            lane.get("data_status") == "structure_connected_values_unproven",
            "lane data status mismatch",
            errors,
        )
        for key in (
            "contains_source_identity",
            "contains_field_plaintext",
            "contains_business_amounts",
            "formal_report_allowed",
            "business_decision_basis_allowed",
        ):
            _require(lane.get(key) is False, f"lane {key} must be false", errors)

    drafts = manifest.get("draft_definitions", [])
    _require(len(drafts) == 2, "draft definition count mismatch", errors)
    _require(
        {row.get("draft_id") for row in drafts}
        == {"financial_operating_weekly_draft", "financial_operating_monthly_draft"},
        "draft IDs mismatch",
        errors,
    )
    for draft in drafts:
        _require(draft.get("report_grade_visible") == "D", "draft grade mismatch", errors)
        _require(draft.get("decision") == "NO_GO", "draft decision mismatch", errors)
        _require(draft.get("draft_report_allowed") is True, "draft permission mismatch", errors)
        _require(draft.get("formal_report_allowed") is False, "formal draft improperly allowed", errors)
        _require(
            draft.get("business_decision_basis_allowed") is False,
            "decision basis improperly allowed",
            errors,
        )
        _require(draft.get("contains_business_amounts") is False, "draft amount flag mismatch", errors)
        _require(
            draft.get("data_status_and_limitations_visible") is True,
            "draft limitations not visible",
            errors,
        )
        _require(len(draft.get("visible_section_titles", [])) == 7, "draft section count mismatch", errors)

    expected_quality = phase._quality_gate()
    _require(manifest.get("quality_gate") == expected_quality, "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_repo_safety(), "public safety drift", errors)
    _require(
        all(value is False for key, value in expected_quality.items() if key.endswith("_allowed") and key not in {"draft_report_allowed", "weekly_draft_allowed", "monthly_draft_allowed"}),
        "closed quality gate became permissive",
        errors,
    )
    raw_boundary = manifest.get("raw_boundary", {})
    _require(raw_boundary.get("raw_read_authorized") is True, "raw read authorization missing", errors)
    _require(raw_boundary.get("raw_snapshot_validation_performed") is True, "raw snapshot flag missing", errors)
    for key, value in raw_boundary.items():
        if key not in {"raw_read_authorized", "raw_snapshot_validation_performed"}:
            _require(value is False, f"raw boundary {key} must be false", errors)

    _require(matrix.get("check_count") == 24, "matrix check count mismatch", errors)
    _require(matrix.get("check_pass_count") == 24, "matrix pass count mismatch", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix contains failures", errors)
    _require(all(row.get("passed") is True for row in matrix.get("checks", [])), "matrix row failed", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("draft_report_allowed") is True, "go/no-go draft permission mismatch", errors)
    for key in (
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "s13_p2_performed",
        "s13_p3_performed",
        "stage13_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(go_no_go.get(key) is False, f"go/no-go {key} must be false", errors)

    browser = manifest.get("browser_review", {})
    browser_expected = {
        "status": "PASS",
        "baseline_file_count": 6,
        "baseline_control_row_count": 54,
        "baseline_pass_count": 54,
        "baseline_warn_count": 0,
        "baseline_fail_count": 0,
        "current_page_count": 2,
        "current_control_row_count": 16,
        "current_pass_count": 16,
        "current_warn_count": 0,
        "current_fail_count": 0,
        "viewport_check_count": 4,
        "section_interaction_check_count": 28,
        "cross_draft_link_http_check_count": 2,
        "cross_draft_navigation_check_count": 2,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
    }
    for key, value in browser_expected.items():
        _require(browser.get(key) == value, f"browser summary {key} mismatch", errors)

    for key in (
        "stage12_post_remediation_review_dependency_validated",
        "historical_s13_p1_policy_fixture_validated",
        "historical_pending_twelve_quarantined",
        "historical_b_grade_sample_quarantined",
    ):
        _require(manifest.get(key) is True, f"manifest {key} must be true", errors)
    _require(
        manifest.get("historical_s13_p1_dynamic_state_is_authoritative") is False,
        "historical S13-P1 state became authoritative",
        errors,
    )
    _require(manifest.get("next_phase") == "S13-P2", "next phase drift", errors)
    return manifest


def _validate_html(errors: list[str]) -> None:
    pages = {
        "weekly": (phase.WEEKLY_HTML_PATH, "经营周报初稿", phase.MONTHLY_HTML_PATH.name),
        "monthly": (phase.MONTHLY_HTML_PATH, "经营月报初稿", phase.WEEKLY_HTML_PATH.name),
    }
    for page_id, (path, marker, expected_href) in pages.items():
        text = path.read_text(encoding="utf-8")
        _require(marker in text, f"HTML marker missing: {page_id}", errors)
        for token in ("Q4 / D", "NO_GO", "0 / 4", "数据状态与限制", "不是正式报告"):
            _require(token in text, f"HTML token missing {page_id}: {token}", errors)
        _require(text.count("data-section-button=") == 7, f"HTML tab count mismatch: {page_id}", errors)
        _require(text.count("data-section-panel=") == 7, f"HTML panel count mismatch: {page_id}", errors)
        href_match = re.search(r'<a[^>]+data-other-draft[^>]+href="([^"]+)"', text)
        _require(bool(href_match), f"cross-draft link missing: {page_id}", errors)
        if href_match:
            _require(href_match.group(1) == expected_href, f"cross-draft href mismatch: {page_id}", errors)
            _require((path.parent / expected_href).is_file(), f"cross-draft target missing: {page_id}", errors)
        _require("gradient(" not in text, f"gradient surface found: {page_id}", errors)
        _require("pending_reconciliation_count" not in text, f"historical pending leaked: {page_id}", errors)
        _require(">B<" not in text and "Q4 / B" not in text, f"historical B grade leaked: {page_id}", errors)
        for marker_value in PUBLIC_BUSINESS_AMOUNT_MARKERS:
            _require(marker_value not in text, f"business amount marker leaked in {page_id}: {marker_value}", errors)


def _validate_dependencies(errors: list[str]) -> None:
    try:
        dependency = validate_v014_s12_post_remediation_stage_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
    except Exception as exc:
        errors.append(f"current Stage 12 dependency failed: {exc}")
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
        "raw_source_file_count": 5,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"Stage 12 dependency {key} mismatch", errors)
    try:
        rebuilt_lanes, rebuilt_counts = phase._build_source_lanes()
        current_manifest = _read_json(phase.MANIFEST_PATH)
        _require(current_manifest.get("source_lane_status") == rebuilt_lanes, "current source lanes drift", errors)
        for key, value in rebuilt_counts.items():
            _require(current_manifest.get("summary", {}).get(key) == value, f"current structure {key} drift", errors)
    except Exception as exc:
        errors.append(f"current public-safe structure dependency failed: {exc}")


def _validate_governance(errors: list[str]) -> None:
    events = [
        row
        for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH)
        if row.get("phase_id") == phase.PHASE_ID
    ]
    statuses = [
        row
        for row in _read_jsonl(phase.STAGE_STATUS_PATH)
        if row.get("phase_id") == phase.PHASE_ID
    ]
    tasks = [
        row
        for row in _read_jsonl(phase.TASK_STATUS_PATH)
        if row.get("phase_id") == phase.PHASE_ID
    ]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("status") == phase.STATUS, "development status mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "development upload flag mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status mismatch", errors)
        _require(statuses[0].get("derived_percent") == "33.33", "stage progress mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)
        _require(tasks[0].get("completed_task_units") == 3, "task completion mismatch", errors)

    formula_path = Path("KMFA/docs/governance/formula_registry.yaml")
    formula_text = formula_path.read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "source_lane_count == 4",
        "unique_source_count == 7",
        "lane_source_binding_count == 8",
        "unique_structure_candidate_count == 35",
        "lane_structure_candidate_association_count == 40",
        "structure_connected_lane_count == 4",
        "raw_value_bound_lane_count == 0",
        "draft_report_count == 2",
        "current_grade == D",
        "decision == NO_GO",
        "formal_report_count == 0",
        "business_decision_basis_count == 0",
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
        "PARAM-KMFA-1735": "4;7;8;35;40;4;0;2;2;7;3;9;2;1;12;5;Q4;D;NO_GO",
        "PARAM-KMFA-1736": "6;54;54;0;0;2;16;16;0;0;4;28;2;2;0;0",
        "PARAM-KMFA-1737": "true;true;true;true;true;true;true;true;false;false;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1738": "true;true;true;true;false;false;false;false;false;false;false;false;false;false;NO_GO",
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
        _require("下一步只能执行 S13-P2" in handoff, "HANDOFF next phase boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("S13-P1" in agents and "S13-P2" in agents, "AGENTS phase scope drift", errors)

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
        (Path("KMFA/功能清单.md"), "v0.1.4 S13-P1 修补后财务经营报表初稿"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int) -> None:
    _require(path.is_file(), f"browser audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len(rows) == expected_rows, f"browser audit row count mismatch: {path}", errors)
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
        phase.PRIVATE_ALIGNMENT_PATH,
        phase.PRIVATE_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.s12_review.PRIVATE_RAW_AFTER_PATH)
        current = phase.s12_review.p1.s11_project._raw_snapshot(
            "validate_v014_s13_p1_post_remediation_financial_operating_report"
        )
        normalize = phase.s12_review.p1.s11_project._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-Stage12 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        alignment = _read_json(phase.PRIVATE_ALIGNMENT_PATH)
        expected_alignment = {
            "classification": "PRIVATE_RUNTIME_ONLY",
            "raw_source_file_count": 5,
            "structure_connected_lane_count": 4,
            "raw_value_bound_lane_count": 0,
            "report_business_amount_output_count": 0,
            "raw_to_report_value_comparison_performed": False,
            "raw_to_report_value_comparison_blocked_by_unproven_binding": True,
            "raw_snapshot_exact_match": True,
            "raw_cross_phase_snapshot_exact_match": True,
            "difference_report_required_for_this_phase": False,
            "final_goal_difference_report_required_if_binding_remains_unresolved": True,
        }
        for key, value in expected_alignment.items():
            _require(alignment.get(key) == value, f"private alignment {key} mismatch", errors)
        private_report = phase.PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("phase 前后快照：exact match", "当前 raw 数值可证明绑定：0/4", "全中文差异报告"):
            _require(token in private_report, f"private report token missing: {token}", errors)

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
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, 2, 16)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser evidence status mismatch", errors)
        expected_counts = {
            "viewport_checks": 4,
            "section_interaction_checks": 28,
            "cross_draft_link_http_checks": 2,
            "cross_draft_navigation_checks": 2,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} count mismatch", errors)
        for key in (
            "section_interaction_checks",
            "cross_draft_link_http_checks",
            "cross_draft_navigation_checks",
        ):
            _require(all(row.get("passed") is True for row in browser.get(key, [])), f"browser {key} failed", errors)
        _require(
            all(
                row.get("marker_visible") is True
                and row.get("d_no_go_visible") is True
                and row.get("amount_free_visible") is True
                and row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for page_id in ("weekly", "monthly"):
        for mode, width in (("desktop", 1440), ("mobile", 390)):
            path = phase.PRIVATE_SCREENSHOT_DIR / f"{page_id}_{mode}.png"
            _require(path.is_file(), f"browser screenshot missing: {path}", errors)
            _require(_git_check_ignore(path), f"browser screenshot not ignored: {path}", errors)
            _require(not _git_tracked(path), f"browser screenshot tracked: {path}", errors)
            if path.is_file():
                actual_width, height = _png_dimensions(path)
                _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
                _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s13_p1_post_remediation_financial_operating_report(
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
    try:
        manifest = validate_v014_s13_p1_post_remediation_financial_operating_report(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S13-P1 post-remediation financial operating report "
        f"lanes={summary['source_lane_count']} drafts={summary['draft_report_count']} "
        f"bound={summary['raw_value_bound_lane_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
