#!/usr/bin/env python3
"""Validate current public-safe KMFA S12-P1 pending-action evidence."""

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

from KMFA.tools import v014_s12_p1_post_remediation_pending_actions as phase


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
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", path.as_posix()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


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
        phase.GROUPS_PATH,
        phase.EVENT_TEMPLATES_PATH,
        phase.GO_NO_GO_PATH,
        phase.HTML_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_GROUPS_PATH,
        phase.METADATA_EVENT_TEMPLATES_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )
    for path in public_paths:
        _check_public_file(path, errors)
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    groups_payload = _read_json(phase.GROUPS_PATH)
    templates_payload = _read_json(phase.EVENT_TEMPLATES_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    _require(summary == _read_json(phase.METADATA_SUMMARY_PATH), "summary mirror drift", errors)
    _require(manifest == _read_json(phase.METADATA_MANIFEST_PATH), "manifest mirror drift", errors)
    _require(groups_payload == _read_json(phase.METADATA_GROUPS_PATH), "groups mirror drift", errors)
    _require(
        templates_payload == _read_json(phase.METADATA_EVENT_TEMPLATES_PATH),
        "event templates mirror drift",
        errors,
    )
    _require(go_no_go == _read_json(phase.METADATA_GO_NO_GO_PATH), "go/no-go mirror drift", errors)
    _require(manifest.get("summary") == summary, "manifest summary drift", errors)
    _require(manifest.get("pending_action_groups") == groups_payload.get("groups"), "manifest groups drift", errors)
    _require(
        manifest.get("manual_event_templates") == templates_payload.get("templates"),
        "manifest templates drift",
        errors,
    )
    return manifest


def _validate_summary(manifest: dict[str, Any], errors: list[str]) -> None:
    summary = manifest.get("summary", {})
    expected = {
        "stage_id": "S12",
        "roadmap_phase_id": "S12-P1",
        "phase_id": phase.PHASE_ID,
        "task_id": phase.TASK_ID,
        "acceptance_id": phase.ACCEPTANCE_ID,
        "version": phase.VERSION,
        "status": phase.STATUS,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        "project_specific_unknown_allocation_count": 4,
        "source_check_matrix_row_count": 13,
        "hard_block_count": 12,
        "pending_action_group_count": 6,
        "manual_event_template_count": 4,
        "manual_action_kind_count": 4,
        "current_approved_business_event_count": 0,
        "current_persistent_business_event_count": 0,
        "historical_approved_policy_fixture_count": 1,
        "historical_reverse_policy_fixture_count": 1,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "s12_p2_performed": False,
        "s12_p3_performed": False,
        "stage12_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    for key, value in expected.items():
        _require(summary.get(key) == value, f"summary {key} mismatch", errors)
    _require("pending_reconciliation_count" not in summary, "stale pending=12 field present", errors)
    _require(
        manifest.get("stage11_post_remediation_review_dependency_validated") is True,
        "Stage 11 dependency flag missing",
        errors,
    )
    _require(manifest.get("next_phase") == "S12-P2", "next phase mismatch", errors)


def _validate_groups_and_templates(manifest: dict[str, Any], errors: list[str]) -> None:
    groups = manifest.get("pending_action_groups", [])
    templates = manifest.get("manual_event_templates", [])
    _require(len(groups) == 6, "pending group count mismatch", errors)
    _require(len({row.get("group_id") for row in groups}) == 6, "pending group ids not unique", errors)
    required_kinds = set(phase.ACTION_LABELS)
    _require({row.get("manual_action_kind") for row in groups} == required_kinds, "group action kinds mismatch", errors)
    for row in groups:
        for key in (
            "group_id",
            "visible_title",
            "manual_action_kind",
            "item_count",
            "responsible_role",
            "status",
            "impact_summary",
            "next_step",
        ):
            _require(row.get(key) not in (None, ""), f"group missing {key}", errors)
        _require(row.get("project_attribution") == "unknown_or_not_applicable", "group attribution drift", errors)
        _require(row.get("session_candidate_only") is True, "group not session-only", errors)
        _require(row.get("persistent_business_write_allowed") is False, "group persistent write allowed", errors)
        _require(row.get("raw_layer_write_allowed") is False, "group raw write allowed", errors)
        _require(row.get("public_amount_values_committed") is False, "group amount value committed", errors)

    _require(len(templates) == 4, "event template count mismatch", errors)
    _require({row.get("manual_action_kind") for row in templates} == required_kinds, "template action kinds mismatch", errors)
    required_fields = {
        "event_id",
        "manual_action_kind",
        "actor_ref",
        "event_time_policy",
        "reason_code",
        "impact_scope",
        "event_version",
    }
    for row in templates:
        _require(required_fields <= set(row), "event template required fields missing", errors)
        _require(row.get("append_only") is True, "event template not append-only", errors)
        _require(row.get("session_candidate_only") is True, "event template not session-only", errors)
        _require(row.get("approval_state") == "draft", "event template is not draft", errors)
        _require(row.get("silent_update_allowed") is False, "event template permits silent update", errors)
        _require(row.get("persistent_business_write_allowed") is False, "event template permits persistence", errors)
        _require(row.get("raw_layer_write_allowed") is False, "event template permits raw write", errors)
        _require(row.get("public_amount_values_committed") is False, "event template exposes amount", errors)
    fixture = manifest.get("approved_event_reversal_policy_fixture", {})
    _require(fixture.get("historical_approved_event_count") == 1, "approved fixture count mismatch", errors)
    _require(fixture.get("historical_reverse_event_count") == 1, "reverse fixture count mismatch", errors)
    _require(fixture.get("reverse_chain_validated") is True, "reverse fixture not validated", errors)
    _require(fixture.get("current_business_resolution_applied") is False, "fixture applied to business state", errors)
    _require(fixture.get("approved_event_silent_update_allowed") is False, "fixture silent update allowed", errors)
    _require(fixture.get("approved_event_reversal_required_for_change") is True, "fixture reversal not required", errors)


def _validate_html(errors: list[str]) -> None:
    if not phase.HTML_PATH.is_file():
        return
    text = phase.HTML_PATH.read_text(encoding="utf-8")
    for token in (
        "待处理事项",
        "处理人",
        "状态",
        "影响",
        "下一步",
        "字段映射",
        "项目匹配",
        "差异处理",
        "备注",
        "生成候选事件",
        "追加反向事件候选",
        'data-pending-search',
        'data-kind-filter',
        'data-status-filter',
        'aria-live="polite"',
        "new Date().toISOString()",
        "Q4 / D · NO_GO",
    ):
        _require(token in text, f"HTML token missing: {token}", errors)
    for forbidden in (
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "XMLHttpRequest",
        "fetch(",
        "data-impact",
        "data-rerun",
    ):
        _require(forbidden not in text, f"HTML forbidden runtime: {forbidden}", errors)
    for link_id, href, _marker in phase.RETURN_LINKS:
        _require(
            f'data-return-link="{link_id}" href="{href}"' in text,
            f"return link missing: {link_id}",
            errors,
        )


def _validate_dependencies(errors: list[str]) -> None:
    stage11 = phase._load_stage11_dependency()
    contract = phase._load_contract()
    _require(stage11.get("phase_id") == "V014_S11_POST_REMEDIATION_STAGE_REVIEW", "Stage 11 phase mismatch", errors)
    _require(stage11.get("validation_summary", {}).get("final_validation_recorded") is True, "Stage 11 final validation missing", errors)
    _require(contract.get("roadmap_contract_read") is True, "roadmap contract not read", errors)
    _require(contract.get("taskpack_human_flow_gate_read") is True, "taskpack human-flow gate not read", errors)
    _require(contract.get("clickable_workbench_sample_read") is True, "workbench sample not read", errors)
    _require(contract.get("legacy_reverse_chain_validated") is True, "legacy reverse chain invalid", errors)


def _validate_boundaries(manifest: dict[str, Any], errors: list[str]) -> None:
    boundaries = manifest.get("phase_boundaries", {})
    for key in ("stage11_post_remediation_review_dependency_validated", "s12_p1_performed"):
        _require(boundaries.get(key) is True, f"boundary {key} must be true", errors)
    for key in (
        "s12_p2_performed",
        "s12_p3_performed",
        "stage12_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "formal_report_release_performed",
        "persistent_business_write_performed",
        "business_execution_performed",
        "raw_write_performed",
        "raw_delete_performed",
        "raw_move_performed",
        "raw_rename_performed",
        "raw_overwrite_performed",
    ):
        _require(boundaries.get(key) is False, f"boundary {key} must be false", errors)
    quality = manifest.get("quality_gate", {})
    for key, value in {
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "decision": "NO_GO",
        "release_permission": "blocked",
        "candidate_event_creation_allowed": True,
        "control_event_append_only": True,
        "approved_event_silent_update_allowed": False,
        "approved_event_reversal_required_for_change": True,
        "current_business_event_approval_allowed": False,
        "impact_preview_publish_allowed": False,
        "derived_rerun_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "raw_layer_write_allowed": False,
        "github_upload_allowed": False,
    }.items():
        _require(quality.get(key) == value, f"quality {key} mismatch", errors)
    safety = manifest.get("public_repo_safety", {})
    _require(safety.get("aggregate_only") is True, "public evidence not aggregate-only", errors)
    _require(all(value is False for key, value in safety.items() if key != "aggregate_only"), "public safety drift", errors)


def _validate_governance(errors: list[str]) -> None:
    matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in matrix, "VERSION_MATRIX profile missing", errors)
    _require(phase.VERSION in matrix, "VERSION_MATRIX version missing", errors)
    _require(phase.FORMULA_ID in Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8"), "formula missing", errors)
    model_text = Path("KMFA/docs/governance/model_registry.yaml").read_text(encoding="utf-8")
    metadata_model_text = Path("KMFA/metadata/model_registry.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in model_text, "model registry missing", errors)
    _require(phase.MODEL_REGISTRY_KEY in metadata_model_text, "metadata model registry missing", errors)
    parameter_text = Path("KMFA/docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in parameter_text, f"parameter missing: {parameter_id}", errors)
    _require(phase.TASK_ID in Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8"), "delivery task missing", errors)
    _require(phase.TASK_ID in Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"), "traceability missing", errors)
    for path in (
        Path("KMFA/CHANGELOG.md"),
        Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"),
        Path("KMFA/docs/governance/MODEL_SPEC.md"),
        Path("KMFA/功能清单.md"),
        Path("KMFA/开发记录.md"),
        Path("KMFA/模型参数文件.md"),
    ):
        _require(phase.PHASE_ID in path.read_text(encoding="utf-8"), f"governance doc missing phase: {path}", errors)
    if _phase_is_current(matrix):
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(f"phase: `{phase.PHASE_ID}`" in handoff, "HANDOFF phase drift", errors)
        _require("S12-P2" in handoff, "HANDOFF next phase missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)


def _read_audit(path: Path, errors: list[str], expected_files: int, expected_rows: int = 0) -> None:
    _require(path.is_file(), f"audit missing: {path}", errors)
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _require(len({row.get("file") for row in rows if row.get("file")}) == expected_files, f"audit file count mismatch: {path}", errors)
    if expected_rows:
        _require(len(rows) == expected_rows, f"audit row count mismatch: {path}", errors)
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
        phase.PRIVATE_VALIDATION_REPORT_PATH,
    )
    for path in private_paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if all(path.is_file() for path in private_paths):
        before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
        after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
        prior = _read_json(phase.s11_review.PRIVATE_RAW_AFTER_PATH)
        current = phase.s11_project._raw_snapshot("validate_v014_s12_p1_post_remediation_pending_actions")
        normalize = phase.s11_project._normalize_raw
        _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
        _require(normalize(before) == normalize(prior), "raw cross-phase mismatch", errors)
        _require(normalize(after) == normalize(current), "raw current mismatch", errors)
        _require(before.get("file_count") == 5, "raw file count mismatch", errors)
        report = phase.PRIVATE_VALIDATION_REPORT_PATH.read_text(encoding="utf-8")
        for token in ("before = after = Stage 11 prior = current: true", "无需生成本 phase 差异报告"):
            _require(token in report, f"private report token missing: {token}", errors)
    if not require_browser_evidence:
        return
    browser_paths = (
        phase.PRIVATE_BASELINE_AUDIT_PATH,
        phase.PRIVATE_CURRENT_AUDIT_PATH,
        phase.PRIVATE_BROWSER_PATH,
    )
    for path in browser_paths:
        _require(path.is_file(), f"browser evidence missing: {path}", errors)
        _require(_git_check_ignore(path), f"browser evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"browser evidence tracked: {path}", errors)
    _read_audit(phase.PRIVATE_BASELINE_AUDIT_PATH, errors, 6, 54)
    _read_audit(phase.PRIVATE_CURRENT_AUDIT_PATH, errors, 1)
    if phase.PRIVATE_BROWSER_PATH.is_file():
        browser = _read_json(phase.PRIVATE_BROWSER_PATH)
        _require(browser.get("status") == "PASS", "browser status mismatch", errors)
        expected_lengths = {
            "viewport_checks": 2,
            "search_checks": 2,
            "kind_filter_checks": 2,
            "status_filter_checks": 2,
            "row_selection_checks": 2,
            "candidate_event_checks": 2,
            "reverse_event_checks": 2,
            "reload_reset_checks": 2,
            "return_link_http_checks": 3,
            "actual_navigation_checks": 3,
        }
        for key, count in expected_lengths.items():
            rows = browser.get(key, [])
            _require(len(rows) == count, f"browser {key} count mismatch", errors)
            _require(all(row.get("passed") is True for row in rows), f"browser {key} failed", errors)
        _require(
            all(
                row.get("console_error_count") == 0
                and row.get("no_horizontal_overflow") is True
                and row.get("no_go_visible") is True
                for row in browser.get("viewport_checks", [])
            ),
            "browser viewport safety failed",
            errors,
        )
    for name, width in (("pending_actions_desktop.png", 1440), ("pending_actions_mobile.png", 390)):
        path = phase.PRIVATE_SCREENSHOT_DIR / name
        _require(path.is_file(), f"screenshot missing: {path}", errors)
        _require(_git_check_ignore(path), f"screenshot not ignored: {path}", errors)
        _require(not _git_tracked(path), f"screenshot tracked: {path}", errors)
        if path.is_file():
            actual_width, height = _png_dimensions(path)
            _require(actual_width == width, f"screenshot width mismatch: {path}", errors)
            _require(height >= 700, f"screenshot height too small: {path}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s12_p1_post_remediation_pending_actions(
    *,
    require_private_evidence: bool = False,
    require_browser_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_summary(manifest, errors)
    _validate_groups_and_templates(manifest, errors)
    _validate_html(errors)
    _validate_dependencies(errors)
    _validate_boundaries(manifest, errors)
    _validate_governance(errors)
    if require_private_evidence:
        _validate_private(errors, require_browser_evidence)
    elif require_browser_evidence:
        errors.append("browser evidence requires private evidence")
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
        manifest = validate_v014_s12_p1_post_remediation_pending_actions(
            require_private_evidence=args.require_private_evidence,
            require_browser_evidence=args.require_browser_evidence,
            require_final_evidence=args.require_final_evidence,
        )
    except (ValidationError, ValueError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    summary = manifest["summary"]
    print(
        "PASS: S12-P1 post-remediation pending actions "
        f"groups={summary['pending_action_group_count']} templates={summary['manual_event_template_count']} "
        f"approved={summary['current_approved_business_event_count']} grade={summary['current_report_grade']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
