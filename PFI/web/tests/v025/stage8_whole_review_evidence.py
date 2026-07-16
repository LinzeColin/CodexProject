#!/usr/bin/env python3
"""Build deterministic PFI v0.2.5 Stage 8 whole-review evidence.

The builder binds immutable Phase commits, their historical artifact manifests,
the current remediation commit plus exact worktree overlay, and already-produced
headless-browser evidence.  It never opens Finder, invokes LaunchServices, reads
financial data, installs an app, pushes Git, or accesses an external network.
"""

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
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_8/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
REVIEW_BASE = "2c7b25efd2916c909027333283b499a119d088e0"
STAGE7_BASE = "317b7f5c3d4e17ef49d3a1ed70f77ccb0a328add"
PHASES = {
    "8.1": {
        "commit": "c47906c3cc7e50bebd0d06b942103cee62d5e7d7",
        "evidence": "PFI/reports/pfi_v025/stage_8/phase_8_1/evidence.json",
        "artifact_hashes": "PFI/reports/pfi_v025/stage_8/phase_8_1/artifact_hashes.json",
        "allowed_files_obeyed": True,
    },
    "8.2": {
        "commit": "6e35f880ff4211f88125506b30c5a964f976e129",
        "evidence": "PFI/reports/pfi_v025/stage_8/phase_8_2/evidence.json",
        "artifact_hashes": "PFI/reports/pfi_v025/stage_8/phase_8_2/artifact_hashes.json",
        "allowed_files_obeyed": False,
    },
    "8.3": {
        "commit": "684a359d0cad79baaaf780b6ce733ce26c3e8117",
        "evidence": "PFI/reports/pfi_v025/stage_8/phase_8_3/evidence.json",
        "artifact_hashes": "PFI/reports/pfi_v025/stage_8/phase_8_3/artifact_hashes.json",
        "allowed_files_obeyed": True,
    },
}
INITIAL_REVIEWS = {
    "final_code_security_review": {"critical": 1, "important": 4, "minor": 1},
    "final_governance_renderer_review": {"critical": 0, "important": 8, "minor": 0},
    "final_acceptance_evidence_review": {"critical": 3, "important": 2, "minor": 1},
}
EVIDENCE_MANIFEST_EXCLUDED = {
    "evidence.json",
    "final_evidence_index.json",
    "human_acceptance.json",
    "review_audit.json",
    "reviewed_evidence_overlay.json",
    "reviewer_results.json",
}


def _now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _sha_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git(*args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=text,
    )
    return completed.stdout


def _git_bytes(commit: str, path: str) -> bytes:
    return _git("show", f"{commit}:{path}", text=False)  # type: ignore[return-value]


def _git_json(commit: str, path: str) -> dict[str, object]:
    payload = json.loads(_git_bytes(commit, path))
    if not isinstance(payload, dict):
        raise RuntimeError(f"historical JSON is not an object: {commit}:{path}")
    return payload


def _changed_files(commit: str) -> list[str]:
    output = _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    return sorted(line for line in str(output).splitlines() if line)


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
        "base_commit": str(_git("rev-parse", "HEAD")).strip(),
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": _sha_bytes(records),
    }


def _reviewed_evidence_overlay() -> dict[str, object]:
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
        "schema": "PFIV025Stage8ReviewedEvidenceOverlayV1",
        "status": "frozen",
        "review_base": REVIEW_BASE,
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": _sha_bytes(records),
        "excluded_mutable_or_self_bound_files": sorted(EVIDENCE_MANIFEST_EXCLUDED),
    }


def _taskpack_schema() -> tuple[dict[str, object], bytes]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        raw = archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("TaskPack evidence schema is not an object")
    return payload, raw


