# IDS v0.1 STAGE-005 Phase 3 Validation Scan

## Identity

- Stage: `STAGE-005`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE005-P3`
- Acceptance ID: `ACC-STAGE-005`
- Stage title: `仓库治理回归验证`
- Recorded at UTC: `2026-07-02T06:55:42Z`

## Goal

Validate the STAGE-005 governance-regression slice across README, governance,
scripts, tests, path references, customer-visible wording, legacy-name
classification, secret-pattern classification, and local data/output
boundaries.

This phase does not modify runtime product behavior, does not start services,
does not install dependencies, and does not enter Phase 4.

Stop marker: this phase does not enter Phase 4.

## Validation Scope

Included:

- tracked files under `KM_IDSystem/`;
- `README.md` and `docs/HANDOFF.md`;
- `docs/governance/roadmap.yaml` and `docs/governance/events.jsonl`;
- `docs/pursuing_goal/ids_v0_1/` stage contracts, validators, tests, and
  evidence;
- `scripts/*.sh` syntax and tracked script path references;
- active customer-visible surfaces under `frontend/` and `app_bundle/`;
- active backend and script reference context under `backend/app/` and
  `scripts/`.

Excluded:

- unrelated CodexProject projects;
- dependency folders, caches, local runtime databases, generated reports, and
  generated output folders;
- real raw materials and any external-drive data root;
- GitHub push, PR, or merge operations.

## Validator Compatibility Update

Phase 3 updated the STAGE-005 validator and unittest so the validator accepts
state after Phase 2 has completed and the active stage has advanced to Phase 3.

TDD evidence:

- Red command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
- Red result: 1 expected error because `evaluate_phase_state` did not exist.
- Green command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
- Green result: 3 tests returned `OK`.

This update is validator-only. It does not alter backend, frontend, launcher,
data, report, dependency, or GitHub behavior.

## Governance Regression Validator Results

Commands run:

- `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
- `Codex bundled python -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`

Results before Phase 3 status update:

- unittest ran 3 tests and returned `OK`;
- validator returned `valid=true`;
- validator returned `issues=[]`;
- `missing_required_files=[]`;
- `event_json_errors=[]`;
- `missing_event_ids=[]`;
- `forbidden_changed_paths=[]`;
- `tracked_forbidden_runtime_files=[]`;
- `unexpected_changed_paths=[]`;
- `tracked_km_ids_files=118`.

Governance regression surface counts:

| Surface | Count |
|---|---:|
| README | 1 |
| handoff docs | 1 |
| governance | 16 |
| ids pursuing goal | 37 |
| scripts | 9 |
| backend tests | 4 |
| backend app | 13 |
| frontend | 11 |
| app bundle | 3 |
| ProductMetaDatabase contract | 7 |

Accepted-name preservation counts:

| Accepted name | Hits |
|---|---:|
| `IDS / Industrial Data System` | 46 |
| `ProductMetaDatabase` | 268 |
| `FinanceMetaDatabase` | 124 |

## Customer-Visible And Legacy-Name Scan

The STAGE-004 legacy-name validator was rerun as a regression check.

Results:

- `valid=true`;
- `issues=[]`;
- `files_scanned=113`;
- `legacy_name_hits=1005`;
- `allowed_legacy_context=1005`;
- `active_display_debt=0`;
- `forbidden_changed_paths=[]`.

The active context scan covered tracked files under:

- `KM_IDSystem/frontend/`
- `KM_IDSystem/backend/app/`
- `KM_IDSystem/app_bundle/`
- `KM_IDSystem/scripts/`

Results:

| Metric | Result |
|---|---:|
| active context legacy hits | 7 |
| customer-visible context hits | 0 |
| unclassified active context hits | 0 |
| unclassified customer-visible hits | 0 |

Classified active refs:

- `KM_IDSystem/backend/app/core/config.py:10:legacy_wuhan_snake` is a legacy
  SQLite filename/default path context.
- `KM_IDSystem/backend/app/services/model_router.py:10:legacy_wuhan_cn` is
  company/source prompt context.
- `KM_IDSystem/scripts/build_app_bundle.sh:9:legacy_asset_opmeicon` and
  `KM_IDSystem/scripts/build_app_bundle.sh:53:legacy_asset_opmeicon` are legacy
  asset filename contexts.
- `KM_IDSystem/scripts/generate_app_icon.py:13-15:legacy_asset_opmeicon` are
  legacy asset filename contexts.

No frontend route, app bundle display text, backend API title, or report
display surface was found using old product names as a new formal display
name.

## README, Governance, Script, Test, And Path References

Checks run:

- `bash -n KM_IDSystem/scripts/*.sh`
- `Codex bundled python -B -m py_compile` on STAGE-003, STAGE-004, STAGE-005
  validators and script Python helpers;
- path-reference scan over README, handoff, STAGE-005 contracts, Phase 2
  evidence, and roadmap;
- required file presence scan over README, handoff, governance, STAGE-005
  evidence, validators, tests, scripts, backend tests, and ProductMetaDatabase
  validator.

Results:

| Metric | Result |
|---|---:|
| shell syntax failures | 0 |
| Python compile failures | 0 |
| required missing files | 0 |
| path refs checked | 89 |
| allowed non-tracked boundary refs | 16 |
| allowed evidence line refs | 16 |
| broken path refs | 0 |

The 16 allowed non-tracked refs are forbidden/runtime/dependency boundaries,
glob command patterns, or wildcard contracts such as `data/`, `reports/`,
`outputs/`, `.venv/`, `frontend/node_modules/`, `frontend/dist/`,
`scripts/*.sh`, or the STAGE-005 wildcard contract. The 16 allowed evidence
line refs point to existing files with line-number/classification suffixes.
They are not broken product references and must not be made tracked files.

## Secret And Runtime Boundary Scan

Raw strict secret-pattern scan found 11 pattern hits:

- `KM_IDSystem/backend/app/services/db.py:235`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE002_PHASE4_CLOSEOUT.md:118`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE003_PHASE3_VALIDATION_SCAN.md:102`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE003_PHASE3_VALIDATION_SCAN.md:104`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE3_VALIDATION_SCAN.md:109`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE3_VALIDATION_SCAN.md:113`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE3_VALIDATION_SCAN.md:117`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE3_VALIDATION_SCAN.md:118`
- `KM_IDSystem/product_meta_database/governance_rules/product_metadata_rules.json:36`
- `KM_IDSystem/product_meta_database/governance_rules/product_metadata_rules.json:37`
- `KM_IDSystem/product_meta_database/governance_rules/product_metadata_rules.json:38`

All 11 are classified as SQL field names, policy marker definitions, or
validation-report self-reference. Actual credential hits after classification:
0.

| Metric | Result |
|---|---:|
| raw secret-pattern hits | 11 |
| actual credential hits after classification | 0 |
| tracked files under `data/`, `reports/`, `outputs/`, `.venv/`, `frontend/node_modules/`, or `frontend/dist/` | 0 |

## Boundary Checks

- No README, governance, script, test, or path reference break was found.
- No customer-visible old product display name was found.
- No backend route, frontend route, launcher behavior, runtime database,
  schema migration, worker, external API path, raw-material copy, generated
  data, report output, dependency folder, GitHub push, PR, or merge was added.
- Sparse-worktree semantic validation remains a diagnostic only and must not be
  resolved by expanding unrelated projects during STAGE-005.

## Rollback

Rollback Phase 3 by reverting the local `IDS-V0_1-STAGE005-P3` commit. Because
Phase 3 is validation/governance evidence plus validator compatibility only,
rollback does not require data cleanup, schema rollback, service restart,
dependency restoration, report cleanup, runtime file restore, GitHub PR
cleanup, or changes to STAGE-001 through STAGE-004 evidence.

## Decision

STAGE-005 Phase 3 passes with zero broken path references, zero active display
debt, zero unclassified customer-visible hits, zero actual credential hits, and
zero forbidden tracked runtime-output files. The next run may enter
STAGE-005 Phase 4 for ACC evidence, rollback summary, and Chinese delivery
feedback. The `STAGE-001..010` batch remains locked from upload.
