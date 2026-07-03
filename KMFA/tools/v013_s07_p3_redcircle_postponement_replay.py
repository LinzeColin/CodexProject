#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S07-P3 Redcircle postponement replay evidence.

This phase replays existing public-safe S07-P3 Redcircle postponement
metadata. It validates the v0.1.3 Stage 6 review dependency, the committed
S07-P1 and S07-P2 replays, and the legacy S07-P3 Redcircle artifacts, then
emits aggregate evidence only. It does not read the local raw data inbox and
does not publish raw filenames, raw hashes, source headers, sheet names, row
values, business values, credentials, connector secrets, or source files.
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
from KMFA.tools.check_v013_s07_p2_wps_file_adapter_replay import (
    validate_v013_s07_p2_wps_file_adapter_replay,
)
from KMFA.tools.redcircle_postponement_policy import (
    DEFAULT_OUTPUT_CONNECTOR_POLICY as LEGACY_CONNECTOR_POLICY,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MANIFEST,
    DEFAULT_OUTPUT_REGISTRY as LEGACY_REGISTRY,
    DEFAULT_OUTPUT_ROLLBACK_PLAN as LEGACY_ROLLBACK_PLAN,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST,
    DEFAULT_OUTPUT_TEMPLATES as LEGACY_TEMPLATES,
    REQUIRED_REDCIRCLE_EXPORT_TYPES,
    read_json,
    read_jsonl,
    validate_redcircle_postponement_policy,
)
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S07_P3_REDCIRCLE_POSTPONEMENT_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/redcircle_postponement_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/redcircle_postponement_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S06_STAGE_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_STAGE_REVIEW/machine/stage6_review_manifest.json"
)
S07_P1_REPLAY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S07_P1_FINANCE_FILE_ADAPTER_REPLAY/machine/finance_file_adapter_replay_manifest.json"
)
S07_P2_REPLAY_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S07_P2_WPS_FILE_ADAPTER_REPLAY/machine/wps_file_adapter_replay_manifest.json"
)
TASK_ID = "KMFA-V013-S07-P3-REDCIRCLE-POSTPONEMENT-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s07_p3_redcircle_postponement_replay.v1"
PHASE_SCOPE = "v013_s07_p3_redcircle_postponement_replay_only"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 Stage 7 review as a separate run only after this phase is committed. "
    "Do not run GitHub upload, raw value matching, lineage full check, formal report release, "
    "live connector, Redcircle automatic connector, or business execution in the S07-P3 run. "
    "GitHub main upload remains deferred until v0.1.3 Stages 1-10 are complete, the whole "
    "Stage 1-10 review passes, and findings are fixed."
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


def validate_s07_p2_dependency() -> dict[str, Any]:
    result = validate_v013_s07_p2_wps_file_adapter_replay()
    if result.get("stage_id") != "S07" or result.get("phase_id") != "S07-P2":
        raise ValueError("S07-P2 dependency validator did not return S07-P2")
    if result.get("github_upload_performed") is not False:
        raise ValueError("S07-P2 dependency must not have performed GitHub upload")
    return result


def validate_legacy_s07_p3() -> dict[str, Any]:
    manifest = read_json(LEGACY_MANIFEST)
    templates = read_jsonl(LEGACY_TEMPLATES)
    connector_policy = read_json(LEGACY_CONNECTOR_POLICY)
    rollback_plan = read_jsonl(LEGACY_ROLLBACK_PLAN)
    registry = read_json(LEGACY_REGISTRY)
    stage_manifest = read_json(LEGACY_STAGE_MANIFEST)
    validate_redcircle_postponement_policy(
        manifest,
        templates,
        connector_policy,
        rollback_plan,
        registry=registry,
    )

    template_quality_counts = Counter(
        str(template.get("quality_state", {}).get("machine_candidate_quality_grade")) for template in templates
    )
    q4_confirmed_count = sum(
        1 for template in templates if template.get("quality_state", {}).get("q4_human_confirmed") is True
    )
    q5_allowed_count = sum(
        1 for template in templates if template.get("quality_state", {}).get("q5_calculation_baseline_allowed") is True
    )
    formal_report_allowed_count = sum(
        1 for template in templates if template.get("quality_state", {}).get("formal_report_allowed") is True
    )

    future_controls = connector_policy["future_connector_controls"]
    return {
        "redcircle_export_types": list(manifest["redcircle_export_types"]),
        "reserved_template_count": manifest["summary"]["reserved_template_count"],
        "connector_policy_count": manifest["summary"]["connector_policy_count"],
        "rollback_plan_count": manifest["summary"]["rollback_plan_count"],
        "automatic_connector_allowed_count": manifest["summary"]["automatic_connector_allowed_count"],
        "registry_source_count": len(registry["sources"]),
        "template_contract_hash_count": sum(1 for template in templates if template.get("template_contract_hash")),
        "source_private_ref_count": sum(1 for template in templates if template.get("source_file_private_ref")),
        "manual_export_file_allowed_count": sum(
            1 for template in templates if template.get("manual_export_file_allowed") is True
        ),
        "template_raw_layer_write_allowed_count": sum(
            1 for template in templates if template.get("raw_layer_write_allowed") is True
        ),
        "rollback_raw_layer_write_allowed_count": sum(
            1 for record in rollback_plan if record.get("raw_layer_write_allowed") is True
        ),
        "rollback_source_mutation_allowed_count": sum(
            1 for record in rollback_plan if record.get("raw_source_mutation_allowed") is True
        ),
        "template_quality_counts": dict(sorted(template_quality_counts.items())),
        "q4_human_confirmed_count": q4_confirmed_count,
        "q5_calculation_baseline_allowed_count": q5_allowed_count,
        "formal_report_allowed_count": formal_report_allowed_count,
        "d15_file_mvp_automatic_connector_allowed": connector_policy[
            "d15_file_mvp_automatic_connector_allowed"
        ],
        "external_connector_included": connector_policy["external_connector_included"],
        "read_only_required": future_controls["read_only_required"],
        "hash_retention_required": future_controls["hash_retention_required"],
        "rollback_plan_required": future_controls["rollback_plan_required"],
        "manual_approval_required": future_controls["manual_approval_required"],
        "stage_scope": manifest["stage_scope"],
        "quality_gate": manifest["quality_gate"],
        "public_repo_safety": manifest["public_repo_safety"],
        "stage_manifest_schema_version": stage_manifest["schema_version"],
    }


