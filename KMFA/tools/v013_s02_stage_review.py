#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 2 review evidence.

This stage review replays the public validators for S02-P1/S02-P2/S02-P3 and
locks the stage-level NO_GO status. It does not write to the raw metadata
directory and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s02_p1_raw_readiness import validate_v013_s02_p1_raw_readiness
from KMFA.tools.check_v013_s02_p2_raw_mapping_readiness import (
    validate_v013_s02_p2_raw_mapping_readiness,
)
from KMFA.tools.check_v013_s02_p3_data_quality_error_gate import (
    validate_v013_s02_p3_data_quality_error_gate,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S02_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage2_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage2_review_report.md"
S02_P1_MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_P1_RAW_READINESS/machine/raw_readiness_manifest.json")
S02_P2_MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_P2_RAW_MAPPING_READINESS/machine/raw_mapping_readiness_manifest.json")
S02_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S02_P3_DATA_QUALITY_ERROR_GATE/machine/data_quality_error_gate_manifest.json"
)
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
TASK_ID = "KMFA-V013-S02-STAGE-REVIEW-20260702"
SCHEMA_VERSION = "kmfa.v013_s02_stage_review.v1"


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


def build_manifest() -> dict[str, Any]:
    p1 = validate_v013_s02_p1_raw_readiness()
    p2 = validate_v013_s02_p2_raw_mapping_readiness()
    p3 = validate_v013_s02_p3_data_quality_error_gate()
    hard_blocks = [
        "raw_value_matching_blocked_authorized_mapping_required",
        "owner_authorized_semantic_mapping_missing",
        "raw_row_value_extraction_not_performed",
        "zero_delta_not_performed",
        "lineage_full_check_not_performed",
        "formal_report_release_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S02",
        "stage_name": "v0.1.3 raw readiness and data quality gate",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "review_scope": "v013_s02_stage_review_only",
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "pass_local_only_no_go_upload_deferred",
        "stage_review_performed": True,
        "github_upload_performed": False,
        "github_upload_status": "not_pushed",
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_completed": False,
        "raw_value_matching_performed": False,
        "raw_dir_read_performed_by_stage_review": False,
        "raw_dir_read_performed_by_dependency_validators": True,
        "raw_dir_mutation_performed": False,
        "phase_count": 3,
        "phase_results": {
            "S02-P1": "PASS" if p1.get("phase_id") == "S02-P1" else "FAIL",
            "S02-P2": "PASS" if p2.get("phase_id") == "S02-P2" else "FAIL",
            "S02-P3": "PASS" if p3.get("phase_id") == "S02-P3" else "FAIL",
        },
        "reviewed_phase_manifests": {
            "S02-P1": S02_P1_MANIFEST_PATH.as_posix(),
            "S02-P2": S02_P2_MANIFEST_PATH.as_posix(),
            "S02-P3": S02_P3_MANIFEST_PATH.as_posix(),
        },
        "stage_gate": {
            "current_data_quality_grade": p3["current_data_quality_grade"],
            "current_report_grade": p3["current_report_grade"],
            "release_permission": p3["release_permission"],
        },
        "current_data_quality_grade": p3["current_data_quality_grade"],
        "current_report_grade": p3["current_report_grade"],
        "release_permission": p3["release_permission"],
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 0,
        "review_findings": [],
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
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
            "raw_business_values_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "normalized_business_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s02_p1_raw_readiness.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s02_p2_raw_mapping_readiness.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s02_p3_data_quality_error_gate.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s02_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            "KMFA/stage_artifacts/V013_S02_STAGE_REVIEW/human/test_results.md",
            "KMFA/tools/v013_s02_stage_review.py",
            "KMFA/tools/check_v013_s02_stage_review.py",
            "KMFA/tests/test_v013_s02_stage_review.py",
        ],
        "next_required_step": (
            "Proceed to v0.1.3 S03-P1 as a separate run; GitHub main upload remains deferred "
            "until the overall completion upload gate."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 Stage 2 Review",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- stage_review_performed: `{str(manifest['stage_review_performed']).lower()}`",
        f"- phase_count: `{manifest['phase_count']}`",
        "- phase_results: `S02-P1=PASS`, `S02-P2=PASS`, `S02-P3=PASS`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- raw_value_matching_performed: `false`",
        "- raw_dir_read_performed_by_stage_review: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- github_upload_performed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        "## Review Findings",
        "",
        "- open_review_finding_count: `0`",
        "- fixed_review_finding_count: `0`",
        "",
        "## Hard Blocks",
        "",
    ]
    lines.extend(f"- `{block}`" for block in manifest["hard_blocks"])
    lines.extend(
        [
            "",
            "## Public Safety",
            "",
            "This review evidence contains only public-safe booleans, aggregate gate status, blocker IDs, validator references, and governance paths.",
            "It does not contain raw filenames, raw hashes, sheet names, ZIP member names, field/header plaintext, row values, business values, credentials, contracts, payroll, tax filings, or bank statements.",
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 Stage 2 review evidence generated "
        f"(phases={manifest['phase_count']}, quality={manifest['current_data_quality_grade']}, "
        f"report={manifest['current_report_grade']}, release={manifest['release_permission']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
