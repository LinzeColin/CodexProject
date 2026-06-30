#!/usr/bin/env python3
"""Build KMFA S08-P2 public-safe business entity model metadata.

The model defines the customer, contract, project, cost, invoice, collection,
receivable, and tax evidence entities, plus their controlled relationships and
lifecycle statuses. Public outputs keep schema, refs, hashes, status metadata,
and evidence refs only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "schema_maps" / "business_entity_model_manifest.json"
DEFAULT_OUTPUT_SCHEMA = ROOT / "metadata" / "schema_maps" / "business_entity_model_schema.json"
DEFAULT_OUTPUT_RELATIONSHIPS = ROOT / "metadata" / "schema_maps" / "business_entity_relationships.jsonl"
DEFAULT_OUTPUT_LIFECYCLES = ROOT / "metadata" / "schema_maps" / "business_entity_lifecycle_statuses.jsonl"
DEFAULT_OUTPUT_SCHEMA_DOC = ROOT / "docs" / "governance" / "BUSINESS_ENTITY_MODEL_SCHEMA.md"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S08_P2_business_entity_model" / "machine" / "s08_p2_manifest.json"
)

REQUIRED_ENTITY_TYPES = (
    "customer",
    "contract",
    "project",
    "cost_record",
    "invoice",
    "collection",
    "receivable",
    "tax_evidence",
)

COMMON_PUBLIC_SAFE_FIELDS = (
    "entity_ref",
    "source_ref",
    "source_hash",
    "lifecycle_status",
    "quality_status",
    "evidence_ref",
)

LIFECYCLE_STATUSES = (
    "candidate",
    "active",
    "requires_review",
    "closed",
)

HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
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
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
}


@dataclass(frozen=True)
class EntitySpec:
    entity_type: str
    role: str
    required_public_safe_fields: tuple[str, ...]
    upstream_refs: tuple[str, ...]


@dataclass(frozen=True)
class RelationshipSpec:
    from_entity_type: str
    to_entity_type: str
    relationship_type: str
    cardinality: str
    required_ref_fields: tuple[str, ...]


ENTITY_SPECS = (
    EntitySpec(
        "customer",
        "counterparty identity anchor for contracts, invoices, collections, receivables, and tax evidence",
        COMMON_PUBLIC_SAFE_FIELDS + ("customer_hash", "counterparty_role"),
        ("project_identity_profile", "finance_source", "wps_source", "redcircle_reserved_export"),
    ),
    EntitySpec(
        "contract",
        "controlled agreement anchor linking customer, project, invoices, receivables, and tax evidence",
        COMMON_PUBLIC_SAFE_FIELDS + ("contract_hash", "customer_entity_ref", "project_entity_ref"),
        ("project_identity_profile", "a0_authority_baseline", "redcircle_reserved_export"),
    ),
    EntitySpec(
        "project",
        "project identity anchor linked to contract, customer, cost, invoice, receivable, and collection evidence",
        COMMON_PUBLIC_SAFE_FIELDS + ("project_identity_profile_ref", "project_composite_key_hash", "company_entity_hash"),
        ("project_composite_key", "a0_authority_baseline", "finance_source", "wps_source"),
    ),
    EntitySpec(
        "cost_record",
        "project cost evidence container; not a fact-layer posting in S08-P2",
        COMMON_PUBLIC_SAFE_FIELDS + ("project_entity_ref", "amount_signature_hash", "cost_category_ref"),
        ("a0_authority_baseline", "finance_source"),
    ),
    EntitySpec(
        "invoice",
        "billing evidence container linked to project, contract, customer, receivable, collection, and tax evidence",
        COMMON_PUBLIC_SAFE_FIELDS + ("invoice_hash", "project_entity_ref", "contract_entity_ref", "customer_entity_ref"),
        ("finance_source", "wps_source", "redcircle_reserved_export"),
    ),
    EntitySpec(
        "collection",
        "payment collection evidence container linked to invoice and receivable settlement status",
        COMMON_PUBLIC_SAFE_FIELDS + ("collection_hash", "invoice_entity_ref", "receivable_entity_ref"),
        ("finance_source", "wps_source", "redcircle_reserved_export"),
    ),
    EntitySpec(
        "receivable",
        "receivable evidence container linked to customer, project, invoice, and collection status",
        COMMON_PUBLIC_SAFE_FIELDS + ("receivable_hash", "customer_entity_ref", "project_entity_ref", "invoice_entity_ref"),
        ("finance_source", "wps_source"),
    ),
    EntitySpec(
        "tax_evidence",
        "tax evidence container linked to invoice and contract without enabling automatic tax filing",
        COMMON_PUBLIC_SAFE_FIELDS + ("tax_evidence_hash", "invoice_entity_ref", "contract_entity_ref"),
        ("finance_source", "redcircle_reserved_export"),
    ),
)

RELATIONSHIP_SPECS = (
    RelationshipSpec("customer", "contract", "customer_has_contract", "one_to_many", ("customer_entity_ref",)),
    RelationshipSpec("contract", "project", "contract_controls_project", "one_to_many", ("contract_entity_ref",)),
    RelationshipSpec("customer", "project", "customer_is_project_counterparty", "one_to_many", ("customer_entity_ref",)),
    RelationshipSpec("project", "cost_record", "project_has_cost_record", "one_to_many", ("project_entity_ref",)),
    RelationshipSpec("project", "invoice", "project_has_invoice", "one_to_many", ("project_entity_ref",)),
    RelationshipSpec("contract", "invoice", "contract_has_invoice", "one_to_many", ("contract_entity_ref",)),
    RelationshipSpec("customer", "invoice", "customer_is_invoice_counterparty", "one_to_many", ("customer_entity_ref",)),
    RelationshipSpec("invoice", "receivable", "invoice_generates_receivable", "one_to_one_or_many", ("invoice_entity_ref",)),
    RelationshipSpec("customer", "receivable", "customer_has_receivable", "one_to_many", ("customer_entity_ref",)),
    RelationshipSpec("project", "receivable", "project_has_receivable", "one_to_many", ("project_entity_ref",)),
    RelationshipSpec("invoice", "collection", "invoice_is_settled_by_collection", "one_to_many", ("invoice_entity_ref",)),
    RelationshipSpec(
        "receivable", "collection", "receivable_is_reduced_by_collection", "one_to_many", ("receivable_entity_ref",)
    ),
    RelationshipSpec(
        "invoice", "tax_evidence", "invoice_supported_by_tax_evidence", "one_to_many", ("invoice_entity_ref",)
    ),
    RelationshipSpec(
        "contract", "tax_evidence", "contract_supported_by_tax_evidence", "one_to_many", ("contract_entity_ref",)
    ),
)


class BusinessEntityModelError(ValueError):
    """Raised when S08-P2 business entity model metadata is invalid."""


def require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise BusinessEntityModelError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise BusinessEntityModelError(f"{field_name} is required")
    return text


def _entity_definition(spec: EntitySpec) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.business_entity_definition.v1",
        "record_type": "business_entity_definition",
        "project_id": "KMFA",
        "stage_phase": "S08-P2",
        "entity_type": spec.entity_type,
        "entity_role": spec.role,
        "required_public_safe_fields": list(spec.required_public_safe_fields),
        "upstream_refs": list(spec.upstream_refs),
        "private_ref_required": True,
        "raw_layer_write_allowed": False,
        "automatic_external_action_allowed": False,
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "field_plaintext_committed": False,
            "raw_file_committed": False,
            "private_tabular_files_committed": False,
        },
    }


def build_default_business_entity_model(
    *, generated_at: str
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_at_value = require_text(generated_at, "generated_at")
    entity_definitions = [_entity_definition(spec) for spec in ENTITY_SPECS]
    relationships = [
        {
            "schema_version": "kmfa.business_entity_relationship.v1",
            "record_type": "business_entity_relationship",
            "project_id": "KMFA",
            "stage_phase": "S08-P2",
            "relationship_id": f"BER-S08P2-{index:03d}",
            "from_entity_type": spec.from_entity_type,
            "to_entity_type": spec.to_entity_type,
            "relationship_type": spec.relationship_type,
            "cardinality": spec.cardinality,
            "required_ref_fields": list(spec.required_ref_fields),
            "relationship_status": "schema_defined",
            "raw_layer_write_allowed": False,
            "evidence_ref": "KMFA/stage_artifacts/S08_P2_business_entity_model/human/test_results.md",
        }
        for index, spec in enumerate(RELATIONSHIP_SPECS, start=1)
    ]
    lifecycle_statuses = [
        {
            "schema_version": "kmfa.business_entity_lifecycle_status.v1",
            "record_type": "business_entity_lifecycle_status",
            "project_id": "KMFA",
            "stage_phase": "S08-P2",
            "status_id": f"BEL-S08P2-{entity_type.upper().replace('_', '-')}-{status.upper().replace('_', '-')}",
            "entity_type": entity_type,
            "lifecycle_status": status,
            "status_category": "review" if status == "requires_review" else "controlled_lifecycle",
            "terminal_status": status == "closed",
            "raw_layer_write_allowed": False,
            "evidence_ref": "KMFA/stage_artifacts/S08_P2_business_entity_model/human/test_results.md",
        }
        for entity_type in REQUIRED_ENTITY_TYPES
        for status in LIFECYCLE_STATUSES
    ]
    schema_doc = {
        "schema_version": "kmfa.business_entity_model_schema.v1",
        "record_type": "business_entity_model_schema",
        "project_id": "KMFA",
        "stage_phase": "S08-P2",
        "generated_at": generated_at_value,
        "entity_definitions": entity_definitions,
        "relationship_ref": "KMFA/metadata/schema_maps/business_entity_relationships.jsonl",
        "lifecycle_ref": "KMFA/metadata/schema_maps/business_entity_lifecycle_statuses.jsonl",
        "source_model_refs": {
            "project_identity_profiles": "KMFA/metadata/schema_maps/project_identity_profiles.jsonl",
            "project_composite_key_manifest": "KMFA/metadata/schema_maps/project_composite_key_manifest.json",
            "a0_authority_baseline": "KMFA/metadata/baseline/a0_authority_baseline_manifest.json",
            "finance_adapter": "KMFA/metadata/schema_maps/finance_file_adapter_manifest.json",
            "wps_adapter": "KMFA/metadata/schema_maps/wps_file_adapter_manifest.json",
            "redcircle_postponement": "KMFA/metadata/schema_maps/redcircle_postponement_manifest.json",
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "field_plaintext_committed": False,
            "raw_file_committed": False,
            "private_tabular_files_committed": False,
        },
    }
    manifest = {
        "schema_version": "kmfa.business_entity_model_manifest.v1",
        "record_type": "s08_p2_business_entity_model_manifest",
        "project_id": "KMFA",
        "stage_phase": "S08-P2",
        "generated_at": generated_at_value,
        "required_entity_types": list(REQUIRED_ENTITY_TYPES),
        "summary": {
            "entity_type_count": len(REQUIRED_ENTITY_TYPES),
            "relationship_count": len(relationships),
            "lifecycle_status_count": len(lifecycle_statuses),
        },
        "stage_scope": {
            "s08_p1_project_composite_key_scope_included": False,
            "s08_p2_entity_model_scope_included": True,
            "s08_p3_matching_quality_scope_included": False,
            "fact_layer_scope_included": False,
            "lineage_full_check_scope_included": False,
            "report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
        },
        "quality_gate": {
            "formal_report_allowed": False,
            "q5_calculation_baseline_allowed": False,
            "github_upload_allowed": False,
            "phase_completion_upload_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "artifact_refs": {
            "schema": "KMFA/metadata/schema_maps/business_entity_model_schema.json",
            "schema_doc": "KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md",
            "relationships": "KMFA/metadata/schema_maps/business_entity_relationships.jsonl",
            "lifecycle_statuses": "KMFA/metadata/schema_maps/business_entity_lifecycle_statuses.jsonl",
            "completion_record": "KMFA/stage_artifacts/S08_P2_business_entity_model/human/s08_p2_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S08_P2_business_entity_model/human/test_results.md",
        },
        "public_repo_safety": {
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
            "field_plaintext_committed": False,
            "raw_file_committed": False,
            "private_tabular_files_committed": False,
        },
    }
    return manifest, schema_doc, relationships, lifecycle_statuses


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


def _require_false(container: dict[str, Any], path: str) -> None:
    for key, value in container.items():
        if value is not False:
            raise BusinessEntityModelError(f"{path}.{key} must be false")


def validate_business_entity_model_artifacts(
    manifest: dict[str, Any],
    schema_doc: dict[str, Any],
    relationships: list[dict[str, Any]],
    lifecycle_statuses: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.business_entity_model_manifest.v1":
        raise BusinessEntityModelError("invalid S08-P2 manifest schema_version")
    if schema_doc.get("schema_version") != "kmfa.business_entity_model_schema.v1":
        raise BusinessEntityModelError("invalid S08-P2 schema doc schema_version")
    if tuple(manifest.get("required_entity_types", [])) != REQUIRED_ENTITY_TYPES:
        raise BusinessEntityModelError("S08-P2 required entity types mismatch")
    entity_definitions = schema_doc.get("entity_definitions", [])
    if not isinstance(entity_definitions, list):
        raise BusinessEntityModelError("S08-P2 schema entity_definitions must be a list")
    if len(entity_definitions) != len(REQUIRED_ENTITY_TYPES):
        raise BusinessEntityModelError("S08-P2 entity definition count mismatch")
    entity_types = {record.get("entity_type") for record in entity_definitions}
    if entity_types != set(REQUIRED_ENTITY_TYPES):
        raise BusinessEntityModelError("S08-P2 entity definition type mismatch")
    if len(relationships) != manifest.get("summary", {}).get("relationship_count"):
        raise BusinessEntityModelError("S08-P2 relationship count mismatch")
    if len(lifecycle_statuses) != manifest.get("summary", {}).get("lifecycle_status_count"):
        raise BusinessEntityModelError("S08-P2 lifecycle status count mismatch")
    if manifest.get("summary", {}).get("entity_type_count") != len(REQUIRED_ENTITY_TYPES):
        raise BusinessEntityModelError("S08-P2 entity type count mismatch")
    if manifest.get("stage_scope", {}).get("s08_p2_entity_model_scope_included") is not True:
        raise BusinessEntityModelError("S08-P2 scope must be included")
    for excluded_scope in (
        "s08_p3_matching_quality_scope_included",
        "fact_layer_scope_included",
        "lineage_full_check_scope_included",
        "report_scope_included",
        "ui_scope_included",
        "external_connector_scope_included",
    ):
        if manifest.get("stage_scope", {}).get(excluded_scope) is not False:
            raise BusinessEntityModelError(f"S08-P2 must exclude {excluded_scope}")
    _require_false(manifest.get("quality_gate", {}), "manifest.quality_gate")
    _require_false(manifest.get("public_repo_safety", {}), "manifest.public_repo_safety")
    _require_false(schema_doc.get("public_repo_safety", {}), "schema_doc.public_repo_safety")

    for entity in entity_definitions:
        fields = set(entity.get("required_public_safe_fields", []))
        missing = set(COMMON_PUBLIC_SAFE_FIELDS) - fields
        if missing:
            raise BusinessEntityModelError(f"{entity.get('entity_type')} missing public-safe fields: {sorted(missing)}")
        if entity.get("private_ref_required") is not True:
            raise BusinessEntityModelError(f"{entity.get('entity_type')} must require private refs")
        if entity.get("raw_layer_write_allowed") is not False:
            raise BusinessEntityModelError(f"{entity.get('entity_type')} cannot allow raw layer writes")
        _require_false(entity.get("public_repo_safety", {}), f"entity.{entity.get('entity_type')}.public_repo_safety")

    for relationship in relationships:
        if relationship.get("from_entity_type") not in entity_types:
            raise BusinessEntityModelError("S08-P2 relationship has unknown from_entity_type")
        if relationship.get("to_entity_type") not in entity_types:
            raise BusinessEntityModelError("S08-P2 relationship has unknown to_entity_type")
        if not relationship.get("relationship_type"):
            raise BusinessEntityModelError("S08-P2 relationship_type is required")
        if relationship.get("raw_layer_write_allowed") is not False:
            raise BusinessEntityModelError("S08-P2 relationships cannot allow raw layer writes")

    lifecycle_by_entity: dict[str, set[str]] = {entity_type: set() for entity_type in REQUIRED_ENTITY_TYPES}
    for status_record in lifecycle_statuses:
        entity_type = status_record.get("entity_type")
        status = status_record.get("lifecycle_status")
        if entity_type not in lifecycle_by_entity:
            raise BusinessEntityModelError("S08-P2 lifecycle has unknown entity_type")
        lifecycle_by_entity[entity_type].add(status)
        if status_record.get("raw_layer_write_allowed") is not False:
            raise BusinessEntityModelError("S08-P2 lifecycle status cannot allow raw layer writes")
    for entity_type, statuses in lifecycle_by_entity.items():
        missing = set(LIFECYCLE_STATUSES) - statuses
        if missing:
            raise BusinessEntityModelError(f"{entity_type} missing lifecycle statuses: {sorted(missing)}")

    required_pairs = {
        ("customer", "contract", "customer_has_contract"),
        ("contract", "project", "contract_controls_project"),
        ("project", "cost_record", "project_has_cost_record"),
        ("project", "invoice", "project_has_invoice"),
        ("invoice", "collection", "invoice_is_settled_by_collection"),
        ("receivable", "collection", "receivable_is_reduced_by_collection"),
        ("invoice", "tax_evidence", "invoice_supported_by_tax_evidence"),
    }
    actual_pairs = {
        (item.get("from_entity_type"), item.get("to_entity_type"), item.get("relationship_type"))
        for item in relationships
    }
    if not required_pairs.issubset(actual_pairs):
        raise BusinessEntityModelError("S08-P2 required relationship graph is incomplete")

    forbidden_hits = _walk_forbidden_keys([manifest, schema_doc, relationships, lifecycle_statuses])
    if forbidden_hits:
        raise BusinessEntityModelError("forbidden public keys found: " + ", ".join(forbidden_hits))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise BusinessEntityModelError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise BusinessEntityModelError(f"{path} contains a non-object JSONL record")
                records.append(value)
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def render_schema_markdown(schema_doc: dict[str, Any], relationships: list[dict[str, Any]]) -> str:
    lines = [
        "# KMFA S08-P2 Business Entity Model Schema",
        "",
        "This public-safe schema defines entity types, required metadata fields, controlled relationships,",
        "and lifecycle states for S08-P2. It does not contain raw business values, source headers,",
        "private files, fact-layer rows, reports, UI scope, or external connector actions.",
        "",
        "## Entity Types",
        "",
        "| Entity Type | Role | Required Public-Safe Fields |",
        "|---|---|---|",
    ]
    for entity in schema_doc["entity_definitions"]:
        fields = "; ".join(entity["required_public_safe_fields"])
        lines.append(f"| `{entity['entity_type']}` | {entity['entity_role']} | `{fields}` |")
    lines.extend(
        [
            "",
            "## Relationships",
            "",
            "| From | To | Relationship | Cardinality |",
            "|---|---|---|---|",
        ]
    )
    for relationship in relationships:
        lines.append(
            f"| `{relationship['from_entity_type']}` | `{relationship['to_entity_type']}` | "
            f"`{relationship['relationship_type']}` | `{relationship['cardinality']}` |"
        )
    lines.extend(
        [
            "",
            "## Lifecycle Statuses",
            "",
            "`candidate`, `active`, `requires_review`, and `closed` are defined for every S08-P2 entity type.",
            "",
            "## Scope Boundary",
            "",
            "- S08-P2 defines schema and metadata only.",
            "- S08-P3 matching quality tests are not included.",
            "- Fact layer, full lineage check, formal report generation, UI, external connectors, and GitHub upload are not included.",
            "- Public outputs keep hash/ref/status/schema/evidence metadata only.",
            "",
        ]
    )
    return "\n".join(lines)


def write_default_artifacts(generated_at: str) -> dict[str, Any]:
    manifest, schema_doc, relationships, lifecycle_statuses = build_default_business_entity_model(
        generated_at=generated_at
    )
    validate_business_entity_model_artifacts(manifest, schema_doc, relationships, lifecycle_statuses)
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_json(DEFAULT_OUTPUT_SCHEMA, schema_doc)
    write_jsonl(DEFAULT_OUTPUT_RELATIONSHIPS, relationships)
    write_jsonl(DEFAULT_OUTPUT_LIFECYCLES, lifecycle_statuses)
    DEFAULT_OUTPUT_SCHEMA_DOC.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_SCHEMA_DOC.write_text(render_schema_markdown(schema_doc, relationships), encoding="utf-8")
    stage_manifest = {
        "schema_version": "kmfa.s08_p2_manifest.v1",
        "record_type": "s08_p2_business_entity_model_manifest",
        "project_id": "KMFA",
        "stage_phase": "S08-P2",
        "generated_at": generated_at,
        "required_entity_type_count": len(REQUIRED_ENTITY_TYPES),
        "relationship_count": len(relationships),
        "lifecycle_status_count": len(lifecycle_statuses),
        "manifest_ref": "KMFA/metadata/schema_maps/business_entity_model_manifest.json",
        "schema_ref": "KMFA/metadata/schema_maps/business_entity_model_schema.json",
        "schema_doc_ref": "KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md",
        "relationships_ref": "KMFA/metadata/schema_maps/business_entity_relationships.jsonl",
        "lifecycle_statuses_ref": "KMFA/metadata/schema_maps/business_entity_lifecycle_statuses.jsonl",
        "completion_record_ref": "KMFA/stage_artifacts/S08_P2_business_entity_model/human/s08_p2_completion_record.md",
        "test_results_ref": "KMFA/stage_artifacts/S08_P2_business_entity_model/human/test_results.md",
        "validator_ref": "KMFA/tools/check_s08_p2_business_entity_model.py",
        "github_upload_allowed": False,
        "formal_report_allowed": False,
        "fact_layer_scope_included": False,
        "s08_p3_matching_quality_scope_included": False,
        "public_repo_safety": manifest["public_repo_safety"],
    }
    write_json(DEFAULT_OUTPUT_STAGE_MANIFEST, stage_manifest)
    return stage_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S08-P2 business entity model artifacts.")
    parser.add_argument("--generated-at", default="2026-06-30T21:00:00+10:00")
    args = parser.parse_args(argv)
    stage_manifest = write_default_artifacts(args.generated_at)
    print(
        "PASS: KMFA S08-P2 business entity model artifacts written "
        f"(entities={stage_manifest['required_entity_type_count']}, "
        f"relationships={stage_manifest['relationship_count']}, "
        f"lifecycle_statuses={stage_manifest['lifecycle_status_count']}, "
        "formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
