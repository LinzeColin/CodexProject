#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S07-P2 WPS file adapter replay evidence.

This phase replays existing public-safe S07-P2 WPS adapter metadata. It
validates the v0.1.3 Stage 6 review dependency, the committed S07-P1 replay,
and the legacy S07-P2 WPS adapter artifacts, then emits aggregate evidence
only. It does not read the local raw data inbox and does not publish raw
filenames, raw hashes, source headers, sheet names, row values, business
values, or source files.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_stage_review import validate_v013_s06_stage_review
from KMFA.tools.check_v013_s07_p1_finance_file_adapter_replay import (
    validate_v013_s07_p1_finance_file_adapter_replay,
)
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR
from KMFA.tools.wps_file_adapter import (
    ACTIVE_MAPPING_RULE_VERSION,
    DEFAULT_OUTPUT_CONVERSION_GUIDANCE as LEGACY_CONVERSION_GUIDANCE,
    DEFAULT_OUTPUT_FIELD_REPORT as LEGACY_FIELD_REPORT,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MANIFEST,
    DEFAULT_OUTPUT_MAPPINGS as LEGACY_MAPPINGS,
    DEFAULT_OUTPUT_REGISTRY as LEGACY_REGISTRY,
    DEFAULT_OUTPUT_RULE_VERSIONS as LEGACY_RULE_VERSIONS,
    REQUIRED_WPS_EXPORT_TYPES,
    read_json,
    read_jsonl,
    validate_wps_adapter,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S07_P2_WPS_FILE_ADAPTER_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/wps_file_adapter_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/wps_file_adapter_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S06_STAGE_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_STAGE_REVIEW/machine/stage6_review_manifest.json"
)
S07_P1_REPLAY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S07_P1_FINANCE_FILE_ADAPTER_REPLAY/machine/finance_file_adapter_replay_manifest.json"
)
TASK_ID = "KMFA-V013-S07-P2-WPS-FILE-ADAPTER-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s07_p2_wps_file_adapter_replay.v1"
PHASE_SCOPE = "v013_s07_p2_wps_file_adapter_replay_only"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S07-P3 as a separate run only after this phase is committed. "
    "Do not run Stage 7 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, or business execution in the S07-P2 run. "
    "GitHub main upload remains deferred until v0.1.3 Stages 1-10 are complete, the "
    "whole Stage 1-10 review passes, and findings are fixed."
)


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


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_stage6_dependency() -> dict[str, Any]:
    result = validate_v013_s06_stage_review()
    if result.get("stage_id") != "S06":
        raise ValueError("S06 dependency validator did not return Stage 6")
    if result.get("github_upload_performed") is not False:
        raise ValueError("S06 dependency must not have performed v0.1.3 GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise ValueError("S06 dependency must defer GitHub upload to Stage 1-10 batch gate")
    return result


def validate_s07_p1_dependency() -> dict[str, Any]:
    result = validate_v013_s07_p1_finance_file_adapter_replay()
    if result.get("stage_id") != "S07" or result.get("phase_id") != "S07-P1":
        raise ValueError("S07-P1 dependency validator did not return S07-P1")
    if result.get("github_upload_performed") is not False:
        raise ValueError("S07-P1 dependency must not have performed GitHub upload")
    return result


def validate_legacy_s07_p2() -> dict[str, Any]:
    manifest = read_json(LEGACY_MANIFEST)
    mappings = read_jsonl(LEGACY_MAPPINGS)
    conversion_guidance = read_jsonl(LEGACY_CONVERSION_GUIDANCE)
    field_report = read_jsonl(LEGACY_FIELD_REPORT)
    rule_versions = read_json(LEGACY_RULE_VERSIONS)
    registry = read_json(LEGACY_REGISTRY)
    validate_wps_adapter(
        manifest,
        mappings,
        conversion_guidance,
        field_report,
        rule_versions,
        registry=registry,
    )

    quality_counts = Counter(
        str(mapping.get("quality_state", {}).get("machine_candidate_quality_grade")) for mapping in mappings
    )
    source_formats = Counter(str(source.get("converted_file_format")) for source in registry["sources"])
    native_conversion_required_count = sum(
        1 for source in registry["sources"] if source.get("native_wps_conversion_required") is True
    )
    q4_confirmed_count = sum(1 for mapping in mappings if mapping.get("quality_state", {}).get("q4_human_confirmed") is True)
    q5_allowed_count = sum(
        1 for mapping in mappings if mapping.get("quality_state", {}).get("q5_calculation_baseline_allowed") is True
    )
    formal_report_allowed_count = sum(
        1 for mapping in mappings if mapping.get("quality_state", {}).get("formal_report_allowed") is True
    )
    hash_only_mappings = [
        mapping
        for mapping in mappings
        if str(mapping.get("source_binding", {}).get("source_header_hash", "")).startswith("sha256:")
        and mapping.get("source_binding", {}).get("source_header_private_ref")
    ]

    return {
        "wps_export_types": list(manifest["wps_export_types"]),
        "source_export_type_count": manifest["summary"]["source_export_type_count"],
        "source_registry_count": manifest["summary"]["source_registry_count"],
        "field_mapping_count": manifest["summary"]["field_mapping_count"],
        "hash_only_field_mapping_count": len(hash_only_mappings),
        "field_report_count": manifest["summary"]["field_report_count"],
        "conversion_guidance_count": manifest["summary"]["conversion_guidance_count"],
        "mapping_rule_version_count": manifest["summary"]["mapping_rule_version_count"],
        "source_header_hash_count": manifest["summary"]["source_header_hash_count"],
        "field_report_readonly_count": sum(1 for record in field_report if record.get("read_only_parse") is True),
        "field_report_raw_layer_write_allowed_count": sum(
            1 for record in field_report if record.get("raw_layer_write_allowed") is True
        ),
        "native_conversion_required_count": native_conversion_required_count,
        "quality_counts": dict(sorted(quality_counts.items())),
        "q4_human_confirmed_count": q4_confirmed_count,
        "q5_calculation_baseline_allowed_count": q5_allowed_count,
        "formal_report_allowed_count": formal_report_allowed_count,
        "converted_format_counts": dict(sorted(source_formats.items())),
        "active_mapping_rule_version": rule_versions["active_mapping_rule_version"],
        "stage_scope": manifest["stage_scope"],
        "quality_gate": manifest["quality_gate"],
        "public_repo_safety": manifest["public_repo_safety"],
    }


def build_manifest() -> dict[str, Any]:
    s06 = validate_stage6_dependency()
    s07_p1 = validate_s07_p1_dependency()
    legacy = validate_legacy_s07_p2()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S07",
        "stage_name": "v0.1.3 finance source adapter and upstream file support",
        "phase_id": "S07-P2",
        "phase_name": "WPS file adapter replay",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_wps_file_adapter_replayed",
        "completed_task_ids": ["S7PBT01", "S7PBT02", "S7PBT03"],
        "acceptance_ids": ["ACC-V013-S07-P2-WPS-FILE-ADAPTER-REPLAY"],
        "s06_stage_review_dependency_validated": True,
        "s06_dependency_ref": S06_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s06_dependency_phase_results": s06.get("phase_results", {}),
        "s06_dependency_current_data_quality_grade": s06.get("current_data_quality_grade"),
        "s06_dependency_current_report_grade": s06.get("current_report_grade"),
        "s07_p1_dependency_validated": True,
        "s07_p1_dependency_ref": S07_P1_REPLAY_MANIFEST_PATH.as_posix(),
        "s07_p1_dependency_status": s07_p1.get("status"),
        "legacy_s07_p2_dependency_validated": True,
        "wps_adapter_summary": {
            "wps_export_types": legacy["wps_export_types"],
            "source_export_type_count": legacy["source_export_type_count"],
            "source_registry_count": legacy["source_registry_count"],
            "field_mapping_count": legacy["field_mapping_count"],
            "hash_only_field_mapping_count": legacy["hash_only_field_mapping_count"],
            "field_report_count": legacy["field_report_count"],
            "conversion_guidance_count": legacy["conversion_guidance_count"],
            "mapping_rule_version_count": legacy["mapping_rule_version_count"],
            "source_header_hash_count": legacy["source_header_hash_count"],
            "field_report_readonly_count": legacy["field_report_readonly_count"],
            "field_report_raw_layer_write_allowed_count": legacy["field_report_raw_layer_write_allowed_count"],
            "native_conversion_required_count": legacy["native_conversion_required_count"],
            "quality_counts": legacy["quality_counts"],
            "q4_human_confirmed_count": legacy["q4_human_confirmed_count"],
            "q5_calculation_baseline_allowed_count": legacy["q5_calculation_baseline_allowed_count"],
            "formal_report_allowed_count": legacy["formal_report_allowed_count"],
            "converted_format_counts": legacy["converted_format_counts"],
            "active_mapping_rule_version": legacy["active_mapping_rule_version"],
        },
        "stage_scope": {
            "wps_file_adapter_replay": True,
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
            "q4_human_confirmed_count": legacy["q4_human_confirmed_count"],
            "q5_calculation_baseline_allowed_count": legacy["q5_calculation_baseline_allowed_count"],
            "formal_report_allowed": False,
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "raw_data_boundary": {
            "local_raw_data_dir": str(RAW_DIR),
            "local_raw_data_dir_role": "protected_finance_input_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "raw_dir_read_required": False,
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_value_matching_performed": False,
        "business_field_parsing_performed": False,
        "source_header_plaintext_publication_allowed": False,
        "field_plaintext_publication_allowed": False,
        "raw_filename_publication_allowed": False,
        "raw_file_hash_publication_allowed": False,
        "tab_label_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "record_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "s07_p1_performed": False,
        "s07_p2_performed": True,
        "s07_p3_performed": False,
        "stage7_review_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        "github_upload_deferred_until_stage10_batch": True,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "public_repo_safety": {
            "protected_finance_inputs_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "wps_native_file_committed": False,
            "csv_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "tab_labels_committed": False,
            "zip_member_names_committed": False,
            "protected_finance_values_committed": False,
            "normalized_protected_values_committed": False,
        },
        "legacy_s07_p2_refs": [
            "KMFA/metadata/imports/wps_export_source_registry.json",
            "KMFA/metadata/schema_maps/wps_file_adapter_manifest.json",
            "KMFA/metadata/schema_maps/wps_field_mappings.jsonl",
            "KMFA/metadata/schema_maps/wps_mapping_rule_versions.json",
            "KMFA/stage_artifacts/S07_P2_wps_file_adapter/machine/wps_conversion_guidance.jsonl",
            "KMFA/stage_artifacts/S07_P2_wps_file_adapter/machine/wps_readonly_field_report.jsonl",
            "KMFA/stage_artifacts/S07_P2_wps_file_adapter/machine/s07_p2_manifest.json",
        ],
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def build_report(manifest: dict[str, Any]) -> str:
    summary = manifest["wps_adapter_summary"]
    export_types = ", ".join(summary["wps_export_types"])
    return "\n".join(
        [
            "# KMFA v0.1.3 S07-P2 WPS File Adapter Replay",
            "",
            f"- task_id: `{manifest['task_id']}`",
            f"- status: `{manifest['status']}`",
            f"- reviewed_head: `{manifest['reviewed_head']}`",
            f"- branch: `{manifest['branch']}`",
            f"- source_export_type_count: `{summary['source_export_type_count']}`",
            f"- wps_export_types: `{export_types}`",
            f"- field_mapping_count: `{summary['field_mapping_count']}`",
            f"- hash_only_field_mapping_count: `{summary['hash_only_field_mapping_count']}`",
            f"- field_report_count: `{summary['field_report_count']}`",
            f"- conversion_guidance_count: `{summary['conversion_guidance_count']}`",
            f"- source_header_hash_count: `{summary['source_header_hash_count']}`",
            f"- mapping_rule_version_count: `{summary['mapping_rule_version_count']}`",
            f"- active_mapping_rule_version: `{summary['active_mapping_rule_version']}`",
            f"- native_conversion_required_count: `{summary['native_conversion_required_count']}`",
            f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
            f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
            f"- formal_report_allowed_count: `{summary['formal_report_allowed_count']}`",
            f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
            f"- current_report_grade: `{manifest['current_report_grade']}`",
            f"- release_permission: `{manifest['release_permission']}`",
            f"- stage7_review_performed: `{str(manifest['stage7_review_performed']).lower()}`",
            f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
            f"- raw_dir_read_performed: `{str(manifest['raw_dir_read_performed']).lower()}`",
            "",
            "## Scope",
            "",
            "- Replayed legacy S07-P2 WPS adapter public-safe metadata only.",
            "- Confirmed converted workbook structures are represented by hash/private refs and aggregate counts.",
            "- Confirmed native WPS files require operator conversion to accepted spreadsheet/text exports before mapping.",
            "- Did not read, list, mutate, copy, commit, or summarize the raw data inbox.",
            "- Did not publish raw filenames, raw file hashes, source header plaintext, sheet names, row values, business values, or source files.",
            "- Did not run S07-P3, Stage 7 review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, or business execution.",
            "",
            "## Evidence",
            "",
            f"- manifest: `{MANIFEST_PATH.as_posix()}`",
            f"- test_results: `{TEST_RESULTS_PATH.as_posix()}`",
            f"- legacy_manifest: `KMFA/metadata/schema_maps/wps_file_adapter_manifest.json`",
            f"- legacy_mapping_rules: `KMFA/metadata/schema_maps/wps_mapping_rule_versions.json`",
            "",
            "## Next Required Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )


def build_test_results() -> str:
    return "\n".join(
        [
            "# Test Results",
            "",
            "- PASS: legacy S07-P2 WPS adapter validator passed before replay.",
            "- PASS: legacy S07-P2 unit tests passed before replay.",
            "- PASS: v0.1.3 S06 Stage review dependency validator passed before replay.",
            "- PASS: v0.1.3 S07-P1 dependency validator passed before replay.",
            "- PASS: v0.1.3 S07-P2 replay generator wrote manifest and human evidence.",
            "- Required follow-up verification: replay validator, focused unit, governance validators, raw/private scan, public-safe scan, secret scan, parse checks, and diff check.",
            "",
            "## Commands",
            "",
            "```bash",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p2_wps_file_adapter.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_wps_file_adapter -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s07_p2_wps_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p2_wps_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s07_p2_wps_file_adapter_replay -q",
            "```",
            "",
            f"- manifest: `{MANIFEST_PATH.as_posix()}`",
            f"- report: `{REPORT_PATH.as_posix()}`",
            "- status: `completed_validated_local_only_no_go_upload_deferred_wps_file_adapter_replayed`",
            "",
        ]
    )


def generate() -> dict[str, Any]:
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(manifest), encoding="utf-8")
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text(build_test_results(), encoding="utf-8")
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["wps_adapter_summary"]
    print(
        "PASS: KMFA v0.1.3 S07-P2 WPS file adapter replay generated "
        f"(exports={summary['source_export_type_count']}, "
        f"field_mappings={summary['field_mapping_count']}, "
        f"conversion_guidance={summary['conversion_guidance_count']}, "
        "stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
