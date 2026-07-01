#!/usr/bin/env python3
"""Validate KMFA post-S18 Part 1 review evidence for Stages 1-3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("KMFA/stage_artifacts/PART1_STAGES_01_03_REVIEW/machine/part1_review_manifest.json")

REQUIRED_STAGE_ARTIFACTS = (
    "KMFA/stage_artifacts/S01_P1_read_only_plan/human/s01_p1_completion_record.md",
    "KMFA/stage_artifacts/S01_P1_read_only_plan/machine/s01_p1_manifest.json",
    "KMFA/stage_artifacts/S01_P2_project_skeleton/human/s01_p2_completion_record.md",
    "KMFA/stage_artifacts/S01_P2_project_skeleton/machine/s01_p2_manifest.json",
    "KMFA/stage_artifacts/S01_P3_no_omission_baseline/human/s01_p3_completion_record.md",
    "KMFA/stage_artifacts/S01_P3_no_omission_baseline/human/test_results.md",
    "KMFA/stage_artifacts/S01_STAGE_REVIEW/human/stage1_review_report.md",
    "KMFA/stage_artifacts/S01_STAGE_REVIEW/machine/stage1_review_manifest.json",
    "KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/machine/stage1_v12_manifest.json",
    "KMFA/stage_artifacts/S02_P1_metadata_protocol/human/s02_p1_completion_record.md",
    "KMFA/stage_artifacts/S02_P1_metadata_protocol/human/test_results.md",
    "KMFA/stage_artifacts/S02_P2_immutability_policy/human/s02_p2_completion_record.md",
    "KMFA/stage_artifacts/S02_P2_immutability_policy/human/test_results.md",
    "KMFA/stage_artifacts/S02_P3_quality_gate/human/s02_p3_completion_record.md",
    "KMFA/stage_artifacts/S02_P3_quality_gate/human/test_results.md",
    "KMFA/stage_artifacts/S02_STAGE_REVIEW/human/stage2_review_report.md",
    "KMFA/stage_artifacts/S02_STAGE_REVIEW/machine/stage2_review_manifest.json",
    "KMFA/stage_artifacts/S03_P1_file_import/human/s03_p1_completion_record.md",
    "KMFA/stage_artifacts/S03_P1_file_import/human/test_results.md",
    "KMFA/stage_artifacts/S03_P2_source_check_matrix/human/s03_p2_completion_record.md",
    "KMFA/stage_artifacts/S03_P2_source_check_matrix/human/test_results.md",
    "KMFA/stage_artifacts/S03_P3_source_priority/human/s03_p3_completion_record.md",
    "KMFA/stage_artifacts/S03_P3_source_priority/human/test_results.md",
    "KMFA/stage_artifacts/S03_STAGE_REVIEW/human/stage3_review_report.md",
    "KMFA/stage_artifacts/S03_STAGE_REVIEW/machine/stage3_review_manifest.json",
)

REQUIRED_BASELINE_REFS = (
    "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md",
    "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
    "KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/HTML文件索引_v1_2.csv",
    "KMFA/metadata/protocol/metadata_protocol.yaml",
    "KMFA/metadata/imports/raw_manifest_policy.yaml",
    "KMFA/metadata/reports/report_release_gate.yaml",
    "KMFA/metadata/sources/source_check_matrix.jsonl",
    "KMFA/metadata/sources/source_priority_policy.yaml",
    "KMFA/tools/no_omission_check.py",
    "KMFA/tools/metadata_protocol_check.py",
    "KMFA/tools/immutability_policy_check.py",
    "KMFA/tools/check_report_grade_gate.py",
    "KMFA/tools/file_import_register.py",
    "KMFA/tools/source_check_matrix.py",
    "KMFA/tools/source_priority.py",
    "KMFA/tests/test_file_import_register.py",
    "KMFA/tests/test_source_check_matrix.py",
    "KMFA/tests/test_source_priority.py",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail(message: str) -> None:
    raise ValueError(message)


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        _fail(f"{label}: expected {expected!r}, got {actual!r}")


def _require_true(label: str, actual: Any) -> None:
    if actual is not True:
        _fail(f"{label}: expected true, got {actual!r}")


def _require_false(label: str, actual: Any) -> None:
    if actual is not False:
        _fail(f"{label}: expected false, got {actual!r}")


def _require_existing_refs(refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        _fail("evidence_refs: expected non-empty list")
    missing = [ref for ref in refs if not isinstance(ref, str) or not Path(ref).exists()]
    if missing:
        _fail("missing evidence refs: " + ", ".join(map(str, missing)))


def _require_false_flags(label: str, payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        _require_false(f"{label}.{key}", value)


def validate_part1_review(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    manifest = _read_json(manifest_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.part_review_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("part_id", manifest.get("part_id"), "PART1_STAGES_01_03")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-PART1-STAGES-01-03-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "part_review_passed_local_only")
    _require_equal("stages", manifest.get("stages"), ["S01", "S02", "S03"])
    _require_equal("next_part_id", manifest.get("next_part_id"), "PART2_STAGES_04_06")
    _require_true("part_review_performed", manifest.get("part_review_performed"))
    _require_false("github_upload_performed", manifest.get("github_upload_performed"))
    _require_false("formal_report_generated", manifest.get("formal_report_generated"))
    _require_false("lineage_full_check_performed", manifest.get("lineage_full_check_performed"))
    _require_false("business_execution_allowed", manifest.get("business_execution_allowed"))
    _require_equal("open_review_finding_count", manifest.get("open_review_finding_count"), 0)
    _require_equal("fixed_review_finding_count", manifest.get("fixed_review_finding_count"), 0)

    counts = manifest.get("review_counts")
    if not isinstance(counts, dict):
        _fail("review_counts: expected object")
    _require_equal("review_counts.stage_count", counts.get("stage_count"), 3)
    _require_equal("review_counts.phase_count", counts.get("phase_count"), 9)
    _require_equal("review_counts.required_stage_artifact_count", counts.get("required_stage_artifact_count"), len(REQUIRED_STAGE_ARTIFACTS))
    _require_equal("review_counts.required_baseline_ref_count", counts.get("required_baseline_ref_count"), len(REQUIRED_BASELINE_REFS))
    _require_equal("review_counts.full_kmfa_unit_tests", counts.get("full_kmfa_unit_tests"), 269)
    _require_equal("review_counts.part1_unit_tests", counts.get("part1_unit_tests"), 12)

    validators = manifest.get("validators_rerun")
    if not isinstance(validators, dict):
        _fail("validators_rerun: expected object")
    for key, value in validators.items():
        _require_true(f"validators_rerun.{key}", value)

    _require_false_flags("public_repo_safety", manifest.get("public_repo_safety", {}))
    _require_existing_refs(manifest.get("evidence_refs"))

    required_paths = [Path(ref) for ref in REQUIRED_STAGE_ARTIFACTS + REQUIRED_BASELINE_REFS]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        _fail("missing required Part 1 paths: " + ", ".join(missing))

    stage1 = _read_json(Path("KMFA/stage_artifacts/S01_STAGE_REVIEW/machine/stage1_review_manifest.json"))
    stage2 = _read_json(Path("KMFA/stage_artifacts/S02_STAGE_REVIEW/machine/stage2_review_manifest.json"))
    stage3 = _read_json(Path("KMFA/stage_artifacts/S03_STAGE_REVIEW/machine/stage3_review_manifest.json"))

    _require_equal("stage1.stage_id", stage1.get("stage_id"), "S01")
    _require_equal("stage1.result", stage1.get("result"), "PASS_WITH_UPLOAD_ISOLATION_REQUIRED")
    _require_false("stage1.raw_sensitive_public_repo_allowed", stage1.get("raw_sensitive_public_repo_allowed"))
    _require_equal("stage2.stage_id", stage2.get("stage_id"), "S02")
    _require_equal("stage2.result", stage2.get("result"), "PASS_UPLOAD_READY")
    _require_false("stage2.raw_sensitive_public_repo_allowed", stage2.get("raw_sensitive_public_repo_allowed"))
    _require_equal("stage3.stage", stage3.get("stage"), "S03")
    _require_equal("stage3.status", stage3.get("status"), "pass_upload_ready")

    return {
        "stage_count": counts["stage_count"],
        "phase_count": counts["phase_count"],
        "required_stage_artifact_count": counts["required_stage_artifact_count"],
        "required_baseline_ref_count": counts["required_baseline_ref_count"],
        "full_kmfa_unit_tests": counts["full_kmfa_unit_tests"],
        "part1_unit_tests": counts["part1_unit_tests"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "github_upload_count": 1 if manifest["github_upload_performed"] else 0,
    }


def main() -> int:
    try:
        counts = validate_part1_review()
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"FAIL: KMFA Part 1 Stage 1-3 review check failed: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA Part 1 Stage 1-3 review check passed "
        f"(stages={counts['stage_count']}, phases={counts['phase_count']}, "
        f"stage_artifacts={counts['required_stage_artifact_count']}, "
        f"baseline_refs={counts['required_baseline_ref_count']}, "
        f"part1_tests={counts['part1_unit_tests']}, "
        f"full_tests={counts['full_kmfa_unit_tests']}, "
        f"github_upload={counts['github_upload_count']})"
    )
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main())
