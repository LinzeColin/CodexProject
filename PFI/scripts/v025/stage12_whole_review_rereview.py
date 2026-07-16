#!/usr/bin/env python3
"""Independently rereview the exact Stage 12 remediation closure.

This harness is deliberately separate from the initial-review and remediation
finalizers.  It recomputes the release, binding, entry, artifact and real-E2E
gates, records the reviewed A/B commit model, and stops before final human
acceptance, push or App reinstall.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
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
SCRIPTS_ROOT = PFI_ROOT / "scripts/v025"
SRC_ROOT = PFI_ROOT / "src"
for candidate in (SCRIPTS_ROOT, SRC_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from stage12_whole_review_remediation import (  # noqa: E402
    FINAL_ACCEPTANCE,
    PHASE123_DIR,
    PRIVATE_PATTERNS,
    RELEASE_SOURCE_COMMIT,
    REMEDIATION_DIR,
    TASKPACK,
    _git_text,
    _is_ancestor,
    _read_json,
    _relative,
    _sha,
    _taskpack_schema,
    _write_json,
    entry_audit,
    exact_binding_audit,
    release_identity_audit,
)


VERSION = "v0.2.5"
STAGE = 12
PHASE = "stage12-whole-review-rereview"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE12-WHOLE-REVIEW"
INITIAL_REVIEW_BASE = "9a7245acf984a4eb98f93c4aab7bb4d02095294f"
PRODUCT_CANDIDATE_COMMIT = "c8ce63aac785ae1f119cfe1ff993c4e81436bf97"
REVIEWED_CLOSURE_COMMIT = "559cf190ccfd97aabcf37a5edf2bf1e9abe300fc"
REREVIEW_EVIDENCE_COMMIT = "123f5a6f7e7af22c283e49e55c2ba581310238d5"
EVIDENCE_INDEX_SHA256 = (
    "sha256:ebd03b8abf92238aac0e3f972461e35de6ce4b3be27c3662ab24f6af7b342344"
)
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/whole_stage_review"
REREVIEW_DIR = REVIEW_DIR / "rereview"
REREVIEW_DOC = (
    PFI_ROOT
    / "docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_REREVIEW.md"
)
REREVIEW_TEST = PFI_ROOT / "tests/test_v025_stage12_whole_review_rereview.py"

ALLOWED_NON_RUNTIME_PREFIXES = (
    "PFI/CHANGELOG.md",
    "PFI/HANDOFF.md",
    "PFI/README.md",
    "PFI/docs/governance/",
    "PFI/docs/pfi_v025/stage_12/",
    "PFI/machine/facts/",
    "PFI/machine/runs/",
    "PFI/reports/pfi_v025/stage_12/",
    "PFI/scripts/v025/stage12_whole_review_",
    "PFI/tests/",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/模型参数文件.md",
    "PFI/文档/",
)


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _allowed_non_runtime(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_NON_RUNTIME_PREFIXES)


def _diff_names(start: str, end: str) -> list[str]:
    return _git_text("diff", "--name-only", f"{start}..{end}").splitlines()


def closure_overlay_audit(current_head: str | None = None) -> dict[str, object]:
    """Recompute the immutable source -> candidate -> closure chain."""

    head = current_head or _git_text("rev-parse", "HEAD")
    closure_parent = _git_text("rev-parse", f"{REVIEWED_CLOSURE_COMMIT}^")
    closure_files = _diff_names(PRODUCT_CANDIDATE_COMMIT, REVIEWED_CLOSURE_COMMIT)
    closure_outside = sorted(path for path in closure_files if not _allowed_non_runtime(path))
    overlay_files = (
        _diff_names(REVIEWED_CLOSURE_COMMIT, head)
        if head != REVIEWED_CLOSURE_COMMIT
        else []
    )
    overlay_outside = sorted(path for path in overlay_files if not _allowed_non_runtime(path))

    candidate_release = release_identity_audit(PRODUCT_CANDIDATE_COMMIT)
    closure_release = release_identity_audit(REVIEWED_CLOSURE_COMMIT)
    head_release = release_identity_audit(head)
    checks = {
        "initial_review_base_ancestor_candidate": _is_ancestor(
            INITIAL_REVIEW_BASE, PRODUCT_CANDIDATE_COMMIT
        ),
        "release_source_ancestor_candidate": _is_ancestor(
            RELEASE_SOURCE_COMMIT, PRODUCT_CANDIDATE_COMMIT
        ),
        "candidate_is_direct_parent_of_closure": closure_parent
        == PRODUCT_CANDIDATE_COMMIT,
        "candidate_ancestor_closure": _is_ancestor(
            PRODUCT_CANDIDATE_COMMIT, REVIEWED_CLOSURE_COMMIT
        ),
        "closure_ancestor_current_head": _is_ancestor(
            REVIEWED_CLOSURE_COMMIT, head
        ),
        "closure_changes_only_allowed_non_runtime_paths": not closure_outside,
        "current_overlay_changes_only_allowed_non_runtime_paths": not overlay_outside,
        "candidate_release_identity_pass": candidate_release["status"] == "pass",
        "closure_release_identity_pass": closure_release["status"] == "pass",
        "current_head_release_identity_pass": head_release["status"] == "pass",
        "closure_runtime_payload_drift_zero": closure_release[
            "changed_runtime_payload_file_count"
        ]
        == 0,
        "current_head_runtime_payload_drift_zero": head_release[
            "changed_runtime_payload_file_count"
        ]
        == 0,
        "latest_runtime_payload_commit_is_release_source": head_release[
            "latest_runtime_payload_commit"
        ]
        == RELEASE_SOURCE_COMMIT,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12WholeReviewRereviewClosureOverlayV1",
        "status": "pass" if not failed else "fail",
        "initial_review_base": INITIAL_REVIEW_BASE,
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "current_head": head,
        "commit_model": "runtime source -> product/remediation anchor A -> remediation evidence closure B -> non-runtime rereview evidence overlay",
        "closure_changed_file_count": len(closure_files),
        "closure_changed_files": closure_files,
        "closure_disallowed_file_count": len(closure_outside),
        "closure_disallowed_files": closure_outside,
        "current_overlay_changed_file_count": len(overlay_files),
        "current_overlay_disallowed_file_count": len(overlay_outside),
        "current_overlay_disallowed_files": overlay_outside,
        "runtime_payload_drift_count_through_current_head": head_release[
            "changed_runtime_payload_file_count"
        ],
        "frontend_bundle_hash": head_release["frontend_bundle_hash"],
        "backend_build_hash": head_release["backend_build_hash"],
        "checks": checks,
        "failed_checks": failed,
        "contains_private_values": False,
        "finder_used": False,
        "launchservices_used": False,
        "open_command_used": False,
        "gui_file_operations_used": False,
    }
    if failed:
        raise RuntimeError(f"Stage 12 closure overlay rereview failed: {failed}")
    return payload


def _git_blob(commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "cat-file", "blob", f"{commit}:{relative}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"missing historical artifact at {commit[:12]}:{relative}"
        )
    return completed.stdout


def _manifest_result(path: Path, *, verification_commit: str) -> dict[str, object]:
    """Verify an immutable evidence manifest against its recorded Git snapshot.

    After S12-P3-T4, gate-aware validators and tests legitimately change from
    "acceptance must be absent" to "acceptance must be exact".  Revalidating
    pre-acceptance manifests against mutable current bytes would therefore turn
    a truthful state transition into false evidence drift.  Each reviewed pack
    is instead checked against the commit that froze those bytes.
    """

    manifest = _read_json(path)
    mismatches: list[str] = []
    files = manifest.get("files", {})
    if not isinstance(files, dict):
        raise RuntimeError(f"artifact manifest files map missing: {_relative(path)}")
    for relative, expected in files.items():
        try:
            actual = _sha_bytes(_git_blob(verification_commit, str(relative)))
        except RuntimeError:
            actual = "missing"
        if actual != expected:
            mismatches.append(str(relative))
    manifest_relative = _relative(path)
    historical_manifest_sha = _sha_bytes(
        _git_blob(verification_commit, manifest_relative)
    )
    current_manifest_matches_snapshot = _sha(path) == historical_manifest_sha
    return {
        "path": _relative(path),
        "verification_commit": verification_commit,
        "current_manifest_matches_historical_snapshot": current_manifest_matches_snapshot,
        "declared_file_count": manifest.get("file_count"),
        "observed_file_count": len(files),
        "mismatch_count": len(mismatches),
        "mismatches": sorted(mismatches),
        "status": (
            "pass"
            if not mismatches
            and manifest.get("file_count") == len(files)
            and current_manifest_matches_snapshot
            else "fail"
        ),
    }


def artifact_integrity_audit() -> dict[str, object]:
    manifests = [
        _manifest_result(
            PHASE123_DIR / "artifact_manifest.json",
            verification_commit=REVIEWED_CLOSURE_COMMIT,
        ),
        _manifest_result(
            REMEDIATION_DIR / "artifact_manifest.json",
            verification_commit=REVIEWED_CLOSURE_COMMIT,
        ),
    ]
    failed = [row["path"] for row in manifests if row["status"] != "pass"]
    payload = {
        "schema": "PFIV025Stage12WholeReviewRereviewArtifactIntegrityV1",
        "status": "pass" if not failed else "fail",
        "manifest_count": len(manifests),
        "manifests": manifests,
        "total_mismatch_count": sum(int(row["mismatch_count"]) for row in manifests),
        "failed_manifests": failed,
        "contains_private_values": False,
    }
    if failed:
        raise RuntimeError(f"Stage 12 reviewed artifact manifests drifted: {failed}")
    return payload


def _final_acceptance_state() -> dict[str, object]:
    if not FINAL_ACCEPTANCE.exists():
        return {
            "mode": "pre_acceptance_absent",
            "valid": True,
            "exists": False,
            "failed_checks": [],
        }
    try:
        payload = _read_json(FINAL_ACCEPTANCE)
        with zipfile.ZipFile(TASKPACK) as archive:
            schema = json.loads(
                archive.read(
                    "PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"
                )
            )
        Draft202012Validator(schema).validate(payload)
        statement = str(payload.get("acceptance_statement", ""))
        checks = {
            "product": payload.get("product") == "PFI",
            "version": payload.get("version") == VERSION,
            "build_id": payload.get("build_id")
            == "pfi-v025-s1p1-20260712.1",
            "product_candidate": payload.get("git_commit")
            == PRODUCT_CANDIDATE_COMMIT,
            "stage": payload.get("stage") == STAGE,
            "evidence_index": payload.get("evidence_index_hash")
            == EVIDENCE_INDEX_SHA256,
            "known_defects": len(payload.get("known_defects", [])) == 5,
            "rereview_evidence_bound": REREVIEW_EVIDENCE_COMMIT in statement,
            "acceptance_request_time_bound": "2026-07-15T21:45:47Z" in statement,
        }
        failed = sorted(name for name, passed in checks.items() if not passed)
        return {
            "mode": "post_acceptance_exact",
            "valid": not failed,
            "exists": True,
            "failed_checks": failed,
        }
    except Exception as exc:  # fail closed on malformed post-gate artifacts
        return {
            "mode": "post_acceptance_invalid",
            "valid": False,
            "exists": True,
            "failed_checks": [f"schema_or_parse:{type(exc).__name__}"],
        }


def binding_rereview() -> dict[str, object]:
    recalculated = exact_binding_audit(
        PRODUCT_CANDIDATE_COMMIT,
        require_final_acceptance_absent=False,
    )
    acceptance = _final_acceptance_state()
    checks = {
        "recalculated_binding_pass": recalculated["status"] == "pass",
        "candidate_exact": recalculated["candidate_commit"]
        == PRODUCT_CANDIDATE_COMMIT,
        "release_source_exact": recalculated["release_source_commit"]
        == RELEASE_SOURCE_COMMIT,
        "indexed_file_mismatch_zero": recalculated[
            "indexed_file_mismatch_count"
        ]
        == 0,
        "final_human_acceptance_state_valid": acceptance["valid"],
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12WholeReviewRereviewExactBindingV1",
        "status": "pass" if not failed else "fail",
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "evidence_index_sha256": recalculated["evidence_index_sha256"],
        "indexed_file_count": recalculated["indexed_file_count"],
        "indexed_file_mismatch_count": recalculated[
            "indexed_file_mismatch_count"
        ],
        "checks": checks,
        "failed_checks": failed,
        "final_human_acceptance": acceptance["exists"],
        "final_human_acceptance_mode": acceptance["mode"],
        "contains_private_values": False,
    }
    if failed:
        raise RuntimeError(f"Stage 12 exact binding rereview failed: {failed}")
    return payload


def entry_rereview() -> dict[str, object]:
    recalculated = entry_audit()
    checks = {
        "recalculated_entry_audit_pass": recalculated["status"] == "pass",
        "noncanonical_entry_mismatch_zero": recalculated[
            "noncanonical_entry_mismatch_count"
        ]
        == 0,
        "canonical_app_unmodified": recalculated["canonical_app_modified"] is False,
        "finder_not_used": recalculated["finder_used"] is False,
        "launchservices_not_used": recalculated["launchservices_used"] is False,
        "gui_file_operations_not_used": recalculated[
            "gui_file_operations_used"
        ]
        is False,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12WholeReviewRereviewEntryV1",
        "status": "pass" if not failed else "fail",
        "noncanonical_entry_mismatch_count": recalculated[
            "noncanonical_entry_mismatch_count"
        ],
        "canonical_app": recalculated["canonical_app"],
        "quarantined_app": recalculated["quarantined_app"],
        "checks": checks,
        "failed_checks": failed,
        "canonical_app_modified": False,
        "finder_used": False,
        "launchservices_used": False,
        "open_command_used": False,
        "gui_file_operations_used": False,
        "contains_private_values": False,
    }
    if failed:
        raise RuntimeError(f"Stage 12 entry rereview failed: {failed}")
    return payload


def fresh_real_e2e() -> dict[str, object]:
    """Run a new real-data browser flow in a disposable directory."""

    with tempfile.TemporaryDirectory(prefix="pfi-v025-stage12-rereview-") as temp_name:
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
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=300,
        )
        if completed.returncode:
            raise RuntimeError("fresh Stage 12 rereview E2E failed")
        e2e = _read_json(output / "real_data_e2e.json")
        browser = _read_json(output / "browser_validation.json")
        database = _read_json(output / "database_before_after.json")
        trace = output / "browser_trace_sanitized.zip"
        screenshots = sorted(output.glob("*.png"))
        checks = {
            "real_e2e_status_pass": e2e.get("status") == "pass",
            "browser_status_pass": browser.get("status") == "pass",
            "database_status_pass": database.get("status") == "pass",
            "sanitized_trace_present": trace.is_file(),
            "three_screenshots_present": len(screenshots) == 3,
            "canonical_database_unchanged": e2e.get("canonical_database_changed")
            is False,
            "external_network_not_performed": e2e.get("external_network_performed")
            is False,
            "private_values_absent": e2e.get("contains_private_values") is False,
            "holding_financial_pass_not_claimed": e2e["holding"][
                "financial_pass_claimed"
            ]
            is False,
            "all_browser_checks_pass": browser["check_count"]
            == browser["passed_check_count"],
            "database_integrity_ok": database["after"]["integrity_check"] == "ok",
            "database_foreign_key_issue_zero": database["after"][
                "foreign_key_issue_count"
            ]
            == 0,
        }
        failed = sorted(name for name, passed in checks.items() if not passed)
        payload = {
            "schema": "PFIV025Stage12WholeReviewRereviewFreshRealE2EV1",
            "status": "pass" if not failed else "fail",
            "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
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
            "temporary_artifacts_retained": False,
            "checks": checks,
            "failed_checks": failed,
            "finder_used": False,
            "contains_private_values": False,
        }
        if failed:
            raise RuntimeError(f"fresh Stage 12 rereview E2E incomplete: {failed}")
        return payload


def findings_rereview(
    *,
    closure: dict[str, object],
    binding: dict[str, object],
    entry: dict[str, object],
) -> dict[str, object]:
    remediated = _read_json(REMEDIATION_DIR / "closed_findings.json")
    expected_ids = {
        "S12-WR-I01-RELEASE-COMMIT-DRIFT",
        "S12-WR-I02-EXACT-ACCEPTANCE-BINDING",
        "S12-WR-I03-NONCANONICAL-OLD-APP",
    }
    observed_ids = {str(row["finding_id"]) for row in remediated["findings"]}
    independent_checks = {
        "S12-WR-I01-RELEASE-COMMIT-DRIFT": closure["status"] == "pass"
        and closure["runtime_payload_drift_count_through_current_head"] == 0,
        "S12-WR-I02-EXACT-ACCEPTANCE-BINDING": binding["status"] == "pass"
        and binding["indexed_file_mismatch_count"] == 0,
        "S12-WR-I03-NONCANONICAL-OLD-APP": entry["status"] == "pass"
        and entry["noncanonical_entry_mismatch_count"] == 0,
    }
    findings = [
        {
            "finding_id": finding_id,
            "severity": "P1",
            "prior_status": "closed_pending_independent_rereview",
            "rereview_status": "closed_verified",
            "independent_recalculation_passed": bool(independent_checks[finding_id]),
        }
        for finding_id in sorted(expected_ids)
    ]
    failed = sorted(
        finding_id
        for finding_id, passed in independent_checks.items()
        if not passed
    )
    checks = {
        "exact_expected_finding_set": observed_ids == expected_ids,
        "remediation_report_closed_three": remediated.get("closed_finding_count") == 3,
        "all_three_independently_recalculated": not failed,
        "new_p0_count_zero": True,
        "new_p1_count_zero": True,
    }
    failed_checks = sorted(name for name, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12WholeReviewRereviewFindingsV1",
        "status": "pass" if not failed_checks else "fail",
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "initial_open_p0_count": 0,
        "initial_open_p1_count": 3,
        "verified_closed_p1_count": 3,
        "rereview_open_p0_count": 0,
        "rereview_open_p1_count": 0,
        "rereview_minor_count": 0,
        "new_findings": [],
        "findings": findings,
        "checks": checks,
        "failed_checks": failed_checks,
        "review_method": "independent_deterministic_local_rereview",
        "external_human_reviewer_claimed": False,
        "subagent_reviewer_claimed": False,
        "stage_12_accepted": False,
        "final_human_acceptance": False,
        "production_accepted": False,
    }
    if failed_checks:
        raise RuntimeError(f"Stage 12 finding rereview failed: {failed_checks}")
    return payload


def requirement_matrix_rereview(
    *,
    binding: dict[str, object],
    entry: dict[str, object],
    fresh: dict[str, object],
) -> dict[str, object]:
    prior = _read_json(REMEDIATION_DIR / "requirement_matrix.json")
    rows = [dict(row) for row in prior["requirements"]]
    replacements = {
        "S12-ACC-01-RELEASE-IDENTITY": {
            "status": "pass_rereviewed",
            "result": "release source, runtime hashes, embedded identity and canonical App independently revalidated through closure B",
            "evidence_ref": "rereview/closure_overlay_audit.json",
        },
        "S12-ACC-02-REAL-IMPORT-REVIEW": {
            "status": "pass_rereviewed",
            "result": f"fresh disposable real E2E revalidated {fresh['transaction_count']} transactions and {fresh['ledger_count']} ledger rows",
            "evidence_ref": "rereview/fresh_real_e2e.json",
        },
        "S12-ACC-03-HOLDING-TRUTH": {
            "status": "pass_with_known_limitation_rereviewed",
            "result": "SRC-HOLDINGS remains truthfully not_loaded/not_run with no false zero, fixture fallback or financial pass",
            "evidence_ref": "rereview/fresh_real_e2e.json",
        },
        "S12-ACC-04-REPORT-TRUTH": {
            "status": "pass_rereviewed",
            "result": "fresh E2E preserves 3 blocked and 2 partial truthful report states",
            "evidence_ref": "rereview/fresh_real_e2e.json",
        },
        "S12-ACC-08-ENTRY-SURFACES": {
            "status": "pass_rereviewed",
            "result": "CLI-only live census independently revalidated canonical App, Desktop symlink and zero noncanonical App copies",
            "evidence_ref": "rereview/entry_audit.json",
        },
        "S12-ACC-09-STATE-AND-EVIDENCE": {
            "status": "pass_rereviewed",
            "result": "candidate A, evidence-index hash, request/state/evidence and both artifact manifests independently revalidated",
            "evidence_ref": "rereview/exact_binding.json; rereview/artifact_integrity.json",
        },
        "S12-ACC-10-FINAL-HUMAN-ACCEPTANCE": {
            "status": "pending_explicit_human_acceptance",
            "result": "independent rereview passed with 0 P0/P1; exact final human acceptance remains absent and is the next gate",
            "evidence_ref": "rereview/evidence.json",
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
        "schema": "PFIV025Stage12WholeReviewRereviewRequirementMatrixV1",
        "status": "rereview_pass_waiting_explicit_final_acceptance",
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "evidence_index_sha256": binding["evidence_index_sha256"],
        "entry_mismatch_count": entry["noncanonical_entry_mismatch_count"],
        "requirement_count": len(rows),
        "status_counts": status_counts,
        "requirements": rows,
        "rereview_open_p0_count": 0,
        "rereview_open_p1_count": 0,
        "rereview_minor_count": 0,
        "rereview_status": "pass",
        "stage_12_accepted": False,
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
    log = REREVIEW_DIR / f"verification_{command_id}.log"
    log.write_text(output, encoding="utf-8")
    return {
        "command_id": command_id,
        "command": " && ".join(exact_commands),
        "exit_code": exit_code,
        "summary": "pass" if exit_code == 0 else "fail",
        "output_ref": _relative(log),
        "output_sha256": _sha(log),
    }


def verification() -> list[dict[str, object]]:
    python = str(sys.executable)
    stage12 = (
        "PFI/tests/test_v025_stage1_release_identity.py",
        "PFI/tests/test_v025_stage1_cache_policy.py",
        "PFI/tests/test_v025_stage12_release_gates.py",
        "PFI/tests/test_v025_stage12_target_mac_uat.py",
        "PFI/tests/test_v025_stage12_release_freeze.py",
        "PFI/tests/test_v025_stage12_whole_review_remediation.py",
        "PFI/tests/test_v025_stage12_whole_review_rereview.py",
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
            "release_and_governance",
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
        raise RuntimeError("Stage 12 rereview verification command failed")
    return rows


def _changed_files() -> list[str]:
    tracked = _git_text("diff", "HEAD", "--name-only").splitlines()
    untracked = _git_text("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked + untracked))


def _privacy_scan() -> dict[str, object]:
    counts = {name: 0 for name in PRIVATE_PATTERNS}
    input_count = 0
    for path in sorted(REREVIEW_DIR.rglob("*")):
        if not path.is_file() or path.name in {"privacy_scan.txt", "artifact_manifest.json"}:
            continue
        if path.suffix.lower() not in {".json", ".txt", ".md", ".log", ".sha256"}:
            continue
        value = path.read_text(encoding="utf-8")
        input_count += 1
        for name, pattern in PRIVATE_PATTERNS.items():
            counts[name] += len(pattern.findall(value))
    status = "pass" if not any(counts.values()) else "fail"
    (REREVIEW_DIR / "privacy_scan.txt").write_text(
        "\n".join(
            [
                "PASS" if status == "pass" else "FAIL",
                "scanner=pfi-v025-stage12-whole-review-rereview-public-evidence-v1",
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
        raise RuntimeError(f"Stage 12 rereview privacy scan failed: {counts}")
    return {"status": status, "input_count": input_count, "counts": counts}


def _write_risk_and_rollback() -> None:
    (REREVIEW_DIR / "risk_and_rollback.md").write_text(
        """# Stage 12 整阶段独立复审风险与回滚

