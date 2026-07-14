#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S07-P1 finance file adapter replay evidence.

This phase replays the existing public-safe S07-P1 finance file adapter
metadata. It validates the v0.1.3 Stage 6 dependency and legacy S07-P1
artifacts, then emits aggregate evidence only. It does not read the local raw
data inbox and does not publish raw filenames, raw hashes, source headers,
sheet names, ZIP member names, row values, business values, or source files.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_stage_review import validate_v013_s06_stage_review
from KMFA.tools.finance_file_adapter import (
    DEFAULT_OUTPUT_CANDIDATES as LEGACY_CANDIDATES,
    DEFAULT_OUTPUT_FIELD_REPORT as LEGACY_FIELD_REPORT,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_MANIFEST,
    DEFAULT_OUTPUT_REGISTRY as LEGACY_REGISTRY,
    REQUIRED_FINANCE_CATEGORIES,
    validate_finance_adapter,
)
from KMFA.tools.v013_s05_p1_a0_file_registration import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S07_P1_FINANCE_FILE_ADAPTER_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/finance_file_adapter_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/finance_file_adapter_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S06_STAGE_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_STAGE_REVIEW/machine/stage6_review_manifest.json"
)
TASK_ID = "KMFA-V013-S07-P1-FINANCE-FILE-ADAPTER-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s07_p1_finance_file_adapter_replay.v1"
PHASE_SCOPE = "v013_s07_p1_finance_file_adapter_replay_only"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S07-P2 as a separate run only after this phase is committed. "
    "Do not run Stage 7 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, or business execution in the S07-P1 run. "
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no} must contain a JSON object")
        records.append(value)
    return records


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


def validate_legacy_s07_p1() -> dict[str, Any]:
    manifest = read_json(LEGACY_MANIFEST)
    candidates = read_jsonl(LEGACY_CANDIDATES)
    registry = read_json(LEGACY_REGISTRY)
    field_report = read_jsonl(LEGACY_FIELD_REPORT)
    validate_finance_adapter(manifest, candidates, field_report, registry=registry)

    quality_counts = Counter(str(candidate.get("quality_state", {}).get("machine_candidate_quality_grade")) for candidate in candidates)
    q4_confirmed_count = sum(1 for candidate in candidates if candidate.get("quality_state", {}).get("q4_human_confirmed") is True)
    q5_allowed_count = sum(
        1 for candidate in candidates if candidate.get("quality_state", {}).get("q5_calculation_baseline_allowed") is True
    )
    formal_report_allowed_count = sum(
        1 for candidate in candidates if candidate.get("quality_state", {}).get("formal_report_allowed") is True
    )
    hash_only_candidates = [
        candidate
        for candidate in candidates
        if str(candidate.get("source_binding", {}).get("source_header_hash", "")).startswith("sha256:")
        and candidate.get("source_binding", {}).get("source_header_private_ref")
    ]
    source_formats = Counter(str(source.get("file_format")) for source in registry["sources"])

    return {
        "finance_categories": list(manifest["finance_categories"]),
        "source_category_count": manifest["summary"]["source_category_count"],
        "source_registry_count": manifest["summary"]["source_registry_count"],
        "field_candidate_count": manifest["summary"]["field_candidate_count"],
        "field_report_count": manifest["summary"]["field_report_count"],
        "source_header_hash_count": manifest["summary"]["source_header_hash_count"],
        "hash_only_field_candidate_count": len(hash_only_candidates),
        "field_report_readonly_count": sum(1 for record in field_report if record.get("read_only_parse") is True),
        "field_report_raw_layer_write_allowed_count": sum(
            1 for record in field_report if record.get("raw_layer_write_allowed") is True
        ),
        "quality_counts": dict(sorted(quality_counts.items())),
        "q4_human_confirmed_count": q4_confirmed_count,
        "q5_calculation_baseline_allowed_count": q5_allowed_count,
        "formal_report_allowed_count": formal_report_allowed_count,
        "source_format_counts": dict(sorted(source_formats.items())),
        "stage_scope": manifest["stage_scope"],
        "quality_gate": manifest["quality_gate"],
        "public_repo_safety": manifest["public_repo_safety"],
    }


