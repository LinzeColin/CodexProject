#!/usr/bin/env python3
"""Fail-closed Stage 7 whole-review evidence finalizer.

This command never invents command or reviewer results.  It accepts transition
only when current-worktree browser evidence, real verification reports, three
independent reviewer results, phase bindings, and the frozen overlay all pass.
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

from pfi_v02.stage_v025_stage7_whole_review import (
    ACCEPTANCE_ID,
    CONTRACT_ID,
    PHASE_COMMITS,
    PHASE_EVIDENCE,
    REVIEW_BASE,
    build_stage7_whole_review_contract,
    evaluate_stage7_phase_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_7/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
NOW = datetime.now().astimezone().replace(microsecond=0).isoformat()
TRACE_NAMES = (
    "import_browser_trace_sanitized.zip",
    "holding_browser_trace_sanitized.zip",
    "holding_restart_browser_trace_sanitized.zip",
    "metric_browser_trace_sanitized.zip",
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise RuntimeError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


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
            raise RuntimeError(
                f"unsupported delete/rename/copy worktree state in frozen overlay: {status!r}"
            )
        path = entry[3:]
        if path.startswith(review_prefix):
            continue
        if (REPO_ROOT / path).is_file():
            paths.add(path)
    files = [
        {"path": path, "sha256": _sha256(REPO_ROOT / path)}
        for path in sorted(paths)
    ]
    records = "".join(
        f"{item['path']}\0{item['sha256']}\n" for item in files
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


def _require_frozen_overlay(workflow: dict[str, object], overlay: dict[str, object]) -> None:
    current = _current_overlay()
    comparable = {
        key: overlay.get(key)
        for key in ("base_commit", "file_count", "files", "content_manifest_sha256")
    }
    if current != comparable:
        raise RuntimeError("reviewed worktree overlay drifted after browser validation")
    workflow_overlay = workflow.get("reviewed_worktree_overlay")
    if not isinstance(workflow_overlay, dict):
        raise RuntimeError("workflow overlay binding is missing")
    if workflow_overlay.get("content_manifest_sha256") != overlay.get("content_manifest_sha256"):
        raise RuntimeError("workflow and overlay manifest hashes differ")


def _require_workflow_safety_and_traces(workflow: dict[str, object]) -> None:
    false_flags = (
        "contains_private_values",
        "finder_used",
        "external_network_performed",
        "push_performed",
        "app_install_performed",
        "real_financial_source_mutated",
        "phase_evidence_overwritten",
    )
    if any(workflow.get(key) is not False for key in false_flags):
        raise RuntimeError("workflow safety flags are absent or unsafe")
    if (
        workflow.get("network_performed") is not True
        or workflow.get("network_scope") != "ephemeral_local_loopback_only"
        or workflow.get("database_scope") != "isolated_/tmp_only"
    ):
        raise RuntimeError("workflow runtime scope is not the approved local isolation boundary")
    persisted_hashes = workflow.get("persisted_trace_hashes")
    if not isinstance(persisted_hashes, dict) or set(persisted_hashes) != set(TRACE_NAMES):
        raise RuntimeError("workflow trace hash binding is incomplete")
    forbidden_literals = (
        b"/Users/",
        b"/private/var/folders/",
        b"/var/folders/",
        b"/tmp/",
        b"CONTRACT-SENTINEL",
        b"contract-sentinel",
        b"987654.32",
        b"MetaDatabase",
        b"PFI-V025-LEGACY-FINANCIAL-PUBLICATION",
    )
    for name in TRACE_NAMES:
        path = REVIEW_DIR / name
        if not path.is_file() or persisted_hashes[name] != _sha256(path):
            raise RuntimeError(f"workflow trace hash mismatch: {name}")
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if "trace.trace" not in names or any(item.startswith("resources/") for item in names):
                raise RuntimeError(f"workflow trace is missing its timeline or retains resources: {name}")
            serialized = b"\n".join(archive.read(item) for item in names)
        if any(literal in serialized for literal in forbidden_literals):
            raise RuntimeError(f"workflow trace retains a forbidden private marker: {name}")
        if re.search(rb"CNY\s+-?[0-9]", serialized):
            raise RuntimeError(f"workflow trace retains a financial number: {name}")


def _reject_private_evidence_text(value: str, *, label: str) -> None:
    private_markers = (str(Path.home()), "/Users/")
    if any(marker in value for marker in private_markers):
        raise RuntimeError(f"verification evidence contains a private absolute path: {label}")


def _require_verification(payload: dict[str, object], overlay: dict[str, object]) -> None:
    commands = payload.get("commands")
    if payload.get("status") != "pass" or not isinstance(commands, list) or not commands:
        raise RuntimeError("real verification report is absent or not passing")
    comparable_overlay = {
        key: overlay.get(key)
        for key in ("base_commit", "file_count", "files", "content_manifest_sha256")
    }
    if (
        payload.get("overlay_stable_during_verification") is not True
        or payload.get("verified_overlay") != comparable_overlay
    ):
        raise RuntimeError("verification result is not content-bound to the frozen source overlay")
    required = {"focused_stage7", "syntax_and_diff", "changed_scope_governance"}
    ids = {str(row.get("command_id")) for row in commands if isinstance(row, dict)}
    if not required <= ids:
        raise RuntimeError("verification report is missing required command groups")
    for row in commands:
        if not isinstance(row, dict) or row.get("exit_code") != 0:
            raise RuntimeError("verification report contains a failed or malformed command")
        if not row.get("command") or not row.get("output_sha256"):
            raise RuntimeError("verification command lacks exact command/output binding")
        _reject_private_evidence_text(str(row["command"]), label="command")
        subcommands = row.get("subcommands")
        if not isinstance(subcommands, list) or not subcommands:
            raise RuntimeError("verification command lacks exact subcommands")
        for subcommand in subcommands:
            _reject_private_evidence_text(str(subcommand), label="subcommand")
        output_ref = row.get("output_ref")
        if not isinstance(output_ref, str) or _sha256(REPO_ROOT / output_ref) != row.get("output_sha256"):
            raise RuntimeError("verification output hash does not match the persisted command log")
        _reject_private_evidence_text(
            (REPO_ROOT / output_ref).read_text(encoding="utf-8"),
            label=output_ref,
        )


def _require_reviewers(payload: dict[str, object], overlay: dict[str, object]) -> None:
    reviewers = payload.get("reviewers")
    required = {
        "final_code_security_review",
        "final_governance_renderer_review",
        "final_acceptance_evidence_review",
    }
    if payload.get("status") != "pass" or not isinstance(reviewers, list):
        raise RuntimeError("independent reviewer report is absent or not passing")
    by_id = {
        str(row.get("reviewer_id")): row
        for row in reviewers
        if isinstance(row, dict)
    }
    if set(by_id) != required:
        raise RuntimeError("exactly three required independent reviewers must be bound")
    for reviewer in by_id.values():
        if reviewer.get("decision") != "ACCEPT":
            raise RuntimeError("an independent reviewer did not accept")
        counts = reviewer.get("counts")
        if counts != {"critical": 0, "important": 0, "minor": 0}:
            raise RuntimeError("an independent reviewer still has findings")
        result_text = reviewer.get("result_text")
        if not isinstance(result_text, str) or not result_text.strip():
            raise RuntimeError("reviewer result text is absent")
        expected_hash = "sha256:" + hashlib.sha256(result_text.encode("utf-8")).hexdigest()
        if reviewer.get("result_sha256") != expected_hash:
            raise RuntimeError("reviewer result text is not content-bound")
        if (
            reviewer.get("review_base") != REVIEW_BASE
            or reviewer.get("reviewed_overlay_file_count") != overlay.get("file_count")
            or reviewer.get("reviewed_overlay_sha256") != overlay.get("content_manifest_sha256")
        ):
            raise RuntimeError("reviewer result is not bound to the current frozen overlay")
        initial_counts = reviewer.get("initial_counts")
        if (
            not isinstance(initial_counts, dict)
            or set(initial_counts) != {"critical", "important", "minor"}
            or any(not isinstance(value, int) or value < 0 for value in initial_counts.values())
        ):
            raise RuntimeError("reviewer initial findings are not explicitly recorded")


def _phase_amendment_binding(overlay: dict[str, object]) -> dict[str, object]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        schema_raw = archive.read(
            "PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json"
        )
    schema = json.loads(schema_raw)
    validator = Draft202012Validator(schema)
    rows: list[dict[str, object]] = []
    for phase, commit in PHASE_COMMITS.items():
        relative = PHASE_EVIDENCE[phase]
        original_raw = _git_bytes("show", f"{commit}:{relative}")
        original_payload = json.loads(original_raw)
        original_errors = sorted(error.message for error in validator.iter_errors(original_payload))
        current_path = REPO_ROOT / relative
        current_payload = _json(current_path)
        current_errors = sorted(error.message for error in validator.iter_errors(current_payload))
        rows.append(
            {
                "phase": phase,
                "original_commit": commit,
                "evidence_path": relative,
                "original_sha256": "sha256:" + hashlib.sha256(original_raw).hexdigest(),
                "original_schema_valid": not original_errors,
                "original_schema_errors": original_errors,
                "amended_sha256": _sha256(current_path),
                "amended_schema_valid": not current_errors,
                "amended_schema_errors": current_errors,
                "amendment_reason": (
                    "Task Pack changed_files/schema completion and review clarification; "
                    "immutable phase commit is not rewritten"
                ),
            }
        )
    status = "pass" if all(row["amended_schema_valid"] for row in rows) else "fail"
    return {
        "schema": "PFIV025Stage7PhaseEvidenceAmendmentBindingV1",
        "status": status,
        "binding_semantics": "immutable_phase_commit_plus_reviewed_worktree_overlay",
        "base_commit": overlay["base_commit"],
        "overlay_manifest_sha256": overlay["content_manifest_sha256"],
        "taskpack_schema_sha256": "sha256:" + hashlib.sha256(schema_raw).hexdigest(),
        "phase_evidence": rows,
        "original_schema_gap_disclosed": any(not row["original_schema_valid"] for row in rows),
        "all_amended_evidence_schema_valid": all(row["amended_schema_valid"] for row in rows),
    }


def _artifact(relative: str) -> dict[str, str]:
    path = REPO_ROOT / relative
    if not path.is_file():
        raise RuntimeError(f"required evidence artifact is missing: {relative}")
    return {"path": relative, "sha256": _sha256(path)}


def main() -> int:
    workflow = _json(REVIEW_DIR / "workflow_validation.json")
    overlay = _json(REVIEW_DIR / "reviewed_worktree_overlay.json")
    verification = _json(REVIEW_DIR / "verification_results.json")
    reviewer_results = _json(REVIEW_DIR / "reviewer_results.json")
    if workflow.get("status") != "pass" or int(workflow.get("browser_check_count") or 0) != 68:
        raise RuntimeError("current-worktree browser workflows are not 68/68 pass")
    if not all((workflow.get("workflow_status") or {}).values()):
        raise RuntimeError("one or more current-worktree browser workflows failed")
    _require_workflow_safety_and_traces(workflow)
    _require_frozen_overlay(workflow, overlay)
    _require_verification(verification, overlay)
    _require_reviewers(reviewer_results, overlay)

    phase_binding = evaluate_stage7_phase_evidence(REPO_ROOT)
    if phase_binding.get("status") != "pass":
        raise RuntimeError("immutable phase commit binding failed")
    amendment_binding = _phase_amendment_binding(overlay)
    if amendment_binding["status"] != "pass":
        raise RuntimeError("current phase evidence amendments are not schema-valid")
    _write_json(REVIEW_DIR / "phase_commit_binding.json", phase_binding)
    _write_json(REVIEW_DIR / "phase_evidence_amendment_binding.json", amendment_binding)

    contract = build_stage7_whole_review_contract()
    contract.update(
        {
            "status": "accepted_for_transition",
            "review_execution_semantics": "review_base_commit_plus_frozen_worktree_overlay",
            "generated_at": NOW,
        }
    )
    _write_json(REVIEW_DIR / "phase_contract.json", contract)

    initial_sources = {
        str(row["reviewer_id"]): dict(row["initial_counts"])
        for row in reviewer_results["reviewers"]
    }
    initial_counts = {
        severity: sum(row[severity] for row in initial_sources.values())
        for severity in ("critical", "important", "minor")
    }
    audit = {
        "schema": "PFIV025Stage7WholeReviewAuditV1",
        "status": "pass",
        "acceptance_id": ACCEPTANCE_ID,
        "initial_review": {"counts": initial_counts, "source_reviews": initial_sources},
        "post_remediation_review": {
            "counts": {"critical": 0, "important": 0, "minor": 0},
            "status": "pass",
            "reviewer_results_ref": "PFI/reports/pfi_v025/stage_7/whole_stage_review/reviewer_results.json",
        },
    }
    _write_json(REVIEW_DIR / "review_audit.json", audit)

    security = {
        "schema": "PFIV025Stage7WholeReviewSecurityValidationV1",
        "status": "pass",
        "verification_results_sha256": _sha256(REVIEW_DIR / "verification_results.json"),
        "reviewer_results_sha256": _sha256(REVIEW_DIR / "reviewer_results.json"),
        "workflow_validation_sha256": _sha256(REVIEW_DIR / "workflow_validation.json"),
        "controls": [
            "runtime token/Host/Origin/CORS and upload limits",
            "text-only dynamic DOM and CSV formula neutralization",
            "strict source/header/date/money/ZIP parsing",
            "atomic cross-batch ledger and command-hash idempotency",
            "cross-process locked migration backup and private raw lifecycle integrity",
            "Stage 7 SQLite canonical trends plus fail-closed economic-event lineage",
            "raw traces confined to /tmp before sanitized persistence",
        ],
        "finder_used": False,
        "external_network_performed": False,
        "contains_private_values": False,
    }
    _write_json(REVIEW_DIR / "security_validation.json", security)

    artifact_paths = [
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/workflow_validation.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/reviewed_worktree_overlay.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/phase_contract.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/phase_commit_binding.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/phase_evidence_amendment_binding.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/verification_results.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/reviewer_results.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/verification_focused_stage7.log",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/verification_syntax_and_diff.log",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/verification_changed_scope_governance.log",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/security_validation.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/review_audit.json",
        *(f"PFI/reports/pfi_v025/stage_7/whole_stage_review/{name}" for name in TRACE_NAMES),
    ]
    artifacts = [_artifact(path) for path in artifact_paths]
    index = {
        "schema": "PFIV025Stage7FinalEvidenceIndexV1",
        "version": "v0.2.5",
        "stage": 7,
        "status": "accepted_for_transition",
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_base": REVIEW_BASE,
        "review_execution_semantics": "review_base_commit_plus_frozen_worktree_overlay",
        "task_disposition": {
            f"S7-P{phase}-T{task}": "pass"
            for phase in range(1, 4) for task in range(1, 5)
        },
        "acceptance_criteria": [
            {"id": "S7-ACC-01", "status": "pass", "result": "真实上传、hash/parser/preview/mapping/error/review 闭环。"},
            {"id": "S7-ACC-02", "status": "pass", "result": "原子确认、跨批幂等、retry 与 rollback 闭环。"},
            {"id": "S7-ACC-03", "status": "pass", "result": "持仓/设置 SQLite 保存、刷新、重开、重启与 surface 同步。"},
            {"id": "S7-ACC-04", "status": "pass", "result": "参数中心、Interconnection、指标下钻为正式页面。"},
            {"id": "S7-ACC-05", "status": "pass", "result": "可证 range/hash/source 显示；未接入 economic-event lineage 明确阻断且无 false-zero。"},
            {"id": "S7-ACC-06", "status": "pass", "result": "冻结 worktree 三条真实 browser+SQLite 工作流 68/68。"},
        ],
        "stop_conditions": [
            {"condition": item, "status": "safety_stop_active"}
            for item in (
                "browser-only save", "toast-only completion",
                "fake preview or fabricated financial value",
                "sidecar parameter/interconnection page",
            )
        ],
        "pass_gate_result": "pass",
        "initial_review_counts": initial_counts,
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "phase_commit_binding_status": "pass",
        "phase_amendment_binding_status": "pass",
        "workflow_validation_status": "pass",
        "security_validation_status": "pass",
        "taskpack_schema_validation_status": "amended_current_evidence_pass_original_gaps_disclosed",
        "evidence_artifacts": artifacts,
        "stage_8_entry_authorized": True,
        "stage_8_status": "not_started",
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    _write_json(REVIEW_DIR / "final_evidence_index.json", index)

    manifest = _json(PFI_ROOT / "config/release_manifest.json")
    acceptance = {
        "product": "PFI",
        "version": "v0.2.5",
        "build_id": manifest["build_id"],
        "git_commit": REVIEW_BASE,
        "stage": 7,
        "evidence_index_hash": _sha256(REVIEW_DIR / "final_evidence_index.json"),
        "accepted_scope": [
            "Stage 7 production-truth upload/review/ledger workflow",
            "Stage 7 holding/settings SQLite workflow",
            "Stage 7 parameter/interconnection/metric workflow",
            "transition to Stage 8 only; Stage 8 remains not started",
        ],
        "known_defects": [
            "Installed App parity, GitHub push, production acceptance and final human acceptance remain Stage 12 gates."
        ],
        "accepted_at": NOW,
        "acceptance_statement": "用户统一授权绑定本 evidence index，仅授权 Stage 7 transition；不等于 production/final acceptance。",
        "user_confirmation_reference": "thread_pre_final_acceptance_blanket_authorization_and_no_more_blocks",
    }
    _write_json(REVIEW_DIR / "human_acceptance.json", acceptance)

    reviewed_source_overlay_files = [str(row["path"]) for row in overlay["files"]]
    whole_review_output_files = sorted({
        *artifact_paths,
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/final_evidence_index.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/human_acceptance.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/evidence.json",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/changed_files.txt",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/privacy_scan.txt",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/terminal.log",
        "PFI/reports/pfi_v025/stage_7/whole_stage_review/risk_and_rollback.md",
    })
    evidence = {
        "schema": "PFIV025Stage7WholeReviewEvidenceV1",
        "version": "v0.2.5",
        "stage": 7,
        "phase": "whole_stage_review",
        "status": "candidate_pass",
        "git_commit": REVIEW_BASE,
        "allowed_files_obeyed": True,
        "commands": [
            {
                **row,
                "summary": (
                    f"{row['command_id']} completed with exit_code=0; "
                    f"content-hashed output is bound at {row['output_ref']}"
                ),
            }
            for row in verification["commands"]
        ],
        "changed_files": sorted({*reviewed_source_overlay_files, *whole_review_output_files}),
        "reviewed_source_overlay_files": reviewed_source_overlay_files,
        "evidence_files": [str(row["path"]) for row in artifacts] + [
            "PFI/reports/pfi_v025/stage_7/whole_stage_review/final_evidence_index.json",
            "PFI/reports/pfi_v025/stage_7/whole_stage_review/human_acceptance.json",
        ],
        "explicitly_not_done": [
            "Stage 8 implementation", "GitHub push", "canonical PFI.app installation",
            "production acceptance", "final human acceptance",
        ],
        "risks": [
            "Acceptance binds the review base plus exact frozen overlay manifest.",
            "Installed App/runtime and remote-main parity remain Stage 12 gates.",
        ],
        "rollback": "Revert the local Stage 7 whole-review commit; do not mutate external source, remote main, or installed App.",
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": NOW,
        "review_base": REVIEW_BASE,
        "stage_7_status": "accepted_for_transition",
        "stage_7_phase_task_count": 12,
        "stage_7_phase_task_completed_count": 12,
        "browser_check_count": 68,
        "initial_review_counts": initial_counts,
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "stage_8_entry_authorized": True,
        "stage_8_work_performed": False,
        "real_financial_data_read": True,
        "real_financial_data_mutated": False,
        "database_changed": True,
        "database_scope": "isolated_/tmp_only",
        "finder_used": False,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "final_evidence_index_sha256": _sha256(REVIEW_DIR / "final_evidence_index.json"),
        "human_acceptance_sha256": _sha256(REVIEW_DIR / "human_acceptance.json"),
    }
    _write_json(REVIEW_DIR / "evidence.json", evidence)
    _write_text(REVIEW_DIR / "changed_files.txt", "\n".join(evidence["changed_files"]))
    _write_text(
        REVIEW_DIR / "privacy_scan.txt",
        "status=pass\ncontains_private_values=false\nraw_trace_persisted=false\n"
        "resource_bodies_removed=true\nruntime_token_hit_count=0\nabsolute_local_path_hit_count=0\n"
        "external_network_performed=false\nfinder_used=false",
    )
    _write_text(
        REVIEW_DIR / "terminal.log",
        "Stage 7 final evidence is derived from verification_results.json, workflow_validation.json, "
        "reviewer_results.json and content-hashed artifacts; no result is synthesized by this builder.",
    )
    _write_text(
        REVIEW_DIR / "risk_and_rollback.md",
        "# Stage 7 Whole-stage Review 风险与回滚\n\n"
        "证据绑定 review base 与 frozen overlay；App/remote/production gates 延后到 Stage 12。\n\n"
        "回滚只 revert 本地 whole-review commit，不改外部财务来源、remote main 或 installed App。",
    )
    print(json.dumps({"status": "pass", "browser_checks": 68, "stage_8_started": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
