#!/usr/bin/env python3
"""Strict fail-closed validator for KMFA v1.5 S03-P1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from KMFA.tools import build_v015_s03_p1_read_only_root_governance as builder
from KMFA.tools import v015_s03_p1_read_only_root_guard as guard


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE
MANIFEST_PATH = ARTIFACT_ROOT / builder.MANIFEST_RELATIVE
TASK_MATRIX_PATH = ARTIFACT_ROOT / builder.TASK_MATRIX_RELATIVE
WRITE_GUARD_PATH = ARTIFACT_ROOT / builder.WRITE_GUARD_RELATIVE
READ_SCOPE_PATH = ARTIFACT_ROOT / builder.READ_SCOPE_RELATIVE
EVIDENCE_SLOTS_PATH = ARTIFACT_ROOT / builder.EVIDENCE_SLOTS_RELATIVE
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / builder.VALIDATION_RESULTS_RELATIVE
PUBLIC_REGISTRY_PATH = PROJECT_ROOT / builder.PUBLIC_REGISTRY_RELATIVE
PUBLIC_ALLOWLIST_PATH = PROJECT_ROOT / builder.PUBLIC_ALLOWLIST_RELATIVE

S02_FROZEN_REFS = (
    "KMFA/stage_artifacts/V015_S02_STAGE_REVIEW/machine/stage2_review_manifest.json",
    "KMFA/stage_artifacts/V015_S02_P1_REQUIREMENTS_SCOPE_LOCK/machine/s02_p1_requirements_scope_lock_manifest.json",
    "KMFA/stage_artifacts/V015_S02_P2_END_TO_END_TRACEABILITY/machine/s02_p2_end_to_end_traceability_manifest.json",
    "KMFA/stage_artifacts/V015_S02_P3_SCOPE_GATE/machine/s02_p3_scope_gate_manifest.json",
)

GOVERNANCE_COMMON_EXPECTED = {
    "docs/governance/project.yaml": (
        'current_stage_id: "S03"',
        'current_phase_id: "V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE"',
        "s03_p2_started: false", "github_upload_performed: false",
    ),
    "docs/governance/roadmap.yaml": (
        'current_stage_id: "S03"',
        'current_phase_id: "V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE"',
    ),
    "README.md": (
        "V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE",
        "os_atime_side_effect_possible=true", "absolute_zero_metadata_mutation_claimed=false",
    ),
    "HANDOFF.md": (
        "V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE",
        "os_atime_side_effect_possible=true", "absolute_zero_metadata_mutation_claimed=false",
    ),
    "功能清单.md": ("V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE",),
    "开发记录.md": ("V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE", "S03P1T03"),
    "模型参数文件.md": (
        "FORM-KMFA-V015-S03-P1-READ-ONLY-ROOT-GUARD-001", "PARAM-KMFA-1855",
        "PARAM-KMFA-1860", "os_atime_truth_tuple",
    ),
    "docs/governance/MODEL_SPEC.md": (
        "FORM-KMFA-V015-S03-P1-READ-ONLY-ROOT-GUARD-001",
        "RECEIPT_BOUND_POST_VALIDATION", "FINAL_V2_REPLAY_ONLY",
        "historical_pre_v2_atime_effect_unknown=true",
        "absolute_zero_metadata_mutation_claimed=false",
        "os_atime_restoration_performed=false", "S03P2T02",
    ),
}

GOVERNANCE_PENDING_EXPECTED = {
    "docs/governance/project.yaml": ('decision: "REMAIN_IN_S03_P1"', "s03_p2_entry_allowed: false"),
    "docs/governance/roadmap.yaml": ('decision: "REMAIN_IN_S03_P1"', "s03_p2_entry_allowed: false"),
    "README.md": ("PENDING_FINAL_VALIDATION", "REMAIN_IN_S03_P1"),
    "HANDOFF.md": ("PENDING_FINAL_VALIDATION", "REMAIN_IN_S03_P1"),
}

GOVERNANCE_FINAL_EXPECTED = {
    "docs/governance/project.yaml": ('decision: "CONTINUE_TO_S03_P2_ONLY"', "s03_p2_entry_allowed: true"),
    "docs/governance/roadmap.yaml": ('decision: "CONTINUE_TO_S03_P2_ONLY"', "s03_p2_entry_allowed: true"),
    "README.md": ("CONTINUE_TO_S03_P2_ONLY",),
    "HANDOFF.md": ("S03-P2", "CONTINUE_TO_S03_P2_ONLY"),
}

ALLOWED_DIFF_PATHS = frozenset(builder.ARTIFACT_REFS.values()) | frozenset({
    "KMFA/tools/v015_s03_p1_read_only_root_guard.py",
    "KMFA/tools/build_v015_s03_p1_read_only_root_governance.py",
    "KMFA/tools/check_v015_s03_p1_read_only_root_governance.py",
    "KMFA/tools/run_v015_s03_p1_validations.py",
    "KMFA/tests/test_v015_s03_p1_read_only_root_guard.py",
    "KMFA/tests/test_v015_s03_p1_read_only_root_governance.py",
    "KMFA/tests/test_v015_s03_p1_validation_runner.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/docs/governance/project.yaml",
    "KMFA/docs/governance/roadmap.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl", "KMFA/metadata/model_registry.yaml",
    "KMFA/README.md", "KMFA/HANDOFF.md", "KMFA/CHANGELOG.md", "KMFA/AGENTS.md",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
})

FORBIDDEN_PUBLIC_TOKENS = (
    b"/" + b"Users/", b"/" + b"Volumes/", b"/" + b"private/",
    b"/" + b"tmp/", b"/" + b"home/", b"KMFA_" + b"MetaData",
)
EMAIL_RE = re.compile(rb"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_RE = re.compile(
    rb"(?i)(?:api[_-]?key|password|secret|(?:access|auth|bearer|refresh|session)[_-]?token)"
    rb"\s*[:=]\s*['\"][^'\"]{8,}"
)

EXPECTED_PARAMETER_ROWS = {
    "PARAM-KMFA-1852": ("allowed_operation_count", "4"),
    "PARAM-KMFA-1853": ("taskpack_mutation_class_count", "4"),
    "PARAM-KMFA-1854": ("evidence_slot_count_per_task", "10"),
    "PARAM-KMFA-1855": ("phase_task_count", "3"),
    "PARAM-KMFA-1856": ("allowed_extension_count", "2"),
    "PARAM-KMFA-1857": ("max_relative_depth", "0"),
    "PARAM-KMFA-1858": ("hash_chunk_size_bytes", "1048576"),
    "PARAM-KMFA-1859": ("kqueue_final_drain_seconds", "0.25"),
    "PARAM-KMFA-1860": ("os_atime_truth_tuple", "true;false"),
}

PENDING_EVENT_ID = (
    "EVENT-KMFA-20260713-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE-"
    "ATIME-TRUTH-PENDING-VALIDATION"
)
PENDING_DEVELOPMENT_EVENT_ID = (
    "DEV-KMFA-20260713-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE-"
    "ATIME-TRUTH-PENDING-VALIDATION"
)
PENDING_STAGE_STATUS_RECORD_ID = (
    "STATUS-KMFA-20260713-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE-"
    "ATIME-TRUTH-PENDING-VALIDATION"
)
PENDING_CORRECTION_STATUS = "execution_complete_atime_truth_final_validation_pending"
PENDING_CORRECTION_REASON = "RETRACT_PREMATURE_FINAL_AND_DECLARE_ATIME_TRUTH_PENDING_RECEIPT"

FINAL_EVENT_ID = (
    "EVENT-KMFA-20260713-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE-"
    "ATIME-TRUTH-FINAL-VALIDATION"
)
FINAL_DEVELOPMENT_EVENT_ID = (
    "DEV-KMFA-20260713-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE-"
    "ATIME-TRUTH-FINAL-VALIDATION"
)
FINAL_STAGE_STATUS_RECORD_ID = (
    "STATUS-KMFA-20260713-V015-S03-P1-READ-ONLY-ROOT-GOVERNANCE-"
    "ATIME-TRUTH-FINAL-VALIDATION"
)
FINAL_CORRECTION_STATUS = (
    "completed_validated_local_only_s03p1_passed_s03_in_progress_atime_truth"
)
FINAL_CORRECTION_REASON = "OS_MANAGED_ATIME_TRUTH_AND_POST_VALIDATION_PROVENANCE"

PENDING_LEDGER_SOURCES = (
    (PROJECT_ROOT / "docs/governance/events.jsonl", "event_id", PENDING_EVENT_ID),
    (
        PROJECT_ROOT / "docs/governance/development_events.jsonl",
        "event_id",
        PENDING_DEVELOPMENT_EVENT_ID,
    ),
    (
        PROJECT_ROOT / "metadata/stage_status.jsonl",
        "status_record_id",
        PENDING_STAGE_STATUS_RECORD_ID,
    ),
)

FINAL_LEDGER_SOURCES = (
    (
        PROJECT_ROOT / "docs/governance/events.jsonl",
        "event_id",
        FINAL_EVENT_ID,
        "supersedes_event_ids",
        [PENDING_EVENT_ID],
    ),
    (
        PROJECT_ROOT / "docs/governance/development_events.jsonl",
        "event_id",
        FINAL_DEVELOPMENT_EVENT_ID,
        "supersedes_event_ids",
        [PENDING_DEVELOPMENT_EVENT_ID],
    ),
    (
        PROJECT_ROOT / "metadata/stage_status.jsonl",
        "status_record_id",
        FINAL_STAGE_STATUS_RECORD_ID,
        "supersedes_status_record_ids",
        [PENDING_STAGE_STATUS_RECORD_ID],
    ),
)


class ValidationError(RuntimeError):
    """Raised when any S03-P1 invariant fails."""


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _regular_single_link(path: Path, errors: list[str], *, label: str) -> bool:
    """Fail closed on links/special files before any content read."""

    try:
        value = os.lstat(path)
    except OSError as error:
        errors.append(f"{label} unavailable: {path}: {error}")
        return False
    safe = (
        stat.S_ISREG(value.st_mode)
        and not stat.S_ISLNK(value.st_mode)
        and int(value.st_nlink) == 1
    )
    _require(safe, f"{label} type/link unsafe: {path}", errors)
    return safe


def _read_bytes_no_follow(path: Path, *, label: str) -> bytes:
    try:
        return builder._read_regular_bytes_no_follow(path, label=label)
    except builder.BuildError as error:
        raise ValidationError(str(error)) from error


def _read_text_no_follow(path: Path, *, label: str) -> str:
    return _read_bytes_no_follow(path, label=label).decode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(_read_text_no_follow(path, label="required JSON"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(
        _read_text_no_follow(path, label="required JSONL").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"expected JSON object at {path}:{line_no}")
        rows.append(value)
    return rows


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _content_hash(value: Mapping[str, Any]) -> str:
    copy = dict(value)
    copy.pop("content_hash", None)
    return "sha256:" + _sha256(
        json.dumps(copy, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _top_level_yaml_scalar(text: str, key: str) -> Optional[str]:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", text, re.MULTILINE)
    if match is None:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'\"', "'"}:
        return value[1:-1]
    return value


def _validate_public_payload(payload: bytes, errors: list[str], *, label: str) -> None:
    for token in FORBIDDEN_PUBLIC_TOKENS:
        _require(token not in payload, f"public-safe token leak in {label}: {token!r}", errors)
    _require(EMAIL_RE.search(payload) is None, f"email leak in {label}", errors)
    _require(SECRET_RE.search(payload) is None, f"secret-like assignment in {label}", errors)


def _validate_manifest(
    manifest: Mapping[str, Any],
    errors: list[str],
    *,
    require_pass: bool = True,
) -> None:
    expected = {
        "schema_version": "kmfa.v015.s03_p1.read_only_root_governance.v2",
        "project_id": "KMFA", "target_release": "v1.5", "stage_id": "S03", "phase_id": "S03-P1",
        "run_phase_id": builder.RUN_PHASE_ID, "task_id": builder.TASK_ID,
        "acceptance_id": builder.ACCEPTANCE_ID, "phase_base_commit": builder.PHASE_BASE_COMMIT,
        "execution_status": "EXECUTION_COMPLETE",
    }
    for key, value in expected.items():
        _require(manifest.get(key) == value, f"manifest {key} drift", errors)
    _require(manifest.get("content_hash") == _content_hash(manifest), "manifest content_hash drift", errors)
    source = manifest.get("source_package", {})
    _require(source.get("package_sha256") == builder.SOURCE_PACKAGE_SHA256, "source package binding drift", errors)
    _require(source.get("verified_member_count") == 21, "source package must verify 21/21", errors)
    _require(source.get("s03_p1_semantic_equal") is True, "source/tracked S03-P1 semantic parity missing", errors)
    validation = manifest.get("validation_receipt_accounting", {})
    final_pass = validation.get("all_exact_pass") is True
    if require_pass:
        _require(final_pass, "exact validation receipts are not all PASS", errors)
    expected_acceptance = "PASSED" if final_pass else "PENDING"
    expected_decision = "CONTINUE_TO_S03_P2_ONLY" if final_pass else "REMAIN_IN_S03_P1"
    _require(manifest.get("evidence_validation_status") == ("PASS" if final_pass else "PENDING"), "manifest evidence validation status drift", errors)
    _require(manifest.get("acceptance_status") == expected_acceptance, "manifest acceptance status drift", errors)
    _require(manifest.get("decision") == expected_decision, "manifest decision drift", errors)
    accounting = manifest.get("task_accounting", {})
    _require(accounting == {"total": 3, "execution_complete": 3, "accepted": 3 if final_pass else 0}, "task accounting drift", errors)
    stage = manifest.get("stage_status", {})
    _require(stage == {"lifecycle": "IN_PROGRESS", "acceptance": "PENDING", "execution_percentage": 33}, "S03 Stage status drift", errors)
    raw = manifest.get("raw_access", {})
    _require(tuple(raw.get("allowed_operations_performed", [])) == builder.EXPECTED_ALLOWED_OPERATIONS, "allowed operations drift", errors)
    _require(raw.get("forbidden_operations_performed") == [], "forbidden operation performed", errors)
    for key in ("raw_business_content_interpreted", "raw_business_values_extracted", "raw_copy_performed"):
        _require(raw.get(key) is False, f"raw boundary true: {key}", errors)
    _require(raw.get("raw_bytes_streamed_for_hash") is True, "hash read truth missing", errors)
    _require(raw.get("prohibited_raw_mutation_detected") is False, "prohibited raw mutation detected", errors)
    _require(
        raw.get("prohibited_mutation_scope") == list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
        "prohibited mutation scope drift",
        errors,
    )
    _require(raw.get("os_atime_side_effect_possible") is True, "OS atime possibility truth missing", errors)
    _require(type(raw.get("os_atime_side_effect_observed")) is bool, "OS atime observation must be boolean", errors)
    _require(raw.get("historical_pre_v2_atime_effect_unknown") is True, "historical pre-v2 atime uncertainty missing", errors)
    _require(raw.get("os_atime_observation_scope") == "FINAL_V2_REPLAY_ONLY", "raw atime observation scope drift", errors)
    _require(raw.get("absolute_zero_metadata_mutation_claimed") is False, "absolute-zero metadata overclaim", errors)
    _require(raw.get("os_atime_restoration_performed") is False, "atime restoration must remain false", errors)
    _require(raw.get("production_raw_mutation_api_present") is False, "production raw mutation API must remain absent", errors)
    for ambiguous in ("raw_mutation_detected", "raw_root_mutated", "raw_inbox_mutated"):
        _require(ambiguous not in raw, f"ambiguous raw mutation field forbidden: {ambiguous}", errors)
    guard_result = manifest.get("guard_result", {})
    _require(guard_result.get("guard_status") == "PASS", "guard status drift", errors)
    _require(guard_result.get("setup_pre_equal") is True and guard_result.get("pre_post_equal") is True, "recursive fingerprint equality missing", errors)
    _require(guard_result.get("event_monitor_status") == "PASS", "event monitor status drift", errors)
    _require(guard_result.get("event_monitor_production_attested") is True, "event monitor production attestation missing", errors)
    _require(guard_result.get("controlled_window_seconds") == guard.CONTROLLED_WINDOW_SECONDS, "controlled monitor window drift", errors)
    _require(guard_result.get("final_drain_seconds") == guard.FINAL_DRAIN_SECONDS, "final monitor drain drift", errors)
    _require(guard_result.get("os_level_immutable_claimed") is False, "OS immutability overclaim", errors)
    _require(guard_result.get("prohibited_raw_mutation_detected") is False, "guard detected prohibited raw mutation", errors)
    _require(guard_result.get("os_atime_side_effect_possible") is True, "guard omitted OS atime possibility", errors)
    _require(type(guard_result.get("os_atime_side_effect_observed")) is bool, "guard atime observation must be boolean", errors)
    _require(guard_result.get("historical_pre_v2_atime_effect_unknown") is True, "guard historical pre-v2 atime uncertainty missing", errors)
    _require(guard_result.get("os_atime_observation_scope") == "FINAL_V2_REPLAY_ONLY", "guard atime observation scope drift", errors)
    _require(guard_result.get("absolute_zero_metadata_mutation_claimed") is False, "guard absolute-zero metadata overclaim", errors)
    _require(guard_result.get("os_atime_restoration_performed") is False, "guard atime restoration must remain false", errors)
    _require(guard_result.get("production_raw_mutation_api_present") is False, "guard production raw mutation API must remain absent", errors)
    slots = manifest.get("evidence_slot_accounting", {})
    _require(slots == {"task_count": 3, "slots_per_task": 10, "total": 30, "covered": 24, "n_a_with_rationale": 6}, "evidence-slot accounting drift", errors)
    risks = manifest.get("open_risk_accounting", {})
    _require(
        risks == {"total": 4, "blocking": 0, "p0": 0, "p1": 2, "p2": 2, "plan_gap_count": 0},
        "open-risk accounting drift",
        errors,
    )
    gate = manifest.get("next_entry_gate", {})
    _require(gate.get("next_allowed_run") == ("S03-P2" if final_pass else "S03-P1"), "next-run gate drift", errors)
    _require(gate.get("s03_p2_entry_allowed") is final_pass and gate.get("s03_p2_started") is False, "S03-P2 gate drift", errors)
    for key in ("s03_p3_entry_allowed", "stage3_review_entry_allowed", "product_implementation_allowed"):
        _require(gate.get(key) is False, f"premature gate opened: {key}", errors)
    for key, value in manifest.get("downstream_actions", {}).items():
        _require(value is False, f"downstream action true: {key}", errors)


def _validate_matrix(
    matrix: Mapping[str, Any],
    errors: list[str],
    *,
    require_pass: bool = True,
) -> None:
    rows = matrix.get("tasks")
    _require(isinstance(rows, list) and len(rows) == 3, "matrix must contain three Tasks", errors)
    if not isinstance(rows, list):
        return
    _require([row.get("task_id") for row in rows] == [task["task_id"] for task in builder.TASKS], "matrix Task order/IDs drift", errors)
    phase_status = matrix.get("phase_acceptance_status")
    _require(phase_status in {"PASSED", "PENDING"}, "matrix phase acceptance status invalid", errors)
    final_pass = phase_status == "PASSED"
    if require_pass:
        _require(final_pass, "matrix phase acceptance is not PASSED", errors)
    for row, task in zip(rows, builder.TASKS):
        source_contract = {key: task[key] for key in ("name", "action", "output", "acceptance", "evidence", "stop")}
        _require(row.get("source_contract") == source_contract, f"{task['task_id']} source contract drift", errors)
        _require(row.get("execution_status") == "EXECUTION_COMPLETE", f"{task['task_id']} execution incomplete", errors)
        _require(row.get("acceptance_status") == ("PASSED" if final_pass else "PENDING"), f"{task['task_id']} acceptance status drift", errors)
        _require(row.get("current_result") == ("TASK_ACCEPTED" if final_pass else "VALIDATION_PENDING"), f"{task['task_id']} result drift", errors)
    _require(matrix.get("task_accounting") == {"total": 3, "execution_complete": 3, "accepted": 3 if final_pass else 0}, "matrix task accounting drift", errors)
    _require(matrix.get("decision") == ("CONTINUE_TO_S03_P2_ONLY" if final_pass else "REMAIN_IN_S03_P1"), "matrix decision drift", errors)


def _validate_policies(registry: Mapping[str, Any], allowlist: Mapping[str, Any], guard_public: Mapping[str, Any], errors: list[str]) -> None:
    _require(
        registry.get("schema_version") == "kmfa.metadata.v015.s03_p1.read_only_root_registry.public_safe.v2",
        "public registry schema drift",
        errors,
    )
    _require(registry.get("root_id") == builder.ROOT_ID, "public registry root_id drift", errors)
    binding = registry.get("path_binding", {})
    _require(binding.get("visibility") == "PRIVATE_ONLY" and binding.get("exact_path_registered") is True, "private exact-path binding missing", errors)
    _require(binding.get("public_path_value") is None, "exact raw path exposed publicly", errors)
    _require(tuple(registry.get("allowed_operations", [])) == builder.EXPECTED_ALLOWED_OPERATIONS, "registry allowed operations drift", errors)
    _require(registry.get("forbidden_operations_performed") == [], "registry forbidden operation performed", errors)
    permission = registry.get("permission_observation", {})
    _require(permission.get("readable") is True and permission.get("permission_known") is True, "root permission unknown/unreadable", errors)
    _require(permission.get("os_level_immutable_claimed") is False, "registry OS immutable overclaim", errors)
    _require(registry.get("prohibited_raw_mutation_detected") is False, "registry detected prohibited raw mutation", errors)
    _require(
        registry.get("prohibited_mutation_scope") == list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
        "registry prohibited mutation scope drift",
        errors,
    )
    _require(registry.get("os_atime_side_effect_possible") is True, "registry OS atime possibility missing", errors)
    _require(type(registry.get("os_atime_side_effect_observed")) is bool, "registry atime observation must be boolean", errors)
    _require(registry.get("historical_pre_v2_atime_effect_unknown") is True, "registry historical pre-v2 atime uncertainty missing", errors)
    _require(registry.get("os_atime_observation_scope") == "FINAL_V2_REPLAY_ONLY", "registry atime observation scope drift", errors)
    _require(registry.get("absolute_zero_metadata_mutation_claimed") is False, "registry absolute-zero metadata overclaim", errors)
    _require(registry.get("os_atime_restoration_performed") is False, "registry atime restoration must remain false", errors)
    _require(registry.get("production_raw_mutation_api_present") is False, "registry production raw mutation API must remain absent", errors)
    for ambiguous in ("raw_mutation_detected", "raw_root_mutated", "raw_inbox_mutated"):
        _require(ambiguous not in registry, f"registry ambiguous raw mutation field forbidden: {ambiguous}", errors)
    _require(allowlist.get("authorization_model") == "DEFAULT_DENY_EXACT_ROOT_AND_FILE_TYPE", "allowlist model drift", errors)
    rules = allowlist.get("source_rules")
    _require(isinstance(rules, list) and len(rules) == 1, "allowlist must contain exactly one source rule", errors)
    if isinstance(rules, list) and len(rules) == 1:
        rule = rules[0]
        _require(rule.get("root_id") == builder.ROOT_ID and rule.get("root_count") == 1, "allowlist root scope drift", errors)
        _require(tuple(sorted(rule.get("allowed_file_extensions", []))) == tuple(sorted(builder.EXPECTED_ALLOWED_EXTENSIONS)), "file-type allowlist drift", errors)
        _require(tuple(rule.get("allowed_operations", [])) == builder.EXPECTED_ALLOWED_OPERATIONS, "allowlist operations drift", errors)
        for key in ("follow_symlinks", "special_files_allowed", "raw_parse_allowed", "raw_value_extract_allowed", "copy_allowed"):
            _require(rule.get(key) is False, f"allowlist boundary true: {key}", errors)
    _require(allowlist.get("full_disk_scan_allowed") is False, "full disk scan opened", errors)
    _require(allowlist.get("arbitrary_root_cli_override_allowed") is False, "arbitrary root CLI override opened", errors)
    _require(
        guard_public.get("schema_version") == "kmfa.v015.s03_p1.write_protection_validation.public_safe.v2",
        "public guard schema drift",
        errors,
    )
    _require(guard_public.get("guard_status") == "PASS", "public guard receipt not PASS", errors)
    _require(guard_public.get("event_monitor_status") == "PASS", "public event monitor not PASS", errors)
    _require(guard_public.get("event_monitor_backend") == guard.DarwinKqueueVnodeMonitor.name, "public event backend drift", errors)
    _require(guard_public.get("event_monitor_production_attested") is True, "public event backend attestation missing", errors)
    _require(guard_public.get("controlled_window_seconds") == guard.CONTROLLED_WINDOW_SECONDS, "public controlled window drift", errors)
    _require(guard_public.get("final_drain_seconds") == guard.FINAL_DRAIN_SECONDS, "public final drain drift", errors)
    _require(guard_public.get("prohibited_raw_mutation_detected") is False, "public guard reports prohibited mutation", errors)
    _require(
        guard_public.get("prohibited_mutation_scope") == list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
        "public guard prohibited mutation scope drift",
        errors,
    )
    _require(guard_public.get("os_atime_side_effect_possible") is True, "public guard OS atime possibility missing", errors)
    _require(type(guard_public.get("os_atime_side_effect_observed")) is bool, "public guard atime observation must be boolean", errors)
    _require(guard_public.get("historical_pre_v2_atime_effect_unknown") is True, "public guard historical pre-v2 atime uncertainty missing", errors)
    _require(guard_public.get("os_atime_observation_scope") == "FINAL_V2_REPLAY_ONLY", "public guard atime observation scope drift", errors)
    _require(guard_public.get("absolute_zero_metadata_mutation_claimed") is False, "public guard absolute-zero metadata overclaim", errors)
    _require(guard_public.get("os_atime_restoration_performed") is False, "public guard atime restoration must remain false", errors)
    _require(guard_public.get("production_raw_mutation_api_present") is False, "public guard production raw mutation API must remain absent", errors)
    for ambiguous in ("raw_mutation_detected", "raw_root_mutated", "raw_inbox_mutated"):
        _require(ambiguous not in guard_public, f"public guard ambiguous raw mutation field forbidden: {ambiguous}", errors)
    _require(guard_public.get("os_level_immutable_claimed") is False, "public guard OS immutable overclaim", errors)
    _require(guard_public.get("mutation_class_contract") == list(builder.EXPECTED_MUTATION_CLASSES), "mutation class contract drift", errors)


def _validate_evidence_slots(rows: Sequence[Mapping[str, Any]], errors: list[str]) -> None:
    _require(len(rows) == 30, "evidence slot rows must equal 30", errors)
    by_task: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        by_task.setdefault(str(row.get("task_id")), []).append(row)
        _require(row.get("status") in {"COVERED", "N/A_WITH_RATIONALE"}, "invalid evidence slot status", errors)
        if row.get("status") == "N/A_WITH_RATIONALE":
            _require(bool(str(row.get("not_applicable_reason", "")).strip()), "N/A evidence slot missing rationale", errors)
        else:
            _require(bool(row.get("evidence_refs")), "covered evidence slot missing ref", errors)
        _require(row.get("private_detail_published") is False, "private evidence published", errors)
    expected_slots = set(builder.EVIDENCE_SLOTS)
    for task in builder.TASKS:
        task_rows = by_task.get(task["task_id"], [])
        _require(len(task_rows) == 10 and {row.get("slot") for row in task_rows} == expected_slots, f"{task['task_id']} evidence slots drift", errors)


def _validate_receipts(rows: Sequence[Mapping[str, Any]], *, require_pass: bool, errors: list[str]) -> None:
    by_id = {str(row.get("validation_id")): row for row in rows}
    _require(len(rows) == len(by_id) == len(builder.EXPECTED_VALIDATION_RECEIPTS), "validation receipt count/uniqueness drift", errors)
    _require(set(by_id) == set(builder.EXPECTED_VALIDATION_RECEIPTS), "validation receipt ID set drift", errors)
    for validation_id, command in builder.EXPECTED_VALIDATION_RECEIPTS.items():
        row = by_id.get(validation_id, {})
        _require(row.get("command") == command, f"validation command drift: {validation_id}", errors)
        if require_pass:
            _require(row.get("result") == "PASS" and row.get("exit_code") == 0, f"validation receipt not exact PASS: {validation_id}", errors)
    if require_pass:
        try:
            builder._normalize_validation_rows(rows, project_root=PROJECT_ROOT)
        except (builder.BuildError, OSError, ValueError) as error:
            errors.append(f"validation receipt provenance invalid: {error}")


def _validate_artifact_integrity(manifest: Mapping[str, Any], errors: list[str]) -> None:
    bindings = manifest.get("artifact_integrity")
    _require(isinstance(bindings, list) and len(bindings) == 12, "artifact integrity binding count drift", errors)
    if not isinstance(bindings, list):
        return
    for binding in bindings:
        ref = str(binding.get("ref", ""))
        path = REPO_ROOT / ref
        _require(ref.startswith("KMFA/"), f"artifact ref outside KMFA: {ref}", errors)
        if _regular_single_link(path, errors, label="artifact integrity input"):
            payload = _read_bytes_no_follow(path, label="artifact integrity input")
            _require(binding.get("bytes") == len(payload) and binding.get("sha256") == _sha256(payload), f"artifact integrity drift: {ref}", errors)


def _validate_artifact_file_set(errors: list[str]) -> None:
    expected_files = {
        REPO_ROOT / ref
        for ref in builder.ARTIFACT_REFS.values()
        if ref.startswith("KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/")
    }
    expected_directories = {ARTIFACT_ROOT}
    for path in expected_files:
        parent = path.parent
        while parent != ARTIFACT_ROOT:
            expected_directories.add(parent)
            parent = parent.parent
    actual_files: set[Path] = set()
    actual_directories: set[Path] = set()
    stack = [ARTIFACT_ROOT]
    while stack:
        directory = stack.pop()
        try:
            directory_stat = os.lstat(directory)
        except FileNotFoundError:
            errors.append(f"artifact directory missing: {directory}")
            continue
        if stat.S_ISLNK(directory_stat.st_mode) or not stat.S_ISDIR(directory_stat.st_mode):
            errors.append(f"artifact directory type unsafe: {directory}")
            continue
        actual_directories.add(directory)
        try:
            entries = list(os.scandir(directory))
        except OSError as error:
            errors.append(f"artifact directory unreadable: {directory}: {error}")
            continue
        for entry in entries:
            path = Path(entry.path)
            try:
                value = entry.stat(follow_symlinks=False)
            except OSError as error:
                errors.append(f"artifact entry unreadable: {path}: {error}")
                continue
            if stat.S_ISLNK(value.st_mode):
                errors.append(f"artifact symlink forbidden: {path}")
            elif stat.S_ISDIR(value.st_mode):
                stack.append(path)
            elif stat.S_ISREG(value.st_mode):
                actual_files.add(path)
                _require(int(value.st_nlink) == 1, f"artifact hardlink forbidden: {path}", errors)
            else:
                errors.append(f"artifact special file forbidden: {path}")
    _require(
        actual_files == expected_files,
        f"S03-P1 artifact file set drift: expected={len(expected_files)} actual={len(actual_files)}",
        errors,
    )
    _require(
        actual_directories == expected_directories,
        f"S03-P1 artifact directory set drift: expected={len(expected_directories)} actual={len(actual_directories)}",
        errors,
    )
    for path in (PUBLIC_REGISTRY_PATH, PUBLIC_ALLOWLIST_PATH):
        try:
            value = os.lstat(path)
        except FileNotFoundError:
            errors.append(f"public protocol artifact missing: {path}")
            continue
        _require(
            stat.S_ISREG(value.st_mode) and not stat.S_ISLNK(value.st_mode) and int(value.st_nlink) == 1,
            f"public protocol artifact type/link unsafe: {path}",
            errors,
        )


def _validate_governance(errors: list[str], *, require_final_state: bool) -> None:
    expected_sets = (
        GOVERNANCE_COMMON_EXPECTED,
        GOVERNANCE_FINAL_EXPECTED if require_final_state else GOVERNANCE_PENDING_EXPECTED,
    )
    for relative, tokens in {
        relative: tuple(
            token
            for expected in expected_sets
            for token in expected.get(relative, ())
        )
        for relative in sorted(set().union(*(expected.keys() for expected in expected_sets)))
    }.items():
        path = PROJECT_ROOT / relative
        if _regular_single_link(path, errors, label="governance file"):
            text = _read_text_no_follow(path, label="governance file")
            for token in tokens:
                _require(token in text, f"governance token missing in {relative}: {token}", errors)
    for relative in (
        "docs/governance/project.yaml",
        "docs/governance/roadmap.yaml",
    ):
        path = PROJECT_ROOT / relative
        if not _regular_single_link(path, errors, label="governance identity file"):
            continue
        text = _read_text_no_follow(path, label="governance identity file")
        _require(
            _top_level_yaml_scalar(text, "current_stage_id") == "S03",
            f"top-level current_stage_id drift in {relative}",
            errors,
        )
        _require(
            _top_level_yaml_scalar(text, "current_phase_id") == builder.RUN_PHASE_ID,
            f"top-level current_phase_id drift in {relative}",
            errors,
        )
    metadata_path = PROJECT_ROOT / "metadata/project/project.yaml"
    if not _regular_single_link(metadata_path, errors, label="metadata project file"):
        return
    metadata_text = _read_text_no_follow(metadata_path, label="metadata project file")
    _require(
        _top_level_yaml_scalar(metadata_text, "current_stage") == "S03",
        "top-level current_stage drift in metadata/project/project.yaml",
        errors,
    )
    _require(
        _top_level_yaml_scalar(metadata_text, "current_phase") == builder.RUN_PHASE_ID,
        "top-level current_phase drift in metadata/project/project.yaml",
        errors,
    )
    roadmap_path = PROJECT_ROOT / "docs/governance/roadmap.yaml"
    if not _regular_single_link(roadmap_path, errors, label="roadmap file"):
        return
    roadmap_text = _read_text_no_follow(roadmap_path, label="roadmap file")
    _require(
        re.search(
            rf'^  current_phase_id:\s*["\']{re.escape(builder.RUN_PHASE_ID)}["\']\s*$',
            roadmap_text,
            re.MULTILINE,
        )
        is not None,
        "active_roadmap current_phase_id drift",
        errors,
    )
    _require(
        re.search(r'^        - phase_id:\s*["\']S03-P1["\']\s*$', roadmap_text, re.MULTILINE)
        is not None,
        "TaskPack Roadmap S03-P1 phase binding missing",
        errors,
    )
    for path, token in (
        (PROJECT_ROOT / "docs/governance/formula_registry.yaml", "FORM-KMFA-V015-S03-P1-READ-ONLY-ROOT-GUARD-001"),
        (PROJECT_ROOT / "docs/governance/parameter_registry.csv", "PARAM-KMFA-1855"),
        (PROJECT_ROOT / "docs/governance/model_registry.yaml", builder.RUN_PHASE_ID),
        (PROJECT_ROOT / "metadata/model_registry.yaml", builder.RUN_PHASE_ID),
    ):
        _require(
            _regular_single_link(path, errors, label="governance registry")
            and token in _read_text_no_follow(path, label="governance registry"),
            f"governance registry binding missing: {token}",
            errors,
        )
    formula_path = PROJECT_ROOT / "docs/governance/formula_registry.yaml"
    formula_text = _read_text_no_follow(formula_path, label="formula registry")
    formula_token = 'formula_id: "FORM-KMFA-V015-S03-P1-READ-ONLY-ROOT-GUARD-001"'
    formula_start = formula_text.find(formula_token)
    next_formula = formula_text.find("\n  - formula_id:", formula_start + len(formula_token))
    formula_block = formula_text[formula_start: next_formula if next_formula >= 0 else None]
    _require(formula_start >= 0, "S03-P1 formula block missing", errors)
    _require('definition_status: "ACTIVE"' in formula_block, "S03-P1 formula definition status drift", errors)
    _require(
        'evaluation_mode: "RECEIPT_BOUND_POST_VALIDATION"' in formula_block,
        "S03-P1 formula evaluation mode drift",
        errors,
    )
    _require("evaluation_status:" not in formula_block, "acceptance-mutable formula evaluation status forbidden", errors)
    parameter_path = PROJECT_ROOT / "docs/governance/parameter_registry.csv"
    if not _regular_single_link(parameter_path, errors, label="parameter registry"):
        return
    parameter_rows = list(csv.DictReader(
        _read_text_no_follow(parameter_path, label="parameter registry").splitlines()
    ))
    for parameter_id, (symbol, active_value) in EXPECTED_PARAMETER_ROWS.items():
        matches = [row for row in parameter_rows if row.get("parameter_id") == parameter_id]
        _require(len(matches) == 1, f"governance parameter uniqueness drift: {parameter_id}", errors)
        if len(matches) == 1:
            row = matches[0]
            _require(row.get("model_id") == "MOD-KMFA-GOV-001", f"parameter model drift: {parameter_id}", errors)
            _require(row.get("formula_id") == "FORM-KMFA-V015-S03-P1-READ-ONLY-ROOT-GUARD-001", f"parameter formula drift: {parameter_id}", errors)
            _require(row.get("symbol") == symbol, f"parameter symbol drift: {parameter_id}", errors)
            _require(row.get("active_value") == active_value, f"parameter active value drift: {parameter_id}", errors)
            _require(row.get("status") == "active", f"parameter status drift: {parameter_id}", errors)


def _validate_final_governance_corrections(
    manifest: Mapping[str, Any],
    receipts: Sequence[Mapping[str, Any]],
    errors: list[str],
) -> None:
    """Bind post-receipt gate promotion to append-only, truthful final events."""

    pass_rows = [row for row in receipts if row.get("result") == "PASS"]
    run_ids = {str(row.get("run_id")) for row in pass_rows}
    _require(
        len(pass_rows) == len(builder.EXPECTED_VALIDATION_RECEIPTS) and len(run_ids) == 1,
        "final governance correction requires one complete receipt run",
        errors,
    )
    run_id = next(iter(run_ids), "")
    try:
        newest_receipt_end = max(
            datetime.fromisoformat(str(row["ended_at"]).replace("Z", "+00:00"))
            for row in pass_rows
        )
    except (KeyError, ValueError):
        errors.append("final governance correction receipt time invalid")
        return
    raw = manifest.get("raw_access", {})
    atime_observed = raw.get("os_atime_side_effect_observed")
    _require(type(atime_observed) is bool, "final manifest atime observation must be boolean", errors)
    for path, identity_key, expected_identity, supersedes_key, expected_supersedes in FINAL_LEDGER_SOURCES:
        if not _regular_single_link(path, errors, label="final governance ledger"):
            continue
        try:
            rows = _read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"final governance ledger parse failed: {path}: {error}")
            continue
        _require(bool(rows), f"final governance ledger empty: {path}", errors)
        if not rows:
            continue
        row = rows[-1]
        _require(row.get(identity_key) == expected_identity, f"final governance correction identity drift: {path}", errors)
        _require(
            row.get(supersedes_key) == expected_supersedes,
            f"final governance correction supersedes binding drift: {path}",
            errors,
        )
        expected_fields = {
            "correction_reason": FINAL_CORRECTION_REASON,
            "status": FINAL_CORRECTION_STATUS,
            "phase_acceptance_status": "PASSED",
            "final_validation_status": "PASS",
            "decision": "CONTINUE_TO_S03_P2_ONLY",
            "s03_p2_entry_allowed": True,
            "s03_p2_started": False,
            "prohibited_raw_mutation_detected": False,
            "prohibited_mutation_scope": list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
            "os_atime_side_effect_possible": True,
            "os_atime_side_effect_observed": atime_observed,
            "historical_pre_v2_atime_effect_unknown": True,
            "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
            "absolute_zero_metadata_mutation_claimed": False,
            "os_atime_restoration_performed": False,
            "production_raw_mutation_api_present": False,
            "validation_run_id": run_id,
            "validation_receipt_count": len(builder.EXPECTED_VALIDATION_RECEIPTS),
            "open_risk_count": 4,
        }
        for key, expected in expected_fields.items():
            _require(row.get(key) == expected, f"final governance correction field drift: {path}:{key}", errors)
        for ambiguous in ("raw_mutation_detected", "raw_root_mutated", "raw_inbox_mutated"):
            _require(ambiguous not in row, f"final governance correction ambiguous field forbidden: {path}:{ambiguous}", errors)
        try:
            event_time = datetime.fromisoformat(str(row.get("event_time", "")).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"final governance correction event_time invalid: {path}")
        else:
            _require(
                event_time >= newest_receipt_end,
                f"final governance correction predates receipt completion: {path}",
                errors,
            )


def _validate_pending_governance_authority(errors: list[str]) -> None:
    """Require a truthful pending authority row before the live receipt run."""

    expected_fields = {
        "correction_reason": PENDING_CORRECTION_REASON,
        "status": PENDING_CORRECTION_STATUS,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PENDING_FINAL_VALIDATION",
        "final_validation_status": "PENDING",
        "decision": "REMAIN_IN_S03_P1",
        "s03_p2_entry_allowed": False,
        "s03_p2_started": False,
        "prohibited_raw_mutation_status": "PENDING_FINAL_LIVE_REPLAY",
        "os_atime_side_effect_possible": True,
        "os_atime_observation_status": "PENDING_FINAL_LIVE_REPLAY",
        "historical_pre_v2_atime_effect_unknown": True,
        "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
        "absolute_zero_metadata_mutation_claimed": False,
        "os_atime_restoration_performed": False,
        "production_raw_mutation_api_present": False,
        "open_risk_count": 4,
    }
    for path, identity_key, expected_identity in PENDING_LEDGER_SOURCES:
        if not _regular_single_link(path, errors, label="pending governance ledger"):
            continue
        try:
            rows = _read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"pending governance ledger parse failed: {path}: {error}")
            continue
        _require(bool(rows), f"pending governance ledger empty: {path}", errors)
        if not rows:
            continue
        row = rows[-1]
        _require(row.get(identity_key) == expected_identity, f"pending governance authority identity drift: {path}", errors)
        for key, expected in expected_fields.items():
            _require(row.get(key) == expected, f"pending governance authority field drift: {path}:{key}", errors)
        for ambiguous in ("raw_mutation_detected", "raw_root_mutated", "raw_inbox_mutated"):
            _require(ambiguous not in row, f"pending governance authority ambiguous field forbidden: {path}:{ambiguous}", errors)
        try:
            event_time = datetime.fromisoformat(str(row.get("event_time", "")).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"pending governance authority event_time invalid: {path}")
        else:
            _require(
                event_time.tzinfo is not None and event_time.utcoffset() is not None,
                f"pending governance authority timezone missing: {path}",
                errors,
            )


def _validate_pre_receipt_final_governance_authority(errors: list[str]) -> None:
    """Validate final-governance shape before a replacement receipt run exists.

    This narrow remediation mode deliberately does not claim that the current
    final ledger is bound to the replacement run.  The normal final validator
    performs that binding after the new receipts are materialized.
    """

    expected_fields = {
        "correction_reason": FINAL_CORRECTION_REASON,
        "status": FINAL_CORRECTION_STATUS,
        "phase_execution_status": "EXECUTION_COMPLETE",
        "phase_acceptance_status": "PASSED",
        "final_validation_status": "PASS",
        "decision": "CONTINUE_TO_S03_P2_ONLY",
        "s03_p2_entry_allowed": True,
        "s03_p2_started": False,
        "prohibited_raw_mutation_detected": False,
        "prohibited_mutation_scope": list(builder.EXPECTED_PROHIBITED_MUTATION_SCOPE),
        "os_atime_side_effect_possible": True,
        "historical_pre_v2_atime_effect_unknown": True,
        "os_atime_observation_scope": "FINAL_V2_REPLAY_ONLY",
        "absolute_zero_metadata_mutation_claimed": False,
        "os_atime_restoration_performed": False,
        "production_raw_mutation_api_present": False,
        "validation_receipt_count": len(builder.EXPECTED_VALIDATION_RECEIPTS),
        "open_risk_count": 4,
    }
    for path, identity_key, expected_identity, supersedes_key, expected_supersedes in FINAL_LEDGER_SOURCES:
        if not _regular_single_link(path, errors, label="pre-receipt final governance ledger"):
            continue
        try:
            rows = _read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"pre-receipt final governance ledger parse failed: {path}: {error}")
            continue
        _require(bool(rows), f"pre-receipt final governance ledger empty: {path}", errors)
        if not rows:
            continue
        row = rows[-1]
        _require(
            row.get(identity_key) == expected_identity,
            f"pre-receipt final governance identity drift: {path}",
            errors,
        )
        _require(
            row.get(supersedes_key) == expected_supersedes,
            f"pre-receipt final governance supersedes drift: {path}",
            errors,
        )
        for key, expected in expected_fields.items():
            _require(
                row.get(key) == expected,
                f"pre-receipt final governance field drift: {path}:{key}",
                errors,
            )
        _require(
            type(row.get("os_atime_side_effect_observed")) is bool,
            f"pre-receipt final governance atime observation invalid: {path}",
            errors,
        )
        _require(
            isinstance(row.get("validation_run_id"), str)
            and re.fullmatch(r"[0-9a-f]{32}", row["validation_run_id"]) is not None,
            f"pre-receipt final governance prior run_id invalid: {path}",
            errors,
        )
        for ambiguous in ("raw_mutation_detected", "raw_root_mutated", "raw_inbox_mutated"):
            _require(
                ambiguous not in row,
                f"pre-receipt final governance ambiguous field forbidden: {path}:{ambiguous}",
                errors,
            )
        try:
            event_time = datetime.fromisoformat(str(row.get("event_time", "")).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"pre-receipt final governance event_time invalid: {path}")
        else:
            _require(
                event_time.tzinfo is not None and event_time.utcoffset() is not None,
                f"pre-receipt final governance timezone missing: {path}",
                errors,
            )


def validate_frozen_s02_dependency(repo_root: Path = REPO_ROOT) -> None:
    errors: list[str] = []
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"],
        cwd=repo_root, capture_output=True, check=False,
    )
    _require(ancestor.returncode == 0, "S02 review commit is not an ancestor of HEAD", errors)
    for ref in S02_FROZEN_REFS:
        committed = subprocess.run(
            ["git", "show", f"{builder.PHASE_BASE_COMMIT}:{ref}"],
            cwd=repo_root, capture_output=True, check=False,
        )
        path = repo_root / ref
        path_safe = _regular_single_link(path, errors, label="frozen S02 dependency")
        _require(committed.returncode == 0 and path_safe, f"frozen S02 dependency missing: {ref}", errors)
        if committed.returncode == 0 and path_safe:
            _require(
                committed.stdout == _read_bytes_no_follow(path, label="frozen S02 dependency"),
                f"frozen S02 dependency drift: {ref}",
                errors,
            )
    manifest_path = repo_root / S02_FROZEN_REFS[0]
    if _regular_single_link(manifest_path, errors, label="frozen S02 manifest"):
        manifest = _read_json(manifest_path)
        gate = manifest.get("stage_gate", {})
        _require(gate.get("stage_lifecycle_status") == "COMPLETED", "S02 dependency lifecycle drift", errors)
        _require(gate.get("stage_acceptance_status") == "PASSED", "S02 dependency acceptance drift", errors)
        _require(gate.get("decision") == "GO_TO_S03_P1_ONLY", "S02 dependency decision drift", errors)
        _require(manifest.get("content_hash") == _content_hash(manifest), "S02 dependency content_hash drift", errors)
    if errors:
        raise ValidationError("\n".join(errors))


def run_structured_public_diff_check(base_ref: str = builder.PHASE_BASE_COMMIT, *, repo_root: Path = REPO_ROOT) -> None:
    errors: list[str] = []
    _require(base_ref == builder.PHASE_BASE_COMMIT, "diff base must equal frozen S03-P1 base", errors)
    diff_check = subprocess.run(["git", "diff", "--check", base_ref, "--", "KMFA"], cwd=repo_root, capture_output=True, text=True, check=False)
    _require(diff_check.returncode == 0, "git diff --check failed: " + (diff_check.stdout + diff_check.stderr).strip(), errors)
    changed = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--name-only", base_ref, "--", "KMFA"], cwd=repo_root, capture_output=True, text=True, check=False)
    untracked = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard", "--", "KMFA"], cwd=repo_root, capture_output=True, text=True, check=False)
    _require(changed.returncode == 0 and untracked.returncode == 0, "changed-path scan failed", errors)
    paths = sorted(set(line.strip() for line in (changed.stdout + "\n" + untracked.stdout).splitlines() if line.strip()))
    safe_paths: set[str] = set()
    for relative in paths:
        _require(relative in ALLOWED_DIFF_PATHS, f"phase diff path outside exact allowlist: {relative}", errors)
        path = repo_root / relative
        if _regular_single_link(path, errors, label="phase diff file"):
            safe_paths.add(relative)
        if relative in safe_paths and path.suffix.lower() in {".json", ".jsonl", ".csv"}:
            try:
                if path.suffix.lower() == ".json":
                    json.loads(_read_text_no_follow(path, label="structured diff JSON"))
                elif path.suffix.lower() == ".jsonl":
                    _read_jsonl(path)
                else:
                    list(csv.DictReader(
                        _read_text_no_follow(path, label="structured diff CSV").splitlines()
                    ))
            except (OSError, ValueError, json.JSONDecodeError) as error:
                errors.append(f"structured parse failed for {relative}: {error}")
    added = subprocess.run(["git", "diff", "--unified=0", "--no-color", base_ref, "--", "KMFA"], cwd=repo_root, capture_output=True, check=False)
    _require(added.returncode == 0, "git diff added-line scan failed", errors)
    added_payload = b"\n".join(line[1:] for line in added.stdout.splitlines() if line.startswith(b"+") and not line.startswith(b"+++"))
    for relative in paths:
        path = repo_root / relative
        if relative in untracked.stdout.splitlines() and relative in safe_paths:
            added_payload += b"\n" + _read_bytes_no_follow(path, label="untracked public diff")
    _validate_public_payload(added_payload, errors, label="S03-P1 diff")
    for ref in builder.ARTIFACT_REFS.values():
        path = repo_root / ref
        if ".codex_private_runtime/" not in ref and _regular_single_link(
            path, errors, label="public artifact"
        ):
            _validate_public_payload(
                _read_bytes_no_follow(path, label="public artifact"),
                errors,
                label=ref,
            )
    if errors:
        raise ValidationError("\n".join(errors))


def _validate_private_evidence(errors: list[str], *, require_event_monitor: bool) -> None:
    try:
        private = builder._validate_private_evidence(PROJECT_ROOT)
    except (builder.BuildError, guard.GuardError, OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"private evidence invalid: {error}")
        return
    for key in ("policy_ref", "receipt_ref", "projection_ref"):
        ref = str(private[key])
        ignored = subprocess.run(["git", "check-ignore", "-q", ref], cwd=REPO_ROOT, check=False)
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", ref], cwd=REPO_ROOT, capture_output=True, check=False)
        _require(ignored.returncode == 0, f"private evidence not gitignored: {ref}", errors)
        _require(tracked.returncode != 0, f"private evidence is tracked: {ref}", errors)
    if require_event_monitor:
        projection = private["projection"]
        monitor = projection.get("monitor", {})
        _require(monitor.get("backend") == guard.DarwinKqueueVnodeMonitor.name, "exact Darwin kqueue event backend required", errors)
        _require(monitor.get("status") == "PASS", "event monitor PASS required", errors)
        _require(monitor.get("production_backend_attested") is True, "production kqueue attestation required", errors)
        _require(monitor.get("controlled_window_seconds") == guard.CONTROLLED_WINDOW_SECONDS, "controlled window must be exact", errors)
        _require(monitor.get("final_drain_seconds") == guard.FINAL_DRAIN_SECONDS, "final drain must be exact", errors)
        _require(monitor.get("mutation_event_detected") is False, "event monitor mutation detected", errors)


def _validate_private_evidence_freshness(
    errors: list[str],
    *,
    max_age_seconds: float,
    now_seconds: Optional[float] = None,
) -> None:
    if max_age_seconds <= 0:
        errors.append("private evidence max age must be positive")
        return
    now = time.time() if now_seconds is None else float(now_seconds)
    mtimes: list[float] = []
    for relative, expected_mode in (
        (builder.PRIVATE_RECEIPT_RELATIVE, 0o600),
        (builder.PRIVATE_PROJECTION_RELATIVE, 0o644),
    ):
        path = PROJECT_ROOT / relative
        try:
            value = os.lstat(path)
        except OSError as error:
            errors.append(f"private evidence freshness input unavailable: {path}: {error}")
            continue
        _require(
            stat.S_ISREG(value.st_mode)
            and not stat.S_ISLNK(value.st_mode)
            and int(value.st_nlink) == 1
            and stat.S_IMODE(value.st_mode) == expected_mode,
            f"private evidence freshness input type/link/mode unsafe: {path}",
            errors,
        )
        age = now - float(value.st_mtime)
        _require(
            -300 <= age <= max_age_seconds,
            f"private evidence is outside freshness window: {path}",
            errors,
        )
        mtimes.append(float(value.st_mtime))
    if len(mtimes) == 2:
        _require(
            abs(mtimes[0] - mtimes[1]) <= 5,
            "private receipt/projection freshness timestamps drift",
            errors,
        )


def _validate_clean_committed_blobs(manifest: Mapping[str, Any], errors: list[str]) -> None:
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    _require(status.returncode == 0 and status.stdout == "", "worktree must be clean", errors)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=False).stdout.strip()
    _require(bool(re.fullmatch(r"[0-9a-f]{40}", head)), "HEAD resolution failed", errors)
    refs = set(manifest.get("artifact_refs", {}).values())
    for ref in refs:
        if ".codex_private_runtime/" in str(ref):
            continue
        path = REPO_ROOT / str(ref)
        committed = subprocess.run(["git", "show", f"{head}:{ref}"], cwd=REPO_ROOT, capture_output=True, check=False)
        _require(
            _regular_single_link(path, errors, label="committed artifact")
            and committed.returncode == 0
            and committed.stdout == _read_bytes_no_follow(path, label="committed artifact"),
            f"committed blob drift: {ref}",
            errors,
        )
    result_commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", builder.ARTIFACT_REFS["manifest"]], cwd=REPO_ROOT, capture_output=True, text=True, check=False).stdout.strip()
    _require(result_commit == head, "S03-P1 manifest result commit must equal HEAD", errors)
    try:
        run_structured_public_diff_check(repo_root=REPO_ROOT)
    except ValidationError as error:
        errors.append(str(error))


def validate_v015_s03_p1(
    *, require_validation_receipts: bool = False, require_private_evidence: bool = False,
    require_event_monitor: bool = False, require_dependency_validator: bool = False,
    require_clean_worktree: bool = False, skip_exact_rebuild: bool = False,
    pre_receipt_final_governance: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    _require(
        not (require_validation_receipts and pre_receipt_final_governance),
        "pre-receipt final governance mode cannot require validation receipts",
        errors,
    )
    required_paths = (
        MANIFEST_PATH, TASK_MATRIX_PATH, WRITE_GUARD_PATH, READ_SCOPE_PATH,
        EVIDENCE_SLOTS_PATH, VALIDATION_RESULTS_PATH, PUBLIC_REGISTRY_PATH, PUBLIC_ALLOWLIST_PATH,
    )
    _validate_artifact_file_set(errors)
    for path in required_paths:
        _regular_single_link(path, errors, label="required artifact")
    if errors:
        raise ValidationError("\n".join(errors))
    manifest = _read_json(MANIFEST_PATH)
    matrix = _read_json(TASK_MATRIX_PATH)
    guard_public = _read_json(WRITE_GUARD_PATH)
    read_scope = _read_json(READ_SCOPE_PATH)
    registry = _read_json(PUBLIC_REGISTRY_PATH)
    allowlist = _read_json(PUBLIC_ALLOWLIST_PATH)
    slots = _read_jsonl(EVIDENCE_SLOTS_PATH)
    receipts = _read_jsonl(VALIDATION_RESULTS_PATH)
    _validate_manifest(manifest, errors, require_pass=require_validation_receipts)
    _validate_matrix(matrix, errors, require_pass=require_validation_receipts)
    _validate_policies(registry, allowlist, guard_public, errors)
    _require(read_scope == allowlist, "stage/public allowlist projection drift", errors)
    _validate_evidence_slots(slots, errors)
    _validate_receipts(receipts, require_pass=require_validation_receipts, errors=errors)
    _validate_artifact_integrity(manifest, errors)
    _validate_governance(
        errors,
        require_final_state=(require_validation_receipts or pre_receipt_final_governance),
    )
    if require_validation_receipts:
        _validate_final_governance_corrections(manifest, receipts, errors)
    elif pre_receipt_final_governance:
        _validate_pre_receipt_final_governance_authority(errors)
    else:
        _validate_pending_governance_authority(errors)
    for path in required_paths:
        _validate_public_payload(
            _read_bytes_no_follow(path, label="required public artifact"),
            errors,
            label=str(path),
        )
    if require_private_evidence:
        _validate_private_evidence(errors, require_event_monitor=require_event_monitor)
    elif require_event_monitor:
        errors.append("--require-event-monitor requires --require-private-evidence")
    if require_dependency_validator:
        try:
            validate_frozen_s02_dependency()
        except ValidationError as error:
            errors.append(str(error))
    if not skip_exact_rebuild and require_private_evidence:
        try:
            outputs = builder.expected_outputs(
                project_root=PROJECT_ROOT,
                source_package=builder.DEFAULT_SOURCE_PACKAGE,
                generated_at=str(manifest.get("generated_at", "")),
                reuse_public_validation_results=True,
            )
            builder.check_outputs(outputs)
        except (builder.BuildError, guard.GuardError, OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"exact rebuild failed: {error}")
    try:
        run_structured_public_diff_check()
    except ValidationError as error:
        errors.append(str(error))
    if require_clean_worktree:
        _validate_clean_committed_blobs(manifest, errors)
    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-validation-receipts", action="store_true")
    parser.add_argument("--require-private-evidence", action="store_true")
    parser.add_argument("--require-event-monitor", action="store_true")
    parser.add_argument("--require-dependency-validator", action="store_true")
    parser.add_argument("--require-clean-worktree", action="store_true")
    parser.add_argument("--skip-validation-receipts", action="store_true")
    parser.add_argument("--skip-exact-rebuild", action="store_true")
    parser.add_argument("--structured-public-diff-check", action="store_true")
    parser.add_argument("--private-evidence-only", action="store_true")
    parser.add_argument("--pre-receipt-final-governance", action="store_true")
    parser.add_argument("--max-private-evidence-age-seconds", type=float, default=7200.0)
    parser.add_argument("--base-ref", default=builder.PHASE_BASE_COMMIT)
    args = parser.parse_args(argv)
    try:
        if args.structured_public_diff_check:
            run_structured_public_diff_check(args.base_ref)
            print("PASS: S03-P1 structured/public/diff checks")
            return 0
        if args.private_evidence_only:
            private_errors: list[str] = []
            _validate_private_evidence(
                private_errors,
                require_event_monitor=args.require_event_monitor,
            )
            _validate_private_evidence_freshness(
                private_errors,
                max_age_seconds=args.max_private_evidence_age_seconds,
            )
            if private_errors:
                raise ValidationError("\n".join(private_errors))
            print(
                "PASS: S03-P1 fresh v2 private guard evidence validated; "
                "no raw replay performed"
            )
            return 0
        manifest = validate_v015_s03_p1(
            require_validation_receipts=args.require_validation_receipts and not args.skip_validation_receipts,
            require_private_evidence=args.require_private_evidence,
            require_event_monitor=args.require_event_monitor,
            require_dependency_validator=args.require_dependency_validator,
            require_clean_worktree=args.require_clean_worktree,
            skip_exact_rebuild=args.skip_exact_rebuild,
            pre_receipt_final_governance=args.pre_receipt_final_governance,
        )
        print(
            "PASS: KMFA v1.5 S03-P1 validated; "
            f"Phase={manifest['acceptance_status']}/{manifest['decision']}; "
            "S03=IN_PROGRESS/PENDING/33%; "
            f"S03-P2 entry={str(manifest['next_entry_gate']['s03_p2_entry_allowed']).lower()} "
            "started=false"
        )
        return 0
    except (ValidationError, json.JSONDecodeError, OSError, ValueError) as error:
        print("FAIL: KMFA v1.5 S03-P1 validation failed")
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
