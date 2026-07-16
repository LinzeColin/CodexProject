#!/usr/bin/env python3
"""Fail-closed finalizer for PFI v0.2.5 Stage 9 transition acceptance."""

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
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REVIEW_BASE = "45653bd4d57d3a4a8d6f025b5f624fed5f155d1e"
REQUIRED_REVIEWERS = {
    "final_code_security_review": {"critical": 0, "important": 4, "minor": 0},
    "final_governance_renderer_review": {"critical": 0, "important": 4, "minor": 2},
    "final_acceptance_evidence_review": {"critical": 2, "important": 3, "minor": 1},
}
MUTABLE_EVIDENCE_FILES = {
    "artifact_hashes.json",
    "evidence.json",
    "final_evidence_index.json",
    "human_acceptance.json",
    "review_audit.json",
    "reviewed_evidence_overlay.json",
    "reviewer_results.json",
}
SELF_BOUND = {"evidence.json", "final_evidence_index.json", "human_acceptance.json"}
REQUIRED_VERIFICATION_COMMANDS = {
    "focused_stage9": "verification_focused_stage9.log",
    "selected_upstream_regression": "verification_selected_upstream_regression.log",
    "current_content_browser": "verification_current_content_browser.log",
    "node_syntax_and_diff": "verification_node_syntax_and_diff.log",
    "pdf_privacy_and_evidence": "verification_pdf_privacy_and_evidence.log",
    "changed_scope_governance": "verification_changed_scope_governance.log",
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
        {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha(path)}
        for path in sorted(REVIEW_DIR.rglob("*"))
        if path.is_file() and path.name not in MUTABLE_EVIDENCE_FILES
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


def _require_overlay() -> dict[str, object]:
    recorded = _json(REVIEW_DIR / "reviewed_worktree_overlay.json")
    current = _current_overlay()
    comparable = {
        key: recorded[key]
        for key in ("base_commit", "file_count", "files", "content_manifest_sha256")
    }
    current_comparable = {
        key: current[key]
        for key in ("base_commit", "file_count", "files", "content_manifest_sha256")
    }
    if current_comparable != comparable or current["base_commit"] != REVIEW_BASE:
        raise RuntimeError("reviewed worktree overlay drifted")
    verification = _json(REVIEW_DIR / "verification_results.json")
    commands = verification.get("commands")
    if (
        verification.get("status") != "pass"
        or verification.get("overlay_stable_during_verification") is not True
        or verification.get("verified_overlay") != recorded
        or not isinstance(commands, list)
        or len(commands) != len(REQUIRED_VERIFICATION_COMMANDS)
        or any(not isinstance(row, dict) for row in commands)
    ):
        raise RuntimeError("verification is failed, incomplete or bound to another overlay")
    typed = [row for row in commands if isinstance(row, dict)]
    ids = [str(row.get("command_id")) for row in typed]
    if len(ids) != len(set(ids)) or set(ids) != set(REQUIRED_VERIFICATION_COMMANDS):
        raise RuntimeError("verification command set differs")
    for row in typed:
        command_id = str(row["command_id"])
        expected = REVIEW_DIR / REQUIRED_VERIFICATION_COMMANDS[command_id]
        if (
            row.get("exit_code") != 0
            or row.get("output_ref") != expected.relative_to(REPO_ROOT).as_posix()
            or not expected.is_file()
            or row.get("output_sha256") != _sha(expected)
            or not isinstance(row.get("subcommands"), list)
            or not row["subcommands"]
        ):
            raise RuntimeError(f"verification command malformed: {command_id}")
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
        "PFI/reports/pfi_v025/stage_9/whole_stage_review/verification_results.json",
        "PFI/reports/pfi_v025/stage_9/whole_stage_review/phase_commit_binding.json",
        "PFI/reports/pfi_v025/stage_9/whole_stage_review/browser_validation.json",
        "PFI/reports/pfi_v025/stage_9/whole_stage_review/model_validation_report.html",
        "PFI/reports/pfi_v025/stage_9/whole_stage_review/structured_uat.json",
        "PFI/reports/pfi_v025/stage_9/whole_stage_review/transition_authorization_binding.json",
    }
    if not required <= paths:
        raise RuntimeError("reviewed evidence overlay omits required Stage 9 evidence")
    return current


