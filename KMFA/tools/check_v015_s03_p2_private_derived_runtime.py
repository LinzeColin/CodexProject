#!/usr/bin/env python3
"""Strict validator for KMFA v1.5 S03-P2 private derived runtime evidence."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from KMFA.tools import build_v015_s03_p2_private_derived_runtime as builder


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "KMFA"
ARTIFACT_ROOT = PROJECT_ROOT / builder.OUTPUT_ROOT_RELATIVE
MANIFEST_PATH = ARTIFACT_ROOT / builder.MANIFEST_RELATIVE
TASK_MATRIX_PATH = ARTIFACT_ROOT / builder.TASK_MATRIX_RELATIVE
RUNTIME_PATH = ARTIFACT_ROOT / builder.RUNTIME_VERIFICATION_RELATIVE
CLEANUP_PATH = ARTIFACT_ROOT / builder.CLEANUP_REHEARSAL_RELATIVE
EVIDENCE_SLOTS_PATH = ARTIFACT_ROOT / builder.EVIDENCE_SLOTS_RELATIVE
VALIDATION_RESULTS_PATH = ARTIFACT_ROOT / builder.VALIDATION_RESULTS_RELATIVE
DIRECTORY_POLICY_PATH = PROJECT_ROOT / builder.DIRECTORY_POLICY_RELATIVE
LIFECYCLE_POLICY_PATH = PROJECT_ROOT / builder.LIFECYCLE_POLICY_RELATIVE

STAGE_FILES = frozenset({
    builder.MANIFEST_RELATIVE.as_posix(),
    builder.TASK_MATRIX_RELATIVE.as_posix(),
    builder.RUNTIME_VERIFICATION_RELATIVE.as_posix(),
    builder.CLEANUP_REHEARSAL_RELATIVE.as_posix(),
    builder.EVIDENCE_SLOTS_RELATIVE.as_posix(),
    builder.RECEIPT_TEMPLATE_RELATIVE.as_posix(),
    builder.VALIDATION_RESULTS_RELATIVE.as_posix(),
    builder.COMPLETION_RELATIVE.as_posix(),
    builder.TEST_RESULTS_RELATIVE.as_posix(),
    builder.ROLLBACK_RELATIVE.as_posix(),
    builder.OPEN_RISKS_RELATIVE.as_posix(),
})

GOVERNANCE_REFS = frozenset({
    "KMFA/AGENTS.md", "KMFA/CHANGELOG.md", "KMFA/HANDOFF.md", "KMFA/README.md",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/docs/governance/project.yaml",
    "KMFA/docs/governance/roadmap.yaml",
    "KMFA/metadata/model_registry.yaml",
    "KMFA/metadata/project/project.yaml",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md",
})
IMPLEMENTATION_REFS = frozenset({
    "KMFA/.gitignore",
    "KMFA/tools/v015_s03_p2_private_derived_runtime.py",
    "KMFA/tools/build_v015_s03_p2_private_derived_runtime.py",
    "KMFA/tools/check_v015_s03_p2_private_derived_runtime.py",
    "KMFA/tools/run_v015_s03_p2_validations.py",
    "KMFA/tests/test_v015_s03_p2_private_derived_runtime.py",
    "KMFA/tests/test_v015_s03_p2_private_derived_runtime_governance.py",
    "KMFA/tests/test_v015_s03_p2_validation_runner.py",
    "KMFA/tools/v015_roadmap_governance_sync.py",
    "KMFA/tests/test_v015_roadmap_governance_sync.py",
    f"KMFA/{builder.DIRECTORY_POLICY_RELATIVE.as_posix()}",
    f"KMFA/{builder.LIFECYCLE_POLICY_RELATIVE.as_posix()}",
} | {
    f"KMFA/{builder.OUTPUT_ROOT_RELATIVE.as_posix()}/{relative}"
    for relative in STAGE_FILES
})
ALLOWED_DIFF_PATHS = GOVERNANCE_REFS | IMPLEMENTATION_REFS
POST_VALIDATION_GOVERNANCE_REFS = frozenset({
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/events.jsonl",
    "KMFA/metadata/stage_status.jsonl",
})
VALIDATION_MUTABLE_ARTIFACT_REFS = frozenset({
    ref
    for key, ref in builder.ARTIFACT_REFS.items()
    if key in builder.VALIDATION_MUTABLE_ARTIFACT_KEYS
})
POSTCOMMIT_EVIDENCE_BOUND_REFS = frozenset(builder.VALIDATION_SUBJECT_REFS) | (
    VALIDATION_MUTABLE_ARTIFACT_REFS | POST_VALIDATION_GOVERNANCE_REFS
)
POSTCOMMIT_ALLOWED_REFS = frozenset(
    ALLOWED_DIFF_PATHS & POSTCOMMIT_EVIDENCE_BOUND_REFS
)
POSTCOMMIT_REMEDIATION_ID = "S03P2-FIX-POSTCOMMIT-VALIDATION-HEAD-CYCLE-V2"
POSTCOMMIT_HEAD_POLICY = (
    "CURRENT_OR_IMMEDIATE_FIRST_PARENT_WITH_PHASE_BASE_AND_SUBJECT_BINDING"
)
ASSURANCE_POSTVALIDATION_KEYS = frozenset({
    "as_of_event_id", "source_snapshot_hash", "source_tree_hash",
    "snapshot_event_time",
})

FROZEN_S03_P1_REFS = frozenset({
    "KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/machine/s03_p1_read_only_root_governance_manifest.json",
    "KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/machine/task_acceptance_matrix_public_safe.json",
    "KMFA/stage_artifacts/V015_S03_P1_READ_ONLY_ROOT_GOVERNANCE/machine/write_protection_validation_public_safe.json",
    "KMFA/metadata/protocol/v015_s03_p1_read_only_root_registry_public_safe.json",
    "KMFA/metadata/protocol/v015_s03_p1_read_allowlist_public_safe.json",
    "KMFA/tools/v015_s03_p1_read_only_root_guard.py",
    "KMFA/tools/build_v015_s03_p1_read_only_root_governance.py",
    "KMFA/tools/check_v015_s03_p1_read_only_root_governance.py",
    "KMFA/tools/run_v015_s03_p1_validations.py",
    "KMFA/tests/test_v015_s03_p1_read_only_root_guard.py",
    "KMFA/tests/test_v015_s03_p1_read_only_root_governance.py",
    "KMFA/tests/test_v015_s03_p1_validation_runner.py",
})

EXPECTED_GOVERNANCE = {
    "current_phase_id": builder.RUN_PHASE_ID,
    "current_task_id": builder.TASK_ID,
    "current_acceptance_id": builder.ACCEPTANCE_ID,
    "phase_execution_status": "EXECUTION_COMPLETE",
    "phase_acceptance_status": "PASSED",
    "evidence_validation_status": "PASS",
    "stage_lifecycle_status": "IN_PROGRESS",
    "stage_acceptance_status": "PENDING",
    "stage_execution_percentage": "67",
    "stage_phase_pass_count": "2",
    "stage_task_accepted_count": "6",
    "phase_task_count": "3",
    "phase_task_accepted_count": "3",
    "private_runtime_layer_count": "9",
    "content_copy_run_count": "2",
    "p1_baseline_exact_match": "true",
    "copy_final_drain_seconds": "0.25",
    "runtime_root_identity_stable": "true",
    "runtime_root_dirfd_held": "true",
    "private_source_file_count": "5",
    "raw_copy_performed": "true",
    "raw_business_interpretation_performed": "false",
    "raw_value_extraction_performed": "false",
    "prohibited_raw_mutation_detected": "false",
    "os_atime_side_effect_possible": "true",
    "absolute_zero_metadata_mutation_claimed": "false",
    "os_atime_restoration_performed": "false",
    "canonical_cleanup_candidate_count": "0",
    "synthetic_cleanup_rehearsal_pass": "true",
    "open_risk_count": "8",
    "active_formula_count": "326",
    "active_parameter_count": "1484",
    "current_parameter_range": "PARAM-KMFA-1861..1869",
    "governance_model_count": "10",
    "decision": "CONTINUE_TO_S03_P3_ONLY",
    "s03_p2_started": "true",
    "s03_p2_acceptance_status": "PASSED",
    "s03_p3_entry_allowed": "true",
    "s03_p3_started": "false",
    "s03_stage_review_entry_allowed": "false",
    "product_implementation_allowed": "false",
    "github_upload_performed_by_current_run": "false",
    "app_reinstall_performed_by_current_run": "false",
    "irreversible_real_cleanup_performed": "false",
}


class ValidationError(RuntimeError):
    """Strict S03-P2 validation failure."""


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _regular_single_link(path: Path, errors: list[str], *, label: str) -> bool:
    try:
        value = os.lstat(path)
    except OSError as error:
        errors.append(f"{label} missing: {path}: {error}")
        return False
    safe = stat.S_ISREG(value.st_mode) and int(value.st_nlink) == 1
    _require(safe, f"{label} type/link unsafe: {path}", errors)
    return safe


def _read_bytes(path: Path, *, label: str) -> bytes:
    return builder._read_regular_bytes_no_follow(path, label=label)


def _read_json(path: Path) -> dict[str, Any]:
    return builder._read_json(path, label=str(path))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return builder._read_jsonl(path, label=str(path))


def _top_level_yaml_scalar(text: str, key: str) -> Optional[str]:
    pattern = re.compile(
        rf"^(?![ \t-]){re.escape(key)}:[ \t]*(?:\"([^\"]*)\"|'([^']*)'|([^#\r\n]*?))[ \t]*(?:#.*)?$",
        re.MULTILINE,
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        return None
    return next((part for part in matches[0] if part != ""), "").strip()


def _validate_public_payload(payload: bytes, errors: list[str], *, label: str) -> None:
    for token in builder._FORBIDDEN_PUBLIC_TOKENS:
        _require(token not in payload, f"{label}: public-safe token leak: {token!r}", errors)
    _require(builder._EMAIL_RE.search(payload) is None, f"{label}: email leak", errors)
    _require(builder._SECRET_RE.search(payload) is None, f"{label}: secret-like assignment", errors)


def _validate_manifest(manifest: Mapping[str, Any], errors: list[str], *, require_pass: bool) -> None:
    expected = {
        "schema_version": "kmfa.v015.s03_p2.private_derived_runtime.public_safe.v1",
        "project_id": "KMFA", "target_release": "v1.5",
        "stage_id": "S03", "phase_id": "S03-P2",
        "run_phase_id": builder.RUN_PHASE_ID, "task_id": builder.TASK_ID,
        "acceptance_id": builder.ACCEPTANCE_ID, "phase_base_commit": builder.PHASE_BASE_COMMIT,
        "execution_status": "EXECUTION_COMPLETE",
    }
    for key, value in expected.items():
        _require(manifest.get(key) == value, f"manifest {key} drift", errors)
    _require(manifest.get("content_hash") == builder._content_hash(manifest), "manifest content_hash drift", errors)
    _require(
        manifest.get("open_risk_accounting")
        == {"total": 5, "blocking": 0, "p0": 0, "p1": 1, "p2": 4, "plan_gap_count": 0},
        "manifest open-risk accounting drift",
        errors,
    )
    _require(manifest.get("stage_status") == {
        "lifecycle": "IN_PROGRESS", "acceptance": "PENDING", "execution_percentage": 67,
    }, "manifest Stage status drift", errors)
    runtime = manifest.get("private_runtime", {})
    _require(runtime.get("layer_count") == 9 and runtime.get("all_layers_gitignored") is True, "manifest runtime contract drift", errors)
    _require(
        manifest.get("boundary_binding")
        == {
            "fixed_p1_policy_and_receipt": True,
            "p1_final_snapshot_exact_match_both_runs": True,
            "raw_root_identity_match_both_runs": True,
            "final_drain_seconds": builder.runtime.p1_guard.FINAL_DRAIN_SECONDS,
            "fixed_project_runtime": True,
            "held_runtime_root_dirfd_both_runs": True,
            "runtime_root_identity_stable": True,
        },
        "manifest P1/runtime boundary binding drift",
        errors,
    )
    copy = manifest.get("copy_acceptance", {})
    for key, expected_value in (
        ("run_count", 2), ("second_run_created_count", 0), ("second_run_new_bytes", 0),
        ("blob_count_stable", True), ("hash_match_both_runs", True),
        ("inventory_digest_set_stable", True),
        ("idempotent_reuse_without_rewrite", True),
        ("prohibited_raw_mutation_detected", False),
        ("os_atime_restoration_performed", False),
        ("absolute_zero_metadata_mutation_claimed", False),
    ):
        _require(copy.get(key) == expected_value, f"manifest copy {key} drift", errors)
    _require(
        copy.get("first_inventory_count")
        == copy.get("second_inventory_count")
        == copy.get("unique_blob_count"),
        "manifest CAS inventory count drift",
        errors,
    )
    _require(copy.get("source_file_count") == builder.EXPECTED_SOURCE_FILE_COUNT, "manifest source count does not match frozen S03-P1", errors)
    cleanup = manifest.get("cleanup_acceptance", {})
    _require(cleanup == {
        "canonical_dry_run": True, "synthetic_rehearsal_pass": True,
        "protected_violation_count": 0, "irreversible_real_cleanup_performed": False,
        "second_confirmation_required": True,
    }, "manifest cleanup acceptance drift", errors)
    gate = manifest.get("next_entry_gate", {})
    downstream = manifest.get("downstream_actions", {})
    if require_pass:
        _require(manifest.get("acceptance_status") == "PASSED", "manifest acceptance not PASSED", errors)
        _require(manifest.get("evidence_validation_status") == "PASS", "manifest evidence validation not PASS", errors)
        _require(manifest.get("decision") == "CONTINUE_TO_S03_P3_ONLY", "manifest final decision drift", errors)
        _require(gate.get("next_allowed_run") == "S03-P3" and gate.get("s03_p3_entry_allowed") is True, "S03-P3 final gate drift", errors)
    else:
        _require(manifest.get("acceptance_status") in {"PENDING", "PASSED"}, "manifest pending state invalid", errors)
    _require(gate.get("s03_p3_started") is False, "S03-P3 started in S03-P2 run", errors)
    _require(downstream.get("s03_p3_started") is False, "downstream S03-P3 started", errors)
    _require(downstream.get("github_upload_performed") is False, "GitHub upload occurred", errors)
    _require(downstream.get("app_reinstall_performed") is False, "App reinstall occurred", errors)
    _require(downstream.get("irreversible_real_cleanup_performed") is False, "real irreversible cleanup occurred", errors)


def _validate_matrix(matrix: Mapping[str, Any], errors: list[str], *, require_pass: bool) -> None:
    tasks = matrix.get("tasks")
    _require(isinstance(tasks, list) and len(tasks) == 3, "task matrix must contain three Tasks", errors)
    if not isinstance(tasks, list):
        return
    for row, expected_task in zip(tasks, builder.TASKS):
        _require(row.get("task_id") == expected_task["task_id"], "task matrix ID drift", errors)
        expected_contract = {
            key: expected_task[key]
            for key in ("name", "action", "output", "acceptance", "evidence", "stop")
        }
        _require(row.get("source_contract") == expected_contract, "task source contract drift", errors)
        _require(row.get("execution_status") == "EXECUTION_COMPLETE", "task execution incomplete", errors)
        if require_pass:
            _require(row.get("acceptance_status") == "PASSED", "task acceptance not PASSED", errors)
    if require_pass:
        _require(matrix.get("phase_acceptance_status") == "PASSED", "matrix Phase not PASSED", errors)
        _require(matrix.get("decision") == "CONTINUE_TO_S03_P3_ONLY", "matrix decision drift", errors)


def _validate_policies(
    directory: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    runtime: Mapping[str, Any],
    cleanup: Mapping[str, Any],
    errors: list[str],
) -> None:
    _require(directory == builder._directory_policy(), "directory policy deterministic drift", errors)
    _require(lifecycle == builder._lifecycle_policy(), "lifecycle policy deterministic drift", errors)
    layers = directory.get("layers", [])
    _require([row.get("layer_id") for row in layers] == list(builder.LAYERS), "directory layer order drift", errors)
    _require(all(row.get("gitignored") is True and row.get("directory_mode") == "0700" for row in layers), "directory layer ignore/mode drift", errors)
    _require(len(lifecycle.get("rules", [])) == 9, "lifecycle policy does not cover all layers", errors)
    _require(lifecycle.get("policy_basis") == "CONDITION_BASED_NO_UNSUPPORTED_RETENTION_DAYS", "unsupported retention-day claim", errors)
    try:
        builder._validate_projection(runtime)
    except builder.BuildError as error:
        errors.append(str(error))
    _require(runtime.get("directory_contract", {}).get("tracked_entry_count") == 0, "runtime tracked entry detected", errors)
    _require(runtime.get("directory_contract", {}).get("unsafe_entry_count") == 0, "runtime unsafe entry detected", errors)
    canonical = cleanup.get("canonical_runtime", {})
    synthetic = cleanup.get("synthetic_rehearsal", {})
    _require(canonical.get("mode") == "DRY_RUN" and canonical.get("candidate_count") == 0, "canonical cleanup is not zero-candidate dry-run", errors)
    _require(canonical.get("retention_basis") == "UNTIL_CONDITION" and canonical.get("auto_delete_enabled") is False, "canonical cleanup is not condition-based no-auto-delete", errors)
    _require(canonical.get("protected_violation_count") == 0, "cleanup protected violation", errors)
    _require(canonical.get("destructive_execution_performed") is False and canonical.get("real_runtime_deletion_allowed") is False, "real runtime deletion overclaim", errors)
    for key in (
        "passed", "plan_deterministic", "second_confirmation_required",
        "exact_plan_digest_required", "one_use_marker_required",
        "backup_verified", "delete_verified", "restore_verified", "rehash_verified",
    ):
        _require(synthetic.get(key) is True, f"synthetic cleanup {key} not proven", errors)


def _validate_slots(rows: Sequence[Mapping[str, Any]], errors: list[str]) -> None:
    _require(len(rows) == 30, "evidence slot count drift", errors)
    expected_pairs = [
        (task["task_id"], slot) for task in builder.TASKS for slot in builder.EVIDENCE_SLOTS
    ]
    _require([(row.get("task_id"), row.get("slot")) for row in rows] == expected_pairs, "evidence slot order/coverage drift", errors)
    for row in rows:
        _require(row.get("status") in {"COVERED", "N/A_WITH_RATIONALE"}, "evidence slot status invalid", errors)
        if row.get("status") == "N/A_WITH_RATIONALE":
            _require(bool(row.get("not_applicable_reason")), "N/A evidence slot lacks rationale", errors)
        else:
            _require(bool(row.get("evidence_refs")), "covered evidence slot lacks refs", errors)


def _committed_validation_head(
    rows: Sequence[Mapping[str, Any]],
    *,
    current_head: str,
) -> str:
    receipt_heads = {
        str(row.get(key) or "")
        for row in rows
        for key in ("head_before", "head_after")
    }
    if len(receipt_heads) != 1:
        return current_head
    candidate = next(iter(receipt_heads))
    if re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
        return current_head
    base_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, candidate],
        cwd=REPO_ROOT, capture_output=True, check=False,
    )
    if base_ancestor.returncode != 0:
        return current_head
    if candidate == current_head:
        return candidate
    parent = subprocess.run(
        ["git", "rev-parse", "--verify", f"{current_head}^1^{{commit}}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if (
        parent.returncode != 0
        or re.fullmatch(r"[0-9a-f]{40}", parent.stdout.strip()) is None
        or parent.stdout.strip() != candidate
    ):
        return current_head
    return candidate


def _validate_receipts(
    rows: Sequence[Mapping[str, Any]],
    errors: list[str],
    *,
    require_pass: bool,
    allow_committed_subject_head: bool = False,
) -> None:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        expected_validation_head = head
        if require_pass and allow_committed_subject_head:
            expected_validation_head = _committed_validation_head(
                rows,
                current_head=head,
            )
        builder._normalize_validation_rows(
            rows,
            require_pass=require_pass,
            current_head=expected_validation_head if require_pass else None,
        )
    except (builder.BuildError, ValueError) as error:
        errors.append(str(error))
        return
    if require_pass:
        try:
            subject = builder.validation_subject_sha256(PROJECT_ROOT)
        except (builder.BuildError, OSError) as error:
            errors.append(str(error))
            return
        _require(all(row.get("validation_subject_sha256") == subject for row in rows), "public receipt subject is stale", errors)
        private_path = PROJECT_ROOT / builder.PRIVATE_VALIDATION_RECEIPTS_RELATIVE
        if _regular_single_link(private_path, errors, label="private validation receipts"):
            value = os.lstat(private_path)
            _require(stat.S_IMODE(value.st_mode) == 0o600, "private validation receipt mode drift", errors)
            private_rows = _read_jsonl(private_path)
            _require(private_rows == list(rows), "public/private validation receipt projection drift", errors)
        now = datetime.now().astimezone()
        for row in rows:
            try:
                ended = datetime.fromisoformat(str(row.get("ended_at", "")).replace("Z", "+00:00"))
                age = (now - ended).total_seconds()
                _require(-300 <= age <= 7200, "validation receipt freshness drift", errors)
            except ValueError:
                errors.append("validation receipt ended_at invalid")


def _validate_integrity(manifest: Mapping[str, Any], errors: list[str]) -> None:
    rows = manifest.get("artifact_integrity")
    _require(isinstance(rows, list) and len(rows) == len(builder.ARTIFACT_REFS) - 1, "artifact integrity count drift", errors)
    if not isinstance(rows, list):
        return
    expected_refs = set(builder.ARTIFACT_REFS.values()) - {builder.ARTIFACT_REFS["manifest"]}
    _require({row.get("ref") for row in rows} == expected_refs, "artifact integrity ref set drift", errors)
    for row in rows:
        ref = row.get("ref")
        if not isinstance(ref, str):
            continue
        path = REPO_ROOT / ref
        if _regular_single_link(path, errors, label="integrity artifact"):
            payload = _read_bytes(path, label="integrity artifact")
            _require(row.get("bytes") == len(payload), f"artifact bytes drift: {ref}", errors)
            _require(row.get("sha256") == builder._sha256(payload), f"artifact digest drift: {ref}", errors)


def _validate_exact_file_set(errors: list[str]) -> None:
    if not ARTIFACT_ROOT.is_dir():
        errors.append("S03-P2 artifact root missing")
        return
    actual = set()
    for path in ARTIFACT_ROOT.rglob("*"):
        if path.is_file() or path.is_symlink():
            actual.add(path.relative_to(ARTIFACT_ROOT).as_posix())
    _require(actual == STAGE_FILES, f"S03-P2 exact artifact file set drift: {sorted(actual ^ STAGE_FILES)}", errors)


def _validate_governance(
    errors: list[str],
    *,
    require_final: bool,
    expected_atime_observed: Optional[bool] = None,
) -> None:
    if not require_final:
        return
    project_path = PROJECT_ROOT / "docs/governance/project.yaml"
    metadata_path = PROJECT_ROOT / "metadata/project/project.yaml"
    for path in (project_path, metadata_path):
        if not _regular_single_link(path, errors, label="governance authority"):
            continue
        text = _read_bytes(path, label="governance authority").decode("utf-8")
        for key, expected in EXPECTED_GOVERNANCE.items():
            candidate_key = key
            if path == metadata_path:
                candidate_key = {
                    "current_phase_id": "current_phase",
                    "current_task_id": "current_task",
                    "current_acceptance_id": "current_acceptance",
                }.get(key, key)
            actual = _top_level_yaml_scalar(text, candidate_key)
            _require(actual == expected, f"{path.name} {candidate_key} drift: {actual!r}", errors)
        atime = _top_level_yaml_scalar(text, "os_atime_side_effect_observed")
        _require(atime in {"true", "false"}, f"{path.name} atime observation missing", errors)
        if expected_atime_observed is not None:
            _require(
                atime == str(expected_atime_observed).lower(),
                f"{path.name} atime observation/projection drift",
                errors,
            )
    required_tokens = {
        "README.md": (builder.RUN_PHASE_ID, "CONTINUE_TO_S03_P3_ONLY", "67%"),
        "HANDOFF.md": (builder.RUN_PHASE_ID, "CONTINUE_TO_S03_P3_ONLY", "s03_p3_started=false"),
        "功能清单.md": (builder.RUN_PHASE_ID, "S03-P2"),
        "开发记录.md": (builder.RUN_PHASE_ID, "CONTINUE_TO_S03_P3_ONLY"),
        "模型参数文件.md": ("PARAM-KMFA-1861", "PARAM-KMFA-1869"),
    }
    for relative, tokens in required_tokens.items():
        path = PROJECT_ROOT / relative
        if _regular_single_link(path, errors, label="governance human plane"):
            text = _read_bytes(path, label="governance human plane").decode("utf-8")
            for token in tokens:
                _require(token in text, f"{relative} missing final token {token}", errors)


def validate_frozen_s03_p1_dependency(repo_root: Path = REPO_ROOT) -> None:
    errors: list[str] = []
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", builder.PHASE_BASE_COMMIT, "HEAD"],
        cwd=repo_root, capture_output=True, check=False,
    )
    _require(ancestor.returncode == 0, "S03-P1 final commit is not an ancestor", errors)
    for ref in FROZEN_S03_P1_REFS:
        committed = subprocess.run(
            ["git", "show", f"{builder.PHASE_BASE_COMMIT}:{ref}"],
            cwd=repo_root, capture_output=True, check=False,
        )
        path = repo_root / ref
        safe = _regular_single_link(path, errors, label="frozen S03-P1 dependency")
        _require(committed.returncode == 0 and safe, f"frozen S03-P1 dependency missing: {ref}", errors)
        if committed.returncode == 0 and safe:
            _require(committed.stdout == _read_bytes(path, label="frozen dependency"), f"frozen S03-P1 dependency drift: {ref}", errors)
    manifest_ref = next(ref for ref in FROZEN_S03_P1_REFS if ref.endswith("governance_manifest.json"))
    committed = subprocess.run(
        ["git", "show", f"{builder.PHASE_BASE_COMMIT}:{manifest_ref}"],
        cwd=repo_root, capture_output=True, check=False,
    )
    if committed.returncode == 0:
        manifest = json.loads(committed.stdout)
        _require(manifest.get("acceptance_status") == "PASSED", "S03-P1 dependency not PASSED", errors)
        _require(manifest.get("decision") == "CONTINUE_TO_S03_P2_ONLY", "S03-P1 decision drift", errors)
        _require(manifest.get("next_entry_gate", {}).get("s03_p2_entry_allowed") is True, "S03-P1 did not open S03-P2", errors)
        p1_source_count = manifest.get("source_package", {}).get("s03_p1_task_count")
        _require(p1_source_count == 3, "S03-P1 source Task count drift", errors)
    frozen_project = subprocess.run(
        ["git", "show", f"{builder.PHASE_BASE_COMMIT}:KMFA/docs/governance/project.yaml"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    _require(frozen_project.returncode == 0, "frozen S03-P1 project authority missing", errors)
    if frozen_project.returncode == 0:
        source_count = _top_level_yaml_scalar(
            frozen_project.stdout,
            "public_safe_preflight_file_count",
        )
        _require(
            source_count == str(builder.EXPECTED_SOURCE_FILE_COUNT),
            "frozen S03-P1 public source count drift",
            errors,
        )
    if errors:
        raise ValidationError("\n".join(errors))


def run_structured_public_diff_check(
    base_ref: str = builder.PHASE_BASE_COMMIT,
    *,
    repo_root: Path = REPO_ROOT,
) -> None:
    errors: list[str] = []
    _require(base_ref == builder.PHASE_BASE_COMMIT, "diff base must equal frozen S03-P1 final commit", errors)
    check = subprocess.run(
        ["git", "diff", "--check", base_ref, "--", "KMFA"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    _require(check.returncode == 0, "git diff --check failed: " + (check.stdout + check.stderr).strip(), errors)
    changed = subprocess.run(
        ["git", "-c", "core.quotepath=false", "diff", "--name-only", base_ref, "--", "KMFA"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    untracked = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "--others", "--exclude-standard", "--", "KMFA"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    _require(changed.returncode == 0 and untracked.returncode == 0, "changed-path scan failed", errors)
    paths = sorted({line.strip() for line in (changed.stdout + "\n" + untracked.stdout).splitlines() if line.strip()})
    untracked_paths = {line.strip() for line in untracked.stdout.splitlines() if line.strip()}
    for relative in paths:
        _require(relative in ALLOWED_DIFF_PATHS, f"phase diff path outside exact allowlist: {relative}", errors)
        path = repo_root / relative
        if relative in ALLOWED_DIFF_PATHS and _regular_single_link(path, errors, label="phase diff file"):
            payload = _read_bytes(path, label="phase diff file")
            try:
                if path.suffix == ".json":
                    json.loads(payload)
                elif path.suffix == ".jsonl":
                    [json.loads(line) for line in payload.splitlines() if line.strip()]
                elif path.suffix == ".csv":
                    list(csv.DictReader(payload.decode("utf-8").splitlines()))
            except (ValueError, json.JSONDecodeError) as error:
                errors.append(f"structured parse failed for {relative}: {error}")
            if relative in untracked_paths:
                _validate_public_payload(payload, errors, label=relative)
    added = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", base_ref, "--", "KMFA"],
        cwd=repo_root, capture_output=True, check=False,
    )
    _require(added.returncode == 0, "git diff added-line scan failed", errors)
    added_payload = b"\n".join(
        line[1:]
        for line in added.stdout.splitlines()
        if line.startswith(b"+") and not line.startswith(b"+++")
    )
    _validate_public_payload(added_payload, errors, label="S03-P2 added lines")
    local_tracked = subprocess.run(
        ["git", "ls-files", "--", "KMFA/local_runtime"],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    _require(local_tracked.returncode == 0 and not local_tracked.stdout.strip(), "local_runtime leaked into Git", errors)
    if errors:
        raise ValidationError("\n".join(errors))


def _validate_private_freshness(errors: list[str], *, max_age_seconds: float) -> None:
    try:
        private = builder._validate_private_evidence(PROJECT_ROOT)
    except (builder.BuildError, OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))
        return
    now_ns = int(datetime.now().timestamp() * 1_000_000_000)
    for key in ("receipt_mtime_ns", "projection_mtime_ns"):
        age = (now_ns - int(private[key])) / 1_000_000_000
        _require(-300 <= age <= max_age_seconds, f"private evidence freshness drift: {key}", errors)


def _git_changed_paths(
    base: str,
    target: str,
    errors: list[str],
    *,
    label: str,
) -> set[str]:
    result = subprocess.run(
        [
            "git", "-c", "core.quotepath=false", "diff", "--name-only",
            "--diff-filter=ACDMRTUXB", f"{base}..{target}", "--",
        ],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        errors.append(f"unable to resolve {label} changed paths")
        return set()
    return {line for line in result.stdout.splitlines() if line}


def _exact_jsonl_append(
    previous: bytes,
    current: bytes,
    current_rows: Sequence[Mapping[str, Any]],
) -> bool:
    try:
        previous_rows = [
            json.loads(line)
            for line in previous.decode("utf-8").splitlines()
            if line.strip()
        ]
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        current.startswith(previous)
        and len(current_rows) == len(previous_rows) + 1
        and list(current_rows[:-1]) == previous_rows
    )


def _normalize_postvalidation_assurance(text: str) -> str:
    normalized = []
    for line in text.splitlines():
        key = line.split(":", 1)[0] if ":" in line and not line.startswith(" ") else ""
        normalized.append(
            f"{key}: <POST_VALIDATION_BOUND>"
            if key in ASSURANCE_POSTVALIDATION_KEYS else line
        )
    return "\n".join(normalized)


def _validate_postvalidation_governance(
    receipts: Sequence[Mapping[str, Any]],
    *,
    receipt_head: str,
    current_head: str,
    errors: list[str],
) -> None:
    run_ids = {str(row.get("run_id") or "") for row in receipts}
    _require(len(run_ids) == 1, "post-validation governance run_id drift", errors)
    run_id = next(iter(run_ids), "")
    _require(re.fullmatch(r"[0-9a-f]{32}", run_id) is not None, "post-validation governance run_id invalid", errors)
    subjects = {str(row.get("validation_subject_sha256") or "") for row in receipts}
    _require(len(subjects) == 1, "post-validation governance subject drift", errors)
    subject = next(iter(subjects), "")
    _require(
        re.fullmatch(r"sha256:[0-9a-f]{64}", subject) is not None,
        "post-validation governance subject invalid",
        errors,
    )
    jsonl_refs = {
        "event": "KMFA/docs/governance/events.jsonl",
        "development": "KMFA/docs/governance/development_events.jsonl",
        "status": "KMFA/metadata/stage_status.jsonl",
    }
    rows_by_kind: dict[str, list[dict[str, Any]]] = {}
    for kind, ref in jsonl_refs.items():
        path = REPO_ROOT / ref
        if not _regular_single_link(path, errors, label="post-validation governance"):
            continue
        rows_by_kind[kind] = _read_jsonl(path)
        previous = subprocess.run(
            ["git", "show", f"{receipt_head}:{ref}"],
            cwd=REPO_ROOT, capture_output=True, check=False,
        )
        current = _read_bytes(path, label="post-validation governance")
        _require(
            previous.returncode == 0
            and _exact_jsonl_append(previous.stdout, current, rows_by_kind[kind]),
            f"post-validation JSONL must append exactly one final row: {ref}",
            errors,
        )
    expected = {
        "project_id": "KMFA",
        "phase_id": builder.RUN_PHASE_ID,
        "acceptance_id": builder.ACCEPTANCE_ID,
        "final_validation_status": "PASS",
        "phase_acceptance_status": "PASSED",
        "decision": "CONTINUE_TO_S03_P3_ONLY",
        "s03_p3_entry_allowed": True,
        "s03_p3_started": False,
        "product_implementation_allowed": False,
        "github_upload_performed_by_current_run": False,
        "app_reinstall_performed_by_current_run": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "formal_report_generated": False,
        "business_execution_performed": False,
        "irreversible_real_cleanup_performed": False,
        "validation_run_id": run_id,
        "validation_receipt_count": len(builder.EXPECTED_VALIDATION_RECEIPTS),
        "validation_pass_count": len(builder.EXPECTED_VALIDATION_RECEIPTS),
        "validation_failed_count": 0,
        "validation_head": receipt_head,
        "validation_subject_sha256": subject,
        "remediation_id": POSTCOMMIT_REMEDIATION_ID,
        "remediation_status": "CLOSED",
        "committed_head_policy": POSTCOMMIT_HEAD_POLICY,
        "divergent_or_mixed_receipt_head_allowed": False,
        "postvalidation_unbound_path_count": 0,
    }
    for kind, rows in rows_by_kind.items():
        _require(bool(rows), f"post-validation {kind} event missing", errors)
        if not rows:
            continue
        tail = rows[-1]
        for key, value in expected.items():
            _require(tail.get(key) == value, f"post-validation {kind} {key} drift", errors)
    development_rows = rows_by_kind.get("development", [])
    phase_changed = _git_changed_paths(
        builder.PHASE_BASE_COMMIT,
        current_head,
        errors,
        label="phase",
    )
    development_tail = development_rows[-1] if development_rows else {}
    covered = {str(ref) for ref in development_tail.get("files_changed", [])}
    _require(phase_changed == covered, "development event exact changed-file coverage drift", errors)
    assurance_path = REPO_ROOT / "KMFA/docs/governance/ASSURANCE_STATUS.yaml"
    if _regular_single_link(assurance_path, errors, label="post-validation assurance"):
        assurance = _read_bytes(assurance_path, label="post-validation assurance").decode("utf-8")
        previous = subprocess.run(
            ["git", "show", f"{receipt_head}:KMFA/docs/governance/ASSURANCE_STATUS.yaml"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        _require(
            previous.returncode == 0
            and _normalize_postvalidation_assurance(assurance)
            == _normalize_postvalidation_assurance(previous.stdout),
            "ASSURANCE_STATUS changed outside post-validation bound fields",
            errors,
        )
        expected_assurance = {
            "project_id": "KMFA",
            "as_of_event_id": str(development_tail.get("event_id") or ""),
            "source_snapshot_hash": subject,
            "source_base_commit": builder.PHASE_BASE_COMMIT,
            "source_tree_hash": subject,
            "snapshot_event_time": str(development_tail.get("event_time") or ""),
            "generator_version": "manual-1.5.0-dev-s03p2",
            "final_commit_binding": "recorded_by_commit_containing_this_phase_evidence",
            "os_atime_observation_scope": "S03_P2_RAW_ROOT_AND_DIRECT_FILES_EACH_COPY_RUN",
        }
        for key, value in expected_assurance.items():
            _require(
                _top_level_yaml_scalar(assurance, key) == value,
                f"ASSURANCE_STATUS {key} drift",
                errors,
            )
        _require("total_active_parameters: 1484" in assurance, "ASSURANCE_STATUS parameter count drift", errors)
        _require("total_active_formulas: 326" in assurance, "ASSURANCE_STATUS formula count drift", errors)


def _validate_clean_committed(
    manifest: Mapping[str, Any],
    receipts: Sequence[Mapping[str, Any]],
    errors: list[str],
) -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=False,
    )
    _require(status.returncode == 0 and not status.stdout.strip(), "worktree is not clean", errors)
    protected_refs = (
        frozenset(builder.VALIDATION_SUBJECT_REFS)
        | frozenset(builder.ARTIFACT_REFS.values())
        | POST_VALIDATION_GOVERNANCE_REFS
    )
    for ref in sorted(protected_refs):
        committed = subprocess.run(
            ["git", "show", f"HEAD:{ref}"], cwd=REPO_ROOT,
            capture_output=True, check=False,
        )
        path = REPO_ROOT / ref
        if _regular_single_link(path, errors, label="committed artifact"):
            _require(committed.returncode == 0 and committed.stdout == _read_bytes(path, label="committed artifact"), f"HEAD blob drift: {ref}", errors)
    current = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD^{commit}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    current_head = current.stdout.strip()
    _require(
        current.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", current_head) is not None,
        "unable to resolve clean committed HEAD",
        errors,
    )
    receipt_head = _committed_validation_head(receipts, current_head=current_head)
    _require(receipt_head != current_head or all(
        row.get("head_before") == row.get("head_after") == current_head
        for row in receipts
    ), "receipt HEAD is not current or immediate first parent", errors)
    phase_changed = _git_changed_paths(
        builder.PHASE_BASE_COMMIT,
        current_head,
        errors,
        label="phase",
    )
    postvalidation_changed = _git_changed_paths(
        receipt_head,
        current_head,
        errors,
        label="post-validation",
    )
    _require(
        phase_changed <= POSTCOMMIT_ALLOWED_REFS,
        f"phase changed path is not validation-bound: {sorted(phase_changed - POSTCOMMIT_ALLOWED_REFS)}",
        errors,
    )
    _require(
        postvalidation_changed <= POSTCOMMIT_ALLOWED_REFS,
        f"post-validation changed path is not allowed: {sorted(postvalidation_changed - POSTCOMMIT_ALLOWED_REFS)}",
        errors,
    )
    _validate_postvalidation_governance(
        receipts,
        receipt_head=receipt_head,
        current_head=current_head,
        errors=errors,
    )


def _validate_mode_contract(
    *,
    require_validation_receipts: bool,
    require_private_evidence: bool,
    require_dependency_validator: bool,
    require_clean_worktree: bool,
    skip_exact_rebuild: bool,
    pre_receipt_final_governance: bool,
) -> None:
    if require_validation_receipts and pre_receipt_final_governance:
        raise ValidationError("pre-receipt mode cannot require receipts")
    if require_clean_worktree and not (
        require_validation_receipts
        and require_private_evidence
        and require_dependency_validator
        and not skip_exact_rebuild
        and not pre_receipt_final_governance
    ):
        raise ValidationError(
            "clean committed mode requires receipts, private evidence, dependency validator, and exact rebuild"
        )


def validate_v015_s03_p2(
    *,
    require_validation_receipts: bool = False,
    require_private_evidence: bool = False,
    require_dependency_validator: bool = False,
    require_clean_worktree: bool = False,
    skip_exact_rebuild: bool = False,
    pre_receipt_final_governance: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    _validate_mode_contract(
        require_validation_receipts=require_validation_receipts,
        require_private_evidence=require_private_evidence,
        require_dependency_validator=require_dependency_validator,
        require_clean_worktree=require_clean_worktree,
        skip_exact_rebuild=skip_exact_rebuild,
        pre_receipt_final_governance=pre_receipt_final_governance,
    )
    _validate_exact_file_set(errors)
    required = (
        MANIFEST_PATH, TASK_MATRIX_PATH, RUNTIME_PATH, CLEANUP_PATH,
        EVIDENCE_SLOTS_PATH, VALIDATION_RESULTS_PATH,
        DIRECTORY_POLICY_PATH, LIFECYCLE_POLICY_PATH,
    )
    for path in required:
        _regular_single_link(path, errors, label="required artifact")
    if errors:
        raise ValidationError("\n".join(errors))
    manifest = _read_json(MANIFEST_PATH)
    matrix = _read_json(TASK_MATRIX_PATH)
    runtime = _read_json(RUNTIME_PATH)
    cleanup = _read_json(CLEANUP_PATH)
    directory = _read_json(DIRECTORY_POLICY_PATH)
    lifecycle = _read_json(LIFECYCLE_POLICY_PATH)
    slots = _read_jsonl(EVIDENCE_SLOTS_PATH)
    receipts = _read_jsonl(VALIDATION_RESULTS_PATH)
    _validate_manifest(manifest, errors, require_pass=require_validation_receipts)
    _validate_matrix(matrix, errors, require_pass=require_validation_receipts)
    _validate_policies(directory, lifecycle, runtime, cleanup, errors)
    _validate_slots(slots, errors)
    _validate_receipts(
        receipts,
        errors,
        require_pass=require_validation_receipts,
        allow_committed_subject_head=require_clean_worktree,
    )
    _validate_integrity(manifest, errors)
    _validate_governance(
        errors,
        require_final=(require_validation_receipts or pre_receipt_final_governance),
        expected_atime_observed=runtime.get("authorized_io", {}).get(
            "os_atime_side_effect_observed"
        ),
    )
    for ref in builder.ARTIFACT_REFS.values():
        path = REPO_ROOT / ref
        if _regular_single_link(path, errors, label="public artifact"):
            _validate_public_payload(_read_bytes(path, label="public artifact"), errors, label=ref)
    if require_private_evidence:
        _validate_private_freshness(errors, max_age_seconds=7200)
    if require_dependency_validator:
        try:
            validate_frozen_s03_p1_dependency()
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
        except (builder.BuildError, OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"exact rebuild failed: {error}")
    try:
        run_structured_public_diff_check()
    except ValidationError as error:
        errors.append(str(error))
    if require_clean_worktree:
        _validate_clean_committed(manifest, receipts, errors)
    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-validation-receipts", action="store_true")
    parser.add_argument("--require-private-evidence", action="store_true")
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
            print("PASS: S03-P2 structured public diff checks")
            return 0
        if args.private_evidence_only:
            errors: list[str] = []
            _validate_private_freshness(errors, max_age_seconds=args.max_private_evidence_age_seconds)
            if errors:
                raise ValidationError("\n".join(errors))
            print("PASS: S03-P2 private evidence is fresh; no raw access performed")
            return 0
        manifest = validate_v015_s03_p2(
            require_validation_receipts=args.require_validation_receipts and not args.skip_validation_receipts,
            require_private_evidence=args.require_private_evidence,
            require_dependency_validator=args.require_dependency_validator,
            require_clean_worktree=args.require_clean_worktree,
            skip_exact_rebuild=args.skip_exact_rebuild,
            pre_receipt_final_governance=args.pre_receipt_final_governance,
        )
        print(
            "PASS: KMFA v1.5 S03-P2 validated; "
            f"Phase={manifest['acceptance_status']}/{manifest['decision']}; "
            "S03=IN_PROGRESS/PENDING/67%; "
            f"S03-P3 entry={str(manifest['next_entry_gate']['s03_p3_entry_allowed']).lower()} started=false"
        )
        return 0
    except (ValidationError, builder.BuildError, json.JSONDecodeError, OSError, ValueError) as error:
        print("FAIL: KMFA v1.5 S03-P2 validation failed")
        print(error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
