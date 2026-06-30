# KMFA S08-P2 Business Entity Model Schema

This public-safe schema defines entity types, required metadata fields, controlled relationships,
and lifecycle states for S08-P2. It does not contain raw business values, source headers,
private files, fact-layer rows, reports, UI scope, or external connector actions.

## Entity Types

| Entity Type | Role | Required Public-Safe Fields |
|---|---|---|
| `customer` | counterparty identity anchor for contracts, invoices, collections, receivables, and tax evidence | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; customer_hash; counterparty_role` |
| `contract` | controlled agreement anchor linking customer, project, invoices, receivables, and tax evidence | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; contract_hash; customer_entity_ref; project_entity_ref` |
| `project` | project identity anchor linked to contract, customer, cost, invoice, receivable, and collection evidence | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; project_identity_profile_ref; project_composite_key_hash; company_entity_hash` |
| `cost_record` | project cost evidence container; not a fact-layer posting in S08-P2 | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; project_entity_ref; amount_signature_hash; cost_category_ref` |
| `invoice` | billing evidence container linked to project, contract, customer, receivable, collection, and tax evidence | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; invoice_hash; project_entity_ref; contract_entity_ref; customer_entity_ref` |
| `collection` | payment collection evidence container linked to invoice and receivable settlement status | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; collection_hash; invoice_entity_ref; receivable_entity_ref` |
| `receivable` | receivable evidence container linked to customer, project, invoice, and collection status | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; receivable_hash; customer_entity_ref; project_entity_ref; invoice_entity_ref` |
| `tax_evidence` | tax evidence container linked to invoice and contract without enabling automatic tax filing | `entity_ref; source_ref; source_hash; lifecycle_status; quality_status; evidence_ref; tax_evidence_hash; invoice_entity_ref; contract_entity_ref` |

## Relationships

| From | To | Relationship | Cardinality |
|---|---|---|---|
| `customer` | `contract` | `customer_has_contract` | `one_to_many` |
| `contract` | `project` | `contract_controls_project` | `one_to_many` |
| `customer` | `project` | `customer_is_project_counterparty` | `one_to_many` |
| `project` | `cost_record` | `project_has_cost_record` | `one_to_many` |
| `project` | `invoice` | `project_has_invoice` | `one_to_many` |
| `contract` | `invoice` | `contract_has_invoice` | `one_to_many` |
| `customer` | `invoice` | `customer_is_invoice_counterparty` | `one_to_many` |
| `invoice` | `receivable` | `invoice_generates_receivable` | `one_to_one_or_many` |
| `customer` | `receivable` | `customer_has_receivable` | `one_to_many` |
| `project` | `receivable` | `project_has_receivable` | `one_to_many` |
| `invoice` | `collection` | `invoice_is_settled_by_collection` | `one_to_many` |
| `receivable` | `collection` | `receivable_is_reduced_by_collection` | `one_to_many` |
| `invoice` | `tax_evidence` | `invoice_supported_by_tax_evidence` | `one_to_many` |
| `contract` | `tax_evidence` | `contract_supported_by_tax_evidence` | `one_to_many` |

## Lifecycle Statuses

`candidate`, `active`, `requires_review`, and `closed` are defined for every S08-P2 entity type.

## Scope Boundary

- S08-P2 defines schema and metadata only.
- S08-P3 matching quality tests are not included.
- Fact layer, full lineage check, formal report generation, UI, external connectors, and GitHub upload are not included.
- Public outputs keep hash/ref/status/schema/evidence metadata only.
