#!/usr/bin/env python3
"""Close the three Stage 12 initial-review P1 findings without rereview or release."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shlex
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

from pfi_v02.stage_v021_runtime_api import (  # noqa: E402
    V025_BACKEND_BUILD_RELATIVE_PATHS,
    _v025_frontend_bundle_hash,
    build_v025_release_asset_identity,
)
from target_mac_uat import CANONICAL_APP, _app_identity  # noqa: E402


VERSION = "v0.2.5"
STAGE = 12
PHASE = "stage12-whole-review-remediation"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE12-WHOLE-REVIEW-REMEDIATION"
RELEASE_SOURCE_COMMIT = "78375ec98fc1265abd03ef10087cc05beccab8b4"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/whole_stage_review"
REMEDIATION_DIR = REVIEW_DIR / "remediation"
PHASE123_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_3"
FINAL_ACCEPTANCE = (
    PFI_ROOT / "reports/pfi_v025/stage_12/final_acceptance/human_acceptance.json"
)
TASKPACK = (
    Path.home()
    / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
)
OLD_APP = Path.home() / "Downloads/PFI.app"
QUARANTINE_APP = (
    Path.home()
    / ".codex_private_runtime/pfi/quarantine/old_apps/PFI-v0.2.3-20260629.1.app"
)
ENTRY_RECEIPT = REMEDIATION_DIR / "entry_quarantine.json"
DESKTOP_ENTRY = Path.home() / "Desktop/PFI.app"
EXPECTED_OLD_VERSION = "0.2.3"
EXPECTED_OLD_BUILD = "20260629.1"
PRIVATE_PATTERNS = {
    "absolute_private_paths": re.compile(
        r"/(?:Users|private/var/folders|var/folders|tmp)/"
    ),
    "financial_values": re.compile(r"\bCNY\s+-?[0-9]"),
    "raw_source_filenames": re.compile(r"alipay_20\d{6}-20\d{6}"),
    "email_addresses": re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    ),
    "private_key_headers": re.compile(
        r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"
    ),
}


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path.name}")
    return payload


def _git_text(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _public_app_identity(identity: dict[str, object]) -> dict[str, object]:
    keys = (
        "kind",
        "short_version",
        "build_version",
        "bundle_identifier",
        "executable_sha256",
        "bundle_tree_sha256",
        "codesign_valid",
        "project_binding_present",
        "project_binding_matches",
        "project_binding_sha256",
    )
    return {key: identity.get(key) for key in keys if key in identity}


def _require_expected_old_app(identity: dict[str, object]) -> None:
    if (
        identity.get("kind") != "app_bundle"
        or identity.get("short_version") != EXPECTED_OLD_VERSION
        or identity.get("build_version") != EXPECTED_OLD_BUILD
    ):
        raise RuntimeError("noncanonical App does not match the reviewed old version/build")


def quarantine_old_app(
    *,
    source: Path = OLD_APP,
    target: Path = QUARANTINE_APP,
    receipt_path: Path = ENTRY_RECEIPT,
    canonical_app: Path = CANONICAL_APP,
) -> dict[str, object]:
    """Atomically isolate the reviewed old App and retain a path-safe rollback receipt."""

    source = source.expanduser()
    target = target.expanduser()
    if source == canonical_app or target == canonical_app:
        raise RuntimeError("canonical App cannot be used as a quarantine endpoint")
    if source.is_symlink() or target.is_symlink():
        raise RuntimeError("App quarantine endpoints must not be symlinks")
    if source.exists() and target.exists():
        raise RuntimeError("both source and quarantine App exist; refuse ambiguous move")

    moved_this_run = False
    if source.exists():
        before = _app_identity(source)
        _require_expected_old_app(before)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(target.parent, 0o700)
        os.replace(source, target)
        moved_this_run = True
    elif target.exists():
        before = _app_identity(target)
        _require_expected_old_app(before)
    else:
        raise RuntimeError("reviewed old App is absent from both source and quarantine")

    after = _app_identity(target)
    _require_expected_old_app(after)
    if source.exists() or not target.exists():
        raise RuntimeError("CLI App quarantine postcondition failed")
    if before.get("bundle_tree_sha256") != after.get("bundle_tree_sha256"):
        raise RuntimeError("App bundle hash changed during quarantine")

    prior = _read_json(receipt_path) if receipt_path.is_file() else {}
    if prior and prior.get("bundle_tree_sha256") != after.get("bundle_tree_sha256"):
        raise RuntimeError("existing quarantine receipt does not match the App")
    payload = {
        "schema": "PFIV025Stage12ReviewOldAppQuarantineV1",
        "status": "pass",
        "observed_at": prior.get("observed_at") or _now(),
        "operation": "cli_atomic_move",
        "moved_this_run": moved_this_run,
        "idempotent_recheck": not moved_this_run,
        "source_location": "downloads_pfi_app",
        "quarantine_location": "private_runtime_old_apps_pfi_v023_20260629_1",
        "source_absent": True,
        "quarantine_present": True,
        "short_version": after["short_version"],
        "build_version": after["build_version"],
        "bundle_tree_sha256": after["bundle_tree_sha256"],
        "executable_sha256": after["executable_sha256"],
        "identity_before": _public_app_identity(before),
        "identity_after": _public_app_identity(after),
        "rollback_command": "mkdir -p \"$HOME/Downloads\" && test ! -e \"$HOME/Downloads/PFI.app\" && mv \"$HOME/.codex_private_runtime/pfi/quarantine/old_apps/PFI-v0.2.3-20260629.1.app\" \"$HOME/Downloads/PFI.app\"",
        "rollback_tested": False,
        "canonical_app_modified": False,
        "deletion_performed": False,
        "finder_used": False,
        "launchservices_used": False,
        "open_command_used": False,
        "gui_file_operations_used": False,
        "contains_private_values": False,
    }
    _write_json(receipt_path, payload)
    return payload


def _embedded_manifest() -> dict[str, Any]:
    source = (PFI_ROOT / "web/index.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script\s+type="application/json"\s+id="pfi-release-manifest">(.*?)</script>',
        source,
        re.DOTALL,
    )
    if match is None:
        raise RuntimeError("embedded release manifest is missing")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise RuntimeError("embedded release manifest is not an object")
    return payload


def release_identity_audit(candidate_commit: str) -> dict[str, object]:
    manifest = _read_json(PFI_ROOT / "config/release_manifest.json")
    identity = build_v025_release_asset_identity(PFI_ROOT, manifest=manifest)
    _, frontend_files = _v025_frontend_bundle_hash(PFI_ROOT)
    backend_files = {
        f"PFI/{relative}" for relative in V025_BACKEND_BUILD_RELATIVE_PATHS
    }
    runtime_scope = set(frontend_files) | backend_files | {
        "PFI/config/release_manifest.json"
    }
    identity_carriers = {
        "PFI/config/release_manifest.json",
        "PFI/web/index.html",
    }
    runtime_payload = sorted(runtime_scope - identity_carriers)
    changed_payload = _git_text(
        "diff",
        "--name-only",
        f"{RELEASE_SOURCE_COMMIT}..{candidate_commit}",
        "--",
        *runtime_payload,
    ).splitlines()
    changed_scope = _git_text(
        "diff",
        "--name-only",
        f"{RELEASE_SOURCE_COMMIT}..{candidate_commit}",
        "--",
        *sorted(runtime_scope),
    ).splitlines()
    latest_payload_commit = _git_text(
        "log",
        "-1",
        "--format=%H",
        candidate_commit,
        "--",
        *runtime_payload,
    )
    embedded = _embedded_manifest()
    installed = _app_identity(CANONICAL_APP)
    receipt = _read_json(
        PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_2/app_installation.json"
    )
    expected_installed = receipt.get("after", {})
    canonical_matches = (
        installed.get("kind") == "app_bundle"
        and installed.get("short_version") == manifest.get("app_short_version")
        and installed.get("build_version") == manifest.get("app_build_version")
        and installed.get("bundle_tree_sha256")
        == expected_installed.get("bundle_tree_sha256")
        and installed.get("executable_sha256")
        == expected_installed.get("executable_sha256")
        and installed.get("codesign_valid") is True
        and installed.get("project_binding_matches") is True
    )
    checks = {
        "candidate_commit_exact": bool(
            re.fullmatch(r"[0-9a-f]{40}", candidate_commit)
        ),
        "release_source_commit_exact": manifest.get("git_commit")
        == RELEASE_SOURCE_COMMIT,
        "release_source_is_ancestor": _is_ancestor(
            RELEASE_SOURCE_COMMIT, candidate_commit
        ),
        "latest_runtime_payload_commit_is_source": latest_payload_commit
        == RELEASE_SOURCE_COMMIT,
        "runtime_payload_unchanged_after_source": not changed_payload,
        "runtime_scope_changes_only_identity_carriers": set(changed_scope)
        <= identity_carriers,
        "config_and_embedded_manifests_exact": embedded == manifest,
        "frontend_hash_matches": identity["frontend_valid"] is True,
        "disk_backend_hash_matches": identity["disk_backend_valid"] is True,
        "running_backend_hash_matches": identity["running_backend_valid"] is True,
        "canonical_app_matches_phase122_receipt": canonical_matches,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12ReviewRemediationReleaseIdentityV1",
        "status": "pass" if not failed else "fail",
        "candidate_commit": candidate_commit,
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "release_source_role": "latest commit changing the immutable runtime payload",
        "candidate_role": "product and Stage 12 review-remediation anchor",
        "identity_carrier_role": "manifest and embedded web manifest may bind the source commit without changing canonical frontend/backend hashes",
        "runtime_scope_file_count": len(runtime_scope),
        "runtime_payload_file_count": len(runtime_payload),
        "identity_carrier_file_count": len(identity_carriers),
        "changed_runtime_payload_file_count": len(changed_payload),
        "changed_runtime_payload_files": changed_payload,
        "changed_runtime_scope_files": changed_scope,
        "latest_runtime_payload_commit": latest_payload_commit,
        "frontend_bundle_hash": identity["frontend_bundle_hash"],
        "backend_build_hash": identity["backend_build_hash"],
        "canonical_app": _public_app_identity(installed),
        "checks": checks,
        "failed_checks": failed,
        "finder_used": False,
        "gui_file_operations_used": False,
        "contains_private_values": False,
    }
    if failed:
        raise RuntimeError(f"release identity remediation audit failed: {failed}")
    return payload


def exact_binding_audit(
    candidate_commit: str, *, require_final_acceptance_absent: bool = False
) -> dict[str, object]:
    index_path = PHASE123_DIR / "final_evidence_index.json"
    index = _read_json(index_path)
    request = _read_json(PHASE123_DIR / "human_acceptance_request.json")
    state = _read_json(PHASE123_DIR / "state_consistency.json")
    evidence = _read_json(PHASE123_DIR / "evidence.json")
    index_hash = _sha(index_path)
    detached = (PHASE123_DIR / "final_evidence_index.sha256").read_text(
        encoding="utf-8"
    )
    mismatches = []
    for row in index["files"]:
        path = REPO_ROOT / str(row["path"])
        actual = _sha(path) if path.is_file() else "missing"
        if actual != row["sha256"]:
            mismatches.append(str(row["path"]))
    detached_matches = detached == (
        f"{index_hash.removeprefix('sha256:')}  final_evidence_index.json\n"
    )
    checks = {
        "index_candidate_exact": index.get("candidate_git_commit")
        == candidate_commit,
        "index_release_source_exact": index.get("release_manifest_git_commit")
        == RELEASE_SOURCE_COMMIT,
        "all_indexed_files_match_current_bytes": not mismatches,
        "detached_index_hash_matches": detached_matches,
        "request_candidate_exact": request.get("git_commit") == candidate_commit,
        "request_index_hash_exact": request.get("evidence_index_hash")
        == index_hash,
        "state_candidate_exact": state.get("git", {}).get("candidate_commit")
        == candidate_commit,
        "state_head_exact_at_generation": state.get("git", {}).get("head")
        == candidate_commit,
        "state_exact_flag_true": state.get("git", {}).get(
            "candidate_commit_exact_at_generation"
        )
        is True,
        "phase_evidence_candidate_exact": evidence.get("git_commit")
        == candidate_commit,
        "no_self_sentinel": all(
            value != "SELF"
            for value in (
                index.get("candidate_git_commit"),
                request.get("git_commit"),
                state.get("git", {}).get("candidate_commit"),
                state.get("git", {}).get("head"),
                evidence.get("git_commit"),
            )
        ),
        "final_human_acceptance_gate": (
            not FINAL_ACCEPTANCE.exists()
            if require_final_acceptance_absent
            else True
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12ReviewRemediationExactBindingV1",
        "status": "pass" if not failed else "fail",
        "candidate_commit": candidate_commit,
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "evidence_index_sha256": index_hash,
        "indexed_file_count": len(index["files"]),
        "indexed_file_mismatch_count": len(mismatches),
        "indexed_file_mismatches": mismatches,
        "checks": checks,
        "failed_checks": failed,
        "rereview_status": "not_started",
        "final_human_acceptance": FINAL_ACCEPTANCE.exists(),
        "contains_private_values": False,
    }
    if failed:
        raise RuntimeError(f"exact candidate binding audit failed: {failed}")
    return payload


def entry_audit() -> dict[str, object]:
    receipt = _read_json(ENTRY_RECEIPT)
    quarantined = _app_identity(QUARANTINE_APP)
    canonical = _app_identity(CANONICAL_APP)
    desktop_is_symlink = DESKTOP_ENTRY.is_symlink()
    desktop_targets_canonical = (
        desktop_is_symlink
        and DESKTOP_ENTRY.resolve(strict=True) == CANONICAL_APP.resolve(strict=True)
    )
    downloads_candidates = sorted(
        path for path in (Path.home() / "Downloads").glob("PFI*.app")
        if path.is_dir() and not path.is_symlink()
    )
    desktop_candidates = sorted(
        path for path in (Path.home() / "Desktop").glob("PFI*.app")
        if path.is_dir() and not path.is_symlink()
    )
    checks = {
        "reviewed_downloads_app_absent": not OLD_APP.exists(),
        "private_quarantine_app_present": QUARANTINE_APP.is_dir(),
        "quarantine_version_exact": quarantined.get("short_version")
        == EXPECTED_OLD_VERSION,
        "quarantine_build_exact": quarantined.get("build_version")
        == EXPECTED_OLD_BUILD,
        "quarantine_hash_matches_receipt": quarantined.get("bundle_tree_sha256")
        == receipt.get("bundle_tree_sha256"),
        "canonical_app_version_exact": canonical.get("short_version") == "0.2.5",
        "canonical_app_build_exact": canonical.get("build_version")
        == "20260712.1",
        "canonical_app_codesign_valid": canonical.get("codesign_valid") is True,
        "canonical_project_binding_exact": canonical.get(
            "project_binding_matches"
        )
        is True,
        "desktop_symlink_targets_canonical": desktop_targets_canonical,
        "downloads_noncanonical_app_count_zero": not downloads_candidates,
        "desktop_noncanonical_app_count_zero": not desktop_candidates,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12ReviewRemediationEntryAuditV1",
        "status": "pass" if not failed else "fail",
        "canonical_location": "applications_pfi_app",
        "desktop_location": "desktop_pfi_app_symlink",
        "reviewed_old_location": "downloads_pfi_app",
        "quarantine_location": "private_runtime_old_apps_pfi_v023_20260629_1",
        "downloads_noncanonical_app_count": len(downloads_candidates),
        "desktop_noncanonical_app_count": len(desktop_candidates),
        "noncanonical_entry_mismatch_count": len(downloads_candidates)
        + len(desktop_candidates),
        "canonical_app": _public_app_identity(canonical),
        "quarantined_app": _public_app_identity(quarantined),
        "checks": checks,
        "failed_checks": failed,
        "canonical_app_modified": False,
        "deletion_performed": False,
        "finder_used": False,
        "launchservices_used": False,
        "open_command_used": False,
        "gui_file_operations_used": False,
        "contains_private_values": False,
    }
    if failed:
        raise RuntimeError(f"entry remediation audit failed: {failed}")
    return payload


def _ephemeral_real_e2e(candidate_commit: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(
        prefix="pfi-v025-stage12-remediation-"
    ) as temp_name:
        output = Path(temp_name) / "real-e2e"
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "PFI/web/tests/v025/stage12_real_e2e_browser.py",
                "--output-dir",
                str(output),
            ],
            cwd=REPO_ROOT,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": "PFI/src",
            },
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        if completed.returncode:
            raise RuntimeError("fresh headless real E2E remediation recheck failed")
        e2e = _read_json(output / "real_data_e2e.json")
        browser = _read_json(output / "browser_validation.json")
        database = _read_json(output / "database_before_after.json")
        trace = output / "browser_trace_sanitized.zip"
        screenshots = sorted(output.glob("*.png"))
        passed = (
            e2e.get("status")
            == browser.get("status")
            == database.get("status")
            == "pass"
            and trace.is_file()
            and len(screenshots) == 3
        )
        if not passed:
            raise RuntimeError("fresh headless E2E artifacts are incomplete")
        return {
            "schema": "PFIV025Stage12ReviewRemediationFreshRealE2EV1",
            "status": "pass",
            "candidate_commit": candidate_commit,
            "source_blob_count": e2e["source"]["source_blob_count"],
            "source_object_set_hash": e2e["source"]["source_object_set_hash"],
            "transaction_count": e2e["import"]["transaction_count"],
            "ledger_count": e2e["import"]["confirmed_ledger_count"],
            "review_count": e2e["import"]["review_count"],
            "replay_idempotent": e2e["import"]["replay_idempotent"],
            "holding_execution_status": e2e["holding"]["execution_status"],
            "holding_truth_gate_status": e2e["holding"]["truth_gate_status"],
            "holding_financial_pass_claimed": e2e["holding"][
                "financial_pass_claimed"
            ],
            "blocked_report_count": e2e["report"]["blocked_report_count"],
            "partial_report_count": e2e["report"]["partial_report_count"],
            "browser_check_count": browser["check_count"],
            "browser_passed_check_count": browser["passed_check_count"],
            "screenshot_count": len(screenshots),
            "trace_sha256": _sha(trace),
            "database_integrity": database["after"]["integrity_check"],
            "database_foreign_key_issue_count": database["after"][
                "foreign_key_issue_count"
            ],
            "canonical_database_read": e2e["canonical_database_read"],
            "canonical_database_changed": e2e["canonical_database_changed"],
            "external_network_performed": e2e["external_network_performed"],
            "contains_private_values": e2e["contains_private_values"],
            "temporary_artifacts_retained": False,
            "finder_used": False,
        }


def _closed_findings(
    candidate_commit: str,
    *,
    release: dict[str, object],
    binding: dict[str, object],
    entry: dict[str, object],
) -> dict[str, object]:
    findings = [
        {
            "finding_id": "S12-WR-I01-RELEASE-COMMIT-DRIFT",
            "severity": "P1",
            "status": "closed_pending_independent_rereview",
            "result": "runtime payload is exactly anchored to the Phase 12.2 source commit; only canonical identity carriers changed afterward",
            "evidence_ref": "remediation/release_identity.json",
            "release_source_commit": release["release_source_commit"],
        },
        {
            "finding_id": "S12-WR-I02-EXACT-ACCEPTANCE-BINDING",
            "severity": "P1",
            "status": "closed_pending_independent_rereview",
            "result": "index, request, state and Phase evidence bind the exact immutable remediation anchor with no SELF sentinel",
            "evidence_ref": "remediation/exact_binding.json",
            "candidate_commit": binding["candidate_commit"],
            "evidence_index_sha256": binding["evidence_index_sha256"],
        },
        {
            "finding_id": "S12-WR-I03-NONCANONICAL-OLD-APP",
            "severity": "P1",
            "status": "closed_pending_independent_rereview",
            "result": "the reviewed old Downloads App was atomically moved to private quarantine; entry mismatch count is zero",
            "evidence_ref": "remediation/entry_audit.json",
            "noncanonical_entry_mismatch_count": entry[
                "noncanonical_entry_mismatch_count"
            ],
        },
    ]
    return {
        "schema": "PFIV025Stage12ReviewRemediationClosedFindingsV1",
        "status": "remediation_complete_waiting_independent_rereview",
        "candidate_commit": candidate_commit,
        "initial_open_p0_count": 0,
        "initial_open_p1_count": 3,
        "remediation_open_p0_count": 0,
        "remediation_open_p1_count": 0,
        "finding_count": len(findings),
        "closed_finding_count": len(findings),
        "findings": findings,
        "rereview_status": "not_started",
        "stage_12_accepted": False,
        "final_human_acceptance": False,
        "production_accepted": False,
    }


def _requirement_matrix(
    candidate_commit: str,
    *,
    release: dict[str, object],
    binding: dict[str, object],
    entry: dict[str, object],
) -> dict[str, object]:
    initial = _read_json(REVIEW_DIR / "requirement_matrix.json")
    rows = [dict(row) for row in initial["requirements"]]
    replacements = {
        "S12-ACC-01-RELEASE-IDENTITY": {
            "status": "pass_remediated_pending_rereview",
            "result": "release source, asset hashes, embedded identity and canonical App are exact",
            "evidence_ref": "remediation/release_identity.json",
        },
        "S12-ACC-08-ENTRY-SURFACES": {
            "status": "pass_remediated_pending_rereview",
            "result": "canonical App and Desktop symlink are exact; Downloads noncanonical App count is zero after reversible CLI quarantine",
            "evidence_ref": "remediation/entry_audit.json",
        },
        "S12-ACC-09-STATE-AND-EVIDENCE": {
            "status": "pass_remediated_pending_rereview",
            "result": "index, request, state and evidence bind one exact candidate commit and evidence-index hash",
            "evidence_ref": "remediation/exact_binding.json",
        },
        "S12-ACC-10-FINAL-HUMAN-ACCEPTANCE": {
            "status": "pending_after_rereview",
            "result": "final acceptance remains absent and may only follow independent rereview",
            "evidence_ref": "remediation/exact_binding.json",
        },
    }
    for row in rows:
        if row["requirement_id"] in replacements:
            row.update(replacements[row["requirement_id"]])
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema": "PFIV025Stage12ReviewRemediationRequirementMatrixV1",
        "status": "remediation_complete_waiting_independent_rereview",
        "candidate_commit": candidate_commit,
        "release_source_commit": release["release_source_commit"],
        "evidence_index_sha256": binding["evidence_index_sha256"],
        "entry_mismatch_count": entry["noncanonical_entry_mismatch_count"],
        "requirement_count": len(rows),
        "status_counts": status_counts,
        "requirements": rows,
        "rereview_status": "not_started",
        "final_human_acceptance": False,
    }


def _sanitize(value: str) -> str:
    return value.replace(str(Path.home()), "$HOME").replace(
        sys.executable, "$PYTHON"
    )


def _run_group(
    command_id: str, commands: Sequence[Sequence[str]]
) -> dict[str, object]:
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "PFI/src:PFI/scripts/v025",
    }
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
    log = REMEDIATION_DIR / f"verification_{command_id}.log"
    log.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "exit_code": exit_code,
        "summary": "pass" if exit_code == 0 else "fail",
        "output_ref": _relative(log),
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
        "PFI/tests/test_v025_stage12_whole_review_remediation.py",
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
            (
                (
                    python,
                    "-B",
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    *stage12,
                ),
            ),
        ),
        _run_group(
            "selected_adjacent_regression",
            (
                (
                    python,
                    "-B",
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    *adjacent,
                ),
            ),
        ),
        _run_group(
            "node_cache_policy",
            (("node", "--test", "PFI/web/tests/v025/stage1_cache_policy.test.mjs"),),
        ),
        _run_group(
            "release_and_dual_plane",
            (
                (
                    python,
                    "-B",
                    "PFI/scripts/v025/release_cache_contract.py",
                    "--project-root",
                    "PFI",
                    "--isolated-candidate",
                    "--policy-json",
                ),
                (
                    python,
                    "-B",
                    "PFI/machine/tools/check_dual_plane_ci.py",
                    "--root",
                    "PFI",
                    "--projects",
                    ".",
                    "--require-projects",
                ),
                (
                    python,
                    "-B",
                    "scripts/lean_governance.py",
                    "check-render",
                    "--project",
                    "PFI",
                ),
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
        raise RuntimeError("Stage 12 remediation verification command failed")
    return rows


def _changed_files() -> list[str]:
    tracked = _git_text("diff", "HEAD", "--name-only").splitlines()
    untracked = _git_text(
        "ls-files", "--others", "--exclude-standard"
    ).splitlines()
    return sorted(set(tracked + untracked))


def _privacy_scan() -> dict[str, object]:
    counts = {name: 0 for name in PRIVATE_PATTERNS}
    input_count = 0
    for path in sorted(REMEDIATION_DIR.rglob("*")):
        if not path.is_file() or path.name in {
            "privacy_scan.txt",
            "artifact_manifest.json",
        }:
            continue
        if path.suffix.lower() not in {
            ".json",
            ".txt",
            ".md",
            ".log",
            ".sha256",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        input_count += 1
        for name, pattern in PRIVATE_PATTERNS.items():
            counts[name] += len(pattern.findall(text))
    status = "pass" if not any(counts.values()) else "fail"
    (REMEDIATION_DIR / "privacy_scan.txt").write_text(
        "\n".join(
            [
                "PASS" if status == "pass" else "FAIL",
                "scanner=pfi-v025-stage12-whole-review-remediation-public-evidence-v1",
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
        raise RuntimeError(f"Stage 12 remediation privacy scan failed: {counts}")
    return {"status": status, "input_count": input_count, "counts": counts}


def _taskpack_schema() -> dict[str, object]:
    with zipfile.ZipFile(TASKPACK) as archive:
        payload = json.loads(
            archive.read(
                "PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"
            )
        )
    if not isinstance(payload, dict):
        raise RuntimeError("TaskPack evidence schema is invalid")
    return payload


def finalize(candidate_commit: str) -> dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{40}", candidate_commit):
        raise RuntimeError("candidate commit must be an exact Git commit")
    if _git_text("rev-parse", "HEAD") != candidate_commit:
        raise RuntimeError("remediation finalization must run on the exact anchor HEAD")
    if FINAL_ACCEPTANCE.exists():
        raise RuntimeError("final human acceptance must remain absent during remediation")
    REMEDIATION_DIR.mkdir(parents=True, exist_ok=True)

    observed_at = _now()
    contract = {
        "schema": "PFIV025Stage12WholeReviewRemediationContractV1",
        "status": "in_progress",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "acceptance_id": ACCEPTANCE_ID,
        "candidate_commit": candidate_commit,
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "target": "close initial-review findings I01, I02 and I03 and stop before independent rereview",
        "non_goals": [
            "independent post-remediation rereview",
            "S12-P3-T4 release freeze",
            "final human acceptance",
            "GitHub push",
            "canonical PFI.app final reinstall",
            "production acceptance",
            "v0.2.6 work",
        ],
        "finder_prohibited": True,
        "gui_file_operations_prohibited": True,
        "observed_at": observed_at,
    }
    _write_json(REMEDIATION_DIR / "phase_contract.json", contract)

    release = release_identity_audit(candidate_commit)
    binding = exact_binding_audit(
        candidate_commit,
        require_final_acceptance_absent=True,
    )
    entry = entry_audit()
    fresh = _ephemeral_real_e2e(candidate_commit)
    findings = _closed_findings(
        candidate_commit, release=release, binding=binding, entry=entry
    )
    matrix = _requirement_matrix(
        candidate_commit, release=release, binding=binding, entry=entry
    )
    for name, payload in (
        ("release_identity.json", release),
        ("exact_binding.json", binding),
        ("entry_audit.json", entry),
        ("fresh_real_e2e.json", fresh),
        ("closed_findings.json", findings),
        ("requirement_matrix.json", matrix),
    ):
        _write_json(REMEDIATION_DIR / name, payload)

    commands = _verification()
    verification = {
        "schema": "PFIV025Stage12WholeReviewRemediationVerificationV1",
        "status": "pass",
        "candidate_commit": candidate_commit,
        "commands": commands,
        "command_count": len(commands),
        "all_exit_zero": all(int(row["exit_code"]) == 0 for row in commands),
        "fresh_real_e2e_status": fresh["status"],
        "release_identity_status": release["status"],
        "exact_binding_status": binding["status"],
        "entry_audit_status": entry["status"],
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
    }
    _write_json(REMEDIATION_DIR / "verification_results.json", verification)
    (REMEDIATION_DIR / "terminal.log").write_text(
        "\n".join(
            f"{row['command_id']}|exit={row['exit_code']}|{row['summary']}"
            for row in commands
        )
        + "\n",
        encoding="utf-8",
    )
    (REMEDIATION_DIR / "risk_and_rollback.md").write_text(
        """# Stage 12 整阶段初审整改风险与回滚

