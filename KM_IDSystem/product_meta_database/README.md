# ProductMetaDatabase

`ProductMetaDatabase` is the IDS v0.1 product metadata control plane. It stores
small, versioned, Git-trackable contracts for product metadata, manifest
templates, governance rules, and taskpack-derived inputs.

It is not a raw-material repository, not an external-drive mirror, not a
runtime database, and not a schema migration. Real source materials, generated
reports, local runtime data, dependency folders, and credentials are outside
this directory.

## Contents

| Path | Purpose |
|---|---|
| `schemas/product_metadata.schema.json` | Minimal product metadata schema for ProductMetaDatabase records. |
| `manifest_templates/product_manifest.template.json` | Manifest template tying schema, rules, and taskpack input together. |
| `governance_rules/product_metadata_rules.json` | Deterministic storage and validation rules for the metadata control plane. |
| `taskpack_inputs/stage002_product_metadata_input.json` | STAGE-002 taskpack-derived input contract. |
| `validate_product_meta_database.py` | Standard-library validator for the skeleton. |
| `tests/test_contract.py` | Focused unittest coverage for the skeleton contract. |

## Local Validation

Run from the repository root:

```bash
python3 KM_IDSystem/product_meta_database/validate_product_meta_database.py
python3 -m unittest KM_IDSystem/product_meta_database/tests/test_contract.py -q
```

The validator parses every JSON contract, verifies policy fields, checks
contract references, blocks runtime-output subdirectories, and confirms this
skeleton does not embed credential-like markers.

## Rollback

Revert the STAGE-002 Phase 2 commit. No data cleanup, service restart,
database rollback, report cleanup, or dependency restoration is required.

