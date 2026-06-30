import json
import unittest

from KMFA.tools.business_entity_model import (
    REQUIRED_ENTITY_TYPES,
    build_default_business_entity_model,
    validate_business_entity_model_artifacts,
)


class BusinessEntityModelTests(unittest.TestCase):
    def test_default_model_defines_required_entities_relationships_and_lifecycles(self) -> None:
        manifest, schema_doc, relationships, lifecycle_statuses = build_default_business_entity_model(
            generated_at="2026-06-30T21:00:00+10:00"
        )
        validate_business_entity_model_artifacts(manifest, schema_doc, relationships, lifecycle_statuses)

        self.assertEqual(set(REQUIRED_ENTITY_TYPES), {
            "customer",
            "contract",
            "project",
            "cost_record",
            "invoice",
            "collection",
            "receivable",
            "tax_evidence",
        })
        self.assertEqual(set(manifest["required_entity_types"]), set(REQUIRED_ENTITY_TYPES))
        self.assertEqual(manifest["summary"]["entity_type_count"], 8)
        self.assertEqual(manifest["summary"]["relationship_count"], len(relationships))
        self.assertEqual(manifest["summary"]["lifecycle_status_count"], len(lifecycle_statuses))
        self.assertGreaterEqual(len(relationships), 10)
        self.assertGreaterEqual(len(lifecycle_statuses), 24)

        schema_entity_types = {record["entity_type"] for record in schema_doc["entity_definitions"]}
        self.assertEqual(schema_entity_types, set(REQUIRED_ENTITY_TYPES))
        for entity in schema_doc["entity_definitions"]:
            self.assertIn("entity_ref", entity["required_public_safe_fields"])
            self.assertIn("source_ref", entity["required_public_safe_fields"])
            self.assertIn("source_hash", entity["required_public_safe_fields"])
            self.assertFalse(entity["public_repo_safety"]["raw_business_values_committed"])

    def test_relationships_cover_entity_graph_without_fact_layer_or_report_scope(self) -> None:
        manifest, schema_doc, relationships, lifecycle_statuses = build_default_business_entity_model(
            generated_at="2026-06-30T21:00:00+10:00"
        )

        pairs = {(item["from_entity_type"], item["to_entity_type"], item["relationship_type"]) for item in relationships}
        self.assertIn(("customer", "contract", "customer_has_contract"), pairs)
        self.assertIn(("contract", "project", "contract_controls_project"), pairs)
        self.assertIn(("project", "cost_record", "project_has_cost_record"), pairs)
        self.assertIn(("project", "invoice", "project_has_invoice"), pairs)
        self.assertIn(("invoice", "collection", "invoice_is_settled_by_collection"), pairs)
        self.assertIn(("receivable", "collection", "receivable_is_reduced_by_collection"), pairs)
        self.assertIn(("invoice", "tax_evidence", "invoice_supported_by_tax_evidence"), pairs)
        self.assertFalse(manifest["stage_scope"]["s08_p3_matching_quality_scope_included"])
        self.assertFalse(manifest["stage_scope"]["fact_layer_scope_included"])
        self.assertFalse(manifest["stage_scope"]["lineage_full_check_scope_included"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

        lifecycle_by_entity: dict[str, set[str]] = {}
        for status in lifecycle_statuses:
            lifecycle_by_entity.setdefault(status["entity_type"], set()).add(status["lifecycle_status"])
        for entity_type in REQUIRED_ENTITY_TYPES:
            self.assertIn("candidate", lifecycle_by_entity[entity_type])
            self.assertIn("active", lifecycle_by_entity[entity_type])
            self.assertIn("requires_review", lifecycle_by_entity[entity_type])

    def test_public_payload_has_no_raw_values_private_files_or_field_plaintext(self) -> None:
        manifest, schema_doc, relationships, lifecycle_statuses = build_default_business_entity_model(
            generated_at="2026-06-30T21:00:00+10:00"
        )
        payload = json.dumps([manifest, schema_doc, relationships, lifecycle_statuses], ensure_ascii=False, sort_keys=True)

        for forbidden_key in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private_csv",
            "bank_account_number",
            "identity_document_number",
        ):
            self.assertNotIn(forbidden_key, payload)
        self.assertIn("source_hash", payload)
        self.assertIn("private_ref_required", payload)


if __name__ == "__main__":
    unittest.main()
