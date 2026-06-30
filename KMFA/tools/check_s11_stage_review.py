#!/usr/bin/env python3
"""Validate KMFA Stage 11 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S11_P1_home_navigation/machine/s11_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S11_P2_source_check_board/machine/s11_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S11_P3_project_cost_page/machine/s11_p3_manifest.json")

DEFAULT_HOME_MODULES = Path("KMFA/metadata/reports/home_navigation_modules.jsonl")
DEFAULT_SOURCE_ROWS = Path("KMFA/metadata/reports/source_check_board_rows.jsonl")
DEFAULT_PROJECT_ROWS = Path("KMFA/metadata/reports/project_cost_page_projects.jsonl")

DEFAULT_HOME_HTML = Path("KMFA/stage_artifacts/S11_P1_home_navigation/exports/html/kmfa_home_navigation.html")
DEFAULT_SOURCE_HTML = Path("KMFA/stage_artifacts/S11_P2_source_check_board/exports/html/kmfa_source_check_board.html")
DEFAULT_PROJECT_HTML = Path("KMFA/stage_artifacts/S11_P3_project_cost_page/exports/html/kmfa_project_cost_page.html")


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
    home_modules_path: Path = DEFAULT_HOME_MODULES,
    source_rows_path: Path = DEFAULT_SOURCE_ROWS,
    project_rows_path: Path = DEFAULT_PROJECT_ROWS,
    home_html_path: Path = DEFAULT_HOME_HTML,
    source_html_path: Path = DEFAULT_SOURCE_HTML,
    project_html_path: Path = DEFAULT_PROJECT_HTML,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        home_modules_path,
        source_rows_path,
        project_rows_path,
        home_html_path,
        source_html_path,
        project_html_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)

    require_equal("stage", review_manifest.get("stage"), "S11")
    require_equal("status", review_manifest.get("status"), "pass_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("upload_performed", review_manifest.get("upload_performed"))
    require_false("s12_allowed", review_manifest.get("s12_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("full_trusted_report_allowed", review_manifest.get("full_trusted_report_allowed"))
    require_equal("report_grade_distribution", review_manifest.get("report_grade_distribution"), {"D": 2})
    require_public_safety("review", review_manifest)

    stage_phase_status = review_manifest.get("stage_phase_status")
    for phase in ("S11-P1", "S11-P2", "S11-P3"):
        require_phase_status(stage_phase_status, phase)

    for ref in review_manifest.get("evidence_refs", []):
        if not Path(ref).exists():
            fail(f"missing evidence ref: {ref}")

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S11-P1")
    require_equal("p1.status", p1_manifest.get("status"), "completed_validated_local_only_stage_review_pending")
    require_equal("p1.summary.navigation_module_count", p1_manifest.get("summary", {}).get("navigation_module_count"), 8)
    require_equal("p1.summary.required_label_count", p1_manifest.get("summary", {}).get("required_label_count"), 8)
    require_true("p1.summary.required_labels_covered", p1_manifest.get("summary", {}).get("required_labels_covered"))
    require_equal("p1.summary.html_export_count", p1_manifest.get("summary", {}).get("html_export_count"), 1)
    require_equal("p1.summary.large_yellow_surface_count", p1_manifest.get("summary", {}).get("large_yellow_surface_count"), 0)
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "formal_report_allowed",
            "complete_trusted_report_display_allowed",
            "business_decision_basis_allowed",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "raw_layer_write_allowed",
            "stage11_review_allowed",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S11-P2")
    require_equal("p2.status", p2_manifest.get("status"), "completed_validated_local_only_stage_review_pending")
    require_equal("p2.summary.matrix_row_count", p2_manifest.get("summary", {}).get("matrix_row_count"), 13)
    require_equal("p2.summary.required_column_count", p2_manifest.get("summary", {}).get("required_column_count"), 11)
    require_true("p2.summary.required_columns_covered", p2_manifest.get("summary", {}).get("required_columns_covered"))
    require_equal("p2.summary.allowed_status_count", p2_manifest.get("summary", {}).get("allowed_status_count"), 5)
    require_true("p2.summary.status_click_detail_enabled", p2_manifest.get("summary", {}).get("status_click_detail_enabled"))
    require_equal("p2.summary.large_yellow_surface_count", p2_manifest.get("summary", {}).get("large_yellow_surface_count"), 0)
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "formal_report_allowed",
            "complete_trusted_report_display_allowed",
            "business_decision_basis_allowed",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "raw_layer_write_allowed",
            "raw_source_mutation_allowed",
            "stage11_review_allowed",
        ),
    )
    require_public_safety("p2", p2_manifest)

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S11-P3")
    require_equal("p3.runtime_status", p3_manifest.get("runtime_status"), "public_safe_project_cost_page_generated_local_only")
    require_equal("p3.summary.project_row_count", p3_manifest.get("summary", {}).get("project_row_count"), 4)
    require_equal("p3.summary.project_list_column_count", p3_manifest.get("summary", {}).get("project_list_column_count"), 7)
    require_true("p3.summary.project_list_columns_covered", p3_manifest.get("summary", {}).get("project_list_columns_covered"))
    require_equal("p3.summary.margin_record_count", p3_manifest.get("summary", {}).get("margin_record_count"), 4)
    require_equal("p3.summary.cost_category_count", p3_manifest.get("summary", {}).get("cost_category_count"), 9)
    require_equal("p3.summary.pending_reconciliation_count", p3_manifest.get("summary", {}).get("pending_reconciliation_count"), 12)
    require_equal("p3.summary.report_grade_visible", p3_manifest.get("summary", {}).get("report_grade_visible"), "D")
    require_true("p3.summary.report_preview_direct_view_allowed", p3_manifest.get("summary", {}).get("report_preview_direct_view_allowed"))
    require_false("p3.summary.quality_grade_bypass_allowed", p3_manifest.get("summary", {}).get("quality_grade_bypass_allowed"))
    require_equal("p3.summary.html_export_count", p3_manifest.get("summary", {}).get("html_export_count"), 1)
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "formal_report_allowed",
            "complete_trusted_report_display_allowed",
            "business_decision_basis_allowed",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "quality_grade_bypass_allowed",
            "raw_layer_write_allowed",
            "report_grade_bypass_allowed",
            "stage11_review_allowed",
        ),
    )
    require_public_safety("p3", p3_manifest)

    counts = {
        "home_navigation_module_count": read_jsonl_count(home_modules_path),
        "source_check_board_row_count": read_jsonl_count(source_rows_path),
        "project_cost_page_project_count": read_jsonl_count(project_rows_path),
        "html_export_count": sum(1 for path in (home_html_path, source_html_path, project_html_path) if path.exists()),
        "pending_reconciliation_count": int(p3_manifest.get("summary", {}).get("pending_reconciliation_count")),
    }

    for key, expected in {
        "home_navigation_module_count": 8,
        "source_check_board_row_count": 13,
        "project_cost_page_project_count": 4,
        "html_export_count": 3,
        "pending_reconciliation_count": 12,
    }.items():
        require_equal(key, counts[key], expected)

    review_counts = review_manifest.get("review_counts")
    if not isinstance(review_counts, dict):
        fail("review_counts: expected object")
    for key, expected in {
        "home_navigation_module_count": 8,
        "source_check_board_row_count": 13,
        "project_cost_page_project_count": 4,
        "html_export_count": 3,
        "cost_category_count": 9,
        "margin_record_count": 4,
        "pending_owner_or_authorized_review_records": 12,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "complete_trusted_report_count": 0,
        "quality_bypass_allowed_count": 0,
        "large_yellow_surface_count": 0,
        "full_kmfa_unit_tests": 132,
    }.items():
        require_equal(f"review_counts.{key}", review_counts.get(key), expected)
    counts["full_kmfa_unit_tests"] = int(review_counts["full_kmfa_unit_tests"])

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 11 review evidence and gates.")
    parser.add_argument("--review-manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    parser.add_argument("--p1-manifest", type=Path, default=DEFAULT_P1_MANIFEST)
    parser.add_argument("--p2-manifest", type=Path, default=DEFAULT_P2_MANIFEST)
    parser.add_argument("--p3-manifest", type=Path, default=DEFAULT_P3_MANIFEST)
    parser.add_argument("--home-modules", type=Path, default=DEFAULT_HOME_MODULES)
    parser.add_argument("--source-rows", type=Path, default=DEFAULT_SOURCE_ROWS)
    parser.add_argument("--project-rows", type=Path, default=DEFAULT_PROJECT_ROWS)
    parser.add_argument("--home-html", type=Path, default=DEFAULT_HOME_HTML)
    parser.add_argument("--source-html", type=Path, default=DEFAULT_SOURCE_HTML)
    parser.add_argument("--project-html", type=Path, default=DEFAULT_PROJECT_HTML)
    args = parser.parse_args(argv)

    try:
        counts = validate_stage_review(
            args.review_manifest,
            args.p1_manifest,
            args.p2_manifest,
            args.p3_manifest,
            args.home_modules,
            args.source_rows,
            args.project_rows,
            args.home_html,
            args.source_html,
            args.project_html,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: KMFA S11 stage review check failed ({exc})", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA S11 stage review check passed "
        f"(home_modules={counts['home_navigation_module_count']}, "
        f"source_rows={counts['source_check_board_row_count']}, "
        f"project_rows={counts['project_cost_page_project_count']}, "
        f"html_exports={counts['html_export_count']}, "
        f"pending_owner_or_authorized_review_records={counts['pending_reconciliation_count']}, "
        "upload_allowed_after_review=true, s12_allowed=false, github_upload_status=not_pushed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
