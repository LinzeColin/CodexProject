#!/usr/bin/env python3
"""Validate KMFA v0.1.4 Stage 1-18 overall review evidence."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.check_lineage_completeness import validate_lineage_completeness_review  # noqa: E402
from KMFA.tools.v014_stage1_18_overall_review import (  # noqa: E402
    ACCEPTANCE_ID,
    GO_NO_GO_PATH,
    GO_NO_GO_RECORD_PATH,
    MANIFEST_PATH,
    METADATA_GO_NO_GO_PATH,
    METADATA_MANIFEST_PATH,
    NEXT_PHASE,
    REPORT_PATH,
    REVIEW_SCOPE,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    SCHEMA_VERSION,
    S05_P1_MANIFEST_PATH,
    S18_STAGE_REVIEW_PATH,
    TASK_ID,
    TEST_RESULTS_PATH,
)


REQUIRED_BLOCKERS = {
    "RAW_ALIGNMENT_NOT_PROVEN_COMPLETE",
    "RAW_PACKAGE_HASH_OR_SIZE_MISMATCH",
    "LINEAGE_FULL_CHECK_NOT_COMPLETE",
    "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
    "S09_PENDING_RECONCILIATION_12",
    "GITHUB_UPLOAD_BLOCKED_BY_RAW_ALIGNMENT_AND_LINEAGE",
    "APP_REINSTALL_BLOCKED_UNTIL_GITHUB_PARITY_AND_RELEASE_GATE",
}
PUBLIC_SAFETY_FALSE_KEYS = (
    "raw_business_data_committed",
    "compressed_raw_package_committed",
    "office_workbook_committed",
    "source_document_committed",
    "raw_or_private_table_committed",
    "local_database_committed",
    "credential_or_secret_committed",
    "raw_filenames_committed",
    "raw_hashes_committed",
    "field_or_header_plaintext_committed",
    "business_values_committed",
    "formal_report_committed",
    "github_upload_artifact_committed",
    "app_reinstall_artifact_committed",
    "production_restore_artifact_committed",
    "external_service_artifact_committed",
    "live_connector_artifact_committed",
)
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
FORBIDDEN_TRACKED_SUFFIXES = (
    ".zip",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".pdf",
    ".sqlite",
    ".sqlite3",
    ".sqlite-shm",
    ".sqlite-wal",
    ".db",
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


def validate_stage_review_validators(errors: list[str]) -> list[str]:
    passed: list[str] = []
    cache: dict[str, dict[str, Any]] = {}

    def patch_cached_stage_validators() -> None:
        for cached_stage_id, cached_payload in cache.items():
            attr_name = f"validate_v014_{cached_stage_id.lower()}_stage_review"
            for module in list(sys.modules.values()):
                if module is not None and hasattr(module, attr_name):
                    setattr(module, attr_name, lambda payload=cached_payload: payload)

    for stage_no in range(1, 19):
        stage_id = f"S{stage_no:02d}"
        patch_cached_stage_validators()
        module = importlib.import_module(f"KMFA.tools.check_v014_s{stage_no:02d}_stage_review")
        patch_cached_stage_validators()
        validator = getattr(module, f"validate_v014_s{stage_no:02d}_stage_review")
        try:
            payload = validator()
        except Exception as exc:  # pragma: no cover - surfaced in validator output
            errors.append(f"{stage_id} stage review validator failed: {exc}")
            continue
        require(str(payload.get("status", "")).startswith("review_passed"), f"{stage_id} status must be review_passed", errors)
        require(payload.get("stage_id") == stage_id, f"{stage_id} validator returned wrong stage_id", errors)
        require(payload.get("github_upload_performed") is False, f"{stage_id} must not have upload performed", errors)
        cache[stage_id] = payload
        passed.append(stage_id)
    return passed


def validate_no_v014_upload_artifacts(errors: list[str]) -> None:
    upload_dirs = sorted(Path("KMFA/stage_artifacts").glob("V014*UPLOAD*"))
    require(not upload_dirs, "v0.1.4 upload artifacts must not exist before final upload gate", errors)


def validate_tracked_public_suffixes(errors: list[str]) -> None:
    tracked = git_output(["ls-files", "KMFA"]).splitlines()
    forbidden = [path for path in tracked if path.lower().endswith(FORBIDDEN_TRACKED_SUFFIXES)]
    require(not forbidden, "forbidden raw/private tracked suffixes: " + ", ".join(forbidden[:20]), errors)


def validate_v014_stage1_18_overall_review(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    metadata_manifest = read_json(METADATA_MANIFEST_PATH)
    go_no_go = read_json(GO_NO_GO_PATH)
    metadata_go_no_go = read_json(METADATA_GO_NO_GO_PATH)
    s05_p1 = read_json(S05_P1_MANIFEST_PATH)
    s18 = read_json(S18_STAGE_REVIEW_PATH)
    validate_lineage_completeness_review()
    passed_stage_validators = validate_stage_review_validators(errors)

    require(metadata_manifest == manifest, "metadata manifest copy must match machine manifest", errors)
    require(metadata_go_no_go == go_no_go, "metadata Go/No-Go copy must match machine Go/No-Go", errors)
    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S01-S18", "stage_id mismatch", errors)
    require(manifest.get("phase_id") == "V014_STAGE1_18_OVERALL_REVIEW", "phase_id mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task_id mismatch", errors)
    require(manifest.get("acceptance_ids") == [ACCEPTANCE_ID], "acceptance_ids mismatch", errors)
    require(manifest.get("review_scope") == REVIEW_SCOPE, "review_scope mismatch", errors)
    require(
        manifest.get("status") == "overall_review_completed_local_only_no_go_upload_app_reinstall_blocked",
        "status mismatch",
        errors,
    )

    stage = manifest.get("stage_review_summary", {})
    require(stage.get("stage_review_count") == 18, "stage_review_count must be 18", errors)
    require(stage.get("stage_review_pass_count") == 18, "stage_review_pass_count must be 18", errors)
    require(stage.get("completed_stage_ids") == [f"S{i:02d}" for i in range(1, 19)], "completed stage ids mismatch", errors)
    require(stage.get("total_phase_count") == 54, "total_phase_count must be 54", errors)
    require(stage.get("total_task_count") == 162, "total_task_count must be 162", errors)
    require(stage.get("open_stage_review_finding_count") == 0, "open stage review findings must be 0", errors)
    require(stage.get("stage_validator_rerun_required_by_validator") is True, "stage validator rerun flag mismatch", errors)
    require(passed_stage_validators == [f"S{i:02d}" for i in range(1, 19)], "stage validator rerun list mismatch", errors)

    gates = manifest.get("final_readiness_gates", {})
    require(gates.get("stage_reviews_all_passed") is True, "stage review gate must pass", errors)
    require(gates.get("raw_alignment_complete") is False, "raw alignment must remain incomplete", errors)
    require(gates.get("lineage_full_check_complete") is False, "lineage full check must remain incomplete", errors)
    require(gates.get("official_report_release_allowed") is False, "official report release must be blocked", errors)
    require(gates.get("github_main_upload_allowed") is False, "GitHub upload must be blocked", errors)
    require(gates.get("app_reinstall_allowed") is False, "app reinstall must be blocked", errors)
    require(gates.get("current_go_no_go") == "NO_GO", "Go/No-Go must be NO_GO", errors)
    require(gates.get("current_report_grade") == "D", "report grade must be D", errors)
    require(gates.get("pending_reconciliation_count") == 12, "pending reconciliation count must be 12", errors)
    require(gates.get("html_audit_fail_count") == 0, "HTML audit fail count must be 0", errors)
    require(s18.get("stage_gate", {}).get("current_go_no_go") == "NO_GO", "S18 gate must remain NO_GO", errors)

    raw_gate = manifest.get("raw_alignment_gate", {})
    s05_raw = s05_p1.get("raw_alignment", {})
    require(raw_gate.get("s05_p1_private_raw_registration_evidence_present") is True, "S05-P1 private registration evidence must exist", errors)
    require(raw_gate.get("raw_alignment_complete") is False, "raw alignment gate must be false", errors)
    require(raw_gate.get("local_raw_package_hash_matches_registered") is False, "raw package hash match must be false", errors)
    require(raw_gate.get("local_raw_package_size_matches_registered") is False, "raw package size match must be false", errors)
    require(raw_gate.get("raw_publication_allowed") is False, "raw publication must be blocked", errors)
    require(raw_gate.get("raw_inbox_read_by_this_overall_review") is False, "raw inbox must not be read by this phase", errors)
    require(raw_gate.get("raw_inbox_mutated_by_this_overall_review") is False, "raw inbox must not be mutated", errors)
    require(raw_gate.get("public_raw_filenames_committed") is False, "public raw filenames must not be committed", errors)
    require(raw_gate.get("public_raw_hashes_committed") is False, "public raw hashes must not be committed", errors)
    require(s05_raw.get("local_raw_package_hash_matches_registered") is False, "S05-P1 package hash mismatch must remain recorded", errors)
    require(s05_raw.get("local_raw_package_size_matches_registered") is False, "S05-P1 package size mismatch must remain recorded", errors)

    lineage = manifest.get("lineage_gate", {})
    require(lineage.get("lineage_status") == "blocked_not_complete", "lineage status must be blocked_not_complete", errors)
    require(lineage.get("lineage_full_check_complete") is False, "lineage complete flag must be false", errors)
    require(lineage.get("official_report_release_allowed") is False, "lineage report release must be blocked", errors)
    require(lineage.get("github_upload_allowed") is False, "lineage GitHub upload must be blocked", errors)

    require(go_no_go == manifest.get("overall_go_no_go"), "manifest Go/No-Go must match machine Go/No-Go", errors)
    require(go_no_go.get("decision") == "NO_GO", "overall decision must be NO_GO", errors)
    require(go_no_go.get("delivery_allowed") is False, "delivery must be blocked", errors)
    require(go_no_go.get("github_upload_allowed") is False, "GitHub upload must be blocked", errors)
    require(go_no_go.get("app_reinstall_allowed") is False, "app reinstall must be blocked", errors)
    require(go_no_go.get("business_execution_allowed") is False, "business execution must be blocked", errors)
    require(REQUIRED_BLOCKERS.issubset(set(go_no_go.get("blocker_ids", []))), "required blockers missing", errors)
    require("V014_STAGE1_18_OVERALL_REVIEW_PENDING" not in go_no_go.get("blocker_ids", []), "overall review pending blocker must be resolved", errors)
    require(go_no_go.get("next_required_phase") == NEXT_PHASE, "next required phase mismatch", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)
    require(manifest.get("github_upload_performed") is False, "GitHub upload must not be performed", errors)
    require(manifest.get("github_upload_status") == "not_uploaded_blocked_by_raw_alignment_and_lineage", "GitHub upload status mismatch", errors)
    require(manifest.get("app_reinstall_performed") is False, "app reinstall must not be performed", errors)
    require(manifest.get("formal_report_release_performed") is False, "formal report release must not be performed", errors)
    require(manifest.get("business_execution_performed") is False, "business execution must not be performed", errors)
    require(manifest.get("raw_inbox_access_performed_by_this_phase") is False, "raw inbox access must not be performed", errors)
    require(manifest.get("next_phase") == NEXT_PHASE, "next phase mismatch", errors)

    for ref in manifest.get("evidence_refs", []):
        check_public_evidence_text(Path(ref), errors)
    for path in (
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
    ):
        check_public_evidence_text(path, errors)
    validate_no_v014_upload_artifacts(errors)
    validate_tracked_public_suffixes(errors)

    status = git_output(["status", "--short", "--branch"])
    require("codex/kmfa" in status, "git status must be on codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 Stage 1-18 overall review evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        manifest = validate_v014_stage1_18_overall_review(args.manifest)
    except Exception as exc:  # pragma: no cover - CLI guard
        print("FAIL: KMFA v0.1.4 Stage 1-18 overall review validation failed")
        print(exc)
        return 1
    stage = manifest["stage_review_summary"]
    gates = manifest["final_readiness_gates"]
    print(
        "PASS: KMFA v0.1.4 Stage 1-18 overall review validated "
        f"(stage_reviews={stage['stage_review_pass_count']}/{stage['stage_review_count']}, "
        f"phases={stage['total_phase_count']}, tasks={stage['total_task_count']}, "
        f"go_no_go={gates['current_go_no_go']}, report_grade={gates['current_report_grade']}, "
        f"pending_reconciliation={gates['pending_reconciliation_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"app_reinstall={str(manifest['app_reinstall_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
