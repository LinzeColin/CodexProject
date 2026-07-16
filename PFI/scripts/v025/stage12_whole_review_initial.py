#!/usr/bin/env python3
"""Run the independent initial Stage 12 review without remediation or acceptance."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Sequence
import zipfile

from jsonschema import Draft202012Validator


PFI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PFI_ROOT.parent
SRC_ROOT = PFI_ROOT / "src"
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
for candidate in (SRC_ROOT, SCRIPTS_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from immutable_real_sources import load_locked_source_objects  # noqa: E402
from pfi_v02.stage_v021_runtime_api import (  # noqa: E402
    _v025_frontend_bundle_hash,
    build_v025_release_asset_identity,
)
from target_mac_uat import CANONICAL_APP, _app_identity  # noqa: E402


VERSION = "v0.2.5"
STAGE = 12
PHASE = "stage12-whole-review-initial"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE12-WHOLE-REVIEW-INITIAL"
CANDIDATE_COMMIT = "9a7245acf984a4eb98f93c4aab7bb4d02095294f"
ORIGIN_MAIN_AT_REVIEW_START = "5ff1f3c5ce49d0bb5466125333b873082d2ddd58"
ROADMAP_SHA256 = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
TASKPACK_SHA256 = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
ROADMAP = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md"
TASKPACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/whole_stage_review"
FINAL_ACCEPTANCE = REVIEW_DIR / "human_acceptance.json"
PHASES = (
    (
        "12.1",
        "phase_12_1",
        "7ce65beead6f1c39c0819ea77ecfdecd950679e8",
        ("S12-P1-T1", "S12-P1-T2", "S12-P1-T3", "S12-P1-T4"),
    ),
    (
        "12.2",
        "phase_12_2",
        "78375ec98fc1265abd03ef10087cc05beccab8b4",
        ("S12-P2-T1", "S12-P2-T2", "S12-P2-T3", "S12-P2-T4"),
    ),
    (
        "12.3",
        "phase_12_3",
        CANDIDATE_COMMIT,
        ("S12-P3-T1", "S12-P3-T2", "S12-P3-T3", "S12-P3-T4"),
    ),
)
PRIVATE_PATTERNS = {
    "absolute_private_paths": re.compile(r"/(?:Users|private/var/folders|var/folders)/"),
    "financial_values": re.compile(r"\bCNY\s+-?[0-9]"),
    "raw_source_filenames": re.compile(r"alipay_20\d{6}-20\d{6}"),
    "email_addresses": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "private_key_headers": re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path.name}")
    return payload


def _git_bytes(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or "git command failed")
    return completed.stdout


def _git_text(*args: str) -> str:
    return _git_bytes(*args).decode("utf-8", errors="strict").strip()


def _git_blob(commit: str, relative: str) -> bytes:
    return _git_bytes("show", f"{commit}:{relative}")


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def _candidate_json(relative: str) -> dict[str, Any]:
    payload = json.loads(_git_blob(CANDIDATE_COMMIT, relative))
    if not isinstance(payload, dict):
        raise RuntimeError(f"candidate artifact is not an object: {relative}")
    return payload


def _taskpack_schema(name: str) -> dict[str, Any]:
    with zipfile.ZipFile(TASKPACK) as archive:
        payload = json.loads(
            archive.read(f"PFI_v0.2.5_TaskPack/schemas/{name}").decode("utf-8")
        )
    if not isinstance(payload, dict):
        raise RuntimeError(f"TaskPack schema is invalid: {name}")
    return payload


def _taskpack_binding() -> dict[str, object]:
    roadmap_hash = _sha(ROADMAP)
    taskpack_hash = _sha(TASKPACK)
    status = (
        "pass"
        if roadmap_hash == f"sha256:{ROADMAP_SHA256}"
        and taskpack_hash == f"sha256:{TASKPACK_SHA256}"
        else "fail"
    )
    if status != "pass":
        raise RuntimeError("Roadmap or TaskPack hash drifted")
    return {
        "schema": "PFIV025Stage12InitialReviewTaskpackBindingV1",
        "status": status,
        "roadmap_sha256": roadmap_hash,
        "taskpack_sha256": taskpack_hash,
        "stage": STAGE,
        "acceptance_id": ACCEPTANCE_ID,
    }


def _phase_commit_binding() -> dict[str, object]:
    evidence_validator = Draft202012Validator(_taskpack_schema("evidence_pack.schema.json"))
    phase_rows: list[dict[str, object]] = []
    total_files = 0
    for phase, directory, commit, task_ids in PHASES:
        root = f"PFI/reports/pfi_v025/stage_12/{directory}"
        evidence_path = f"{root}/evidence.json"
        manifest_path = f"{root}/artifact_manifest.json"
        evidence = json.loads(_git_blob(commit, evidence_path))
        manifest = json.loads(_git_blob(commit, manifest_path))
        schema_errors = [error.message for error in evidence_validator.iter_errors(evidence)]
        files: list[dict[str, object]] = []
        for relative, expected in sorted(manifest["files"].items()):
            payload = _git_blob(commit, relative)
            actual = _sha_bytes(payload)
            files.append(
                {
                    "path": relative,
                    "expected_sha256": expected,
                    "actual_sha256": actual,
                    "match": actual == expected,
                }
            )
        total_files += len(files)
        row_pass = (
            manifest.get("status") == "pass"
            and manifest.get("file_count") == len(files)
            and all(item["match"] for item in files)
            and not schema_errors
            and evidence.get("status") == "candidate_pass"
            and tuple(evidence.get("task_ids", ())) == task_ids
            and evidence.get("git_commit") == "SELF"
        )
        phase_rows.append(
            {
                "phase": phase,
                "commit": commit,
                "artifact_file_count": len(files),
                "artifact_match_count": sum(bool(item["match"]) for item in files),
                "all_artifacts_match": all(item["match"] for item in files),
                "evidence_schema_error_count": len(schema_errors),
                "task_ids_exact": tuple(evidence.get("task_ids", ())) == task_ids,
                "candidate_status": evidence.get("status"),
                "status": "pass" if row_pass else "fail",
                "files": files,
            }
        )
    chain = all(
        _is_ancestor(PHASES[index][2], PHASES[index + 1][2])
        for index in range(len(PHASES) - 1)
    )
    status = "pass" if chain and all(row["status"] == "pass" for row in phase_rows) else "fail"
    if status != "pass":
        raise RuntimeError("Stage 12 phase commit binding failed")
    return {
        "schema": "PFIV025Stage12InitialReviewPhaseCommitBindingV1",
        "status": status,
        "candidate_commit": CANDIDATE_COMMIT,
        "phase_chain_linear": chain,
        "phase_count": len(phase_rows),
        "artifact_file_count": total_files,
        "phases": phase_rows,
    }


def _final_index_audit() -> dict[str, object]:
    root = "PFI/reports/pfi_v025/stage_12/phase_12_3"
    index_path = f"{root}/final_evidence_index.json"
    index_blob = _git_blob(CANDIDATE_COMMIT, index_path)
    index = json.loads(index_blob)
    request = _candidate_json(f"{root}/human_acceptance_request.json")
    state = _candidate_json(f"{root}/state_consistency.json")
    detached = _git_blob(CANDIDATE_COMMIT, f"{root}/final_evidence_index.sha256").decode("utf-8")
    index_hash = _sha_bytes(index_blob)
    file_rows = []
    for row in index["files"]:
        actual = _sha_bytes(_git_blob(CANDIDATE_COMMIT, row["path"]))
        file_rows.append(
            {
                "path": row["path"],
                "expected_sha256": row["sha256"],
                "actual_sha256": actual,
                "match": actual == row["sha256"],
            }
        )
    detached_matches = detached == (
        f"{index_hash.removeprefix('sha256:')}  final_evidence_index.json\n"
    )
    request_hash_matches = request.get("evidence_index_hash") == index_hash
    request_commit_exact = request.get("git_commit") == CANDIDATE_COMMIT
    state_head_exact = state.get("git", {}).get("head") == CANDIDATE_COMMIT
    state_ahead_exact = state.get("git", {}).get("ahead") == 118
    immutable_hashes_pass = (
        all(row["match"] for row in file_rows)
        and detached_matches
        and request_hash_matches
    )
    if not immutable_hashes_pass:
        raise RuntimeError("Phase 12.3 final evidence index hash validation failed")
    return {
        "schema": "PFIV025Stage12InitialReviewFinalIndexAuditV1",
        "status": "fail_exact_candidate_binding_required",
        "candidate_commit": CANDIDATE_COMMIT,
        "index_sha256": index_hash,
        "index_file_count": len(file_rows),
        "index_match_count": sum(bool(row["match"]) for row in file_rows),
        "all_index_files_match_at_candidate": all(row["match"] for row in file_rows),
        "detached_hash_matches": detached_matches,
        "acceptance_request_hash_matches": request_hash_matches,
        "acceptance_request_git_commit": request.get("git_commit"),
        "acceptance_request_commit_exact": request_commit_exact,
        "state_observed_head": state.get("git", {}).get("head"),
        "state_head_exact": state_head_exact,
        "state_observed_ahead": state.get("git", {}).get("ahead"),
        "state_ahead_exact": state_ahead_exact,
        "final_human_acceptance": False,
        "human_acceptance_artifact_exists": FINAL_ACCEPTANCE.exists(),
    }


def _release_identity_audit() -> dict[str, object]:
    manifest = _candidate_json("PFI/config/release_manifest.json")
    disk = build_v025_release_asset_identity(PFI_ROOT, manifest=manifest)
    _, frontend_files = _v025_frontend_bundle_hash(PFI_ROOT)
    runtime_files = sorted(
        set(frontend_files)
        | set(str(path) for path in disk["backend_files"])
        | {"PFI/config/release_manifest.json"}
    )
    manifest_commit = str(manifest["git_commit"])
    changed_runtime_files = _git_text(
        "diff",
        "--name-only",
        f"{manifest_commit}..{CANDIDATE_COMMIT}",
        "--",
        *runtime_files,
    ).splitlines()
    latest_runtime_commit = _git_text(
        "log",
        "-1",
        "--format=%H",
        CANDIDATE_COMMIT,
        "--",
        *runtime_files,
    )
    installed = _app_identity(CANONICAL_APP)
    receipt = _candidate_json(
        "PFI/reports/pfi_v025/stage_12/phase_12_2/app_installation.json"
    )
    installed_matches_receipt = (
        installed.get("kind") == "app_bundle"
        and installed.get("short_version") == manifest.get("app_short_version")
        and installed.get("build_version") == manifest.get("app_build_version")
        and installed.get("bundle_tree_sha256")
        == receipt.get("after", {}).get("bundle_tree_sha256")
        and installed.get("executable_sha256")
        == receipt.get("after", {}).get("executable_sha256")
        and installed.get("codesign_valid") is True
        and installed.get("project_binding_matches") is True
    )
    source_commit_exact = not changed_runtime_files
    return {
        "schema": "PFIV025Stage12InitialReviewReleaseIdentityAuditV1",
        "status": "fail_manifest_commit_precedes_runtime_changes",
        "candidate_commit": CANDIDATE_COMMIT,
        "manifest_git_commit": manifest_commit,
        "manifest_commit_is_ancestor": _is_ancestor(manifest_commit, CANDIDATE_COMMIT),
        "manifest_commit_exact_for_runtime_files": source_commit_exact,
        "runtime_bound_file_count": len(runtime_files),
        "runtime_files_changed_after_manifest_commit_count": len(changed_runtime_files),
        "runtime_files_changed_after_manifest_commit": changed_runtime_files,
        "latest_runtime_change_commit": latest_runtime_commit,
        "frontend_hash_matches_manifest": disk["frontend_valid"],
        "disk_backend_hash_matches_manifest": disk["disk_backend_valid"],
        "running_backend_hash_matches_manifest": disk["running_backend_valid"],
        "asset_hash_identity_valid": disk["valid"],
        "installed_app_matches_phase122_receipt": installed_matches_receipt,
        "installed_app_short_version": installed.get("short_version"),
        "installed_app_build_version": installed.get("build_version"),
        "installed_app_codesign_valid": installed.get("codesign_valid"),
        "installed_app_project_binding_matches": installed.get("project_binding_matches"),
        "contains_private_values": False,
        "finder_used": False,
    }


def _entry_audit() -> dict[str, object]:
    census = _candidate_json(
        "PFI/reports/pfi_v025/stage_12/phase_12_2/entry_census.json"
    )
    mismatch_count = int(census.get("noncanonical_copy_mismatch_count", -1))
    downloads = census.get("entries", {}).get("downloads", {})
    return {
        "schema": "PFIV025Stage12InitialReviewEntryAuditV1",
        "status": "fail_noncanonical_old_app_remains" if mismatch_count else "pass",
        "canonical_app_version": census.get("entries", {}).get("applications", {}).get(
            "short_version"
        ),
        "desktop_targets_canonical": census.get("entries", {}).get("desktop", {}).get(
            "targets_canonical"
        ),
        "noncanonical_copy_mismatch_count": mismatch_count,
        "noncanonical_copy_version": downloads.get("short_version"),
        "noncanonical_copy_build": downloads.get("build_version"),
        "noncanonical_copies_modified": census.get("noncanonical_copies_modified"),
        "finder_used": False,
        "launchservices_used": False,
        "remediation_must_remain_cli_only": True,
    }


def _ephemeral_real_e2e() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage12-initial-review-") as temp_name:
        output = Path(temp_name) / "real-e2e"
        command = [
            sys.executable,
            "-B",
            "PFI/web/tests/v025/stage12_real_e2e_browser.py",
            "--output-dir",
            str(output),
        ]
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "PFI/src"},
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        if completed.returncode:
            raise RuntimeError("fresh headless real E2E recheck failed")
        e2e = _read_json(output / "real_data_e2e.json")
        browser = _read_json(output / "browser_validation.json")
        database = _read_json(output / "database_before_after.json")
        trace = output / "browser_trace_sanitized.zip"
        screenshots = sorted(output.glob("*.png"))
        status = (
            "pass"
            if e2e.get("status") == browser.get("status") == database.get("status") == "pass"
            and trace.is_file()
            and len(screenshots) == 3
            else "fail"
        )
        if status != "pass":
            raise RuntimeError("fresh headless E2E artifacts are incomplete")
        return {
            "schema": "PFIV025Stage12InitialReviewFreshRealE2EV1",
            "status": status,
            "candidate_commit": CANDIDATE_COMMIT,
            "source_blob_count": e2e["source"]["source_blob_count"],
            "source_object_set_hash": e2e["source"]["source_object_set_hash"],
            "transaction_count": e2e["import"]["transaction_count"],
            "ledger_count": e2e["import"]["confirmed_ledger_count"],
            "review_count": e2e["import"]["review_count"],
            "replay_idempotent": e2e["import"]["replay_idempotent"],
            "holding_execution_status": e2e["holding"]["execution_status"],
            "holding_truth_gate_status": e2e["holding"]["truth_gate_status"],
            "holding_financial_pass_claimed": e2e["holding"]["financial_pass_claimed"],
            "blocked_report_count": e2e["report"]["blocked_report_count"],
            "partial_report_count": e2e["report"]["partial_report_count"],
            "browser_check_count": browser["check_count"],
            "browser_passed_check_count": browser["passed_check_count"],
            "screenshot_count": len(screenshots),
            "trace_sha256": _sha(trace),
            "database_integrity": database["after"]["integrity_check"],
            "database_foreign_key_issue_count": database["after"]["foreign_key_issue_count"],
            "canonical_database_read": e2e["canonical_database_read"],
            "canonical_database_changed": e2e["canonical_database_changed"],
            "external_network_performed": e2e["external_network_performed"],
            "contains_private_values": e2e["contains_private_values"],
            "temporary_artifacts_retained": False,
            "finder_used": False,
        }


def _requirement_matrix(
    *,
    release: dict[str, object],
    index: dict[str, object],
    entry: dict[str, object],
    fresh: dict[str, object],
) -> dict[str, object]:
    phase121_quality = _candidate_json(
        "PFI/reports/pfi_v025/stage_12/phase_12_1/quality_evidence.json"
    )
    phase122_lifecycle = _candidate_json(
        "PFI/reports/pfi_v025/stage_12/phase_12_2/target_mac_lifecycle.json"
    )
    phase122_backup = _candidate_json(
        "PFI/reports/pfi_v025/stage_12/phase_12_2/backup_restore_result.json"
    )
    phase122_disk = _candidate_json(
        "PFI/reports/pfi_v025/stage_12/phase_12_2/disk_pressure_result.json"
    )
    rows = [
        {
            "requirement_id": "S12-ACC-01-RELEASE-IDENTITY",
            "status": "fail_remediation_required",
            "result": "asset hashes and installed App match, but manifest git_commit predates runtime-bound changes",
            "evidence_ref": "release_identity_audit.json",
        },
        {
            "requirement_id": "S12-ACC-02-REAL-IMPORT-REVIEW",
            "status": "pass",
            "result": f"fresh headless recheck imported {fresh['transaction_count']} real transactions idempotently",
            "evidence_ref": "fresh_real_e2e.json",
        },
        {
            "requirement_id": "S12-ACC-03-HOLDING-TRUTH",
            "status": "pass_with_known_limitation",
            "result": "SRC-HOLDINGS remains not_loaded/not_run; no fixture, false zero or financial pass",
            "evidence_ref": "fresh_real_e2e.json",
        },
        {
            "requirement_id": "S12-ACC-04-REPORT-TRUTH",
            "status": "pass",
            "result": "available reports remain truthful partial/blocked states without private values",
            "evidence_ref": "fresh_real_e2e.json",
        },
        {
            "requirement_id": "S12-ACC-05-ROUTES-UX-QUALITY",
            "status": "pass_with_truthful_substitute",
            "result": "20-route WCAG/CDP AX/keyboard/visual suite passed; axe-core remains explicitly not claimed",
            "evidence_ref": "PFI/reports/pfi_v025/stage_12/phase_12_1/quality_evidence.json",
            "axe_pass_claimed": phase121_quality["axe_pass_claimed"],
        },
        {
            "requirement_id": "S12-ACC-06-TARGET-MAC-LIFECYCLE",
            "status": "pass_with_known_limitation",
            "result": "start/stop/restart/repeated-start/offline recovery pass; kernel sleep/wake remains an explicit proxy-only limitation",
            "evidence_ref": "PFI/reports/pfi_v025/stage_12/phase_12_2/target_mac_lifecycle.json",
            "actual_os_sleep_performed": phase122_lifecycle["suspend_resume"]["actual_os_sleep_performed"],
        },
        {
            "requirement_id": "S12-ACC-07-BACKUP-DISK-RECOVERY",
            "status": "pass",
            "result": "canonical read-only backup plus isolated restore/rollback and real SQLITE_FULL recovery passed",
            "evidence_ref": "PFI/reports/pfi_v025/stage_12/phase_12_2/backup_restore_result.json",
            "canonical_private_database_mutated": phase122_backup["canonical_private_database_mutated"],
            "sqlite_full_observed": phase122_disk["sqlite_full_observed"],
        },
        {
            "requirement_id": "S12-ACC-08-ENTRY-SURFACES",
            "status": "fail_remediation_required",
            "result": "canonical App is current, but one old noncanonical Downloads App remains",
            "evidence_ref": "entry_audit.json",
            "finder_method_overridden_by_latest_user_instruction": True,
        },
        {
            "requirement_id": "S12-ACC-09-STATE-AND-EVIDENCE",
            "status": "fail_remediation_required",
            "result": "all indexed bytes match, but the pending request uses SELF and the state snapshot records the pre-candidate HEAD",
            "evidence_ref": "final_index_audit.json",
        },
        {
            "requirement_id": "S12-ACC-10-FINAL-HUMAN-ACCEPTANCE",
            "status": "pending_after_rereview",
            "result": "no final acceptance artifact exists; explicit exact-release acceptance remains reserved",
            "evidence_ref": "final_index_audit.json",
        },
    ]
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    return {
        "schema": "PFIV025Stage12InitialReviewRequirementMatrixV1",
        "status": "remediation_required",
        "candidate_commit": CANDIDATE_COMMIT,
        "requirement_count": len(rows),
        "status_counts": status_counts,
        "requirements": rows,
        "release_hash_identity_valid": release["asset_hash_identity_valid"],
        "index_bytes_valid": index["all_index_files_match_at_candidate"],
        "entry_mismatch_count": entry["noncanonical_copy_mismatch_count"],
    }


def _initial_findings(
    *,
    release: dict[str, object],
    index: dict[str, object],
    entry: dict[str, object],
) -> dict[str, object]:
    findings = [
        {
            "finding_id": "S12-WR-I01-RELEASE-COMMIT-DRIFT",
            "severity": "P1",
            "classification": "important",
            "release_blocking": True,
            "status": "open_for_remediation",
            "result": (
                f"release_manifest git_commit {str(release['manifest_git_commit'])[:10]} predates "
                f"{release['runtime_files_changed_after_manifest_commit_count']} runtime-bound file changes"
            ),
            "evidence_ref": "release_identity_audit.json",
            "remediation": "define and bind a post-review product-source commit, regenerate manifest/frontend/backend identity, and prove no runtime-bound drift after that source anchor",
        },
        {
            "finding_id": "S12-WR-I02-EXACT-ACCEPTANCE-BINDING",
            "severity": "P1",
            "classification": "important",
            "release_blocking": True,
            "status": "open_for_remediation",
            "result": (
                f"acceptance request commit={index['acceptance_request_git_commit']}; "
                f"state head={str(index['state_observed_head'])[:10]}; candidate={CANDIDATE_COMMIT[:10]}"
            ),
            "evidence_ref": "final_index_audit.json",
            "remediation": "regenerate the candidate state/index/request after review remediation with an explicit immutable candidate/source-commit model and no stale precommit snapshot",
        },
        {
            "finding_id": "S12-WR-I03-NONCANONICAL-OLD-APP",
            "severity": "P1",
            "classification": "important",
            "release_blocking": True,
            "status": "open_for_remediation",
            "result": (
                f"CLI census still finds one noncanonical App at version {entry['noncanonical_copy_version']} "
                f"build {entry['noncanonical_copy_build']}"
            ),
            "evidence_ref": "entry_audit.json",
            "remediation": "quarantine or remove the old noncanonical bundle using CLI only, then rerun the entry census without Finder or LaunchServices",
        },
    ]
    residual_risks = [
        {
            "risk_id": "S12-WR-R01-ACTUAL-SLEEP-WAKE-NOT-RUN",
            "severity": "P2",
            "disposition": "bind as a known limitation unless a later safe CLI-only target-Mac rehearsal is explicitly chosen",
        },
        {
            "risk_id": "S12-WR-R02-HOLDINGS-SOURCE-NOT-LOADED",
            "severity": "P2",
            "disposition": "retain truthful not_loaded/not_run and no-false-zero behavior; no data may be invented",
        },
        {
            "risk_id": "S12-WR-R03-FINDER-METHOD-OVERRIDDEN",
            "severity": "P2",
            "disposition": "latest user instruction prohibits Finder/GUI; retain CLI bundle and headless-browser evidence",
        },
        {
            "risk_id": "S12-WR-R04-AXE-CORE-NOT-AVAILABLE",
            "severity": "P2",
            "disposition": "retain explicit no-axe claim and deterministic WCAG 2.2 AA/CDP AX substitute",
        },
        {
            "risk_id": "S12-WR-R05-HISTORICAL-STATE-TEST-DEBT",
            "severity": "P2",
            "count": 6,
            "disposition": "retain current-state replacement gates without rewriting immutable historical evidence",
        },
    ]
    return {
        "schema": "PFIV025Stage12InitialReviewFindingsV1",
        "status": "remediation_required",
        "candidate_commit": CANDIDATE_COMMIT,
        "review_execution_truth": "one local deterministic review runner evaluated three independent lenses; no external human, subagent, Finder operation or GUI reviewer is claimed",
        "review_lenses": [
            {
                "lens_id": "release_identity_and_entry_truth",
                "finding_ids": ["S12-WR-I01-RELEASE-COMMIT-DRIFT", "S12-WR-I03-NONCANONICAL-OLD-APP"],
            },
            {
                "lens_id": "evidence_and_acceptance_binding",
                "finding_ids": ["S12-WR-I02-EXACT-ACCEPTANCE-BINDING"],
            },
            {
                "lens_id": "real_workflow_quality_and_resilience",
                "finding_ids": [],
                "result": "technical gates pass with five explicit P2 residual risks",
            },
        ],
        "counts": {"critical": 0, "important": 3, "minor": 0},
        "open_p0_count": 0,
        "open_p1_count": 3,
        "findings": findings,
        "residual_risks": residual_risks,
        "rereview_status": "not_started",
        "final_human_acceptance": False,
        "production_accepted": False,
    }


def _sanitize(value: str) -> str:
    return value.replace(str(Path.home()), "$HOME").replace(sys.executable, "$PYTHON")


def _run_group(command_id: str, commands: Sequence[Sequence[str]]) -> dict[str, object]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "PFI/src"}
    chunks: list[str] = []
    exact_commands: list[str] = []
    exit_code = 0
    for command in commands:
        exact = _sanitize(shlex.join(command))
        exact_commands.append(exact)
        completed = subprocess.run(
            list(command),
            cwd=REPO_ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=900,
        )
        chunks.append(f"$ {exact}\n{_sanitize(completed.stdout)}")
        if completed.returncode:
            exit_code = completed.returncode
            break
    output = "\n".join(chunks).rstrip() + "\n"
    log = REVIEW_DIR / f"verification_{command_id}.log"
    log.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "exit_code": exit_code,
        "summary": "pass" if exit_code == 0 else "fail",
        "output_ref": log.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": _sha(log),
    }


def _verification() -> list[dict[str, object]]:
    python = str(sys.executable)
    stage12 = (
        "PFI/tests/test_v025_stage1_release_identity.py",
        "PFI/tests/test_v025_stage1_cache_policy.py",
        "PFI/tests/test_v025_stage12_release_gates.py",
        "PFI/tests/test_v025_stage12_target_mac_uat.py",
        "PFI/tests/test_v025_stage12_release_freeze.py",
    )
    adjacent = (
        "PFI/tests/test_v025_stage4_cross_page_consistency.py",
        "PFI/tests/test_v025_stage4_metric_states.py",
        "PFI/tests/test_v025_stage5_dual_consumption.py",
        "PFI/tests/test_v025_stage5_financial_invariants.py",
        "PFI/tests/test_v025_stage6_navigation_contract.py",
        "PFI/tests/test_v025_stage7_import_review_ledger.py",
        "PFI/tests/test_v025_stage7_holding_persistence.py",
        "PFI/tests/test_v025_stage8_phase83_accessibility_uat.py",
        "PFI/tests/test_v025_stage9_whole_review.py",
        "PFI/tests/test_v025_stage10_runtime_diff.py",
        "PFI/tests/test_v025_stage10_crash_recovery.py",
        "PFI/tests/test_v025_stage11_backup_restore.py",
        "PFI/tests/test_v025_stage11_distribution_boundary.py",
    )
    rows = [
        _run_group(
            "focused_stage12",
            ((python, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *stage12),),
        ),
        _run_group(
            "selected_adjacent_regression",
            ((python, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *adjacent),),
        ),
        _run_group(
            "node_cache_policy",
            (("node", "--test", "PFI/web/tests/v025/stage1_cache_policy.test.mjs"),),
        ),
        _run_group(
            "release_and_dual_plane",
            (
                (python, "-B", "PFI/scripts/v025/release_cache_contract.py", "--project-root", "PFI", "--isolated-candidate", "--policy-json"),
                (python, "-B", "PFI/machine/tools/check_dual_plane_ci.py", "--root", "PFI", "--projects", ".", "--require-projects"),
                (python, "-B", "scripts/lean_governance.py", "check-render", "--project", "PFI"),
                ("git", "diff", "--check"),
            ),
        ),
    ]
    from build_stage11_phase111_evidence import _complete_overlay_governance

    for index, row in enumerate(_complete_overlay_governance(), start=1):
        rows.append(
            {
                "command_id": f"complete_overlay_governance_{index}",
                "command": row["command"],
                "exit_code": row["exit_code"],
                "summary": row["summary"],
            }
        )
    if any(int(row["exit_code"]) != 0 for row in rows):
        raise RuntimeError("initial review verification command failed")
    return rows


def _changed_files() -> list[str]:
    tracked = _git_text("diff", "HEAD", "--name-only").splitlines()
    untracked = _git_text("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked + untracked))


def _privacy_scan() -> dict[str, object]:
    counts = {name: 0 for name in PRIVATE_PATTERNS}
    input_count = 0
    for path in sorted(REVIEW_DIR.rglob("*")):
        if not path.is_file() or path.name in {"privacy_scan.txt", "artifact_manifest.json"}:
            continue
        if path.suffix.lower() not in {".json", ".txt", ".md", ".log", ".sha256"}:
            continue
        text = path.read_text(encoding="utf-8")
        input_count += 1
        for name, pattern in PRIVATE_PATTERNS.items():
            counts[name] += len(pattern.findall(text))
    status = "pass" if not any(counts.values()) else "fail"
    (REVIEW_DIR / "privacy_scan.txt").write_text(
        "\n".join(
            [
                "PASS" if status == "pass" else "FAIL",
                "scanner=pfi-v025-stage12-initial-whole-review-public-evidence-v1",
                f"input_count={input_count}",
                *(f"{name}={count}" for name, count in counts.items()),
                "contains_private_values=false",
                "finder_operations=0",
                "launchservices_operations=0",
                "gui_file_operations=0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if status != "pass":
        raise RuntimeError(f"initial whole-review privacy scan failed: {counts}")
    return {"status": status, "input_count": input_count, "counts": counts}


def run() -> dict[str, object]:
    head = _git_text("rev-parse", "HEAD")
    origin_main = _git_text("rev-parse", "origin/main")
    if head != CANDIDATE_COMMIT:
        raise RuntimeError("initial review must run on the exact Phase 12.3 candidate commit")
    if origin_main != ORIGIN_MAIN_AT_REVIEW_START:
        raise RuntimeError("origin/main moved before the Stage 12 initial review")
    if FINAL_ACCEPTANCE.exists():
        raise RuntimeError("final human acceptance must not exist during initial review")

    if REVIEW_DIR.exists():
        shutil.rmtree(REVIEW_DIR)
    REVIEW_DIR.mkdir(parents=True)
    observed_at = _now()
    contract = {
        "schema": "PFIV025Stage12InitialWholeReviewContractV1",
        "status": "in_progress",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "acceptance_id": ACCEPTANCE_ID,
        "candidate_commit": CANDIDATE_COMMIT,
        "origin_main": origin_main,
        "review_scope": "Stage 12.1 through 12.3 candidate, release identity, real workflow, target-Mac CLI evidence, governance and final binding",
        "non_goals": [
            "finding remediation",
            "rereview",
            "final human acceptance",
            "release freeze",
            "GitHub push",
            "canonical App reinstall",
            "v0.2.6 work",
        ],
        "finder_prohibited": True,
        "gui_file_operations_prohibited": True,
        "observed_at": observed_at,
    }
    _write_json(REVIEW_DIR / "phase_contract.json", contract)
    taskpack = _taskpack_binding()
    phase_binding = _phase_commit_binding()
    index = _final_index_audit()
    release = _release_identity_audit()
    entry = _entry_audit()
    source_objects, source_attestation = load_locked_source_objects(repo_root=REPO_ROOT)
    if len(source_objects) != 4 or source_attestation.get("status") != "pass":
        raise RuntimeError("immutable source lock failed during initial review")
    fresh = _ephemeral_real_e2e()
    matrix = _requirement_matrix(release=release, index=index, entry=entry, fresh=fresh)
    findings = _initial_findings(release=release, index=index, entry=entry)
    commands = _verification()

    for name, payload in (
        ("taskpack_binding.json", taskpack),
        ("phase_commit_binding.json", phase_binding),
        ("final_index_audit.json", index),
        ("release_identity_audit.json", release),
        ("entry_audit.json", entry),
        ("source_lock_audit.json", source_attestation),
        ("fresh_real_e2e.json", fresh),
        ("requirement_matrix.json", matrix),
        ("initial_review_findings.json", findings),
    ):
        _write_json(REVIEW_DIR / name, payload)

    verification = {
        "schema": "PFIV025Stage12InitialReviewVerificationV1",
        "status": "pass",
        "candidate_commit": CANDIDATE_COMMIT,
        "commands": commands,
        "command_count": len(commands),
        "all_exit_zero": all(int(row["exit_code"]) == 0 for row in commands),
        "fresh_real_e2e_status": fresh["status"],
        "phase_artifact_file_count": phase_binding["artifact_file_count"],
        "final_index_file_count": index["index_file_count"],
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
    }
    _write_json(REVIEW_DIR / "verification_results.json", verification)
    (REVIEW_DIR / "terminal.log").write_text(
        "\n".join(
            f"{row['command_id']}|exit={row['exit_code']}|{row['summary']}"
            for row in commands
        )
        + "\n",
        encoding="utf-8",
    )
    (REVIEW_DIR / "risk_and_rollback.md").write_text(
        """# Stage 12 独立整阶段初审风险与回滚

