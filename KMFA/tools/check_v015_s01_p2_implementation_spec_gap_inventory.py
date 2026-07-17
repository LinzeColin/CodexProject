#!/usr/bin/env python3
"""Validate KMFA v1.5 S01-P2 implementation/spec gap inventory."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY"
MANIFEST_PATH = ARTIFACT_ROOT / "machine/s01_p2_implementation_spec_gap_inventory_manifest.json"
GAP_PATH = ARTIFACT_ROOT / "machine/implementation_gap_matrix_public_safe.csv"
MIGRATION_PATH = ARTIFACT_ROOT / "machine/migration_decision_matrix_public_safe.csv"
GIT_PLAN_PATH = ARTIFACT_ROOT / "machine/git_recovery_plan_public_safe.json"
ACCEPTANCE_PATH = ARTIFACT_ROOT / "machine/acceptance_matrix_public_safe.json"
METADATA_PATH = REPO_ROOT / "KMFA/metadata/baseline/v015_s01_p2_implementation_spec_gap_inventory.json"
P1_MANIFEST_PATH = REPO_ROOT / "KMFA/stage_artifacts/V015_S01_P1_LEGACY_REFERENCE_BASELINE_FREEZE/machine/s01_p1_legacy_reference_baseline_manifest.json"
SOURCE_PACKAGE = Path("/Users/linzezhang/Downloads/KMFA_ChatGPT_Stage3_Codex_TaskPack_Roadmap_v2_0_UIUX_FULL_REBUILD.zip")
SOURCE_PACKAGE_SHA256 = "e822c98bfe21445b4ddf7110ecf81d14c8fa8bd5f2cdeb00fab4a21e72df39f8"
BASELINE_COMMIT = "d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05"
S01P1_CHECKPOINT = "0e309502f21f12e2deba0931acd3fe1bafd0614c"
LEGACY_BLOB = "5410e829d842f2349c2a6b02042184534bb3b1bf"
LEGACY_TARGET_PATH = "KMFA/stage_artifacts/V014_S11_P1_POST_REMEDIATION_HOME_NAVIGATION/exports/html/kmfa_home_navigation.html"
LEGACY_TARGET_SHA256 = "8b3618a6ba01977ead18e03b07afc4296183ebcf02aa4b2a5e3fd4af29b816b2"
EXPECTED_REQUIREMENT_IDS = {f"R{i:03d}" for i in range(1, 56)}
EXPECTED_CAPABILITY_IDS = {f"CAP-{i:03d}" for i in range(1, 38)}
ALLOWED_GAP_STATUSES = {
    "PARTIAL_VERIFIED",
    "MISSING",
    "UNVERIFIED",
    "DEFERRED",
    "CONFLICTING_POLICY",
}
ALLOWED_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"}
ALLOWED_MIGRATION_DECISIONS = {"KEEP", "REFACTOR", "DEPRECATE", "UNVERIFIED"}
PROTECTED_CAPABILITIES = {f"CAP-{i:03d}" for i in range(1, 12)}
STATIC_OR_CONFLICTING_CAPABILITIES = {f"CAP-{i:03d}" for i in range(25, 30)}
EXPECTED_ACCEPTANCE_CHECK_IDS = {
    "all_55_requirements_present_once",
    "taskpack_priority_and_name_identity_locked",
    "no_requirement_claims_v15_acceptance",
    "every_gap_has_severity_impact_evidence_stage",
    "public_repo_policy_conflict_explicit",
    "four_migration_classes_present",
    "keep_requires_verified_evidence",
    "unverified_never_keep",
    "governance_and_precision_invariants_preserved",
    "static_runtime_and_legacy_ui_not_retained",
    "existing_independent_worktree_reuse_planned",
    "v014_commit_blob_and_archive_recovery_validated",
    "raw_root_stat_unchanged",
    "no_p2_fixes_or_runtime_implementation",
    "no_p3_stage_review_upload_or_reinstall",
    "s01p1_negative_findings_preserved",
}
EXPECTED_RELEASE_STATE_KEYS = {
    "delivery_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
    "formal_report_allowed",
    "github_upload_allowed",
    "app_reinstall_allowed",
}
EXPECTED_ARTIFACT_REFS = {
    "gap_matrix": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/implementation_gap_matrix_public_safe.csv",
    "migration_matrix": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/migration_decision_matrix_public_safe.csv",
    "git_recovery_plan": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/git_recovery_plan_public_safe.json",
    "acceptance_matrix": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/machine/acceptance_matrix_public_safe.json",
    "gap_report": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/human/implementation_gap_report_zh.md",
    "migration_report": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/human/migration_decision_report_zh.md",
    "git_plan_report": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/human/branch_rollback_merge_plan_zh.md",
    "risk_register": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/human/risk_register_zh.md",
    "test_results": "KMFA/stage_artifacts/V015_S01_P2_IMPLEMENTATION_SPEC_GAP_INVENTORY/human/test_results_zh.md",
    "metadata_snapshot": "KMFA/metadata/baseline/v015_s01_p2_implementation_spec_gap_inventory.json",
}
EXPECTED_CURRENT_PHASE_BOUNDARY_KEYS = {
    "fixes_performed",
    "next_phase_started",
    "stage_review_performed",
    "github_upload_performed",
    "app_reinstall_performed",
    "raw_mutation_performed",
}
EXPECTED_MANIFEST_PHASE_GATE_KEYS = {
    "task_execution_complete_count",
    "task_acceptance_passed_count",
    "s01p2_acceptance_passed",
    "stage_01_passed",
    "stage_01_review_performed",
    "next_phase_started",
    "fixes_performed",
    "github_upload_performed",
    "app_reinstall_performed",
    "raw_mutation_performed",
    "next_allowed_run",
}
EXPECTED_TASK_EVIDENCE = {
    "S01P2T01": "machine/implementation_gap_matrix_public_safe.csv",
    "S01P2T02": "machine/migration_decision_matrix_public_safe.csv",
    "S01P2T03": "machine/git_recovery_plan_public_safe.json",
}
SELECTED_COMMAND_FORBIDDEN_FRAGMENTS = (
    "--force",
    "reset --hard",
    "checkout --",
    "clean -fd",
    "clean -fdx",
    "rebase",
    "filter-repo",
    "filter-branch",
    "rm -rf",
    "rsync --delete",
)


class ValidationError(RuntimeError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_content_hash(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("content_hash", None)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _git(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, check=False)


def _git_bytes(args: list[str]) -> bytes:
    result = _git(args)
    if result.returncode != 0:
        raise ValidationError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _git_text(args: list[str]) -> str:
    return _git_bytes(args).decode("utf-8").strip()


def _taskpack_requirements(package: Path) -> dict[str, tuple[str, str]]:
    with zipfile.ZipFile(package) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.rsplit("/", 1)[-1].startswith("04_") and name.lower().endswith(".csv")
        ]
        if len(candidates) != 1:
            raise ValidationError(f"taskpack requirement CSV count mismatch: {len(candidates)}")
        text = archive.read(candidates[0]).decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    return {
        str(row["需求ID"]): (str(row["优先级"]), str(row["需求名称"]))
        for row in rows
    }


def _validate_evidence_refs(rows: list[dict[str, str]], errors: list[str]) -> None:
    repo_root = REPO_ROOT.resolve()
    for row in rows:
        row_id = row.get("requirement_id") or row.get("capability_id") or "unknown"
        refs = [item.strip() for item in row.get("evidence_refs", "").split(";") if item.strip()]
        _require(bool(refs), f"{row_id}: missing evidence refs", errors)
        for ref in refs:
            relative = Path(ref)
            safe_relative = (
                not relative.is_absolute()
                and ".." not in relative.parts
                and relative.parts
                and relative.parts[0] == "KMFA"
            )
            _require(safe_relative, f"{row_id}: evidence ref must be repository-relative {ref}", errors)
            if not safe_relative:
                continue
            resolved = (REPO_ROOT / relative).resolve()
            _require(resolved != repo_root, f"{row_id}: evidence ref cannot be repository root {ref}", errors)
            try:
                resolved.relative_to(repo_root)
            except ValueError:
                _require(False, f"{row_id}: evidence ref escapes repository {ref}", errors)
                continue
            _require(resolved.exists(), f"{row_id}: missing evidence path {ref}", errors)


def validate_v015_s01_p2_implementation_spec_gap_inventory(
    manifest_path: Path = MANIFEST_PATH,
    *,
    gap_path: Path = GAP_PATH,
    migration_path: Path = MIGRATION_PATH,
    git_plan_path: Path = GIT_PLAN_PATH,
    acceptance_path: Path = ACCEPTANCE_PATH,
    metadata_path: Path = METADATA_PATH,
    source_package: Path | None = SOURCE_PACKAGE,
    require_source_package: bool = False,
    require_raw_root: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _read_json(manifest_path)
    acceptance = _read_json(acceptance_path)
    git_plan = _read_json(git_plan_path)
    metadata = _read_json(metadata_path)
    gaps = _read_csv(gap_path)
    migrations = _read_csv(migration_path)

    _require(
        manifest.get("schema_version") == "kmfa.v015.s01_p2_implementation_spec_gap_inventory.v1",
        "manifest schema mismatch",
        errors,
    )
    _require(manifest.get("project_id") == "KMFA", "manifest project mismatch", errors)
    _require(manifest.get("target_release") == "v1.5", "manifest target release mismatch", errors)
    _require(manifest.get("roadmap_phase_id") == "S01-P2", "manifest phase mismatch", errors)
    _require(manifest.get("execution_status") == "EXECUTION_COMPLETE", "execution status mismatch", errors)
    _require(manifest.get("acceptance_status") == "PASSED", "S01-P2 acceptance mismatch", errors)
    _require(manifest.get("decision") == "CONTINUE_TO_S01_P3_ONLY", "next run decision mismatch", errors)
    _require(manifest.get("content_hash") == _canonical_content_hash(manifest), "manifest content hash mismatch", errors)
    source_meta = manifest.get("source_package", {})
    _require(source_meta.get("sha256") == SOURCE_PACKAGE_SHA256, "manifest source package hash mismatch", errors)
    _require(source_meta.get("requirement_count") == 55, "manifest source requirement count mismatch", errors)
    baseline_dependency = manifest.get("baseline_dependency", {})
    _require(baseline_dependency.get("s01p1_manifest_ref") == P1_MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(), "S01P1 manifest ref drift", errors)
    _require(baseline_dependency.get("s01p1_checkpoint_commit") == S01P1_CHECKPOINT, "S01P1 checkpoint dependency drift", errors)
    _require(baseline_dependency.get("v014_public_safe_baseline_commit") == BASELINE_COMMIT, "v0.1.4 baseline dependency drift", errors)
    _require(baseline_dependency.get("s01p1_acceptance_status") == "NOT_PASSED", "S01P1 acceptance must remain NOT_PASSED", errors)
    _require(baseline_dependency.get("s01p1_decision") == "NO_GO", "S01P1 decision must remain NO_GO", errors)
    _require(baseline_dependency.get("negative_findings_preserved") is True, "S01P1 negative findings must be preserved", errors)

    gap_ids = [row.get("requirement_id", "") for row in gaps]
    _require(len(gaps) == 55, "gap row count must be 55", errors)
    _require(len(gap_ids) == len(set(gap_ids)), "duplicate requirement ID", errors)
    _require(set(gap_ids) == EXPECTED_REQUIREMENT_IDS, "requirement ID coverage mismatch", errors)
    for row in gaps:
        rid = row.get("requirement_id", "")
        _require(row.get("priority") in {"P0", "P1", "P2"}, f"{rid}: invalid priority", errors)
        _require(bool(row.get("requirement_name", "").strip()), f"{rid}: missing requirement name", errors)
        _require(row.get("current_status") in ALLOWED_GAP_STATUSES, f"{rid}: invalid current status", errors)
        _require(row.get("current_status") not in {"PASSED", "ACCEPTED", "SATISFIED"}, f"{rid}: false v1.5 acceptance claim", errors)
        _require(bool(row.get("gap_type", "").strip()), f"{rid}: missing gap type", errors)
        _require(row.get("severity") in ALLOWED_SEVERITIES, f"{rid}: invalid severity", errors)
        _require(bool(row.get("impact", "").strip()), f"{rid}: missing impact", errors)
        _require(bool(re.fullmatch(r"S(?:0[1-9]|1[0-9]|2[0-4])", row.get("recommended_stage", ""))), f"{rid}: invalid recommended Stage", errors)
        _require(row.get("migration_hint") in ALLOWED_MIGRATION_DECISIONS, f"{rid}: invalid migration hint", errors)
    _validate_evidence_refs(gaps, errors)
    r007 = next((row for row in gaps if row.get("requirement_id") == "R007"), {})
    _require(r007.get("current_status") == "CONFLICTING_POLICY", "R007 policy conflict must remain explicit", errors)
    _require(r007.get("migration_hint") == "REFACTOR", "R007 must route to REFACTOR", errors)

    migration_ids = [row.get("capability_id", "") for row in migrations]
    _require(len(migrations) == 37, "migration row count must be 37", errors)
    _require(len(migration_ids) == len(set(migration_ids)), "duplicate capability ID", errors)
    _require(set(migration_ids) == EXPECTED_CAPABILITY_IDS, "capability ID coverage mismatch", errors)
    decisions = {row.get("decision", "") for row in migrations}
    _require(decisions == ALLOWED_MIGRATION_DECISIONS, "all four migration classes are required", errors)
    for row in migrations:
        cid = row.get("capability_id", "")
        decision = row.get("decision")
        verification = row.get("verification_status")
        _require(decision in ALLOWED_MIGRATION_DECISIONS, f"{cid}: invalid decision", errors)
        _require(verification in {"VERIFIED", "EVIDENCE_PARTIAL", "NOT_VERIFIED"}, f"{cid}: invalid verification status", errors)
        _require(bool(row.get("rationale", "").strip()), f"{cid}: missing rationale", errors)
        _require(bool(row.get("preservation_constraint", "").strip()), f"{cid}: missing preservation constraint", errors)
        _require(bool(re.fullmatch(r"S(?:0[1-9]|1[0-9]|2[0-4])", row.get("target_stage", ""))), f"{cid}: invalid target Stage", errors)
        if decision == "KEEP":
            _require(verification == "VERIFIED", f"{cid}: KEEP requires VERIFIED", errors)
        if decision == "UNVERIFIED":
            _require(verification == "NOT_VERIFIED", f"{cid}: UNVERIFIED must be NOT_VERIFIED", errors)
    _validate_evidence_refs(migrations, errors)
    migration_by_id = {row.get("capability_id"): row for row in migrations}
    for cid in PROTECTED_CAPABILITIES:
        _require(migration_by_id.get(cid, {}).get("decision") == "KEEP", f"{cid}: protected invariant must be KEEP", errors)
    for cid in STATIC_OR_CONFLICTING_CAPABILITIES:
        _require(migration_by_id.get(cid, {}).get("decision") == "DEPRECATE", f"{cid}: static/conflicting capability must be DEPRECATE", errors)

    _require(git_plan.get("schema_version") == "kmfa.v015.s01_p2_git_recovery_plan.v1", "Git plan schema mismatch", errors)
    _require(git_plan.get("plan_status") == "PLANNED_AND_DRY_RUN_VALIDATED", "Git plan status mismatch", errors)
    repo = git_plan.get("repository", {})
    _require(repo.get("implementation_branch") == "codex/kmfa", "implementation branch mismatch", errors)
    _require(repo.get("s01p1_checkpoint_commit") == S01P1_CHECKPOINT, "S01P1 checkpoint drift", errors)
    _require(repo.get("v014_public_safe_baseline_commit") == BASELINE_COMMIT, "v0.1.4 baseline drift", errors)
    _require(repo.get("v014_legacy_target_path") == LEGACY_TARGET_PATH, "legacy target path drift", errors)
    _require(repo.get("v014_legacy_target_blob_oid") == LEGACY_BLOB, "legacy blob drift", errors)
    _require(repo.get("v014_legacy_target_sha256") == LEGACY_TARGET_SHA256, "legacy target SHA-256 drift", errors)
    _require(repo.get("branch_reuse_decision") == "REUSE_EXISTING_INDEPENDENT_WORKTREE_BRANCH", "worktree reuse decision mismatch", errors)
    for key in ("extra_branch_created", "extra_worktree_created", "baseline_tag_created"):
        _require(repo.get(key) is False, f"unexpected Git mutation: {key}", errors)
    _require(_git(["cat-file", "-e", f"{BASELINE_COMMIT}^{{commit}}"]).returncode == 0, "baseline commit not resolvable", errors)
    _require(_git(["merge-base", "--is-ancestor", BASELINE_COMMIT, "HEAD"]).returncode == 0, "baseline is not HEAD ancestor", errors)
    _require(_git_text(["rev-parse", f"{BASELINE_COMMIT}:{LEGACY_TARGET_PATH}"]) == LEGACY_BLOB, "live legacy blob mismatch", errors)
    _require(hashlib.sha256(_git_bytes(["show", f"{BASELINE_COMMIT}:{LEGACY_TARGET_PATH}"])).hexdigest() == LEGACY_TARGET_SHA256, "live legacy target SHA-256 mismatch", errors)
    recovery = git_plan.get("one_command_code_recovery", {})
    _require(recovery.get("command") == f"git switch --detach {BASELINE_COMMIT}", "recovery command must target the fixed v0.1.4 commit", errors)
    _require(recovery.get("restore_development_command") == "git switch codex/kmfa", "development restore command mismatch", errors)
    _require(recovery.get("guard") == 'test -z "$(git status --porcelain=v1)"', "clean-worktree recovery guard mismatch", errors)
    parallel = git_plan.get("parallel_read_only_recovery_option", {})
    _require(str(parallel.get("command", "")).endswith(f" {BASELINE_COMMIT}"), "parallel recovery must target the fixed v0.1.4 commit", errors)
    dry_run = git_plan.get("dry_run_evidence", {})
    for key in (
        "baseline_commit_resolves",
        "baseline_is_head_ancestor",
        "legacy_blob_matches",
        "streamed_archive_sha256_matches",
        "current_branch_ref_format_valid",
        "optional_tag_ref_format_valid",
        "raw_root_stat_unchanged",
    ):
        expected = "PASS_AFTER_LOCALE_FIXED_TO_C" if key == "streamed_archive_sha256_matches" else "PASS"
        _require(dry_run.get(key) == expected, f"Git dry-run evidence mismatch: {key}", errors)
    selected_commands = [
        recovery.get("command", ""),
        recovery.get("restore_development_command", ""),
        parallel.get("command", ""),
        parallel.get("cleanup_command", ""),
    ]
    for command in selected_commands:
        lowered = str(command).lower()
        for token in SELECTED_COMMAND_FORBIDDEN_FRAGMENTS:
            _require(token not in lowered, f"destructive selected recovery command: {token}", errors)
    final_steps = git_plan.get("final_merge_and_single_upload", [])
    _require(isinstance(final_steps, list) and len(final_steps) == 9, "final merge/upload step count mismatch", errors)
    final_text = "\n".join(str(item) for item in final_steps)
    for required in (
        "git fetch origin main",
        "git merge-tree",
        "git merge --no-ff --no-commit origin/main",
        "git merge --abort",
        "git ls-remote",
        "git push origin HEAD:refs/heads/main",
        "local HEAD、origin/main、GitHub main",
        "App/GitHub/本地治理记录 parity",
    ):
        _require(required in final_text, f"final merge/upload plan missing: {required}", errors)
    for token in SELECTED_COMMAND_FORBIDDEN_FRAGMENTS:
        _require(token not in final_text.lower(), f"destructive final merge/upload plan: {token}", errors)
    boundary = git_plan.get("current_phase_boundaries", {})
    _require(set(boundary) == EXPECTED_CURRENT_PHASE_BOUNDARY_KEYS, "current phase boundary key set mismatch", errors)
    for key in (
        "fixes_performed",
        "next_phase_started",
        "stage_review_performed",
        "github_upload_performed",
        "app_reinstall_performed",
        "raw_mutation_performed",
    ):
        _require(boundary.get(key) is False, f"phase boundary drift: {key}", errors)

    _require(acceptance.get("schema_version") == "kmfa.v015.s01_p2_acceptance_matrix.v1", "acceptance schema mismatch", errors)
    _require(acceptance.get("phase_acceptance_status") == "PASSED", "acceptance status mismatch", errors)
    _require(acceptance.get("quality_gate_passed") is True, "quality gate mismatch", errors)
    checks = acceptance.get("checks", [])
    _require(len(checks) == acceptance.get("check_count") == 16, "acceptance check count mismatch", errors)
    _require(all(item.get("result") == "PASS" for item in checks), "all acceptance checks must PASS", errors)
    check_ids = [str(item.get("check_id")) for item in checks]
    _require(len(check_ids) == len(set(check_ids)), "duplicate acceptance check ID", errors)
    _require(set(check_ids) == EXPECTED_ACCEPTANCE_CHECK_IDS, "acceptance check ID set mismatch", errors)
    _require(all(bool(str(item.get("evidence", "")).strip()) for item in checks), "acceptance check evidence missing", errors)
    _require(acceptance.get("check_pass_count") == 16, "acceptance pass count mismatch", errors)
    _require(acceptance.get("check_fail_count") == 0, "acceptance fail count mismatch", errors)
    _require(acceptance.get("stage_01_passed") is False, "Stage 01 must remain not passed", errors)
    _require(acceptance.get("next_allowed_run") == "S01-P3 only", "acceptance next run mismatch", errors)

    _require(metadata.get("schema_version") == "kmfa.metadata.v015.s01_p2_implementation_spec_gap_inventory.v1", "metadata schema mismatch", errors)
    _require(metadata.get("project_id") == "KMFA", "metadata project mismatch", errors)
    _require(metadata.get("target_release") == "v1.5", "metadata target release mismatch", errors)
    _require(metadata.get("requirement_count") == 55, "metadata requirement count mismatch", errors)
    _require(metadata.get("migration_capability_count") == 37, "metadata migration count mismatch", errors)
    _require(metadata.get("s01p2_acceptance_passed") is True, "metadata phase acceptance mismatch", errors)
    _require(metadata.get("stage_01_passed") is False, "metadata Stage status mismatch", errors)
    _require(metadata.get("s01p1_acceptance_preserved") == "NOT_PASSED", "S01P1 status drift", errors)
    _require(metadata.get("next_allowed_run") == "S01-P3", "metadata next run mismatch", errors)

    gap_counts = manifest.get("requirement_gap_inventory", {})
    _require(gap_counts.get("total") == len(gaps), "manifest gap count mismatch", errors)
    _require(gap_counts.get("accepted_v15_requirement_count") == 0, "manifest false accepted requirement count", errors)
    _require(gap_counts.get("status_counts") == dict(Counter(row["current_status"] for row in gaps)), "manifest gap status counts mismatch", errors)
    _require(gap_counts.get("severity_counts") == dict(Counter(row["severity"] for row in gaps)), "manifest severity counts mismatch", errors)
    _require(gap_counts.get("migration_hint_counts") == dict(Counter(row["migration_hint"] for row in gaps)), "manifest migration hint counts mismatch", errors)
    migration_counts = manifest.get("migration_inventory", {})
    _require(migration_counts.get("total") == len(migrations), "manifest migration count mismatch", errors)
    _require(migration_counts.get("decision_counts") == dict(Counter(row["decision"] for row in migrations)), "manifest migration decision counts mismatch", errors)
    _require(migration_counts.get("keep_verified_count") == sum(row["decision"] == "KEEP" for row in migrations), "manifest KEEP count mismatch", errors)
    _require(migration_counts.get("unverified_keep_count") == 0, "manifest unverified KEEP mismatch", errors)
    outcomes = manifest.get("task_outcomes", [])
    _require(len(outcomes) == 3, "task outcome row count mismatch", errors)
    _require({item.get("task_id") for item in outcomes} == {"S01P2T01", "S01P2T02", "S01P2T03"}, "task outcome IDs mismatch", errors)
    _require(all(item.get("acceptance_status") == "PASSED" for item in outcomes), "task acceptance mismatch", errors)
    for item in outcomes:
        task_id = str(item.get("task_id"))
        evidence = item.get("evidence")
        _require(evidence == EXPECTED_TASK_EVIDENCE.get(task_id), f"task evidence mismatch: {task_id}", errors)
        if evidence:
            _require((ARTIFACT_ROOT / str(evidence)).is_file(), f"task evidence missing: {task_id}", errors)
    phase_gate = manifest.get("phase_gate", {})
    _require(set(phase_gate) == EXPECTED_MANIFEST_PHASE_GATE_KEYS, "manifest phase gate key set mismatch", errors)
    _require(phase_gate.get("task_execution_complete_count") == 3, "phase task execution count mismatch", errors)
    _require(phase_gate.get("task_acceptance_passed_count") == 3, "phase task pass count mismatch", errors)
    _require(phase_gate.get("s01p2_acceptance_passed") is True, "phase acceptance flag mismatch", errors)
    _require(phase_gate.get("stage_01_passed") is False, "manifest Stage 01 must remain false", errors)
    _require(phase_gate.get("next_allowed_run") == "S01-P3", "manifest next run mismatch", errors)
    for key in ("stage_01_review_performed", "next_phase_started", "fixes_performed", "github_upload_performed", "app_reinstall_performed", "raw_mutation_performed"):
        _require(phase_gate.get(key) is False, f"manifest phase boundary drift: {key}", errors)
    release_state = manifest.get("release_state", {})
    _require(set(release_state) == EXPECTED_RELEASE_STATE_KEYS, "release state key set mismatch", errors)
    for key, value in release_state.items():
        _require(value is False, f"release state must remain false: {key}", errors)
    public_safety = manifest.get("public_repo_safety", {})
    expected_public_safety_keys = {
        "raw_file_name_committed",
        "raw_file_hash_committed",
        "raw_business_value_committed",
        "source_document_committed",
        "credential_committed",
        "private_evidence_payload_committed",
    }
    _require(set(public_safety) == expected_public_safety_keys, "public safety key set mismatch", errors)
    for key, value in public_safety.items():
        _require(value is False, f"public safety boundary drift: {key}", errors)
    artifact_refs = manifest.get("artifact_refs", {})
    _require(artifact_refs == EXPECTED_ARTIFACT_REFS, "artifact refs mismatch", errors)
    for label, ref in artifact_refs.items():
        _require((REPO_ROOT / str(ref)).is_file(), f"missing artifact ref {label}: {ref}", errors)

    package_available = source_package is not None and source_package.is_file()
    if require_source_package:
        _require(package_available, "source package required but missing", errors)
    if package_available:
        _require(_sha256_file(source_package) == SOURCE_PACKAGE_SHA256, "source package SHA-256 mismatch", errors)
        taskpack = _taskpack_requirements(source_package)
        _require(set(taskpack) == EXPECTED_REQUIREMENT_IDS, "taskpack requirement coverage mismatch", errors)
        by_id = {row["requirement_id"]: row for row in gaps}
        for rid, (priority, name) in taskpack.items():
            _require(by_id.get(rid, {}).get("priority") == priority, f"{rid}: priority differs from taskpack", errors)
            _require(by_id.get(rid, {}).get("requirement_name") == name, f"{rid}: name differs from taskpack", errors)

    if require_raw_root:
        raw = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
        _require(raw.is_dir(), "raw root missing", errors)
        if raw.is_dir():
            stat_value = raw.stat()
            expected = git_plan.get("dry_run_evidence", {}).get("raw_root_stat", {})
            _require(stat_value.st_dev == expected.get("device"), "raw device drift", errors)
            _require(stat_value.st_ino == expected.get("inode"), "raw inode drift", errors)
            _require(stat_value.st_size == expected.get("size"), "raw size drift", errors)
            _require(int(stat_value.st_mtime) == expected.get("mtime_epoch"), "raw mtime drift", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--gap-matrix", type=Path, default=GAP_PATH)
    parser.add_argument("--migration-matrix", type=Path, default=MIGRATION_PATH)
    parser.add_argument("--git-plan", type=Path, default=GIT_PLAN_PATH)
    parser.add_argument("--acceptance", type=Path, default=ACCEPTANCE_PATH)
    parser.add_argument("--metadata", type=Path, default=METADATA_PATH)
    parser.add_argument("--source-package", type=Path, default=SOURCE_PACKAGE)
    parser.add_argument("--require-source-package", action="store_true")
    parser.add_argument("--require-raw-root", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_v015_s01_p2_implementation_spec_gap_inventory(
            args.manifest,
            gap_path=args.gap_matrix,
            migration_path=args.migration_matrix,
            git_plan_path=args.git_plan,
            acceptance_path=args.acceptance,
            metadata_path=args.metadata,
            source_package=args.source_package,
            require_source_package=args.require_source_package,
            require_raw_root=args.require_raw_root,
        )
    except (OSError, ValueError, ValidationError, zipfile.BadZipFile) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS",
        "phase": result["roadmap_phase_id"],
        "acceptance_status": result["acceptance_status"],
        "stage_01_passed": result["phase_gate"]["stage_01_passed"],
        "next_allowed_run": result["phase_gate"]["next_allowed_run"],
        "requirement_count": result["requirement_gap_inventory"]["total"],
        "migration_capability_count": result["migration_inventory"]["total"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
