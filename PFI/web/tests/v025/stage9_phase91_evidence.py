#!/usr/bin/env python3
"""Build fail-closed PFI v0.2.5 Stage 9 Phase 9.1 evidence."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker

from pfi_os.application.reports.contracts import (
    ACCEPTANCE_ID,
    COMPLETENESS_RULES_RELATIVE,
    PHASE_ID,
    REPORT_SCHEMA_RELATIVE,
    TASK_IDS,
    build_phase91_contract,
    build_phase91_report_pack,
    validate_phase91_report_pack,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
PFI_ROOT = REPO_ROOT / "PFI"
PHASE_DIR = PFI_ROOT / "reports/pfi_v025/stage_9/phase_9_1"
DOC_RELATIVE = Path(
    "docs/pfi_v025/stage_9/PHASE_9_1_REPORT_CONTRACT_IMPLEMENTATION.md"
)
INPUT_RELATIVES = (
    Path("reports/pfi_v025/stage_2/phase_2_1/source_manifest.json"),
    Path("reports/pfi_v025/stage_4/phase_4_3/read_model_status.json"),
    Path("reports/pfi_v025/stage_7/whole_stage_review/workflow_validation.json"),
    Path("config/formulas/v025_formula_registry.json"),
    Path("config/pfi_parameters.yaml"),
    REPORT_SCHEMA_RELATIVE,
    COMPLETENESS_RULES_RELATIVE,
    Path("src/pfi_os/application/reports/contracts.py"),
)
REQUIRED_COMMAND_IDS = {
    "phase91_target",
    "upstream_regression",
    "syntax_schema_diff",
    "changed_scope_governance",
}
SUPPORT_FILES = (
    "terminal.log",
    "changed_files.txt",
    "risk_and_rollback.md",
    "verification_results.json",
)
PRIVACY_SCAN_FILES = (
    "phase_contract.json",
    "report_schema.json",
    "completeness_rules.json",
    "report_manifest.json",
    "data_quality_report.json",
    "report_validation.json",
    "input_immutability.json",
    "verification_results.json",
    "terminal.log",
    "changed_files.txt",
    "risk_and_rollback.md",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
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


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes() -> dict[str, str]:
    return {
        relative.as_posix(): _sha(PFI_ROOT / relative)
        for relative in INPUT_RELATIVES
    }


def _require_support_files() -> dict[str, object]:
    for name in SUPPORT_FILES:
        if not (PHASE_DIR / name).is_file():
            raise RuntimeError(f"missing Phase 9.1 support file: {name}")
    verification = _json(PHASE_DIR / "verification_results.json")
    commands = verification.get("commands")
    if (
        verification.get("status") != "pass"
        or not isinstance(commands, list)
        or len(commands) != len(REQUIRED_COMMAND_IDS)
        or any(not isinstance(row, dict) for row in commands)
    ):
        raise RuntimeError("verification results are absent, failed or incomplete")
    ids = [str(row.get("command_id")) for row in commands if isinstance(row, dict)]
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_COMMAND_IDS:
        raise RuntimeError("verification command IDs are duplicated, missing or unexpected")
    for row in commands:
        if (
            row.get("exit_code") != 0
            or not isinstance(row.get("command"), str)
            or not str(row["command"]).strip()
            or not isinstance(row.get("summary"), str)
            or not str(row["summary"]).strip()
        ):
            raise RuntimeError(f"malformed verification result: {row.get('command_id')}")
    if any(
        verification.get(flag) is not False
        for flag in (
            "contains_private_values",
            "database_read",
            "database_changed",
            "formula_values_changed",
            "parameter_values_changed",
            "finder_used",
            "launchservices_used",
            "external_network_performed",
            "push_performed",
            "app_install_performed",
        )
    ):
        raise RuntimeError("verification safety flags are unsafe or missing")
    return verification


def _validate_schema(report_schema: dict[str, object], reports: list[object]) -> None:
    validator = Draft202012Validator(
        report_schema, format_checker=FormatChecker()
    )
    errors = [
        error.message
        for report in reports
        for error in validator.iter_errors(report)
    ]
    if errors:
        raise RuntimeError("report schema validation failed: " + "; ".join(errors))


def _privacy_scan() -> None:
    patterns = (
        re.compile(r"/Users/"),
        re.compile(r"(?i)(account[_ -]?number|card[_ -]?number|credential|password)"),
        re.compile(r"(?i)(mock|sample|demo|synthetic|fixture|fake)[_-]?financial"),
    )
    hits: list[str] = []
    for name in PRIVACY_SCAN_FILES:
        path = PHASE_DIR / name
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern.search(text):
                hits.append(f"{name}:{pattern.pattern}")
    if hits:
        raise RuntimeError("privacy scan failed: " + ", ".join(hits))
    (PHASE_DIR / "privacy_scan.txt").write_text(
        "forbidden_hits=0\n"
        "contains_private_values=false\n"
        "financial_values_emitted=0\n",
        encoding="utf-8",
    )


def main() -> int:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    verification = _require_support_files()
    observed_at = str(verification.get("observed_at") or _now())
    before = _input_hashes()
    pack = build_phase91_report_pack(PFI_ROOT, generated_at=observed_at)
    gate = validate_phase91_report_pack(pack, pfi_root=PFI_ROOT)
    if gate["status"] != "pass":
        raise RuntimeError("report pack validation failed")
    report_schema = _json(PFI_ROOT / REPORT_SCHEMA_RELATIVE)
    reports = pack["reports"]
    if not isinstance(reports, list):
        raise RuntimeError("report manifest reports must be a list")
    _validate_schema(report_schema, reports)

    _write_json(PHASE_DIR / "phase_contract.json", build_phase91_contract())
    _write_json(PHASE_DIR / "report_schema.json", report_schema)
    _write_json(
        PHASE_DIR / "completeness_rules.json",
        _json(PFI_ROOT / COMPLETENESS_RULES_RELATIVE),
    )
    _write_json(PHASE_DIR / "report_manifest.json", pack)
    _write_json(
        PHASE_DIR / "data_quality_report.json",
        next(
            report
            for report in reports
            if isinstance(report, dict) and report.get("report_type") == "data_quality"
        ),
    )
    _write_json(PHASE_DIR / "report_validation.json", gate)
    after = _input_hashes()
    immutability = {
        "schema": "PFIV025Stage9Phase91InputImmutabilityV1",
        "status": "pass" if before == after else "fail",
        "before": before,
        "after": after,
        "database_read": False,
        "database_changed": False,
        "real_financial_rows_read": False,
        "real_financial_source_mutated": False,
    }
    if immutability["status"] != "pass":
        raise RuntimeError("Phase 9.1 input files changed during evidence build")
    _write_json(PHASE_DIR / "input_immutability.json", immutability)
    _privacy_scan()

    artifact_names = (
        "phase_contract.json",
        "report_schema.json",
        "completeness_rules.json",
        "report_manifest.json",
        "data_quality_report.json",
        "report_validation.json",
        "input_immutability.json",
        "verification_results.json",
        "terminal.log",
        "changed_files.txt",
        "risk_and_rollback.md",
        "privacy_scan.txt",
    )
    artifact_hashes = {
        f"reports/pfi_v025/stage_9/phase_9_1/{name}": _sha(PHASE_DIR / name)
        for name in artifact_names
    }
    artifact_hashes[DOC_RELATIVE.as_posix()] = _sha(PFI_ROOT / DOC_RELATIVE)
    artifacts = {
        "schema": "PFIV025Stage9Phase91ArtifactHashesV1",
        "status": "pass",
        "files": artifact_hashes,
        "file_count": len(artifact_hashes),
    }
    _write_json(PHASE_DIR / "artifact_hashes.json", artifacts)

    evidence = {
        "schema": "PFIV025Stage9Phase91EvidenceV1",
        "version": "v0.2.5",
        "stage": 9,
        "phase": "9.1",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "task_statuses": {
            task_id: "candidate_complete" for task_id in TASK_IDS
        },
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "status": "candidate_pass",
        "risk_tier": "T2",
        "observed_at": observed_at,
        "report_manifest_hash": pack["manifest_hash"],
        "report_snapshot_hashes": {
            str(report["report_type"]): str(report["snapshot_hash"])
            for report in reports
            if isinstance(report, dict)
        },
        "input_hashes": pack["hashes"],
        "report_statuses": {
            str(report["report_type"]): str(report["status"])
            for report in reports
            if isinstance(report, dict)
        },
        "report_count": len(reports),
        "complete_report_count": sum(
            isinstance(report, dict) and report.get("status") == "complete"
            for report in reports
        ),
        "partial_report_count": sum(
            isinstance(report, dict) and report.get("status") == "partial"
            for report in reports
        ),
        "blocked_report_count": sum(
            isinstance(report, dict) and report.get("status") == "blocked"
            for report in reports
        ),
        "data_quality_report_generatable": True,
        "cross_report_hashes_consistent": gate[
            "cross_report_hashes_consistent"
        ],
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
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "phase_9_2_started": False,
        "phase_9_3_started": False,
        "stage_9_whole_stage_review_done": False,
        "requires_stage_whole_review": True,
        "production_accepted": False,
        "final_human_acceptance": False,
        "stage_9_status": "in_progress",
        "stage_9_completed_task_count": 4,
        "stage_9_total_task_count": 12,
        "overall_completed_task_count": 112,
        "overall_task_count": 156,
        "overall_progress_percent": 71.79,
        "next_task_id": "S9-P2-T1",
        "next_gate": ACCEPTANCE_ID,
        "verification_results_ref": (
            "PFI/reports/pfi_v025/stage_9/phase_9_1/verification_results.json"
        ),
        "verification_commands": verification["commands"],
        "artifact_hashes_ref": (
            "PFI/reports/pfi_v025/stage_9/phase_9_1/artifact_hashes.json"
        ),
        "artifact_hashes_sha256": _sha(PHASE_DIR / "artifact_hashes.json"),
        "evidence_refs": [
            f"PFI/{DOC_RELATIVE.as_posix()}",
            "PFI/config/reports/v025_report.schema.json",
            "PFI/config/reports/v025_completeness_rules.json",
            "PFI/reports/pfi_v025/stage_9/phase_9_1/report_manifest.json",
            "PFI/reports/pfi_v025/stage_9/phase_9_1/data_quality_report.json",
            "PFI/reports/pfi_v025/stage_9/phase_9_1/report_validation.json",
            "PFI/reports/pfi_v025/stage_9/phase_9_1/input_immutability.json",
            "PFI/reports/pfi_v025/stage_9/phase_9_1/artifact_hashes.json",
        ],
        "explicitly_not_done": [
            "Phase 9.2 financial analysis, sensitivity and model validation",
            "Phase 9.3 decision lifecycle, review and multi-format export",
            "Stage 9 whole-stage independent review, remediation, re-review and transition acceptance",
            "GitHub push, canonical PFI.app reinstall and production/final acceptance",
        ],
    }
    _write_json(PHASE_DIR / "evidence.json", evidence)
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "phase_id": PHASE_ID,
                "report_count": evidence["report_count"],
                "report_statuses": evidence["report_statuses"],
                "manifest_hash": evidence["report_manifest_hash"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