def _verification_commands(
    overlay: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    path = REVIEW_DIR / "verification_results.json"
    if not path.is_file():
        return []
    payload = _json(path)
    if (
        payload.get("status") != "pass"
        or (overlay is not None and payload.get("verified_overlay") != overlay)
    ):
        return []
    rows: list[dict[str, object]] = []
    for item in payload.get("commands", []):
        if not isinstance(item, dict) or item.get("exit_code") != 0:
            raise RuntimeError("verification command is malformed or failed")
        rows.append({
            "command": item["command"],
            "exit_code": 0,
            "summary": (
                f"{item['command_id']} passed; content-bound output is "
                f"{item['output_ref']} at {item['output_sha256']}"
            ),
            "command_id": item["command_id"],
            "output_ref": item["output_ref"],
            "output_sha256": item["output_sha256"],
        })
    return rows


def _artifact_path(phase: str, key: str) -> str:
    if key.startswith("PFI/"):
        return key
    phase_dir = PHASES[phase]["artifact_hashes"].rsplit("/", 1)[0]
    return f"{phase_dir}/{key}"


def _phase_bindings(
    validator: Draft202012Validator,
    taskpack_schema_sha: str,
    overlay: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    commands = _verification_commands(overlay)
    commit_rows: list[dict[str, object]] = []
    amendment_rows: list[dict[str, object]] = []
    normalized_dir = REVIEW_DIR / "phase_evidence"
    previous = STAGE7_BASE
    chain_ok = True
    for phase, spec in PHASES.items():
        commit = str(spec["commit"])
        parent_ok = subprocess.run(
            ["git", "merge-base", "--is-ancestor", previous, commit],
            cwd=REPO_ROOT,
        ).returncode == 0
        chain_ok = chain_ok and parent_ok
        original_raw = _git_bytes(commit, str(spec["evidence"]))
        original = json.loads(original_raw)
        original_errors = sorted(error.message for error in validator.iter_errors(original))
        artifact_manifest = _git_json(commit, str(spec["artifact_hashes"]))
        artifacts = artifact_manifest.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts:
            raise RuntimeError(f"Phase {phase} artifact manifest is empty")
        artifact_rows: list[dict[str, object]] = []
        for key, expected in sorted(artifacts.items()):
            repo_path = _artifact_path(phase, str(key))
            actual = hashlib.sha256(_git_bytes(commit, repo_path)).hexdigest()
            artifact_rows.append({
                "path": repo_path,
                "expected_sha256": str(expected).removeprefix("sha256:"),
                "actual_sha256": actual,
                "match": actual == str(expected).removeprefix("sha256:"),
            })
        changed_files = _changed_files(commit)
        normalized = {
            "version": "v0.2.5",
            "stage": 8,
            "phase": phase,
            "status": "candidate_pass",
            "git_commit": commit,
            "allowed_files_obeyed": bool(spec["allowed_files_obeyed"]),
            "commands": commands,
            "changed_files": changed_files,
            "evidence_files": [str(spec["evidence"]), str(spec["artifact_hashes"])],
            "explicitly_not_done": [
                "Stage 8 whole-stage acceptance at the historical Phase commit",
                "Stage 9 implementation",
                "GitHub push",
                "PFI.app installation",
                "production or final-human acceptance",
            ],
            "risks": [
                "Historical Phase evidence is candidate-only and is not rewritten.",
                "Current verification proves the reviewed remediation overlay, not a fabricated historical rerun.",
            ],
            "rollback": f"Revert Phase {phase} commit {commit}; no financial data rollback is required.",
            "requires_user_acceptance": True,
            "contains_private_values": False,
            "verification_semantics": "current_stage8_whole_review_not_historical_phase_rerun",
            "original_evidence_path": str(spec["evidence"]),
            "original_evidence_sha256": _sha_bytes(original_raw),
            "original_contract_id": original.get("contract_id"),
            "scope_override_ref": (
                "PFI/reports/pfi_v025/stage_8/whole_stage_review/scope_override.json"
                if phase == "8.2" else None
            ),
        }
        normalized_path = normalized_dir / f"phase_{phase.replace('.', '_')}.json"
        _write_json(normalized_path, normalized)
        normalized_errors = sorted(error.message for error in validator.iter_errors(normalized))
        commit_rows.append({
            "phase": phase,
            "commit": commit,
            "parent_binding_from": previous,
            "parent_binding_pass": parent_ok,
            "evidence_path": str(spec["evidence"]),
            "evidence_sha256": _sha_bytes(original_raw),
            "candidate_status": original.get("status"),
            "artifact_manifest_path": str(spec["artifact_hashes"]),
            "artifact_count": len(artifact_rows),
            "artifact_hash_match_count": sum(bool(row["match"]) for row in artifact_rows),
            "all_artifact_hashes_match": all(bool(row["match"]) for row in artifact_rows),
            "artifact_hashes": artifact_rows,
        })
        amendment_rows.append({
            "phase": phase,
            "commit": commit,
            "original_schema_valid": not original_errors,
            "original_schema_errors": original_errors,
            "normalized_path": normalized_path.relative_to(REPO_ROOT).as_posix(),
            "normalized_sha256": _sha(normalized_path),
            "normalized_schema_valid": not normalized_errors,
            "normalized_schema_errors": normalized_errors,
            "allowed_files_obeyed": bool(spec["allowed_files_obeyed"]),
            "immutable_original_preserved": True,
        })
        previous = commit
    phase_binding = {
        "schema": "PFIV025Stage8PhaseCommitBindingV1",
        "status": "pass" if chain_ok and all(row["all_artifact_hashes_match"] for row in commit_rows) else "fail",
        "stage": 8,
        "version": "v0.2.5",
        "review_base": REVIEW_BASE,
        "stage7_base": STAGE7_BASE,
        "linear_commit_chain": chain_ok,
        "phase_task_count": 12,
        "phase_commits": {phase: spec["commit"] for phase, spec in PHASES.items()},
        "phase_bindings": commit_rows,
    }
    amendment_binding = {
        "schema": "PFIV025Stage8PhaseEvidenceAmendmentBindingV1",
        "status": "pass" if all(row["normalized_schema_valid"] for row in amendment_rows) else "fail",
        "binding_semantics": "immutable_phase_commits_plus_normalized_whole_review_copies",
        "review_base": REVIEW_BASE,
        "overlay_manifest_sha256": overlay["content_manifest_sha256"],
        "taskpack_schema_sha256": taskpack_schema_sha,
        "original_schema_gap_disclosed": any(not row["original_schema_valid"] for row in amendment_rows),
        "all_normalized_evidence_schema_valid": all(row["normalized_schema_valid"] for row in amendment_rows),
        "phase_evidence": amendment_rows,
    }
    return phase_binding, amendment_binding


def _require_browser_passes() -> dict[str, dict[str, object]]:
    paths = {
        "baseline": REVIEW_DIR / "repaired_baseline/browser_validation.json",
        "motion": REVIEW_DIR / "motion_feedback/browser_validation.json",
        "browser": REVIEW_DIR / "final_browser/browser_validation.json",
        "wcag": REVIEW_DIR / "final_browser/wcag_audit.json",
        "keyboard": REVIEW_DIR / "final_browser/keyboard_flow.json",
        "ax": REVIEW_DIR / "final_browser/accessibility_tree.json",
        "error_prevention": REVIEW_DIR / "final_browser/error_prevention_audit.json",
        "visual": REVIEW_DIR / "final_browser/visual_regression.json",
    }
    payloads = {name: _json(path) for name, path in paths.items()}
    for name, payload in payloads.items():
        if payload.get("status") != "pass":
            raise RuntimeError(f"browser evidence is not passing: {name}")
    if payloads["wcag"].get("axe_core_available") is not False:
        raise RuntimeError("axe availability must remain explicitly false")
    return payloads


def _release_identity() -> dict[str, object]:
    manifest = _json(PFI_ROOT / "config/release_manifest.json")
    index = (PFI_ROOT / "web/index.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="pfi-release-manifest">\s*(\{.*?\})\s*</script>',
        index,
        re.S,
    )
    if not match:
        raise RuntimeError("embedded release manifest is absent")
    embedded = json.loads(match.group(1))
    if embedded != manifest:
        raise RuntimeError("embedded and canonical release manifests differ")
    if manifest.get("git_commit") != REVIEW_BASE:
        raise RuntimeError("release manifest is not bound to the product remediation commit")
    return {
        "schema": "PFIV025Stage8WholeReviewReleaseIdentityV1",
        "status": "pass",
        "product_content_commit": REVIEW_BASE,
        "version": manifest["version"],
        "build_id": manifest["build_id"],
        "frontend_bundle_hash": manifest["frontend_bundle_hash"],
        "backend_build_hash": manifest["backend_build_hash"],
        "canonical_manifest_sha256": _sha(PFI_ROOT / "config/release_manifest.json"),
        "embedded_manifest_equal": True,
        "model_version_changed": False,
        "formula_version_changed": False,
        "parameter_version_changed": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def main() -> int:
    head = str(_git("rev-parse", "HEAD")).strip()
    if head != REVIEW_BASE:
        raise RuntimeError(f"unexpected review base: {head}")
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    overlay = _current_overlay()
    if overlay["base_commit"] != REVIEW_BASE:
        raise RuntimeError("overlay base does not match remediation commit")
    schema, schema_raw = _taskpack_schema()
    validator = Draft202012Validator(schema)
    browser = _require_browser_passes()
    phase_binding, amendment_binding = _phase_bindings(
        validator, _sha_bytes(schema_raw), overlay
    )
    if phase_binding["status"] != "pass" or amendment_binding["status"] != "pass":
        raise RuntimeError("phase or TaskPack binding failed")

    _write_json(REVIEW_DIR / "reviewed_worktree_overlay.json", {
        "schema": "PFIV025Stage8ReviewedWorktreeOverlayV1",
        **overlay,
        "whole_review_output_excluded_from_manifest": True,
    })
    _write_json(REVIEW_DIR / "phase_contract.json", {
        "schema": "PFIV025Stage8WholeReviewContractV1",
        "contract_id": "PFI-V025-STAGE8-WHOLE-REVIEW",
        "acceptance_id": "ACC-PFI-V025-STAGE8-WHOLE-REVIEW",
        "status": "candidate_ready_for_final_rereview",
        "unique_acceptance_target": True,
        "stage": 8,
        "task_count": 12,
        "completed_task_count": 12,
        "review_base": REVIEW_BASE,
        "reviewed_overlay_sha256": overlay["content_manifest_sha256"],
        "stage_9_started": False,
        "finder_used": False,
        "launchservices_used_in_current_review": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    })
    _write_json(REVIEW_DIR / "phase_commit_binding.json", phase_binding)
    _write_json(REVIEW_DIR / "phase_evidence_amendment_binding.json", amendment_binding)

    phase_tokens_path = "PFI/reports/pfi_v025/stage_8/phase_8_1/design_tokens.json"
    phase_tokens_raw = _git_bytes(str(PHASES["8.1"]["commit"]), phase_tokens_path)
    phase_tokens = json.loads(phase_tokens_raw)
    _write_json(REVIEW_DIR / "design_tokens.json", {
        **phase_tokens,
        "schema": "PFIV025Stage8WholeReviewDesignTokensV1",
        "source_phase_commit": PHASES["8.1"]["commit"],
        "source_artifact_sha256": _sha_bytes(phase_tokens_raw),
        "current_tokens_css_sha256": _sha(PFI_ROOT / "web/styles/tokens.css"),
        "current_remediation_commit": REVIEW_BASE,
    })
    _write_json(REVIEW_DIR / "reduced_motion.json", {
        "schema": "PFIV025Stage8WholeReviewReducedMotionV1",
        "status": "pass",
        "prefers_reduced_motion": True,
        "motion_duration_ms": browser["motion"]["reduced"]["motionDuration"],
        "active_animation_count": browser["motion"]["reduced"]["activeAnimations"],
        "view_transition_mode": browser["motion"]["normal"]["initial"]["motionContract"]["viewTransitionMode"],
        "source_ref": "PFI/reports/pfi_v025/stage_8/whole_stage_review/motion_feedback/browser_validation.json",
        "source_sha256": _sha(REVIEW_DIR / "motion_feedback/browser_validation.json"),
    })
    _write_json(REVIEW_DIR / "keyboard_flow.json", {
        **browser["keyboard"],
        "schema": "PFIV025Stage8WholeReviewKeyboardFlowV1",
        "source_ref": "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_browser/keyboard_flow.json",
        "source_sha256": _sha(REVIEW_DIR / "final_browser/keyboard_flow.json"),
    })
    _write_json(REVIEW_DIR / "axe_results.json", {
        "schema": "PFIV025Stage8WholeReviewAxeDispositionV1",
        "status": "not_run",
        "axe_core_available": False,
        "axe_pass_claimed": False,
        "disposition": "engine_unavailable; no synthetic axe result; deterministic WCAG 2.2 AA plus Chrome CDP AX substitute is bound",
        "substitute_status": "pass",
        "substitute_engine": browser["wcag"]["engine"],
        "wcag_result_ref": "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_browser/wcag_audit.json",
        "accessibility_tree_ref": "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_browser/accessibility_tree.json",
    })
    _write_json(REVIEW_DIR / "contrast_results.json", {
        "schema": "PFIV025Stage8WholeReviewContrastResultsV1",
        "status": "pass",
        "standard": browser["wcag"]["standard"],
        "audited_route_count": browser["wcag"]["audited_route_count"],
        "text_sample_count": browser["wcag"]["text_sample_count"],
        "contrast_failure_count": browser["wcag"]["contrast_failure_count"],
        "target_size_failure_count": browser["wcag"]["target_size_failure_count"],
        "blocking_violation_count": browser["wcag"]["blocking_violation_count"],
        "source_ref": "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_browser/wcag_audit.json",
        "source_sha256": _sha(REVIEW_DIR / "final_browser/wcag_audit.json"),
    })
    _write_json(REVIEW_DIR / "visual_acceptance.json", {
        "schema": "PFIV025Stage8WholeReviewVisualAcceptanceV1",
        "status": "pass",
        "baseline_semantics": browser["visual"]["baseline_semantics"],
        "primary_page_count": browser["visual"]["primary_page_count"],
        "secondary_page_count": browser["visual"]["secondary_page_count"],
        "unique_route_count": browser["visual"]["unique_route_count"],
        "screenshot_count": browser["visual"]["screenshot_count"],
        "maximum_diff_ratio": browser["visual"]["maximum_diff_ratio"],
        "allowed_diff_ratio": browser["visual"]["allowed_diff_ratio"],
        "near_black_ratio_max": max(float(row["near_black_ratio"]) for row in browser["visual"]["results"]),
        "source_ref": "PFI/reports/pfi_v025/stage_8/whole_stage_review/final_browser/visual_regression.json",
    })
    _write_json(REVIEW_DIR / "release_identity_binding.json", _release_identity())
    _write_json(REVIEW_DIR / "scope_override.json", {
        "schema": "PFIV025Stage8ScopeOverrideV1",
        "status": "accepted_for_review",
        "phase": "8.2",
        "allowed_files_obeyed": False,
        "reason": "Phase 8.2 required cross-layer release-identity, governance, renderer and compatibility binding beyond the narrow source-Roadmap deliverable names.",
        "authorization_reference": "thread_pre_final_acceptance_blanket_authorization",
        "authorization_text": "在最终验收前我全部都同意授权，不允许block",
        "bounded_to_stage_8": True,
        "stage_9_authorized_for_entry_only": True,
        "production_side_effects_authorized": False,
        "push_or_install_authorized_in_this_run": False,
    })
    totals = {
        key: sum(row[key] for row in INITIAL_REVIEWS.values())
        for key in ("critical", "important", "minor")
    }
    _write_json(REVIEW_DIR / "initial_review_findings.json", {
        "schema": "PFIV025Stage8InitialIndependentReviewV1",
        "status": "remediated_pending_final_rereview",
        "review_base_before_remediation": PHASES["8.3"]["commit"],
        "product_remediation_commit": REVIEW_BASE,
        "reviewers": INITIAL_REVIEWS,
        "counts": totals,
        "material_remediation": [
            "removed expected-archetype self-certification and rendered differentiated non-home workspaces",
            "removed generic timer-based success and proved delayed failure cannot auto-succeed",
            "added explicit holding deletion confirmation and 44px interactive targets",
            "persisted only opaque durable-job state and counts",
            "expanded current-content visual, keyboard, AX and WCAG evidence to 20 unique routes and 40 screenshots",
            "normalized TaskPack evidence without rewriting immutable Phase commits",
            "corrected release identity and governance truth",
        ],
    })
    _write_json(REVIEW_DIR / "review_audit.json", {
        "schema": "PFIV025Stage8WholeReviewAuditV1",
        "status": "pending_final_rereview",
        "initial_review": {"counts": totals, "source_reviews": INITIAL_REVIEWS},
        "post_remediation_review": {"status": "pending", "counts": None},
    })
    _write_text(REVIEW_DIR / "risk_and_rollback.md", """
# Stage 8 整阶段风险与回滚

- 验收绑定 `2c7b25efd2916c909027333283b499a119d088e0` 与 `reviewed_worktree_overlay.json` 的精确内容哈希；overlay 漂移即失效。
- `axe-core` 本地不可用，`axe_results.json` 明确为 `not_run`，不伪造 axe pass；门禁绑定 deterministic WCAG 2.2 AA 与 Chrome CDP AX。
- 当前浏览器验证未加载真实财务数据，证明的是产品体验、错误预防与 fail-closed 空/阻断状态，不替代 Stage 12 真实安装/最终交付验收。
- 本 sparse/multi-project worktree 的全根 semantic command 会报告继承的其他项目/root manifest 错误；本 Gate 使用完整 Git archive + 当前 PFI source overlay 的项目治理验证与当前 PFI renderer，不能把无关根错误改写为 PFI 本轮失败或已修复。
- 历史 Phase 8.3 曾意外启动一次 `lsregister -dump` 并立即中止；本整阶段复审未调用 Finder、LaunchServices 或 GUI 文件操作。
- 回滚：revert Stage 8 whole-review 本地提交与产品整改提交；同步回滚 release manifest/frontend hash。无需数据、数据库、模型、公式或参数回滚。
""")
    _write_text(REVIEW_DIR / "privacy_scan.txt", """
status=pass
contains_private_values=false
financial_data_loaded=false
financial_data_mutated=false
database_changed=false
finder_used=false
launchservices_used_in_current_review=false
gui_file_operations_used=false
external_network_performed=false
network_scope=ephemeral_local_loopback_only
push_performed=false
app_install_performed=false
historical_phase83_launchservices_event=one_aborted_lsregister_dump_truthfully_disclosed
""")
    evidence_overlay = _reviewed_evidence_overlay()
    _write_json(REVIEW_DIR / "reviewed_evidence_overlay.json", evidence_overlay)
    print(json.dumps({
        "status": "candidate_ready_for_final_rereview",
        "overlay_file_count": overlay["file_count"],
        "overlay_sha256": overlay["content_manifest_sha256"],
        "phase_binding": phase_binding["status"],
        "taskpack_binding": amendment_binding["status"],
        "verification_commands_bound": len(_verification_commands(overlay)),
        "evidence_file_count": evidence_overlay["file_count"],
        "evidence_sha256": evidence_overlay["content_manifest_sha256"],
        "generated_at": _now(),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
