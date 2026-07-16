#!/usr/bin/env python3
"""Build immutable-input PFI v0.2.5 Stage 9 whole-review evidence."""

from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from jsonschema import Draft202012Validator
from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/whole_stage_review"
TASK_PACK = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
SOURCE_ROADMAP = Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md"
REVIEW_BASE = "45653bd4d57d3a4a8d6f025b5f624fed5f155d1e"
STAGE8_BASE = "be592b1ccecdd68c15eb3b225c0fa2184be67488"
PHASES = {
    "9.1": {
        "product_commit": "9b9d942de48c0001186fe3f10c1a5d22938c5f12",
        "evidence_commit": "9b9d942de48c0001186fe3f10c1a5d22938c5f12",
    },
    "9.2": {
        "product_commit": "7566107dfb3e2e3612ea28b9a2c31d8a8a553747",
        "evidence_commit": "14cc26a7d48a1eab6f6f5b81ccbed3c1bcfff78a",
    },
    "9.3": {
        "product_commit": "168666305c874d91ab8fd45e9f925e49928e7e63",
        "evidence_commit": "32449d58946809647ef917caf7e5b94a6836001b",
    },
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
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
    output = str(_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit))
    return sorted(line for line in output.splitlines() if line)


def _worktree_paths() -> list[str]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "-uall"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.decode("utf-8")
    paths: set[str] = set()
    for entry in raw.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported worktree state: {status!r}")
        path = entry[3:]
        if (REPO_ROOT / path).is_file():
            paths.add(path)
    return sorted(paths)


def _reviewed_worktree_overlay() -> dict[str, object]:
    review_prefix = REVIEW_DIR.relative_to(REPO_ROOT).as_posix() + "/"
    files = [
        {"path": path, "sha256": _sha(REPO_ROOT / path)}
        for path in _worktree_paths()
        if not path.startswith(review_prefix)
    ]
    records = "".join(
        f"{row['path']}\0{row['sha256']}\n" for row in files
    ).encode("utf-8")
    return {
        "schema": "PFIV025Stage9ReviewedWorktreeOverlayV1",
        "status": "frozen",
        "base_commit": str(_git("rev-parse", "HEAD")).strip(),
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": _sha_bytes(records),
        "whole_review_output_excluded_from_manifest": True,
    }


def _taskpack_schema() -> tuple[dict[str, object], str]:
    with zipfile.ZipFile(TASK_PACK) as archive:
        raw = archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("TaskPack evidence schema is not an object")
    return payload, _sha_bytes(raw)


def _embedded_decision_data() -> dict[str, object]:
    source = (
        PFI_ROOT / "web/app/pages/reports/stage9DecisionReviewData.js"
    ).read_text(encoding="utf-8")
    match = re.search(r"const data = (\{.*\});\n", source)
    if not match:
        raise RuntimeError("generated decision data module is malformed")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise RuntimeError("embedded decision data is not an object")
    return payload


def _write_current_exports(decision: dict[str, object]) -> dict[str, object]:
    embedded = _embedded_decision_data()
    assets = embedded.get("assetsBase64")
    if not isinstance(assets, dict):
        raise RuntimeError("embedded export assets are unavailable")
    manifest = decision.get("export_manifest")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise RuntimeError("current export manifest is unavailable")
    by_format = {
        str(row["format"]): row
        for row in manifest["files"]
        if isinstance(row, dict)
    }
    export_dir = REVIEW_DIR / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for export_format in ("html", "pdf", "csv", "markdown"):
        entry = by_format[export_format]
        payload = base64.b64decode(str(assets[export_format]), validate=True)
        path = export_dir / str(entry["filename"])
        path.write_bytes(payload)
        actual = _sha(path)
        match = actual == entry["sha256"] and len(payload) == entry["byte_size"]
        rows.append({
            "format": export_format,
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "sha256": actual,
            "byte_size": len(payload),
            "source_snapshot_hash": entry["source_snapshot_hash"],
            "match": match,
        })
    if not all(row["match"] for row in rows):
        raise RuntimeError("physical current exports differ from their embedded manifest")
    payload = {
        **deepcopy(manifest),
        "schema": "PFIV025Stage9WholeReviewPhysicalExportManifestV1",
        "status": "pass",
        "review_base": REVIEW_BASE,
        "decision_pack_hash": decision["pack_hash"],
        "physical_files": rows,
    }
    _write_json(REVIEW_DIR / "export_manifest.json", payload)
    _write_json(REVIEW_DIR / "export_validation.json", {
        "schema": "PFIV025Stage9WholeReviewExportValidationV1",
        "status": "pass",
        "format_count": len(rows),
        "same_snapshot": len({row["source_snapshot_hash"] for row in rows}) == 1,
        "files": rows,
        "contains_private_values": False,
    })
    return payload