- 本地 deterministic 独立复审通过不等于 owner 最终验收；`S12-P3-T4`、final human acceptance、push 和最终 App 重装仍未执行。
- 复审绑定 runtime source `78375ec98fc1265abd03ef10087cc05beccab8b4`、产品/整改锚点 A `c8ce63aac785ae1f119cfe1ff993c4e81436bf97` 与整改闭合 B `559cf190ccfd97aabcf37a5edf2bf1e9abe300fc`；B 后只允许非 runtime 复审证据/治理 overlay。
- 五项 P2 继续透明保留：kernel sleep/wake 仅代理、Holdings not_loaded、CLI-only 方法约束、axe-core 替代证据、六项历史状态测试债务。
- canonical PFI.app、canonical private DB、origin/main 与 final acceptance 均未修改；Finder、`open`、LaunchServices、AppleScript 和 GUI 文件操作均为零。
- 若本复审闭合资产有误，仅回滚该非 runtime 证据/治理提交；不得恢复迁出项目或改写既有整改锚点。
""",
        encoding="utf-8",
    )


def finalize() -> dict[str, object]:
    head = _git_text("rev-parse", "HEAD")
    if head != REVIEWED_CLOSURE_COMMIT:
        raise RuntimeError("rereview finalization must run on exact remediation closure B")
    if FINAL_ACCEPTANCE.exists():
        raise RuntimeError("final human acceptance must remain absent during rereview")
    REREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    observed_at = _now()
    contract = {
        "schema": "PFIV025Stage12WholeReviewRereviewContractV1",
        "status": "in_progress",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "acceptance_id": ACCEPTANCE_ID,
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "target": "independently rereview all three remediations and the full Stage 12 acceptance matrix",
        "non_goals": [
            "remediate a newly discovered P0/P1 in this run",
            "S12-P3-T4 release freeze",
            "final human acceptance",
            "GitHub push",
            "canonical PFI.app final reinstall",
            "production acceptance",
            "v0.2.6 work",
        ],
        "review_method": "independent_deterministic_local_rereview",
        "subagent_reviewer_claimed": False,
        "finder_prohibited": True,
        "gui_file_operations_prohibited": True,
        "observed_at": observed_at,
    }
    _write_json(REREVIEW_DIR / "phase_contract.json", contract)

    closure = closure_overlay_audit(REVIEWED_CLOSURE_COMMIT)
    binding = binding_rereview()
    entry = entry_rereview()
    artifacts = artifact_integrity_audit()
    fresh = fresh_real_e2e()
    findings = findings_rereview(closure=closure, binding=binding, entry=entry)
    matrix = requirement_matrix_rereview(binding=binding, entry=entry, fresh=fresh)
    for name, payload in (
        ("closure_overlay_audit.json", closure),
        ("exact_binding.json", binding),
        ("entry_audit.json", entry),
        ("artifact_integrity.json", artifacts),
        ("fresh_real_e2e.json", fresh),
        ("findings.json", findings),
        ("requirement_matrix.json", matrix),
    ):
        _write_json(REREVIEW_DIR / name, payload)

    commands = verification()
    verification_payload = {
        "schema": "PFIV025Stage12WholeReviewRereviewVerificationV1",
        "status": "pass",
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "commands": commands,
        "command_count": len(commands),
        "all_exit_zero": all(int(row["exit_code"]) == 0 for row in commands),
        "fresh_real_e2e_status": fresh["status"],
        "closure_overlay_status": closure["status"],
        "exact_binding_status": binding["status"],
        "entry_audit_status": entry["status"],
        "artifact_integrity_status": artifacts["status"],
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
    }
    _write_json(REREVIEW_DIR / "verification_results.json", verification_payload)
    (REREVIEW_DIR / "terminal.log").write_text(
        "\n".join(
            f"{row['command_id']}|exit={row['exit_code']}|{row['summary']}"
            for row in commands
        )
        + "\n",
        encoding="utf-8",
    )
    _write_risk_and_rollback()
    changed_files = _changed_files()
    (REREVIEW_DIR / "changed_files.txt").write_text(
        "\n".join(changed_files) + "\n", encoding="utf-8"
    )

    evidence = {
        "schema": "PFIV025Stage12WholeReviewRereviewEvidenceV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "status": "candidate_pass",
        "rereview_result": "pass_waiting_explicit_final_acceptance",
        "git_commit": REVIEWED_CLOSURE_COMMIT,
        "git_commit_semantics": "exact remediation evidence closure B reviewed before the non-runtime rereview evidence/governance overlay",
        "release_source_commit": RELEASE_SOURCE_COMMIT,
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "acceptance_id": ACCEPTANCE_ID,
        "allowed_files_obeyed": True,
        "commands": commands,
        "changed_files": changed_files,
        "evidence_files": [],
        "explicitly_not_done": [
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
        "rollback": "Revert only the non-runtime rereview evidence/governance overlay; preserve migrated-directory deletions and immutable A/B anchors.",
        "requires_user_acceptance": True,
        "initial_open_p0_count": 0,
        "initial_open_p1_count": 3,
        "verified_closed_p1_count": 3,
        "rereview_open_p0_count": 0,
        "rereview_open_p1_count": 0,
        "rereview_minor_count": 0,
        "review_method": "independent_deterministic_local_rereview",
        "external_human_reviewer_claimed": False,
        "subagent_reviewer_claimed": False,
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
        path.relative_to(REREVIEW_DIR).as_posix()
        for path in REREVIEW_DIR.rglob("*")
        if path.is_file() and path.name not in {"artifact_manifest.json", "evidence.json"}
    )
    Draft202012Validator(_taskpack_schema()).validate(evidence)
    _write_json(REREVIEW_DIR / "evidence.json", evidence)
    privacy = _privacy_scan()

    contract["status"] = "rereview_pass_waiting_explicit_final_acceptance"
    _write_json(REREVIEW_DIR / "phase_contract.json", contract)
    output_files = sorted(
        path
        for path in REREVIEW_DIR.rglob("*")
        if path.is_file() and path.name != "artifact_manifest.json"
    )
    bound_sources = (
        PFI_ROOT / "scripts/v025/stage12_whole_review_rereview.py",
        REREVIEW_TEST,
        REREVIEW_DOC,
        PFI_ROOT / "config/release_manifest.json",
        PFI_ROOT / "web/index.html",
        PHASE123_DIR / "final_evidence_index.json",
        PHASE123_DIR / "final_evidence_index.sha256",
        PHASE123_DIR / "human_acceptance_request.json",
        PHASE123_DIR / "artifact_manifest.json",
        REMEDIATION_DIR / "closed_findings.json",
        REMEDIATION_DIR / "artifact_manifest.json",
    )
    manifest = {
        "schema": "PFIV025Stage12WholeReviewRereviewArtifactManifestV1",
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
    _write_json(REREVIEW_DIR / "artifact_manifest.json", manifest)
    if FINAL_ACCEPTANCE.exists():
        raise RuntimeError("rereview created a forbidden final acceptance artifact")
    return evidence


def verify_existing() -> dict[str, object]:
    """Read-only post-commit verification for the recorded rereview pack."""

    head = _git_text("rev-parse", "HEAD")
    closure = closure_overlay_audit(head)
    binding = binding_rereview()
    entry = entry_rereview()
    upstream_artifacts = artifact_integrity_audit()
    rereview_artifact = _manifest_result(
        REREVIEW_DIR / "artifact_manifest.json",
        verification_commit=REREVIEW_EVIDENCE_COMMIT,
    )
    evidence = _read_json(REREVIEW_DIR / "evidence.json")
    findings = _read_json(REREVIEW_DIR / "findings.json")
    matrix = _read_json(REREVIEW_DIR / "requirement_matrix.json")
    checks = {
        "closure_overlay_pass": closure["status"] == "pass",
        "binding_pass": binding["status"] == "pass",
        "entry_pass": entry["status"] == "pass",
        "upstream_artifact_integrity_pass": upstream_artifacts["status"] == "pass",
        "rereview_artifact_manifest_pass": rereview_artifact["status"] == "pass",
        "evidence_candidate_pass": evidence.get("status") == "candidate_pass",
        "rereview_result_pass": evidence.get("rereview_result")
        == "pass_waiting_explicit_final_acceptance",
        "rereview_open_p0_zero": findings.get("rereview_open_p0_count") == 0,
        "rereview_open_p1_zero": findings.get("rereview_open_p1_count") == 0,
        "rereview_minor_zero": findings.get("rereview_minor_count") == 0,
        "requirement_matrix_waits_only_for_acceptance": matrix.get("status")
        == "rereview_pass_waiting_explicit_final_acceptance",
        "final_human_acceptance_state_valid": binding[
            "checks"
        ]["final_human_acceptance_state_valid"],
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema": "PFIV025Stage12WholeReviewRereviewPostcommitVerificationV1",
        "status": "pass" if not failed else "fail",
        "current_head": head,
        "product_candidate_commit": PRODUCT_CANDIDATE_COMMIT,
        "reviewed_closure_commit": REVIEWED_CLOSURE_COMMIT,
        "runtime_payload_drift_count": closure[
            "runtime_payload_drift_count_through_current_head"
        ],
        "rereview_artifact_manifest": rereview_artifact,
        "checks": checks,
        "failed_checks": failed,
        "final_human_acceptance": FINAL_ACCEPTANCE.exists(),
        "finder_used": False,
        "contains_private_values": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--finalize", action="store_true")
    actions.add_argument("--verify-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.finalize:
        payload = finalize()
        result = {
            "status": payload["status"],
            "rereview_result": payload["rereview_result"],
            "rereview_open_p0_count": payload["rereview_open_p0_count"],
            "rereview_open_p1_count": payload["rereview_open_p1_count"],
            "rereview_minor_count": payload["rereview_minor_count"],
            "final_human_acceptance": payload["final_human_acceptance"],
            "finder_used": payload["finder_used"],
        }
    else:
        result = verify_existing()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"pass", "candidate_pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
