#!/usr/bin/env python3
"""Validate KMFA post-S18 Part 3 review evidence for Stages 7-9."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("KMFA/stage_artifacts/PART3_STAGES_07_09_REVIEW/machine/part3_review_manifest.json")

REQUIRED_STAGE_ARTIFACTS = (
    "KMFA/stage_artifacts/S07_P1_finance_file_adapter/human/s07_p1_completion_record.md",
    "KMFA/stage_artifacts/S07_P1_finance_file_adapter/human/test_results.md",
    "KMFA/stage_artifacts/S07_P1_finance_file_adapter/machine/finance_readonly_field_report.jsonl",
    "KMFA/stage_artifacts/S07_P1_finance_file_adapter/machine/s07_p1_manifest.json",
    "KMFA/stage_artifacts/S07_P2_wps_file_adapter/human/s07_p2_completion_record.md",
    "KMFA/stage_artifacts/S07_P2_wps_file_adapter/human/test_results.md",
    "KMFA/stage_artifacts/S07_P2_wps_file_adapter/machine/s07_p2_manifest.json",
    "KMFA/stage_artifacts/S07_P2_wps_file_adapter/machine/wps_conversion_guidance.jsonl",
    "KMFA/stage_artifacts/S07_P2_wps_file_adapter/machine/wps_readonly_field_report.jsonl",
    "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/s07_p3_completion_record.md",
    "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/test_results.md",
    "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/redcircle_connector_postponement_policy.json",
    "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/redcircle_future_rollback_plan.jsonl",
    "KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/s07_p3_manifest.json",
    "KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S07_STAGE_REVIEW/human/stage7_review_report.md",
    "KMFA/stage_artifacts/S07_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_review_manifest.json",
    "KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json",
    "KMFA/stage_artifacts/S08_P1_project_composite_key/human/s08_p1_completion_record.md",
    "KMFA/stage_artifacts/S08_P1_project_composite_key/human/test_results.md",
    "KMFA/stage_artifacts/S08_P1_project_composite_key/machine/s08_p1_manifest.json",
    "KMFA/stage_artifacts/S08_P2_business_entity_model/human/s08_p2_completion_record.md",
    "KMFA/stage_artifacts/S08_P2_business_entity_model/human/test_results.md",
    "KMFA/stage_artifacts/S08_P2_business_entity_model/machine/s08_p2_manifest.json",
    "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/entity_matching_report.md",
    "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/s08_p3_completion_record.md",
    "KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/test_results.md",
    "KMFA/stage_artifacts/S08_P3_entity_matching_quality/machine/entity_matching_report.json",
    "KMFA/stage_artifacts/S08_P3_entity_matching_quality/machine/s08_p3_manifest.json",
    "KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S08_STAGE_REVIEW/human/stage8_review_report.md",
    "KMFA/stage_artifacts/S08_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_review_manifest.json",
    "KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json",
    "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/s09_p1_completion_record.md",
    "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/test_results.md",
    "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/machine/s09_p1_manifest.json",
    "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/s09_p2_completion_record.md",
    "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/test_results.md",
    "KMFA/stage_artifacts/S09_P2_margin_cash_margin/machine/s09_p2_manifest.json",
    "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/s09_p3_completion_record.md",
    "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/test_results.md",
    "KMFA/stage_artifacts/S09_P3_scope_reconciliation/machine/s09_p3_manifest.json",
    "KMFA/stage_artifacts/S09_STAGE_REVIEW/human/github_upload_record.md",
    "KMFA/stage_artifacts/S09_STAGE_REVIEW/human/stage9_review_report.md",
    "KMFA/stage_artifacts/S09_STAGE_REVIEW/human/test_results.md",
    "KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_review_manifest.json",
    "KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_upload_manifest.json",
)

REQUIRED_BASELINE_REFS = (
    "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md",
    "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md",
    "KMFA/tools/finance_file_adapter.py",
    "KMFA/tools/check_s07_p1_finance_file_adapter.py",
    "KMFA/tests/test_finance_file_adapter.py",
    "KMFA/tools/wps_file_adapter.py",
    "KMFA/tools/check_s07_p2_wps_file_adapter.py",
    "KMFA/tests/test_wps_file_adapter.py",
    "KMFA/tools/redcircle_postponement_policy.py",
    "KMFA/tools/check_s07_p3_redcircle_postponement.py",
    "KMFA/tests/test_redcircle_postponement_policy.py",
    "KMFA/metadata/imports/finance_support_source_registry.json",
    "KMFA/metadata/schema_maps/finance_file_adapter_manifest.json",
    "KMFA/metadata/schema_maps/finance_field_candidates.jsonl",
    "KMFA/metadata/schema_maps/finance_file_mapping_policy.yaml",
    "KMFA/metadata/imports/wps_export_source_registry.json",
    "KMFA/metadata/schema_maps/wps_file_adapter_manifest.json",
    "KMFA/metadata/schema_maps/wps_field_mappings.jsonl",
    "KMFA/metadata/schema_maps/wps_mapping_rule_versions.json",
    "KMFA/metadata/schema_maps/wps_file_mapping_policy.yaml",
    "KMFA/metadata/imports/redcircle_export_source_registry.json",
    "KMFA/metadata/schema_maps/redcircle_postponement_manifest.json",
    "KMFA/metadata/schema_maps/redcircle_reserved_export_templates.jsonl",
    "KMFA/metadata/schema_maps/redcircle_postponement_policy.yaml",
    "KMFA/tools/project_composite_key.py",
    "KMFA/tools/check_s08_p1_project_composite_key.py",
    "KMFA/tests/test_project_composite_key.py",
    "KMFA/tools/business_entity_model.py",
    "KMFA/tools/check_s08_p2_business_entity_model.py",
    "KMFA/tests/test_business_entity_model.py",
    "KMFA/tools/entity_matching_quality.py",
    "KMFA/tools/check_s08_p3_entity_matching_quality.py",
    "KMFA/tests/test_entity_matching_quality.py",
    "KMFA/metadata/schema_maps/project_composite_key_manifest.json",
    "KMFA/metadata/schema_maps/project_identity_profiles.jsonl",
    "KMFA/metadata/schema_maps/project_composite_key_matches.jsonl",
    "KMFA/metadata/quality/project_identity_review_queue.jsonl",
    "KMFA/metadata/schema_maps/business_entity_model_manifest.json",
    "KMFA/metadata/schema_maps/business_entity_model_schema.json",
    "KMFA/metadata/schema_maps/business_entity_relationships.jsonl",
    "KMFA/metadata/schema_maps/business_entity_lifecycle_statuses.jsonl",
    "KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md",
    "KMFA/metadata/quality/entity_matching_quality_manifest.json",
    "KMFA/metadata/quality/entity_matching_quality_cases.jsonl",
    "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
    "KMFA/tools/project_cost_fact_layer.py",
    "KMFA/tools/check_s09_p1_project_cost_fact_layer.py",
    "KMFA/tests/test_project_cost_fact_layer.py",
    "KMFA/tools/project_margin_cash_margin.py",
    "KMFA/tools/check_s09_p2_margin_cash_margin.py",
    "KMFA/tests/test_project_margin_cash_margin.py",
    "KMFA/tools/project_scope_reconciliation.py",
    "KMFA/tools/check_s09_p3_scope_reconciliation.py",
    "KMFA/tests/test_project_scope_reconciliation.py",
    "KMFA/tools/check_s09_stage_review.py",
    "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
    "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
    "KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl",
    "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
    "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
    "KMFA/metadata/quality/scope_difference_summary.jsonl",
    "KMFA/metadata/reports/project_scope_reconciliation_manifest.json",
    "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
    "KMFA/metadata/quality/scope_reconciliation_domain_controls.jsonl",
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


def validate_part3_review(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, int]:
    manifest = _read_json(manifest_path)

    _require_equal("schema_version", manifest.get("schema_version"), "kmfa.part_review_manifest.v1")
    _require_equal("project_id", manifest.get("project_id"), "KMFA")
    _require_equal("part_id", manifest.get("part_id"), "PART3_STAGES_07_09")
    _require_equal("review_id", manifest.get("review_id"), "KMFA-PART3-STAGES-07-09-REVIEW-20260702")
    _require_equal("status", manifest.get("status"), "part_review_passed_local_only")
    _require_equal("stages", manifest.get("stages"), ["S07", "S08", "S09"])
    _require_equal("next_part_id", manifest.get("next_part_id"), "PART4_STAGES_10_12")
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
    _require_equal("review_counts.part3_unit_tests", counts.get("part3_unit_tests"), 32)
    _require_equal("review_counts.full_kmfa_unit_tests", counts.get("full_kmfa_unit_tests"), 271)
    _require_equal("review_counts.s07_finance_field_candidates", counts.get("s07_finance_field_candidates"), 45)
    _require_equal("review_counts.s07_wps_field_mappings", counts.get("s07_wps_field_mappings"), 20)
    _require_equal("review_counts.s07_redcircle_reserved_templates", counts.get("s07_redcircle_reserved_templates"), 4)
    _require_equal("review_counts.s08_project_identity_components", counts.get("s08_project_identity_components"), 8)
    _require_equal("review_counts.s08_business_entity_types", counts.get("s08_business_entity_types"), 8)
    _require_equal("review_counts.s08_entity_matching_quality_cases", counts.get("s08_entity_matching_quality_cases"), 4)
    _require_equal("review_counts.s09_project_cost_fact_records", counts.get("s09_project_cost_fact_records"), 4)
    _require_equal("review_counts.s09_project_margin_records", counts.get("s09_project_margin_records"), 4)
    _require_equal("review_counts.s09_scope_reconciliation_records", counts.get("s09_scope_reconciliation_records"), 12)
    _require_equal("review_counts.s09_pending_reconciliation_records", counts.get("s09_pending_reconciliation_records"), 12)

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
        _fail("missing required Part 3 paths: " + ", ".join(missing))

    s07p1 = _read_json(Path("KMFA/stage_artifacts/S07_P1_finance_file_adapter/machine/s07_p1_manifest.json"))
    s07p2 = _read_json(Path("KMFA/stage_artifacts/S07_P2_wps_file_adapter/machine/s07_p2_manifest.json"))
    s07p3 = _read_json(Path("KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/machine/s07_p3_manifest.json"))
    s07_review = _read_json(Path("KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_review_manifest.json"))
    s07_upload = _read_json(Path("KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json"))
    s08p1 = _read_json(Path("KMFA/stage_artifacts/S08_P1_project_composite_key/machine/s08_p1_manifest.json"))
    s08p2 = _read_json(Path("KMFA/stage_artifacts/S08_P2_business_entity_model/machine/s08_p2_manifest.json"))
    s08p3 = _read_json(Path("KMFA/stage_artifacts/S08_P3_entity_matching_quality/machine/s08_p3_manifest.json"))
    s08_review = _read_json(Path("KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_review_manifest.json"))
    s08_upload = _read_json(Path("KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json"))
    s09p1 = _read_json(Path("KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/machine/s09_p1_manifest.json"))
    s09p2 = _read_json(Path("KMFA/stage_artifacts/S09_P2_margin_cash_margin/machine/s09_p2_manifest.json"))
    s09p3 = _read_json(Path("KMFA/stage_artifacts/S09_P3_scope_reconciliation/machine/s09_p3_manifest.json"))
    s09_review = _read_json(Path("KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_review_manifest.json"))
    s09_upload = _read_json(Path("KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_upload_manifest.json"))
    scope_records = _read_jsonl(Path("KMFA/metadata/quality/scope_reconciliation_records.jsonl"))

    _require_equal("s07p1.stage_phase", s07p1.get("stage_phase"), "S07-P1")
    _require_equal("s07p1.validation_status", s07p1.get("validation_status"), "phase_validator_passed_local_only")
    _require_equal("s07p1.summary.source_category_count", s07p1.get("summary", {}).get("source_category_count"), 9)
    _require_equal("s07p1.summary.field_candidate_count", s07p1.get("summary", {}).get("field_candidate_count"), 45)
    _require_equal("s07p1.summary.field_report_count", s07p1.get("summary", {}).get("field_report_count"), 9)
    _require_false("s07p1.stage_scope.wps_scope_included", s07p1.get("stage_scope", {}).get("wps_scope_included"))
    _require_false("s07p1.stage_scope.redcircle_scope_included", s07p1.get("stage_scope", {}).get("redcircle_scope_included"))
    _require_false_flags("s07p1.public_repo_safety", s07p1.get("public_repo_safety", {}))
    _require_equal("s07p2.stage_phase", s07p2.get("stage_phase"), "S07-P2")
    _require_equal("s07p2.wps_export_type_count", s07p2.get("wps_export_type_count"), 4)
    _require_equal("s07p2.field_mapping_count", s07p2.get("field_mapping_count"), 20)
    _require_equal("s07p2.field_report_count", s07p2.get("field_report_count"), 4)
    _require_false("s07p2.finance_scope_included", s07p2.get("finance_scope_included"))
    _require_false("s07p2.redcircle_scope_included", s07p2.get("redcircle_scope_included"))
    _require_false_flags("s07p2.public_repo_safety", s07p2.get("public_repo_safety", {}))
    _require_equal("s07p3.stage_phase", s07p3.get("stage_phase"), "S07-P3")
    _require_equal("s07p3.summary.reserved_template_count", s07p3.get("summary", {}).get("reserved_template_count"), 4)
    _require_equal("s07p3.summary.rollback_plan_count", s07p3.get("summary", {}).get("rollback_plan_count"), 4)
    _require_false("s07p3.mvp_scope.d15_file_mvp_automatic_connector_allowed", s07p3.get("mvp_scope", {}).get("d15_file_mvp_automatic_connector_allowed"))
    _require_true("s07p3.future_required_controls.read_only_required", s07p3.get("future_required_controls", {}).get("read_only_required"))
    _require_true("s07p3.future_required_controls.hash_retention_required", s07p3.get("future_required_controls", {}).get("hash_retention_required"))
    _require_false_flags("s07p3.public_repo_safety", s07p3.get("public_repo_safety", {}))
    _require_equal("s07_review.stage", s07_review.get("stage"), "S07")
    _require_equal("s07_review.status", s07_review.get("status"), "pass_upload_ready_local_only")
    _require_false("s07_review.upload_performed", s07_review.get("upload_performed"))
    _require_equal("s07_upload.status", s07_upload.get("status"), "uploaded_to_github_main")

    _require_equal("s08p1.stage_phase", s08p1.get("stage_phase"), "S08-P1")
    _require_equal("s08p1.required_component_count", s08p1.get("required_component_count"), 8)
    _require_equal("s08p1.profile_count", s08p1.get("profile_count"), 4)
    _require_equal("s08p1.match_result_count", s08p1.get("match_result_count"), 3)
    _require_equal("s08p1.manual_review_queue_count", s08p1.get("manual_review_queue_count"), 2)
    _require_false_flags("s08p1.public_repo_safety", s08p1.get("public_repo_safety", {}))
    _require_equal("s08p2.stage_phase", s08p2.get("stage_phase"), "S08-P2")
    _require_equal("s08p2.required_entity_type_count", s08p2.get("required_entity_type_count"), 8)
    _require_equal("s08p2.relationship_count", s08p2.get("relationship_count"), 14)
    _require_equal("s08p2.lifecycle_status_count", s08p2.get("lifecycle_status_count"), 32)
    _require_false("s08p2.fact_layer_scope_included", s08p2.get("fact_layer_scope_included"))
    _require_false_flags("s08p2.public_repo_safety", s08p2.get("public_repo_safety", {}))
    _require_equal("s08p3.stage_phase", s08p3.get("stage_phase"), "S08-P3")
    _require_equal("s08p3.scenario_count", s08p3.get("scenario_count"), 4)
    _require_equal("s08p3.quality_case_count", s08p3.get("quality_case_count"), 4)
    _require_equal("s08p3.manual_review_queue_count", s08p3.get("manual_review_queue_count"), 3)
    _require_equal("s08p3.entity_matching_report_count", s08p3.get("entity_matching_report_count"), 1)
    _require_false_flags("s08p3.public_repo_safety", s08p3.get("public_repo_safety", {}))
    _require_equal("s08_review.stage", s08_review.get("stage"), "S08")
    _require_equal("s08_review.status", s08_review.get("status"), "pass_upload_ready_local_only")
    _require_false("s08_review.upload_performed", s08_review.get("upload_performed"))
    _require_equal("s08_upload.status", s08_upload.get("status"), "uploaded_to_github_main")

    _require_equal("s09p1.stage_phase", s09p1.get("stage_phase"), "S09-P1")
    _require_equal("s09p1.required_metric_count", s09p1.get("required_metric_count"), 6)
    _require_equal("s09p1.fact_record_count", s09p1.get("fact_record_count"), 4)
    _require_equal("s09p1.cost_category_count", s09p1.get("cost_category_count"), 9)
    _require_equal("s09p1.unallocated_pool_count", s09p1.get("unallocated_pool_count"), 9)
    _require_equal("s09p1.unresolved_difference_count", s09p1.get("unresolved_difference_count"), 1)
    _require_false_flags("s09p1.public_repo_safety", s09p1.get("public_repo_safety", {}))
    _require_equal("s09p2.stage_phase", s09p2.get("stage_phase"), "S09-P2")
    _require_equal("s09p2.margin_record_count", s09p2.get("margin_record_count"), 4)
    _require_equal("s09p2.difference_summary_count", s09p2.get("difference_summary_count"), 12)
    _require_equal("s09p2.upstream_manual_review_queue_count", s09p2.get("upstream_manual_review_queue_count"), 3)
    _require_false_flags("s09p2.public_repo_safety", s09p2.get("public_repo_safety", {}))
    _require_equal("s09p3.stage_phase", s09p3.get("stage_phase"), "S09-P3")
    _require_equal("s09p3.reconciliation_record_count", s09p3.get("reconciliation_record_count"), 12)
    _require_equal("s09p3.domain_control_count", s09p3.get("domain_control_count"), 6)
    _require_equal("s09p3.confirmed_resolution_count", s09p3.get("confirmed_resolution_count"), 0)
    _require_equal("s09p3.pending_resolution_count", s09p3.get("pending_resolution_count"), 12)
    _require_false("s09p3.derived_metric_rerun_allowed", s09p3.get("derived_metric_rerun_allowed"))
    _require_false("s09p3.formal_report_allowed", s09p3.get("formal_report_allowed"))
    _require_false("s09p3.github_upload_allowed", s09p3.get("github_upload_allowed"))
    _require_equal("s09_review.stage", s09_review.get("stage"), "S09")
    _require_equal("s09_review.status", s09_review.get("status"), "pass_upload_ready_local_only")
    _require_false("s09_review.upload_performed", s09_review.get("upload_performed"))
    _require_equal("s09_review.review_counts.scope_reconciliation_records", s09_review.get("review_counts", {}).get("scope_reconciliation_records"), 12)
    _require_equal("s09_review.review_counts.pending_owner_or_authorized_review_records", s09_review.get("review_counts", {}).get("pending_owner_or_authorized_review_records"), 12)
    _require_equal("s09_upload.status", s09_upload.get("status"), "uploaded_to_github_main")
    _require_equal("scope_reconciliation_record_count", len(scope_records), 12)

    return {
        "stage_count": counts["stage_count"],
        "phase_count": counts["phase_count"],
        "required_stage_artifact_count": counts["required_stage_artifact_count"],
        "required_baseline_ref_count": counts["required_baseline_ref_count"],
        "part3_unit_tests": counts["part3_unit_tests"],
        "full_kmfa_unit_tests": counts["full_kmfa_unit_tests"],
        "open_review_finding_count": manifest["open_review_finding_count"],
        "github_upload_count": 1 if manifest["github_upload_performed"] else 0,
    }


def main() -> int:
    try:
        counts = validate_part3_review()
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"FAIL: KMFA Part 3 Stage 7-9 review check failed: {exc}", file=sys.stderr)
        return 1
    print(
        "PASS: KMFA Part 3 Stage 7-9 review check passed "
        f"(stages={counts['stage_count']}, phases={counts['phase_count']}, "
        f"stage_artifacts={counts['required_stage_artifact_count']}, "
        f"baseline_refs={counts['required_baseline_ref_count']}, "
        f"part3_tests={counts['part3_unit_tests']}, "
        f"full_tests={counts['full_kmfa_unit_tests']}, "
        f"github_upload={counts['github_upload_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
