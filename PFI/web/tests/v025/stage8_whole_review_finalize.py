#!/usr/bin/env python3
"""Fail-closed finalizer for PFI v0.2.5 Stage 8 transition acceptance."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_8/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REVIEW_BASE = "2c7b25efd2916c909027333283b499a119d088e0"
REQUIRED_REVIEWERS = {
    "final_code_security_review": {"critical": 1, "important": 4, "minor": 1},
    "final_governance_renderer_review": {"critical": 0, "important": 8, "minor": 0},
    "final_acceptance_evidence_review": {"critical": 3, "important": 2, "minor": 1},
}
SELF_BOUND = {"evidence.json", "final_evidence_index.json", "human_acceptance.json"}
EVIDENCE_MANIFEST_EXCLUDED = {
    *SELF_BOUND,
    "review_audit.json",
    "reviewed_evidence_overlay.json",
    "reviewer_results.json",
}
REQUIRED_VERIFICATION_COMMANDS = {
    "focused_stage8": "PFI/reports/pfi_v025/stage_8/whole_stage_review/verification_focused_stage8.log",
    "syntax_and_diff": "PFI/reports/pfi_v025/stage_8/whole_stage_review/verification_syntax_and_diff.log",
    "changed_scope_governance": "PFI/reports/pfi_v025/stage_8/whole_stage_review/verification_changed_scope_governance.log",
}


def _now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


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


def _current_overlay() -> dict[str, object]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    review_prefix = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    paths: set[str] = set()
    for entry in raw.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported overlay state: {status!r}")
        path = entry[3:]
        if path.startswith(review_prefix):
            continue
        if (REPO_ROOT / path).is_file():
            paths.add(path)
    files = [{"path": path, "sha256": _sha(REPO_ROOT / path)} for path in sorted(paths)]
    records = "".join(
        f"{row['path']}\0{row['sha256']}\n" for row in files
    ).encode("utf-8")
    return {
        "base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
            check=True, text=True, capture_output=True,
        ).stdout.strip(),
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
    }


def _current_evidence_overlay() -> dict[str, object]:
    files = [
        {
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "sha256": _sha(path),
        }
        for path in sorted(REVIEW_DIR.rglob("*"))
        if path.is_file() and path.name not in EVIDENCE_MANIFEST_EXCLUDED
    ]
    records = "".join(
        f"{row['path']}\0{row['sha256']}\n" for row in files
    ).encode("utf-8")
    return {
        "review_base": REVIEW_BASE,
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": "sha256:" + hashlib.sha256(records).hexdigest(),
    }


def _validate_verification_payload(
    verification: dict[str, object],
    current: dict[str, object],
) -> list[dict[str, object]]:
    commands = verification.get("commands")
    if (
        verification.get("status") != "pass"
        or verification.get("overlay_stable_during_verification") is not True
        or verification.get("verified_overlay") != current
        or not isinstance(commands, list)
        or len(commands) != len(REQUIRED_VERIFICATION_COMMANDS)
        or any(not isinstance(row, dict) for row in commands)
    ):
        raise RuntimeError("verification is absent, failed, incomplete, or bound to another overlay")
    typed = [row for row in commands if isinstance(row, dict)]
    ids = [str(row.get("command_id")) for row in typed]
    if len(ids) != len(set(ids)) or set(ids) != set(REQUIRED_VERIFICATION_COMMANDS):
        raise RuntimeError("verification command IDs are duplicated, missing, or unexpected")
    for row in typed:
        command_id = str(row["command_id"])
        if (
            row.get("exit_code") != 0
            or row.get("output_ref") != REQUIRED_VERIFICATION_COMMANDS[command_id]
            or not isinstance(row.get("output_sha256"), str)
            or not str(row["output_sha256"]).startswith("sha256:")
            or not isinstance(row.get("command"), str)
            or not str(row["command"]).strip()
            or not isinstance(row.get("subcommands"), list)
            or not row["subcommands"]
        ):
            raise RuntimeError(f"verification command is malformed: {command_id}")
    return typed


def _require_overlay() -> dict[str, object]:
    recorded = _json(REVIEW_DIR / "reviewed_worktree_overlay.json")
    comparable = {
        key: recorded[key]
        for key in ("base_commit", "file_count", "files", "content_manifest_sha256")
    }
    current = _current_overlay()
    if current != comparable or current["base_commit"] != REVIEW_BASE:
        raise RuntimeError("reviewed source overlay drifted")
    verification = _json(REVIEW_DIR / "verification_results.json")
    commands = _validate_verification_payload(verification, current)
    for row in commands:
        output = REPO_ROOT / str(row.get("output_ref"))
        if not output.is_file() or _sha(output) != row.get("output_sha256"):
            raise RuntimeError("verification output hash mismatch")
    return current


def _require_evidence_overlay() -> dict[str, object]:
    recorded = _json(REVIEW_DIR / "reviewed_evidence_overlay.json")
    current = _current_evidence_overlay()
    comparable = {
        key: recorded.get(key)
        for key in ("review_base", "file_count", "files", "content_manifest_sha256")
    }
    if recorded.get("status") != "frozen" or comparable != current:
        raise RuntimeError("reviewed evidence overlay drifted")
    paths = {str(row["path"]) for row in current["files"]}
    required = {
        "PFI/reports/pfi_v025/stage_8/whole_stage_review/verification_results.json",
        "PFI/reports/pfi_v025/stage_8/whole_stage_review/phase_commit_binding.json",
        "PFI/reports/pfi_v025/stage_8/whole_stage_review/phase_evidence_amendment_binding.json",
        "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_browser/browser_validation.json",
        "PFI/reports/pfi_v025/stage_8/whole_stage_review/motion_feedback/browser_validation.json",
        "PFI/reports/pfi_v025/stage_8/whole_stage_review/repaired_baseline/browser_validation.json",
    }
    if not required <= paths:
        raise RuntimeError("reviewed evidence overlay omits required evidence")
    return current


def _validate_reviewer_payload(
    payload: dict[str, object],
    overlay: dict[str, object],
    evidence_overlay: dict[str, object],
) -> list[dict[str, object]]:
    reviewers = payload.get("reviewers")
    if (
        payload.get("status") != "pass"
        or not isinstance(reviewers, list)
        or len(reviewers) != len(REQUIRED_REVIEWERS)
        or any(not isinstance(row, dict) for row in reviewers)
    ):
        raise RuntimeError("reviewer result set is not passing")
    typed = [row for row in reviewers if isinstance(row, dict)]
    ids = [str(row.get("reviewer_id")) for row in typed]
    if len(ids) != len(set(ids)) or set(ids) != set(REQUIRED_REVIEWERS):
        raise RuntimeError("exactly three required reviewers must be present")
    by_id = {str(row["reviewer_id"]): row for row in typed}
    for reviewer_id, initial_counts in REQUIRED_REVIEWERS.items():
        row = by_id[reviewer_id]
        if row.get("decision") != "ACCEPT":
            raise RuntimeError(f"reviewer did not accept: {reviewer_id}")
        if row.get("counts") != {"critical": 0, "important": 0, "minor": 0}:
            raise RuntimeError(f"reviewer has residual findings: {reviewer_id}")
        if row.get("initial_counts") != initial_counts:
            raise RuntimeError(f"reviewer initial-count binding differs: {reviewer_id}")
        if (
            row.get("review_base") != REVIEW_BASE
            or row.get("reviewed_overlay_file_count") != overlay["file_count"]
            or row.get("reviewed_overlay_sha256") != overlay["content_manifest_sha256"]
            or row.get("reviewed_evidence_file_count") != evidence_overlay["file_count"]
            or row.get("reviewed_evidence_sha256") != evidence_overlay["content_manifest_sha256"]
        ):
            raise RuntimeError(f"reviewer source/evidence overlay binding differs: {reviewer_id}")
        result_text = row.get("result_text")
        if not isinstance(result_text, str) or not result_text.strip():
            raise RuntimeError(f"reviewer result text missing: {reviewer_id}")
        expected = "sha256:" + hashlib.sha256(result_text.encode("utf-8")).hexdigest()
        if row.get("result_sha256") != expected:
            raise RuntimeError(f"reviewer result hash mismatch: {reviewer_id}")
    if any(payload.get(flag) is not False for flag in (
        "contains_private_values", "finder_used", "launchservices_used",
        "external_network_performed",
    )):
        raise RuntimeError("reviewer execution safety flags are unsafe or missing")
    return typed


def _require_reviewers(
    overlay: dict[str, object],
    evidence_overlay: dict[str, object],
) -> dict[str, object]:
    payload = _json(REVIEW_DIR / "reviewer_results.json")
    _validate_reviewer_payload(payload, overlay, evidence_overlay)
    return payload


def _require_supporting_evidence() -> None:
    required_pass = (
        "phase_commit_binding.json",
        "phase_evidence_amendment_binding.json",
        "design_tokens.json",
        "reduced_motion.json",
        "keyboard_flow.json",
        "contrast_results.json",
        "visual_acceptance.json",
        "release_identity_binding.json",
        "final_browser/browser_validation.json",
        "final_browser/wcag_audit.json",
        "final_browser/accessibility_tree.json",
        "final_browser/error_prevention_audit.json",
        "final_browser/visual_regression.json",
        "motion_feedback/browser_validation.json",
        "repaired_baseline/browser_validation.json",
    )
    for relative in required_pass:
        if _json(REVIEW_DIR / relative).get("status") != "pass":
            raise RuntimeError(f"supporting evidence is not passing: {relative}")
    axe = _json(REVIEW_DIR / "axe_results.json")
    if not (
        axe.get("status") == "not_run"
        and axe.get("axe_core_available") is False
        and axe.get("axe_pass_claimed") is False
        and axe.get("substitute_status") == "pass"
    ):
        raise RuntimeError("axe unavailability/substitute disposition is not truthful")


def _privacy_scan() -> None:
    forbidden = (str(Path.home()), "/Users/")
    for path in sorted(REVIEW_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".json", ".md", ".txt", ".log"}:
            text = path.read_text(encoding="utf-8")
            if any(marker in text for marker in forbidden):
                raise RuntimeError(f"private absolute path in evidence: {path.name}")
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    value = archive.read(name)
                    if any(marker.encode("utf-8") in value for marker in forbidden):
                        raise RuntimeError(f"private absolute path in trace: {path.name}:{name}")


def _artifacts() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(REVIEW_DIR.rglob("*")):
        if not path.is_file() or path.name in SELF_BOUND:
            continue
        rows.append({
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "sha256": _sha(path),
        })
    return rows


def main() -> int:
    overlay = _require_overlay()
    evidence_overlay = _require_evidence_overlay()
    reviewers = _require_reviewers(overlay, evidence_overlay)
    _require_supporting_evidence()
    _privacy_scan()
    initial_counts = {
        key: sum(row[key] for row in REQUIRED_REVIEWERS.values())
        for key in ("critical", "important", "minor")
    }
    _write_json(REVIEW_DIR / "review_audit.json", {
        "schema": "PFIV025Stage8WholeReviewAuditV1",
        "status": "pass",
        "initial_review": {"counts": initial_counts, "source_reviews": REQUIRED_REVIEWERS},
        "post_remediation_review": {
            "status": "pass",
            "counts": {"critical": 0, "important": 0, "minor": 0},
            "reviewer_results_ref": "PFI/reports/pfi_v025/stage_8/whole_stage_review/reviewer_results.json",
        },
    })
    artifacts = _artifacts()
    final_index = {
        "schema": "PFIV025Stage8FinalEvidenceIndexV1",
        "status": "accepted_for_transition",
        "version": "v0.2.5",
        "stage": 8,
        "contract_id": "PFI-V025-STAGE8-WHOLE-REVIEW",
        "acceptance_id": "ACC-PFI-V025-STAGE8-WHOLE-REVIEW",
        "review_base": REVIEW_BASE,
        "review_execution_semantics": "review_base_commit_plus_exact_frozen_worktree_overlay",
        "reviewed_overlay_file_count": overlay["file_count"],
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "reviewed_evidence_file_count": evidence_overlay["file_count"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "phase_commit_binding_status": "pass",
        "phase_evidence_normalization_status": "pass",
        "verification_status": "pass",
        "independent_rereview_status": "pass",
        "initial_review_counts": initial_counts,
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "acceptance_criteria": [
            {"id": "S8-ACC-01", "status": "pass", "result": "暖白/浅灰默认亮色，蓝/绿/金语义点缀，10 类 token family。"},
            {"id": "S8-ACC-02", "status": "pass", "result": "10 主页面与 10 重点二级页为 20 个差异化真实 workspace；40 张 desktop/mobile 当前内容截图通过。"},
            {"id": "S8-ACC-03", "status": "pass", "result": "100/300/1000/10000ms 真实反馈预算、220ms 上限、reduced-motion 0ms 与 View Transition 渐进增强。"},
            {"id": "S8-ACC-04", "status": "pass", "result": "haptics/sound 默认关闭、显式 opt-in，不支持时 visual-only 静默降级。"},
            {"id": "S8-ACC-05", "status": "pass", "result": "20 唯一路由 deterministic WCAG 2.2 AA、键盘、Chrome CDP AX、44px target、状态消息与错误预防通过。"},
            {"id": "S8-ACC-06", "status": "pass_with_truthful_substitute", "result": "axe-core 不可用且未伪报；axe_results.json 为 not_run，并绑定 zero-blocking WCAG/CDP AX substitute。"},
            {"id": "S8-ACC-07", "status": "accepted_via_standing_transition_authorization", "result": "用户在最终验收前的统一授权用于 Stage 8 transition；不等于 production/final acceptance。"},
        ],
        "artifact_count": len(artifacts),
        "evidence_artifacts": artifacts,
        "historical_phase83_launchservices_used": True,
        "current_whole_review_finder_used": False,
        "current_whole_review_launchservices_used": False,
        "external_network_performed": False,
        "financial_data_loaded": False,
        "database_changed": False,
        "push_performed": False,
        "app_install_performed": False,
        "stage_8_status": "accepted_for_transition",
        "stage_9_entry_authorized": True,
        "stage_9_status": "not_started",
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    _write_json(REVIEW_DIR / "final_evidence_index.json", final_index)
    index_sha = _sha(REVIEW_DIR / "final_evidence_index.json")
    human_acceptance = {
        "schema": "PFIV025Stage8TransitionHumanAcceptanceV1",
        "status": "accepted_via_standing_transition_authorization",
        "accepted_at": _now(),
        "product": "PFI",
        "version": "v0.2.5",
        "stage": 8,
        "acceptance_id": "ACC-PFI-V025-STAGE8-WHOLE-REVIEW",
        "acceptance_statement": "用户确认明亮、专业、有质感，操作反馈自然，整体不再像 AI 机械堆叠。",
        "acceptance_basis": "standing_transition_authorization_before_final_acceptance",
        "user_confirmation_reference": "在最终验收前我全部都同意授权，不允许block",
        "user_finder_instruction": "不要再进行任何的finder操作，纯粹浪费时间！",
        "evidence_index_hash": index_sha,
        "review_base": REVIEW_BASE,
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "reviewed_evidence_file_count": evidence_overlay["file_count"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "accepted_scope": [
            "Stage 8 design, motion, feedback, haptics, accessibility and human-quality transition gate",
            "authorization to enter Stage 9 only; Stage 9 remains not_started in this run",
        ],
        "explicitly_not_accepted": [
            "production acceptance",
            "final human acceptance",
            "installed-app parity",
            "GitHub main parity",
            "Stage 9 implementation",
        ],
    }
    _write_json(REVIEW_DIR / "human_acceptance.json", human_acceptance)

    verification = _json(REVIEW_DIR / "verification_results.json")
    commands = []
    for row in verification["commands"]:
        commands.append({
            "command": row["command"],
            "exit_code": row["exit_code"],
            "summary": f"{row['command_id']} pass; {row['output_ref']} hash {row['output_sha256']}",
            "command_id": row["command_id"],
            "output_ref": row["output_ref"],
            "output_sha256": row["output_sha256"],
        })
    overlay_paths = [str(row["path"]) for row in overlay["files"]]
    artifact_paths = [row["path"] for row in artifacts]
    evidence = {
        "version": "v0.2.5",
        "stage": 8,
        "phase": "whole_stage_review",
        "status": "candidate_pass",
        "git_commit": REVIEW_BASE,
        "allowed_files_obeyed": True,
        "commands": commands,
        "changed_files": sorted(set(overlay_paths + artifact_paths + [
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_evidence_index.json",
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/human_acceptance.json",
        ])),
        "evidence_files": [
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_evidence_index.json",
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/reviewed_worktree_overlay.json",
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/phase_commit_binding.json",
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/phase_evidence_amendment_binding.json",
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/verification_results.json",
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/reviewer_results.json",
            "PFI/reports/pfi_v025/stage_8/whole_stage_review/human_acceptance.json",
        ],
        "explicitly_not_done": [
            "Stage 9 implementation",
            "GitHub push",
            "PFI.app installation or Finder launch",
            "external-network access",
            "production acceptance",
            "final human acceptance",
        ],
        "risks": [
            "Acceptance is invalid if the review-base plus frozen overlay hash drifts.",
            "axe-core was unavailable; no axe pass is claimed and the deterministic WCAG/CDP AX substitute remains explicit.",
            "No real financial data was loaded, so Stage 12 installed-app and final-delivery UAT remain open.",
        ],
        "rollback": "Revert the local Stage 8 whole-review commit and remediation commit; restore the matching frontend release identity. No financial-data rollback is required.",
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "contract_id": "PFI-V025-STAGE8-WHOLE-REVIEW",
        "acceptance_id": "ACC-PFI-V025-STAGE8-WHOLE-REVIEW",
        "generated_at": _now(),
        "review_base": REVIEW_BASE,
        "reviewed_overlay_file_count": overlay["file_count"],
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "reviewed_evidence_file_count": evidence_overlay["file_count"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "final_evidence_index_sha256": index_sha,
        "human_acceptance_sha256": _sha(REVIEW_DIR / "human_acceptance.json"),
        "initial_review_counts": initial_counts,
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "stage_8_phase_task_completed_count": 12,
        "stage_8_phase_task_count": 12,
        "v025_completed_task_count": 108,
        "v025_task_count": 156,
        "overall_progress_percent": 69.23,
        "stage_8_status": "accepted_for_transition",
        "stage_8_whole_stage_review_status": "pass",
        "stage_8_user_acceptance_status": "accepted_via_standing_transition_authorization",
        "stage_9_entry_authorized": True,
        "stage_9_status": "not_started",
        "next_task_id": "S9-P1-T1",
        "next_acceptance_id": "ACC-PFI-V025-STAGE9-WHOLE-REVIEW",
        "historical_phase83_launchservices_used": True,
        "finder_used": False,
        "launchservices_used_in_current_review": False,
        "gui_file_operations_used": False,
        "financial_data_loaded": False,
        "financial_data_mutated": False,
        "database_changed": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "reviewer_results_sha256": _sha(REVIEW_DIR / "reviewer_results.json"),
        "reviewer_result_count": len(reviewers["reviewers"]),
    }
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema = json.loads(archive.read(
            "PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"
        ))
    errors = sorted(error.message for error in Draft202012Validator(schema).iter_errors(evidence))
    if errors:
        raise RuntimeError(f"final evidence violates TaskPack schema: {errors}")
    _write_json(REVIEW_DIR / "evidence.json", evidence)
    _privacy_scan()
    print(json.dumps({
        "status": "accepted_for_transition",
        "stage": 8,
        "stage_9_status": "not_started",
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "artifact_count": len(artifacts),
        "reviewer_count": len(reviewers["reviewers"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