def _require_reviewers(
    overlay: dict[str, object], evidence_overlay: dict[str, object],
) -> dict[str, object]:
    payload = _json(REVIEW_DIR / "reviewer_results.json")
    reviewers = payload.get("reviewers")
    if (
        payload.get("status") != "pass"
        or not isinstance(reviewers, list)
        or len(reviewers) != 3
        or any(not isinstance(row, dict) for row in reviewers)
    ):
        raise RuntimeError("reviewer result set is not passing")
    typed = [row for row in reviewers if isinstance(row, dict)]
    ids = [str(row.get("reviewer_id")) for row in typed]
    if len(ids) != len(set(ids)) or set(ids) != set(REQUIRED_REVIEWERS):
        raise RuntimeError("exactly the three required reviewers must be present")
    for row in typed:
        reviewer_id = str(row["reviewer_id"])
        if (
            row.get("decision") != "ACCEPT"
            or row.get("counts") != {"critical": 0, "important": 0, "minor": 0}
            or row.get("initial_counts") != REQUIRED_REVIEWERS[reviewer_id]
            or row.get("review_base") != REVIEW_BASE
            or row.get("reviewed_overlay_file_count") != overlay["file_count"]
            or row.get("reviewed_overlay_sha256") != overlay["content_manifest_sha256"]
            or row.get("reviewed_evidence_file_count") != evidence_overlay["file_count"]
            or row.get("reviewed_evidence_sha256") != evidence_overlay["content_manifest_sha256"]
        ):
            raise RuntimeError(f"reviewer binding or result differs: {reviewer_id}")
        result_text = row.get("result_text")
        if not isinstance(result_text, str) or not result_text.strip():
            raise RuntimeError(f"reviewer result text missing: {reviewer_id}")
        expected = "sha256:" + hashlib.sha256(result_text.encode("utf-8")).hexdigest()
        if row.get("result_sha256") != expected:
            raise RuntimeError(f"reviewer result hash mismatch: {reviewer_id}")
    if any(payload.get(flag) is not False for flag in (
        "contains_private_values", "finder_used", "launchservices_used",
        "gui_file_operations_used", "external_network_performed",
    )):
        raise RuntimeError("review execution safety flags are unsafe or missing")
    return payload


def _require_supporting_evidence() -> None:
    required_pass = (
        "phase_commit_binding.json",
        "browser_validation.json",
        "report_manifest.json",
        "report_consistency.json",
        "export_manifest.json",
        "export_validation.json",
        "pdf_validation.json",
        "input_immutability.json",
        "authority_binding.json",
    )
    for relative in required_pass:
        if _json(REVIEW_DIR / relative).get("status") != "pass":
            raise RuntimeError(f"supporting evidence is not passing: {relative}")
    browser = _json(REVIEW_DIR / "browser_validation.json")
    if browser.get("check_count") != 16 or browser.get("passed_check_count") != 16:
        raise RuntimeError("browser acceptance is not 16/16")
    uat = _json(REVIEW_DIR / "structured_uat.json")
    if uat.get("overall_result") != "pass_for_stage_transition_only":
        raise RuntimeError("structured UAT is not a truthful transition pass")
    authorization = _json(REVIEW_DIR / "transition_authorization_binding.json")
    if authorization.get("status") != "accepted_via_standing_transition_authorization":
        raise RuntimeError("standing transition authorization is not bound")
    if not (REVIEW_DIR / "model_validation_report.html").is_file():
        raise RuntimeError("model validation report is absent")


def _privacy_scan() -> None:
    forbidden = (str(Path.home()), "BEGIN PRIVATE KEY", "AKIA")
    user_path = re.compile(r"/Users/[A-Za-z0-9._-]+/")
    user_path_bytes = re.compile(rb"/Users/[A-Za-z0-9._-]+/")
    for path in sorted(REVIEW_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".json", ".md", ".txt", ".log", ".html", ".csv"}:
            text = path.read_text(encoding="utf-8")
            if any(marker in text for marker in forbidden) or user_path.search(text):
                raise RuntimeError(f"private path or credential marker in evidence: {path.name}")
        elif path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    value = archive.read(name)
                    if (
                        any(marker.encode("utf-8") in value for marker in forbidden)
                        or user_path_bytes.search(value)
                    ):
                        raise RuntimeError(f"private path or credential marker in trace: {path.name}:{name}")


