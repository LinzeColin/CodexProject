#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S07-P2 public-safe WPS file adapter evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s06_stage_review import validate_v014_s06_stage_review
from KMFA.tools.check_v014_s07_p1_finance_file_adapter import validate_v014_s07_p1_finance_file_adapter
from KMFA.tools.wps_file_adapter import (
    ACTIVE_MAPPING_RULE_VERSION,
    REQUIRED_WPS_EXPORT_TYPES,
    build_default_wps_adapter,
    validate_wps_adapter,
)


TASK_ID = "KMFA-V014-S07-P2-WPS-FILE-ADAPTER-20260704"
ACCEPTANCE_ID = "ACC-V014-S07-P2-WPS-FILE-ADAPTER"
SCHEMA_VERSION = "kmfa.v014_s07_p2_wps_file_adapter.v1"
PHASE_SCOPE = "v014_s07_p2_wps_file_adapter_only"
EVIDENCE_TIME = "2026-07-04T10:30:00+10:00"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "wps_file_adapter_manifest.json"
CONVERSION_GUIDANCE_PATH = MACHINE_DIR / "wps_conversion_guidance.jsonl"
FIELD_REPORT_PATH = MACHINE_DIR / "wps_readonly_field_report.jsonl"
REPORT_PATH = HUMAN_DIR / "wps_file_adapter_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_ADAPTER_MANIFEST_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p2_wps_file_adapter_manifest.json")
METADATA_MAPPINGS_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p2_wps_field_mappings.jsonl")
METADATA_RULE_VERSIONS_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p2_wps_mapping_rule_versions.json")
METADATA_SOURCE_REGISTRY_PATH = Path("KMFA/metadata/imports/v014_s07_p2_wps_export_source_registry.json")

S06_STAGE_REVIEW_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S06_STAGE_REVIEW/machine/stage6_review_manifest.json")
S07_P1_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/machine/finance_file_adapter_manifest.json")

NEXT_PHASE = "S07-P3"
NEXT_INSTRUCTION = (
    "Run v0.1.4 S07-P3 Redcircle export postponement policy as a separate run only after S07-P2 is committed. "
    "Do not perform Stage 7 review or GitHub upload in S07-P2. GitHub main upload remains "
    "deferred until v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
)
RAW_INBOX_REF = "operator-designated local raw/private inbox outside repository"
PUBLIC_SAFE_WPS_CONVERSION_STATUS = "requires_conversion_to_public_safe_tabular_export"
PUBLIC_SAFE_CONVERTED_FORMAT_CLASSES = ["spreadsheet_table", "delimited_table"]


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


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def validate_stage6_dependency() -> dict[str, Any]:
    stage6 = validate_v014_s06_stage_review()
    if stage6.get("stage_id") != "S06":
        raise ValueError("Stage 6 dependency validator did not return S06")
    if stage6.get("github_upload_performed") is not False:
        raise ValueError("Stage 6 dependency must not upload to GitHub")
    if stage6.get("s07_p1_started") is not False:
        raise ValueError("Stage 6 dependency must not have started S07-P1")
    if stage6.get("release_state", {}).get("current_go_no_go") != "NO_GO":
        raise ValueError("Stage 6 dependency must keep NO_GO")
    return stage6


def validate_s07_p1_dependency() -> dict[str, Any]:
    s07_p1 = validate_v014_s07_p1_finance_file_adapter()
    if s07_p1.get("stage_id") != "S07" or s07_p1.get("phase_id") != "S07-P1":
        raise ValueError("S07-P1 dependency validator did not return S07-P1")
    if s07_p1.get("github_upload_performed") is not False:
        raise ValueError("S07-P1 dependency must not upload to GitHub")
    if s07_p1.get("s07_p2_performed") is not False:
        raise ValueError("S07-P1 dependency must not perform S07-P2")
    return s07_p1


