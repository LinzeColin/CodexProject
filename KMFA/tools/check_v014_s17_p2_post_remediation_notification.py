#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S17-P2 notification evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_p2_post_remediation_notification as phase
from KMFA.tools.check_v014_s17_p1_post_remediation_access_security import (
    validate_v014_s17_p1_post_remediation_access_security,
)
from KMFA.tools.check_v014_s17_p2_notification_policy import (
    validate_v014_s17_p2_notification_policy as validate_historical_s17_p2,
)


FORBIDDEN_PUBLIC_SUFFIXES = {".zip", ".xlsx", ".xls", ".pdf", ".db", ".sqlite"}
FORBIDDEN_PUBLIC_TEXT = (
    "private_ref://",
    "original_filename",
    "sheet_name_private",
    "source_header_text",
    "raw_value",
    "normalized_value",
    "customer_name_plaintext",
    "project_name_plaintext",
    "counterparty_name_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "/Users/linzezhang/Downloads",
    "KMFA_MetaData",
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_path_private",
    "raw_filename_private",
    "member_name_private",
    "sheet_name_private",
    "preview_rows_private",
    "raw_value",
    "normalized_value",
    "amount_cents",
    "amount_yuan",
    "payment_account",
    "bank_account_number",
    "contract_number",
    "invoice_number",
    "recipient_email",
    "recipient_address",
    "report_attachment_path",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_=-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
)


class ValidationError(Exception):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"missing JSONL: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _git_ignored(path: Path) -> bool:
    return subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _git_tracked(path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def _walk(value: Any, key: str = "") -> list[tuple[str, Any]]:
    rows = [(key, value)]
    if isinstance(value, dict):
        for child_key, child in value.items():
            rows.extend(_walk(child, str(child_key)))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_walk(child, key))
    return rows


def _public_paths() -> tuple[Path, ...]:
    return (
        phase.SUMMARY_PATH,
        phase.MANIFEST_PATH,
        phase.RULE_PATH,
        phase.TRIGGER_EVALUATION_PATH,
        phase.OUTBOX_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_RULE_PATH,
        phase.METADATA_TRIGGER_EVALUATION_PATH,
        phase.METADATA_OUTBOX_PATH,
        phase.METADATA_MATRIX_PATH,
        phase.METADATA_GO_NO_GO_PATH,
    )


def _scan_public(path: Path, errors: list[str]) -> None:
    _require(path.is_file(), f"public evidence missing: {path}", errors)
    if not path.is_file():
        return
    _require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden suffix: {path}", errors)
    data = path.read_bytes()
    _require(b"\x00" not in data, f"binary public evidence: {path}", errors)
    text = data.decode("utf-8")
    for token in FORBIDDEN_PUBLIC_TEXT:
        _require(token not in text, f"forbidden public text in {path}: {token}", errors)
    for pattern in SECRET_PATTERNS:
        _require(pattern.search(text) is None, f"secret-like text in {path}", errors)
    if path.suffix in {".json", ".jsonl"}:
        payloads = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(text)]
        for payload in payloads:
            for key, value in _walk(payload):
                _require(key not in FORBIDDEN_PUBLIC_KEYS, f"forbidden key in {path}: {key}", errors)
                if isinstance(value, float):
                    errors.append(f"public float value in {path}: {key}")


def _expected_summary() -> dict[str, Any]:
    return {
        "current_s17_p1_validated": True,
        "current_s10_review_validated": True,
        "notification_rule_count": 3,
        "required_trigger_count": 3,
        "trigger_evaluation_count": 3,
        "eligible_reminder_count": 3,
        "trigger_evaluation_mismatch_count": 0,
        "metadata_outbox_log_count": 3,
        "metadata_notification_audit_log_count": 3,
        "short_chinese_reminder_count": 3,
        "in_app_link_count": 3,
        "in_app_link_exists_count": 3,
        "max_body_summary_chars": 120,
        "audit_required_field_count": 7,
        "real_notification_delivery_count": 0,
        "full_report_body_count": 0,
        "report_attachment_count": 0,
        "recipient_address_plaintext_count": 0,
        "external_connector_count": 0,
        "restricted_html_preview_count": 2,
        "hard_block_count": 12,
        "unresolved_source_indicator_count": 4,
        "formal_report_count": 0,
        "raw_source_file_count": 5,
        "raw_snapshot_exact_match": True,
        "raw_cross_phase_snapshot_exact_match": True,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "open_final_difference_accepted_count": 3,
        "nonzero_delta_reconciliation_count": 9,
        "zero_delta_reconciliation_count": 2,
        "incomplete_reconciliation_count": 1,
        **phase._phase_boundaries(),
    }