def _artifacts() -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": _sha(path)}
        for path in sorted(REVIEW_DIR.rglob("*"))
        if path.is_file() and path.name not in SELF_BOUND
    ]


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
        "schema": "PFIV025Stage9WholeReviewAuditV1",
        "status": "pass",
        "initial_review": {"counts": initial_counts, "source_reviews": REQUIRED_REVIEWERS},
        "post_remediation_review": {
            "status": "pass",
            "counts": {"critical": 0, "important": 0, "minor": 0},
            "reviewer_results_ref": "PFI/reports/pfi_v025/stage_9/whole_stage_review/reviewer_results.json",
        },
    })
    artifacts = _artifacts()
    final_index = {
        "schema": "PFIV025Stage9FinalEvidenceIndexV1",
        "status": "accepted_for_transition",
        "version": "v0.2.5",
        "stage": 9,
        "contract_id": "PFI-V025-STAGE9-WHOLE-REVIEW",
        "acceptance_id": "ACC-PFI-V025-STAGE9-WHOLE-REVIEW",
        "review_base": REVIEW_BASE,
        "review_execution_semantics": "review_base_commit_plus_exact_frozen_worktree_and_evidence_overlays",
        "reviewed_overlay_file_count": overlay["file_count"],
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "reviewed_evidence_file_count": evidence_overlay["file_count"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "verification_status": "pass",
        "independent_rereview_status": "pass",
        "initial_review_counts": initial_counts,
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "acceptance_criteria": [
            {"id": "S9-ACC-01", "status": "pass_with_limits", "result": "数据质量可生成；消费/现金流 partial，净资产/现金/投资 blocked，不输出假结论。"},
            {"id": "S9-ACC-02", "status": "pass", "result": "主报告显示总流出、生活消费、投资资金流出、投资域配置四组件，并解释 activity 不等于 net-worth loss。"},
            {"id": "S9-ACC-03", "status": "pass_with_blocked_formulas", "result": "FORM15/19 有当前证据；FORM16..18 blocked，FORM20 structure-only。"},
            {"id": "S9-ACC-04", "status": "pass_truthful_partial", "result": "模型卡、限制、反证、敏感性和参数影响可见；historical/OOS 继续 blocked。"},
            {"id": "S9-ACC-05", "status": "pass", "result": "只读决策对象含证据、反证、失效条件、风险与人工复核状态；无自动交易或执行路径。"},
            {"id": "S9-ACC-06", "status": "pass", "result": "HTML/PDF/CSV/Markdown 来自同一 snapshot，manifest、完整 hashes 与物理 PDF 可验证。"},
            {"id": "S9-ACC-07", "status": "pass", "result": "current-content browser 16/16、DOM/CDP AX、完整验证与三方复审 C0/I0/M0。"},
            {"id": "S9-ACC-08", "status": "accepted_via_standing_transition_authorization", "result": "用户站立授权用于 Stage 9 transition 与 Stage 10 entry；不等于 Stage 10 implementation、production 或 final acceptance。"},
        ],
        "report_count": 5,
        "partial_report_count": 2,
        "blocked_report_count": 3,
        "dual_consumption_component_count": 4,
        "browser_acceptance_check_count": 16,
        "export_format_count": 4,
        "artifact_count": len(artifacts),
        "evidence_artifacts": artifacts,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "external_network_performed": False,
        "real_financial_rows_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "push_performed": False,
        "app_install_performed": False,
        "stage_9_status": "accepted_for_transition",
        "stage_10_entry_authorized": True,
        "stage_10_status": "not_started",
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    _write_json(REVIEW_DIR / "final_evidence_index.json", final_index)
    index_sha = _sha(REVIEW_DIR / "final_evidence_index.json")
    release = _json(PFI_ROOT / "config/release_manifest.json")
    human_acceptance = {
        "product": "PFI",
        "version": "v0.2.5",
        "build_id": str(release["build_id"]),
        "git_commit": REVIEW_BASE,
        "stage": 9,
        "evidence_index_hash": index_sha,
        "accepted_scope": [
            "Stage 9 report, model-validation, human-decision and same-source export transition gate",
            "authorization to enter Stage 10 only; Stage 10 implementation remains not_started in this run",
        ],
        "known_defects": [
            "net worth, cash and investment reports remain blocked because required production inputs are absent",
            "consumption and cashflow remain partial coverage analyses",
            "historical and out-of-sample model validation remains blocked without ground truth",
        ],
        "accepted_at": _now(),
        "acceptance_statement": "用户在最终验收前的统一授权接受 Stage 9 transition，并仅授权后续独立 run 进入 Stage 10；不接受生产或最终验收。",
        "user_confirmation_reference": "在最终验收前我全部都同意授权，不允许block",
    }
    with zipfile.ZipFile(TASK_PACK) as archive:
        human_schema = json.loads(archive.read(
            "PFI_v0.2.5_TaskPack/schemas/human_acceptance.schema.json"
        ))
        evidence_schema = json.loads(archive.read(
            "PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"
        ))
    errors = sorted(error.message for error in Draft202012Validator(human_schema).iter_errors(human_acceptance))
    if errors:
        raise RuntimeError(f"human acceptance violates TaskPack schema: {errors}")
    _write_json(REVIEW_DIR / "human_acceptance.json", human_acceptance)

    verification = _json(REVIEW_DIR / "verification_results.json")
    commands = [
        {
            "command": row["command"],
            "exit_code": row["exit_code"],
            "summary": f"{row['command_id']} pass; {row['output_ref']} hash {row['output_sha256']}",
        }
        for row in verification["commands"]
    ]
    overlay_paths = [str(row["path"]) for row in overlay["files"]]
    artifact_paths = [row["path"] for row in artifacts]
    evidence = {
        "version": "v0.2.5",
        "stage": 9,
        "phase": "whole_stage_review",
        "status": "candidate_pass",
        "git_commit": REVIEW_BASE,
        "allowed_files_obeyed": False,
        "commands": commands,
        "changed_files": sorted(set(overlay_paths + artifact_paths + [
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/final_evidence_index.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/human_acceptance.json",
        ])),
        "evidence_files": [
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/final_evidence_index.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/reviewed_worktree_overlay.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/reviewed_evidence_overlay.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/phase_commit_binding.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/verification_results.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/reviewer_results.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/structured_uat.json",
            "PFI/reports/pfi_v025/stage_9/whole_stage_review/human_acceptance.json",
        ],
        "explicitly_not_done": [
            "Stage 10 implementation",
            "GitHub push or PFI.app installation",
            "Finder, LaunchServices or GUI file operations",
            "external-network access",
            "production acceptance",
            "final human acceptance",
        ],
        "risks": [
            "net worth, cash and investment remain blocked because required production inputs are absent",
            "consumption and cashflow remain partial and do not support complete financial conclusions",
            "historical and out-of-sample model validation remains blocked without ground truth",
        ],
        "rollback": "Revert the Stage 9 evidence/governance transition commit and remediation commits; preserve immutable Phase 9.1/9.2/9.3 artifacts. No data rollback is required.",
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "contract_id": "PFI-V025-STAGE9-WHOLE-REVIEW",
        "acceptance_id": "ACC-PFI-V025-STAGE9-WHOLE-REVIEW",
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
        "stage_9_phase_task_completed_count": 12,
        "stage_9_phase_task_count": 12,
        "v025_completed_task_count": 120,
        "v025_task_count": 156,
        "overall_progress_percent": 76.92,
        "report_count": 5,
        "partial_report_count": 2,
        "blocked_report_count": 3,
        "dual_consumption_component_count": 4,
        "stage_9_status": "accepted_for_transition",
        "stage_9_whole_stage_review_status": "pass",
        "stage_9_user_acceptance_status": "accepted_via_standing_transition_authorization",
        "stage_10_entry_authorized": True,
        "stage_10_status": "not_started",
        "next_task_id": "S10-P1-T1",
        "next_acceptance_id": "ACC-PFI-V025-STAGE10-WHOLE-REVIEW",
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "real_financial_rows_read": False,
        "financial_data_mutated": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "reviewer_results_sha256": _sha(REVIEW_DIR / "reviewer_results.json"),
        "reviewer_result_count": len(reviewers["reviewers"]),
    }
    errors = sorted(error.message for error in Draft202012Validator(evidence_schema).iter_errors(evidence))
    if errors:
        raise RuntimeError(f"final evidence violates TaskPack schema: {errors}")
    _write_json(REVIEW_DIR / "evidence.json", evidence)
    _privacy_scan()
    print(json.dumps({
        "status": "accepted_for_transition",
        "stage": 9,
        "stage_10_status": "not_started",
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "reviewed_evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "artifact_count": len(artifacts),
        "reviewer_count": len(reviewers["reviewers"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
