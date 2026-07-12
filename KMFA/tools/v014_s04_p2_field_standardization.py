#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S04-P2 field standardization evidence.

This phase locks field standardization, alias mapping, and missing/invalid
field quality-status behavior with synthetic public-safe values only. It does
not read, list, hash, mutate, or write the local raw data inbox, and it does
not perform S04-P3, Stage 4 review, GitHub upload, raw value matching, formal
reporting, live connector calls, or business execution.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_stage_review import RAW_INBOX
from KMFA.tools.check_v014_s04_p1_amount_precision import validate_v014_s04_p1_amount_precision
from KMFA.tools.field_standardization import CANONICAL_FIELDS, build_mapping_record, standardize_record


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S04_P2_FIELD_STANDARDIZATION")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/field_standardization_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/field_standardization_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = PUBLIC_OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = PUBLIC_OUTPUT_DIR / "human/rollback_plan.md"
ALIAS_DICTIONARY_PATH = Path("KMFA/metadata/schema_maps/field_alias_dictionary.csv")
FIELD_POLICY_PATH = Path("KMFA/metadata/schema_maps/field_standardization_policy.yaml")
FIELD_QUALITY_PROTOCOL_PATH = Path("KMFA/metadata/quality/field_quality_status.jsonl")
TASK_ID = "KMFA-V014-S04-P2-FIELD-STANDARDIZATION-20260704"
SCHEMA_VERSION = "kmfa.v014_s04_p2_field_standardization.v1"


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def count_alias_dictionary_rows(path: Path = ALIAS_DICTIONARY_PATH) -> int:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def replay_field_standardization_capability() -> dict[str, Any]:
    evidence_ref = TEST_RESULTS_PATH.as_posix()
    source_id = "SRC-v014-s04p2-public-safe-synthetic"
    import_run_id = "IMP-v014-s04p2-public-safe-synthetic"
    mapping_version = "MAP-v014-s04p2-public-safe-v0.1.4"
    event_time = "2026-07-04T03:00:00+10:00"

    row = {
        "日期": "2026年6月29日",
        "所属期间": "202606",
        "主体": " 公开主体 A ",
        "项目名称": " 示例 项目 ",
        "客户": " 示例客户 ",
        "合同号": " kmfa - demo - 001 ",
    }
    standardized = standardize_record(
        row,
        source_id=source_id,
        import_run_id=import_run_id,
        mapping_version=mapping_version,
        evidence_ref=evidence_ref,
        event_time=event_time,
    )
    expected_values = {
        "document_date": "2026-06-29",
        "period_month": "2026-06",
        "company_entity": "公开主体 A",
        "project_name": "示例 项目",
        "counterparty": "示例客户",
        "contract_number": "KMFA-DEMO-001",
    }
    standardization_results = [
        {
            "canonical_field": field,
            "expected_value": expected,
            "actual_value": standardized["standardized_fields"].get(field),
            "passed": standardized["standardized_fields"].get(field) == expected,
        }
        for field, expected in expected_values.items()
    ]

    mapping_records = [
        build_mapping_record(
            source_id=source_id,
            mapping_version=mapping_version,
            source_field_alias=alias,
            evidence_ref=evidence_ref,
        )
        for alias in ("业务日期", "会计期间", "公司主体", "工程名称", "客户名称", "合同编码")
    ]

    quality_replay = standardize_record(
        {"日期": "2026-13-01", "期间": "2026-06"},
        source_id=source_id,
        import_run_id=import_run_id,
        mapping_version=mapping_version,
        evidence_ref=evidence_ref,
        event_time=event_time,
    )
    quality_statuses = quality_replay["quality_statuses"]

    return {
        "canonical_fields": list(CANONICAL_FIELDS),
        "canonical_field_count": len(CANONICAL_FIELDS),
        "alias_dictionary_row_count": count_alias_dictionary_rows(),
        "mapping_record_count": len(mapping_records),
        "mapping_records_public_safe": all(
            record.get("raw_layer_write_allowed") is False
            and record.get("raw_source_mutation_allowed") is False
            and record.get("source_field_alias_hash", "").startswith("sha256:")
            and "raw_value" not in record
            and "source_header_text" not in record
            for record in mapping_records
        ),
        "standardization_case_results": standardization_results,
        "standardization_case_count": len(standardization_results),
        "standardization_case_passed_count": sum(1 for item in standardization_results if item["passed"]),
        "quality_status_count": len(quality_statuses),
        "quality_statuses_public_safe": all(
            status.get("record_type") == "field_quality_status"
            and status.get("raw_layer_write_allowed") is False
            and status.get("raw_source_mutation_allowed") is False
            and status.get("field_skipped_silently") is False
            and "raw_value" not in status
            and "original_value" not in status
            for status in quality_statuses
        ),
        "quality_status_issue_types": sorted({status["issue_type"] for status in quality_statuses}),
        "quality_passed_for_complete_synthetic_row": standardized["quality_passed"],
        "quality_passed_for_incomplete_synthetic_row": quality_replay["quality_passed"],
    }