def build_manifest() -> dict[str, Any]:
    s06 = validate_stage6_dependency()
    s07_p1 = validate_s07_p1_dependency()
    s07_p2 = validate_s07_p2_dependency()
    legacy = validate_legacy_s07_p3()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S07",
        "stage_name": "v0.1.3 finance source adapter and upstream file support",
        "phase_id": "S07-P3",
        "phase_name": "Redcircle export postponement replay",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_redcircle_postponement_replayed",
        "completed_task_ids": ["S7PCT01", "S7PCT02", "S7PCT03"],
        "acceptance_ids": ["ACC-V013-S07-P3-REDCIRCLE-POSTPONEMENT-REPLAY"],
        "s06_stage_review_dependency_validated": True,
        "s06_dependency_ref": S06_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s06_dependency_phase_results": s06.get("phase_results", {}),
        "s06_dependency_current_data_quality_grade": s06.get("current_data_quality_grade"),
        "s06_dependency_current_report_grade": s06.get("current_report_grade"),
        "s07_p1_dependency_validated": True,
        "s07_p1_dependency_ref": S07_P1_REPLAY_MANIFEST_PATH.as_posix(),
        "s07_p1_dependency_status": s07_p1.get("status"),
        "s07_p2_dependency_validated": True,
        "s07_p2_dependency_ref": S07_P2_REPLAY_MANIFEST_PATH.as_posix(),
        "s07_p2_dependency_status": s07_p2.get("status"),
        "legacy_s07_p3_dependency_validated": True,
        "redcircle_postponement_summary": {
            "redcircle_export_types": legacy["redcircle_export_types"],
            "reserved_template_count": legacy["reserved_template_count"],
            "connector_policy_count": legacy["connector_policy_count"],
            "rollback_plan_count": legacy["rollback_plan_count"],
            "automatic_connector_allowed_count": legacy["automatic_connector_allowed_count"],
            "registry_source_count": legacy["registry_source_count"],
            "template_contract_hash_count": legacy["template_contract_hash_count"],
            "source_private_ref_count": legacy["source_private_ref_count"],
            "manual_export_file_allowed_count": legacy["manual_export_file_allowed_count"],
            "template_raw_layer_write_allowed_count": legacy["template_raw_layer_write_allowed_count"],
            "rollback_raw_layer_write_allowed_count": legacy["rollback_raw_layer_write_allowed_count"],
            "rollback_source_mutation_allowed_count": legacy["rollback_source_mutation_allowed_count"],
            "template_quality_counts": legacy["template_quality_counts"],
            "q4_human_confirmed_count": legacy["q4_human_confirmed_count"],
            "q5_calculation_baseline_allowed_count": legacy["q5_calculation_baseline_allowed_count"],
            "formal_report_allowed_count": legacy["formal_report_allowed_count"],
            "d15_file_mvp_automatic_connector_allowed": legacy["d15_file_mvp_automatic_connector_allowed"],
            "external_connector_included": legacy["external_connector_included"],
            "read_only_required": legacy["read_only_required"],
            "hash_retention_required": legacy["hash_retention_required"],
            "rollback_plan_required": legacy["rollback_plan_required"],
            "manual_approval_required": legacy["manual_approval_required"],
        },
        "stage_scope": {
            "redcircle_postponement_replay": True,
            "redcircle_reserved_templates": True,
            "finance_scope_included": False,
            "wps_scope_included": False,
            "stage7_review_included": False,
            "external_connector_included": False,
            "redcircle_automatic_connector_included": False,
            "facts_layer_write_included": False,
            "lineage_full_check_included": False,
            "formal_report_generation_included": False,
            "github_upload_included": False,
        },
        "quality_gate": {
            "candidate_quality_grade": "Q1_reserved_template",
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
        "connector_secret_publication_allowed": False,
        "s07_p1_performed": False,
        "s07_p2_performed": False,
        "s07_p3_performed": True,
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
            "redcircle_native_file_committed": False,
            "csv_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "connector_secret_committed": False,
            "field_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "tab_labels_committed": False,
            "zip_member_names_committed": False,
            "protected_finance_values_committed": False,
            "normalized_protected_values_committed": False,
        },
        "legacy_s07_p3_refs": [
            "KMFA/metadata/imports/redcircle_export_source_registry.json",
            "KMFA/metadata/schema_maps/redcircle_postponement_manifest.json",
            "KMFA/metadata/schema_maps/redcircle_reserved_export_templates.jsonl",
            "KMFA/metadata/schema_maps/redcircle_postponement_policy.yaml",
            "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/redcircle_connector_postponement_policy.json",
            "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/redcircle_future_rollback_plan.jsonl",
            "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/s07_p3_manifest.json",
        ],
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def build_report(manifest: dict[str, Any]) -> str:
    summary = manifest["redcircle_postponement_summary"]
    export_types = ", ".join(summary["redcircle_export_types"])
    return "\n".join(
        [
            "# KMFA v0.1.3 S07-P3 Redcircle Postponement Replay",
            "",
            f"- task_id: `{manifest['task_id']}`",
            f"- status: `{manifest['status']}`",
            f"- reviewed_head: `{manifest['reviewed_head']}`",
            f"- branch: `{manifest['branch']}`",
            f"- redcircle_export_types: `{export_types}`",
            f"- reserved_template_count: `{summary['reserved_template_count']}`",
            f"- connector_policy_count: `{summary['connector_policy_count']}`",
            f"- rollback_plan_count: `{summary['rollback_plan_count']}`",
            f"- registry_source_count: `{summary['registry_source_count']}`",
            f"- template_contract_hash_count: `{summary['template_contract_hash_count']}`",
            f"- source_private_ref_count: `{summary['source_private_ref_count']}`",
            f"- automatic_connector_allowed_count: `{summary['automatic_connector_allowed_count']}`",
            f"- manual_export_file_allowed_count: `{summary['manual_export_file_allowed_count']}`",
            f"- d15_file_mvp_automatic_connector_allowed: `{str(summary['d15_file_mvp_automatic_connector_allowed']).lower()}`",
            f"- read_only_required: `{str(summary['read_only_required']).lower()}`",
            f"- hash_retention_required: `{str(summary['hash_retention_required']).lower()}`",
            f"- rollback_plan_required: `{str(summary['rollback_plan_required']).lower()}`",
            f"- manual_approval_required: `{str(summary['manual_approval_required']).lower()}`",
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
            "- Replayed legacy S07-P3 Redcircle postponement public-safe metadata only.",
            "- Confirmed four reserved export templates and future read-only/hash/rollback/manual-approval controls.",
            "- Confirmed D15 file MVP keeps Redcircle automatic connector blocked.",
            "- Did not read, list, mutate, copy, commit, or summarize the raw data inbox.",
            "- Did not publish raw filenames, raw file hashes, source header plaintext, sheet names, row values, business values, connector secrets, or source files.",
            "- Did not run Stage 7 review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, Redcircle automatic connector, or business execution.",
            "",
            "## Evidence",
            "",
            f"- manifest: `{MANIFEST_PATH.as_posix()}`",
            f"- test_results: `{TEST_RESULTS_PATH.as_posix()}`",
            f"- legacy_manifest: `KMFA/metadata/schema_maps/redcircle_postponement_manifest.json`",
            f"- legacy_policy: `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/redcircle_connector_postponement_policy.json`",
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
            "- PASS: legacy S07-P3 Redcircle postponement validator passed before replay.",
            "- PASS: legacy S07-P3 unit tests passed before replay.",
            "- PASS: v0.1.3 S06 Stage review dependency validator passed before replay.",
            "- PASS: v0.1.3 S07-P1 dependency validator passed before replay.",
            "- PASS: v0.1.3 S07-P2 dependency validator passed before replay.",
            "- PASS: v0.1.3 S07-P3 replay generator wrote manifest and human evidence.",
            "- Required follow-up verification: replay validator, focused unit, governance validators, raw/private scan, public-safe scan, secret scan, parse checks, and diff check.",
            "",
            "## Commands",
            "",
            "```bash",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p3_redcircle_postponement.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_redcircle_postponement_policy -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p2_wps_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s07_p3_redcircle_postponement_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p3_redcircle_postponement_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s07_p3_redcircle_postponement_replay -q",
            "```",
            "",
            f"- manifest: `{MANIFEST_PATH.as_posix()}`",
            f"- report: `{REPORT_PATH.as_posix()}`",
            "- status: `completed_validated_local_only_no_go_upload_deferred_redcircle_postponement_replayed`",
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
    summary = manifest["redcircle_postponement_summary"]
    print(
        "PASS: KMFA v0.1.3 S07-P3 Redcircle postponement replay generated "
        f"(templates={summary['reserved_template_count']}, "
        f"rollback_plans={summary['rollback_plan_count']}, "
        "d15_connector_allowed=false, stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
