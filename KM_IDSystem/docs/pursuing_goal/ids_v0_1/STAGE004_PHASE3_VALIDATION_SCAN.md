# IDS v0.1 STAGE-004 Phase 3 Validation Scan

## Identity

- Stage: `STAGE-004`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE004-P3`
- Acceptance ID: `ACC-STAGE-004`
- Stage title: `旧名称引用扫描`
- Recorded at UTC: `2026-07-02T06:24:24Z`

## Goal

Validate the Phase 2 legacy-name scan slice across classification coverage,
customer-visible wording, active runtime context, false-positive exclusions,
secret-pattern classification, and local data/output boundaries.

This phase does not replace old names, does not modify runtime code, and does
not enter Phase 4.

Stop marker: this phase does not enter Phase 4.

## Validation Scope

Included:

- tracked text files under `KM_IDSystem/`;
- STAGE-004 entry, boundary, validator, unittest, and Phase 2 evidence;
- active frontend, backend app, app bundle, and script paths for legacy-name
  context classification;
- secret-pattern scan across tracked `KM_IDSystem/` files;
- changed-scope and forbidden tracked runtime-output checks.

Excluded:

- unrelated projects outside `KM_IDSystem/`;
- dependency folders, caches, local runtime databases, generated reports, and
  generated output folders;
- real raw materials and any external-drive data root.

## STAGE-004 Validator Results

Commands run:

- `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py -q`
- `Codex bundled python -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py`

Results:

- unittest ran 2 tests and returned `OK`;
- validator returned `valid=true`;
- validator returned `issues=[]`;
- `files_scanned=106`;
- `legacy_name_hits=1000`;
- `allowed_legacy_context=1000`;
- `active_display_debt=0`;
- `unique_paths_with_legacy_hits=49`;
- `forbidden_changed_paths=[]`.

Accepted-name false-positive guards remained present:

| Accepted name | Hits |
|---|---:|
| `IDS / Industrial Data System` | 38 |
| `ProductMetaDatabase` | 201 |
| `FinanceMetaDatabase` | 89 |

## Active Display And Customer-Visible Scan

The active context scan covered tracked files under:

- `KM_IDSystem/frontend/`
- `KM_IDSystem/backend/app/`
- `KM_IDSystem/app_bundle/`
- `KM_IDSystem/scripts/`

Results:

| Metric | Result |
|---|---:|
| active context legacy hits | 7 |
| unclassified active context hits | 0 |
| customer-visible context hits | 2 |
| unclassified customer-visible hits | 0 |

Classified active context refs:

- `KM_IDSystem/backend/app/core/config.py:10:legacy_wuhan_snake` is a legacy
  SQLite filename/default path context, not a new display name.
- `KM_IDSystem/backend/app/services/model_router.py:10:legacy_wuhan_cn` is
  company/source prompt context, not a new product display name.
- `KM_IDSystem/scripts/build_app_bundle.sh:9:legacy_asset_opmeicon` and
  `KM_IDSystem/scripts/build_app_bundle.sh:53:legacy_asset_opmeicon` are
  legacy asset filename contexts.
- `KM_IDSystem/scripts/generate_app_icon.py:13-15:legacy_asset_opmeicon` are
  legacy asset filename contexts.

No frontend route, app bundle display text, backend API title, or report
display surface was found using old product names as a new formal display
name in this scan.

## Secret And Runtime Boundary Scan

Raw strict secret-pattern scan found 8 pattern hits:

- `KM_IDSystem/backend/app/models/schemas.py:77` contains the empty schema
  field default `api_key: str = ""`;
- `KM_IDSystem/backend/app/services/db.py:235` contains SQL field text
  `api_key=excluded.api_key`;
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_PHASE4_CLOSEOUT.md:118`
  records policy marker text;
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE003_PHASE3_VALIDATION_SCAN.md:102`
  records the forbidden marker definition `BEGIN PRIVATE KEY`;
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE003_PHASE3_VALIDATION_SCAN.md:104`
  records SQL field text;
- `KM_IDSystem/product_meta_database/governance_rules/product_metadata_rules.json:36-38`
  defines blocked content markers: `BEGIN PRIVATE KEY`, `api_key=`, and
  `password=`.

All 8 are classified as schema text, SQL field names, policy marker
definitions, or validation-report self-reference. Actual credential hits after
classification: 0.

| Metric | Result |
|---|---:|
| raw secret-pattern hits | 8 |
| actual credential hits after classification | 0 |
| tracked files under `data/`, `reports/`, `outputs/`, `.venv/`, or `frontend/node_modules/` | 0 |

## Boundary Checks

- No old-name replacement was performed.
- No backend route, frontend route, app bundle display name, runtime database,
  schema migration, worker, external API path, raw-material copy, generated
  data, report output, dependency folder, GitHub push, PR, or merge was added.
- `ProductMetaDatabase` remains an accepted STAGE-002 subsystem and is not old
  name debt.
- `FinanceMetaDatabase` remains an accepted STAGE-003 canonical finance
  metadata name and is not old name debt.
- STAGE-004 Phase 3 adds only validation and governance evidence.

## Final Run Checks

Final validation for this phase must include:

- STAGE-004 unittest: 2 tests returned `OK`;
- STAGE-004 validator: `valid=true`, `issues=[]`,
  `active_display_debt=0`, `forbidden_changed_paths=[]`;
- active display and customer-visible scan:
  `unclassified_active_hits=[]`,
  `unclassified_customer_visible_hits=[]`;
- secret and runtime boundary scan:
  `actual_credential_hits=[]`,
  `tracked_forbidden_runtime_files=[]`;
- `check-render --project KM_IDSystem`;
- marker, JSONL, and changed-scope check;
- `git diff --check`;
- semantic governance validate as a sparse-worktree diagnostic only.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE004-P3` commit. Because
Phase 3 is validation/governance evidence only, rollback does not require
data cleanup, schema rollback, service restart, dependency restoration, report
cleanup, runtime file restore, or old-name replacement reversal.

## Decision

STAGE-004 Phase 3 passes with zero active display debt, zero unclassified
customer-visible hits, zero actual credential hits, and zero forbidden tracked
runtime-output files. The next run may enter STAGE-004 Phase 4 for ACC
evidence, rollback summary, and Chinese delivery feedback. The
`STAGE-001..010` batch remains locked from upload.
