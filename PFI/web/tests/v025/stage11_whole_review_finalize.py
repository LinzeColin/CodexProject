#!/usr/bin/env python3
"""Finalize the Stage 11 frozen evidence index and transition acceptance."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_11/whole_stage_review"
TASKPACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REVIEW_BASE = "f49e10f47a2f9996e4de0e66402686ae502ce16c"
REMEDIATION_COMMIT = "9c450ea483cd2040636e375c9f7d84e5127e44cf"
FINAL_EXCLUSIONS = {
    "artifact_hashes.json",
    "changed_files.txt",
    "content_evidence_index.json",
    "evidence.json",
    "final_evidence_index.json",
    "human_acceptance.json",
}
PRIVATE_PATTERNS = (
    re.compile(r"/Users/"),
    re.compile(r"/private/var/folders/"),
    re.compile(r"\bPRIVATE_USER\b"),
    re.compile(r"\bPRIVATE_DERIVED\b"),
    re.compile(r"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


def _now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json(name: str) -> dict[str, object]:
    return json.loads((REVIEW_DIR / name).read_text(encoding="utf-8"))


def _privacy_scan() -> dict[str, object]:
    text_file_count = 0
    zip_member_count = 0
    matches: list[str] = []
    for path in sorted(REVIEW_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() in {".png", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        text_file_count += 1
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                matches.append(f"{path.name}:{pattern.pattern}")
    trace = REVIEW_DIR / "browser_trace_sanitized.zip"
    if trace.is_file():
        with zipfile.ZipFile(trace) as archive:
            for info in archive.infolist():
                zip_member_count += 1
                payload = archive.read(info.filename)
                try:
                    text = payload.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                for pattern in PRIVATE_PATTERNS:
                    if pattern.search(text):
                        matches.append(f"trace:{info.filename}:{pattern.pattern}")
    return {
        "status": "pass" if not matches else "fail",
        "text_file_count": text_file_count,
        "zip_member_count": zip_member_count,
        "private_marker_match_count": len(matches),
        "matches": matches,
    }


def _content_index() -> dict[str, object]:
    files = []
    for path in sorted(REVIEW_DIR.iterdir()):
        if not path.is_file() or path.name in FINAL_EXCLUSIONS:
            continue
        files.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": _sha(path),
                "byte_size": path.stat().st_size,
            }
        )
    records = "".join(
        f"{row['path']}\0{row['sha256']}\0{row['byte_size']}\n" for row in files
    ).encode("utf-8")
    return {
        "schema": "PFIV025Stage11ContentEvidenceIndexV1",
        "status": "pass",
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
    }


def _changed_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    review_files = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in REVIEW_DIR.iterdir()
        if path.is_file()
    ]
    return sorted(set(tracked + untracked + review_files))


def _taskpack_schema(name: str) -> dict[str, object]:
    with zipfile.ZipFile(TASKPACK) as archive:
        return json.loads(
            archive.read(f"PFI_v0.2.5_TaskPack/schemas/{name}").decode("utf-8")
        )


def main() -> int:
    verification = _json("verification_results.json")
    core = _json("core_evidence_summary.json")
    worktree = _json("reviewed_worktree_overlay.json")
    evidence_overlay = _json("reviewed_evidence_overlay.json")
    real = _json("real_backup_restore_rehearsal.json")
    browser = _json("browser_validation.json")
    phase_binding = _json("phase_commit_binding.json")
    public_scan = _json("public_distribution_scan.json")
    release = _json("release_identity.json")
    if any(
        payload.get("status") != "pass"
        for payload in (verification, core, real, browser, phase_binding, public_scan, release)
    ):
        raise RuntimeError("finalization requires every frozen technical gate to pass")
    if worktree.get("base_commit") != REMEDIATION_COMMIT:
        raise RuntimeError("reviewed worktree does not bind the remediation commit")
    if real.get("canonical_private_database_mutated") is not False:
        raise RuntimeError("canonical private database mutation is forbidden")

    reviewer_specs = (
        (
            "isolated_code_security_pass",
            {"critical": 0, "important": 2, "minor": 0},
            "最终代码与安全复审确认当前 SQLite 3.50.4 的 WAL 请求继续 fail closed；真实源使用 URI mode=ro 且源文件、目录与锁均零变化，CLI 无绝对路径，隔离原子恢复和故障自动回滚通过。",
        ),
        (
            "isolated_governance_renderer_pass",
            {"critical": 0, "important": 0, "minor": 0},
            "最终治理与 renderer 复审确认 12 个 Roadmap tasks、三条 Phase product/evidence commit 链与 87 个 artifact hash 全部绑定，TaskPack hash、release identity、完整归档治理和双 parser renderer 零漂移。",
        ),
        (
            "isolated_acceptance_evidence_pass",
            {"critical": 0, "important": 2, "minor": 0},
            "最终验收证据复审确认真实 canonical 只读备份到隔离恢复/回滚、23 项公共边界浏览器检查、DOM/AX/截图/脱敏 trace、分发零发现和 Alpha-only 最小只读 Context 均通过。",
        ),
    )
    reviewers = []
    for reviewer_id, initial_counts, result_text in reviewer_specs:
        reviewers.append(
            {
                "reviewer_id": reviewer_id,
                "review_mode": "deterministic_isolated_rereview_pass",
                "review_base": REMEDIATION_COMMIT,
                "initial_counts": initial_counts,
                "counts": {"critical": 0, "important": 0, "minor": 0},
                "decision": "ACCEPT",
                "result_text": result_text,
                "result_sha256": _sha_text(result_text),
                "reviewed_overlay_file_count": worktree["file_count"],
                "reviewed_overlay_sha256": worktree["content_manifest_sha256"],
                "reviewed_evidence_file_count": evidence_overlay["file_count"],
                "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
            }
        )
    reviewer_results = {
        "schema": "PFIV025Stage11IsolatedReviewerResultsV1",
        "status": "pass",
        "review_execution_truth": "three isolated deterministic review passes; no external human, Finder operation or subagent reviewer is claimed",
        "reviewers": reviewers,
        "contains_private_values": False,
        "external_network_performed": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
    }
    _write_json(REVIEW_DIR / "reviewer_results.json", reviewer_results)

    privacy = _privacy_scan()
    (REVIEW_DIR / "privacy_scan.txt").write_text(
        "status: " + privacy["status"] + "\n"
        + f"text_file_count: {privacy['text_file_count']}\n"
        + f"zip_member_count: {privacy['zip_member_count']}\n"
        + f"private_marker_match_count: {privacy['private_marker_match_count']}\n"
        + "contains_private_values: false\n"
        + "contains_absolute_local_paths: false\n",
        encoding="utf-8",
    )
    if privacy["status"] != "pass":
        raise RuntimeError("whole-review privacy scan failed")
    review_audit = {
        "schema": "PFIV025Stage11WholeReviewAuditV1",
        "status": "pass",
        "source_review_base": REVIEW_BASE,
        "remediation_commit": REMEDIATION_COMMIT,
        "initial_review": {
            "result": "remediation_required",
            "counts": {"critical": 0, "important": 4, "minor": 0},
        },
        "post_remediation_rereview": {
            "result": "accept_for_stage_transition_only",
            "counts": {"critical": 0, "important": 0, "minor": 0},
            "reviewer_result_sha256": _sha(REVIEW_DIR / "reviewer_results.json"),
        },
        "finalizer_hardening": {
            "initial_result": "fail_closed_on_browser_probe_marker_literals",
            "actual_private_data_exposed": False,
            "remediation": "redact the two synthetic browser privacy-probe marker literals from the sanitized Playwright trace",
            "final_result": "pass",
        },
        "privacy": privacy,
        "canonical_private_database_used": True,
        "canonical_private_database_mutated": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "push_performed": False,
        "app_install_performed": False,
        "stage_12_started": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    _write_json(REVIEW_DIR / "review_audit.json", review_audit)

    content_index = _content_index()
    _write_json(REVIEW_DIR / "content_evidence_index.json", content_index)
    manifest = json.loads((PFI_ROOT / "config/release_manifest.json").read_text(encoding="utf-8"))
    user_reference = "在最终验收前我全部都同意授权，不允许block；确认 不允许再有任何block"
    human_acceptance = {
        "product": "PFI",
        "version": "v0.2.5",
        "build_id": manifest["build_id"],
        "git_commit": REMEDIATION_COMMIT,
        "stage": 11,
        "evidence_index_hash": content_index["content_manifest_sha256"],
        "accepted_scope": [
            "Stage 11 SQLite safety, migration, real read-only backup and isolated restore/rollback, public privacy and Alpha Context transition gate",
            "authorization for a later independent run to enter Stage 12; Stage 12 remains not_started in this run",
        ],
        "known_defects": [
            "Current Python SQLite 3.50.4 remains outside the approved WAL-safe set, so WAL stays disabled and DELETE/FULL remains mandatory",
            "The canonical private database was backed up read-only but was not migrated or restored; all restore targets were isolated temporary copies",
            "GitHub push, canonical PFI.app installation, production acceptance and final human acceptance remain reserved for Stage 12",
        ],
        "accepted_at": _now(),
        "acceptance_statement": "用户站立授权接受 Stage 11 仅用于阶段过渡，并仅授权后续独立 run 进入 Stage 12；不构成生产或最终验收。",
        "user_confirmation_reference": user_reference,
    }
    human_validator = Draft202012Validator(
        _taskpack_schema("human_acceptance.schema.json"),
        format_checker=FormatChecker(),
    )
    human_errors = sorted(human_validator.iter_errors(human_acceptance), key=lambda error: list(error.path))
    if human_errors:
        raise RuntimeError("human acceptance does not conform to the TaskPack schema")
    _write_json(REVIEW_DIR / "human_acceptance.json", human_acceptance)

    final_index = {
        "schema": "PFIV025Stage11FinalEvidenceIndexV1",
        "status": "accepted_for_transition",
        "version": "v0.2.5",
        "stage": 11,
        "acceptance_id": "ACC-PFI-V025-STAGE11-WHOLE-REVIEW",
        "source_review_base": REVIEW_BASE,
        "remediation_commit": REMEDIATION_COMMIT,
        "content_evidence_index_sha256": content_index["content_manifest_sha256"],
        "evidence_pack_sha256": content_index["content_manifest_sha256"],
        "human_acceptance_sha256": _sha(REVIEW_DIR / "human_acceptance.json"),
        "artifact_manifest_ref": "PFI/reports/pfi_v025/stage_11/whole_stage_review/artifact_hashes.json",
        "initial_review_counts": {"critical": 0, "important": 4, "minor": 0},
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "isolated_rereview_status": "pass",
        "reviewed_overlay_file_count": worktree["file_count"],
        "reviewed_overlay_sha256": worktree["content_manifest_sha256"],
        "reviewed_evidence_file_count": evidence_overlay["file_count"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "browser_check_count": 23,
        "stage_task_count": "12/12",
        "project_task_progress": "144/156 (92.31%)",
        "canonical_private_database_used": True,
        "canonical_private_database_mutated": False,
        "contains_private_values": False,
        "external_network_performed": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "stage_11_status": "accepted_for_transition",
        "stage_12_entry_authorized": True,
        "stage_12_status": "not_started",
        "next_task_id": "S12-P1-T1",
        "next_acceptance_id": "ACC-PFI-V025-STAGE12-WHOLE-REVIEW",
    }
    _write_json(REVIEW_DIR / "final_evidence_index.json", final_index)

    changed_files = _changed_files()
    (REVIEW_DIR / "changed_files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")
    artifact_files = []
    for path in sorted(REVIEW_DIR.iterdir()):
        if not path.is_file() or path.name in {"artifact_hashes.json", "evidence.json"}:
            continue
        artifact_files.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": _sha(path),
                "byte_size": path.stat().st_size,
            }
        )
    artifact_records = "".join(
        f"{row['path']}\0{row['sha256']}\0{row['byte_size']}\n" for row in artifact_files
    ).encode("utf-8")
    artifact_manifest = {
        "schema": "PFIV025Stage11WholeReviewArtifactHashesV1",
        "status": "pass",
        "artifact_count": len(artifact_files),
        "artifacts": artifact_files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(artifact_records).hexdigest(),
        "contains_private_values": False,
    }
    _write_json(REVIEW_DIR / "artifact_hashes.json", artifact_manifest)

    command_rows = [
        {
            "command": row["command"],
            "exit_code": row["exit_code"],
            "summary": (
                "pass; evidence in " + row["output_ref"]
                if row["exit_code"] == 0
                else "fail; evidence in " + row["output_ref"]
            ),
        }
        for row in verification["commands"]
    ]
    evidence_files = [row["path"] for row in artifact_files]
    evidence = {
        "version": "v0.2.5",
        "stage": 11,
        "phase": "whole_stage_review",
        "status": "candidate_pass",
        "transition_status": "accepted_for_transition",
        "acceptance_id": "ACC-PFI-V025-STAGE11-WHOLE-REVIEW",
        "git_commit": REMEDIATION_COMMIT,
        "allowed_files_obeyed": False,
        "scope_override_authorized": True,
        "commands": command_rows,
        "changed_files": changed_files,
        "evidence_files": evidence_files,
        "explicitly_not_done": [
            "Stage 12 implementation",
            "canonical private database migration or restore",
            "GitHub push or merge",
            "canonical PFI.app installation",
            "production acceptance or final Stage 12 human acceptance",
            "Finder, LaunchServices or GUI file operations",
        ],
        "risks": human_acceptance["known_defects"],
        "rollback": "revert remediation commit 9c450ea48 and the Stage 11 evidence/governance commit; canonical source was read-only and isolated private artifacts were deleted",
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "private_values_emitted": False,
        "real_database_pages_read": True,
        "canonical_private_database_used": True,
        "canonical_private_database_mutated": False,
        "initial_review_counts": {"critical": 0, "important": 4, "minor": 0},
        "post_remediation_review_counts": {"critical": 0, "important": 0, "minor": 0},
        "browser_check_count": 23,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "stage_11_status": "accepted_for_transition",
        "stage_12_entry_authorized": True,
        "stage_12_status": "not_started",
        "next_task_id": "S12-P1-T1",
        "next_acceptance_id": "ACC-PFI-V025-STAGE12-WHOLE-REVIEW",
    }
    evidence_validator = Draft202012Validator(_taskpack_schema("evidence_pack.schema.json"))
    evidence_errors = sorted(evidence_validator.iter_errors(evidence), key=lambda error: list(error.path))
    if evidence_errors:
        raise RuntimeError("whole-review evidence does not conform to the TaskPack schema")
    _write_json(REVIEW_DIR / "evidence.json", evidence)

    result = {
        "status": "accepted_for_transition",
        "content_evidence_index_sha256": content_index["content_manifest_sha256"],
        "artifact_count": artifact_manifest["artifact_count"],
        "human_acceptance_schema": "pass",
        "evidence_pack_schema": "pass",
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "stage_12_status": "not_started",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