- 初审结论为 `remediation_required`：0 critical、3 important；不代表 Stage 12 通过、release freeze 或用户最终验收。
- 三项整改：runtime manifest commit 真值、exact candidate/acceptance 绑定、旧非 canonical App 的 CLI-only 隔离。
- 五项 P2 保持透明：真实 kernel sleep/wake 未执行、Holdings source 未加载、Finder 方法被用户最新指令覆盖、axe-core 不可用、6 项历史状态测试债务。
- 本轮不修改 canonical private DB，不安装 App，不调用 Finder/LaunchServices/open/AppleScript/GUI，不访问外部网络，不 push。
- 回滚：revert 本轮初审 commit；初审只新增 review 证据与状态记录，candidate `9a7245acf` 本身保持不变。
""",
        encoding="utf-8",
    )
    changed_files = _changed_files()
    (REVIEW_DIR / "changed_files.txt").write_text(
        "\n".join(changed_files) + "\n", encoding="utf-8"
    )
    evidence = {
        "schema": "PFIV025Stage12InitialWholeReviewEvidenceV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "status": "fail",
        "review_result": "remediation_required",
        "git_commit": CANDIDATE_COMMIT,
        "git_commit_semantics": "exact Stage 12.3 candidate reviewed by this initial review",
        "acceptance_id": ACCEPTANCE_ID,
        "allowed_files_obeyed": True,
        "commands": commands,
        "changed_files": changed_files,
        "evidence_files": sorted(
            path.relative_to(REVIEW_DIR).as_posix()
            for path in REVIEW_DIR.rglob("*")
            if path.is_file() and path.name != "artifact_manifest.json"
        ),
        "explicitly_not_done": [
            "finding remediation",
            "post-remediation rereview",
            "S12-P3-T4 release freeze",
            "final human acceptance artifact",
            "GitHub main push",
            "canonical PFI.app final reinstall",
            "production acceptance",
            "v0.2.6 work",
        ],
        "risks": [row["risk_id"] for row in findings["residual_risks"]],
        "rollback": "Revert the Stage 12 initial whole-review commit; candidate and canonical private data are unchanged.",
        "requires_user_acceptance": True,
        "finding_counts": findings["counts"],
        "open_p0_count": findings["open_p0_count"],
        "open_p1_count": findings["open_p1_count"],
        "remediation_required": True,
        "rereview_status": "not_started",
        "finder_used": False,
        "open_command_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
        "canonical_private_database_mutated": False,
        "app_install_performed": False,
        "push_performed": False,
        "release_freeze_performed": False,
        "final_human_acceptance": False,
        "production_accepted": False,
        "contains_private_values": False,
    }
    Draft202012Validator(_taskpack_schema("evidence_pack.schema.json")).validate(evidence)
    _write_json(REVIEW_DIR / "evidence.json", evidence)
    privacy = _privacy_scan()
    output_files = sorted(
        path for path in REVIEW_DIR.rglob("*")
        if path.is_file() and path.name != "artifact_manifest.json"
    )
    bound_sources = (
        PFI_ROOT / "scripts/v025/stage12_whole_review_initial.py",
        PFI_ROOT / "tests/test_v025_stage12_whole_review_initial.py",
        PFI_ROOT / "docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_INITIAL.md",
    )
    manifest = {
        "schema": "PFIV025Stage12InitialReviewArtifactManifestV1",
        "status": "pass",
        "files": {
            path.relative_to(REPO_ROOT).as_posix(): _sha(path)
            for path in (*output_files, *bound_sources)
            if path.is_file()
        },
        "privacy_scan_status": privacy["status"],
        "contains_private_values": False,
    }
    manifest["file_count"] = len(manifest["files"])
    _write_json(REVIEW_DIR / "artifact_manifest.json", manifest)
    if FINAL_ACCEPTANCE.exists():
        raise RuntimeError("initial review created a forbidden final acceptance artifact")
    return evidence


def main() -> int:
    evidence = run()
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "review_result": evidence["review_result"],
                "open_p0_count": evidence["open_p0_count"],
                "open_p1_count": evidence["open_p1_count"],
                "finder_used": evidence["finder_used"],
                "final_human_acceptance": evidence["final_human_acceptance"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