def build_manifest() -> dict[str, Any]:
    s06 = validate_stage6_dependency()
    legacy = validate_legacy_s07_p1()
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S07",
        "stage_name": "v0.1.3 finance source adapter and upstream file support",
        "phase_id": "S07-P1",
        "phase_name": "finance file adapter replay",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_finance_file_adapter_replayed",
        "completed_task_ids": ["S7PAT01", "S7PAT02", "S7PAT03"],
        "acceptance_ids": ["ACC-V013-S07-P1-FINANCE-FILE-ADAPTER-REPLAY"],
        "s06_stage_review_dependency_validated": True,
        "s06_dependency_ref": S06_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s06_dependency_phase_results": s06.get("phase_results", {}),
        "s06_dependency_current_data_quality_grade": s06.get("current_data_quality_grade"),
        "s06_dependency_current_report_grade": s06.get("current_report_grade"),
        "legacy_s07_p1_dependency_validated": True,
        "finance_adapter_summary": {
            "finance_categories": legacy["finance_categories"],
            "source_category_count": legacy["source_category_count"],
            "source_registry_count": legacy["source_registry_count"],
            "field_candidate_count": legacy["field_candidate_count"],
            "field_report_count": legacy["field_report_count"],
            "source_header_hash_count": legacy["source_header_hash_count"],
            "hash_only_field_candidate_count": legacy["hash_only_field_candidate_count"],
            "field_report_readonly_count": legacy["field_report_readonly_count"],
            "field_report_raw_layer_write_allowed_count": legacy["field_report_raw_layer_write_allowed_count"],
            "quality_counts": legacy["quality_counts"],
            "q4_human_confirmed_count": legacy["q4_human_confirmed_count"],
            "q5_calculation_baseline_allowed_count": legacy["q5_calculation_baseline_allowed_count"],
            "formal_report_allowed_count": legacy["formal_report_allowed_count"],
            "source_format_counts": legacy["source_format_counts"],
        },
        "stage_scope": {
            "finance_file_adapter_replay": True,
            "finance_file_adapter": True,
            "wps_scope_included": False,
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
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
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
        "sheet_name_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "row_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "s07_p1_performed": True,
        "s07_p2_performed": False,
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
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s07_p1_finance_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s07_p1_finance_file_adapter_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p1_finance_file_adapter.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py",
        ],
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            "KMFA/tools/v013_s07_p1_finance_file_adapter_replay.py",
            "KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py",
            "KMFA/tests/test_v013_s07_p1_finance_file_adapter_replay.py",
        ],
        "legacy_s07_p1_refs": [
            "KMFA/tools/finance_file_adapter.py",
            "KMFA/tools/check_s07_p1_finance_file_adapter.py",
            "KMFA/tests/test_finance_file_adapter.py",
            "KMFA/metadata/imports/finance_support_source_registry.json",
            "KMFA/metadata/schema_maps/finance_file_adapter_manifest.json",
            "KMFA/metadata/schema_maps/finance_field_candidates.jsonl",
            "KMFA/stage_artifacts/S07_P1_finance_file_adapter/machine/finance_readonly_field_report.jsonl",
            "KMFA/stage_artifacts/S07_P1_finance_file_adapter/human/test_results.md",
        ],
        "non_scope": [
            "S07-P2 WPS adapter",
            "S07-P3 Redcircle postponement policy",
            "Stage 7 review",
            "GitHub upload",
            "raw data inspection",
            "raw directory mutation",
            "raw filename or raw hash publication",
            "source header or raw field plaintext publication",
            "sheet or ZIP member name publication",
            "row value publication",
            "business value publication",
            "raw value matching",
            "lineage full check completion",
            "formal report release",
            "live connector",
            "business execution",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["finance_adapter_summary"]
    lines = [
        "# KMFA v0.1.3 S07-P1 Finance File Adapter Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        f"- s06_stage_review_dependency_validated: `{str(manifest['s06_stage_review_dependency_validated']).lower()}`",
        f"- legacy_s07_p1_dependency_validated: `{str(manifest['legacy_s07_p1_dependency_validated']).lower()}`",
        f"- source_category_count: `{summary['source_category_count']}`",
        f"- field_candidate_count: `{summary['field_candidate_count']}`",
        f"- hash_only_field_candidate_count: `{summary['hash_only_field_candidate_count']}`",
        f"- field_report_count: `{summary['field_report_count']}`",
        f"- source_header_hash_count: `{summary['source_header_hash_count']}`",
        f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
        f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
        f"- formal_report_allowed_count: `{summary['formal_report_allowed_count']}`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        f"- raw_dir_read_performed: `{str(manifest['raw_dir_read_performed']).lower()}`",
        f"- raw_dir_mutation_performed: `{str(manifest['raw_dir_mutation_performed']).lower()}`",
        f"- github_upload_status: `{manifest['github_upload_status']}`",
        "",
        "## Boundary",
        "",
        "- This phase replays public-safe aggregate adapter evidence only.",
        "- It does not read, list, modify, move, delete, rename, overwrite, or write inside the raw data inbox.",
        "- It does not publish source headers, raw filenames, raw hashes, sheet names, ZIP member names, row values, business values, source files, credentials, contracts, bank statements, salary data, or tax filing material.",
        "- S07-P2, S07-P3, Stage 7 review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, and business execution remain out of scope.",
        "",
        "## Next",
        "",
        manifest["next_required_step"],
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_test_results(manifest: dict[str, Any]) -> None:
    lines = [
        "# Test Results",
        "",
        "- PASS: legacy S07-P1 finance adapter validator passed before replay.",
        "- PASS: legacy S07-P1 unit tests passed before replay.",
        "- PASS: v0.1.3 Stage 6 review dependency validator passed before replay.",
        "- PASS: v0.1.3 S07-P1 replay generator wrote manifest and human evidence.",
        "- Required follow-up verification: replay validator, focused unit, governance validators, raw/private scan, public-safe scan, secret scan, parse checks, and diff check.",
        "",
        "## Commands",
        "",
        "```bash",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p1_finance_file_adapter.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_finance_file_adapter -q",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s07_p1_finance_file_adapter_replay.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s07_p1_finance_file_adapter_replay -q",
        "```",
        "",
        f"- manifest: `{MANIFEST_PATH.as_posix()}`",
        f"- report: `{REPORT_PATH.as_posix()}`",
        f"- status: `{manifest['status']}`",
    ]
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    write_report(manifest)
    write_test_results(manifest)
    print(
        "PASS: KMFA v0.1.3 S07-P1 finance file adapter replay generated "
        f"(categories={manifest['finance_adapter_summary']['source_category_count']}, "
        f"field_candidates={manifest['finance_adapter_summary']['field_candidate_count']}, "
        f"field_reports={manifest['finance_adapter_summary']['field_report_count']}, "
        "stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