def build_manifest() -> dict[str, Any]:
    s04_p1 = validate_v014_s04_p1_amount_precision()
    replay = replay_field_standardization_capability()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S04",
        "stage_name": "v0.1.4 amount precision field standardization and basic tools",
        "phase_id": "S04-P2",
        "phase_name": "field standardization",
        "phase_scope": "v014_s04_p2_field_standardization_only",
        "task_id": TASK_ID,
        "acceptance_id": "ACC-V014-S04-P2-FIELD-STANDARDIZATION",
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "completed_task_ids": ["S4PBT01", "S4PBT02", "S4PBT03"],
        "s04_p1_dependency_validated": (
            s04_p1.get("phase_id") == "S04-P1"
            and s04_p1.get("status") == "completed_validated_local_only_no_go_upload_deferred"
            and s04_p1.get("github_upload_performed") is False
            and "S04-P2" in s04_p1.get("next_required_step", "")
        ),
        "s04_p1_dependency_ref": "KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json",
        "field_standardization_dependency_validated": (
            replay["canonical_field_count"] == 6
            and replay["standardization_case_count"] == replay["standardization_case_passed_count"] == 6
            and replay["quality_status_count"] == 5
            and replay["mapping_records_public_safe"] is True
            and replay["quality_statuses_public_safe"] is True
        ),
        "canonical_fields": replay["canonical_fields"],
        "canonical_field_count": replay["canonical_field_count"],
        "alias_dictionary_row_count": replay["alias_dictionary_row_count"],
        "mapping_record_count": replay["mapping_record_count"],
        "mapping_records_public_safe": replay["mapping_records_public_safe"],
        "standardization_case_count": replay["standardization_case_count"],
        "standardization_case_passed_count": replay["standardization_case_passed_count"],
        "standardization_case_results": replay["standardization_case_results"],
        "quality_status_count": replay["quality_status_count"],
        "quality_status_issue_types": replay["quality_status_issue_types"],
        "quality_statuses_public_safe": replay["quality_statuses_public_safe"],
        "quality_passed_for_complete_synthetic_row": replay["quality_passed_for_complete_synthetic_row"],
        "quality_passed_for_incomplete_synthetic_row": replay["quality_passed_for_incomplete_synthetic_row"],
        "field_standardization_refs": [
            "KMFA/tools/field_standardization.py",
            "KMFA/tests/test_field_standardization.py",
            ALIAS_DICTIONARY_PATH.as_posix(),
            FIELD_POLICY_PATH.as_posix(),
            FIELD_QUALITY_PROTOCOL_PATH.as_posix(),
            "KMFA/stage_artifacts/S04_P2_field_standardization/human/s04_p2_completion_record.md",
            "KMFA/stage_artifacts/S04_P2_field_standardization/human/test_results.md",
        ],
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_INBOX,
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_hash_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "raw_dir_read_performed": False,
        "raw_dir_list_performed": False,
        "raw_dir_hash_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_file_bytes_committed": False,
        "raw_filename_publication_allowed": False,
        "raw_file_hash_publication_allowed": False,
        "field_plaintext_publication_allowed": False,
        "sheet_name_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "row_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "business_field_parsing_performed": False,
        "raw_value_matching_performed": False,
        "raw_field_mapping_performed": False,
        "field_standardization_performed": True,
        "field_alias_mapping_performed": True,
        "s04_p3_started": False,
        "stage4_review_performed": False,
        "github_upload_performed": False,
        "github_main_upload_allowed": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q2",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "current_go_no_go": "NO_GO",
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "raw_business_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s04_p2_field_standardization.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p2_field_standardization.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p2_field_standardization -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_field_standardization -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p1_amount_precision.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tools/v014_s04_p2_field_standardization.py",
            "KMFA/tools/check_v014_s04_p2_field_standardization.py",
            "KMFA/tests/test_v014_s04_p2_field_standardization.py",
            "KMFA/tools/field_standardization.py",
            "KMFA/tests/test_field_standardization.py",
            "KMFA/tools/check_v014_s04_p1_amount_precision.py",
        ],
        "non_scope": [
            "S04-P3 basic tool report",
            "Stage 4 review",
            "GitHub upload",
            "raw root read list hash mutation",
            "raw value matching",
            "raw source field or header plaintext publication",
            "lineage full check",
            "formal report",
            "live connector",
            "business execution",
        ],
        "next_required_step": (
            "Proceed to v0.1.4 S04-P3 basic tool report as a separate run; do not perform "
            "Stage 4 review, GitHub upload, raw value matching, raw source field/header plaintext publication, "
            "lineage full check, formal report release, live connector, OpMe deep coupling, or business execution in S04-P2."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S04-P2 Field Standardization",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        f"- s04_p1_dependency_validated: `{str(manifest['s04_p1_dependency_validated']).lower()}`",
        f"- field_standardization_dependency_validated: `{str(manifest['field_standardization_dependency_validated']).lower()}`",
        f"- canonical_field_count: `{manifest['canonical_field_count']}`",
        f"- alias_dictionary_row_count: `{manifest['alias_dictionary_row_count']}`",
        f"- mapping_record_count: `{manifest['mapping_record_count']}`",
        f"- standardization_case_passed_count: `{manifest['standardization_case_passed_count']}/{manifest['standardization_case_count']}`",
        f"- quality_status_count: `{manifest['quality_status_count']}`",
        "",
        "## Field Standardization Boundaries",
        "",
        "- supported: canonical date, period, entity, project, counterparty and contract fields",
        "- alias_mapping: hash-only source alias key plus canonical field id",
        "- missing_or_invalid_fields: quality status, no silent skip",
        "- quality_status_issue_types: `invalid_field_value`, `missing_required_field`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- codex_read_list_hash_performed_by_this_phase: `false`",
        "- codex_modify_delete_move_rename_overwrite_or_generate_inside_allowed: `false`",
        "- public_repo_raw_commit_allowed: `false`",
        "- private_runtime_output_dir: `KMFA/.codex_private_runtime/`",
        "",
        "## Public-Safe Boundary",
        "",
        "- raw_file_bytes_committed: `false`",
        "- raw_filename_publication_allowed: `false`",
        "- raw_file_hash_publication_allowed: `false`",
        "- field_plaintext_publication_allowed: `false`",
        "- sheet_name_publication_allowed: `false`",
        "- zip_member_name_publication_allowed: `false`",
        "- row_value_publication_allowed: `false`",
        "- business_value_publication_allowed: `false`",
        "",
        "## Non-Scope",
        "",
        "- raw_field_mapping_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- s04_p3_started: `false`",
        "- stage4_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Gate Status",
        "",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        f"- current_go_no_go: `{manifest['current_go_no_go']}`",
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results() -> None:
    if TEST_RESULTS_PATH.exists():
        return
    lines = [
        "# KMFA v0.1.4 S04-P2 Test Results",
        "",
        "- status: `pending_final_validation`",
        "- red_step: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p2_field_standardization -q` failed before validator implementation with missing module.",
        "- note: `Generator created placeholder; final validation evidence will overwrite this file before commit.`",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_risk_and_rollback() -> None:
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S04-P2 Risk Register",
                "",
                "| risk_id | risk | control | status |",
                "|---|---|---|---|",
                "| `RISK-V014-S04P2-001` | Field standardization evidence uses synthetic values only and does not prove raw business header mapping. | Keep S04-P2 scoped to public-safe tool capability; raw value matching and authorized mapping remain later blocked work. | `controlled` |",
                "| `RISK-V014-S04P2-002` | Missing or invalid fields could be silently skipped. | Validator requires five quality-status records for incomplete synthetic replay and `field_skipped_silently=false`. | `controlled` |",
                "| `RISK-V014-S04P2-003` | Source aliases could leak raw headers. | Mapping evidence stores alias hash/key only and the public boundary forbids raw source field/header plaintext publication. | `controlled` |",
                "| `RISK-V014-S04P2-004` | S04-P2 could be mistaken for Stage 4 review or upload readiness. | Manifest locks S04-P3/Stage 4 review/GitHub upload as false and points next step to S04-P3 only. | `controlled` |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S04-P2 Rollback Plan",
                "",
                "- revert_files: `KMFA/tools/v014_s04_p2_field_standardization.py`, `KMFA/tools/check_v014_s04_p2_field_standardization.py`, `KMFA/tests/test_v014_s04_p2_field_standardization.py`, `KMFA/stage_artifacts/V014_S04_P2_FIELD_STANDARDIZATION/`, and S04-P2 governance rows.",
                "- raw_data_action: `none`; `/Users/linzezhang/Downloads/KMFA_MetaData` was not read, listed, hashed, modified, deleted, moved, renamed, overwritten, or written by this phase.",
                "- verification_after_rollback: rerun `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p1_amount_precision.py` and governance validators.",
                "- stop_condition: any raw/private payload, business value, credential, raw source header plaintext, or GitHub upload side effect requires immediate rollback and report.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_risk_and_rollback()
    write_pending_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.4 S04-P2 field standardization evidence generated "
        f"(canonical_fields={manifest['canonical_field_count']}, "
        f"aliases={manifest['alias_dictionary_row_count']}, "
        f"cases={manifest['standardization_case_passed_count']}/{manifest['standardization_case_count']}, "
        f"quality_statuses={manifest['quality_status_count']}, "
        f"raw_read={str(manifest['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
