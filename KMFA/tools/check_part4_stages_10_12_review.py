#!/usr/bin/env python3
"""Validate KMFA post-S18 Part 4 review evidence for Stages 10-12."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("KMFA/stage_artifacts/PART4_STAGES_10_12_REVIEW/machine/part4_review_manifest.json")

REQUIRED_STAGE_ARTIFACTS = (
    "KMFA/stage_artifacts/S10_P1_report_templates/human/s10_p1_completion_record.md",
    "KMFA/stage_artifacts/S10_P1_report_templates/human/test_results.md",
    "KMFA/stage_artifacts/S10_P1_report_templates/machine/s10_p1_manifest.json",
    "KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/s10_p2_completion_record.md",
    "KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/test_results.md",
    "KMFA/stage_artifacts/S10_P2_report_grade_runtime/machine/s10_p2_manifest.json",
    "KMFA/stage_artifacts/S10_P3_report_export/exports/csv/business_overview_report_appendix.csv",
    "KMFA/stage_artifacts/S10_P3_report_export/exports/csv/project_cost_special_report_appendix.csv",
    "KMFA/stage_artifacts/S10_P3_report_export/exports/html/business_overview_report.html",
    "KMFA/stage_artifacts/S10_P3_report_export/exports/html/project_cost_special_report.html",
    "KMFA/stage_artifacts/S10_P3_report_export/human/s10_p3_completion_record.md",
    "KMFA/stage_artifacts/S10_P3_report_export/human/test_results.md",
    "KMFA/stage_artifacts/S10_P3_report_export/machine/s10_p3_manifest.json",
    "KMFA/stage_artifacts/S10_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S10_STAGE_REVIEW/human/stage10_review_report.md",
    "KMFA/stage_artifacts/S10_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_review_manifest.json",
    "KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_upload_manifest.json",
    "KMFA/stage_artifacts/S11_P1_home_navigation/exports/html/kmfa_home_navigation.html",
    "KMFA/stage_artifacts/S11_P1_home_navigation/human/s11_p1_completion_record.md",
    "KMFA/stage_artifacts/S11_P1_home_navigation/human/test_results.md",
    "KMFA/stage_artifacts/S11_P1_home_navigation/machine/s11_p1_manifest.json",
    "KMFA/stage_artifacts/S11_P2_source_check_board/exports/html/kmfa_source_check_board.html",
    "KMFA/stage_artifacts/S11_P2_source_check_board/human/s11_p2_completion_record.md",
    "KMFA/stage_artifacts/S11_P2_source_check_board/human/test_results.md",
    "KMFA/stage_artifacts/S11_P2_source_check_board/machine/s11_p2_manifest.json",
    "KMFA/stage_artifacts/S11_P3_project_cost_page/exports/html/kmfa_project_cost_page.html",
    "KMFA/stage_artifacts/S11_P3_project_cost_page/human/s11_p3_completion_record.md",
    "KMFA/stage_artifacts/S11_P3_project_cost_page/human/test_results.md",
    "KMFA/stage_artifacts/S11_P3_project_cost_page/machine/s11_p3_manifest.json",
    "KMFA/stage_artifacts/S11_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S11_STAGE_REVIEW/human/stage11_review_report.md",
    "KMFA/stage_artifacts/S11_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_review_manifest.json",
    "KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_upload_manifest.json",
    "KMFA/stage_artifacts/S12_GITHUB_UPLOAD/human/github_upload_record.md",
    "KMFA/stage_artifacts/S12_GITHUB_UPLOAD/machine/stage12_upload_manifest.json",
    "KMFA/stage_artifacts/S12_P1_manual_resolution_events/exports/html/kmfa_manual_resolution_workbench.html",
    "KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/s12_p1_completion_record.md",
    "KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/test_results.md",
    "KMFA/stage_artifacts/S12_P1_manual_resolution_events/machine/s12_p1_manifest.json",
    "KMFA/stage_artifacts/S12_P2_manual_impact_preview/exports/html/kmfa_manual_impact_preview.html",
    "KMFA/stage_artifacts/S12_P2_manual_impact_preview/human/s12_p2_completion_record.md",
    "KMFA/stage_artifacts/S12_P2_manual_impact_preview/human/test_results.md",
    "KMFA/stage_artifacts/S12_P2_manual_impact_preview/machine/s12_p2_manifest.json",
    "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/exports/html/kmfa_manual_rerun_mechanism.html",
    "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/human/s12_p3_completion_record.md",
    "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/human/test_results.md",
    "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/machine/s12_p3_manifest.json",
    "KMFA/stage_artifacts/S12_STAGE_REVIEW/human/stage12_review_report.md",
    "KMFA/stage_artifacts/S12_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S12_STAGE_REVIEW/machine/stage12_review_manifest.json",
)

REQUIRED_BASELINE_REFS = (
    "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md",
    "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
    "KMFA/tools/report_templates.py",
    "KMFA/tools/check_s10_p1_report_templates.py",
    "KMFA/tests/test_report_templates.py",
    "KMFA/tools/report_grade_runtime.py",
    "KMFA/tools/check_s10_p2_report_grade_runtime.py",
    "KMFA/tests/test_report_grade_runtime.py",
    "KMFA/tools/report_export_runtime.py",
    "KMFA/tools/check_s10_p3_report_export.py",
    "KMFA/tests/test_report_export_runtime.py",
    "KMFA/tools/check_s10_stage_review.py",
    "KMFA/tests/test_s10_stage_review.py",
    "KMFA/metadata/reports/report_templates.jsonl",
    "KMFA/metadata/reports/report_grade_policy.yaml",
    "KMFA/metadata/reports/report_grade_runtime_manifest.json",
    "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
    "KMFA/metadata/reports/report_export_manifest.json",
    "KMFA/metadata/reports/report_export_records.jsonl",
    "KMFA/tools/home_navigation_runtime.py",
    "KMFA/tools/check_s11_p1_home_navigation.py",
    "KMFA/tests/test_home_navigation_runtime.py",
    "KMFA/tools/source_check_board_runtime.py",
    "KMFA/tools/check_s11_p2_source_check_board.py",
    "KMFA/tests/test_source_check_board_runtime.py",
    "KMFA/tools/project_cost_page_runtime.py",
    "KMFA/tools/check_s11_p3_project_cost_page.py",
    "KMFA/tests/test_project_cost_page_runtime.py",
    "KMFA/tools/check_s11_stage_review.py",
    "KMFA/tests/test_s11_stage_review.py",
    "KMFA/metadata/reports/home_navigation_manifest.json",
    "KMFA/metadata/reports/home_navigation_modules.jsonl",
    "KMFA/metadata/reports/source_check_board_manifest.json",
    "KMFA/metadata/reports/source_check_board_rows.jsonl",
    "KMFA/metadata/reports/project_cost_page_manifest.json",
    "KMFA/metadata/reports/project_cost_page_projects.jsonl",
    "KMFA/tools/manual_resolution_events.py",
    "KMFA/tools/check_s12_p1_manual_resolution_events.py",
    "KMFA/tests/test_manual_resolution_events.py",
    "KMFA/tools/manual_impact_preview.py",
    "KMFA/tools/check_s12_p2_manual_impact_preview.py",
    "KMFA/tests/test_manual_impact_preview.py",
    "KMFA/tools/manual_rerun_mechanism.py",
    "KMFA/tools/check_s12_p3_manual_rerun_mechanism.py",
    "KMFA/tests/test_manual_rerun_mechanism.py",
    "KMFA/tools/check_s12_stage_review.py",
    "KMFA/tests/test_s12_stage_review.py",
    "KMFA/metadata/approvals/manual_resolution_event_manifest.json",
    "KMFA/metadata/approvals/manual_resolution_events.jsonl",
    "KMFA/metadata/approvals/manual_impact_preview_manifest.json",
    "KMFA/metadata/approvals/manual_impact_previews.jsonl",
    "KMFA/metadata/lineage/manual_rerun_manifest.json",
    "KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl",
    "KMFA/metadata/lineage/manual_rerun_steps.jsonl",
    "KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path} contains non-object JSONL record")
            records.append(payload)
    return records


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


def _require_review_gate(label: str, payload: dict[str, Any], next_scope_key: str) -> dict[str, Any]:
    _require_equal(f"{label}.github_upload_status", payload.get("github_upload_status"), "not_pushed")
    if "upload_performed" in payload:
        _require_false(f"{label}.upload_performed", payload.get("upload_performed"))
    if "github_upload_performed" in payload:
        _require_false(f"{label}.github_upload_performed", payload.get("github_upload_performed"))
    _require_false(f"{label}.lineage_full_check_performed", payload.get("lineage_full_check_performed"))
    _require_false(f"{label}.formal_report_generated", payload.get("formal_report_generated"))
    _require_false(f"{label}.business_decision_basis_allowed", payload.get("business_decision_basis_allowed"))
    _require_false(f"{label}.{next_scope_key}", payload.get(next_scope_key))
    _require_false_flags(f"{label}.public_repo_safety", payload.get("public_repo_safety", {}))
    counts = payload.get("review_counts")
    if not isinstance(counts, dict):
        _fail(f"{label}.review_counts: expected object")
    return counts


def _require_stage_upload(label: str, payload: dict[str, Any]) -> None:
    _require_equal(f"{label}.status", payload.get("status"), "uploaded_to_github_main")
    if "push_performed" in payload:
        _require_true(f"{label}.push_performed", payload.get("push_performed"))


def validate_part4_review(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    manifest = _read_json(manifest_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.part_review_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("part_id", manifest.get("part_id"), "PART4_STAGES_10_12")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-PART4-STAGES-10-12-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "part_review_passed_local_only")
    _require_equal("stages", manifest.get("stages"), ["S10", "S11", "S12"])
    _require_equal("next_part_id", manifest.get("next_part_id"), "PART5_STAGES_13_15")
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
    _require_equal("review_counts.part4_unit_tests", counts.get("part4_unit_tests"), 53)
    _require_equal("review_counts.full_kmfa_unit_tests", counts.get("full_kmfa_unit_tests"), 272)
    _require_equal("review_counts.s10_report_templates", counts.get("s10_report_templates"), 2)
    _require_equal("review_counts.s10_report_sections", counts.get("s10_report_sections"), 11)
    _require_equal("review_counts.s10_report_grade_records", counts.get("s10_report_grade_records"), 2)
    _require_equal("review_counts.s10_export_records", counts.get("s10_export_records"), 2)
    _require_equal("review_counts.s10_html_exports", counts.get("s10_html_exports"), 2)
    _require_equal("review_counts.s10_csv_appendices", counts.get("s10_csv_appendices"), 2)
    _require_equal("review_counts.s11_home_modules", counts.get("s11_home_modules"), 8)
    _require_equal("review_counts.s11_source_rows", counts.get("s11_source_rows"), 13)
    _require_equal("review_counts.s11_project_cost_rows", counts.get("s11_project_cost_rows"), 4)
    _require_equal("review_counts.s11_html_exports", counts.get("s11_html_exports"), 3)
    _require_equal("review_counts.s12_manual_events", counts.get("s12_manual_events"), 5)
    _require_equal("review_counts.s12_impact_previews", counts.get("s12_impact_previews"), 5)
    _require_equal("review_counts.s12_eligible_reruns", counts.get("s12_eligible_reruns"), 2)
    _require_equal("review_counts.s12_blocked_previews", counts.get("s12_blocked_previews"), 3)
    _require_equal("review_counts.s12_rerun_steps", counts.get("s12_rerun_steps"), 8)
    _require_equal("review_counts.s12_consistency_checks", counts.get("s12_consistency_checks"), 2)

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
        _fail("missing required Part 4 paths: " + ", ".join(missing))

    stage10 = _read_json(Path("KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_review_manifest.json"))
    stage11 = _read_json(Path("KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_review_manifest.json"))
    stage12 = _read_json(Path("KMFA/stage_artifacts/S12_STAGE_REVIEW/machine/stage12_review_manifest.json"))
    stage10_counts = _require_review_gate("S10 review", stage10, "s11_allowed")
    stage11_counts = _require_review_gate("S11 review", stage11, "s12_allowed")
    stage12_counts = _require_review_gate("S12 review", stage12, "s13_allowed")

    _require_stage_upload("S10 upload", _read_json(Path("KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_upload_manifest.json")))
    _require_stage_upload("S11 upload", _read_json(Path("KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_upload_manifest.json")))
    _require_stage_upload("S12 upload", _read_json(Path("KMFA/stage_artifacts/S12_GITHUB_UPLOAD/machine/stage12_upload_manifest.json")))

    _require_equal("S10.report_template_count", stage10_counts.get("report_template_count"), 2)
    _require_equal("S10.report_template_section_count", stage10_counts.get("report_template_section_count"), 11)
    _require_equal("S10.report_grade_record_count", stage10_counts.get("report_grade_record_count"), 2)
    _require_equal("S10.report_export_record_count", stage10_counts.get("report_export_record_count"), 2)
    _require_equal("S10.html_export_count", stage10_counts.get("html_export_count"), 2)
    _require_equal("S10.csv_appendix_count", stage10_counts.get("csv_appendix_count"), 2)
    _require_equal("S10.committed_pdf_file_count", stage10_counts.get("committed_pdf_file_count"), 0)
    _require_equal("S10.committed_excel_file_count", stage10_counts.get("committed_excel_file_count"), 0)
    _require_equal("S10.formal_report_count", stage10_counts.get("formal_report_count"), 0)

    _require_equal("S11.home_navigation_module_count", stage11_counts.get("home_navigation_module_count"), 8)
    _require_equal("S11.source_check_board_row_count", stage11_counts.get("source_check_board_row_count"), 13)
    _require_equal("S11.project_cost_page_project_count", stage11_counts.get("project_cost_page_project_count"), 4)
    _require_equal("S11.html_export_count", stage11_counts.get("html_export_count"), 3)
    _require_equal("S11.pending_owner_or_authorized_review_records", stage11_counts.get("pending_owner_or_authorized_review_records"), 12)
    _require_equal("S11.quality_bypass_allowed_count", stage11_counts.get("quality_bypass_allowed_count"), 0)

    _require_equal("S12.manual_resolution_event_count", stage12_counts.get("manual_resolution_event_count"), 5)
    _require_equal("S12.manual_impact_preview_count", stage12_counts.get("manual_impact_preview_count"), 5)
    _require_equal("S12.eligible_rerun_event_count", stage12_counts.get("eligible_rerun_event_count"), 2)
    _require_equal("S12.blocked_publish_count", stage12_counts.get("blocked_publish_count"), 3)
    _require_equal("S12.rerun_step_count", stage12_counts.get("rerun_step_count"), 8)
    _require_equal("S12.same_source_consistency_check_count", stage12_counts.get("same_source_consistency_check_count"), 2)
    _require_equal("S12.github_upload_count", stage12_counts.get("github_upload_count"), 0)

    report_templates = _read_jsonl(Path("KMFA/metadata/reports/report_templates.jsonl"))
    grade_records = _read_jsonl(Path("KMFA/metadata/reports/report_grade_runtime_records.jsonl"))
    export_records = _read_jsonl(Path("KMFA/metadata/reports/report_export_records.jsonl"))
    home_modules = _read_jsonl(Path("KMFA/metadata/reports/home_navigation_modules.jsonl"))
    source_rows = _read_jsonl(Path("KMFA/metadata/reports/source_check_board_rows.jsonl"))
    project_rows = _read_jsonl(Path("KMFA/metadata/reports/project_cost_page_projects.jsonl"))
    manual_events = _read_jsonl(Path("KMFA/metadata/approvals/manual_resolution_events.jsonl"))
    impact_previews = _read_jsonl(Path("KMFA/metadata/approvals/manual_impact_previews.jsonl"))
    invalidations = _read_jsonl(Path("KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl"))
    rerun_steps = _read_jsonl(Path("KMFA/metadata/lineage/manual_rerun_steps.jsonl"))
    consistency_checks = _read_jsonl(Path("KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl"))

    _require_equal("metadata.report_templates", len(report_templates), 2)
    _require_equal("metadata.report_grade_records", len(grade_records), 2)
    _require_equal("metadata.report_export_records", len(export_records), 2)
    _require_equal("metadata.home_navigation_modules", len(home_modules), 8)
    _require_equal("metadata.source_check_board_rows", len(source_rows), 13)
    _require_equal("metadata.project_cost_page_projects", len(project_rows), 4)
    _require_equal("metadata.manual_resolution_events", len(manual_events), 5)
    _require_equal("metadata.manual_impact_previews", len(impact_previews), 5)
    _require_equal("metadata.manual_rerun_cache_invalidations", len(invalidations), 2)
    _require_equal("metadata.manual_rerun_steps", len(rerun_steps), 8)
    _require_equal("metadata.manual_rerun_consistency_checks", len(consistency_checks), 2)

    if any(record.get("computed_report_grade") != "D" for record in grade_records):
        _fail("S10 report grade records must remain D")
    if any(record.get("formal_report_allowed") is not False for record in grade_records + export_records + home_modules + source_rows + project_rows):
        _fail("report/UI records must keep formal_report_allowed=false")
    if any(record.get("github_upload_allowed") is not False for record in impact_previews + invalidations + rerun_steps + consistency_checks):
        _fail("S12 rerun/preview records must keep github_upload_allowed=false")
    if sum(1 for record in impact_previews if record.get("preview_passed") is True) != 2:
        _fail("S12 preview_passed count must remain 2")
    if sum(1 for record in impact_previews if record.get("control_event_publish_allowed") is False) != 3:
        _fail("S12 blocked publish count must remain 3")

    return {
        "stage_count": counts["stage_count"],
        "phase_count": counts["phase_count"],
        "required_stage_artifact_count": counts["required_stage_artifact_count"],
        "required_baseline_ref_count": counts["required_baseline_ref_count"],
        "part4_unit_tests": counts["part4_unit_tests"],
        "full_kmfa_unit_tests": counts["full_kmfa_unit_tests"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "github_upload_count": int(manifest["github_upload_performed"]),
    }


def main() -> int:
    try:
        counts = validate_part4_review(DEFAULT_MANIFEST)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA Part 4 Stage 10-12 review check passed "
        f"(stages={counts['stage_count']}, phases={counts['phase_count']}, "
        f"stage_artifacts={counts['required_stage_artifact_count']}, "
        f"baseline_refs={counts['required_baseline_ref_count']}, "
        f"part4_tests={counts['part4_unit_tests']}, full_tests={counts['full_kmfa_unit_tests']}, "
        f"github_upload={counts['github_upload_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