def load_public_safe_wps_baseline() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    manifest, mappings, conversion_guidance, field_report, rule_versions = build_default_wps_adapter(
        generated_at=EVIDENCE_TIME
    )
    registry = {
        "record_type": "wps_export_source_registry",
        "sources": manifest["source_registry"],
        "public_repo_safety": manifest["public_repo_safety"],
    }
    validate_wps_adapter(
        manifest,
        mappings,
        conversion_guidance,
        field_report,
        rule_versions,
        registry=registry,
    )
    return manifest, mappings, conversion_guidance, field_report, rule_versions


def public_field_ref(mapping: dict[str, Any]) -> str:
    canonical = mapping["canonical_field"]
    return "field:" + sha256_text(
        f"{mapping['export_type']}:{canonical['field_key']}:{canonical['value_kind']}:{canonical['field_role']}"
    ).removeprefix("sha256:")


def build_v014_outputs(
    baseline_manifest: dict[str, Any],
    baseline_mappings: list[dict[str, Any]],
    baseline_conversion_guidance: list[dict[str, Any]],
    baseline_field_report: list[dict[str, Any]],
    baseline_rule_versions: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    registry_sources: list[dict[str, Any]] = []
    for source in baseline_manifest["source_registry"]:
        registry_sources.append(
            {
                "record_type": "v014_wps_export_source",
                "schema_version": "kmfa.v014_wps_export_source.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P2",
                "source_ref": source["source_ref"],
                "export_type": source["export_type"],
                "converted_file_format": source["converted_file_format"],
                "converted_structure_fingerprint": source["converted_file_hash"],
                "source_file_private_ref": source["source_file_private_ref"],
                "read_only_parse": True,
                "native_wps_conversion_required": True,
                "native_wps_parse_status": PUBLIC_SAFE_WPS_CONVERSION_STATUS,
                "parse_status": "public_safe_converted_structure_probe_only",
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "source_file_committed": False,
            }
        )

    mapping_rows: list[dict[str, Any]] = []
    for mapping in baseline_mappings:
        binding = mapping["source_binding"]
        canonical = mapping["canonical_field"]
        mapping_rows.append(
            {
                "record_type": "v014_wps_field_mapping",
                "schema_version": "kmfa.v014_wps_field_mapping.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P2",
                "mapping_id": mapping["mapping_id"].replace("WPS-FLD-", "V014-WPS-FLD-", 1),
                "mapping_rule_version_id": mapping["mapping_rule_version_id"],
                "export_type": mapping["export_type"],
                "source_ref": mapping["source_ref"],
                "canonical_field_ref": public_field_ref(mapping),
                "canonical_value_kind": canonical["value_kind"],
                "canonical_role": canonical["field_role"],
                "source_binding": {
                    "source_file_private_ref": binding["source_file_private_ref"],
                    "converted_file_format": binding["file_format"],
                    "converted_structure_fingerprint": binding["file_hash"],
                    "sheet_ref": binding["sheet_ref"],
                    "column_ref": binding["column_ref"],
                    "source_header_fingerprint": binding["source_header_hash"],
                    "source_header_private_ref": binding["source_header_private_ref"],
                    "source_anchor_status": "hash_only_from_public_safe_converted_structure_probe",
                },
                "quality_state": {
                    "machine_candidate_quality_grade": "Q2_structure_candidate",
                    "q4_human_confirmed": False,
                    "q5_calculation_baseline_allowed": False,
                    "formal_report_allowed": False,
                },
                "public_repo_safety": {
                    "source_payload_values_committed": False,
                    "source_header_plaintext_committed": False,
                    "field_plaintext_committed": False,
                    "source_file_committed": False,
                    "private_csv_committed": False,
                    "wps_native_file_committed": False,
                },
                "next_required_phase": "S07 stage review before downstream lineage or fact layer use",
            }
        )

    mappings_by_export: dict[str, list[dict[str, Any]]] = {}
    for row in mapping_rows:
        mappings_by_export.setdefault(str(row["export_type"]), []).append(row)

    conversion_guidance_rows: list[dict[str, Any]] = []
    for row in baseline_conversion_guidance:
        conversion_guidance_rows.append(
            {
                "record_type": "v014_wps_conversion_guidance",
                "schema_version": "kmfa.v014_wps_conversion_guidance.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P2",
                "source_ref": row["source_ref"],
                "export_type": row["export_type"],
                "native_wps_file_format": row["native_wps_file_format"],
                "native_wps_container_type": row["native_wps_container_type"],
                "native_wps_parse_status": PUBLIC_SAFE_WPS_CONVERSION_STATUS,
                "accepted_converted_formats": PUBLIC_SAFE_CONVERTED_FORMAT_CLASSES,
                "operator_guidance_ref": "guidance:wps-export-to-public-safe-tabular-format-before-mapping",
                "read_only_after_conversion": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_file_private_ref": row["source_file_private_ref"],
            }
        )

    readonly_reports: list[dict[str, Any]] = []
    for report in baseline_field_report:
        export_type = str(report["export_type"])
        source_mappings = mappings_by_export.get(export_type, [])
        readonly_reports.append(
            {
                "record_type": "v014_wps_file_readonly_field_report",
                "schema_version": "kmfa.v014_wps_file_field_report.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P2",
                "source_ref": report["source_ref"],
                "export_type": export_type,
                "converted_file_format": report["file_format"],
                "converted_structure_fingerprint": report["file_hash"],
                "parse_status": "public_safe_converted_structure_probe_only",
                "native_wps_parse_status": PUBLIC_SAFE_WPS_CONVERSION_STATUS,
                "read_only_parse": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "source_header_plaintext_committed": False,
                "sheet_count": report["sheet_count"],
                "source_header_fingerprint_count": report["source_header_hash_count"],
                "field_mapping_count": len(source_mappings),
                "canonical_field_ref_count": len({row["canonical_field_ref"] for row in source_mappings}),
                "mapping_rule_version_id": report["mapping_rule_version_id"],
                "stage_scope": {
                    "finance_scope_included": False,
                    "wps_scope_included": True,
                    "redcircle_scope_included": False,
                    "external_connector_included": False,
                },
            }
        )

    rule_versions = {
        "record_type": "v014_wps_mapping_rule_versions",
        "schema_version": "kmfa.v014_wps_mapping_rule_versions.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "active_mapping_rule_version": baseline_rule_versions["active_mapping_rule_version"],
        "versions": [
            {
                "mapping_rule_version_id": version["mapping_rule_version_id"],
                "version_status": version["version_status"],
                "created_at": EVIDENCE_TIME,
                "change_type": "v014_public_safe_wps_mapping_rule_lock",
                "covered_export_types": list(version["covered_export_types"]),
                "mapping_records_ref": METADATA_MAPPINGS_PATH.as_posix(),
                "public_repo_safety": {
                    "source_payload_values_committed": False,
                    "source_header_plaintext_committed": False,
                    "field_plaintext_committed": False,
                    "source_file_committed": False,
                    "private_csv_committed": False,
                    "wps_native_file_committed": False,
                },
            }
            for version in baseline_rule_versions["versions"]
        ],
    }

    adapter_manifest = {
        "record_type": "v014_wps_file_adapter_metadata_manifest",
        "schema_version": "kmfa.v014_wps_file_adapter_metadata.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "generated_at": EVIDENCE_TIME,
        "wps_export_types": list(REQUIRED_WPS_EXPORT_TYPES),
        "active_mapping_rule_version": ACTIVE_MAPPING_RULE_VERSION,
        "source_registry_ref": METADATA_SOURCE_REGISTRY_PATH.as_posix(),
        "field_mappings_ref": METADATA_MAPPINGS_PATH.as_posix(),
        "conversion_guidance_ref": CONVERSION_GUIDANCE_PATH.as_posix(),
        "field_report_ref": FIELD_REPORT_PATH.as_posix(),
        "mapping_rule_versions_ref": METADATA_RULE_VERSIONS_PATH.as_posix(),
        "summary": {
            "source_export_type_count": len({item["export_type"] for item in registry_sources}),
            "source_registry_count": len(registry_sources),
            "field_mapping_count": len(mapping_rows),
            "hash_only_field_mapping_count": sum(
                1
                for row in mapping_rows
                if str(row["source_binding"].get("source_header_fingerprint", "")).startswith("sha256:")
                and row["source_binding"].get("source_header_private_ref")
            ),
            "field_report_count": len(readonly_reports),
            "conversion_guidance_count": len(conversion_guidance_rows),
            "mapping_rule_version_count": len(rule_versions["versions"]),
            "source_header_fingerprint_count": sum(row["source_header_fingerprint_count"] for row in readonly_reports),
            "native_conversion_required_count": sum(
                1 for source in registry_sources if source["native_wps_conversion_required"] is True
            ),
            "active_mapping_rule_version": ACTIVE_MAPPING_RULE_VERSION,
        },
        "stage_scope": {
            "wps_file_adapter": True,
            "finance_scope_included": False,
            "redcircle_scope_included": False,
            "stage7_review_included": False,
            "external_connector_included": False,
            "facts_layer_write_included": False,
            "lineage_full_check_included": False,
            "formal_report_generation_included": False,
            "github_upload_included": False,
        },
        "quality_gate": {
            "candidate_quality_grade": "Q2_structure_candidate",
            "requires_stage7_review_before_downstream_use": True,
            "q4_human_confirmed_count": 0,
            "q5_calculation_baseline_allowed_count": 0,
            "formal_report_allowed_count": 0,
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "public_repo_safety": {
            "source_payload_values_committed": False,
            "source_header_plaintext_committed": False,
            "field_plaintext_committed": False,
            "source_file_committed": False,
            "private_csv_committed": False,
            "wps_native_file_committed": False,
            "xlsx_committed": False,
            "pdf_committed": False,
            "zip_committed": False,
            "credentials_committed": False,
        },
    }
    source_registry = {
        "record_type": "v014_wps_export_source_registry",
        "schema_version": "kmfa.v014_wps_export_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P2",
        "sources": registry_sources,
        "public_repo_safety": adapter_manifest["public_repo_safety"],
    }
    return adapter_manifest, mapping_rows, source_registry, rule_versions, conversion_guidance_rows, readonly_reports


def build_manifest(
    stage6: dict[str, Any],
    s07_p1: dict[str, Any],
    adapter_manifest: dict[str, Any],
    mapping_rows: list[dict[str, Any]],
    source_registry: dict[str, Any],
    rule_versions: dict[str, Any],
    conversion_guidance_rows: list[dict[str, Any]],
    readonly_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    quality_counts = Counter(row["quality_state"]["machine_candidate_quality_grade"] for row in mapping_rows)
    summary = adapter_manifest["summary"]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S07",
        "stage_name": "file-based source adapters and field mapping",
        "phase_id": "S07-P2",
        "phase_name": "WPS file adapter",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "evidence_time": EVIDENCE_TIME,
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_wps_file_adapter",
        "completed_task_ids": ["S7PBT01", "S7PBT02", "S7PBT03"],
        "s06_stage_review_dependency_validated": True,
        "s06_dependency_ref": S06_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s06_dependency_status": stage6["status"],
        "s06_dependency_phase_results": stage6["phase_results"],
        "s06_dependency_current_data_quality_grade": stage6["release_state"]["current_data_quality_grade"],
        "s06_dependency_current_report_grade": stage6["release_state"]["current_report_grade"],
        "s07_p1_dependency_validated": True,
        "s07_p1_dependency_ref": S07_P1_MANIFEST_PATH.as_posix(),
        "s07_p1_dependency_status": s07_p1["status"],
        "legacy_wps_adapter_validated": True,
        "wps_adapter_summary": {
            **summary,
            "wps_export_types": list(adapter_manifest["wps_export_types"]),
            "quality_counts": dict(sorted(quality_counts.items())),
            "q4_human_confirmed_count": sum(1 for row in mapping_rows if row["quality_state"]["q4_human_confirmed"]),
            "q5_calculation_baseline_allowed_count": sum(
                1 for row in mapping_rows if row["quality_state"]["q5_calculation_baseline_allowed"]
            ),
            "formal_report_allowed_count": sum(1 for row in mapping_rows if row["quality_state"]["formal_report_allowed"]),
            "readonly_parse_count": sum(1 for row in readonly_reports if row["read_only_parse"]),
            "raw_layer_write_allowed_count": sum(1 for row in readonly_reports if row["raw_layer_write_allowed"]),
            "source_registry_count": len(source_registry["sources"]),
            "mapping_rule_version_count": len(rule_versions["versions"]),
            "conversion_guidance_count": len(conversion_guidance_rows),
        },
        "metadata_outputs": {
            "adapter_manifest_ref": METADATA_ADAPTER_MANIFEST_PATH.as_posix(),
            "source_registry_ref": METADATA_SOURCE_REGISTRY_PATH.as_posix(),
            "field_mappings_ref": METADATA_MAPPINGS_PATH.as_posix(),
            "conversion_guidance_ref": CONVERSION_GUIDANCE_PATH.as_posix(),
            "readonly_field_report_ref": FIELD_REPORT_PATH.as_posix(),
            "mapping_rule_versions_ref": METADATA_RULE_VERSIONS_PATH.as_posix(),
        },
        "stage_scope": adapter_manifest["stage_scope"],
        "quality_gate": adapter_manifest["quality_gate"],
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_stat_performed_by_this_phase": False,
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
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_content_matching_performed": False,
        "business_field_value_parsing_performed": False,
        "source_header_plaintext_committed": False,
        "field_plaintext_committed": False,
        "s07_p1_performed": False,
        "s07_p2_performed": True,
        "s07_p3_performed": False,
        "stage7_review_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "public_repo_safety": adapter_manifest["public_repo_safety"],
        "validation_summary": {
            "generator": "PASS",
            "s06_stage_review_dependency": "PASS",
            "s07_p1_dependency": "PASS",
            "legacy_wps_adapter": "PASS",
            "s07_p2_validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "legacy_wps_adapter_validator": "PENDING_FINAL_VALIDATION",
            "legacy_wps_adapter_unit_test": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "ruby_yaml_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "public_s07_p2_semantic_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            CONVERSION_GUIDANCE_PATH.as_posix(),
            FIELD_REPORT_PATH.as_posix(),
            METADATA_ADAPTER_MANIFEST_PATH.as_posix(),
            METADATA_SOURCE_REGISTRY_PATH.as_posix(),
            METADATA_MAPPINGS_PATH.as_posix(),
            METADATA_RULE_VERSIONS_PATH.as_posix(),
            "KMFA/tools/v014_s07_p2_wps_file_adapter.py",
            "KMFA/tools/check_v014_s07_p2_wps_file_adapter.py",
            "KMFA/tests/test_v014_s07_p2_wps_file_adapter.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["wps_adapter_summary"]
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P2 WPS File Adapter",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred_wps_file_adapter`",
                "- scope: `S07-P2 only`",
                f"- s06_stage_review_dependency_validated: `{str(manifest['s06_stage_review_dependency_validated']).lower()}`",
                f"- s07_p1_dependency_validated: `{str(manifest['s07_p1_dependency_validated']).lower()}`",
                f"- source_export_type_count: `{summary['source_export_type_count']}`",
                f"- source_registry_count: `{summary['source_registry_count']}`",
                f"- field_mapping_count: `{summary['field_mapping_count']}`",
                f"- hash_only_field_mapping_count: `{summary['hash_only_field_mapping_count']}`",
                f"- readonly_field_report_count: `{summary['field_report_count']}`",
                f"- conversion_guidance_count: `{summary['conversion_guidance_count']}`",
                f"- mapping_rule_version_count: `{summary['mapping_rule_version_count']}`",
                f"- source_header_fingerprint_count: `{summary['source_header_fingerprint_count']}`",
                f"- native_conversion_required_count: `{summary['native_conversion_required_count']}`",
                f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
                f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
                f"- formal_report_allowed_count: `{summary['formal_report_allowed_count']}`",
                f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
                f"- current_report_grade: `{manifest['current_report_grade']}`",
                f"- release_permission: `{manifest['release_permission']}`",
                f"- github_upload_status: `{manifest['github_upload_status']}`",
                "",
                "## Boundary",
                "",
                "- This phase creates public-safe WPS adapter metadata from converted-structure probes and existing public adapter logic only.",
                "- It does not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the operator-designated raw/private inbox.",
                "- Public evidence keeps source refs, fingerprints, private refs, aggregate counts, mapping ids, rule version ids and quality gates only.",
                "- It records that native WPS exports require operator conversion to accepted spreadsheet/text exports before mapping.",
                "- It does not publish source headers, raw file names, raw file hashes, tab labels, source values, credentials, workbooks, documents, private tables, databases or raw business data.",
                "- S07-P3, Stage 7 review, GitHub upload, raw content matching, lineage full check, formal report, live connector, OpMe deep coupling and business execution remain out of scope.",
                "",
                "## Next",
                "",
                manifest["next_phase_instruction"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P2 WPS File Adapter Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- generator: `PASS`",
                "- s06_stage_review_dependency: `PASS`",
                "- s07_p1_dependency: `PASS`",
                "- legacy_wps_adapter: `PASS`",
                "- s07_p3_performed: `false`",
                "- stage7_review_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_performed: `false`",
                "- raw_inbox_mutation_performed: `false`",
                "",
                "Final command results are captured after validator, focused unit test, governance checks and safety scans pass in this run.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P2 Risk Register",
                "",
                "| Risk | Mitigation | Status |",
                "|---|---|---|",
                "| WPS adapter evidence could be mistaken for raw WPS import. | Manifest keeps raw inbox read false and publishes only refs/fingerprints/counts. | controlled |",
                "| Native WPS files could be treated as directly parsed. | Conversion guidance keeps native WPS parse status as conversion required. | controlled |",
                "| Adapter evidence could be mistaken for Stage 7 completion. | Manifest keeps S07-P3 and Stage 7 review false. | controlled |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P2 Rollback Plan",
                "",
                "1. Revert the local commit containing `V014_S07_P2_WPS_FILE_ADAPTER` artifacts and v014 WPS metadata rows.",
                "2. Restore the active next phase to `S07-P2` if the validator is invalidated.",
                "3. Do not modify, delete, move, rename, overwrite or write the raw inbox during rollback.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    stage6 = validate_stage6_dependency()
    s07_p1 = validate_s07_p1_dependency()
    baseline_manifest, baseline_mappings, baseline_conversion_guidance, baseline_field_report, baseline_rule_versions = (
        load_public_safe_wps_baseline()
    )
    adapter_manifest, mapping_rows, source_registry, rule_versions, conversion_guidance_rows, readonly_reports = (
        build_v014_outputs(
            baseline_manifest,
            baseline_mappings,
            baseline_conversion_guidance,
            baseline_field_report,
            baseline_rule_versions,
        )
    )
    manifest = build_manifest(
        stage6,
        s07_p1,
        adapter_manifest,
        mapping_rows,
        source_registry,
        rule_versions,
        conversion_guidance_rows,
        readonly_reports,
    )
    write_json(METADATA_ADAPTER_MANIFEST_PATH, adapter_manifest)
    write_json(METADATA_SOURCE_REGISTRY_PATH, source_registry)
    write_jsonl(METADATA_MAPPINGS_PATH, mapping_rows)
    write_json(METADATA_RULE_VERSIONS_PATH, rule_versions)
    write_jsonl(CONVERSION_GUIDANCE_PATH, conversion_guidance_rows)
    write_jsonl(FIELD_REPORT_PATH, readonly_reports)
    write_json(MANIFEST_PATH, manifest)
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["wps_adapter_summary"]
    print(
        "PASS: KMFA v0.1.4 S07-P2 WPS file adapter generated "
        f"(exports={summary['source_export_type_count']}, "
        f"field_mappings={summary['field_mapping_count']}, "
        f"conversion_guidance={summary['conversion_guidance_count']}, "
        f"q5_allowed={summary['q5_calculation_baseline_allowed_count']}, "
        "stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
