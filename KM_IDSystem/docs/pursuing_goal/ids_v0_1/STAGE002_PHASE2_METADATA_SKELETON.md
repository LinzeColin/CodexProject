# IDS v0.1 STAGE-002 Phase 2 Metadata Skeleton

## Identity

- Stage: `STAGE-002`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE002-P2`
- Acceptance ID: `ACC-STAGE-002`
- Stage title: `新建 ProductMetaDatabase`
- Recorded at UTC: `2026-07-02T05:11:01Z`

## Goal

Create the smallest useful `ProductMetaDatabase` skeleton for IDS v0.1:
product schema, manifest template, governance rules, taskpack input, README,
validator, and focused tests. The skeleton must be parseable, Git-trackable,
and reversible without touching raw materials or runtime data.

## Implemented Skeleton

`KM_IDSystem/product_meta_database/` now contains:

| Path | Purpose |
|---|---|
| `README.md` | Operator contract, contents, validation command, rollback. |
| `schemas/product_metadata.schema.json` | Minimal product metadata schema with future lineage fields. |
| `manifest_templates/product_manifest.template.json` | Manifest template linking schema, rules, and taskpack input. |
| `governance_rules/product_metadata_rules.json` | Storage, marker, path, and contract-reference rules. |
| `taskpack_inputs/stage002_product_metadata_input.json` | P0 STAGE-002 taskpack-derived metadata input. |
| `validate_product_meta_database.py` | Standard-library validator for the skeleton. |
| `tests/test_contract.py` | Focused unittest contract coverage. |

## Boundaries Preserved

- No backend route, frontend route, app bundle, service launcher, or runtime DB
  was added.
- No schema migration, PostgreSQL dependency, worker, external API, or raw file
  ingestion was added.
- No `data/`, `reports/`, `outputs/`, `.venv/`, `frontend/node_modules/`,
  external-drive root, or `00_ORIGINAL_RAW_DATA` path was created or modified.
- `external_api_policy` remains `denied`.
- `raw_material_policy` remains `forbidden`.
- Product display identity remains `IDS / Industrial Data System`.

## TDD Evidence

Red:

- Command:
  `Codex bundled python -m unittest KM_IDSystem/product_meta_database/tests/test_contract.py -q`
- Result before implementation: 2 errors because
  `KM_IDSystem/product_meta_database/validate_product_meta_database.py` did not
  exist.

Green:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/product_meta_database/tests/test_contract.py -q`
- Result after implementation: 2 tests ran and returned `OK`.
- Command:
  `Codex bundled python -B KM_IDSystem/product_meta_database/validate_product_meta_database.py`
- Result after implementation: `valid=true`, `issues=[]`,
  `external_api_policy=denied`, `raw_material_policy=forbidden`,
  `forbidden_markers=[]`, `forbidden_runtime_paths_present=false`,
  and six future lineage fields.

Final run checks:

- `check-render --project KM_IDSystem`: `drift_count=0`;
- marker and JSONL check: `stage002_phase2_marker_jsonl_ok events=15`;
- changed-scope and `git diff --check`: `changed_scope_ok`;
- no `__pycache__` remained under `KM_IDSystem/product_meta_database/`;
- full semantic governance validate remains blocked by the known sparse
  worktree omissions: 28 errors for missing root governance schemas,
  workflows/hooks, governance tests, skill/config files, and unrelated
  registered project directories.

## Validation Coverage

The validator checks:

- all JSON contracts parse with the Python standard library;
- required contract references match across schema, manifest, rules, and
  taskpack input;
- `product_id`, `subsystem`, `stage`, and `acceptance_id` remain bound to
  `IDS`, `ProductMetaDatabase`, `STAGE-002`, and `ACC-STAGE-002`;
- credential-like markers are absent from content outside their rule
  definitions;
- forbidden runtime subpaths do not exist inside ProductMetaDatabase;
- every contract file remains below `max_contract_file_bytes`.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE002-P2` commit. Because
this phase adds only static metadata contracts and tests, rollback does not
require data cleanup, report cleanup, service restart, dependency restoration,
database migration rollback, or raw-material handling.

## Decision

STAGE-002 Phase 2 is locally satisfied. The next run may enter STAGE-002 Phase
3 to validate references, legacy alias classification, and boundary exceptions.
The `STAGE-001..010` batch still must not be pushed until all 10 stages are
complete, reviewed, and repaired.
