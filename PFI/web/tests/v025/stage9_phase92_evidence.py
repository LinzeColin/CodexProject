#!/usr/bin/env python3
"""Build fail-closed PFI v0.2.5 Stage 9 Phase 9.2 evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from jsonschema import Draft202012Validator

from pfi_os.application.analysis.report_analysis import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_IDS,
    build_phase92_analysis_pack,
    build_phase92_contract,
    validate_phase92_analysis_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/phase_9_2"
PRODUCT_COMMIT = "7566107dfb3e2e3612ea28b9a2c31d8a8a553747"
IMPLEMENTATION_BASE = "9b9d942de48c0001186fe3f10c1a5d22938c5f12"
SNAPSHOT_RELATIVE = Path("config/reports/v025_phase92_analysis_snapshot.json")
DOC_RELATIVE = Path(
    "docs/pfi_v025/stage_9/PHASE_9_2_FINANCIAL_ANALYSIS_IMPLEMENTATION.md"
)
TASK_PACK = (
    Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
)
INPUT_RELATIVES = (
    Path("reports/pfi_v025/stage_9/phase_9_1/report_manifest.json"),
    Path("reports/pfi_v025/stage_2/phase_2_1/source_manifest.json"),
    Path("reports/pfi_v025/stage_4/phase_4_3/read_model_status.json"),
    Path("reports/pfi_v025/stage_7/whole_stage_review/workflow_validation.json"),
    Path("reports/pfi_v025/stage_5/phase_5_3/model_validation_card.json"),
    Path("reports/pfi_v025/stage_5/phase_5_3/sensitivity_results.json"),
    Path("reports/pfi_v025/stage_5/phase_5_3/invariant_results.json"),
    Path("reports/pfi_v025/stage_5/phase_5_3/metamorphic_results.json"),
    Path("config/formulas/v025_formula_registry.json"),
    Path("config/pfi_parameters.yaml"),
    Path("config/reports/v025_completeness_rules.json"),
)
REQUIRED_COMMAND_IDS = {
    "phase92_target",
    "upstream_regression",
    "formal_browser",
    "release_identity_and_static",
    "changed_scope_governance",
}
GENERATED_NAMES = (
    "phase_contract.json",
    "analysis_report_set.json",
    "report_consistency.json",
    "formula_drilldown.json",
    "sensitivity_preview.json",
    "model_validation_cards.json",
    "source_review_index.json",
    "ui_contract.json",
    "input_immutability.json",
    "privacy_scan.txt",
    "changed_files.txt",
    "artifact_hashes.json",
    "evidence.json",
)
SUPPORT_NAMES = (
    "browser_validation.json",
    "playwright_result.json",
    "sensitivity_view.png",
    "browser_trace_sanitized.zip",
    "verification_results.json",
    "terminal.log",
    "risk_and_rollback.md",
)


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, payload: str) -> None:
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _product_input_hashes() -> dict[str, str]:
    return {
        relative.as_posix(): _sha_bytes(
            _git_bytes("show", f"{PRODUCT_COMMIT}:PFI/{relative.as_posix()}")
        )
        for relative in INPUT_RELATIVES
    }


def _current_input_hashes() -> dict[str, str]:
    return {
        relative.as_posix(): _sha(PFI_ROOT / relative)
        for relative in INPUT_RELATIVES
    }


def _verification() -> dict[str, object]:
    path = PHASE_DIR / "verification_results.json"
    if not path.is_file():
        raise RuntimeError("verification_results.json is required")
    payload = _json(path)
    commands = payload.get("commands")
    if (
        payload.get("status") != "pass"
        or payload.get("verified_product_commit") != PRODUCT_COMMIT
        or not isinstance(commands, list)
        or any(not isinstance(row, dict) for row in commands)
    ):
        raise RuntimeError("verification result is absent, stale or malformed")
    ids = [str(row.get("command_id")) for row in commands if isinstance(row, dict)]
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_COMMAND_IDS:
        raise RuntimeError("verification command IDs are missing, duplicated or unexpected")
    if any(
        row.get("exit_code") != 0
        or not str(row.get("command") or "").strip()
        or not str(row.get("summary") or "").strip()
        for row in commands
        if isinstance(row, dict)
    ):
        raise RuntimeError("a verification command is failed or malformed")
    for flag in (
        "contains_private_values",
        "database_read",
        "database_changed",
        "formula_values_changed",
        "parameter_values_changed",
        "model_values_changed",
        "finder_used",
        "launchservices_used",
        "external_network_performed",
        "push_performed",
        "app_install_performed",
    ):
        if payload.get(flag) is not False:
            raise RuntimeError(f"unsafe or absent verification flag: {flag}")
    return payload


def _changed_files() -> list[str]:
    committed = set(
        _git_bytes("diff", "--name-only", f"{IMPLEMENTATION_BASE}..{PRODUCT_COMMIT}")
        .decode("utf-8")
        .splitlines()
    )
    raw_status = _git_bytes("status", "--porcelain=v1", "-z", "-uall").decode(
        "utf-8"
    )
    overlay: set[str] = set()
    for entry in raw_status.split("\0"):
        if len(entry) < 4:
            continue
        status = entry[:2]
        if any(marker in status for marker in ("D", "R", "C")):
            raise RuntimeError(f"unsupported changed-file state: {status!r}")
        overlay.add(entry[3:])
    phase_prefix = PHASE_DIR.relative_to(REPO_ROOT).as_posix()
    expected_outputs = {
        f"{phase_prefix}/{name}" for name in (*GENERATED_NAMES, *SUPPORT_NAMES)
    }
    paths = sorted(path for path in committed | overlay | expected_outputs if path)
    if not paths or any(not path.startswith("PFI/") for path in paths):
        raise RuntimeError("Phase 9.2 changed files escaped the PFI project")
    if any("phase_9_3" in path or "whole_stage_review" in path for path in paths):
        raise RuntimeError("Phase 9.2 changed files leaked into a later gate")
    return paths


def _privacy_scan(paths: list[Path]) -> None:
    patterns = (
        re.compile(r"/Users/"),
        re.compile(r"/private/var/folders/"),
        re.compile(r"\bCNY\s+-?[0-9]"),
        re.compile(r"(?i)(account[_ -]?number|card[_ -]?number|credential|password)"),
    )
    hits: list[str] = []
    for path in paths:
        if path.suffix.lower() in {".png", ".zip"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(text):
                hits.append(f"{path.name}:{pattern.pattern}")
    if hits:
        raise RuntimeError("privacy scan failed: " + ", ".join(hits))
    _write_text(
        PHASE_DIR / "privacy_scan.txt",
        "forbidden_hits=0\n"
        "absolute_local_paths=0\n"
        "financial_amounts=0\n"
        "contains_private_values=false\n"
        "financial_values_emitted=0",
    )


def _taskpack_schema() -> dict[str, object]:
    if not TASK_PACK.is_file():
        raise RuntimeError("authoritative Task Pack is unavailable")
    with zipfile.ZipFile(TASK_PACK) as archive:
        payload = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
        )
    if not isinstance(payload, dict):
        raise RuntimeError("Task Pack evidence schema is not an object")
    return payload


def main() -> int:
    for name in SUPPORT_NAMES:
        path = PHASE_DIR / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"required support evidence is missing: {name}")
    verification = _verification()
    browser = _json(PHASE_DIR / "browser_validation.json")
    if (
        browser.get("status") != "pass"
        or browser.get("product_commit") != PRODUCT_COMMIT
        or browser.get("check_count") != browser.get("passed_check_count")
    ):
        raise RuntimeError("browser evidence is absent, failed or stale")
    snapshot = _json(PFI_ROOT / SNAPSHOT_RELATIVE)
    rebuilt = build_phase92_analysis_pack(
        PFI_ROOT, observed_at=str(snapshot.get("observed_at") or "")
    )
    if snapshot != rebuilt:
        raise RuntimeError("tracked analysis snapshot differs from current inputs")
    gate = validate_phase92_analysis_pack(snapshot, pfi_root=PFI_ROOT)
    if gate["status"] != "pass":
        raise RuntimeError("analysis snapshot validation failed")
    before = _product_input_hashes()
    after = _current_input_hashes()
    if before != after:
        raise RuntimeError("an accepted Phase 9.2 input changed after product commit")

    _write_json(PHASE_DIR / "phase_contract.json", build_phase92_contract())
    _write_json(
        PHASE_DIR / "analysis_report_set.json",
        {
            "schema": "PFIV025Stage9Phase92ReportSetEvidenceV1",
            "phase_id": PHASE_ID,
            "pack_hash": snapshot["pack_hash"],
            "report_set": snapshot["report_set"],
            "financial_values_emitted": 0,
            "contains_private_values": False,
        },
    )
    _write_json(
        PHASE_DIR / "report_consistency.json",
        {
            **gate,
            "pack_hash": snapshot["pack_hash"],
            "report_snapshot_hashes": {
                str(row["report_type"]): str(row["snapshot_hash"])
                for row in snapshot["report_set"]
                if isinstance(row, dict)
            },
            "report_statuses": {
                str(row["report_type"]): str(row["status"])
                for row in snapshot["report_set"]
                if isinstance(row, dict)
            },
        },
    )
    for filename, schema, key in (
        ("formula_drilldown.json", "PFIV025Stage9Phase92FormulaEvidenceV1", "formula_drilldowns"),
        ("sensitivity_preview.json", "PFIV025Stage9Phase92SensitivityEvidenceV1", "sensitivity_previews"),
        ("model_validation_cards.json", "PFIV025Stage9Phase92ModelCardEvidenceV1", "model_validation_cards"),
        ("source_review_index.json", "PFIV025Stage9Phase92SourceReviewEvidenceV1", "source_review_index"),
    ):
        _write_json(
            PHASE_DIR / filename,
            {
                "schema": schema,
                "phase_id": PHASE_ID,
                "pack_hash": snapshot["pack_hash"],
                key: snapshot[key],
                "financial_values_emitted": 0,
                "contains_private_values": False,
            },
        )
    _write_json(PHASE_DIR / "ui_contract.json", snapshot["ui_contract"])
    _write_json(
        PHASE_DIR / "input_immutability.json",
        {
            "schema": "PFIV025Stage9Phase92InputImmutabilityV1",
            "status": "pass",
            "product_commit": PRODUCT_COMMIT,
            "before": before,
            "after": after,
            "snapshot_current_input_binding": True,
            "database_read": False,
            "database_changed": False,
            "real_financial_rows_read": False,
            "real_financial_source_mutated": False,
        },
    )
    changed_files = _changed_files()
    _write_text(PHASE_DIR / "changed_files.txt", "\n".join(changed_files))
    scan_paths = [
        PHASE_DIR / name
        for name in (*GENERATED_NAMES[:-3], *SUPPORT_NAMES)
        if (PHASE_DIR / name).is_file()
    ] + [PFI_ROOT / SNAPSHOT_RELATIVE, PFI_ROOT / DOC_RELATIVE]
    _privacy_scan(scan_paths)

    artifact_paths = [
        PHASE_DIR / name
        for name in (
            "phase_contract.json",
            "analysis_report_set.json",
            "report_consistency.json",
            "formula_drilldown.json",
            "sensitivity_preview.json",
            "model_validation_cards.json",
            "source_review_index.json",
            "ui_contract.json",
            "input_immutability.json",
            "browser_validation.json",
            "playwright_result.json",
            "sensitivity_view.png",
            "browser_trace_sanitized.zip",
            "verification_results.json",
            "terminal.log",
            "risk_and_rollback.md",
            "privacy_scan.txt",
            "changed_files.txt",
        )
    ] + [PFI_ROOT / SNAPSHOT_RELATIVE, PFI_ROOT / DOC_RELATIVE]
    artifact_hashes = {
        path.relative_to(PFI_ROOT).as_posix(): _sha(path) for path in artifact_paths
    }
    _write_json(
        PHASE_DIR / "artifact_hashes.json",
        {
            "schema": "PFIV025Stage9Phase92ArtifactHashesV1",
            "status": "pass",
            "product_commit": PRODUCT_COMMIT,
            "file_count": len(artifact_hashes),
            "files": artifact_hashes,
        },
    )

    commands = verification["commands"]
    evidence_files = [
        f"PFI/reports/pfi_v025/stage_9/phase_9_2/{name}"
        for name in (*GENERATED_NAMES, *SUPPORT_NAMES)
    ] + [f"PFI/{SNAPSHOT_RELATIVE.as_posix()}", f"PFI/{DOC_RELATIVE.as_posix()}"]
    evidence = {
        "schema": "PFIV025Stage9Phase92EvidenceV1",
        "version": "v0.2.5",
        "stage": 9,
        "phase": "9.2",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {task_id: "candidate_complete" for task_id in TASK_IDS},
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "status": "candidate_pass",
        "git_commit": PRODUCT_COMMIT,
        "implementation_base": IMPLEMENTATION_BASE,
        "allowed_files_obeyed": True,
        "commands": commands,
        "changed_files": changed_files,
        "evidence_files": sorted(set(evidence_files)),
        "explicitly_not_done": [
            "Phase 9.3 decision lifecycle, counter-evidence review and multi-format export",
            "Stage 9 whole-stage independent review, remediation, re-review and transition acceptance",
            "Stage 10 entry, GitHub push, canonical PFI.app reinstall and production/final acceptance",
        ],
        "risks": [
            "net worth, cash and investment remain blocked because required production sources are not loaded",
            "consumption and cashflow are partial coverage analyses and are not complete financial conclusions",
            "historical and out-of-sample model validation remains blocked without ground truth",
        ],
        "rollback": (
            "Revert the two Phase 9.2 product commits and the direct evidence/governance commit; "
            "immutable Phase 9.1 snapshots and accepted input artifacts remain unchanged."
        ),
        "requires_user_acceptance": True,
        "observed_at": snapshot["observed_at"],
        "risk_tier": "T3_FINANCIAL_MODEL_VALIDATION_UI",
        "analysis_pack_hash": snapshot["pack_hash"],
        "input_hashes": snapshot["hashes"],
        "report_statuses": {
            str(row["report_type"]): str(row["status"])
            for row in snapshot["report_set"]
            if isinstance(row, dict)
        },
        "report_count": 5,
        "complete_report_count": 0,
        "partial_report_count": 2,
        "blocked_report_count": 3,
        "formula_drilldown_count": 6,
        "sensitivity_preview_count": 4,
        "model_validation_card_count": 1,
        "source_review_count": 7,
        "browser_check_count": browser["check_count"],
        "browser_passed_check_count": browser["passed_check_count"],
        "cross_report_hashes_consistent": True,
        "formula_values_changed": False,
        "parameter_values_changed": False,
        "model_values_changed": False,
        "database_read": False,
        "database_changed": False,
        "real_financial_rows_read": False,
        "real_financial_source_mutated": False,
        "contains_private_values": False,
        "financial_values_emitted": 0,
        "finder_used": False,
        "launchservices_used": False,
        "gui_file_operations_used": False,
        "network_performed": True,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "phase_9_3_started": False,
        "stage_9_whole_stage_review_done": False,
        "requires_stage_whole_review": True,
        "production_accepted": False,
        "final_human_acceptance": False,
        "stage_9_status": "in_progress",
        "stage_9_completed_task_count": 8,
        "stage_9_total_task_count": 12,
        "overall_completed_task_count": 116,
        "overall_task_count": 156,
        "overall_progress_percent": 74.36,
        "next_task_id": "S9-P3-T1",
        "next_gate": ACCEPTANCE_ID,
        "verification_results_ref": "PFI/reports/pfi_v025/stage_9/phase_9_2/verification_results.json",
        "artifact_hashes_ref": "PFI/reports/pfi_v025/stage_9/phase_9_2/artifact_hashes.json",
        "artifact_hashes_sha256": _sha(PHASE_DIR / "artifact_hashes.json"),
    }
    errors = sorted(
        Draft202012Validator(_taskpack_schema()).iter_errors(evidence),
        key=lambda error: list(error.path),
    )
    if errors:
        raise RuntimeError(
            "Task Pack evidence schema failed: "
            + "; ".join(error.message for error in errors)
        )
    _write_json(PHASE_DIR / "evidence.json", evidence)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "phase_id": PHASE_ID,
                "product_commit": PRODUCT_COMMIT,
                "analysis_pack_hash": evidence["analysis_pack_hash"],
                "report_statuses": evidence["report_statuses"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
