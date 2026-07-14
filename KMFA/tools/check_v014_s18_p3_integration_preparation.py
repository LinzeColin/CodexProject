#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S18-P3 integration-preparation evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_s18_p3_integration_preparation import (  # noqa: E402
    ACCEPTANCE_ID,
    BACKLOG_PATH,
    BACKLOG_RECORD_PATH,
    CONNECTOR_PLAN_PATH,
    CONNECTOR_PLAN_RECORD_PATH,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MACHINE_DIR,
    MANIFEST_PATH,
    METADATA_BACKLOG_PATH,
    METADATA_CONNECTOR_PLAN_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    METADATA_OPME_PLAN_PATH,
    NEXT_PHASE,
    NEXT_REQUIRED_STEP,
    OPME_PLAN_PATH,
    OPME_PLAN_RECORD_PATH,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_BACKLOG_IDS,
    REQUIRED_CONNECTOR_IDS,
    REQUIRED_OPME_ENTRY_SURFACES,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    _phase_boundaries,
    _public_repo_safety,
    _quality_gate,
    _raw_boundary,
    load_v14_taskpack_baseline,
    validate_historical_s18_p3_public_safe_baseline,
    validate_s18_p2_dependency,
)


FALSE_PUBLIC_SAFETY_KEYS = tuple(key for key, value in _public_repo_safety().items() if value is False)
FALSE_RAW_KEYS = tuple(key for key, value in _raw_boundary().items() if value is False)
TRUE_QUALITY_KEYS = tuple(key for key, value in _quality_gate().items() if value is True)
FALSE_QUALITY_KEYS = tuple(key for key, value in _quality_gate().items() if value is False)
TRUE_PHASE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is True)
FALSE_PHASE_KEYS = tuple(key for key, value in _phase_boundaries().items() if value is False)

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "original_filename",
    "member_sha256:",
    "actual_package_sha256",
    "authoritative_value_cents",
    "system_value_cents",
    "amount_cents:",
    "amount_yuan:",
    "sheet_name:",
    "row_value:",
    "cell_value:",
    "business_data:",
    "bank_statement_payload",
    "contract_full_text",
    "salary_detail",
    "tax_filing_material",
    "connector_" + "token:",
    "connector_" + "pass" + "word:",
    "api" + "_key:",
    "private" + "_key:",
    "credential_material",
    "report_attachment_path",
    "production_restore_material",
    "external_service_material",
    "live_connector_material",
    "app_reinstall_material",
    "-----" "BEGIN",
    "s" "k-",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "supplier_name_plaintext",
    "payment_account",
    "account_number:",
    "invoice_number:",
    "tax_identifier:",
    "private_ref://",
    "recipient_" + "email",
    "smtp",
    "KMFA" "_MetaData",
    "/Users/linzezhang/Downloads",
    ".xlsx",
    ".xls",
    ".zip",
    ".pdf",
    ".sqlite",
    ".db",
)
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api" + r"_key|token)\s*=\s*[^\s,;]{8,}"),
)


class ValidationError(Exception):
    pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValidationError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValidationError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValidationError(f"{path} contains a non-object JSONL row")
        rows.append(value)
    return rows


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _require_false_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is False, f"{label}.{key} must be false", errors)


def _require_true_keys(record: dict[str, Any], keys: tuple[str, ...], label: str, errors: list[str]) -> None:
    for key in keys:
        require(record.get(key) is True, f"{label}.{key} must be true", errors)


def check_public_evidence_text(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public evidence: {path}", errors)
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public evidence text {forbidden!r} in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"secret-like token found in {path}: {pattern.pattern}", errors)