- 三项 P1 已完成整改，但必须经后续独立复审才能转为 Stage 12 审查通过；本轮不执行最终验收。
- runtime payload 锚定于 `78375ec98fc1265abd03ef10087cc05beccab8b4`，remediation candidate 只增加身份载体、整改工具与证据；任何后续 runtime 漂移都必须重建 release identity。
- 旧 Downloads App 未删除，已用 CLI 原子移动至权限为 0700 的私有隔离目录；公开 receipt 保留 `$HOME` 形式的精确回滚命令。
- canonical PFI.app、canonical private DB、origin/main 与 final human acceptance 均未修改。
- 五项 P2 继续透明保留：kernel sleep/wake 代理限制、Holdings not_loaded、CLI-only 方法约束、axe-core 替代证据、六项历史状态测试债务。
- 停止边界：独立复审、`S12-P3-T4`、最终验收、push、最终 App 重装和 v0.2.6 均未开始；Finder/LaunchServices/open/AppleScript/GUI 操作均为零。
""",
        encoding="utf-8",
    )
    changed_files = _changed_files()
    (REMEDIATION_DIR / "changed_files.txt").write_text(
        "\n".join(changed_files) + "\n", encoding="utf-8"
    )
    evidence = {
        "schema": "PFIV025Stage12WholeReviewRemediationEvidenceV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "status": "candidate_pass",
        "remediation_result": "complete_waiting_independent_rereview",
        "git_commit": candidate_commit,
        "git_commit_semantics": "exact product and Stage 12 remediation anchor; current overlay contains only evidence and governance",
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "acceptance_id": ACCEPTANCE_ID,
        "allowed_files_obeyed": True,
        "commands": commands,
        "changed_files": changed_files,
        "evidence_files": [],
        "explicitly_not_done": [
            "independent post-remediation rereview",
            "S12-P3-T4 release freeze",
            "final human acceptance artifact",
            "GitHub main push",
            "canonical PFI.app final reinstall",
            "production acceptance",
            "v0.2.6 work",
        ],
        "risks": [
            "S12-WR-R01-ACTUAL-SLEEP-WAKE-NOT-RUN",
            "S12-WR-R02-HOLDINGS-SOURCE-NOT-LOADED",
            "S12-WR-R03-FINDER-METHOD-OVERRIDDEN",
            "S12-WR-R04-AXE-CORE-NOT-AVAILABLE",
            "S12-WR-R05-HISTORICAL-STATE-TEST-DEBT",
        ],
        "rollback": "Restore the quarantined old App with the receipt command, then revert the evidence/governance overlay and remediation anchor if necessary.",
        "requires_user_acceptance": True,
        "initial_open_p0_count": 0,
        "initial_open_p1_count": 3,
        "remediation_open_p0_count": 0,
        "remediation_open_p1_count": 0,
        "closed_finding_count": 3,
        "rereview_status": "not_started",
        "stage_12_accepted": False,
        "finder_used": False,
        "open_command_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
        "canonical_private_database_mutated": False,
        "canonical_app_modified": False,
        "app_install_performed": False,
        "push_performed": False,
        "release_freeze_performed": False,
        "final_human_acceptance": False,
        "production_accepted": False,
        "contains_private_values": False,
    }
    evidence["evidence_files"] = sorted(
        path.relative_to(REMEDIATION_DIR).as_posix()
        for path in REMEDIATION_DIR.rglob("*")
        if path.is_file() and path.name not in {"artifact_manifest.json", "evidence.json"}
    )
    Draft202012Validator(_taskpack_schema()).validate(evidence)
    _write_json(REMEDIATION_DIR / "evidence.json", evidence)
    privacy = _privacy_scan()
    output_files = sorted(
        path
        for path in REMEDIATION_DIR.rglob("*")
        if path.is_file() and path.name != "artifact_manifest.json"
    )
    bound_sources = (
        PFI_ROOT / "scripts/v025/stage12_whole_review_remediation.py",
        PFI_ROOT / "scripts/v025/prepare_release_freeze.py",
        PFI_ROOT / "tests/test_v025_stage12_whole_review_remediation.py",
        PFI_ROOT
        / "docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_REMEDIATION.md",
        PFI_ROOT / "config/release_manifest.json",
        PFI_ROOT / "web/index.html",
    )
    manifest = {
        "schema": "PFIV025Stage12WholeReviewRemediationArtifactManifestV1",
        "status": "pass",
        "files": {
            _relative(path): _sha(path)
            for path in (*output_files, *bound_sources)
            if path.is_file()
        },
        "privacy_scan_status": privacy["status"],
        "contains_private_values": False,
    }
    manifest["file_count"] = len(manifest["files"])
    _write_json(REMEDIATION_DIR / "artifact_manifest.json", manifest)
    if FINAL_ACCEPTANCE.exists():
        raise RuntimeError("remediation created a forbidden final acceptance artifact")
    return evidence


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--quarantine-entry", action="store_true")
    actions.add_argument("--finalize", action="store_true")
    parser.add_argument("--candidate-commit")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.quarantine_entry:
        payload = quarantine_old_app()
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "operation": payload["operation"],
                    "moved_this_run": payload["moved_this_run"],
                    "source_absent": payload["source_absent"],
                    "quarantine_present": payload["quarantine_present"],
                    "finder_used": payload["finder_used"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    if not args.candidate_commit:
        raise SystemExit("--candidate-commit is required with --finalize")
    evidence = finalize(args.candidate_commit)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "remediation_result": evidence["remediation_result"],
                "closed_finding_count": evidence["closed_finding_count"],
                "rereview_status": evidence["rereview_status"],
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