def _validate_rules(errors: list[str]) -> None:
    rows = _read_jsonl(phase.RULE_PATH)
    by_trigger = {row.get("trigger_id"): row for row in rows}
    _require(len(rows) == 3 and set(by_trigger) == set(phase.REQUIRED_TRIGGER_IDS), "notification rule set drift", errors)
    _require({row.get("recipient_role") for row in rows} == {"management", "reviewer", "finance"}, "recipient role set drift", errors)
    for trigger_id, row in by_trigger.items():
        _require(row.get("policy_version") == phase.POLICY_VERSION, f"policy version drift: {trigger_id}", errors)
        _require(row.get("channel") == "email_reminder", f"channel drift: {trigger_id}", errors)
        for key in ("metadata_log_required", "in_app_link_required", "append_only_required"):
            _require(row.get(key) is True, f"notification requirement missing: {trigger_id}:{key}", errors)
        for key in (
            "full_report_body_allowed",
            "report_attachment_allowed",
            "recipient_address_plaintext_allowed",
            "raw_payload_allowed",
            "business_value_plaintext_allowed",
            "external_connector_allowed",
            "real_delivery_allowed",
        ):
            _require(row.get(key) is False, f"notification rule boundary opened: {trigger_id}:{key}", errors)
        _require(row.get("body_summary_max_chars") == 120, f"body limit drift: {trigger_id}", errors)


def _validate_evaluations(errors: list[str]) -> None:
    rows = _read_jsonl(phase.TRIGGER_EVALUATION_PATH)
    by_trigger = {row.get("trigger_id"): row for row in rows}
    _require(len(rows) == 3 and set(by_trigger) == set(phase.REQUIRED_TRIGGER_IDS), "trigger evaluation set drift", errors)
    expected_counts = {"report_generation_completed": 2, "major_risk": 12, "data_source_missing": 4}
    for trigger_id, expected_count in expected_counts.items():
        row = by_trigger.get(trigger_id, {})
        _require(row.get("source_evidence_count") == expected_count, f"source count drift: {trigger_id}", errors)
        _require(row.get("expected_eligible_for_metadata_outbox") is True, f"expected eligibility drift: {trigger_id}", errors)
        _require(row.get("eligible_for_metadata_outbox") is True, f"current trigger not eligible: {trigger_id}", errors)
        _require(row.get("status") == "PASS", f"trigger evaluation failed: {trigger_id}", errors)
        _require(row.get("business_value_materialized") is False, f"business value materialized: {trigger_id}", errors)
        _require(row.get("real_delivery_eligible") is False, f"delivery eligibility opened: {trigger_id}", errors)


def _validate_outbox(errors: list[str]) -> None:
    rows = _read_jsonl(phase.OUTBOX_PATH)
    _require(len(rows) == 3, "metadata outbox count drift", errors)
    _require({row.get("trigger_id") for row in rows} == set(phase.REQUIRED_TRIGGER_IDS), "outbox trigger set drift", errors)
    _require(len({row.get("event_id") for row in rows}) == 3, "outbox event identity drift", errors)
    _require(len({row.get("idempotency_key") for row in rows}) == 3, "outbox idempotency drift", errors)
    for row in rows:
        trigger_id = row.get("trigger_id")
        validation = phase.validate_outbox_candidate(row)
        _require(validation["valid"], f"invalid outbox row {trigger_id}: {validation['errors']}", errors)
        _require(row.get("actor_role") == "reviewer", f"audit actor drift: {trigger_id}", errors)
        _require(row.get("action_type") == "notification", f"audit action drift: {trigger_id}", errors)
        _require(row.get("result_status") == "metadata_logged_only_not_delivered", f"outbox status drift: {trigger_id}", errors)
        _require(row.get("append_only") is True, f"append-only missing: {trigger_id}", errors)
        _require(row.get("metadata_log_written") is True, f"metadata log missing: {trigger_id}", errors)
        _require(row.get("in_app_link_exists") is True, f"link existence drift: {trigger_id}", errors)
        _require(Path(str(row.get("in_app_link_ref"))).is_file(), f"link target missing: {trigger_id}", errors)
        _require(len(str(row.get("body_summary", ""))) <= 120, f"body too long: {trigger_id}", errors)
        _require(re.search(r"[\u4e00-\u9fff]", str(row.get("subject", ""))) is not None, f"subject not Chinese: {trigger_id}", errors)
        _require(re.search(r"[\u4e00-\u9fff]", str(row.get("body_summary", ""))) is not None, f"body not Chinese: {trigger_id}", errors)
        for field in phase.AUDIT_REQUIRED_FIELDS:
            _require(bool(row.get(field)), f"audit field missing: {trigger_id}:{field}", errors)


