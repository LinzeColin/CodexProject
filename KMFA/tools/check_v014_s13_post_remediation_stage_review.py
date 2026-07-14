#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 13 post-remediation review evidence."""

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

from KMFA.tools import v014_s13_post_remediation_stage_review as phase
from KMFA.tools.check_v014_s13_p1_post_remediation_financial_operating_report import (
    validate_v014_s13_p1_post_remediation_financial_operating_report,
)
from KMFA.tools.check_v014_s13_p2_post_remediation_collection_receivable_aging import (
    validate_v014_s13_p2_post_remediation_collection_receivable_aging,
)
from KMFA.tools.check_v014_s13_p3_post_remediation_cross_table_review import (
    validate_v014_s13_p3_post_remediation_cross_table_review,
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
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


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
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked: {path}", errors)
    _require(LOCAL_DOWNLOADS_PATTERN.search(text) is None, f"local path leaked: {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token: {path}", errors)
    if path.suffix.lower() == ".json":
        value = json.loads(text)
        _require(not list(_walk_floats(value)), f"float found: {path}", errors)
        for key in _walk_keys(value):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key {key!r}: {path}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    public_paths = (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)

    summary = _read_json(phase.SUMMARY_PATH)
    manifest = _read_json(phase.MANIFEST_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(matrix == _read_json(phase.METADATA_MATRIX_PATH), "matrix mirror drift", errors)
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)

    expected = {
        "project_id": "KMFA",
        "stage_id": "S13",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "STAGE-REVIEW",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "review_scope": phase.REVIEW_SCOPE,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "phase_results": {"S13-P1": "PASS", "S13-P2": "PASS", "S13-P3": "PASS"},
        "financial_source_lane_count": 4,
        "financial_structure_connected_lane_count": 4,
        "financial_raw_value_bound_lane_count": 0,
        "financial_draft_report_count": 2,
        "receivable_source_lane_count": 5,
        "receivable_private_parseable_lane_count": 3,
        "receivable_row_binding_proven_lane_count": 0,
        "receivable_issue_definition_count": 4,
        "receivable_identified_business_item_count": 0,
        "receivable_actionable_priority_count": 0,
        "receivable_assigned_responsibility_count": 0,
        "cross_table_review_dimension_count": 4,
        "cross_table_comparable_dimension_count": 0,
        "cross_table_exact_comparison_count": 0,
        "cross_table_proven_match_count": 0,
        "cross_table_proven_mismatch_count": 0,
        "cross_table_not_comparable_dimension_count": 4,
        "cross_table_difference_queue_count": 4,
        "cross_table_difference_queue_is_non_additive": True,
        "cross_table_quality_report_count": 1,
        "current_stage_page_count": 4,
        "cross_page_link_count": 12,
        "broken_cross_page_link_count": 0,
        "cross_page_navigation_strongly_connected": True,
        "browser_status": "PASS",
        "browser_viewport_check_count": 8,
        "representative_interaction_check_count": 8,
        "cross_page_link_http_check_count": 12,
        "cross_page_navigation_check_count": 12,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "fixed_review_finding_count": 9,
        "open_review_finding_count": 0,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "s14_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require("pending_reconciliation_count" not in summary, "historical pending leaked", errors)

    findings = manifest.get("review_findings", [])
    _require(len(findings) == 9, "review finding count mismatch", errors)
    _require(all(row.get("status") == "fixed" for row in findings), "open review finding remains", errors)
    _require(
        {row.get("finding_id") for row in findings}
        == {f"S13-POST-REVIEW-F{index:02d}" for index in range(1, 10)},
        "review finding ids mismatch",
        errors,
    )
    _require(matrix.get("check_fail_count") == 0, "matrix failure", errors)
    _require(matrix.get("check_count") == matrix.get("check_pass_count"), "matrix incomplete", errors)

    quality = manifest.get("quality_gate", {})
    for key in ("current_public_safe_pages_allowed", "restricted_internal_preview_allowed"):
        _require(quality.get(key) is True, f"quality gate {key} mismatch", errors)
    for key in (
        "quality_grade_bypass_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "difference_closure_allowed",
        "business_execution_allowed",
    ):
        _require(quality.get(key) is False, f"quality gate {key} mismatch", errors)
    _require(quality.get("current_data_quality_grade") == "Q4", "quality grade drift", errors)
    _require(quality.get("current_report_grade") == "D", "report grade drift", errors)
    _require(quality.get("decision") == "NO_GO", "quality decision drift", errors)

    boundaries = manifest.get("review_boundaries", {})
    for key in ("s13_p1_validated", "s13_p2_validated", "s13_p3_validated", "stage13_review_performed"):
        _require(boundaries.get(key) is True, f"boundary {key} mismatch", errors)
    for key in (
        "s14_p1_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "difference_closure_performed",
        "business_execution_performed",
        "persistent_business_write_performed",
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} mismatch", errors)

    for key in (
        "historical_review_dependency_validated",
        "historical_pending_twelve_quarantined",
        "historical_static_business_items_quarantined",
        "historical_cross_table_semantics_quarantined",
        "historical_upload_ready_semantics_quarantined",
        "phase_validator_frozen_semantics_validated",
        "cross_page_navigation_validated",
    ):
        _require(manifest.get(key) is True, f"manifest {key} mismatch", errors)
    _require(manifest.get("historical_review_dynamic_state_is_authoritative") is False, "historical state authoritative", errors)
    _require(manifest.get("next_phase") == "S14-P1", "next phase mismatch", errors)

    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "aggregate safety mismatch", errors)
    for key, value in safety.items():
        if key != "aggregate_only":
            _require(value is False, f"public safety {key} mismatch", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    return manifest


def _validate_cross_page_html(errors: list[str]) -> None:
    pages = {page_id: (spec["path"], spec["marker"]) for page_id, spec in phase.PAGE_SPECS.items()}
    for page_id, (path, marker) in pages.items():
        _require(path.is_file(), f"page missing: {page_id}", errors)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        _require(marker in text, f"page marker missing: {page_id}", errors)
        _require("NO_GO" in text and "D" in text, f"D/NO_GO missing: {page_id}", errors)
        _require("gradient(" not in text, f"gradient found: {page_id}", errors)
        _require("pending_reconciliation_count" not in text, f"historical pending leaked: {page_id}", errors)
    for source_id, target_id, selector in phase.LINK_SPECS:
        source_path = phase.PAGE_SPECS[source_id]["path"]
        text = source_path.read_text(encoding="utf-8")
        attr_match = re.search(
            re.escape(selector.split("[")[1].split("=")[0]) + r'(?:="[^"]+")?[^>]*href="([^"]+)"',
            text,
        )
        if selector == "a[data-other-draft]":
            attr_match = re.search(r'<a[^>]+data-other-draft[^>]+href="([^"]+)"', text)
        elif '="' in selector:
            attr, value = selector.split("[")[1].rstrip("]").split("=", 1)
            value = value.strip('"')
            attr_match = re.search(
                rf'<a[^>]+{re.escape(attr)}="{re.escape(value)}"[^>]+href="([^"]+)"|<a[^>]+href="([^"]+)"[^>]+{re.escape(attr)}="{re.escape(value)}"',
                text,
            )
        _require(bool(attr_match), f"link selector missing: {source_id}->{target_id}", errors)
        if attr_match:
            href = next((value for value in attr_match.groups() if value), "")
            target = (source_path.parent / href).resolve()
            _require(target == phase.PAGE_SPECS[target_id]["path"].resolve(), f"link target drift: {source_id}->{target_id}", errors)
            _require(target.is_file(), f"link target missing: {source_id}->{target_id}", errors)
    weekly = phase.p1.WEEKLY_HTML_PATH.read_text(encoding="utf-8")
    monthly = phase.p1.MONTHLY_HTML_PATH.read_text(encoding="utf-8")
    for page_id, text in (("weekly", weekly), ("monthly", monthly)):
        _require(text.count("data-stage-link=") == 2, f"P1 stage link count mismatch: {page_id}", errors)
        _require("Stage 13 三个 phase 均已完成" in text, f"P1 current status missing: {page_id}", errors)
        _require("Stage 13 仅完成 S13-P1" not in text, f"P1 stale status remains: {page_id}", errors)
    p2_text = phase.p2.HTML_PATH.read_text(encoding="utf-8")
    _require(p2_text.count("data-report-link=") == 3, "P2 stage link count mismatch", errors)
    p3_text = phase.p3.HTML_PATH.read_text(encoding="utf-8")
    _require(p3_text.count("data-dependency-link=") == 3, "P3 stage link count mismatch", errors)


def _validate_dependencies(errors: list[str]) -> None:
    try:
        p1_manifest = validate_v014_s13_p1_post_remediation_financial_operating_report(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        p2_manifest = validate_v014_s13_p2_post_remediation_collection_receivable_aging(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        p3_manifest = validate_v014_s13_p3_post_remediation_cross_table_review(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
    except Exception as exc:
        errors.append(f"current phase dependency failed: {exc}")
        return
    _require(p1_manifest.get("summary", {}).get("raw_value_bound_lane_count") == 0, "P1 value binding drift", errors)
    _require(p1_manifest.get("browser_review", {}).get("current_pass_count") == 20, "P1 audit drift", errors)
    _require(p2_manifest.get("summary", {}).get("identified_business_item_count") == 0, "P2 business item drift", errors)
    _require(p2_manifest.get("browser_review", {}).get("dependency_navigation_check_count") == 3, "P2 navigation drift", errors)
    p3_summary = p3_manifest.get("summary", {})
    _require(p3_summary.get("not_comparable_dimension_count") == 4, "P3 not-comparable drift", errors)
    _require(p3_summary.get("difference_queue_is_non_additive") is True, "P3 queue semantics drift", errors)


def _validate_governance(errors: list[str]) -> None:
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    statuses = [row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    tasks = [row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("fixed_review_finding_count") == 9, "event finding count mismatch", errors)
        _require(events[0].get("open_review_finding_count") == 0, "event open finding mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "event upload mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "phase_pass_count == 3",
        "financial_raw_value_bound_lane_count == 0",
        "receivable_identified_business_item_count == 0",
        "cross_table_not_comparable_dimension_count == 4",
        "cross_table_exact_comparison_count == 0",
        "cross_table_difference_queue_is_non_additive == true",
        "cross_page_link_count == 12",
        "fixed_review_finding_count == 9",
        "open_review_finding_count == 0",
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
    expected = {
        "PARAM-KMFA-1747": "3;4;4;0;2;5;3;0;4;0;4;0;0;4;4;true;1;4;12;0;8;8;12;12;9;0;5;3;9;2;1;Q4;D;NO_GO",
        "PARAM-KMFA-1748": "true;true;true;true;true;true;true;false;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1749": "true;true;true;true;true;false;false;false;false;NO_GO",
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
        _require("下一步只能执行 S14-P1" in handoff, "HANDOFF next phase missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require("Stage 13 整体复审" in agents and "S14-P1" in agents, "AGENTS scope drift", errors)

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
        (Path("KMFA/功能清单.md"), "Stage 13 修补后整体复审"),
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
        phase.PRIVATE_REVIEW_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.p3.PRIVATE_RAW_AFTER_PATH)
        raw_helper = phase.p1.s12_review.p1.s11_project
        current = raw_helper._raw_snapshot("validate_v014_s13_post_remediation_stage_review")
        normalize = raw_helper._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-S13-P3 mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        report = phase.PRIVATE_REVIEW_REPORT_PATH.read_text(encoding="utf-8")
        for token in (
            "3 / 9 / 2 / 1",
            "4 NOT_COMPARABLE / 0 exact / 4 non-additive queue",
            "本轮无需生成 raw 差异报告",
            "全中文最终差异报告",
            "不推断、不平均、不补零",
        ):
            _require(token in report, f"private report token missing: {token}", errors)

    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BROWSER_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_P1_AUDIT_PATH,
        phase.PRIVATE_P2_AUDIT_PATH,
        phase.PRIVATE_P3_AUDIT_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    _read_audit(phase.PRIVATE_P1_AUDIT_PATH, errors, 2, 20)
    _read_audit(phase.PRIVATE_P2_AUDIT_PATH, errors, 1, 7)
    _read_audit(phase.PRIVATE_P3_AUDIT_PATH, errors, 1, 7)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        expected_counts = {
            "viewport_checks": 8,
            "representative_interaction_checks": 8,
            "cross_page_link_http_checks": 12,
            "cross_page_navigation_checks": 12,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} mismatch", errors)
        for key in (
            "representative_interaction_checks",
            "cross_page_link_http_checks",
            "cross_page_navigation_checks",
        ):
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
    for page_id in phase.PAGE_SPECS:
        for mode, width in (("desktop", 1440), ("mobile", 390)):
            path = phase.PRIVATE_SCREENSHOT_DIR / f"{page_id}_{mode}.png"
            _require(path.is_file(), f"screenshot missing: {path}", errors)
            _require(_git_check_ignore(path), f"screenshot not ignored: {path}", errors)
            _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
            if path.is_file():
                actual_width, height = _png_dimensions(path)
                _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
                _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s13_post_remediation_stage_review(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_cross_page_html(errors)
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
            "focused_phase_tests",
            "review_tests",
            "strict_validator",
            "browser_cross_page_flow",
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
    manifest = validate_v014_s13_post_remediation_stage_review(
        require_private_evidence=args.require_private_evidence,
        require_browser_evidence=args.require_browser_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "Stage 13 strict review PASS: "
        f"phases=3 findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
