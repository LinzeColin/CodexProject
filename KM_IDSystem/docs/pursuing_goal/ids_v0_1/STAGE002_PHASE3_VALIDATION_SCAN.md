# IDS v0.1 STAGE-002 Phase 3 Validation Scan

## Identity

- Stage: `STAGE-002`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE002-P3`
- Acceptance ID: `ACC-STAGE-002`
- Stage title: `新建 ProductMetaDatabase`
- Recorded at UTC: `2026-07-02T05:22:02Z`

## Goal

Validate the `ProductMetaDatabase` skeleton created in Phase 2. This phase
checks reference integrity, legacy alias classification, raw-material and
secret boundaries, runtime-output boundaries, and whether any active blocker
remains before the Stage 002 closeout phase.

## Validation Scope

Included:

- tracked files under `KM_IDSystem/`;
- `KM_IDSystem/product_meta_database/` JSON contracts, README, validator, and
  test file;
- Stage 002 governance artifacts under
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/`;
- `KM_IDSystem/docs/governance/roadmap.yaml` and `events.jsonl`.

Excluded:

- unrelated projects outside `KM_IDSystem/`;
- dependency folders, caches, local runtime databases, generated reports, and
  generated output folders;
- real raw materials and any external-drive data root.

## ProductMetaDatabase Contract Validation

Commands run:

- `Codex bundled python -B -m unittest KM_IDSystem/product_meta_database/tests/test_contract.py -q`
- `Codex bundled python -B KM_IDSystem/product_meta_database/validate_product_meta_database.py`

Results:

- unittest ran 2 tests and returned `OK`;
- validator returned `valid=true`;
- validator returned `issues=[]`;
- `external_api_policy=denied`;
- `raw_material_policy=forbidden`;
- `forbidden_markers=[]`;
- `forbidden_runtime_paths_present=false`;
- contract references resolved for:
  - `product_metadata_schema`;
  - `product_manifest_template`;
  - `governance_rules`;
  - `taskpack_input`;
- future lineage fields exist for source documents, chunks, evidence refs,
  audit events, index versions, and report snapshots.

## Legacy Alias Scan

Refined project scan used word boundaries for `OpMe`/`OPME`/`opme` so ordinary
words such as `development` are not counted as legacy aliases.

| Metric | Result |
|---|---:|
| classified project text files scanned | 92 |
| classified legacy hits | 529 |
| ProductMetaDatabase legacy hits | 0 |
| non-blocking review items | 1 |
| active blockers | 0 |

The only review item is:

- `KM_IDSystem/backend/app/services/model_router.py:10`, where the system prompt
  references `武汉开明高科技有限公司`.

This remains classified as company/source prompt context rather than a product
display name. It is not a blocker for `ACC-STAGE-002`, and it is unchanged from
the Stage 001 validation classification.

## Secret And Runtime Boundary Scan

The strict secret scan checked credential-like patterns instead of short
substrings that also appear in ordinary identifiers such as `risk-*` CSS class
names.

| Metric | Result |
|---|---:|
| strict secret hits | 0 |
| tracked runtime files under `data/`, `reports/`, `outputs/`, `.venv/`, or `frontend/node_modules/` | 0 |
| forbidden directories under `KM_IDSystem/product_meta_database/` | 0 |

Allowed policy mentions of `00_ORIGINAL_RAW_DATA` remain in governance and
stage-boundary documents as prohibitions, not raw-data references or stored
materials.

## Boundary Checks

- No backend route, frontend route, service launcher, app bundle, runtime DB,
  external API path, schema migration, or worker was added in Phase 3.
- No ProductMetaDatabase contract file points to real raw material storage.
- No `__pycache__` directory remained under `KM_IDSystem/product_meta_database/`
  after validation.
- No GitHub push or PR was performed because the `STAGE-001..010` batch is not
  complete.

## Final Run Checks

- `check-render --project KM_IDSystem`: `drift_count=0`;
- marker and JSONL check: `stage002_phase3_marker_jsonl_ok events=16`;
- changed-scope and `git diff --check`: `changed_scope_ok`;
- full semantic governance validate remains blocked by the known sparse
  worktree omissions: 28 errors for missing root governance schemas,
  workflows/hooks, governance tests, skill/config files, and unrelated
  registered project directories.

## Decision

STAGE-002 Phase 3 passes with one non-blocking company-context review item and
zero active blockers. The next run may enter STAGE-002 Phase 4 for ACC
evidence, rollback summary, and Chinese delivery feedback. The
`STAGE-001..010` batch remains locked from upload.
