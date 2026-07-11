#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 12 post-remediation review evidence."""

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

from KMFA.tools import v014_s12_post_remediation_stage_review as phase
from KMFA.tools.check_v014_s12_p1_post_remediation_pending_actions import (
    validate_v014_s12_p1_post_remediation_pending_actions,
)
from KMFA.tools.check_v014_s12_p2_post_remediation_impact_preview import (
    validate_v014_s12_p2_post_remediation_impact_preview,
)
from KMFA.tools.check_v014_s12_p3_post_remediation_rerun_mechanism import (
    validate_v014_s12_p3_post_remediation_rerun_mechanism,
)


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
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


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
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public suffix: {path}", errors)
    text = path.read_text(encoding="utf-8", errors="ignore")
    _require(RAW_ROOT_TOKEN not in text, f"raw root token leaked in {path}", errors)
    _require(LOCAL_DOWNLOADS_PATTERN.search(text) is None, f"local Downloads path leaked in {path}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like token in {path}", errors)
    if path.suffix.lower() == ".json":
        for key in _walk_keys(json.loads(text)):
            _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden public key {key!r} in {path}", errors)


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
        "stage_id": "S12",
        "phase_id": phase.PHASE_ID,
        "roadmap_phase_id": "STAGE-REVIEW",
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "review_scope": phase.REVIEW_SCOPE,
        "status": phase.STATUS,
        "decision": "NO_GO",
        "pending_action_group_count": 6,
        "manual_event_template_count": 4,
        "manual_action_kind_count": 4,
        "impact_preview_definition_count": 6,
        "high_risk_preview_count": 5,
        "second_confirmation_required_count": 5,
        "potential_affected_project_slot_count": 4,
        "rerun_plan_definition_count": 6,
        "required_rerun_chain_layer_count": 4,
        "planned_rerun_step_count": 24,
        "current_approved_business_event_count": 0,
        "current_published_business_event_count": 0,
        "current_persistent_cache_invalidation_count": 0,
        "current_persistent_rerun_step_count": 0,
        "current_persistent_consistency_check_count": 0,
        "current_stage_page_count": 3,
        "cross_page_link_count": 6,
        "broken_cross_page_link_count": 0,
        "browser_viewport_check_count": 6,
        "representative_interaction_check_count": 6,
        "cross_page_link_http_check_count": 6,
        "cross_page_navigation_check_count": 6,
        "console_error_count": 0,
        "horizontal_overflow_count": 0,
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "hard_block_count": 12,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "project_specific_attributed_difference_count": 0,
        "project_specific_unknown_allocation_count": 4,
        "formal_report_count": 0,
        "business_decision_basis_allowed_count": 0,
        "fixed_review_finding_count": 7,
        "open_review_finding_count": 0,
        "raw_source_file_count": 5,
        "s13_p1_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require(summary.get("phase_results") == {"S12-P1": "PASS", "S12-P2": "PASS", "S12-P3": "PASS"}, "phase results mismatch", errors)
    for key in ("cross_page_navigation_strongly_connected", "raw_snapshot_exact_match", "raw_cross_phase_snapshot_exact_match"):
        _require(summary.get(key) is True, f"summary {key} must be true", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending field leaked into summary", errors)

    findings = manifest.get("review_findings", [])
    _require(len(findings) == 7, "review finding count mismatch", errors)
    _require(all(item.get("status") == "fixed" for item in findings), "review finding remains open", errors)
    for key in (
        "phase_validator_frozen_semantics_validated",
        "cross_page_navigation_validated",
        "historical_review_dependency_validated",
        "historical_five_events_quarantined",
        "historical_two_eligible_events_quarantined",
        "historical_eight_rerun_steps_quarantined",
    ):
        _require(manifest.get(key) is True, f"manifest {key} must be true", errors)
    _require(manifest.get("historical_review_dynamic_state_is_authoritative") is False, "historical review became authoritative", errors)

    quality = manifest.get("quality_gate", {})
    for key, value in {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "stage12_public_safe_pages_allowed": True,
        "restricted_internal_preview_allowed": True,
        "quality_grade_bypass_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
    }.items():
        _require(quality.get(key) == value, f"quality {key} mismatch", errors)

    boundaries = manifest.get("review_boundaries", {})
    for key in ("s12_p1_validated", "s12_p2_validated", "s12_p3_validated", "stage12_review_performed"):
        _require(boundaries.get(key) is True, f"boundary {key} must be true", errors)
    for key in (
        "s13_p1_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "business_execution_performed",
        "persistent_business_write_performed",
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence must be aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety drift", errors)

    _require(matrix.get("check_count") == 30, "matrix count mismatch", errors)
    _require(matrix.get("check_pass_count") == 30, "matrix pass count mismatch", errors)
    _require(matrix.get("check_fail_count") == 0, "matrix contains failures", errors)
    _require(all(item.get("passed") is True for item in matrix.get("checks", [])), "matrix row failed", errors)
    _require(go_no_go.get("decision") == "NO_GO", "go/no-go decision mismatch", errors)
    _require(go_no_go.get("stage12_review_validated") is True, "go/no-go review flag mismatch", errors)
    for key in (
        "quality_grade_bypass_allowed",
        "formal_report_allowed",
        "business_decision_basis_allowed",
        "s13_p1_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "business_execution_performed",
    ):
        _require(go_no_go.get(key) is False, f"go/no-go {key} must be false", errors)
    return manifest


def _validate_cross_page_html(errors: list[str]) -> None:
    pages = {
        "pending": (phase.p1.HTML_PATH, phase.p1.HTML_PATH.read_text(encoding="utf-8")),
        "impact": (phase.p2.HTML_PATH, phase.p2.HTML_PATH.read_text(encoding="utf-8")),
        "rerun": (phase.p3.HTML_PATH, phase.p3.HTML_PATH.read_text(encoding="utf-8")),
    }

    def href(text: str, link_id: str) -> str:
        match = re.search(
            rf'<a[^>]+data-return-link="{re.escape(link_id)}"[^>]+href="([^"]+)"',
            text,
        )
        return match.group(1) if match else ""

    page_hrefs = {
        "pending": [href(pages["pending"][1], "impact"), href(pages["pending"][1], "rerun")],
        "impact": [href(pages["impact"][1], "pending"), href(pages["impact"][1], "rerun")],
        "rerun": [href(pages["rerun"][1], "pending"), href(pages["rerun"][1], "impact")],
    }
    expected_hrefs = {
        "pending": [phase.p1.P2_HREF, phase.p1.P3_HREF],
        "impact": [phase.p2.P1_HREF, phase.p2.P3_HREF],
        "rerun": [phase.p3.P1_HREF, phase.p3.P2_HREF],
    }
    _require(page_hrefs == expected_hrefs, "current Stage 12 cross-page links mismatch", errors)
    for page_id, hrefs in page_hrefs.items():
        origin = pages[page_id][0]
        for href in hrefs:
            _require((origin.parent / href).resolve().is_file(), f"cross-page target missing: {origin}:{href}", errors)
    for page_id, (_path, text) in pages.items():
        _require("NO_GO" in text, f"NO_GO missing from {page_id}", errors)
        _require("D级" in text or "Q4 / D" in text, f"D grade missing from {page_id}", errors)
        _require("gradient(" not in text, f"gradient surface found in {page_id}", errors)
    _require("后续独立 phase" not in pages["pending"][1], "P1 stale future phase label remains", errors)
    _require("后续独立 phase" not in pages["impact"][1], "P2 stale future phase label remains", errors)
    _require("S12-P3 重跑未执行" not in pages["impact"][1], "P2 stale P3 boundary remains", errors)


def _validate_dependencies(errors: list[str]) -> None:
    try:
        p1_manifest = validate_v014_s12_p1_post_remediation_pending_actions(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        p2_manifest = validate_v014_s12_p2_post_remediation_impact_preview(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
        p3_manifest = validate_v014_s12_p3_post_remediation_rerun_mechanism(
            require_private_evidence=True,
            require_browser_evidence=True,
            require_final_evidence=True,
        )
    except Exception as exc:
        errors.append(f"current phase dependency failed: {exc}")
        return
    _require(p1_manifest.get("summary", {}).get("pending_action_group_count") == 6, "P1 pending groups drift", errors)
    _require(p2_manifest.get("summary", {}).get("impact_preview_definition_count") == 6, "P2 impact previews drift", errors)
    p3_summary = p3_manifest.get("summary", {})
    _require(p3_summary.get("rerun_plan_definition_count") == 6, "P3 rerun plans drift", errors)
    _require(p3_summary.get("current_persistent_rerun_step_count") == 0, "P3 persistent rerun drift", errors)


def _validate_governance(errors: list[str]) -> None:
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    statuses = [row for row in _read_jsonl(phase.STAGE_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    tasks = [row for row in _read_jsonl(phase.TASK_STATUS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    _require(len(events) == 1, "development event missing or duplicated", errors)
    _require(len(statuses) == 1, "stage status missing or duplicated", errors)
    _require(len(tasks) == 1, "task status missing or duplicated", errors)
    if events:
        _require(events[0].get("fixed_review_finding_count") == 7, "development finding count mismatch", errors)
        _require(events[0].get("github_upload_performed") is False, "development upload flag mismatch", errors)
    if statuses:
        _require(statuses[0].get("status") == phase.STATUS, "stage status value mismatch", errors)
    if tasks:
        _require(tasks[0].get("acceptance_id") == phase.ACCEPTANCE_ID, "task acceptance mismatch", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula record missing", errors)
    for token in (
        "phase_pass_count == 3",
        "pending_action_group_count == 6",
        "impact_preview_definition_count == 6",
        "rerun_plan_definition_count == 6",
        "planned_rerun_step_count == 24",
        "persistent_rerun_step_count == 0",
        "cross_page_link_count == 6",
        "broken_cross_page_link_count == 0",
        "fixed_review_finding_count == 7",
        "open_review_finding_count == 0",
        "current_grade == D",
        "project_specific_attributed_difference_count == 0",
        "potential_affected_project_slot_count == 4",
    ):
        _require(token in formula_text, f"formula control missing: {token}", errors)
    for path in (Path("KMFA/docs/governance/model_registry.yaml"), Path("KMFA/metadata/model_registry.yaml")):
        text = path.read_text(encoding="utf-8")
        _require(phase.MODEL_REGISTRY_KEY in text, f"model registry key missing in {path}", errors)
        _require(phase.FORMULA_ID in text, f"formula ref missing in {path}", errors)
        for parameter_id in phase.PARAMETER_IDS:
            _require(parameter_id in text, f"parameter ref missing in {path}: {parameter_id}", errors)

    with Path("KMFA/docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
        parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
    expected = {
        "PARAM-KMFA-1732": "6;4;6;5;5;6;4;24;0;0;0;0;0;3;9;2;1;12;5;3;6;6;6;7;0;Q4;D;NO_GO",
        "PARAM-KMFA-1733": "true;true;true;true;true;true;true;true;true;false;false;false;false;false;false;false;false;false;NO_GO",
        "PARAM-KMFA-1734": "true;true;true;true;true;true;false;false;false;false;false;false;false;false;false;false;NO_GO",
    }
    for parameter_id, expected_value in expected.items():
        row = parameters.get(parameter_id, {})
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected_value, f"parameter drift: {parameter_id}:{field}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    phase_is_current = _phase_is_current(version_matrix)
    _require(phase.MODEL_REGISTRY_KEY in version_matrix, "VERSION_MATRIX phase profile missing", errors)
    _require(phase.VERSION in version_matrix, "VERSION_MATRIX phase version missing", errors)
    if phase_is_current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF current phase drift", errors)
        _require("S13-P1" in handoff, "HANDOFF next phase missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
    traceability = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in traceability and phase.ACCEPTANCE_ID in traceability, "traceability record missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "Stage 12 修补后整体复审"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing in {path}", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int = 0) -> None:
    _require(path.is_file(), f"browser audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len({row.get("file") for row in rows}) == expected_files, f"browser audit file count mismatch: {path}", errors)
    if expected_rows:
        _require(len(rows) == expected_rows, f"browser audit row count mismatch: {path}", errors)
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
        current = phase.p1.s11_project._raw_snapshot("validate_v014_s12_post_remediation_stage_review")
        normalize = phase.p1.s11_project._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        report = phase.PRIVATE_REVIEW_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("无需生成最终差异报告", "不推断、不平均、不补零", "3 / 9 / 2 / 1"):
            _require(token in report, f"private review report missing token: {token}", errors)

    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BROWSER_PATH,
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_PENDING_AUDIT_PATH,
        phase.PRIVATE_IMPACT_AUDIT_PATH,
        phase.PRIVATE_RERUN_AUDIT_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    for path in (phase.PRIVATE_PENDING_AUDIT_PATH, phase.PRIVATE_IMPACT_AUDIT_PATH, phase.PRIVATE_RERUN_AUDIT_PATH):
        _read_audit(path, errors, 1)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        expected_counts = {
            "viewport_checks": 6,
            "representative_interaction_checks": 6,
            "cross_page_link_http_checks": 6,
            "cross_page_navigation_checks": 6,
        }
        for key, count in expected_counts.items():
            _require(len(browser.get(key, [])) == count, f"browser {key} count mismatch", errors)
        for key in ("representative_interaction_checks", "cross_page_link_http_checks", "cross_page_navigation_checks"):
            _require(all(item.get("passed") is True for item in browser.get(key, [])), f"browser {key} failed", errors)
        _require(all(
            item.get("marker_visible") is True
            and item.get("d_no_go_visible") is True
            and item.get("console_error_count") == 0
            and item.get("no_horizontal_overflow") is True
            for item in browser.get("viewport_checks", [])
        ), "browser viewport safety failed", errors)
    for page_id in ("pending", "impact", "rerun"):
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
def validate_v014_s12_post_remediation_stage_review(
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
        manifest = validate_v014_s12_post_remediation_stage_review(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: Stage 12 post-remediation review "
        f"phases=3 findings={summary['fixed_review_finding_count']}/0 "
        f"links={summary['cross_page_link_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