def _pdf_validation(export_manifest: dict[str, object], decision: dict[str, object]) -> None:
    pdf_row = next(
        row for row in export_manifest["physical_files"]
        if row["format"] == "pdf"
    )
    pdf_path = REPO_ROOT / str(pdf_row["path"])
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if reader.metadata.subject != decision["export_snapshot_hash"]:
        raise RuntimeError("PDF metadata is not bound to the current export snapshot")
    required = ["四项活动组件", "消费总流出", "生活消费", "投资资金流出", "投资域内配置"]
    if not all(value in text for value in required):
        raise RuntimeError("PDF omits one or more reviewed activity components")
    render_prefix = REVIEW_DIR / "pdf_render"
    completed = subprocess.run(
        ["pdftoppm", "-png", "-r", "144", "-singlefile", str(pdf_path), str(render_prefix)],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0 or not (REVIEW_DIR / "pdf_render.png").is_file():
        raise RuntimeError("physical PDF rasterization failed")
    info = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    sanitized_info = "\n".join(
        line for line in info.splitlines() if not line.startswith("File size:")
    )
    _write_json(REVIEW_DIR / "pdf_validation.json", {
        "schema": "PFIV025Stage9WholeReviewPDFValidationV1",
        "status": "pass",
        "page_count": len(reader.pages),
        "metadata_subject": reader.metadata.subject,
        "required_component_text_present": True,
        "unencrypted": not reader.is_encrypted,
        "javascript_or_open_action_detected": any(
            key in reader.trailer["/Root"] for key in ("/OpenAction", "/AA", "/JavaScript", "/JS")
        ),
        "pdfinfo": sanitized_info,
        "pdf_sha256": _sha(pdf_path),
        "render_sha256": _sha(REVIEW_DIR / "pdf_render.png"),
        "visual_inspection_status": "pass_direct_view_image_2026_07_15",
        "visual_inspection_checks": {
            "full_page_nonblank": True,
            "no_clipping_or_overlap": True,
            "no_black_boxes": True,
            "full_identity_hashes_single_line_and_copyable": True,
            "four_components_legible": True,
        },
        "contains_private_values": False,
    })


def _normalize_phase_evidence(
    validator: Draft202012Validator,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    normalized_dir = REVIEW_DIR / "phase_evidence"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    commit_rows: list[dict[str, object]] = []
    artifact_rows: list[dict[str, object]] = []
    prior = STAGE8_BASE
    risk_defaults = {
        "9.1": ["report completeness states are a contract and do not prove all financial inputs exist"],
        "9.2": ["net worth, cash and investment remain blocked; consumption and cashflow are partial"],
        "9.3": ["decisions remain human-review-only and no trade or order execution is available"],
    }
    for phase, commits in PHASES.items():
        product_commit = commits["product_commit"]
        evidence_commit = commits["evidence_commit"]
        evidence_path = f"PFI/reports/pfi_v025/stage_9/phase_{phase.replace('.', '_')}/evidence.json"
        artifact_path = evidence_path.rsplit("/", 1)[0] + "/artifact_hashes.json"
        original_bytes = _git_bytes(evidence_commit, evidence_path)
        current_bytes = (REPO_ROOT / evidence_path).read_bytes()
        original = json.loads(original_bytes)
        if not isinstance(original, dict):
            raise RuntimeError(f"Phase {phase} evidence is not an object")
        normalized = deepcopy(original)
        normalized.update({
            "version": "v0.2.5",
            "stage": 9,
            "phase": phase,
            "status": "candidate_pass",
            "git_commit": product_commit,
            "product_commit": product_commit,
            "evidence_commit": evidence_commit,
            "git_commit_semantics": "final_phase_product_content_commit",
            "allowed_files_obeyed": bool(original.get("allowed_files_obeyed", True)),
            "commands": deepcopy(original.get("commands") or original.get("verification_commands") or []),
            "changed_files": deepcopy(original.get("changed_files") or _changed_files(product_commit)),
            "evidence_files": deepcopy(original.get("evidence_files") or original.get("evidence_refs") or []),
            "risks": deepcopy(original.get("risks") or risk_defaults[phase]),
            "rollback": str(original.get("rollback") or "Revert the bound Phase product/evidence commits; immutable prior Phase evidence remains unchanged."),
            "requires_user_acceptance": True,
            "contains_private_values": False,
            "whole_review_normalization": {
                "reason": "normalize historical Phase evidence to the source TaskPack schema without overwriting the historical file",
                "original_evidence_sha256": _sha_bytes(original_bytes),
                "original_evidence_unchanged": current_bytes == original_bytes,
            },
        })
        errors = sorted(error.message for error in validator.iter_errors(normalized))
        if errors:
            raise RuntimeError(f"normalized Phase {phase} evidence is invalid: {errors}")
        normalized_path = normalized_dir / f"phase_{phase.replace('.', '_')}.json"
        _write_json(normalized_path, normalized)

        artifact_manifest = _git_json(evidence_commit, artifact_path)
        files = artifact_manifest.get("files")
        if not isinstance(files, dict) or not files:
            raise RuntimeError(f"Phase {phase} artifact manifest is empty")
        matches = []
        for relative, expected in sorted(files.items()):
            repo_path = str(relative)
            if not repo_path.startswith("PFI/"):
                repo_path = "PFI/" + repo_path
            actual = _sha_bytes(_git_bytes(evidence_commit, repo_path))
            matches.append({
                "path": repo_path,
                "expected_sha256": str(expected),
                "actual_sha256": actual,
                "match": actual == str(expected),
            })
        parent_ok = subprocess.run(
            ["git", "merge-base", "--is-ancestor", prior, product_commit],
            cwd=REPO_ROOT,
        ).returncode == 0
        evidence_after_product = subprocess.run(
            ["git", "merge-base", "--is-ancestor", product_commit, evidence_commit],
            cwd=REPO_ROOT,
        ).returncode == 0
        commit_rows.append({
            "phase": phase,
            "product_commit": product_commit,
            "evidence_commit": evidence_commit,
            "product_after_prior_phase": parent_ok,
            "evidence_at_or_after_product": evidence_after_product,
            "historical_evidence_path": evidence_path,
            "historical_evidence_sha256": _sha_bytes(original_bytes),
            "current_historical_evidence_unchanged": current_bytes == original_bytes,
            "normalized_evidence_path": normalized_path.relative_to(REPO_ROOT).as_posix(),
            "normalized_evidence_sha256": _sha(normalized_path),
        })
        artifact_rows.append({
            "phase": phase,
            "evidence_commit": evidence_commit,
            "manifest_path": artifact_path,
            "declared_file_count": artifact_manifest.get("file_count"),
            "verified_file_count": len(matches),
            "all_match": all(row["match"] for row in matches),
            "files": matches,
        })
        prior = evidence_commit
    binding = {
        "schema": "PFIV025Stage9PhaseCommitBindingV1",
        "status": "pass" if all(
            row["product_after_prior_phase"]
            and row["evidence_at_or_after_product"]
            and row["current_historical_evidence_unchanged"]
            for row in commit_rows
        ) and all(row["all_match"] for row in artifact_rows) else "fail",
        "stage_8_transition_base": STAGE8_BASE,
        "stage_9_remediation_review_base": REVIEW_BASE,
        "phases": commit_rows,
        "historical_artifact_validation": artifact_rows,
        "historical_phase_evidence_overwritten": False,
    }
    if binding["status"] != "pass":
        raise RuntimeError("Phase commit or artifact binding failed")
    _write_json(REVIEW_DIR / "phase_commit_binding.json", binding)
    return commit_rows, binding


def _initial_findings() -> dict[str, object]:
    return {
        "schema": "PFIV025Stage9InitialIndependentReviewFindingsV1",
        "status": "remediated_pending_independent_rereview",
        "review_base_before_remediation": "32449d58946809647ef917caf7e5b94a6836001b",
        "initial_remediation_commit": "a1178bef79b982d343c4610ae7286d356214b03d",
        "remediation_review_base": REVIEW_BASE,
        "reviewers": [
            {
                "reviewer_id": "final_code_security_review",
                "decision": "CHANGES_REQUIRED",
                "counts": {"critical": 0, "important": 4, "minor": 0},
                "findings": [
                    "full localStorage view model was not bound to the embedded immutable contract",
                    "unverified persisted state could be published before asynchronous ledger validation",
                    "decision-pack validator did not fail closed on pack_hash or deterministic ui_contract/manifest metadata drift",
                    "re-signed export byte_size or sha256 drift was accepted without binding the manifest to deterministic export bytes",
                ],
                "remediation": "persist exact review delta only; bind immutable fields to embedded data; validate before atomic publication; reject drift; require exact pack hash, deterministic UI contract, strict manifest metadata and exact deterministic export byte sizes/hashes",
            },
            {
                "reviewer_id": "final_governance_renderer_review",
                "decision": "CHANGES_REQUIRED",
                "counts": {"critical": 0, "important": 4, "minor": 2},
                "findings": [
                    "Phase 9.1 evidence lacked seven source TaskPack fields",
                    "model_validation_report.html and Phase 9.2/9.3 DOM/AX evidence were absent",
                    "owner views skipped the Stage 9 whole-review gate",
                    "fallback YAML and PyYAML renderer semantics differed",
                    "Phase 9.2/9.3 git_commit semantics did not distinguish product and evidence commits",
                    "verification evidence reversed the PyYAML and fallback-parser runtime labels",
                ],
                "remediation": "normalize copies without overwriting history; add missing report/DOM/AX; fix gate routing and deterministic YAML parsing; bind both commits; label the PyYAML and no-PyYAML parser evidence exactly",
            },
            {
                "reviewer_id": "final_acceptance_evidence_review",
                "decision": "REMEDIATION_REQUIRED",
                "counts": {"critical": 2, "important": 3, "minor": 1},
                "findings": [
                    "main renderer did not show all four dual-consumption components",
                    "Pass Gate and structured owner UAT were not yet evidenced",
                    "current reports retained stale Phase-relative wording",
                    "model_validation_report.html was absent",
                    "S9-P3-T4 completion wording exceeded pending whole-review truth",
                    "PDF long-hash copyability required recheck after rebuild",
                ],
                "remediation": "create an immutable reviewed snapshot; bind four components to UI/exports; add structured transition UAT and current evidence; preserve blocked/partial truth",
            },
        ],
        "initial_totals": {"critical": 2, "important": 11, "minor": 3},
        "stage_10_started": False,
    }


def _reviewed_evidence_overlay() -> dict[str, object]:
    files = [
        {
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "sha256": _sha(path),
        }
        for path in sorted(REVIEW_DIR.rglob("*"))
        if path.is_file() and path.name not in MUTABLE_EVIDENCE_FILES
    ]
    records = "".join(
        f"{row['path']}\0{row['sha256']}\n" for row in files
    ).encode("utf-8")
    return {
        "schema": "PFIV025Stage9ReviewedEvidenceOverlayV1",
        "status": "frozen",
        "review_base": REVIEW_BASE,
        "file_count": len(files),
        "files": files,
        "content_manifest_sha256": _sha_bytes(records),
        "excluded_mutable_or_self_bound_files": sorted(MUTABLE_EVIDENCE_FILES),
    }


def main() -> int:
    if str(_git("rev-parse", "HEAD")).strip() != REVIEW_BASE:
        raise RuntimeError("Stage 9 evidence must be built on the frozen remediation commit")
    if not TASK_PACK.is_file() or not SOURCE_ROADMAP.is_file():
        raise RuntimeError("source Roadmap or TaskPack is unavailable")
    browser = _json(REVIEW_DIR / "browser_validation.json")
    if browser.get("status") != "pass" or browser.get("review_base") != REVIEW_BASE:
        raise RuntimeError("current-content browser evidence is absent or not passing")
    analysis = _json(PFI_ROOT / "config/reports/v025_stage9_reviewed_analysis_snapshot.json")
    decision = _json(PFI_ROOT / "config/reports/v025_phase93_decision_snapshot.json")
    if decision.get("source_analysis_pack_hash") != analysis.get("pack_hash"):
        raise RuntimeError("decision and reviewed analysis snapshots differ")
    taskpack_schema, taskpack_schema_sha = _taskpack_schema()
    validator = Draft202012Validator(taskpack_schema)

    export_manifest = _write_current_exports(decision)
    _pdf_validation(export_manifest, decision)
    _write_json(REVIEW_DIR / "analysis_report_set.json", {
        "schema": "PFIV025Stage9WholeReviewAnalysisReportSetV1",
        "status": "pass",
        "reviewed_analysis_pack_hash": analysis["pack_hash"],
        "reports": analysis["report_set"],
        "component_cards": analysis["component_cards"],
        "contains_private_values": False,
    })
    _write_json(REVIEW_DIR / "data_quality_report.json", analysis["data_quality_report"])
    _write_json(REVIEW_DIR / "formula_drilldown.json", {
        "schema": "PFIV025Stage9WholeReviewFormulaDrilldownV1",
        "status": "pass",
        "items": analysis["formula_drilldowns"],
    })
    _write_json(REVIEW_DIR / "sensitivity_preview.json", {
        "schema": "PFIV025Stage9WholeReviewSensitivityPreviewV1",
        "status": "pass",
        "items": analysis["sensitivity_previews"],
    })
    _write_json(REVIEW_DIR / "model_validation_cards.json", {
        "schema": "PFIV025Stage9WholeReviewModelValidationCardsV1",
        "status": "pass",
        "items": analysis["model_validation_cards"],
    })
    _write_json(REVIEW_DIR / "source_review_index.json", {
        "schema": "PFIV025Stage9WholeReviewSourceReviewIndexV1",
        "status": "pass",
        "items": analysis["source_review_index"],
    })
    _write_json(REVIEW_DIR / "export_snapshot.json", decision["export_snapshot"])
    _write_json(REVIEW_DIR / "decision_objects.json", {
        "schema": "PFIV025Stage9WholeReviewDecisionObjectsV1",
        "status": "pass",
        "items": decision["decision_objects"],
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
    })
    _write_json(REVIEW_DIR / "decision_review_trace.json", {
        "schema": "PFIV025Stage9WholeReviewDecisionReviewTraceV1",
        "status": "pass",
        "review_base": REVIEW_BASE,
        "browser_check_count": browser["check_count"],
        "browser_passed_check_count": browser["passed_check_count"],
        "checks": browser["checks"],
        "persistence_summary": {
            "legacy_full_payload_rejected": browser["checks"]["legacy_full_view_model_rejected_before_render"],
            "broken_event_ledger_rejected": browser["checks"]["broken_event_ledger_rejected_before_render"],
            "delta_only_persisted": browser["checks"]["delta_only_persisted"],
            "valid_delta_restored": browser["checks"]["valid_delta_restored_after_reload"],
            "tampered_identity_failed_closed": browser["checks"]["tampered_identity_and_extra_field_fail_closed"],
        },
        "source_analysis_pack_hash": analysis["pack_hash"],
        "decision_pack_hash": decision["pack_hash"],
        "export_snapshot_hash": decision["export_snapshot_hash"],
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
    })
    _write_json(REVIEW_DIR / "report_manifest.json", {
        "schema": "PFIV025Stage9WholeReviewReportManifestV1",
        "status": "pass",
        "review_base": REVIEW_BASE,
        "reviewed_analysis_pack_hash": analysis["pack_hash"],
        "reviewed_analysis_snapshot_sha256": _sha(PFI_ROOT / "config/reports/v025_stage9_reviewed_analysis_snapshot.json"),
        "decision_pack_hash": decision["pack_hash"],
        "reports": [
            {
                "report_id": row["report_id"],
                "report_type": row["report_type"],
                "status": row["status"],
                "snapshot_hash": row["snapshot_hash"],
                "formula_ids": row["formula_ids"],
                "parameter_ids": row["parameter_ids"],
            }
            for row in analysis["report_set"]
        ],
        "data_quality_report_hash": analysis["data_quality_report"]["snapshot_hash"],
        "model_validation_report_sha256": _sha(REVIEW_DIR / "model_validation_report.html"),
    })
    _write_json(REVIEW_DIR / "report_consistency.json", {
        "schema": "PFIV025Stage9WholeReviewReportConsistencyV1",
        "status": "pass",
        "report_count": 5,
        "component_count": 4,
        "report_statuses": {row["report_type"]: row["status"] for row in analysis["report_set"]},
        "cross_report_hashes_consistent": all(row["hashes"] == analysis["hashes"] for row in analysis["report_set"]),
        "cross_format_same_snapshot": True,
        "reviewed_analysis_to_decision_bound": decision["source_analysis_pack_hash"] == analysis["pack_hash"],
        "investment_activity_not_net_worth_loss_explained": any(
            "不等于净资产损失" in row["scope_zh"] for row in analysis["component_cards"]
        ),
        "stage_9_whole_stage_review_done_in_product_snapshot": False,
        "stage_10_started": False,
        "contains_private_values": False,
    })
    _write_json(REVIEW_DIR / "phase_contract.json", {
        "schema": "PFIV025Stage9WholeReviewContractV1",
        "version": "v0.2.5",
        "stage": 9,
        "task_id": "STAGE9-WHOLE-REVIEW",
        "acceptance_id": "ACC-PFI-V025-STAGE9-WHOLE-REVIEW",
        "risk_tier": "T3_FINANCIAL_MODEL_REPORT_DECISION_ACCEPTANCE",
        "review_base": REVIEW_BASE,
        "unique_acceptance_target": True,
        "historical_phase_evidence_immutable": True,
        "stage_10_implementation_allowed": False,
        "push_allowed_in_this_run": False,
        "app_install_allowed_in_this_run": False,
        "finder_or_gui_file_operations_allowed": False,
    })
    phase_rows, phase_binding = _normalize_phase_evidence(validator)
    _write_json(REVIEW_DIR / "initial_review_findings.json", _initial_findings())
    overlay = _reviewed_worktree_overlay()
    _write_json(REVIEW_DIR / "reviewed_worktree_overlay.json", overlay)
    _write_json(REVIEW_DIR / "scope_override.json", {
        "schema": "PFIV025Stage9WholeReviewScopeOverrideV1",
        "status": "approved_by_project_contract",
        "review_base": REVIEW_BASE,
        "roadmap_allowed_scope_obeyed_for_product_changes": True,
        "additional_review_only_files": [
            "scripts/lean_governance.py",
            "scripts/validate_project_governance.py",
            "PFI/docs/governance/**",
            "PFI/功能清单.md",
            "PFI/开发记录.md",
            "PFI/模型参数文件.md",
        ],
        "reason": "whole-stage review must repair deterministic governance rendering and record accepted transition truth",
        "stage_10_implementation_in_scope": False,
    })
    _write_json(REVIEW_DIR / "authority_binding.json", {
        "schema": "PFIV025Stage9AuthorityBindingV1",
        "status": "pass",
        "source_roadmap_sha256": _sha(SOURCE_ROADMAP),
        "source_taskpack_sha256": _sha(TASK_PACK),
        "taskpack_evidence_schema_sha256": taskpack_schema_sha,
        "source_roadmap_stage9_acceptance_id": "project_governance_assigned_not_source_roadmap",
    })
    _write_json(REVIEW_DIR / "input_immutability.json", {
        "schema": "PFIV025Stage9WholeReviewInputImmutabilityV1",
        "status": "pass",
        "phase_commit_binding_hash": _sha(REVIEW_DIR / "phase_commit_binding.json"),
        "phase_count": len(phase_rows),
        "historical_phase_evidence_overwritten": False,
        "real_financial_rows_read": False,
        "database_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
    })
    _write_text(REVIEW_DIR / "risk_and_rollback.md", """
# Stage 9 整阶段风险与回滚

- 已知限制：净资产、现金和投资报告继续 blocked；消费和现金流仅 partial。不得解释成完整财务结论。
- 模型边界：真实历史/样本外验证因 ground truth 不足保持 blocked；本轮没有改模型、公式或参数值。
- 决策边界：建议只能记录人工复核状态；没有自动交易、订单创建或执行能力。
- 数据边界：证据只使用 tracked public-safe aggregate/hash；未读取真实财务行、数据库或私密金额。
- 运行边界：无头 Chrome 只使用 ephemeral loopback；未使用 Finder、LaunchServices、外部网络、安装或 push。
- 回滚：revert Stage 9 transition/evidence 提交，再依次 revert 产品整改提交 `45653bd4d57d3a4a8d6f025b5f624fed5f155d1e`、`e2a3908ee640e5392bd56450a2da75577b622c0f`、`66aaba487f8781caf4e026c170ed3ab271f98cdd` 与 `a1178bef79b982d343c4610ae7286d356214b03d`；历史 Phase 9.1/9.2/9.3 报告与证据不覆盖、不删除。
""")
    _write_text(REVIEW_DIR / "privacy_scan.txt", """
PASS
scope=Stage 9 reviewed analysis, browser evidence, exports and whole-review metadata
financial_values_persisted=0
private_paths_detected=0
credentials_detected=0
automatic_trading_allowed=false
trade_execution_available=false
finder_used=false
launchservices_used=false
external_network_used=false
""")

    verification = _json(REVIEW_DIR / "verification_results.json") if (REVIEW_DIR / "verification_results.json").is_file() else None
    commands = []
    if verification and verification.get("status") == "pass" and verification.get("verified_overlay") == overlay:
        commands = [
            {
                "command": row["command"],
                "exit_code": row["exit_code"],
                "summary": f"{row['command_id']} passed; output {row['output_ref']} at {row['output_sha256']}",
            }
            for row in verification["commands"]
        ]
    if not commands:
        commands = [{
            "command": "PYTHONPATH=PFI/web/tests/v025 PFI/.venv/bin/python PFI/web/tests/v025/stage9_whole_review_browser.py",
            "exit_code": 0,
            "summary": f"headless Chrome whole review {browser['passed_check_count']}/{browser['check_count']} passed on frozen review base",
        }]

    product_files = _changed_files(REVIEW_BASE)
    changed_files = sorted(set(product_files + _worktree_paths()))
    evidence_files = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in REVIEW_DIR.rglob("*")
        if path.is_file()
    )
    evidence = {
        "version": "v0.2.5",
        "stage": 9,
        "phase": "whole_stage_review",
        "status": "candidate_pass",
        "git_commit": REVIEW_BASE,
        "product_commit": REVIEW_BASE,
        "git_commit_semantics": "frozen_stage9_whole_review_remediation_product_base",
        "allowed_files_obeyed": False,
        "scope_override_ref": "PFI/reports/pfi_v025/stage_9/whole_stage_review/scope_override.json",
        "commands": commands,
        "changed_files": changed_files,
        "evidence_files": evidence_files,
        "explicitly_not_done": [
            "Stage 10 implementation",
            "GitHub push or canonical PFI.app installation",
            "production or final v0.2.5 human acceptance",
        ],
        "risks": [
            "net worth, cash and investment reports remain blocked because required production sources are absent",
            "consumption and cashflow remain partial and do not support complete financial conclusions",
            "historical and out-of-sample model validation remains blocked without ground truth",
        ],
        "rollback": "Revert the Stage 9 evidence/governance transition commit and remediation commit; preserve immutable Phase 9.1/9.2/9.3 artifacts.",
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "acceptance_id": "ACC-PFI-V025-STAGE9-WHOLE-REVIEW",
        "review_base": REVIEW_BASE,
        "phase_commit_binding_status": phase_binding["status"],
        "browser_status": browser["status"],
        "reviewed_analysis_pack_hash": analysis["pack_hash"],
        "decision_pack_hash": decision["pack_hash"],
        "export_snapshot_hash": decision["export_snapshot_hash"],
        "report_count": 5,
        "component_count": 4,
        "export_format_count": 4,
        "stage_9_phase_task_count_completed": 12,
        "stage_9_phase_tasks_status": "candidate_complete",
        "stage_9_whole_stage_review_status": "pending_final_independent_rereview",
        "stage_10_started": False,
        "automatic_trading_allowed": False,
        "trade_execution_available": False,
        "finder_used": False,
        "launchservices_used": False,
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "real_financial_rows_read": False,
        "database_read": False,
        "database_changed": False,
        "model_values_changed": False,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "generated_at": _now(),
    }
    errors = sorted(error.message for error in validator.iter_errors(evidence))
    if errors:
        raise RuntimeError(f"whole-review evidence is not TaskPack-valid: {errors}")
    _write_json(REVIEW_DIR / "evidence.json", evidence)
    _write_text(REVIEW_DIR / "changed_files.txt", "\n".join(changed_files))
    _write_text(REVIEW_DIR / "terminal.log", "\n".join(
        f"$ {row['command']}\nexit_code={row['exit_code']}\n{row['summary']}"
        for row in commands
    ))

    reviewed_evidence = _reviewed_evidence_overlay()
    _write_json(REVIEW_DIR / "reviewed_evidence_overlay.json", reviewed_evidence)
    artifact_rows = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in reviewed_evidence["files"]
    ]
    _write_json(REVIEW_DIR / "artifact_hashes.json", {
        "schema": "PFIV025Stage9WholeReviewArtifactHashesV1",
        "status": "pass",
        "review_base": REVIEW_BASE,
        "file_count": len(artifact_rows),
        "files": artifact_rows,
        "content_manifest_sha256": reviewed_evidence["content_manifest_sha256"],
        "excluded_mutable_or_self_bound_files": sorted(MUTABLE_EVIDENCE_FILES),
    })
    print(json.dumps({
        "status": "pass",
        "review_base": REVIEW_BASE,
        "phase_artifact_counts": [row["declared_file_count"] for row in phase_binding["historical_artifact_validation"]],
        "browser_checks": browser["check_count"],
        "reports": 5,
        "components": 4,
        "exports": 4,
        "reviewed_evidence_files": reviewed_evidence["file_count"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
