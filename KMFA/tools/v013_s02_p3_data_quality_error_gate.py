#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S02-P3 data quality and error gate evidence.

This phase does not inspect raw files. It derives the current public-safe gate
from S02-P1/S02-P2 public manifests and the existing S02-P3 policy definitions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s02_p1_raw_readiness import validate_v013_s02_p1_raw_readiness
from KMFA.tools.check_v013_s02_p2_raw_mapping_readiness import (
    validate_v013_s02_p2_raw_mapping_readiness,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S02_P3_DATA_QUALITY_ERROR_GATE")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/data_quality_error_gate_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/data_quality_error_gate_report.md"
QUALITY_POLICY_PATH = Path("KMFA/metadata/quality/quality_grade_policy.yaml")
REPORT_POLICY_PATH = Path("KMFA/metadata/reports/report_grade_policy.yaml")
RELEASE_GATE_PATH = Path("KMFA/metadata/reports/report_release_gate.yaml")
S02_P1_MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_P1_RAW_READINESS/machine/raw_readiness_manifest.json")
S02_P2_MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S02_P2_RAW_MAPPING_READINESS/machine/raw_mapping_readiness_manifest.json")
TASK_ID = "KMFA-V013-S02-P3-DATA-QUALITY-ERROR-GATE-20260702"
SCHEMA_VERSION = "kmfa.v013_s02_p3_data_quality_error_gate.v1"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def quality_gate_map(release_gate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["quality_grade"]: {
            "maximum_report_grade": item["maximum_report_grade"],
            "release_permission": item["release_permission"],
        }
        for item in release_gate["quality_to_report_gate"]
    }


def build_manifest() -> dict[str, Any]:
    s02_p1_result = validate_v013_s02_p1_raw_readiness()
    s02_p2_result = validate_v013_s02_p2_raw_mapping_readiness()
    s02_p1_manifest = read_json(S02_P1_MANIFEST_PATH)
    s02_p2_manifest = read_json(S02_P2_MANIFEST_PATH)
    quality_policy = read_json(QUALITY_POLICY_PATH)
    report_policy = read_json(REPORT_POLICY_PATH)
    release_gate = read_json(RELEASE_GATE_PATH)
    quality_grades = [item["grade"] for item in quality_policy["quality_grades"]]
    report_grades = [item["grade"] for item in report_policy["report_grades"]]
    gate_map = quality_gate_map(release_gate)

    current_quality_grade = "Q2"
    current_report_grade = gate_map[current_quality_grade]["maximum_report_grade"]
    release_permission = gate_map[current_quality_grade]["release_permission"]
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
        "phase_id": "S02-P3",
        "task_id": TASK_ID,
        "phase_scope": "data_quality_error_gate_public_safe_lock",
        "s02_p1_dependency_validated": s02_p1_result.get("phase_id") == "S02-P1",
        "s02_p2_dependency_validated": s02_p2_result.get("phase_id") == "S02-P2",
        "quality_grade_policy_validated": quality_policy.get("schema_version") == "kmfa.quality_grade_policy.v1",
        "report_grade_policy_validated": report_policy.get("schema_version") == "kmfa.report_grade_policy.v1",
        "release_gate_policy_validated": release_gate.get("schema_version") == "kmfa.report_release_gate.v1",
        "quality_grades": quality_grades,
        "report_grades": report_grades,
        "quality_to_report_gate": gate_map,
        "current_data_quality_grade": current_quality_grade,
        "current_data_quality_grade_reason": (
            "Raw files and container/schema readiness are visible through S02-P1/S02-P2 aggregate evidence, "
            "but row-value extraction, owner-authorized semantic mapping, zero-delta, and full lineage are not complete."
        ),
        "current_report_grade": current_report_grade,
        "release_permission": release_permission,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "formal_report_allowed": False,
        "internal_review_report_allowed": False,
        "preview_allowed": False,
        "business_decision_basis_allowed": False,
        "data_matches_raw_claim_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "raw_value_matching_performed": False,
        "raw_value_matching_readiness_status": s02_p2_manifest["raw_value_matching_readiness_status"],
        "raw_business_value_extraction_performed": False,
        "raw_row_value_extraction_performed": False,
        "raw_dir": s02_p1_manifest["raw_dir"],
        "raw_dir_read_performed_by_s02_p3": False,
        "raw_dir_mutation_allowed": False,
        "raw_dir_mutation_performed": False,
        "stage_review_performed": False,
        "github_upload_performed": False,
        "delivery_allowed": False,
        "business_execution_allowed": False,
        "source_public_manifests": [
            S02_P1_MANIFEST_PATH.as_posix(),
            S02_P2_MANIFEST_PATH.as_posix(),
        ],
        "policy_refs": [
            QUALITY_POLICY_PATH.as_posix(),
            REPORT_POLICY_PATH.as_posix(),
            RELEASE_GATE_PATH.as_posix(),
            "KMFA/docs/governance/QUALITY_GATE_POLICY.md",
        ],
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
        },
        "public_manifest_contains_raw_filenames": False,
        "public_manifest_contains_field_plaintext": False,
        "public_manifest_contains_sheet_names": False,
        "public_manifest_contains_zip_member_names": False,
        "public_manifest_contains_raw_values": False,
        "next_required_step": (
            "Stage 2 review may run only after S02-P1, S02-P2, and S02-P3 validators pass; "
            "GitHub main upload remains deferred until the overall completion upload gate."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S02-P3 Data Quality / Error Gate",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- data_matches_raw_claim_allowed: `false`",
        "- raw_dir_read_performed_by_s02_p3: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- stage_review_performed: `false`",
        "- github_upload_performed: `false`",
        "",
        "## Gate Rationale",
        "",
        manifest["current_data_quality_grade_reason"],
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
            "This evidence contains only policy refs, aggregate gate status, booleans, and blocker IDs.",
            "It does not contain raw file names, raw hashes, sheet names, ZIP member names, field/header plaintext, row values, business values, credentials, bank statements, contracts, payroll, or tax filings.",
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
        "PASS: KMFA v0.1.3 S02-P3 data quality/error gate evidence generated "
        f"(quality={manifest['current_data_quality_grade']}, report={manifest['current_report_grade']}, "
        f"release={manifest['release_permission']}, github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
