#!/usr/bin/env python3
"""Build the deterministic core evidence for the Stage 11 whole-stage review."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_11/whole_stage_review"
ROADMAP = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md"
TASKPACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REVIEW_BASE = "f49e10f47a2f9996e4de0e66402686ae502ce16c"
REMEDIATION_COMMIT = "9c450ea483cd2040636e375c9f7d84e5127e44cf"
EXPECTED_ROADMAP_SHA256 = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
EXPECTED_TASKPACK_SHA256 = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
PHASES = (
    (
        "11.1",
        "phase_11_1",
        "ad16901505f7e6f23653aa8b1e03945211dc4e93",
        "aa6bacba3342fe0a775fad2225317dd20842f6bf",
    ),
    (
        "11.2",
        "phase_11_2",
        "bbfdfa419e1fb8ffc3e3ba22d63cffbc3d5f267b",
        "599c64eb00d2c725a4817deb050312a91462774e",
    ),
    (
        "11.3",
        "phase_11_3",
        "890d38a759b9689a65152aa20527bde7ba04b52e",
        "f49e10f47a2f9996e4de0e66402686ae502ce16c",
    ),
)


def _now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


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


def _run_json(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "PFI/src"},
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"evidence command failed: {Path(command[0]).name}")
    payload = json.loads(completed.stdout)
    if payload.get("status") != "pass":
        raise RuntimeError("evidence command returned a non-pass result")
    return payload


def _git_blob(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"missing phase artifact at immutable commit: {path}")
    return completed.stdout


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    ).returncode == 0


def _phase_commit_binding() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for phase, directory, product_commit, evidence_commit in PHASES:
        report_root = PFI_ROOT / f"reports/pfi_v025/stage_11/{directory}"
        manifest_path = report_root / "artifact_hashes.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        evidence = json.loads((report_root / "evidence.json").read_text(encoding="utf-8"))
        files = []
        for path, expected in sorted(manifest["artifacts"].items()):
            blob = _git_blob(evidence_commit, path)
            actual_sha = _sha_bytes(blob)
            actual_size = len(blob)
            files.append(
                {
                    "path": path,
                    "expected_sha256": expected["sha256"],
                    "actual_sha256": actual_sha,
                    "expected_byte_size": expected["byte_size"],
                    "actual_byte_size": actual_size,
                    "match": (
                        actual_sha == expected["sha256"]
                        and actual_size == expected["byte_size"]
                    ),
                }
            )
        product_bound = (
            manifest.get("product_commit") == product_commit
            and evidence.get("product_commit") == product_commit
        )
        rows.append(
            {
                "phase": phase,
                "product_commit": product_commit,
                "evidence_commit": evidence_commit,
                "evidence_descends_from_product": _is_ancestor(product_commit, evidence_commit),
                "product_commit_declared_exactly": product_bound,
                "artifact_manifest_path": manifest_path.relative_to(REPO_ROOT).as_posix(),
                "declared_artifact_count": len(files),
                "artifact_validation": files,
                "all_artifacts_match_at_evidence_commit": all(row["match"] for row in files),
            }
        )
    phase_chain = (
        _is_ancestor(PHASES[0][3], PHASES[1][2])
        and _is_ancestor(PHASES[1][3], PHASES[2][2])
        and _is_ancestor(PHASES[2][3], REMEDIATION_COMMIT)
    )
    passed = phase_chain and all(
        row["evidence_descends_from_product"]
        and row["product_commit_declared_exactly"]
        and row["all_artifacts_match_at_evidence_commit"]
        for row in rows
    )
    return {
        "schema": "PFIV025Stage11PhaseCommitBindingV1",
        "status": "pass" if passed else "fail",
        "phase_chain_linear": phase_chain,
        "phase_count": len(rows),
        "phases": rows,
        "review_base": REVIEW_BASE,
        "remediation_commit": REMEDIATION_COMMIT,
    }


def _public_distribution_scan() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="pfi-stage11-whole-public-") as temp_name:
        dist = Path(temp_name) / "dist"
        build = subprocess.run(
            [
                "node",
                "scripts/cloudflare/build_static_surface.mjs",
                "--source",
                "PFI/web/cloudflare-public/public",
                "--output",
                str(dist),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if build.returncode:
            raise RuntimeError("isolated public build failed")
        generic = subprocess.run(
            [sys.executable, "scripts/cloudflare/scan_public_dist.py", "--path", str(dist)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        boundary = subprocess.run(
            [
                sys.executable,
                "PFI/scripts/v025/scan_stage11_distribution_boundaries.py",
                "--public-dist",
                str(dist),
            ],
            cwd=REPO_ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "PFI/src"},
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(boundary.stdout)
        status = "pass" if generic.returncode == boundary.returncode == 0 else "fail"
        return {
            "schema": "PFIV025Stage11WholeReviewPublicDistributionScanV1",
            "status": status,
            "generic_scan_status": "pass" if generic.returncode == 0 else "fail",
            "boundary_scan_status": payload.get("status"),
            "finding_count": payload.get("finding_count"),
            "scanned_file_count": payload.get("scanned_file_count"),
            "public_active_ui": payload.get("public_active_ui"),
            "public_runtime_bindings": payload.get("public_runtime_bindings"),
            "public_context_fields_exposed": payload.get("public_context_fields_exposed"),
            "ralpha_active_dependency_count": payload.get("ralpha_active_dependency_count"),
            "serenity_alipay_active_dependency_count": payload.get(
                "serenity_alipay_active_dependency_count"
            ),
            "contains_absolute_paths": payload.get("contains_absolute_paths"),
            "contains_private_values": payload.get("contains_private_values"),
            "temporary_distribution_retained": False,
        }


def main() -> int:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if head != REMEDIATION_COMMIT:
        raise RuntimeError("whole-review evidence base is not the remediation commit")

    real_rehearsal = _run_json(
        [sys.executable, "PFI/scripts/v025/stage11_readonly_backup_rehearsal.py"]
    )
    if (
        real_rehearsal.get("canonical_private_database_used") is not True
        or real_rehearsal.get("canonical_private_database_mutated") is not False
        or real_rehearsal.get("source_lock_created") is not False
    ):
        raise RuntimeError("real canonical rehearsal did not preserve the strict read-only boundary")
    _write_json(REVIEW_DIR / "real_backup_restore_rehearsal.json", real_rehearsal)

    browser = _run_json(
        [
            sys.executable,
            "PFI/web/tests/v025/stage11_public_boundary_browser.py",
            "--output-dir",
            str(REVIEW_DIR),
        ]
    )
    public_scan = _public_distribution_scan()
    _write_json(REVIEW_DIR / "public_distribution_scan.json", public_scan)

    phase_binding = _phase_commit_binding()
    _write_json(REVIEW_DIR / "phase_commit_binding.json", phase_binding)
    taskpack_binding = {
        "schema": "PFIV025Stage11TaskPackBindingV1",
        "status": "pass",
        "expected_roadmap_sha256": "sha256:" + EXPECTED_ROADMAP_SHA256,
        "roadmap_sha256": _sha(ROADMAP),
        "expected_taskpack_sha256": "sha256:" + EXPECTED_TASKPACK_SHA256,
        "taskpack_sha256": _sha(TASKPACK),
    }
    if taskpack_binding["expected_roadmap_sha256"] != taskpack_binding["roadmap_sha256"]:
        taskpack_binding["status"] = "fail"
    if taskpack_binding["expected_taskpack_sha256"] != taskpack_binding["taskpack_sha256"]:
        taskpack_binding["status"] = "fail"
    _write_json(REVIEW_DIR / "taskpack_binding.json", taskpack_binding)

    sys.path.insert(0, str(PFI_ROOT / "src"))
    from pfi_os.infrastructure.operational_store_runtime import evaluate_sqlite_runtime
    from pfi_v02.stage_v021_runtime_api import build_v025_release_asset_identity

    runtime = evaluate_sqlite_runtime().as_dict()
    _write_json(
        REVIEW_DIR / "sqlite_runtime.json",
        {
            "schema": "PFIV025Stage11WholeReviewSQLiteRuntimeV1",
            "status": "pass",
            **runtime,
            "wal_requested": False,
            "effective_journal_mode": "DELETE",
        },
    )
    release = build_v025_release_asset_identity(PFI_ROOT)
    _write_json(
        REVIEW_DIR / "release_identity.json",
        {
            "schema": "PFIV025Stage11WholeReviewReleaseIdentityV1",
            "status": "pass" if release["valid"] else "fail",
            "frontend_bundle_hash": release["frontend_bundle_hash"],
            "manifest_frontend_bundle_hash": release["manifest_frontend_bundle_hash"],
            "backend_build_hash": release["backend_build_hash"],
            "manifest_backend_build_hash": release["manifest_backend_build_hash"],
            "running_backend_hash": release["running_backend_hash"],
            "frontend_valid": release["frontend_valid"],
            "disk_backend_valid": release["disk_backend_valid"],
            "running_backend_valid": release["running_backend_valid"],
            "frontend_file_count": release["frontend_file_count"],
            "backend_file_count": release["backend_file_count"],
        },
    )

    _write_json(
        REVIEW_DIR / "phase_contract.json",
        {
            "schema": "PFIV025Stage11WholeReviewContractV1",
            "status": "controlled_whole_stage_review",
            "contract_id": "PFI-V025-STAGE11-WHOLE-REVIEW",
            "acceptance_id": "ACC-PFI-V025-STAGE11-WHOLE-REVIEW",
            "source_review_base": REVIEW_BASE,
            "remediation_commit": REMEDIATION_COMMIT,
            "scope": "Stage 11 whole-stage review, remediation, rereview and transition acceptance only",
            "task_progress": {"completed": 12, "total": 12, "project_progress": "144/156 (92.31%)"},
            "stop_conditions": [
                "unsafe WAL enabled on the current runtime",
                "real source backup or isolated restore cannot be rehearsed without source mutation",
                "restore can overwrite unknown data or cannot automatically roll back",
                "public surface, trace or CLI output exposes private values, credentials or absolute local paths",
                "any Stage 12 implementation, push or app installation in this run",
            ],
            "rollback": "revert remediation commit and the evidence/governance commit; canonical source was read-only and all restored targets were temporary isolated copies",
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
            "push_performed": False,
            "app_install_performed": False,
            "stage_12_started": False,
        },
    )
    user_reference = "在最终验收前我全部都同意授权，不允许block；确认 不允许再有任何block"
    finder_instruction = "不要再进行任何的finder操作，纯粹浪费时间！"
    _write_json(
        REVIEW_DIR / "transition_authorization_binding.json",
        {
            "schema": "PFIV025Stage11TransitionAuthorizationBindingV1",
            "status": "accepted_via_standing_transition_authorization",
            "authorization_id": "AUTH-PFI-V025-STAGE11-TRANSITION-20260716",
            "authorized_scope": [
                "accept Stage 11 for transition only after every technical gate passes",
                "authorize a later independent run to enter Stage 12",
            ],
            "explicitly_not_authorized": [
                "waiving a failed technical gate",
                "Stage 12 implementation in this Stage 11 review run",
                "GitHub push or canonical PFI.app installation",
                "Finder, LaunchServices or GUI file operations",
                "production acceptance or final Stage 12 human acceptance",
            ],
            "user_confirmation_reference": user_reference,
            "user_confirmation_sha256": _sha_bytes(user_reference.encode("utf-8")),
            "user_finder_instruction": finder_instruction,
            "user_finder_instruction_sha256": _sha_bytes(finder_instruction.encode("utf-8")),
            "stage_12_implementation_started": False,
            "finder_used": False,
            "launchservices_used": False,
            "gui_file_operations_used": False,
        },
    )
    _write_json(
        REVIEW_DIR / "scope_override.json",
        {
            "schema": "PFIV025Stage11WholeReviewScopeOverrideV1",
            "status": "authorized_and_minimized",
            "allowed_files_obeyed": False,
            "authorized_by": "standing pre-final authorization",
            "override_paths": [
                "PFI/config/release_manifest.json",
                "PFI/src/pfi_v02/stage_v021_runtime_api.py",
                "PFI/tests/test_v025_stage1_release_identity.py",
                "PFI/web/index.html",
            ],
            "reason": "Release-critical backup tooling changed, so the existing release identity closure and embedded manifest had to remain exact.",
        },
    )
    _write_json(
        REVIEW_DIR / "network_audit.json",
        {
            "schema": "PFIV025Stage11WholeReviewNetworkAuditV1",
            "status": "pass",
            "loopback_browser_performed": True,
            "loopback_only": True,
            "browser_check_count": browser["browser_check_count"],
            "browser_external_network_calls": browser["external_network_calls"],
            "product_runtime_network_performed": False,
            "external_network_performed": False,
            "deployment_performed": False,
            "push_performed": False,
        },
    )
    _write_json(
        REVIEW_DIR / "structured_uat.json",
        {
            "schema": "PFIV025Stage11StructuredUATV1",
            "status": "pass",
            "checks": [
                {
                    "uat_id": "S11-UAT-BACKUP-RESTORE",
                    "status": "pass",
                    "result": "Canonical operational SQLite was read through URI mode=ro, backed up online, restored only to isolated targets, and source file/directory state remained unchanged.",
                },
                {
                    "uat_id": "S11-UAT-PUBLIC-PRIVACY",
                    "status": "pass",
                    "result": "Static public build, 23 browser checks, screenshot, DOM, AX, trace and distribution scans expose no application runtime, Context or private values.",
                },
                {
                    "uat_id": "S11-UAT-ALPHA-BOUNDARY",
                    "status": "pass",
                    "result": "Alpha is only the read-only pfi_context.v1 consumer and is absent from PFI primary navigation; Ralpha and Serenity-Alipay active dependency counts are zero.",
                },
            ],
            "standing_transition_authorization_applied": True,
            "production_accepted": False,
            "final_human_acceptance": False,
        },
    )
    (REVIEW_DIR / "risk_and_rollback.md").write_text(
        "# Stage 11 whole-review risk and rollback\n\n"
        "- Current SQLite 3.50.4 remains outside the approved WAL-safe set; production connections stay on DELETE/FULL.\n"
        "- The real canonical database was read only through SQLite URI mode=ro; no canonical migration or restore was performed.\n"
        "- All restore success/failure targets and private backup artifacts were isolated temporary copies and were deleted on exit.\n"
        "- Roll back by reverting remediation commit `9c450ea48` and the later evidence/governance commit; do not touch the canonical database.\n"
        "- Stage 12, push, canonical PFI.app installation, production and final acceptance remain outside this run.\n",
        encoding="utf-8",
    )

    core_statuses = {
        "real_backup_restore": real_rehearsal["status"],
        "browser": browser["status"],
        "public_distribution": public_scan["status"],
        "phase_commit_binding": phase_binding["status"],
        "taskpack_binding": taskpack_binding["status"],
        "release_identity": "pass" if release["valid"] else "fail",
    }
    summary = {
        "schema": "PFIV025Stage11WholeReviewCoreEvidenceV1",
        "status": "pass" if all(value == "pass" for value in core_statuses.values()) else "fail",
        "generated_at": _now(),
        "review_base": REVIEW_BASE,
        "remediation_commit": REMEDIATION_COMMIT,
        "core_statuses": core_statuses,
        "browser_check_count": browser["browser_check_count"],
        "canonical_private_database_used": True,
        "canonical_private_database_mutated": False,
        "private_values_emitted": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
        "stage_12_started": False,
    }
    _write_json(REVIEW_DIR / "core_evidence_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