def _validate_public(errors: list[str]) -> dict[str, Any]:
    for path in _public_paths():
        _scan_public(path, errors)
    if not phase.MANIFEST_PATH.is_file():
        return {}
    manifest = _read_json(phase.MANIFEST_PATH)
    summary = _read_json(phase.SUMMARY_PATH)
    matrix = _read_json(phase.MATRIX_PATH)
    go_no_go = _read_json(phase.GO_NO_GO_PATH)
    for key, expected in (
        ("phase_id", phase.PHASE_ID),
        ("roadmap_phase_id", phase.ROADMAP_PHASE_ID),
        ("task_id", phase.TASK_ID),
        ("acceptance_id", phase.ACCEPTANCE_ID),
        ("version", phase.VERSION),
        ("status", phase.STATUS),
        ("decision", phase.DECISION),
        ("formula_id", phase.FORMULA_ID),
        ("parameter_ids", list(phase.PARAMETER_IDS)),
        ("model_registry_key", phase.MODEL_REGISTRY_KEY),
    ):
        _require(manifest.get(key) == expected, f"manifest {key} drift", errors)
    _require(manifest.get("summary") == summary, "summary mirror drift", errors)
    _require(manifest.get("acceptance_matrix") == matrix, "matrix mirror drift", errors)
    _require(manifest.get("go_no_go") == go_no_go, "go/no-go mirror drift", errors)
    for key, expected in _expected_summary().items():
        _require(summary.get(key) == expected, f"summary {key} drift", errors)
    _require(manifest.get("current_s17_p1_validated") is True, "current S17-P1 dependency missing", errors)
    _require(manifest.get("current_s10_review_validated") is True, "current S10 dependency missing", errors)
    _require(manifest.get("historical_s17_p2_validated") is True, "historical S17-P2 missing", errors)
    _require(manifest.get("historical_s17_p2_dynamic_state_is_authoritative") is False, "historical S17-P2 active", errors)
    for key in (
        "historical_three_rules_quarantined",
        "historical_three_events_quarantined",
        "historical_three_dispatch_logs_quarantined",
    ):
        _require(manifest.get(key) is True, f"historical fixture not quarantined: {key}", errors)
    _require(manifest.get("audit_required_fields") == list(phase.AUDIT_REQUIRED_FIELDS), "audit fields drift", errors)
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety drift", errors)
    _require(manifest.get("raw_boundary") == phase._raw_boundary(), "raw boundary drift", errors)
    _require(manifest.get("repo_tracking_scan", {}).get("status") == "PASS", "repo tracking scan failed", errors)
    _require(matrix.get("check_count") == 13 and matrix.get("check_pass_count") == 13 and matrix.get("check_fail_count") == 0, "acceptance matrix failed", errors)
    _require(go_no_go.get("s17_p2_validated") is True, "S17-P2 go/no-go missing", errors)
    _require(go_no_go.get("metadata_outbox_allowed") is True, "metadata outbox gate missing", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            if key != "metadata_outbox_allowed":
                _require(value is False, f"go/no-go boundary opened: {key}", errors)
    _require(manifest.get("next_phase") == "S17-P3", "next phase drift", errors)
    for path, expected in (
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_MATRIX_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _require(_read_json(path) == expected, f"metadata mirror drift: {path}", errors)
    for public_path, metadata_path in (
        (phase.RULE_PATH, phase.METADATA_RULE_PATH),
        (phase.TRIGGER_EVALUATION_PATH, phase.METADATA_TRIGGER_EVALUATION_PATH),
        (phase.OUTBOX_PATH, phase.METADATA_OUTBOX_PATH),
    ):
        _require(_read_jsonl(public_path) == _read_jsonl(metadata_path), f"metadata JSONL mirror drift: {metadata_path}", errors)
    _validate_rules(errors)
    _validate_evaluations(errors)
    _validate_outbox(errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    current_s17_p1 = validate_v014_s17_p1_post_remediation_access_security(
        require_private_evidence=True,
        require_final_evidence=True,
    )
    _require(current_s17_p1.get("phase_id") == phase.s17_p1.PHASE_ID, "current S17-P1 identity drift", errors)
    _require(current_s17_p1.get("next_phase") == "S17-P2", "current S17-P1 route drift", errors)
    _require(current_s17_p1.get("summary", {}).get("s17_p2_performed") is False, "current S17-P1 boundary drift", errors)
    current_s10 = phase._validate_frozen_s10_review()
    s10_summary = current_s10.get("summary", {})
    _require(s10_summary.get("html_restricted_preview_count") == 2, "current restricted report count drift", errors)
    _require(s10_summary.get("formal_report_count") == 0, "formal report state drift", errors)
    _require(s10_summary.get("hard_block_count") == 12, "current hard block state drift", errors)
    historical = validate_historical_s17_p2()
    historical_summary = historical.get("notification_policy_summary", {})
    _require(historical_summary.get("notification_rule_count") == 3, "historical rule fixture drift", errors)
    _require(historical_summary.get("notification_event_count") == 3, "historical event fixture drift", errors)
    _require(historical_summary.get("notification_dispatch_log_count") == 3, "historical dispatch fixture drift", errors)


def _expected_parameters() -> dict[str, str]:
    boundary_values = ["true" if value else "false" for value in phase._phase_boundaries().values()]
    return {
        "PARAM-KMFA-1796": "3;3;3;3;0;2;12;4",
        "PARAM-KMFA-1797": "3;3;3;3;120;7;0;0;0;0;0",
        "PARAM-KMFA-1798": "2;0;12;3;9;2;1;Q4;D;NO_GO",
        "PARAM-KMFA-1799": ";".join(["5", "true", "true", *boundary_values, "Q4", "D", "NO_GO"]),
    }


def _validate_governance(manifest: dict[str, Any], errors: list[str]) -> None:
    for path in (phase.DEVELOPMENT_EVENTS_PATH, phase.STAGE_STATUS_PATH, phase.TASK_STATUS_PATH):
        rows = [row for row in _read_jsonl(path) if row.get("phase_id") == phase.PHASE_ID]
        _require(len(rows) == 1, f"governance JSONL row count drift: {path}", errors)
        if rows:
            _require(rows[0].get("status") == phase.STATUS, f"governance status drift: {path}", errors)
    events = [row for row in _read_jsonl(phase.DEVELOPMENT_EVENTS_PATH) if row.get("phase_id") == phase.PHASE_ID]
    if events:
        _require(events[0].get("files_changed") == phase._phase_public_files(), "event file list drift", errors)
        _require(events[0].get("metadata_outbox_log_count") == 3, "event outbox count drift", errors)
        _require(events[0].get("real_notification_delivery_count") == 0, "event delivery drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "notification_rule_count == 3",
        "trigger_evaluation_mismatch_count == 0",
        "metadata_outbox_log_count == 3",
        "in_app_link_count == 3",
        "real_notification_delivery_count == 0",
        "full_report_body_count == 0",
        "external_connector_count == 0",
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
    for parameter_id, expected in _expected_parameters().items():
        row = parameters.get(parameter_id, {})
        _require(row.get("formula_id") == phase.FORMULA_ID, f"parameter formula drift: {parameter_id}", errors)
        for field in ("default_value", "initial_or_prior_value", "active_value", "extracted_value"):
            _require(row.get(field) == expected, f"parameter drift: {parameter_id}:{field}", errors)
        _require(row.get("status") == "active", f"parameter status drift: {parameter_id}", errors)

    version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
    _require(phase.MODEL_REGISTRY_KEY in version_matrix and phase.VERSION in version_matrix, "VERSION_MATRIX profile missing", errors)
    current = f'current_phase: "{phase.PHASE_ID}"' in version_matrix
    if current:
        _require(Path("KMFA/VERSION").read_text(encoding="utf-8").strip() == phase.VERSION, "VERSION drift", errors)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in handoff, "HANDOFF phase drift", errors)
        _require("下一步只能执行 S17-P3" in handoff, "HANDOFF S17-P3 route missing", errors)
        _require("不得执行 Stage 17 整体复审" in handoff, "HANDOFF review boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in agents and "S17-P3" in agents, "AGENTS scope drift", errors)
        for path in (Path("KMFA/docs/governance/OWNER_STATUS.md"), Path("KMFA/docs/governance/STATUS.md")):
            _require(phase.PHASE_ID in path.read_text(encoding="utf-8"), f"active status token missing: {path}", errors)
    trace = Path("KMFA/docs/governance/TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
    delivery = Path("KMFA/docs/governance/delivery_tasks.yaml").read_text(encoding="utf-8")
    assurance = Path("KMFA/docs/governance/ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
    _require(phase.TASK_ID in trace and phase.ACCEPTANCE_ID in trace, "traceability missing", errors)
    _require(phase.TASK_ID in delivery and phase.ACCEPTANCE_ID in delivery, "delivery task missing", errors)
    if current:
        _require(f'snapshot_event_time: "{manifest["generated_at"]}"' in assurance, "assurance time drift", errors)
    _require(phase.FORMULA_ID in assurance, "assurance formula missing", errors)
    for parameter_id in phase.PARAMETER_IDS:
        _require(parameter_id in assurance, f"assurance parameter missing: {parameter_id}", errors)
    for path, token in (
        (Path("KMFA/CHANGELOG.md"), phase.VERSION),
        (Path("KMFA/docs/governance/DEVELOPMENT_LEDGER.md"), phase.PHASE_ID),
        (Path("KMFA/docs/governance/MODEL_SPEC.md"), phase.FORMULA_ID),
        (Path("KMFA/功能清单.md"), "S17-P2 通知"),
        (Path("KMFA/开发记录.md"), phase.TASK_ID),
        (Path("KMFA/模型参数文件.md"), phase.FORMULA_ID),
    ):
        _require(token in path.read_text(encoding="utf-8"), f"governance token missing: {path}", errors)


def _validate_private(errors: list[str]) -> None:
    paths = (phase.PRIVATE_RAW_BEFORE_PATH, phase.PRIVATE_RAW_AFTER_PATH, phase.PRIVATE_SCAN_REPORT_PATH)
    for path in paths:
        _require(path.is_file(), f"private evidence missing: {path}", errors)
        _require(_git_ignored(path), f"private evidence not ignored: {path}", errors)
        _require(not _git_tracked(path), f"private evidence tracked: {path}", errors)
    if not all(path.is_file() for path in paths):
        return
    before = _read_json(phase.PRIVATE_RAW_BEFORE_PATH)
    after = _read_json(phase.PRIVATE_RAW_AFTER_PATH)
    prior = _read_json(phase.s17_p1.PRIVATE_RAW_AFTER_PATH)
    helper = phase.s17_p1.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    current = helper._raw_snapshot("validate_v014_s17_p2_post_remediation_notification")
    normalize = helper._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior) == normalize(current), "raw cross-phase mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count drift", errors)
    scan = phase.s17_p1._repo_tracking_scan()
    _require(scan.get("tracked_forbidden_suffix_count") == 0, "current tracked forbidden suffix found", errors)
    _require(scan.get("tracked_private_runtime_path_count") == 0, "current tracked private runtime found", errors)
    report = phase.PRIVATE_SCAN_REPORT_PATH.read_text(encoding="utf-8")
    for token in (
        "phase 前后快照：exact match",
        "与 S17-P1 快照：exact match",
        "真实投递/完整正文/附件/地址/连接器：0 / 0 / 0 / 0 / 0",
        "全中文最终差异报告",
    ):
        _require(token in report, f"private report token missing: {token}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s17_p2_post_remediation_notification(
    *,
    require_private_evidence: bool = False,
    require_final_evidence: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _validate_public(errors)
    _validate_dependencies(errors)
    if manifest:
        _validate_governance(manifest, errors)
    if require_private_evidence:
        _validate_private(errors)
    if require_final_evidence and manifest:
        validation = manifest.get("validation_summary", {})
        _require(validation.get("final_validation_recorded") is True, "final validation not recorded", errors)
        for key in (
            "focused_test",
            "strict_validator",
            "notification_rule_evaluation_and_outbox",
            "raw_alignment",
            "governance_and_safety_scans",
        ):
            _require(validation.get(key) == "PASS", f"final validation drift: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s17_p2_post_remediation_notification(
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S17-P2 strict validation PASS: "
        f"rules={summary['notification_rule_count']} evaluations={summary['trigger_evaluation_count']} "
        f"outbox={summary['metadata_outbox_log_count']} delivery={summary['real_notification_delivery_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
