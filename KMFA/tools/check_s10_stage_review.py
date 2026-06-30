#!/usr/bin/env python3
"""Validate KMFA Stage 10 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S10_P1_report_templates/machine/s10_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S10_P2_report_grade_runtime/machine/s10_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S10_P3_report_export/machine/s10_p3_manifest.json")

DEFAULT_TEMPLATE_RECORDS = Path("KMFA/metadata/reports/report_templates.jsonl")
DEFAULT_TEMPLATE_SECTIONS = Path("KMFA/metadata/reports/report_template_sections.jsonl")
DEFAULT_GRADE_RECORDS = Path("KMFA/metadata/reports/report_grade_runtime_records.jsonl")
DEFAULT_EXPORT_RECORDS = Path("KMFA/metadata/reports/report_export_records.jsonl")

DEFAULT_HTML_DIR = Path("KMFA/stage_artifacts/S10_P3_report_export/exports/html")
DEFAULT_CSV_DIR = Path("KMFA/stage_artifacts/S10_P3_report_export/exports/csv")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_count(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        json.loads(line)
        count += 1
    return count


def fail(message: str) -> None:
    raise ValueError(message)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def require_true(label: str, actual: Any) -> None:
    if actual is not True:
        fail(f"{label}: expected true, got {actual!r}")


def require_false(label: str, actual: Any) -> None:
    if actual is not False:
        fail(f"{label}: expected false, got {actual!r}")


def require_phase_status(stage_phase_status: Any, phase: str) -> None:
    if not isinstance(stage_phase_status, dict):
        fail("stage_phase_status: expected object")
    status = stage_phase_status.get(phase)
    if not isinstance(status, str) or not status.startswith("completed_validated_local_only"):
        fail(f"stage_phase_status.{phase}: expected completed_validated_local_only*, got {status!r}")


def require_false_flags(label: str, payload: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        require_false(f"{label}.{key}", payload.get(key))


def require_public_safety(label: str, payload: dict[str, Any]) -> None:
    public_safety = payload.get("public_repo_safety")
    if not isinstance(public_safety, dict):
        fail(f"{label}.public_repo_safety: expected object")
    for key, value in public_safety.items():
        require_false(f"{label}.public_repo_safety.{key}", value)


def validate_stage_review(
    review_manifest_path: Path = DEFAULT_REVIEW_MANIFEST,
    p1_manifest_path: Path = DEFAULT_P1_MANIFEST,
    p2_manifest_path: Path = DEFAULT_P2_MANIFEST,
    p3_manifest_path: Path = DEFAULT_P3_MANIFEST,
    template_records_path: Path = DEFAULT_TEMPLATE_RECORDS,
    template_sections_path: Path = DEFAULT_TEMPLATE_SECTIONS,
    grade_records_path: Path = DEFAULT_GRADE_RECORDS,
    export_records_path: Path = DEFAULT_EXPORT_RECORDS,
    html_dir: Path = DEFAULT_HTML_DIR,
    csv_dir: Path = DEFAULT_CSV_DIR,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        template_records_path,
        template_sections_path,
        grade_records_path,
        export_records_path,
        html_dir / "project_cost_special_report.html",
        html_dir / "business_overview_report.html",
        csv_dir / "project_cost_special_report_appendix.csv",
        csv_dir / "business_overview_report_appendix.csv",
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)

    require_equal("stage", review_manifest.get("stage"), "S10")
    require_equal("status", review_manifest.get("status"), "pass_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("upload_performed", review_manifest.get("upload_performed"))
    require_false("s11_allowed", review_manifest.get("s11_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("ui_scope_included", review_manifest.get("ui_scope_included"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("full_trusted_report_allowed", review_manifest.get("full_trusted_report_allowed"))
    require_equal("report_grade_distribution", review_manifest.get("report_grade_distribution"), {"D": 2})
    require_public_safety("review", review_manifest)

    stage_phase_status = review_manifest.get("stage_phase_status")
    for phase in ("S10-P1", "S10-P2", "S10-P3"):
        require_phase_status(stage_phase_status, phase)

    for ref in review_manifest.get("evidence_refs", []):
        if not Path(ref).exists():
            fail(f"missing evidence ref: {ref}")

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S10-P1")
    require_equal("p1.status", p1_manifest.get("status"), "completed_validated_local_only")
    require_equal("p1.summary.template_count", p1_manifest.get("summary", {}).get("template_count"), 2)
    require_equal("p1.summary.section_count", p1_manifest.get("summary", {}).get("section_count"), 11)
    require_equal("p1.summary.project_cost_section_count", p1_manifest.get("summary", {}).get("project_cost_section_count"), 4)
    require_equal("p1.summary.business_overview_section_count", p1_manifest.get("summary", {}).get("business_overview_section_count"), 7)
    require_equal("p1.summary.export_artifact_count", p1_manifest.get("summary", {}).get("export_artifact_count"), 0)
    require_equal("p1.summary.formal_report_count", p1_manifest.get("summary", {}).get("formal_report_count"), 0)
    require_equal("p1.summary.pending_reconciliation_count", p1_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "formal_report_allowed",
            "trusted_grade_assignment_allowed",
            "s10_p2_report_grade_runtime_allowed",
            "s10_p3_export_allowed",
            "html_export_allowed",
            "csv_excel_export_allowed",
            "pdf_export_allowed",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "stage10_review_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S10-P2")
    require_equal("p2.status", p2_manifest.get("status"), "completed_validated_local_only")
    require_equal("p2.summary.report_grade_record_count", p2_manifest.get("summary", {}).get("report_grade_record_count"), 2)
    require_equal("p2.summary.grade_distribution", p2_manifest.get("summary", {}).get("grade_distribution"), {"D": 2})
    require_equal("p2.summary.pending_reconciliation_count", p2_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p2.summary.confirmed_resolution_count", p2_manifest.get("summary", {}).get("confirmed_resolution_count"), 0)
    require_equal("p2.summary.full_trusted_report_allowed_count", p2_manifest.get("summary", {}).get("full_trusted_report_allowed_count"), 0)
    require_equal("p2.summary.formal_report_count", p2_manifest.get("summary", {}).get("formal_report_count"), 0)
    require_equal("p2.summary.export_artifact_count", p2_manifest.get("summary", {}).get("export_artifact_count"), 0)
    require_false("p2.summary.zero_delta_passed", p2_manifest.get("summary", {}).get("zero_delta_passed"))
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "formal_report_allowed",
            "complete_trusted_report_display_allowed",
            "business_decision_basis_allowed",
            "s10_p3_export_allowed",
            "html_export_allowed",
            "csv_excel_export_allowed",
            "pdf_export_allowed",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "stage10_review_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S10-P3")
    require_equal("p3.status", p3_manifest.get("status"), "completed_validated_local_only_review_pending")
    require_equal("p3.next_gate", p3_manifest.get("next_gate"), "S10_STAGE_REVIEW_REQUIRED_BEFORE_GITHUB_UPLOAD")
    require_equal("p3.summary.report_export_record_count", p3_manifest.get("summary", {}).get("report_export_record_count"), 2)
    require_equal("p3.summary.html_export_count", p3_manifest.get("summary", {}).get("html_export_count"), 2)
    require_equal("p3.summary.csv_appendix_count", p3_manifest.get("summary", {}).get("csv_appendix_count"), 2)
    require_equal("p3.summary.excel_compatible_download_count", p3_manifest.get("summary", {}).get("excel_compatible_download_count"), 2)
    require_equal("p3.summary.committed_pdf_file_count", p3_manifest.get("summary", {}).get("committed_pdf_file_count"), 0)
    require_equal("p3.summary.committed_excel_file_count", p3_manifest.get("summary", {}).get("committed_excel_file_count"), 0)
    require_equal("p3.summary.formal_report_count", p3_manifest.get("summary", {}).get("formal_report_count"), 0)
    require_equal("p3.summary.business_decision_basis_count", p3_manifest.get("summary", {}).get("business_decision_basis_count"), 0)
    require_equal("p3.summary.pending_reconciliation_count", p3_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p3.summary.grade_distribution", p3_manifest.get("summary", {}).get("grade_distribution"), {"D": 2})
    require_true("p3.summary.pdf_export_enabled_after_template_stable", p3_manifest.get("summary", {}).get("pdf_export_enabled_after_template_stable"))
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "formal_report_allowed",
            "complete_trusted_report_display_allowed",
            "business_decision_basis_allowed",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "stage10_review_allowed",
        ),
    )
    require_public_safety("p3", p3_manifest)

    counts = {
        "report_template_count": read_jsonl_count(template_records_path),
        "report_template_section_count": read_jsonl_count(template_sections_path),
        "report_grade_record_count": read_jsonl_count(grade_records_path),
        "report_export_record_count": read_jsonl_count(export_records_path),
        "html_export_count": len(list(html_dir.glob("*.html"))),
        "csv_appendix_count": len(list(csv_dir.glob("*_appendix.csv"))),
    }
    expected_counts = {
        "report_template_count": 2,
        "report_template_section_count": 11,
        "report_grade_record_count": 2,
        "report_export_record_count": 2,
        "html_export_count": 2,
        "csv_appendix_count": 2,
    }
    for key, expected in expected_counts.items():
        require_equal(key, counts[key], expected)

    review_counts = review_manifest.get("review_counts")
    if not isinstance(review_counts, dict):
        fail("review_counts: expected object")
    for key, expected in {
        "report_template_count": 2,
        "report_template_section_count": 11,
        "project_cost_section_count": 4,
        "business_overview_section_count": 7,
        "report_grade_record_count": 2,
        "report_export_record_count": 2,
        "html_export_count": 2,
        "csv_appendix_count": 2,
        "excel_compatible_download_count": 2,
        "pending_owner_or_authorized_review_records": 12,
        "committed_pdf_file_count": 0,
        "committed_excel_file_count": 0,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "full_kmfa_unit_tests": 116,
    }.items():
        require_equal(f"review_counts.{key}", review_counts.get(key), expected)
    counts["full_kmfa_unit_tests"] = int(review_counts["full_kmfa_unit_tests"])

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 10 review evidence and gates.")
    parser.add_argument("--review-manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    parser.add_argument("--p1-manifest", type=Path, default=DEFAULT_P1_MANIFEST)
    parser.add_argument("--p2-manifest", type=Path, default=DEFAULT_P2_MANIFEST)
    parser.add_argument("--p3-manifest", type=Path, default=DEFAULT_P3_MANIFEST)
    parser.add_argument("--template-records", type=Path, default=DEFAULT_TEMPLATE_RECORDS)
    parser.add_argument("--template-sections", type=Path, default=DEFAULT_TEMPLATE_SECTIONS)
    parser.add_argument("--grade-records", type=Path, default=DEFAULT_GRADE_RECORDS)
    parser.add_argument("--export-records", type=Path, default=DEFAULT_EXPORT_RECORDS)
    parser.add_argument("--html-dir", type=Path, default=DEFAULT_HTML_DIR)
    parser.add_argument("--csv-dir", type=Path, default=DEFAULT_CSV_DIR)
    args = parser.parse_args(argv)

    try:
        counts = validate_stage_review(
            args.review_manifest,
            args.p1_manifest,
            args.p2_manifest,
            args.p3_manifest,
            args.template_records,
            args.template_sections,
            args.grade_records,
            args.export_records,
            args.html_dir,
            args.csv_dir,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: KMFA S10 stage review check failed ({exc})", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA S10 stage review check passed "
        f"(report_templates={counts['report_template_count']}, "
        f"sections={counts['report_template_section_count']}, "
        f"grade_records={counts['report_grade_record_count']}, "
        f"export_records={counts['report_export_record_count']}, "
        f"html_exports={counts['html_export_count']}, "
        f"csv_appendices={counts['csv_appendix_count']}, "
        "pending_owner_or_authorized_review_records=12, "
        "upload_allowed_after_review=true, s11_allowed=false, github_upload_status=not_pushed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