def validate_v014_s18_p3_integration_preparation(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    connector_plans = read_jsonl(CONNECTOR_PLAN_PATH)
    metadata_connector_plans = read_jsonl(METADATA_CONNECTOR_PLAN_PATH)
    opme_plan = read_json(OPME_PLAN_PATH)
    metadata_opme_plan = read_json(METADATA_OPME_PLAN_PATH)
    backlog_items = read_jsonl(BACKLOG_PATH)
    metadata_backlog_items = read_jsonl(METADATA_BACKLOG_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    s18_p2 = validate_s18_p2_dependency()
    legacy_manifest, legacy_connectors, legacy_opme, legacy_backlog = validate_historical_s18_p3_public_safe_baseline()
    baseline = load_v14_taskpack_baseline()

    require(metadata_manifest == manifest, "metadata manifest copy must match machine manifest", errors)
    require(metadata_connector_plans == connector_plans, "metadata connector copy must match machine connector rows", errors)
    require(metadata_opme_plan == opme_plan, "metadata opme copy must match machine opme plan", errors)
    require(metadata_backlog_items == backlog_items, "metadata backlog copy must match machine backlog rows", errors)
    require(metadata_go_no_go == go_no_go, "metadata Go/No-Go copy must match machine Go/No-Go", errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema_version mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S18", "stage_id must be S18", errors)
    require(manifest.get("phase_id") == "S18-P3", "phase_id mismatch", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase_scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance id mismatch", errors)
    require(manifest.get("completed_task_ids") == ["S18P3T01", "S18P3T02", "S18P3T03"], "task ids mismatch", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_required_step") == NEXT_REQUIRED_STEP, "next required step mismatch", errors)
    require(manifest.get("branch") == git_output(["branch", "--show-current"]), "manifest branch mismatch", errors)
    require(manifest.get("s18_p2_dependency_validated") is True, "S18-P2 dependency flag missing", errors)
    require(s18_p2.get("next_phase") == "S18-P3", "S18-P2 dependency must route to S18-P3", errors)
    require(
        manifest.get("historical_s18_p3_public_safe_baseline_validated") is True,
        "legacy S18-P3 baseline validation flag missing",
        errors,
    )
    require(legacy_manifest.get("stage_phase") == "S18-P3", "legacy manifest stage phase mismatch", errors)
    require(len(legacy_connectors) == 3, "legacy connector count mismatch", errors)
    require(len(legacy_opme.get("entry_surfaces", [])) == 4, "legacy opme surface count mismatch", errors)
    require(len(legacy_backlog) == 6, "legacy backlog count mismatch", errors)
    require(manifest.get("required_connector_ids") == list(REQUIRED_CONNECTOR_IDS), "required connector ids mismatch", errors)
    require(
        manifest.get("required_opme_entry_surfaces") == list(REQUIRED_OPME_ENTRY_SURFACES),
        "required opme surfaces mismatch",
        errors,
    )
    require(manifest.get("required_backlog_ids") == list(REQUIRED_BACKLOG_IDS), "required backlog ids mismatch", errors)

    progress = manifest.get("stage18_phase_progress", {})
    require(progress.get("completed_phase_count") == 3, "completed phase count mismatch", errors)
    require(progress.get("total_phase_count") == 3, "total phase count mismatch", errors)
    require(progress.get("derived_percent_bps") == 10000, "progress bps mismatch", errors)
    require(progress.get("derived_percent_label") == "100.00%", "progress label mismatch", errors)
    require(progress.get("s18_p1_performed") is True, "S18-P1 must be performed", errors)
    require(progress.get("s18_p2_performed") is True, "S18-P2 must be performed", errors)
    require(progress.get("s18_p3_performed") is True, "S18-P3 must be performed", errors)
    require(progress.get("stage18_review_performed") is False, "Stage18 review must not be performed", errors)

    summary = manifest.get("integration_preparation_summary", {})
    require(summary.get("connector_plan_count") == 3, "connector count mismatch", errors)
    require(summary.get("read_only_connector_count") == 3, "read-only connector count mismatch", errors)
    require(summary.get("opme_entry_surface_count") == 4, "opme surface count mismatch", errors)
    require(summary.get("backlog_item_count") == 6, "backlog count mismatch", errors)
    require(summary.get("live_connector_call_count") == 0, "live connector count must be zero", errors)
    require(summary.get("external_service_call_count") == 0, "external service count must be zero", errors)
    require(summary.get("source_mutation_allowed_count") == 0, "source mutation count must be zero", errors)
    require(summary.get("next_required_phase") == NEXT_PHASE, "next required phase mismatch", errors)

    quality = manifest.get("quality_gate", {})
    _require_true_keys(quality, TRUE_QUALITY_KEYS, "quality_gate", errors)
    _require_false_keys(quality, FALSE_QUALITY_KEYS, "quality_gate", errors)
    _require_false_keys(manifest.get("raw_data_boundary", {}), FALSE_RAW_KEYS, "raw_data_boundary", errors)
    _require_true_keys(manifest.get("phase_boundaries", {}), TRUE_PHASE_KEYS, "phase_boundaries", errors)
    _require_false_keys(manifest.get("phase_boundaries", {}), FALSE_PHASE_KEYS, "phase_boundaries", errors)
    _require_false_keys(manifest.get("public_repo_safety", {}), FALSE_PUBLIC_SAFETY_KEYS, "public_repo_safety", errors)
    require(baseline == manifest.get("v14_taskpack_baseline"), "v1.4 taskpack baseline mismatch", errors)

    connector_ids = tuple(row.get("connector_id") for row in connector_plans)
    require(connector_ids == REQUIRED_CONNECTOR_IDS, "connector id ordering mismatch", errors)
    for row in connector_plans:
        require(row.get("record_type") == "v014_s18_p3_read_only_connector_plan", "connector record type mismatch", errors)
        require(row.get("schema_version") == "kmfa.v014_s18_p3_read_only_connector_plan.v1", "connector schema mismatch", errors)
        require(row.get("project_id") == "KMFA", "connector project mismatch", errors)
        require(row.get("phase_id") == "S18-P3", "connector phase mismatch", errors)
        require(row.get("task_id") == "S18P3T01", "connector task mismatch", errors)
        require(row.get("integration_mode") == "read_only_future_connector", "connector mode mismatch", errors)
        require(row.get("lifecycle_state") == "proposal_only", "connector lifecycle mismatch", errors)
        for key in ("manual_authorization_required", "hash_retention_required", "rollback_required"):
            require(row.get(key) is True, f"connector {row.get('connector_id')}.{key} must be true", errors)
        for key in (
            "source_mutation_allowed",
            "auto_write_allowed",
            "credential_required_now",
            "live_connector_called",
            "external_service_called",
            "raw_business_data_committed",
            "field_plaintext_committed",
            "github_upload_allowed",
            "business_execution_allowed",
        ):
            require(row.get(key) is False, f"connector {row.get('connector_id')}.{key} must be false", errors)

    require(opme_plan == manifest.get("opme_entry_plan"), "manifest opme plan mismatch", errors)
    require(opme_plan.get("record_type") == "v014_s18_p3_opme_entry_integration_plan", "opme record type mismatch", errors)
    require(tuple(opme_plan.get("entry_surfaces", ())) == REQUIRED_OPME_ENTRY_SURFACES, "opme surfaces mismatch", errors)
    require(opme_plan.get("integration_mode") == "entry_link_and_status_index_only", "opme integration mode mismatch", errors)
    require(opme_plan.get("coupling_level") == "light_entry_only", "opme coupling level mismatch", errors)
    for key in (
        "deep_coupling_allowed",
        "shared_database_allowed",
        "sensitive_data_mixing_allowed",
        "opme_controls_kmfa_business_logic",
        "kmfa_controls_opme_service_logic",
        "external_service_called",
        "raw_business_data_committed",
        "field_plaintext_committed",
        "credential_committed",
        "github_upload_allowed",
        "business_execution_allowed",
    ):
        require(opme_plan.get(key) is False, f"opme.{key} must be false", errors)

    backlog_ids = tuple(row.get("backlog_id") for row in backlog_items)
    require(backlog_ids == REQUIRED_BACKLOG_IDS, "backlog id ordering mismatch", errors)
    for row in backlog_items:
        require(row.get("record_type") == "v014_s18_p3_next_stage_backlog_item", "backlog record type mismatch", errors)
        require(row.get("phase_id") == "S18-P3", "backlog phase mismatch", errors)
        require(row.get("task_id") == "S18P3T03", "backlog task mismatch", errors)
        require(row.get("status") == "backlog_proposed_not_started", "backlog status mismatch", errors)
        for key in (
            "started",
            "business_execution_allowed",
            "external_connector_allowed",
            "github_upload_allowed",
            "raw_business_data_required_in_public_repo",
        ):
            require(row.get(key) is False, f"backlog {row.get('backlog_id')}.{key} must be false", errors)

    require(connector_plans == manifest.get("read_only_connector_plans"), "manifest connector rows mismatch", errors)
    require(backlog_items == manifest.get("next_stage_backlog"), "manifest backlog rows mismatch", errors)
    require(go_no_go == manifest.get("go_no_go"), "manifest Go/No-Go mismatch", errors)
    require(go_no_go.get("decision") == "NO_GO", "Go/No-Go decision mismatch", errors)
    require(go_no_go.get("delivery_allowed") is False, "delivery must be false", errors)
    require(go_no_go.get("business_decision_basis_allowed") is False, "business basis must be false", errors)
    require(go_no_go.get("github_upload_allowed") is False, "github upload allowed must be false", errors)
    require(go_no_go.get("s18_p3_pending") is False, "S18-P3 must no longer be pending", errors)
    for blocker in (
        "STAGE18_REVIEW_PENDING",
        "LINEAGE_FULL_CHECK_NOT_COMPLETE",
        "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
        "GITHUB_UPLOAD_DEFERRED_UNTIL_V014_STAGE1_18_COMPLETE",
    ):
        require(blocker in go_no_go.get("blocker_ids", []), f"missing blocker {blocker}", errors)
    require("S18_P3_PENDING" not in go_no_go.get("blocker_ids", []), "S18_P3_PENDING blocker must be resolved", errors)

    github = manifest.get("github_upload", {})
    require(github.get("github_upload_performed") is False, "GitHub upload must be false", errors)
    require(
        github.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete",
        "GitHub upload status mismatch",
        errors,
    )
    require(github.get("github_upload_deferred_until_v014_stage1_18_complete") is True, "upload defer flag missing", errors)

    for path in (
        REPORT_PATH,
        CONNECTOR_PLAN_RECORD_PATH,
        OPME_PLAN_RECORD_PATH,
        BACKLOG_RECORD_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        CONNECTOR_PLAN_PATH,
        OPME_PLAN_PATH,
        BACKLOG_PATH,
        GO_NO_GO_PATH,
    ):
        check_public_evidence_text(path, errors)
    require(MACHINE_DIR.exists(), "machine evidence dir missing", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S18-P3 integration preparation evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    manifest = validate_v014_s18_p3_integration_preparation(args.manifest)
    summary = manifest["integration_preparation_summary"]
    print(
        "PASS: KMFA v0.1.4 S18-P3 integration preparation validated "
        f"(connectors={summary['connector_plan_count']}, "
        f"opme_surfaces={summary['opme_entry_surface_count']}, "
        f"backlog={summary['backlog_item_count']}, "
        "live_connector_called=false, stage18_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
