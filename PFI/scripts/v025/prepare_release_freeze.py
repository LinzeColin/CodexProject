#!/usr/bin/env python3
"""Prepare the Stage 12.3 release-freeze candidate without accepting or pushing it."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
from typing import Any, Sequence
import zipfile

from jsonschema import Draft202012Validator

from immutable_real_sources import (
    DEFAULT_LOCK_PATH,
    load_locked_source_objects,
)


PFI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PFI_ROOT.parent
VERSION = "v0.2.5"
STAGE = 12
PHASE = "12.3"
PHASE_ID = "V025-S12-P12.3"
TASK_IDS = ("S12-P3-T1", "S12-P3-T2", "S12-P3-T3", "S12-P3-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S12-P123-RELEASE-FREEZE-CANDIDATE"
REMEDIATION_ACCEPTANCE_ID = "ACC-PFI-V025-STAGE12-WHOLE-REVIEW-REMEDIATION"
DEFAULT_OUTPUT_DIR = PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_3"
FINAL_ACCEPTANCE = (
    PFI_ROOT / "reports/pfi_v025/stage_12/final_acceptance/human_acceptance.json"
)
TASK_PACK = (
    Path.home()
    / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
)
STATE_MARKER = "PFI-V025-STAGE12-WHOLE-REVIEW-INITIAL-REMEDIATION-REQUIRED"
EXPECTED_CURRENT_STATUS = "stage_12_whole_review_initial_remediation_required"


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _git_text(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _summary(stdout: str, stderr: str, returncode: int) -> str:
    text = "\n".join(part for part in (stdout, stderr) if part).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = lines[-1] if lines else ("pass" if returncode == 0 else "failed")
    result = re.sub(r"/(?:Users|private/var/folders|var/folders|tmp)/\S+", "[LOCAL_PATH_REDACTED]", result)
    return result[:500]


def _run(
    command: Sequence[str],
    *,
    command_id: str,
    timeout: int = 900,
    env: dict[str, str] | None = None,
) -> dict[str, object]:
    completed = subprocess.run(
        list(command),
        cwd=REPO_ROOT,
        env={**os.environ, **(env or {})},
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    row = {
        "command_id": command_id,
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "summary": _summary(completed.stdout, completed.stderr, completed.returncode),
    }
    if completed.returncode != 0:
        raise RuntimeError(f"{command_id} failed: {row['summary']}")
    return row


def _critical_evidence_inputs() -> list[Path]:
    paths: set[Path] = set()
    reports_root = PFI_ROOT / "reports/pfi_v025"
    for stage in range(12):
        stage_root = reports_root / f"stage_{stage}"
        for path in stage_root.rglob("*"):
            if path.is_file() and path.name in {
                "evidence.json",
                "final_evidence_index.json",
                "human_acceptance.json",
            }:
                paths.add(path)
        whole_evidence = stage_root / "whole_stage_review/evidence.json"
        if not whole_evidence.is_file():
            raise RuntimeError(f"Stage {stage} whole-stage evidence is missing")

    phase_files = {
        "phase_12_1": (
            "evidence.json",
            "artifact_manifest.json",
            "release_identity.json",
            "test_matrix.json",
            "browser_validation.json",
            "accessibility.json",
            "performance.json",
            "privacy_scan.txt",
        ),
        "phase_12_2": (
            "evidence.json",
            "artifact_manifest.json",
            "release_identity.json",
            "target_mac_lifecycle.json",
            "target_mac_browser.json",
            "human_task_uat.json",
            "backup_restore_result.json",
            "disk_pressure_result.json",
            "defect_register.json",
            "privacy_scan.txt",
        ),
    }
    for phase, names in phase_files.items():
        for name in names:
            path = reports_root / "stage_12" / phase / name
            if not path.is_file():
                raise RuntimeError(f"required Stage 12 evidence is missing: {phase}/{name}")
            paths.add(path)
    paths.update(
        {
            PFI_ROOT / "VERSION",
            PFI_ROOT / "config/release_manifest.json",
            DEFAULT_LOCK_PATH,
        }
    )
    review_root = reports_root / "stage_12" / "whole_stage_review"
    for relative in (
        "evidence.json",
        "initial_review_findings.json",
        "phase_commit_binding.json",
        "final_index_audit.json",
        "release_identity_audit.json",
        "entry_audit.json",
        "requirement_matrix.json",
        "artifact_manifest.json",
        "remediation/entry_quarantine.json",
    ):
        path = review_root / relative
        if not path.is_file():
            raise RuntimeError(f"required Stage 12 review evidence is missing: {relative}")
        paths.add(path)
    return sorted(paths)


def _build_final_evidence_index(
    observed_at: str, *, candidate_commit: str
) -> dict[str, object]:
    manifest = _read_json(PFI_ROOT / "config/release_manifest.json")
    rows = [
        {
            "path": _relative(path),
            "bytes": path.stat().st_size,
            "sha256": _sha(path),
        }
        for path in _critical_evidence_inputs()
    ]
    stage_counts = {
        str(stage): sum(
            row["path"].startswith(f"PFI/reports/pfi_v025/stage_{stage}/")
            for row in rows
        )
        for stage in range(13)
    }
    return {
        "schema": "PFIV025Stage12Phase123FinalEvidenceIndexV1",
        "status": "remediation_candidate_ready_for_independent_rereview",
        "product": "PFI",
        "version": VERSION,
        "build_id": manifest["build_id"],
        "release_manifest_git_commit": manifest["git_commit"],
        "candidate_git_commit": candidate_commit,
        "candidate_git_commit_semantics": "exact remediation anchor commit; later evidence/governance commits may only add non-runtime review material",
        "generated_at": observed_at,
        "acceptance_id": REMEDIATION_ACCEPTANCE_ID,
        "source_roadmap_sha256": "sha256:fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b",
        "source_taskpack_sha256": "sha256:591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2",
        "coverage": {
            "stage_0_through_11_whole_stage_evidence_present": True,
            "stage_12_phase_12_1_candidate_present": True,
            "stage_12_phase_12_2_candidate_present": True,
            "stage_12_phase_12_3_tasks_complete": "3/4",
            "stage_12_initial_whole_stage_review_present": True,
            "stage_12_review_remediation_anchor_present": True,
            "stage_12_whole_stage_review_status": "remediation_complete_waiting_independent_rereview",
            "final_human_acceptance": False,
        },
        "stage_file_counts": stage_counts,
        "file_count": len(rows),
        "files": rows,
        "index_excludes": [
            "itself and its detached SHA-256 file",
            "Phase 12.3 acceptance request and evidence to prevent circular hashing",
            "remediation closure evidence written after this index to prevent circular hashing",
            "future Stage 12 independent rereview and final human acceptance artifacts",
        ],
        "contains_private_values": False,
        "finder_used": False,
        "push_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }


def _state_consistency(
    observed_at: str, *, candidate_commit: str
) -> dict[str, object]:
    version = (PFI_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    manifest = _read_json(PFI_ROOT / "config/release_manifest.json")
    project = (PFI_ROOT / "docs/governance/project.yaml").read_text(
        encoding="utf-8"
    )
    roadmap = (PFI_ROOT / "docs/governance/roadmap.yaml").read_text(
        encoding="utf-8"
    )
    machine_status = _read_json(PFI_ROOT / "machine/facts/status.json")
    source_objects, source_attestation = load_locked_source_objects(repo_root=REPO_ROOT)
    behind, ahead = (
        int(value)
        for value in _git_text(
            "rev-list", "--left-right", "--count", "origin/main...HEAD"
        ).split()
    )
    app_plist_path = Path("/Applications/PFI.app/Contents/Info.plist")
    if not app_plist_path.is_file():
        raise RuntimeError("canonical PFI.app Info.plist is missing")
    with app_plist_path.open("rb") as handle:
        app_plist = plistlib.load(handle)
    head = _git_text("rev-parse", "HEAD")

    checks = {
        "version_file": version == VERSION,
        "release_manifest_version": manifest.get("version") == VERSION,
        "release_manifest_build": manifest.get("app_build_version") == "20260712.1",
        "project_current_status": f'current_status: "{EXPECTED_CURRENT_STATUS}"'
        in project,
        "project_phase_status": '  stage_12_phase_12_3_status: "in_progress_waiting_t4"'
        in project,
        "project_completed_task_count": "  stage_12_phase_task_count_completed: 11"
        in project,
        "project_whole_review_remediation_required": '  stage_12_whole_stage_review_status: "initial_review_remediation_required"'
        in project,
        "project_final_acceptance_false": "  final_human_acceptance: false" in project,
        "roadmap_current_phase": 'current_phase_id: "V025-S12-WHOLE-REVIEW"' in roadmap,
        "roadmap_current_task": 'current_task_id: "STAGE12-WHOLE-REVIEW-REMEDIATION"' in roadmap,
        "roadmap_phase_status": '  stage_12_phase_12_3_status: "in_progress_waiting_t4"'
        in roadmap,
        "machine_plane_version": machine_status.get("version") == VERSION,
        "machine_plane_phase": machine_status.get("phase") == "V025-S12-WHOLE-REVIEW",
        "machine_plane_task": machine_status.get("task")
        == "STAGE12-WHOLE-REVIEW-REMEDIATION",
        "readme_current_marker": STATE_MARKER
        in (PFI_ROOT / "README.md").read_text(encoding="utf-8"),
        "handoff_current_marker": STATE_MARKER
        in (PFI_ROOT / "HANDOFF.md").read_text(encoding="utf-8"),
        "human_feature_progress": "155/156 (99.36%)"
        in (PFI_ROOT / "功能清单.md").read_text(encoding="utf-8"),
        "human_ledger_progress": "155/156 (99.36%)"
        in (PFI_ROOT / "开发记录.md").read_text(encoding="utf-8"),
        "human_model_next_gate": "STAGE12-WHOLE-REVIEW"
        in (PFI_ROOT / "模型参数文件.md").read_text(encoding="utf-8"),
        "canonical_app_version": app_plist.get("CFBundleShortVersionString") == "0.2.5",
        "canonical_app_build": app_plist.get("CFBundleVersion") == "20260712.1",
        "source_lock_verified": len(source_objects) == 4
        and source_attestation.get("status") == "pass",
        "origin_main_not_ahead_of_head": behind == 0,
        "candidate_commit_is_exact_head": head == candidate_commit,
        "release_source_commit_is_ancestor": bool(
            re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("git_commit") or ""))
        )
        and subprocess.run(
            ["git", "merge-base", "--is-ancestor", str(manifest["git_commit"]), candidate_commit],
            cwd=REPO_ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0,
        "final_human_acceptance_absent": not FINAL_ACCEPTANCE.exists(),
    }
    failed = sorted(key for key, passed in checks.items() if not passed)
    payload = {
        "schema": "PFIV025Stage12Phase123StateConsistencyV1",
        "status": "pass" if not failed else "fail",
        "observed_at": observed_at,
        "checks": checks,
        "failed_checks": failed,
        "release": {
            "version": version,
            "build_id": manifest.get("build_id"),
            "app_short_version": app_plist.get("CFBundleShortVersionString"),
            "app_build_version": app_plist.get("CFBundleVersion"),
        },
        "progress": {
            "project_tasks": "155/156 (99.36%)",
            "stage_12_tasks": "11/12 (91.67%)",
            "next_task": "STAGE12-WHOLE-REVIEW-REMEDIATION",
            "pending_task": "S12-P3-T4",
        },
        "git": {
            "head": head,
            "origin_main": _git_text("rev-parse", "origin/main"),
            "ahead": ahead,
            "behind": behind,
            "candidate_commit": candidate_commit,
            "candidate_commit_exact_at_generation": head == candidate_commit,
            "candidate_commit_role": "product_and_stage12_remediation_anchor",
            "release_source_commit": manifest.get("git_commit"),
            "later_commit_policy": "only evidence and governance overlays; no runtime payload drift",
        },
        "source_lock": source_attestation,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "push_performed": False,
        "release_freeze_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    if failed:
        raise RuntimeError(f"Phase 12.3 state consistency failed: {failed}")
    return payload


def _known_defects() -> list[dict[str, object]]:
    register = _read_json(
        PFI_ROOT / "reports/pfi_v025/stage_12/phase_12_2/defect_register.json"
    )
    if register.get("open_p0_count") != 0 or register.get("open_p1_count") != 0:
        raise RuntimeError("open P0/P1 prevents release-freeze preparation")
    retained = [
        dict(row)
        for row in register["defects"]
        if row.get("defect_id") != "S12-P122-P2-NONCANONICAL-ENTRY-MISMATCH"
    ]
    retained.extend(
        [
            {
                "defect_id": "S12-WR-R03-FINDER-METHOD-OVERRIDDEN",
                "severity": "P2",
                "status": "accepted_user_method_constraint",
                "release_blocking": False,
                "disposition": "Retain CLI bundle execution and headless-browser evidence; never claim Finder execution.",
            },
            {
                "defect_id": "S12-WR-R04-AXE-CORE-NOT-AVAILABLE",
                "severity": "P2",
                "status": "accepted_substitute_evidence",
                "release_blocking": False,
                "disposition": "Retain the explicit no-axe claim and deterministic WCAG 2.2 AA, keyboard and CDP AX substitute.",
            },
            {
                "defect_id": "S12-WR-R05-HISTORICAL-STATE-TEST-DEBT",
                "severity": "P2",
                "status": "accepted_current_state_replacement_gates",
                "release_blocking": False,
                "count": 6,
                "disposition": "Retain six immutable historical-state tests as debt and require current-state replacement gates.",
            },
        ]
    )
    return retained


def _acceptance_request(
    *, observed_at: str, evidence_index_hash: str, candidate_commit: str
) -> dict[str, object]:
    manifest = _read_json(PFI_ROOT / "config/release_manifest.json")
    return {
        "schema": "PFIV025Stage12FinalHumanAcceptanceRequestV1",
        "status": "awaiting_stage12_independent_rereview_then_explicit_human_acceptance",
        "request_generated_at": observed_at,
        "acceptance_id": REMEDIATION_ACCEPTANCE_ID,
        "product": "PFI",
        "version": VERSION,
        "build_id": manifest["build_id"],
        "app_version": manifest["app_short_version"],
        "app_build": manifest["app_build_version"],
        "git_commit": candidate_commit,
        "git_commit_semantics": "exact product and Stage 12 remediation anchor; evidence-index hash binds the later non-runtime evidence overlay",
        "evidence_index_hash": evidence_index_hash,
        "evidence_index_ref": "PFI/reports/pfi_v025/stage_12/phase_12_3/final_evidence_index.json",
        "accepted_scope": [
            "PFI v0.2.5 Stage 0 through Stage 11 accepted transition evidence",
            "Stage 12 Phase 12.1 automated real E2E and regression candidate",
            "Stage 12 Phase 12.2 canonical CLI App and target-Mac resilience candidate",
            "Stage 12 Phase 12.3 exact candidate binding regenerated after initial-review remediation",
            "Stage 12 initial-review findings I01, I02 and I03 remediated, pending independent rereview",
        ],
        "known_defects": _known_defects(),
        "required_before_confirmation": [
            "independent Stage 12 post-remediation rereview passes",
            "open P0 and P1 counts remain zero",
            "version, build, exact commit and evidence-index hash still match this request",
            "the user explicitly accepts the exact reviewed release and listed known defects",
        ],
        "explicit_confirmation_required": True,
        "prior_blanket_authorization_is_not_final_acceptance": True,
        "human_acceptance_artifact_to_create_after_confirmation": "PFI/reports/pfi_v025/stage_12/final_acceptance/human_acceptance.json",
        "human_acceptance_artifact_exists": False,
        "release_freeze_performed": False,
        "push_performed": False,
        "final_reinstall_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "finder_used": False,
    }


def _changed_files() -> list[str]:
    tracked = _git_text("diff", "HEAD", "--name-only").splitlines()
    untracked = _git_text("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked + untracked))


def _provisional_evidence(
    observed_at: str, *, candidate_commit: str
) -> dict[str, object]:
    return {
        "schema": "PFIV025Stage12Phase123EvidenceV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {
            "S12-P3-T1": "candidate_complete",
            "S12-P3-T2": "candidate_complete",
            "S12-P3-T3": "candidate_complete",
            "S12-P3-T4": "waiting_whole_stage_review_then_explicit_human_acceptance",
        },
        "acceptance_id": REMEDIATION_ACCEPTANCE_ID,
        "status": "candidate_pass",
        "phase_completion_status": "3_of_4_candidate_complete_waiting_final_gate",
        "git_commit": candidate_commit,
        "git_commit_semantics": "exact product and Stage 12 remediation anchor; this evidence is a non-runtime overlay",
        "observed_at": observed_at,
        "allowed_files_obeyed": False,
        "scope_override_authorized": True,
        "scope_override_reason": "Upstream dual-plane integration and the bounded immutable-source lock repair are required to preserve current repository truth without restoring the migrated MetaDatabase tree.",
        "commands": [],
        "changed_files": _changed_files(),
        "evidence_files": [],
        "explicitly_not_done": [
            "Stage 12 independent post-remediation rereview",
            "S12-P3-T4 final release freeze",
            "final human acceptance artifact",
            "GitHub main push",
            "post-push canonical PFI.app reinstall and parity proof",
            "production acceptance",
            "v0.2.6 work",
        ],
        "risks": [
            "Actual kernel sleep/wake remains an accepted P2 limitation; only the owned-process proxy ran.",
            "SRC-HOLDINGS remains not_loaded/not_run; no holding financial pass is claimed.",
            "Finder remains prohibited; CLI-only entry quarantine is complete and must be rechecked without GUI discovery.",
            "Any runtime payload change after the exact release source commit requires a new release identity and candidate anchor.",
        ],
        "rollback": "Revert the Phase 12.3 candidate commit and upstream merge if necessary; retain the installed Phase 12.2 rollback archive. No canonical database, remote branch or final acceptance artifact is changed in this Phase.",
        "requires_user_acceptance": True,
        "open_p0_count": 0,
        "open_p1_count": 0,
        "open_p2_count": 5,
        "source_migration_lock_used": True,
        "finder_used": False,
        "open_command_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
        "canonical_database_changed": False,
        "app_install_performed": False,
        "push_performed": False,
        "release_freeze_performed": False,
        "stage_12_whole_stage_review_status": "remediation_complete_waiting_independent_rereview",
        "production_accepted": False,
        "final_human_acceptance": False,
        "contains_private_values": False,
        "requires_stage_whole_review": True,
    }


def _run_verification() -> list[dict[str, object]]:
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "PFI/src"}
    rows = [
        _run(
            [
                "PFI/.venv/bin/python",
                "-B",
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "PFI/tests/test_v025_stage1_release_identity.py",
                "PFI/tests/test_v025_stage1_cache_policy.py",
                "PFI/tests/test_v025_stage12_release_gates.py",
                "PFI/tests/test_v025_stage12_target_mac_uat.py",
                "PFI/tests/test_v025_stage12_release_freeze.py",
                "PFI/tests/test_v025_stage12_whole_review_remediation.py",
            ],
            command_id="focused_release_stage12_python",
            env=env,
        ),
        _run(
            ["node", "--test", "PFI/web/tests/v025/stage1_cache_policy.test.mjs"],
            command_id="release_cache_node",
        ),
        _run(
            [
                "PFI/.venv/bin/python",
                "-B",
                "PFI/machine/tools/check_dual_plane_ci.py",
                "--root",
                "PFI",
                "--projects",
                ".",
                "--require-projects",
            ],
            command_id="pfi_dual_plane_ci",
            env=env,
        ),
        _run(
            ["PFI/.venv/bin/python", "-B", "scripts/lean_governance.py", "check-render", "--project", "PFI"],
            command_id="pfi_lean_renderer",
            env=env,
        ),
        _run(["git", "diff", "--check"], command_id="git_diff_check"),
    ]
    from build_stage11_phase111_evidence import _complete_overlay_governance

    overlay_rows = _complete_overlay_governance()
    for index, row in enumerate(overlay_rows, start=1):
        if row.get("exit_code") != 0:
            raise RuntimeError(f"complete overlay governance check {index} failed")
        rows.append(
            {
                "command_id": f"complete_overlay_governance_{index}",
                "command": row["command"],
                "exit_code": row["exit_code"],
                "summary": row["summary"],
            }
        )
    return rows


def _privacy_scan(output_dir: Path) -> dict[str, object]:
    patterns = {
        "absolute_private_paths": re.compile(r"/(?:Users|private/var/folders|var/folders|tmp)/"),
        "financial_values": re.compile(r"\bCNY\s+-?[0-9]"),
        "raw_source_filenames": re.compile(r"alipay_20\d{6}-20\d{6}"),
        "email_addresses": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        "private_key_headers": re.compile(r"BEGIN (?:RSA |EC )?PRIVATE KEY"),
    }
    counts = {name: 0 for name in patterns}
    input_count = 0
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name in {"privacy_scan.txt", "artifact_manifest.json"}:
            continue
        if path.suffix.lower() not in {".json", ".txt", ".md", ".sha256"}:
            continue
        text = path.read_text(encoding="utf-8")
        input_count += 1
        for name, pattern in patterns.items():
            counts[name] += len(pattern.findall(text))
    status = "pass" if not any(counts.values()) else "fail"
    lines = [
        "PASS" if status == "pass" else "FAIL",
        "scanner=pfi-v025-stage12-phase123-public-evidence-scan-v1",
        f"input_count={input_count}",
        *(f"{name}={count}" for name, count in counts.items()),
        "contains_private_values=false",
        "finder_operations=0",
        "launchservices_operations=0",
        "gui_file_operations=0",
    ]
    (output_dir / "privacy_scan.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if status != "pass":
        raise RuntimeError(f"Phase 12.3 privacy scan failed: {counts}")
    return {"status": status, "counts": counts, "input_count": input_count}


def _taskpack_evidence_schema() -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        payload = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
        )
    if not isinstance(payload, dict):
        raise RuntimeError("TaskPack evidence schema is invalid")
    return payload


def run_phase123(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    candidate_commit: str | None = None,
) -> dict[str, object]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    observed_at = _now()
    exact_candidate = candidate_commit or _git_text("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", exact_candidate):
        raise RuntimeError("candidate commit must be an exact 40-character Git commit")
    head = _git_text("rev-parse", "HEAD")
    if head != exact_candidate:
        raise RuntimeError(
            "candidate commit must equal HEAD while Phase 12.3 evidence is generated"
        )
    phase_contract = {
        "schema": "PFIV025Stage12Phase123ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": PHASE,
        "task_ids": list(TASK_IDS),
        "acceptance_id": REMEDIATION_ACCEPTANCE_ID,
        "target": "exact remediation candidate ready for independent post-remediation rereview",
        "candidate_git_commit": exact_candidate,
        "candidate_git_commit_semantics": "exact product and Stage 12 remediation anchor; later commits may only add non-runtime evidence and governance overlays",
        "stop_before": [
            "independent post-remediation whole-stage rereview",
            "S12-P3-T4 release freeze",
            "explicit final human acceptance",
            "GitHub push",
            "post-push canonical App reinstall",
        ],
        "finder_prohibited": True,
    }
    _write_json(output_dir / "phase_contract.json", phase_contract)

    state = _state_consistency(observed_at, candidate_commit=exact_candidate)
    _write_json(output_dir / "state_consistency.json", state)
    _write_json(output_dir / "source_migration_lock.json", state["source_lock"])

    index = _build_final_evidence_index(
        observed_at, candidate_commit=exact_candidate
    )
    index_path = output_dir / "final_evidence_index.json"
    _write_json(index_path, index)
    index_hash = _sha(index_path)
    (output_dir / "final_evidence_index.sha256").write_text(
        f"{index_hash.removeprefix('sha256:')}  final_evidence_index.json\n",
        encoding="utf-8",
    )
    request = _acceptance_request(
        observed_at=observed_at,
        evidence_index_hash=index_hash,
        candidate_commit=exact_candidate,
    )
    _write_json(output_dir / "human_acceptance_request.json", request)

    evidence = _provisional_evidence(
        observed_at, candidate_commit=exact_candidate
    )
    _write_json(output_dir / "evidence.json", evidence)
    (output_dir / "privacy_scan.txt").write_text(
        "PENDING\nscanner=pfi-v025-stage12-phase123-public-evidence-scan-v1\n",
        encoding="utf-8",
    )
    _write_json(
        output_dir / "artifact_manifest.json",
        {
            "schema": "PFIV025Stage12Phase123ArtifactManifestV1",
            "status": "not_run",
            "files": {},
            "contains_private_values": False,
        },
    )
    commands = _run_verification()
    evidence["commands"] = commands
    evidence["changed_files"] = _changed_files()
    evidence["evidence_index_hash"] = index_hash
    evidence["acceptance_request_status"] = request["status"]
    evidence["evidence_files"] = sorted(
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "artifact_manifest.json"
    )
    Draft202012Validator(_taskpack_evidence_schema()).validate(evidence)
    _write_json(output_dir / "evidence.json", evidence)
    (output_dir / "terminal.log").write_text(
        "\n".join(
            f"{row['command_id']}|exit={row['exit_code']}|{row['summary']}"
            for row in commands
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "changed_files.txt").write_text(
        "\n".join(evidence["changed_files"]) + "\n", encoding="utf-8"
    )
    (output_dir / "risk_and_rollback.md").write_text(
        """# Phase 12.3 整阶段审查整改风险与回滚

