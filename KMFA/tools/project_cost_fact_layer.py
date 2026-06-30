#!/usr/bin/env python3
"""Build KMFA S09-P1 public-safe project cost fact layer metadata.

S09-P1 establishes the structural fact layer for project revenue, contract
amount, invoice, collection, total cost, and cost category slots. It does not
perform gross margin, cash gross margin, scope reconciliation, formal report
generation, UI, external connector, Stage 9 review, or GitHub upload work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_AUTHORITY_MANIFEST = ROOT / "metadata" / "baseline" / "a0_authority_baseline_manifest.json"
DEFAULT_AUTHORITY_RECORDS = ROOT / "metadata" / "baseline" / "a0_authority_baseline_records.jsonl"
DEFAULT_PROJECT_PROFILES = ROOT / "metadata" / "schema_maps" / "project_identity_profiles.jsonl"
DEFAULT_ENTITY_SCHEMA = ROOT / "metadata" / "schema_maps" / "business_entity_model_schema.json"
DEFAULT_ZERO_DELTA_RESULTS = ROOT / "metadata" / "quality" / "zero_delta_results.jsonl"
DEFAULT_DATA_QUALITY_RESULTS = ROOT / "metadata" / "quality" / "data_quality_results.jsonl"
DEFAULT_SOURCE_DIFFERENCE_QUEUE = ROOT / "metadata" / "quality" / "source_difference_queue.jsonl"
DEFAULT_ENTITY_MATCHING_REVIEW_QUEUE = ROOT / "metadata" / "quality" / "entity_matching_review_queue.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "project_cost_fact_layer_manifest.json"
DEFAULT_OUTPUT_FACT_RECORDS = ROOT / "metadata" / "lineage" / "project_cost_fact_records.jsonl"
DEFAULT_OUTPUT_UNALLOCATED_POOL = ROOT / "metadata" / "lineage" / "unallocated_project_cost_pool.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S09_P1_project_cost_fact_layer" / "machine" / "s09_p1_manifest.json"
)

REQUIRED_FACT_METRICS = (
    "revenue",
    "contract_amount",
    "invoice_amount",
    "collection_amount",
    "cost_total",
    "cost_category",
)

REQUIRED_COST_CATEGORIES = (
    "labor",
    "material",
    "machinery",
    "subcontract",
    "transport",
    "travel",
    "tax",
    "management_fee",
    "interest",
)

FORBIDDEN_PUBLIC_KEYS = {
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "raw_file_bytes",
    "original_filename",
    "private_csv",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "password",
    "token",
    "api_key",
    "private_key",
}

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db")
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


class ProjectCostFactLayerError(ValueError):
    """Raised when S09-P1 project cost fact layer artifacts are invalid."""


def require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ProjectCostFactLayerError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ProjectCostFactLayerError(f"{field_name} is required")
    return text


def _sha256_for(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_values_committed": False,
        "normalized_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ProjectCostFactLayerError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ProjectCostFactLayerError(f"{path} contains a non-object JSONL record")
            records.append(value)
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    return _read_json(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return _read_jsonl(path)


def _authority_summary(authority_records: list[dict[str, Any]]) -> dict[str, Any]:
    locked = [item for item in authority_records if item.get("lock_status") == "q5_locked_public_safe_hash_baseline"]
    excluded = [item for item in authority_records if item.get("lock_status") == "excluded_cross_source_support_only"]
    locked_fields = sorted({str(item.get("field_key")) for item in locked if item.get("field_key")})
    return {
        "locked_field_count": len(locked),
        "excluded_cross_source_support_count": len(excluded),
        "locked_field_keys": locked_fields,
        "required_s09_field_support_present": {
            "contract_amount": "contract_amount" in locked_fields,
            "cost_total": "total_expense" in locked_fields,
            "cost_category": "cost_category" in locked_fields,
        },
        "authority_baseline_ref": "KMFA/metadata/baseline/a0_authority_baseline_manifest.json",
        "authority_records_ref": "KMFA/metadata/baseline/a0_authority_baseline_records.jsonl",
    }


def _upstream_quality_summary(
    zero_delta_results: list[dict[str, Any]],
    data_quality_results: list[dict[str, Any]],
    source_difference_queue: list[dict[str, Any]],
    entity_matching_review_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    zero_delta_fail_count = sum(
        1
        for item in zero_delta_results
        if item.get("record_type") == "zero_delta_result"
        and (item.get("zero_delta_passed") is False or item.get("status") == "failed")
    )
    unresolved_difference_count = sum(
        1
        for item in source_difference_queue
        if item.get("record_type") == "source_difference_queue_item"
        and item.get("status") not in {"resolved", "closed", "cancelled"}
    )
    blocked_quality_result_count = sum(
        1
        for item in data_quality_results
        if item.get("record_type") == "data_quality_result" and item.get("validation_status") == "blocked"
    )
    manual_review_queue_count = sum(
        1
        for item in entity_matching_review_queue
        if item.get("record_type") == "entity_matching_quality_review_queue_item"
        and item.get("status") != "closed"
    )
    return {
        "zero_delta_fail_count": zero_delta_fail_count,
        "blocked_quality_result_count": blocked_quality_result_count,
        "unresolved_difference_count": unresolved_difference_count,
        "manual_review_queue_count": manual_review_queue_count,
        "formal_calculation_blocked": any(
            count > 0
            for count in (
                zero_delta_fail_count,
                unresolved_difference_count,
                blocked_quality_result_count,
                manual_review_queue_count,
            )
        ),
        "zero_delta_results_ref": "KMFA/metadata/quality/zero_delta_results.jsonl",
        "data_quality_results_ref": "KMFA/metadata/quality/data_quality_results.jsonl",
        "source_difference_queue_ref": "KMFA/metadata/quality/source_difference_queue.jsonl",
        "entity_matching_review_queue_ref": "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
    }


def _metric_private_refs(fact_record_id: str) -> dict[str, str]:
    return {metric: f"private_ref://KMFA/S09-P1/{fact_record_id}/{metric}" for metric in REQUIRED_FACT_METRICS}


def _metric_hash_refs(fact_record_id: str) -> dict[str, str]:
    return {metric: _sha256_for(f"S09-P1:{fact_record_id}:{metric}:value-ref") for metric in REQUIRED_FACT_METRICS}


def _cost_category_private_refs(fact_record_id: str) -> dict[str, str]:
    return {category: f"private_ref://KMFA/S09-P1/{fact_record_id}/cost-category/{category}" for category in REQUIRED_COST_CATEGORIES}


def _cost_category_hash_refs(fact_record_id: str) -> dict[str, str]:
    return {
        category: _sha256_for(f"S09-P1:{fact_record_id}:cost-category:{category}")
        for category in REQUIRED_COST_CATEGORIES
    }


def _profile_ref(profile: dict[str, Any], index: int) -> str:
    profile_id = require_text(profile.get("profile_id", f"profile-{index}"), "profile_id")
    return f"KMFA/metadata/schema_maps/project_identity_profiles.jsonl#{profile_id}"


def _build_fact_records(
    project_profiles: list[dict[str, Any]], upstream_quality: dict[str, Any]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, profile in enumerate(project_profiles, start=1):
        fact_record_id = f"PCF-S09P1-{index:03d}"
        profile_ref = _profile_ref(profile, index)
        records.append(
            {
                "schema_version": "kmfa.project_cost_fact_record.v1",
                "record_type": "project_cost_fact_record",
                "project_id": "KMFA",
                "stage_phase": "S09-P1",
                "fact_record_id": fact_record_id,
                "project_identity_profile_ref": profile_ref,
                "project_entity_ref": f"entity_ref://KMFA/S08-P2/project/{index:03d}",
                "authority_baseline_ref": "KMFA/metadata/baseline/a0_authority_baseline_manifest.json",
                "business_entity_schema_ref": "KMFA/metadata/schema_maps/business_entity_model_schema.json",
                "quality_gate_ref": "KMFA/metadata/quality/data_quality_results.jsonl",
                "source_hash": _sha256_for(f"S09-P1:{fact_record_id}:{profile_ref}"),
                "source_refs": [
                    "source_ref://KMFA/S05/A0-authority-baseline",
                    "source_ref://KMFA/S06/zero-delta-and-difference-queue",
                    "source_ref://KMFA/S08/project-identity-and-entity-model",
                ],
                "metric_slots": list(REQUIRED_FACT_METRICS),
                "metric_private_refs": _metric_private_refs(fact_record_id),
                "metric_hash_refs": _metric_hash_refs(fact_record_id),
                "cost_category_slots": list(REQUIRED_COST_CATEGORIES),
                "cost_category_private_refs": _cost_category_private_refs(fact_record_id),
                "cost_category_hash_refs": _cost_category_hash_refs(fact_record_id),
                "metric_values_public_committed": False,
                "amount_calculation_performed": False,
                "formal_calculation_allowed": False,
                "calculation_status": "blocked_pending_quality_resolution"
                if upstream_quality["formal_calculation_blocked"]
                else "structural_ready_pending_s09_p2",
                "unallocated_cost_pool_ref": "KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl",
                "raw_layer_write_allowed": False,
                "evidence_ref": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/test_results.md",
                "public_repo_safety": _public_repo_safety(),
            }
        )
    return records


def _build_unallocated_pool(upstream_quality: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "kmfa.unallocated_project_cost_pool.v1",
            "record_type": "unallocated_project_cost_pool_item",
            "project_id": "KMFA",
            "stage_phase": "S09-P1",
            "pool_id": f"UPC-S09P1-{index:03d}",
            "pool_type": "unallocated_project_cost_pool",
            "cost_category": category,
            "cost_category_ref": f"cost_category_ref://KMFA/S09-P1/{category}",
            "cost_category_hash": _sha256_for(f"S09-P1:unallocated-cost-category:{category}"),
            "amount_value_private_ref": f"private_ref://KMFA/S09-P1/unallocated-cost/{category}",
            "amount_value_hash_ref": _sha256_for(f"S09-P1:unallocated-cost:{category}:value-ref"),
            "amount_value_public_committed": False,
            "assignment_status": "pending_project_assignment_or_quality_resolution",
            "blocking_reason_refs": [
                "KMFA/metadata/quality/source_difference_queue.jsonl",
                "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
            ],
            "source_difference_queue_ref": upstream_quality["source_difference_queue_ref"],
            "entity_matching_review_queue_ref": upstream_quality["entity_matching_review_queue_ref"],
            "raw_layer_write_allowed": False,
            "evidence_ref": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/test_results.md",
            "public_repo_safety": _public_repo_safety(),
        }
        for index, category in enumerate(REQUIRED_COST_CATEGORIES, start=1)
    ]


def build_default_project_cost_fact_layer(
    *, generated_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_at_value = require_text(generated_at, "generated_at")
    authority_manifest = _read_json(DEFAULT_AUTHORITY_MANIFEST)
    authority_records = _read_jsonl(DEFAULT_AUTHORITY_RECORDS)
    project_profiles = _read_jsonl(DEFAULT_PROJECT_PROFILES)
    entity_schema = _read_json(DEFAULT_ENTITY_SCHEMA)
    zero_delta_results = _read_jsonl(DEFAULT_ZERO_DELTA_RESULTS)
    data_quality_results = _read_jsonl(DEFAULT_DATA_QUALITY_RESULTS)
    source_difference_queue = _read_jsonl(DEFAULT_SOURCE_DIFFERENCE_QUEUE)
    entity_matching_review_queue = _read_jsonl(DEFAULT_ENTITY_MATCHING_REVIEW_QUEUE)

    authority_summary = _authority_summary(authority_records)
    upstream_quality = _upstream_quality_summary(
        zero_delta_results, data_quality_results, source_difference_queue, entity_matching_review_queue
    )
    fact_records = _build_fact_records(project_profiles, upstream_quality)
    unallocated_pool = _build_unallocated_pool(upstream_quality)

    manifest = {
        "schema_version": "kmfa.project_cost_fact_layer_manifest.v1",
        "record_type": "project_cost_fact_layer_manifest",
        "project_id": "KMFA",
        "stage_phase": "S09-P1",
        "generated_at": generated_at_value,
        "formula_version": "FORM-KMFA-PROJECT-COST-FACT-LAYER-001",
        "mapping_version": "MAP-KMFA-S09P1-PUBLIC-SAFE-v1",
        "fact_layer_status": "structural_fact_layer_blocked_for_formal_calculation"
        if upstream_quality["formal_calculation_blocked"]
        else "structural_fact_layer_ready_for_s09_p2",
        "required_fact_metrics": list(REQUIRED_FACT_METRICS),
        "required_cost_categories": list(REQUIRED_COST_CATEGORIES),
        "summary": {
            "required_metric_count": len(REQUIRED_FACT_METRICS),
            "cost_category_count": len(REQUIRED_COST_CATEGORIES),
            "project_identity_profile_count": len(project_profiles),
            "fact_record_count": len(fact_records),
            "unallocated_pool_count": len(unallocated_pool),
            "authority_locked_field_count": authority_summary["locked_field_count"],
            "authority_excluded_field_count": authority_summary["excluded_cross_source_support_count"],
            "business_entity_type_count": len(entity_schema.get("entity_definitions", [])),
        },
        "authority_baseline_summary": authority_summary,
        "upstream_authority_manifest_ref": "KMFA/metadata/baseline/a0_authority_baseline_manifest.json",
        "upstream_authority_record_type": authority_manifest.get("record_type"),
        "upstream_quality_summary": upstream_quality,
        "stage_scope": {
            "s09_p1_project_cost_fact_layer_scope_included": True,
            "s09_p2_margin_calculation_scope_included": False,
            "s09_p3_scope_difference_reconciliation_scope_included": False,
            "stage9_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "formal_report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
        },
        "quality_gate": {
            "formal_report_allowed": False,
            "github_upload_allowed": False,
            "phase_completion_upload_allowed": False,
            "s09_p2_margin_calculation_allowed": False,
            "s09_p3_scope_difference_reconciliation_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "artifact_refs": {
            "fact_layer_manifest": "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
            "fact_records": "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
            "unallocated_project_cost_pool": "KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl",
            "stage_manifest": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/machine/s09_p1_manifest.json",
            "completion_record": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/s09_p1_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/test_results.md",
            "validator": "KMFA/tools/check_s09_p1_project_cost_fact_layer.py",
        },
        "public_repo_safety": _public_repo_safety(),
    }
    validate_project_cost_fact_layer_artifacts(manifest, fact_records, unallocated_pool)
    return manifest, fact_records, unallocated_pool


def _walk_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(_walk_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_forbidden_keys(child, f"{path}[{index}]"))
    return hits


def _walk_forbidden_suffixes(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            hits.extend(_walk_forbidden_suffixes(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_forbidden_suffixes(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value.lower().endswith(FORBIDDEN_PUBLIC_SUFFIXES):
        hits.append(path)
    return hits


def _require_false(container: dict[str, Any], path: str) -> None:
    for key, value in container.items():
        if value is not False:
            raise ProjectCostFactLayerError(f"{path}.{key} must be false")


def _require_hash(value: Any, path: str) -> None:
    if not isinstance(value, str) or not HASH_RE.match(value):
        raise ProjectCostFactLayerError(f"{path} must be sha256")


def _validate_private_ref_map(refs: dict[str, Any], expected_keys: tuple[str, ...], path: str) -> None:
    if set(refs) != set(expected_keys):
        raise ProjectCostFactLayerError(f"{path} keys mismatch")
    for key, value in refs.items():
        if not isinstance(value, str) or not value.startswith("private_ref://"):
            raise ProjectCostFactLayerError(f"{path}.{key} must be private_ref")


def _validate_hash_ref_map(refs: dict[str, Any], expected_keys: tuple[str, ...], path: str) -> None:
    if set(refs) != set(expected_keys):
        raise ProjectCostFactLayerError(f"{path} keys mismatch")
    for key, value in refs.items():
        _require_hash(value, f"{path}.{key}")


def validate_project_cost_fact_layer_artifacts(
    manifest: dict[str, Any],
    fact_records: list[dict[str, Any]],
    unallocated_pool: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.project_cost_fact_layer_manifest.v1":
        raise ProjectCostFactLayerError("invalid S09-P1 manifest schema_version")
    if manifest.get("stage_phase") != "S09-P1":
        raise ProjectCostFactLayerError("S09-P1 manifest stage_phase mismatch")
    if tuple(manifest.get("required_fact_metrics", [])) != REQUIRED_FACT_METRICS:
        raise ProjectCostFactLayerError("S09-P1 required fact metrics mismatch")
    if tuple(manifest.get("required_cost_categories", [])) != REQUIRED_COST_CATEGORIES:
        raise ProjectCostFactLayerError("S09-P1 required cost categories mismatch")

    summary = manifest.get("summary", {})
    if summary.get("required_metric_count") != len(REQUIRED_FACT_METRICS):
        raise ProjectCostFactLayerError("S09-P1 required metric count mismatch")
    if summary.get("cost_category_count") != len(REQUIRED_COST_CATEGORIES):
        raise ProjectCostFactLayerError("S09-P1 cost category count mismatch")
    if summary.get("fact_record_count") != len(fact_records):
        raise ProjectCostFactLayerError("S09-P1 fact record count mismatch")
    if summary.get("unallocated_pool_count") != len(unallocated_pool):
        raise ProjectCostFactLayerError("S09-P1 unallocated pool count mismatch")
    if summary.get("unallocated_pool_count", 0) < len(REQUIRED_COST_CATEGORIES):
        raise ProjectCostFactLayerError("S09-P1 must queue each required cost category in unallocated pool")

    stage_scope = manifest.get("stage_scope", {})
    if stage_scope.get("s09_p1_project_cost_fact_layer_scope_included") is not True:
        raise ProjectCostFactLayerError("S09-P1 scope must be included")
    for excluded_scope in (
        "s09_p2_margin_calculation_scope_included",
        "s09_p3_scope_difference_reconciliation_scope_included",
        "stage9_review_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_scope_included",
        "ui_scope_included",
        "external_connector_scope_included",
    ):
        if stage_scope.get(excluded_scope) is not False:
            raise ProjectCostFactLayerError(f"S09-P1 must exclude {excluded_scope}")

    _require_false(manifest.get("quality_gate", {}), "manifest.quality_gate")
    _require_false(manifest.get("public_repo_safety", {}), "manifest.public_repo_safety")

    upstream_quality = manifest.get("upstream_quality_summary", {})
    if upstream_quality.get("formal_calculation_blocked") is True:
        if manifest.get("fact_layer_status") != "structural_fact_layer_blocked_for_formal_calculation":
            raise ProjectCostFactLayerError("S09-P1 blocked upstream quality must block formal calculation")
    if upstream_quality.get("manual_review_queue_count", 0) < 1:
        raise ProjectCostFactLayerError("S09-P1 must preserve unresolved entity matching review queue status")
    if upstream_quality.get("unresolved_difference_count", 0) < 1:
        raise ProjectCostFactLayerError("S09-P1 must preserve unresolved source difference queue status")

    for record in fact_records:
        if record.get("schema_version") != "kmfa.project_cost_fact_record.v1":
            raise ProjectCostFactLayerError("invalid S09-P1 fact record schema_version")
        if record.get("record_type") != "project_cost_fact_record":
            raise ProjectCostFactLayerError("S09-P1 fact record type mismatch")
        if record.get("stage_phase") != "S09-P1":
            raise ProjectCostFactLayerError("S09-P1 fact record stage_phase mismatch")
        if set(record.get("metric_slots", [])) != set(REQUIRED_FACT_METRICS):
            raise ProjectCostFactLayerError(f"{record.get('fact_record_id')} metric slots mismatch")
        if set(record.get("cost_category_slots", [])) != set(REQUIRED_COST_CATEGORIES):
            raise ProjectCostFactLayerError(f"{record.get('fact_record_id')} cost categories mismatch")
        _validate_private_ref_map(record.get("metric_private_refs", {}), REQUIRED_FACT_METRICS, "metric_private_refs")
        _validate_hash_ref_map(record.get("metric_hash_refs", {}), REQUIRED_FACT_METRICS, "metric_hash_refs")
        _validate_private_ref_map(
            record.get("cost_category_private_refs", {}), REQUIRED_COST_CATEGORIES, "cost_category_private_refs"
        )
        _validate_hash_ref_map(
            record.get("cost_category_hash_refs", {}), REQUIRED_COST_CATEGORIES, "cost_category_hash_refs"
        )
        _require_hash(record.get("source_hash"), "record.source_hash")
        if record.get("metric_values_public_committed") is not False:
            raise ProjectCostFactLayerError("S09-P1 fact record cannot commit metric values")
        if record.get("amount_calculation_performed") is not False:
            raise ProjectCostFactLayerError("S09-P1 cannot perform amount calculation")
        if record.get("formal_calculation_allowed") is not False:
            raise ProjectCostFactLayerError("S09-P1 cannot allow formal calculation")
        if record.get("raw_layer_write_allowed") is not False:
            raise ProjectCostFactLayerError("S09-P1 fact record cannot write raw layer")
        _require_false(record.get("public_repo_safety", {}), f"record.{record.get('fact_record_id')}.public_repo_safety")

    pool_categories = {item.get("cost_category") for item in unallocated_pool}
    if pool_categories != set(REQUIRED_COST_CATEGORIES):
        raise ProjectCostFactLayerError("S09-P1 unallocated pool cost category coverage mismatch")
    for pool_item in unallocated_pool:
        if pool_item.get("schema_version") != "kmfa.unallocated_project_cost_pool.v1":
            raise ProjectCostFactLayerError("invalid S09-P1 unallocated pool schema_version")
        if pool_item.get("pool_type") != "unallocated_project_cost_pool":
            raise ProjectCostFactLayerError("S09-P1 pool type mismatch")
        _require_hash(pool_item.get("cost_category_hash"), "pool.cost_category_hash")
        _require_hash(pool_item.get("amount_value_hash_ref"), "pool.amount_value_hash_ref")
        if not str(pool_item.get("amount_value_private_ref", "")).startswith("private_ref://"):
            raise ProjectCostFactLayerError("S09-P1 pool amount private ref missing")
        if pool_item.get("amount_value_public_committed") is not False:
            raise ProjectCostFactLayerError("S09-P1 pool cannot commit amount values")
        if pool_item.get("assignment_status") != "pending_project_assignment_or_quality_resolution":
            raise ProjectCostFactLayerError("S09-P1 pool assignment status mismatch")
        if pool_item.get("raw_layer_write_allowed") is not False:
            raise ProjectCostFactLayerError("S09-P1 pool cannot write raw layer")
        _require_false(pool_item.get("public_repo_safety", {}), f"pool.{pool_item.get('pool_id')}.public_repo_safety")

    forbidden_hits = _walk_forbidden_keys([manifest, fact_records, unallocated_pool])
    if forbidden_hits:
        raise ProjectCostFactLayerError("forbidden public keys found: " + ", ".join(forbidden_hits))
    suffix_hits = _walk_forbidden_suffixes([manifest, fact_records, unallocated_pool])
    if suffix_hits:
        raise ProjectCostFactLayerError("forbidden raw/sensitive suffix refs found: " + ", ".join(suffix_hits))


def write_default_artifacts(generated_at: str) -> dict[str, Any]:
    manifest, fact_records, unallocated_pool = build_default_project_cost_fact_layer(generated_at=generated_at)
    _write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    _write_jsonl(DEFAULT_OUTPUT_FACT_RECORDS, fact_records)
    _write_jsonl(DEFAULT_OUTPUT_UNALLOCATED_POOL, unallocated_pool)
    stage_manifest = {
        "schema_version": "kmfa.s09_p1_manifest.v1",
        "record_type": "s09_p1_project_cost_fact_layer_manifest",
        "project_id": "KMFA",
        "stage_phase": "S09-P1",
        "generated_at": generated_at,
        "fact_layer_status": manifest["fact_layer_status"],
        "required_metric_count": manifest["summary"]["required_metric_count"],
        "cost_category_count": manifest["summary"]["cost_category_count"],
        "fact_record_count": manifest["summary"]["fact_record_count"],
        "unallocated_pool_count": manifest["summary"]["unallocated_pool_count"],
        "manual_review_queue_count": manifest["upstream_quality_summary"]["manual_review_queue_count"],
        "unresolved_difference_count": manifest["upstream_quality_summary"]["unresolved_difference_count"],
        "fact_layer_manifest_ref": "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
        "fact_records_ref": "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
        "unallocated_project_cost_pool_ref": "KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl",
        "completion_record_ref": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/s09_p1_completion_record.md",
        "test_results_ref": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/test_results.md",
        "validator_ref": "KMFA/tools/check_s09_p1_project_cost_fact_layer.py",
        "github_upload_allowed": False,
        "formal_report_allowed": False,
        "s09_p2_scope_included": False,
        "s09_p3_scope_included": False,
        "stage9_review_scope_included": False,
        "public_repo_safety": manifest["public_repo_safety"],
    }
    _write_json(DEFAULT_OUTPUT_STAGE_MANIFEST, stage_manifest)
    return stage_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S09-P1 project cost fact layer artifacts.")
    parser.add_argument("--generated-at", default="2026-06-30T23:30:00+10:00")
    args = parser.parse_args(argv)
    stage_manifest = write_default_artifacts(args.generated_at)
    print(
        "PASS: KMFA S09-P1 project cost fact layer artifacts written "
        f"(fact_records={stage_manifest['fact_record_count']}, "
        f"cost_categories={stage_manifest['cost_category_count']}, "
        f"unallocated_pool={stage_manifest['unallocated_pool_count']}, "
        "formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
