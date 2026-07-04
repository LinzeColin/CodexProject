#!/usr/bin/env python3
"""Validate KMFA v0.1.4 S07-P2 public-safe WPS file adapter evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from KMFA.tools.v014_s07_p2_wps_file_adapter import (
    ACCEPTANCE_ID,
    ACTIVE_MAPPING_RULE_VERSION,
    CONVERSION_GUIDANCE_PATH,
    FIELD_REPORT_PATH,
    MANIFEST_PATH,
    METADATA_ADAPTER_MANIFEST_PATH,
    METADATA_MAPPINGS_PATH,
    METADATA_RULE_VERSIONS_PATH,
    METADATA_SOURCE_REGISTRY_PATH,
    NEXT_INSTRUCTION,
    NEXT_PHASE,
    PHASE_SCOPE,
    REPORT_PATH,
    REQUIRED_WPS_EXPORT_TYPES,
    RISK_REGISTER_PATH,
    ROLLBACK_PATH,
    S06_STAGE_REVIEW_MANIFEST_PATH,
    S07_P1_MANIFEST_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    TEST_RESULTS_PATH,
    load_public_safe_wps_baseline,
)


FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xlsx", ".xls", ".xlsm", ".pdf", ".sqlite", ".sqlite3", ".db")
RAW_INBOX_DIRECTORY_TOKEN = "KMFA" + "_MetaData"
PUBLIC_SAFE_WPS_CONVERSION_STATUS = "requires_conversion_to_public_safe_tabular_export"
LOCAL_DOWNLOADS_RAW_PATH_PATTERN = re.compile(r"/Users/[^\s\"'`]+/Downloads/[^\s\"'`]+")
STRICT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|secret|api_key|token)\s*=\s*[^\s,;]{8,}"),
)
FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "source_header_text",
    "field_key",
    "field_label",
    "file_hash",
    "sheet_name",
    "member_name",
    "member_path",
    "package_name",
    "business_value",
    "row_value",
    "cell_value",
    "plaintext_content",
    "full_file_text",
    "raw_file_bytes",
    "original_filename",
    "canonical_field_keys",
}
FORBIDDEN_TEXT = (
    "raw_value:",
    "normalized_value:",
    "source_header_text:",
    "field_key:",
    "field_label:",
    "file_hash:",
    "sheet_name:",
    "member_name:",
    "member_path:",
    "package_name:",
    "business_value:",
    "row_value:",
    "cell_value:",
    "S07P2_",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "10000",
    "9999",
    "-----" "BEGIN",
    "s" "k-",
)
PUBLIC_SAFETY_FALSE_KEYS = (
    "source_payload_values_committed",
    "source_header_plaintext_committed",
    "field_plaintext_committed",
    "source_file_committed",
    "private_csv_committed",
    "wps_native_file_committed",
    "xlsx_committed",
    "pdf_committed",
    "zip_committed",
    "credentials_committed",
)
STAGE_SCOPE_FALSE_KEYS = (
    "finance_scope_included",
    "redcircle_scope_included",
    "stage7_review_included",
    "external_connector_included",
    "facts_layer_write_included",
    "lineage_full_check_included",
    "formal_report_generation_included",
    "github_upload_included",
)
MANIFEST_FALSE_KEYS = (
    "raw_inbox_read_performed",
    "raw_inbox_mutation_performed",
    "raw_layer_write_allowed",
    "raw_source_mutation_allowed",
    "raw_content_matching_performed",
    "business_field_value_parsing_performed",
    "source_header_plaintext_committed",
    "field_plaintext_committed",
    "s07_p1_performed",
    "s07_p3_performed",
    "stage7_review_performed",
    "github_upload_performed",
    "delivery_allowed",
    "formal_report_allowed",
    "business_decision_basis_allowed",
    "business_execution_allowed",
)
RAW_BOUNDARY_FALSE_KEYS = (
    "codex_read_required_by_this_phase",
    "codex_read_performed_by_this_phase",
    "codex_list_performed_by_this_phase",
    "codex_stat_performed_by_this_phase",
    "codex_hash_performed_by_this_phase",
    "codex_modify_allowed",
    "codex_delete_allowed",
    "codex_move_allowed",
    "codex_rename_allowed",
    "codex_overwrite_allowed",
    "codex_generate_inside_allowed",
    "github_commit_allowed",
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
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValidationError(f"{path} must contain at least one row")
    if not all(isinstance(row, dict) for row in rows):
        raise ValidationError(f"{path} must contain JSON objects")
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


def walk_forbidden_keys(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                errors.append(f"forbidden public key {key!r} at {path}")
            walk_forbidden_keys(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_forbidden_keys(child, errors, f"{path}[{index}]")


def check_public_safe_file(path: Path, errors: list[str]) -> None:
    require(path.exists(), f"missing public-safe file: {path}", errors)
    if not path.exists():
        return
    require(path.suffix.lower() not in FORBIDDEN_PUBLIC_SUFFIXES, f"forbidden public extension: {path}", errors)
    if path.suffix.lower() not in {".md", ".json", ".jsonl", ".csv", ".yaml", ".yml"}:
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for forbidden in FORBIDDEN_TEXT:
        require(forbidden.lower() not in lower, f"forbidden public text {forbidden!r} in {path}", errors)
    require(RAW_INBOX_DIRECTORY_TOKEN.lower() not in lower, f"forbidden raw inbox directory token in {path}", errors)
    require(LOCAL_DOWNLOADS_RAW_PATH_PATTERN.search(text) is None, f"forbidden local Downloads raw path in {path}", errors)
    for pattern in STRICT_SECRET_PATTERNS:
        require(pattern.search(text) is None, f"high-signal secret pattern in {path}: {pattern.pattern}", errors)


def validate_legacy_wps_adapter_baseline() -> dict[str, Any]:
    baseline_manifest, mappings, conversion_guidance, field_report, rule_versions = load_public_safe_wps_baseline()
    hash_only_mappings = [
        mapping
        for mapping in mappings
        if str(mapping.get("source_binding", {}).get("source_header_hash", "")).startswith("sha256:")
        and mapping.get("source_binding", {}).get("source_header_private_ref")
    ]
    return {
        "source_export_type_count": baseline_manifest["summary"]["source_export_type_count"],
        "source_registry_count": baseline_manifest["summary"]["source_registry_count"],
        "field_mapping_count": baseline_manifest["summary"]["field_mapping_count"],
        "hash_only_field_mapping_count": len(hash_only_mappings),
        "field_report_count": baseline_manifest["summary"]["field_report_count"],
        "conversion_guidance_count": baseline_manifest["summary"]["conversion_guidance_count"],
        "mapping_rule_version_count": baseline_manifest["summary"]["mapping_rule_version_count"],
        "source_header_fingerprint_count": baseline_manifest["summary"]["source_header_hash_count"],
        "native_conversion_required_count": len(conversion_guidance),
        "active_mapping_rule_version": rule_versions["active_mapping_rule_version"],
        "readonly_parse_count": sum(1 for row in field_report if row.get("read_only_parse") is True),
        "raw_layer_write_allowed_count": sum(
            1 for row in field_report if row.get("raw_layer_write_allowed") is True
        ),
    }


def validate_v014_s07_p2_wps_file_adapter(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    manifest = read_json(manifest_path)
    adapter_manifest = read_json(METADATA_ADAPTER_MANIFEST_PATH)
    source_registry = read_json(METADATA_SOURCE_REGISTRY_PATH)
    mappings = read_jsonl(METADATA_MAPPINGS_PATH)
    rule_versions = read_json(METADATA_RULE_VERSIONS_PATH)
    conversion_guidance = read_jsonl(CONVERSION_GUIDANCE_PATH)
    readonly_reports = read_jsonl(FIELD_REPORT_PATH)
    stage6 = read_json(S06_STAGE_REVIEW_MANIFEST_PATH)
    s07_p1 = read_json(S07_P1_MANIFEST_PATH)
    legacy = validate_legacy_wps_adapter_baseline()

    for value in (
        manifest,
        adapter_manifest,
        source_registry,
        mappings,
        rule_versions,
        conversion_guidance,
        readonly_reports,
    ):
        walk_forbidden_keys(value, errors)

    require(manifest.get("schema_version") == SCHEMA_VERSION, "schema mismatch", errors)
    require(manifest.get("project_id") == "KMFA", "project_id mismatch", errors)
    require(manifest.get("version") == "0.1.4", "version mismatch", errors)
    require(manifest.get("stage_id") == "S07", "stage_id must be S07", errors)
    require(manifest.get("phase_id") == "S07-P2", "phase_id must be S07-P2", errors)
    require(manifest.get("phase_scope") == PHASE_SCOPE, "phase scope mismatch", errors)
    require(manifest.get("task_id") == TASK_ID, "task id mismatch", errors)
    require(manifest.get("acceptance_id") == ACCEPTANCE_ID, "acceptance id mismatch", errors)
    require(
        manifest.get("status") == "completed_validated_local_only_no_go_upload_deferred_wps_file_adapter",
        "status mismatch",
        errors,
    )
    require(manifest.get("completed_task_ids") == ["S7PBT01", "S7PBT02", "S7PBT03"], "task id list mismatch", errors)
    require(manifest.get("next_recommended_phase") == NEXT_PHASE, "next phase mismatch", errors)
    require(manifest.get("next_phase_instruction") == NEXT_INSTRUCTION, "next instruction mismatch", errors)

    require(stage6.get("stage_id") == "S06", "Stage 6 dependency mismatch", errors)
    require(stage6.get("github_upload_performed") is False, "Stage 6 dependency upload flag mismatch", errors)
    require(stage6.get("s07_p1_started") is False, "Stage 6 dependency must not start S07-P1", errors)
    require(s07_p1.get("phase_id") == "S07-P1", "S07-P1 dependency mismatch", errors)
    require(s07_p1.get("s07_p2_performed") is False, "S07-P1 dependency must not include S07-P2", errors)
    require(s07_p1.get("github_upload_performed") is False, "S07-P1 dependency upload flag mismatch", errors)
    require(manifest.get("s06_stage_review_dependency_validated") is True, "S06 dependency flag mismatch", errors)
    require(manifest.get("s07_p1_dependency_validated") is True, "S07-P1 dependency flag mismatch", errors)
    require(manifest.get("legacy_wps_adapter_validated") is True, "legacy WPS adapter flag mismatch", errors)

    summary = manifest.get("wps_adapter_summary", {})
    expected = {
        "source_export_type_count": 4,
        "source_registry_count": 4,
        "field_mapping_count": 20,
        "hash_only_field_mapping_count": 20,
        "field_report_count": 4,
        "conversion_guidance_count": 4,
        "mapping_rule_version_count": 1,
        "source_header_fingerprint_count": 20,
        "native_conversion_required_count": 4,
        "q4_human_confirmed_count": 0,
        "q5_calculation_baseline_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "readonly_parse_count": 4,
        "raw_layer_write_allowed_count": 0,
        "quality_counts": {"Q2_structure_candidate": 20},
        "active_mapping_rule_version": ACTIVE_MAPPING_RULE_VERSION,
    }
    require(set(summary.get("wps_export_types", [])) == set(REQUIRED_WPS_EXPORT_TYPES), "WPS export type set mismatch", errors)
    for key, value in expected.items():
        require(summary.get(key) == value, f"summary.{key} mismatch", errors)
    for key, value in legacy.items():
        require(summary.get(key) == value, f"legacy baseline {key} mismatch", errors)

    require(adapter_manifest.get("schema_version") == "kmfa.v014_wps_file_adapter_metadata.v1", "adapter schema mismatch", errors)
    require(set(adapter_manifest.get("wps_export_types", [])) == set(REQUIRED_WPS_EXPORT_TYPES), "adapter export set mismatch", errors)
    require(len(source_registry.get("sources", [])) == 4, "source registry count mismatch", errors)
    require(len(mappings) == 20, "field mapping row count mismatch", errors)
    require(len(conversion_guidance) == 4, "conversion guidance row count mismatch", errors)
    require(len(readonly_reports) == 4, "readonly report row count mismatch", errors)
    require(len(rule_versions.get("versions", [])) == 1, "mapping rule version count mismatch", errors)

    for source in source_registry.get("sources", []):
        require(source.get("record_type") == "v014_wps_export_source", "source record type mismatch", errors)
        require(source.get("export_type") in REQUIRED_WPS_EXPORT_TYPES, "source export type mismatch", errors)
        require(str(source.get("converted_structure_fingerprint", "")).startswith("sha256:"), "source fingerprint mismatch", errors)
        require(source.get("native_wps_conversion_required") is True, "source conversion required must be true", errors)
        require(source.get("read_only_parse") is True, "source read_only_parse must be true", errors)
        require(source.get("raw_layer_write_allowed") is False, "source raw layer write must be false", errors)
        require(source.get("source_file_committed") is False, "source file committed must be false", errors)

    seen_mappings: set[str] = set()
    for mapping in mappings:
        require(mapping.get("record_type") == "v014_wps_field_mapping", "mapping record type mismatch", errors)
        mapping_id = str(mapping.get("mapping_id", ""))
        require(mapping_id.startswith("V014-WPS-FLD-"), "mapping id prefix mismatch", errors)
        require(mapping_id not in seen_mappings, f"duplicate mapping id {mapping_id}", errors)
        seen_mappings.add(mapping_id)
        require(str(mapping.get("canonical_field_ref", "")).startswith("field:"), "canonical field ref mismatch", errors)
        require(mapping.get("mapping_rule_version_id") == ACTIVE_MAPPING_RULE_VERSION, "mapping rule version mismatch", errors)
        binding = mapping.get("source_binding", {})
        require(str(binding.get("source_header_fingerprint", "")).startswith("sha256:"), "source header fingerprint mismatch", errors)
        require(binding.get("source_header_private_ref"), "source header private ref required", errors)
        require(str(binding.get("converted_structure_fingerprint", "")).startswith("sha256:"), "converted fingerprint mismatch", errors)
        quality = mapping.get("quality_state", {})
        require(quality.get("q4_human_confirmed") is False, "mapping Q4 must be false", errors)
        require(quality.get("q5_calculation_baseline_allowed") is False, "mapping Q5 must be false", errors)
        require(quality.get("formal_report_allowed") is False, "mapping formal report must be false", errors)
        safety = mapping.get("public_repo_safety", {})
        for key in (
            "source_payload_values_committed",
            "source_header_plaintext_committed",
            "field_plaintext_committed",
            "source_file_committed",
            "wps_native_file_committed",
        ):
            require(safety.get(key) is False, f"mapping public safety {key} must be false", errors)

    for guidance in conversion_guidance:
        require(guidance.get("record_type") == "v014_wps_conversion_guidance", "guidance type mismatch", errors)
        require(guidance.get("native_wps_parse_status") == PUBLIC_SAFE_WPS_CONVERSION_STATUS, "guidance status mismatch", errors)
        require(guidance.get("read_only_after_conversion") is True, "guidance readonly flag mismatch", errors)
        require(guidance.get("raw_layer_write_allowed") is False, "guidance raw layer write mismatch", errors)

    for report in readonly_reports:
        require(report.get("record_type") == "v014_wps_file_readonly_field_report", "field report type mismatch", errors)
        require(report.get("read_only_parse") is True, "field report readonly flag mismatch", errors)
        require(report.get("raw_layer_write_allowed") is False, "field report raw layer write mismatch", errors)
        require(report.get("source_header_plaintext_committed") is False, "field report header plaintext flag mismatch", errors)
        require(report.get("field_mapping_count") == 5, "field report mapping count mismatch", errors)
        require(report.get("canonical_field_ref_count") == 5, "field report canonical ref count mismatch", errors)

    stage_scope = manifest.get("stage_scope", {})
    require(stage_scope.get("wps_file_adapter") is True, "WPS scope must be true", errors)
    for key in STAGE_SCOPE_FALSE_KEYS:
        require(stage_scope.get(key) is False, f"stage_scope.{key} must be false", errors)

    quality_gate = manifest.get("quality_gate", {})
    require(quality_gate.get("candidate_quality_grade") == "Q2_structure_candidate", "quality grade mismatch", errors)
    require(quality_gate.get("current_data_quality_grade") == "Q4", "current data quality mismatch", errors)
    require(quality_gate.get("current_report_grade") == "D", "current report grade mismatch", errors)
    require(quality_gate.get("release_permission") == "blocked", "release permission mismatch", errors)
    require(quality_gate.get("q4_human_confirmed_count") == 0, "Q4 count mismatch", errors)
    require(quality_gate.get("q5_calculation_baseline_allowed_count") == 0, "Q5 count mismatch", errors)
    require(quality_gate.get("formal_report_allowed_count") == 0, "formal report count mismatch", errors)

    raw = manifest.get("raw_data_boundary", {})
    require(raw.get("raw_inbox_ref") == "operator-designated local raw/private inbox outside repository", "raw inbox ref mismatch", errors)
    for key in RAW_BOUNDARY_FALSE_KEYS:
        require(raw.get(key) is False, f"raw_data_boundary.{key} must be false", errors)
    for key in MANIFEST_FALSE_KEYS:
        require(manifest.get(key) is False, f"{key} must be false", errors)
    require(manifest.get("s07_p2_performed") is True, "s07_p2_performed must be true", errors)
    require(manifest.get("github_upload_status") == "not_uploaded_deferred_until_v014_stage1_18_complete", "upload status mismatch", errors)
    require(manifest.get("current_data_quality_grade") == "Q4", "manifest data quality mismatch", errors)
    require(manifest.get("current_report_grade") == "D", "manifest report grade mismatch", errors)
    require(manifest.get("release_permission") == "blocked", "manifest release mismatch", errors)

    safety = manifest.get("public_repo_safety", {})
    for key in PUBLIC_SAFETY_FALSE_KEYS:
        require(safety.get(key) is False, f"public_repo_safety.{key} must be false", errors)

    for ref in manifest.get("evidence_refs", []):
        require(Path(ref).exists(), f"missing evidence ref: {ref}", errors)
    for ref in manifest.get("metadata_outputs", {}).values():
        require(Path(ref).exists(), f"missing metadata output ref: {ref}", errors)
    for path in (
        MANIFEST_PATH,
        CONVERSION_GUIDANCE_PATH,
        FIELD_REPORT_PATH,
        REPORT_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_ADAPTER_MANIFEST_PATH,
        METADATA_MAPPINGS_PATH,
        METADATA_RULE_VERSIONS_PATH,
        METADATA_SOURCE_REGISTRY_PATH,
    ):
        check_public_safe_file(path, errors)

    reviewed_head = str(manifest.get("reviewed_head", ""))
    require(len(reviewed_head) == 40 and all(char in "0123456789abcdef" for char in reviewed_head), "reviewed_head mismatch", errors)
    require("codex/kmfa" in git_output(["status", "--short", "--branch"]), "branch must be codex/kmfa", errors)

    if errors:
        raise ValidationError("\n".join(errors))
    return {
        "project_id": manifest["project_id"],
        "version": manifest["version"],
        "stage_id": manifest["stage_id"],
        "phase_id": manifest["phase_id"],
        "phase_scope": manifest["phase_scope"],
        "status": manifest["status"],
        "s06_stage_review_dependency_validated": manifest["s06_stage_review_dependency_validated"],
        "s07_p1_dependency_validated": manifest["s07_p1_dependency_validated"],
        "legacy_wps_adapter_validated": manifest["legacy_wps_adapter_validated"],
        "source_export_type_count": summary["source_export_type_count"],
        "source_registry_count": summary["source_registry_count"],
        "field_mapping_count": summary["field_mapping_count"],
        "hash_only_field_mapping_count": summary["hash_only_field_mapping_count"],
        "field_report_count": summary["field_report_count"],
        "conversion_guidance_count": summary["conversion_guidance_count"],
        "mapping_rule_version_count": summary["mapping_rule_version_count"],
        "source_header_fingerprint_count": summary["source_header_fingerprint_count"],
        "native_conversion_required_count": summary["native_conversion_required_count"],
        "q4_human_confirmed_count": summary["q4_human_confirmed_count"],
        "q5_calculation_baseline_allowed_count": summary["q5_calculation_baseline_allowed_count"],
        "formal_report_allowed_count": summary["formal_report_allowed_count"],
        "s07_p1_performed": manifest["s07_p1_performed"],
        "s07_p2_performed": manifest["s07_p2_performed"],
        "s07_p3_performed": manifest["s07_p3_performed"],
        "stage7_review_performed": manifest["stage7_review_performed"],
        "github_upload_performed": manifest["github_upload_performed"],
        "raw_inbox_read_performed": manifest["raw_inbox_read_performed"],
        "raw_inbox_mutation_performed": manifest["raw_inbox_mutation_performed"],
        "business_field_value_parsing_performed": manifest["business_field_value_parsing_performed"],
        "source_header_plaintext_committed": manifest["source_header_plaintext_committed"],
        "field_plaintext_committed": manifest["field_plaintext_committed"],
        "delivery_allowed": manifest["delivery_allowed"],
        "formal_report_allowed": manifest["formal_report_allowed"],
        "current_data_quality_grade": manifest["current_data_quality_grade"],
        "current_report_grade": manifest["current_report_grade"],
        "release_permission": manifest["release_permission"],
        "next_recommended_phase": manifest["next_recommended_phase"],
        "next_phase_instruction": manifest["next_phase_instruction"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.4 S07-P2 WPS file adapter evidence.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args(argv)
    try:
        result = validate_v014_s07_p2_wps_file_adapter(args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.4 S07-P2 WPS file adapter validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.4 S07-P2 WPS file adapter validated "
        f"(exports={result['source_export_type_count']}, "
        f"field_mappings={result['field_mapping_count']}, "
        f"conversion_guidance={result['conversion_guidance_count']}, "
        f"q5_allowed={result['q5_calculation_baseline_allowed_count']}, "
        "stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