- 本次只完成初审三个 P1 的整改、精确候选绑定和最终证据索引重建；独立复审、`S12-P3-T4` 与最终明确验收均未开始。
- 上游已迁移顶层 `MetaDatabase`；不得恢复该目录。真实源只从当前分支可达的 immutable commit 读取，并逐 blob 校验 OID、字节数与 SHA-256。
- 已知 P2 为五项：真实内核 sleep/wake 未执行、Holdings source 未加载、CLI-only 方法约束、无 axe-core 的替代证据，以及六个历史状态测试债务；P0/P1 为零。
- 旧 Downloads App 已通过 CLI 原子移动到私有隔离区并保留精确回滚命令；canonical PFI.app 未修改。
- 回滚：先按公开 receipt 的命令恢复旧 App；必要时 revert remediation anchor 与后续证据/治理提交。未改 canonical DB、remote main 或 final human acceptance。
- 停止边界：不执行独立复审、最终验收、push、最终重装或 v0.2.6；Finder/LaunchServices/open/GUI 操作始终为零。
""",
        encoding="utf-8",
    )
    privacy = _privacy_scan(output_dir)
    artifact_inputs = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "artifact_manifest.json"
    )
    bound_sources = (
        DEFAULT_LOCK_PATH,
        PFI_ROOT / "scripts/v025/immutable_real_sources.py",
        PFI_ROOT / "scripts/v025/prepare_release_freeze.py",
        PFI_ROOT / "scripts/v025/stage12_whole_review_remediation.py",
        PFI_ROOT / "scripts/v025/release_acceptance.py",
        PFI_ROOT / "scripts/v025/target_mac_uat.py",
        PFI_ROOT / "web/tests/v025/stage12_real_e2e_browser.py",
        PFI_ROOT / "tests/test_v025_stage12_release_gates.py",
        PFI_ROOT / "tests/test_v025_stage12_release_freeze.py",
        PFI_ROOT / "tests/test_v025_stage12_whole_review_remediation.py",
        PFI_ROOT / "docs/pfi_v025/stage_12/STAGE_12_WHOLE_STAGE_REVIEW_REMEDIATION.md",
    )
    artifact_manifest = {
        "schema": "PFIV025Stage12Phase123ArtifactManifestV1",
        "status": "pass",
        "files": {
            _relative(path): _sha(path)
            for path in (*artifact_inputs, *bound_sources)
        },
        "privacy_scan_status": privacy["status"],
        "contains_private_values": False,
    }
    artifact_manifest["file_count"] = len(artifact_manifest["files"])
    _write_json(output_dir / "artifact_manifest.json", artifact_manifest)
    if FINAL_ACCEPTANCE.exists():
        raise RuntimeError("final human acceptance appeared during Phase 12.3")
    return evidence
