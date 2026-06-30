#!/usr/bin/env python3
"""Validate KMFA Stage 12 review evidence and gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_REVIEW_MANIFEST = Path("KMFA/stage_artifacts/S12_STAGE_REVIEW/machine/stage12_review_manifest.json")
DEFAULT_P1_MANIFEST = Path("KMFA/stage_artifacts/S12_P1_manual_resolution_events/machine/s12_p1_manifest.json")
DEFAULT_P2_MANIFEST = Path("KMFA/stage_artifacts/S12_P2_manual_impact_preview/machine/s12_p2_manifest.json")
DEFAULT_P3_MANIFEST = Path("KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/machine/s12_p3_manifest.json")

DEFAULT_EVENTS = Path("KMFA/metadata/approvals/manual_resolution_events.jsonl")
DEFAULT_PREVIEWS = Path("KMFA/metadata/approvals/manual_impact_previews.jsonl")
DEFAULT_INVALIDATIONS = Path("KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl")
DEFAULT_RERUN_STEPS = Path("KMFA/metadata/lineage/manual_rerun_steps.jsonl")
DEFAULT_CONSISTENCY_CHECKS = Path("KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl")

DEFAULT_P1_HTML = Path("KMFA/stage_artifacts/S12_P1_manual_resolution_events/exports/html/kmfa_manual_resolution_workbench.html")
DEFAULT_P2_HTML = Path("KMFA/stage_artifacts/S12_P2_manual_impact_preview/exports/html/kmfa_manual_impact_preview.html")
DEFAULT_P3_HTML = Path("KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/exports/html/kmfa_manual_rerun_mechanism.html")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


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


def require_false_flags(label: str, payload: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        require_false(f"{label}.{key}", payload.get(key))


def require_public_safety(label: str, payload: dict[str, Any]) -> None:
    public_safety = payload.get("public_repo_safety")
    if not isinstance(public_safety, dict):
        fail(f"{label}.public_repo_safety: expected object")
    for key, value in public_safety.items():
        require_false(f"{label}.public_repo_safety.{key}", value)


def require_phase_status(stage_phase_status: Any, phase: str) -> None:
    if not isinstance(stage_phase_status, dict):
        fail("stage_phase_status: expected object")
    status = stage_phase_status.get(phase)
    if not isinstance(status, str) or not status.startswith("completed_validated_local_only"):
        fail(f"stage_phase_status.{phase}: expected completed_validated_local_only*, got {status!r}")


def require_existing_refs(refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        fail("evidence_refs: expected non-empty list")
    for ref in refs:
        if not isinstance(ref, str):
            fail(f"evidence_refs: expected string ref, got {ref!r}")
        if not Path(ref).exists():
            fail(f"missing evidence ref: {ref}")


def validate_stage_review(
    review_manifest_path: Path = DEFAULT_REVIEW_MANIFEST,
    p1_manifest_path: Path = DEFAULT_P1_MANIFEST,
    p2_manifest_path: Path = DEFAULT_P2_MANIFEST,
    p3_manifest_path: Path = DEFAULT_P3_MANIFEST,
    events_path: Path = DEFAULT_EVENTS,
    previews_path: Path = DEFAULT_PREVIEWS,
    invalidations_path: Path = DEFAULT_INVALIDATIONS,
    rerun_steps_path: Path = DEFAULT_RERUN_STEPS,
    consistency_checks_path: Path = DEFAULT_CONSISTENCY_CHECKS,
    p1_html_path: Path = DEFAULT_P1_HTML,
    p2_html_path: Path = DEFAULT_P2_HTML,
    p3_html_path: Path = DEFAULT_P3_HTML,
) -> dict[str, int]:
    required_paths = [
        review_manifest_path,
        p1_manifest_path,
        p2_manifest_path,
        p3_manifest_path,
        events_path,
        previews_path,
        invalidations_path,
        rerun_steps_path,
        consistency_checks_path,
        p1_html_path,
        p2_html_path,
        p3_html_path,
        Path("KMFA/stage_artifacts/S12_STAGE_REVIEW/human/stage12_review_report.md"),
        Path("KMFA/stage_artifacts/S12_STAGE_REVIEW/human/test_results.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        fail("missing required evidence paths: " + ", ".join(missing))

    forbidden_upload_paths = [
        Path("KMFA/stage_artifacts/S12_STAGE_REVIEW/human/github_upload_record.md"),
        Path("KMFA/stage_artifacts/S12_STAGE_REVIEW/machine/stage12_upload_manifest.json"),
    ]
    unexpected = [str(path) for path in forbidden_upload_paths if path.exists()]
    if unexpected:
        fail("Stage 12 review must not contain upload evidence: " + ", ".join(unexpected))

    review_manifest = read_json(review_manifest_path)
    p1_manifest = read_json(p1_manifest_path)
    p2_manifest = read_json(p2_manifest_path)
    p3_manifest = read_json(p3_manifest_path)
    events = read_jsonl(events_path)
    previews = read_jsonl(previews_path)
    invalidations = read_jsonl(invalidations_path)
    rerun_steps = read_jsonl(rerun_steps_path)
    consistency_checks = read_jsonl(consistency_checks_path)

    require_equal("stage", review_manifest.get("stage"), "S12")
    require_equal("status", review_manifest.get("status"), "review_passed_upload_ready_local_only")
    require_equal("github_upload_status", review_manifest.get("github_upload_status"), "not_pushed")
    require_true("upload_allowed_after_review", review_manifest.get("upload_allowed_after_review"))
    require_false("github_upload_performed", review_manifest.get("github_upload_performed"))
    require_false("s13_allowed", review_manifest.get("s13_allowed"))
    require_false("lineage_full_check_performed", review_manifest.get("lineage_full_check_performed"))
    require_false("formal_report_generated", review_manifest.get("formal_report_generated"))
    require_false("external_connector_included", review_manifest.get("external_connector_included"))
    require_false("business_decision_basis_allowed", review_manifest.get("business_decision_basis_allowed"))
    require_false("full_trusted_report_allowed", review_manifest.get("full_trusted_report_allowed"))
    require_equal("next_gate_id", review_manifest.get("next_gate_id"), "KMFA-S12-GITHUB-UPLOAD-GATE")
    require_equal("open_review_finding_count", review_manifest.get("open_review_finding_count"), 0)
    require_public_safety("review", review_manifest)

    for phase in ("S12-P1", "S12-P2", "S12-P3"):
        require_phase_status(review_manifest.get("stage_phase_status"), phase)
    require_existing_refs(review_manifest.get("evidence_refs"))

    require_equal("p1.stage_phase", p1_manifest.get("stage_phase"), "S12-P1")
    require_equal("p1.runtime_status", p1_manifest.get("runtime_status"), "public_safe_manual_resolution_events_generated_local_only")
    require_equal("p1.summary.manual_event_count", p1_manifest.get("summary", {}).get("manual_event_count"), 5)
    require_equal("p1.summary.event_type_count", p1_manifest.get("summary", {}).get("event_type_count"), 4)
    require_equal("p1.summary.manual_action_kind_count", p1_manifest.get("summary", {}).get("manual_action_kind_count"), 4)
    require_equal("p1.summary.approved_event_count", p1_manifest.get("summary", {}).get("approved_event_count"), 1)
    require_equal("p1.summary.reverse_event_count", p1_manifest.get("summary", {}).get("reverse_event_count"), 1)
    require_false_flags(
        "p1.quality_gate",
        p1_manifest.get("quality_gate", {}),
        (
            "approved_event_silent_update_allowed",
            "business_decision_basis_allowed",
            "business_plaintext_commit_allowed",
            "derived_rerun_allowed",
            "formal_report_allowed",
            "github_upload_allowed",
            "impact_preview_publish_allowed",
            "phase_completion_upload_allowed",
            "raw_layer_write_allowed",
            "raw_source_mutation_allowed",
            "source_layer_write_allowed",
        ),
    )
    require_false_flags(
        "p1.stage_scope",
        p1_manifest.get("stage_scope", {}),
        (
            "difference_closure_scope_included",
            "external_connector_scope_included",
            "formal_report_runtime_scope_included",
            "github_upload_scope_included",
            "lineage_full_check_scope_included",
            "s12_p2_impact_preview_scope_included",
            "s12_p3_rerun_mechanism_scope_included",
            "stage12_review_scope_included",
        ),
    )
    require_public_safety("p1", p1_manifest)

    require_equal("p2.stage_phase", p2_manifest.get("stage_phase"), "S12-P2")
    require_equal("p2.status", p2_manifest.get("status"), "completed_validated_local_only")
    require_equal("p2.summary.impact_preview_count", p2_manifest.get("summary", {}).get("impact_preview_count"), 5)
    require_equal("p2.summary.source_event_count", p2_manifest.get("summary", {}).get("source_event_count"), 5)
    require_equal("p2.summary.high_risk_count", p2_manifest.get("summary", {}).get("high_risk_count"), 3)
    require_equal("p2.summary.blocked_publish_count", p2_manifest.get("summary", {}).get("blocked_publish_count"), 3)
    require_equal("p2.summary.affected_project_count", p2_manifest.get("summary", {}).get("affected_project_count"), 8)
    require_equal("p2.summary.affected_metric_count", p2_manifest.get("summary", {}).get("affected_metric_count"), 11)
    require_equal("p2.summary.affected_report_count", p2_manifest.get("summary", {}).get("affected_report_count"), 5)
    require_false_flags(
        "p2.quality_gate",
        p2_manifest.get("quality_gate", {}),
        (
            "business_decision_basis_allowed",
            "business_plaintext_commit_allowed",
            "derived_rerun_allowed",
            "derived_rerun_executed",
            "formal_report_allowed",
            "formal_report_generated",
            "github_upload_allowed",
            "phase_completion_upload_allowed",
            "raw_layer_write_allowed",
            "raw_source_mutation_allowed",
            "source_layer_write_allowed",
            "unpassed_preview_publish_allowed",
        ),
    )
    require_false_flags(
        "p2.stage_scope",
        p2_manifest.get("stage_scope", {}),
        (
            "difference_closure_scope_included",
            "external_connector_scope_included",
            "formal_report_runtime_scope_included",
            "github_upload_scope_included",
            "lineage_full_check_scope_included",
            "s12_p3_rerun_mechanism_scope_included",
            "stage12_review_scope_included",
        ),
    )

    require_equal("p3.stage_phase", p3_manifest.get("stage_phase"), "S12-P3")
    require_equal("p3.status", p3_manifest.get("status"), "completed_validated_local_only")
    require_equal("p3.summary.source_event_count", p3_manifest.get("summary", {}).get("source_event_count"), 5)
    require_equal("p3.summary.source_preview_count", p3_manifest.get("summary", {}).get("source_preview_count"), 5)
    require_equal("p3.summary.eligible_event_count", p3_manifest.get("summary", {}).get("eligible_event_count"), 2)
    require_equal("p3.summary.blocked_preview_count", p3_manifest.get("summary", {}).get("blocked_preview_count"), 3)
    require_equal("p3.summary.cache_invalidation_count", p3_manifest.get("summary", {}).get("cache_invalidation_count"), 2)
    require_equal("p3.summary.rerun_chain_layer_count", p3_manifest.get("summary", {}).get("rerun_chain_layer_count"), 4)
    require_equal("p3.summary.rerun_step_count", p3_manifest.get("summary", {}).get("rerun_step_count"), 8)
    require_equal(
        "p3.summary.same_source_consistency_check_count",
        p3_manifest.get("summary", {}).get("same_source_consistency_check_count"),
        2,
    )
    require_false_flags(
        "p3.quality_gate",
        p3_manifest.get("quality_gate", {}),
        (
            "blocked_preview_rerun_allowed",
            "business_decision_basis_allowed",
            "business_plaintext_commit_allowed",
            "formal_report_allowed",
            "formal_report_generated",
            "github_upload_allowed",
            "old_version_overwrite_allowed",
            "phase_completion_upload_allowed",
            "raw_layer_write_allowed",
            "raw_source_mutation_allowed",
            "report_grade_upgrade_allowed",
            "source_layer_write_allowed",
            "stage12_review_allowed",
        ),
    )
    require_false_flags(
        "p3.stage_scope",
        p3_manifest.get("stage_scope", {}),
        (
            "difference_closure_scope_included",
            "external_connector_scope_included",
            "formal_report_runtime_scope_included",
            "github_upload_scope_included",
            "lineage_full_check_scope_included",
            "stage12_review_scope_included",
        ),
    )

    counts = {
        "manual_resolution_event_count": len(events),
        "manual_impact_preview_count": len(previews),
        "eligible_rerun_event_count": int(p3_manifest.get("summary", {}).get("eligible_event_count")),
        "blocked_preview_count": int(p3_manifest.get("summary", {}).get("blocked_preview_count")),
        "cache_invalidation_count": len(invalidations),
        "rerun_step_count": len(rerun_steps),
        "same_source_consistency_check_count": len(consistency_checks),
        "html_export_count": sum(1 for path in (p1_html_path, p2_html_path, p3_html_path) if path.exists()),
    }

    for key, expected in {
        "manual_resolution_event_count": 5,
        "manual_impact_preview_count": 5,
        "eligible_rerun_event_count": 2,
        "blocked_preview_count": 3,
        "cache_invalidation_count": 2,
        "rerun_step_count": 8,
        "same_source_consistency_check_count": 2,
        "html_export_count": 3,
    }.items():
        require_equal(key, counts[key], expected)

    review_counts = review_manifest.get("review_counts")
    if not isinstance(review_counts, dict):
        fail("review_counts: expected object")
    for key, expected in {
        "manual_resolution_event_count": 5,
        "manual_impact_preview_count": 5,
        "high_risk_preview_count": 3,
        "blocked_publish_count": 3,
        "eligible_rerun_event_count": 2,
        "cache_invalidation_count": 2,
        "rerun_step_count": 8,
        "same_source_consistency_check_count": 2,
        "html_export_count": 3,
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "lineage_full_check_count": 0,
        "github_upload_count": 0,
        "s13_scope_count": 0,
        "full_kmfa_unit_tests": 152,
    }.items():
        require_equal(f"review_counts.{key}", review_counts.get(key), expected)
    counts["full_kmfa_unit_tests"] = int(review_counts["full_kmfa_unit_tests"])

    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA Stage 12 review evidence and gates.")
    parser.add_argument("--review-manifest", type=Path, default=DEFAULT_REVIEW_MANIFEST)
    parser.add_argument("--p1-manifest", type=Path, default=DEFAULT_P1_MANIFEST)
    parser.add_argument("--p2-manifest", type=Path, default=DEFAULT_P2_MANIFEST)
    parser.add_argument("--p3-manifest", type=Path, default=DEFAULT_P3_MANIFEST)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--previews", type=Path, default=DEFAULT_PREVIEWS)
    parser.add_argument("--invalidations", type=Path, default=DEFAULT_INVALIDATIONS)
    parser.add_argument("--rerun-steps", type=Path, default=DEFAULT_RERUN_STEPS)
    parser.add_argument("--consistency-checks", type=Path, default=DEFAULT_CONSISTENCY_CHECKS)
    parser.add_argument("--p1-html", type=Path, default=DEFAULT_P1_HTML)
    parser.add_argument("--p2-html", type=Path, default=DEFAULT_P2_HTML)
    parser.add_argument("--p3-html", type=Path, default=DEFAULT_P3_HTML)
    args = parser.parse_args(argv)

    try:
        counts = validate_stage_review(
            args.review_manifest,
            args.p1_manifest,
            args.p2_manifest,
            args.p3_manifest,
            args.events,
            args.previews,
            args.invalidations,
            args.rerun_steps,
            args.consistency_checks,
            args.p1_html,
            args.p2_html,
            args.p3_html,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: KMFA S12 stage review check failed ({exc})", file=sys.stderr)
        return 1

    print(
        "PASS: KMFA S12 stage review check passed "
        f"(manual_events={counts['manual_resolution_event_count']}, "
        f"impact_previews={counts['manual_impact_preview_count']}, "
        f"eligible_reruns={counts['eligible_rerun_event_count']}, "
        f"blocked_previews={counts['blocked_preview_count']}, "
        f"rerun_steps={counts['rerun_step_count']}, "
        f"consistency_checks={counts['same_source_consistency_check_count']}, "
        "upload_allowed_after_review=true, s13_allowed=false, github_upload_status=not_pushed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
