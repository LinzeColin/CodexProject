#!/usr/bin/env python3
"""Validate current KMFA v0.1.4 S17-P1 access and security evidence."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools import v014_s17_p1_post_remediation_access_security as phase
from KMFA.tools.access_security_policy import (
    REQUIRED_AUDIT_ACTION_TYPES,
    REQUIRED_SENSITIVE_POLICY_CATEGORIES,
)
from KMFA.tools.check_v014_s16_post_remediation_stage_review import (
    validate_v014_s16_post_remediation_stage_review,
)
from KMFA.tools.check_v014_s17_p1_access_security import (
    validate_v014_s17_p1_access_security as validate_historical_s17_p1,
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
    "customer_name_plaintext",
    "project_name_plaintext",
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
        phase.ROLE_POLICY_PATH,
        phase.AUTHORIZATION_PROBE_PATH,
        phase.SENSITIVE_POLICY_PATH,
        phase.AUDIT_CONTRACT_PATH,
        phase.AUDIT_PROBE_PATH,
        phase.MATRIX_PATH,
        phase.GO_NO_GO_PATH,
        phase.REPORT_PATH,
        phase.TEST_RESULTS_PATH,
        phase.RISK_REGISTER_PATH,
        phase.ROLLBACK_PATH,
        phase.METADATA_SUMMARY_PATH,
        phase.METADATA_MANIFEST_PATH,
        phase.METADATA_ROLE_POLICY_PATH,
        phase.METADATA_SENSITIVE_POLICY_PATH,
        phase.METADATA_AUDIT_CONTRACT_PATH,
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
        "current_s16_review_validated": True,
        "role_count": 4,
        "allowed_action_assignment_count": 14,
        "critical_denied_action_count": 9,
        "authorization_probe_count": 16,
        "authorization_probe_allow_count": 8,
        "authorization_probe_deny_count": 8,
        "authorization_probe_mismatch_count": 0,
        "sensitive_policy_category_count": 15,
        "tracked_forbidden_suffix_count": 0,
        "tracked_private_runtime_path_count": 0,
        "audit_action_type_count": 5,
        "audit_contract_probe_count": 5,
        "audit_contract_probe_pass_count": 5,
        "audit_contract_probe_mismatch_count": 0,
        "actual_business_audit_event_count": 0,
        "notification_delivery_count": 0,
        "full_report_notification_body_count": 0,
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


def _validate_role_policy(errors: list[str]) -> None:
    rows = _read_jsonl(phase.ROLE_POLICY_PATH)
    roles = {row.get("role_id"): row for row in rows}
    _require(len(rows) == 4 and set(roles) == {"management", "finance", "reviewer", "readonly"}, "role set drift", errors)
    _require(sum(len(row.get("allowed_actions", [])) for row in rows) == 14, "allowed action assignment drift", errors)
    for role_id, row in roles.items():
        _require(row.get("policy_version") == phase.ROLE_POLICY_VERSION, f"role policy version drift: {role_id}", errors)
        _require(row.get("least_privilege_applied") is True, f"least privilege missing: {role_id}", errors)
        _require(row.get("deny_by_default") is True, f"deny default missing: {role_id}", errors)
        _require(row.get("audit_required") is True, f"audit requirement missing: {role_id}", errors)
        _require(row.get("denied_critical_actions") == list(phase.CRITICAL_DENIED_ACTIONS), f"critical deny drift: {role_id}", errors)
        for key in (
            "raw_business_data_access_in_public_repo",
            "sensitive_file_public_commit_allowed",
            "credential_access_allowed",
            "quality_gate_bypass_allowed",
            "business_execution_allowed",
            "notification_delivery_allowed",
        ):
            _require(row.get(key) is False, f"role boundary opened: {role_id}:{key}", errors)
        expected_write = "none" if role_id == "readonly" else "metadata_only"
        _require(row.get("max_write_scope") == expected_write, f"write scope drift: {role_id}", errors)
    _require(phase.evaluate_access(rows, "unknown", "read_governance_status")["decision"] == "DENY", "unknown role not denied", errors)
    _require(phase.evaluate_access(rows, "management", "unknown_action")["decision"] == "DENY", "unknown action not denied", errors)


def _validate_authorization_probes(errors: list[str]) -> None:
    rows = _read_jsonl(phase.AUTHORIZATION_PROBE_PATH)
    _require(len(rows) == 16, "authorization probe count drift", errors)
    _require(len({row.get("probe_id") for row in rows}) == 16, "authorization probe identity drift", errors)
    _require(sum(row.get("actual_decision") == "ALLOW" for row in rows) == 8, "authorization ALLOW count drift", errors)
    _require(sum(row.get("actual_decision") == "DENY" for row in rows) == 8, "authorization DENY count drift", errors)
    for row in rows:
        _require(row.get("actual_decision") == row.get("expected_decision"), f"authorization mismatch: {row.get('probe_id')}", errors)
        _require(row.get("status") == "PASS", f"authorization probe failed: {row.get('probe_id')}", errors)
        _require(row.get("probe_only") is True, f"authorization probe boundary drift: {row.get('probe_id')}", errors)
        _require(row.get("persistent_authorization_event_written") is False, f"authorization event write drift: {row.get('probe_id')}", errors)


def _validate_sensitive_policy(errors: list[str]) -> None:
    rows = _read_jsonl(phase.SENSITIVE_POLICY_PATH)
    categories = {row.get("category_id"): row for row in rows}
    _require(len(rows) == 15 and set(categories) == set(REQUIRED_SENSITIVE_POLICY_CATEGORIES), "sensitive category drift", errors)
    for category, row in categories.items():
        _require(row.get("policy_version") == phase.SENSITIVE_POLICY_VERSION, f"sensitive policy version drift: {category}", errors)
        for key in ("public_repo_allowed", "git_upload_allowed", "value_plaintext_allowed"):
            _require(row.get(key) is False, f"sensitive boundary opened: {category}:{key}", errors)
        _require(row.get("metadata_hash_or_ref_only_allowed") is True, f"hash/ref boundary missing: {category}", errors)
        _require(row.get("handling") == "private_storage_or_hash_only_metadata", f"handling drift: {category}", errors)
        controls = row.get("enforcement_controls", [])
        for control in ("tracked_forbidden_suffix_scan", "private_runtime_tracking_scan", "strict_public_text_and_secret_scan"):
            _require(control in controls, f"sensitive control missing: {category}:{control}", errors)


def _validate_audit_contract(errors: list[str]) -> None:
    contracts = _read_jsonl(phase.AUDIT_CONTRACT_PATH)
    actions = {row.get("action_type"): row for row in contracts}
    _require(len(contracts) == 5 and set(actions) == set(REQUIRED_AUDIT_ACTION_TYPES), "audit action drift", errors)
    for action, row in actions.items():
        _require(row.get("contract_version") == phase.AUDIT_CONTRACT_VERSION, f"audit version drift: {action}", errors)
        _require(row.get("required_fields") == list(phase.AUDIT_REQUIRED_FIELDS), f"audit fields drift: {action}", errors)
        for key in ("append_only_required", "actor_role_required", "evidence_ref_required"):
            _require(row.get(key) is True, f"audit requirement missing: {action}:{key}", errors)
        for key in ("raw_payload_allowed", "private_document_allowed", "business_value_plaintext_allowed", "sends_full_report_body", "persistent_event_write_enabled"):
            _require(row.get(key) is False, f"audit boundary opened: {action}:{key}", errors)
        if action == "notification":
            _require(row.get("delivery_scope") == "audit_log_contract_only_no_delivery", "notification contract drift", errors)
    probes = _read_jsonl(phase.AUDIT_PROBE_PATH)
    _require(len(probes) == 5 and {row.get("action_type") for row in probes} == set(REQUIRED_AUDIT_ACTION_TYPES), "audit probe drift", errors)
    for row in probes:
        _require(row.get("status") == "PASS", f"audit probe failed: {row.get('probe_id')}", errors)
        _require(row.get("missing_required_field_count") == 0, f"audit probe missing fields: {row.get('probe_id')}", errors)
        _require(row.get("forbidden_payload_present") is False, f"audit probe payload drift: {row.get('probe_id')}", errors)
        _require(row.get("persistent_audit_event_written") is False, f"audit event write drift: {row.get('probe_id')}", errors)
        _require(row.get("notification_delivered") is False, f"notification delivery drift: {row.get('probe_id')}", errors)
        _require(row.get("full_report_body_sent") is False, f"full body drift: {row.get('probe_id')}", errors)


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
    _require(manifest.get("current_s16_review_validated") is True, "current S16 dependency missing", errors)
    _require(manifest.get("historical_s17_p1_validated") is True, "historical S17-P1 missing", errors)
    _require(manifest.get("historical_s17_p1_dynamic_state_is_authoritative") is False, "historical S17-P1 active", errors)
    _require(manifest.get("historical_four_roles_quarantined") is True, "historical roles not quarantined", errors)
    _require(manifest.get("historical_fifteen_sensitive_categories_quarantined") is True, "historical sensitive policies not quarantined", errors)
    _require(manifest.get("historical_five_audit_actions_quarantined") is True, "historical audit actions not quarantined", errors)
    _require(manifest.get("deny_by_default_enforced") is True, "deny by default missing", errors)
    _require(manifest.get("quality_gate") == phase._quality_gate(), "quality gate drift", errors)
    _require(manifest.get("phase_boundaries") == phase._phase_boundaries(), "phase boundary drift", errors)
    _require(manifest.get("public_repo_safety") == phase._public_safety(), "public safety drift", errors)
    _require(manifest.get("raw_boundary") == phase._raw_boundary(), "raw boundary drift", errors)
    _require(manifest.get("repo_tracking_scan", {}).get("status") == "PASS", "repo tracking scan failed", errors)
    _require(matrix.get("check_count") == 12 and matrix.get("check_pass_count") == 12 and matrix.get("check_fail_count") == 0, "acceptance matrix failed", errors)
    _require(go_no_go.get("s17_p1_validated") is True, "S17-P1 go/no-go missing", errors)
    for key, value in go_no_go.items():
        if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
            _require(value is False, f"go/no-go boundary opened: {key}", errors)
    _require(manifest.get("next_phase") == "S17-P2", "next phase drift", errors)
    for path, expected in (
        (phase.METADATA_SUMMARY_PATH, summary),
        (phase.METADATA_MANIFEST_PATH, manifest),
        (phase.METADATA_MATRIX_PATH, matrix),
        (phase.METADATA_GO_NO_GO_PATH, go_no_go),
    ):
        _require(_read_json(path) == expected, f"metadata mirror drift: {path}", errors)
    for public_path, metadata_path in (
        (phase.ROLE_POLICY_PATH, phase.METADATA_ROLE_POLICY_PATH),
        (phase.SENSITIVE_POLICY_PATH, phase.METADATA_SENSITIVE_POLICY_PATH),
        (phase.AUDIT_CONTRACT_PATH, phase.METADATA_AUDIT_CONTRACT_PATH),
    ):
        _require(_read_jsonl(public_path) == _read_jsonl(metadata_path), f"metadata JSONL mirror drift: {metadata_path}", errors)
    _validate_role_policy(errors)
    _validate_authorization_probes(errors)
    _validate_sensitive_policy(errors)
    _validate_audit_contract(errors)
    return manifest


def _validate_dependencies(errors: list[str]) -> None:
    current = validate_v014_s16_post_remediation_stage_review(
        require_private_evidence=True,
        require_browser_evidence=True,
        require_final_evidence=True,
    )
    _require(current.get("phase_id") == phase.s16_review.PHASE_ID, "current Stage 16 review identity drift", errors)
    _require(current.get("next_phase") == "S17-P1", "current Stage 16 route drift", errors)
    _require(current.get("summary", {}).get("stage16_review_performed") is True, "current Stage 16 review incomplete", errors)
    _require(current.get("summary", {}).get("github_upload_performed") is False, "current Stage 16 upload drift", errors)
    historical = validate_historical_s17_p1()
    hs = historical.get("access_security_summary", {})
    _require(hs.get("role_count") == 4, "historical role fixture drift", errors)
    _require(hs.get("sensitive_policy_category_count") == 15, "historical sensitive fixture drift", errors)
    _require(hs.get("audit_action_type_count") == 5, "historical audit fixture drift", errors)


def _expected_parameters() -> dict[str, str]:
    return {
        "PARAM-KMFA-1792": "4;14;9;16;8;8;0;true",
        "PARAM-KMFA-1793": "15;15;0;0;6;true",
        "PARAM-KMFA-1794": "5;5;5;0;0;0;0;7",
        "PARAM-KMFA-1795": (
            "5;true;true;3;9;2;1;true;"
            "false;false;false;false;false;false;false;false;false;false;false;false;false;false;false;false;false;false;"
            "Q4;D;NO_GO"
        ),
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
        _require(events[0].get("role_count") == 4, "event role count drift", errors)
        _require(events[0].get("authorization_probe_mismatch_count") == 0, "event authorization drift", errors)

    formula_text = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
    _require(phase.FORMULA_ID in formula_text, "formula missing", errors)
    for token in (
        "role_count == 4",
        "authorization_probe_mismatch_count == 0",
        "sensitive_policy_category_count == 15",
        "tracked_forbidden_suffix_count == 0",
        "audit_action_type_count == 5",
        "audit_contract_probe_mismatch_count == 0",
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
        _require("下一步只能执行 S17-P2" in handoff, "HANDOFF S17-P2 route missing", errors)
        _require("不得执行 S17-P3" in handoff, "HANDOFF later phase boundary missing", errors)
        _require("不得执行 GitHub upload" in handoff, "HANDOFF upload boundary missing", errors)
        agents = Path("KMFA/AGENTS.md").read_text(encoding="utf-8")
        _require(phase.PHASE_ID in agents and "S17-P2" in agents, "AGENTS scope drift", errors)
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
        (Path("KMFA/功能清单.md"), "S17-P1 权限与安全"),
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
    prior = _read_json(phase.s16_review.PRIVATE_RAW_AFTER_PATH)
    helper = phase.s16_review.p1.s15_review.p1.s14_review.p1.s13_review.p1.s12_review.p1.s11_project
    current = helper._raw_snapshot("validate_v014_s17_p1_post_remediation_access_security")
    normalize = helper._normalize_raw
    _require(normalize(before) == normalize(after), "raw before/after mismatch", errors)
    _require(normalize(before) == normalize(prior) == normalize(current), "raw cross-phase mismatch", errors)
    _require(before.get("file_count") == 5, "raw file count drift", errors)
    scan = phase._repo_tracking_scan()
    _require(scan.get("tracked_forbidden_suffix_count") == 0, "current tracked forbidden suffix found", errors)
    _require(scan.get("tracked_private_runtime_path_count") == 0, "current tracked private runtime found", errors)
    report = phase.PRIVATE_SCAN_REPORT_PATH.read_text(encoding="utf-8")
    for token in ("phase 前后快照：exact match", "与 Stage 16 review 快照：exact match", "授权探针不一致：0", "审计契约探针不一致：0", "全中文最终差异报告"):
        _require(token in report, f"private report token missing: {token}", errors)


@functools.lru_cache(maxsize=8)
def validate_v014_s17_p1_post_remediation_access_security(
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
        for key in ("focused_test", "strict_validator", "authorization_and_audit_probes", "raw_alignment", "governance_and_safety_scans"):
            _require(validation.get(key) == "PASS", f"final validation drift: {key}", errors)
    if errors:
        raise ValidationError("; ".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-final-evidence", action="store_true")
    args = parser.parse_args()
    manifest = validate_v014_s17_p1_post_remediation_access_security(
        require_private_evidence=args.require_private_evidence,
        require_final_evidence=args.require_final_evidence,
    )
    summary = manifest["summary"]
    print(
        "S17-P1 strict validation PASS: "
        f"roles={summary['role_count']} auth={summary['authorization_probe_count']} "
        f"sensitive={summary['sensitive_policy_category_count']} audit={summary['audit_action_type_count']} "
        f"grade={summary['current_report_grade']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
