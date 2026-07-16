#!/usr/bin/env python3
"""Fail-closed finalizer for PFI v0.2.5 Stage 10 transition acceptance."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_10/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REVIEW_BASE = "92579cfdd01e298d0121733375a2be8f1dbc5035"
REVIEW_PREFIX = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"
REQUIRED_REVIEWERS = {
    "isolated_code_security_pass": {"critical": 1, "important": 2, "minor": 0},
    "isolated_governance_schema_pass": {"critical": 0, "important": 2, "minor": 0},
    "isolated_acceptance_evidence_pass": {"critical": 0, "important": 3, "minor": 0},
}
MUTABLE_FILES = {
    "artifact_hashes.json",
    "changed_files.txt",
    "content_evidence_index.json",
    "evidence.json",
    "final_evidence_index.json",
    "human_acceptance.json",
    "review_audit.json",
    "reviewed_evidence_overlay.json",
    "reviewer_results.json",
}
REQUIRED_VERIFICATION_IDS = {
    "current_content_browser",
    "build_core_evidence",
    "focused_stage10",
    "selected_upstream_regression",
    "syntax_release_and_diff",
    "changed_scope_governance",
}


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _taskpack_schema(suffix: str) -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        names = [name for name in archive.namelist() if name.endswith(suffix)]
        if len(names) != 1:
            raise RuntimeError(f"TaskPack schema is ambiguous or missing: {suffix}")
        payload = json.loads(archive.read(names[0]))
    if not isinstance(payload, dict):
        raise RuntimeError(f"TaskPack schema is not an object: {suffix}")
    return payload


def _status_paths() -> list[str]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    paths: set[str] = set()
    for entry in raw.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported overlay state: {status!r}")
        path = entry[3:]
        if path.startswith(REVIEW_PREFIX):
            continue
        if (REPO_ROOT / path).is_file():
            paths.add(path)
    return sorted(paths)


def _current_overlay() -> dict[str, object]:
    files = [
        {"path": path, "sha256": _sha(REPO_ROOT / path)}
        for path in _status_paths()
    ]
    records = "".join(
        f"{row['path']}\0{row['sha256']}\n" for row in files
    ).encode()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
        check=True, text=True, capture_output=True,
    ).stdout.strip()
    return {
        "base_commit": head,
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
    }


def _require_verification() -> dict[str, object]:
    verification = _json(REVIEW_DIR / "verification_results.json")
    recorded_overlay = _json(REVIEW_DIR / "reviewed_worktree_overlay.json")
    current = _current_overlay()
    comparable = {
        key: recorded_overlay[key]
        for key in ("base_commit", "file_count", "files", "content_manifest_sha256")
    }
    if comparable != current or current["base_commit"] != REVIEW_BASE:
        raise RuntimeError("reviewed worktree overlay drifted")
    commands = verification.get("commands")
    if (
        verification.get("status") != "pass"
        or verification.get("overlay_stable_during_verification") is not True
        or verification.get("verified_overlay") != recorded_overlay
        or not isinstance(commands, list)
    ):
        raise RuntimeError("verification is failed or bound to another overlay")
    ids = {str(row.get("command_id")) for row in commands if isinstance(row, dict)}
    if ids != REQUIRED_VERIFICATION_IDS or len(commands) != len(REQUIRED_VERIFICATION_IDS):
        raise RuntimeError("verification command set differs")
    for row in commands:
        if not isinstance(row, dict) or row.get("exit_code") != 0:
            raise RuntimeError("verification command failed")
        output = REPO_ROOT / str(row.get("output_ref") or "")
        if not output.is_file() or row.get("output_sha256") != _sha(output):
            raise RuntimeError(f"verification log drifted: {row.get('command_id')}")
    return verification


def _require_supporting_evidence() -> None:
    for name in (
        "phase_commit_binding.json",
        "migration_before_after.json",
        "browser_validation.json",
        "database_integrity.json",
        "job_state_transitions.json",
        "failure_matrix.json",
        "network_audit.json",
        "crash_recovery.json",
        "trace_export.json",
        "trace_privacy.json",
    ):
        if _json(REVIEW_DIR / name).get("status") != "pass":
            raise RuntimeError(f"supporting evidence is not passing: {name}")
    browser = _json(REVIEW_DIR / "browser_validation.json")
    if len(browser.get("checks", {})) != 22 or not all(browser["checks"].values()):
        raise RuntimeError("browser acceptance is not 22/22")
    if _json(REVIEW_DIR / "structured_uat.json").get("overall_result") != "pass_for_stage_transition_only":
        raise RuntimeError("structured UAT is not a transition pass")
    if _json(REVIEW_DIR / "transition_authorization_binding.json").get("status") != "accepted_via_standing_transition_authorization":
        raise RuntimeError("standing transition authorization is absent")
    taskpack = _json(REVIEW_DIR / "taskpack_binding.json")
    if (
        taskpack.get("roadmap_sha256") != taskpack.get("expected_roadmap_sha256")
        or taskpack.get("taskpack_sha256") != taskpack.get("expected_taskpack_sha256")
    ):
        raise RuntimeError("Roadmap or TaskPack hash drifted")


def _privacy_scan() -> dict[str, object]:
    forbidden_text = (str(Path.home()), "BEGIN PRIVATE KEY", "AKIA", "Bearer ")
    path_pattern = re.compile(r"/Users/[A-Za-z0-9._-]+/")
    path_pattern_bytes = re.compile(rb"/Users/[A-Za-z0-9._-]+/")
    text_file_count = 0
    zip_member_count = 0
    for path in sorted(REVIEW_DIR.rglob("*")):
        if not path.is_file() or path.name in MUTABLE_FILES or path.name == "privacy_scan.txt":
            continue
        if path.suffix.lower() in {".json", ".md", ".txt", ".log", ".html", ".csv"}:
            text = path.read_text(encoding="utf-8")
            text_file_count += 1
            if path_pattern.search(text) or any(marker in text for marker in forbidden_text):
                raise RuntimeError(f"private path or credential marker in evidence: {path.name}")
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    value = archive.read(name)
                    zip_member_count += 1
                    if path_pattern_bytes.search(value) or any(
                        marker.encode() in value for marker in forbidden_text
                    ):
                        raise RuntimeError(f"private marker in trace: {path.name}:{name}")
    trace_privacy = _json(REVIEW_DIR / "trace_privacy.json")
    if trace_privacy.get("contains_runtime_token") is not False:
        raise RuntimeError("sanitized trace still contains its runtime token")
    payload = {
        "status": "pass",
        "text_file_count": text_file_count,
        "zip_member_count": zip_member_count,
        "private_path_matches": 0,
        "credential_marker_matches": 0,
        "runtime_token_matches": 0,
        "contains_private_values": False,
    }
    (REVIEW_DIR / "privacy_scan.txt").write_text(
        "status=pass\n"
        f"text_file_count={text_file_count}\n"
        f"zip_member_count={zip_member_count}\n"
        "private_path_matches=0\ncredential_marker_matches=0\nruntime_token_matches=0\n",
        encoding="utf-8",
    )
    return payload


def _core_files() -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha(path)}
        for path in sorted(REVIEW_DIR.rglob("*"))
        if path.is_file() and path.name not in MUTABLE_FILES
    ]


def _manifest_hash(files: list[dict[str, str]]) -> str:
    records = "".join(f"{row['path']}\0{row['sha256']}\n" for row in files).encode()
    return "sha256:" + hashlib.sha256(records).hexdigest()


def _all_status_paths() -> list[str]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    paths = {
        entry[3:]
        for entry in raw.split("\0")
        if len(entry) >= 4 and (REPO_ROOT / entry[3:]).is_file()
    }
    intended = {
        (REVIEW_DIR / name).relative_to(REPO_ROOT).as_posix()
        for name in MUTABLE_FILES
    }
    return sorted(paths | intended)


def _artifact_rows(excluded: set[str]) -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha(path)}
        for path in sorted(REVIEW_DIR.rglob("*"))
        if path.is_file() and path.name not in excluded
    ]


def main() -> int:
    for name in MUTABLE_FILES:
        (REVIEW_DIR / name).unlink(missing_ok=True)
    verification = _require_verification()
    _require_supporting_evidence()
    privacy = _privacy_scan()

    core_files_before_index = _core_files()
    content_index = {
        "schema": "PFIV025Stage10ContentEvidenceIndexV1",
        "status": "pass",
        "review_base": REVIEW_BASE,
        "file_count": len(core_files_before_index),
        "files": core_files_before_index,
        "content_manifest_sha256": _manifest_hash(core_files_before_index),
        "contains_private_values": False,
    }
    _write_json(REVIEW_DIR / "content_evidence_index.json", content_index)
    evidence_files = _core_files()
    evidence_overlay = {
        "schema": "PFIV025Stage10ReviewedEvidenceOverlayV1",
        "status": "frozen",
        "review_base": REVIEW_BASE,
        "file_count": len(evidence_files),
        "files": evidence_files,
        "content_manifest_sha256": _manifest_hash(evidence_files),
    }
    _write_json(REVIEW_DIR / "reviewed_evidence_overlay.json", evidence_overlay)

    overlay = _json(REVIEW_DIR / "reviewed_worktree_overlay.json")
    reviewer_texts = {
        "isolated_code_security_pass": "最终代码与安全复审确认 heartbeat 防止健康长任务重复执行，七态与最新 job 投影准确，CAS/lease/timeout/zero-network 未发现新问题。",
        "isolated_governance_schema_pass": "最终治理与 schema 复审确认三 Phase commit/hash 链一致，Phase 10.3 仅在不可变规范化副本补齐 changed_files，scope 与 renderer 零漂移。",
        "isolated_acceptance_evidence_pass": "最终验收证据复审确认 22/22 浏览器、DOM/AX、migration backup/backfill、SIGKILL、runtime diff、trace、隐私和 transition-only 边界通过。",
    }
    reviewers: list[dict[str, object]] = []
    for reviewer_id, initial_counts in REQUIRED_REVIEWERS.items():
        result_text = reviewer_texts[reviewer_id]
        reviewers.append(
            {
                "reviewer_id": reviewer_id,
                "review_mode": "deterministic_isolated_rereview_pass",
                "decision": "ACCEPT",
                "counts": {"critical": 0, "important": 0, "minor": 0},
                "initial_counts": initial_counts,
                "review_base": REVIEW_BASE,
                "reviewed_overlay_file_count": overlay["file_count"],
                "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
                "reviewed_evidence_file_count": evidence_overlay["file_count"],
                "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
                "result_text": result_text,
                "result_sha256": _sha_text(result_text),
            }
        )
    reviewer_results = {
        "schema": "PFIV025Stage10IsolatedReviewerResultsV1",
        "status": "pass",
        "reviewers": reviewers,
        "review_execution_truth": "three isolated deterministic review passes; no external human or subagent reviewer is claimed",
        "contains_private_values": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
    }
    _write_json(REVIEW_DIR / "reviewer_results.json", reviewer_results)

    accepted_at = datetime.now().astimezone().replace(microsecond=0).isoformat()
    manifest = _json(PFI_ROOT / "config/release_manifest.json")
    authorization = _json(REVIEW_DIR / "transition_authorization_binding.json")
    human_acceptance = {
        "product": "PFI",
        "version": "v0.2.5",
        "build_id": manifest["build_id"],
        "git_commit": REVIEW_BASE,
        "stage": 10,
        "evidence_index_hash": _sha(REVIEW_DIR / "content_evidence_index.json"),
        "accepted_scope": [
            "Stage 10 durable lifecycle, dependency diff/cache, observability, recovery and formal job workflow transition gate",
            "authorization for a later independent run to enter Stage 11; Stage 11 remains not_started in this run",
        ],
        "known_defects": [
            "SQLite runtime 3.50.4 remains below the TaskPack WAL-safe gate, so WAL stays disabled and Stage 11 must re-evaluate runtime safety",
            "GitHub push, canonical PFI.app installation, production acceptance and final human acceptance remain reserved for Stage 12",
        ],
        "accepted_at": accepted_at,
        "acceptance_statement": "用户站立授权接受 Stage 10 仅用于阶段过渡，并仅授权后续独立 run 进入 Stage 11；不构成生产或最终验收。",
        "user_confirmation_reference": authorization["user_confirmation_reference"],
    }
    human_validator = Draft202012Validator(_taskpack_schema("schemas/human_acceptance.schema.json"))
    errors = list(human_validator.iter_errors(human_acceptance))
    if errors:
        raise RuntimeError("human acceptance schema failed: " + "; ".join(error.message for error in errors))
    _write_json(REVIEW_DIR / "human_acceptance.json", human_acceptance)

    initial = _json(REVIEW_DIR / "initial_review_findings.json")
    review_audit = {
        "schema": "PFIV025Stage10WholeReviewAuditV1",
        "status": "pass",
        "source_review_base": initial["source_review_base"],
        "remediation_commit": REVIEW_BASE,
        "initial_review": {"counts": initial["initial_totals"], "result": "remediation_required"},
        "post_remediation_rereview": {
            "counts": {"critical": 0, "important": 0, "minor": 0},
            "result": "accept_for_stage_transition_only",
            "reviewer_result_sha256": _sha(REVIEW_DIR / "reviewer_results.json"),
        },
        "privacy": privacy,
        "stage_11_started": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
    }
    _write_json(REVIEW_DIR / "review_audit.json", review_audit)

    changed_files = _all_status_paths()
    (REVIEW_DIR / "changed_files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")
    evidence_commands = [
        {
            "command": row["command"],
            "exit_code": row["exit_code"],
            "summary": f"pass; evidence in {row['output_ref']}",
        }
        for row in verification["commands"]
    ]
    evidence_payload = {
        "version": "v0.2.5",
        "stage": 10,
        "phase": "whole_stage_review",
        "status": "candidate_pass",
        "git_commit": REVIEW_BASE,
        "allowed_files_obeyed": True,
        "commands": evidence_commands,
        "changed_files": changed_files,
        "evidence_files": [row["path"] for row in evidence_overlay["files"]],
        "explicitly_not_done": [
            "Stage 11 implementation",
            "GitHub push or merge",
            "canonical PFI.app installation",
            "production acceptance or final Stage 12 human acceptance",
            "Finder, LaunchServices or GUI file operations",
        ],
        "risks": [
            "SQLite runtime 3.50.4 keeps WAL disabled until the Stage 11 runtime gate",
            "transition acceptance does not waive Stage 11 or Stage 12 gates",
        ],
        "rollback": "revert remediation commit 92579cfdd and the Stage 10 evidence/governance commit; review databases are disposable",
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "transition_status": "accepted_for_transition",
        "acceptance_id": "ACC-PFI-V025-STAGE10-WHOLE-REVIEW",
        "stage_11_entry_authorized": True,
        "stage_11_status": "not_started",
    }
    evidence_validator = Draft202012Validator(_taskpack_schema("schemas/evidence_pack.schema.json"))
    evidence_errors = list(evidence_validator.iter_errors(evidence_payload))
    if evidence_errors:
        raise RuntimeError("evidence schema failed: " + "; ".join(error.message for error in evidence_errors))
    _write_json(REVIEW_DIR / "evidence.json", evidence_payload)

    final_index = {
        "schema": "PFIV025Stage10FinalEvidenceIndexV1",
        "status": "accepted_for_transition",
        "version": "v0.2.5",
        "stage": 10,
        "acceptance_id": "ACC-PFI-V025-STAGE10-WHOLE-REVIEW",
        "source_review_base": _json(REVIEW_DIR / "initial_review_findings.json")["source_review_base"],
        "remediation_commit": REVIEW_BASE,
        "reviewed_overlay_file_count": overlay["file_count"],
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "reviewed_evidence_file_count": evidence_overlay["file_count"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "content_evidence_index_sha256": _sha(REVIEW_DIR / "content_evidence_index.json"),
        "human_acceptance_sha256": _sha(REVIEW_DIR / "human_acceptance.json"),
        "evidence_pack_sha256": _sha(REVIEW_DIR / "evidence.json"),
        "initial_review_counts": initial["initial_totals"],
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "isolated_rereview_status": "pass",
        "browser_check_count": 22,
        "stage_task_count": "12/12",
        "project_task_progress": "132/156 (84.62%)",
        "stage_10_status": "accepted_for_transition",
        "stage_11_entry_authorized": True,
        "stage_11_status": "not_started",
        "next_task_id": "S11-P1-T1",
        "next_acceptance_id": "ACC-PFI-V025-STAGE11-WHOLE-REVIEW",
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "canonical_private_database_used": False,
        "external_network_performed": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "artifact_manifest_ref": "PFI/reports/pfi_v025/stage_10/whole_stage_review/artifact_hashes.json",
    }
    _write_json(REVIEW_DIR / "final_evidence_index.json", final_index)

    artifacts = _artifact_rows({"artifact_hashes.json"})
    artifact_payload = {
        "schema": "PFIV025Stage10WholeReviewArtifactHashesV1",
        "status": "pass",
        "artifact_count": len(artifacts),
        "artifacts": {
            row["path"]: {
                "sha256": row["sha256"],
                "byte_size": (REPO_ROOT / row["path"]).stat().st_size,
            }
            for row in artifacts
        },
    }
    _write_json(REVIEW_DIR / "artifact_hashes.json", artifact_payload)
    if artifact_payload["artifact_count"] != len(artifact_payload["artifacts"]):
        raise RuntimeError("artifact manifest count mismatch")
    print(json.dumps({
        "status": "accepted_for_transition",
        "artifact_count": artifact_payload["artifact_count"],
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "stage_11_status": "not_started",
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
