# IDS v0.1 STAGE-001 Phase 3 Validation Scan

## Identity

- Stage: `STAGE-001`
- Phase: `Phase 3`
- Task ID: `IDS-V0_1-STAGE001-P3`
- Acceptance ID: `ACC-STAGE-001`
- Stage title: `IDS 产品命名合同`
- Recorded at UTC: `2026-07-02T04:47:54Z`

## Goal

Verify that active customer-visible product surfaces no longer use old product
names, classify remaining legacy aliases, check README/governance/test/script
references, and confirm this stage did not touch raw data, secrets, or local
runtime output directories.

## Scan Scope

- Scope: tracked files under `KM_IDSystem/`.
- Excluded: unrelated projects, dependency folders, runtime output folders,
  generated reports, databases, and binary assets.
- Search families: `Wuhan Kaiming OpMe`, `武汉开明智能工业运维助手`,
  `wuhan-kaiming-assistant`, `OpMe_System`, `opme-system`, word-boundary
  `OpMe`/`OPME`/`opme`, `wuhan_kaiming`, `Wuhan Kaiming`, `武汉开明`, and
  `开明智能`.

## Results

| Metric | Result |
|---|---:|
| project files scanned | 86 |
| classified legacy hits | 560 |
| active blockers | 0 |
| review items | 1 |

## Classification

- Legacy aliases in `README.md`, `docs/HANDOFF.md`, and
  `docs/CLEANUP_POLICY.md` are explicitly marked as legacy, compatibility,
  history, or rollback context.
- Legacy references in `CHANGELOG.md`, cleanup reports, older governance
  ledgers, and pursuing-goal provenance files are historical evidence and are
  not current product display names.
- `OPME_*` environment variables, `opme-test` temporary test database names,
  and `data/wuhan_kaiming.sqlite` are retained as compatibility/runtime
  identifiers and documented as legacy where they appear in formal docs.
- `OpMeIcon.*` remains a legacy asset filename used by the macOS icon pipeline;
  it is not a visible product name.
- The only review item is
  `KM_IDSystem/backend/app/services/model_router.py:10`, where the system prompt
  references `武汉开明高科技有限公司`. This is classified as company/source
  context rather than a product display name. It is not a blocker for
  `ACC-STAGE-001`; a future owner branding decision can decide whether to
  replace company identity in prompts.

## Exception Fixes During Phase 3

The scan also checked script and launcher references. Two active-entry issues
were fixed in this phase:

1. `KM_IDSystem/app_bundle/native_launcher.c` no longer hardcodes the stale
   `/Users/linzezhang/Documents/Codex/2026-06-04/...` checkout. It now receives
   `IDS_PROJECT_DIR`, `IDS_RUN_SCRIPT`, and `IDS_LOG_FILE` from
   `scripts/build_app_bundle.sh` at compile time.
2. `KM_IDSystem/scripts/stop_local_services.sh` is executable in the git index
   so lifecycle tests and installed launchers can execute it directly.

## Validation Results

- Red lifecycle test before repair: failed on stale native launcher path and
  direct `stop_local_services.sh` permission.
- Green lifecycle test after repair:
  `python3 -m unittest KM_IDSystem/backend/tests/test_lifecycle_contract.py -q`
  ran 5 tests and returned `OK`.
- Focused naming contract test:
  `python3 -m unittest KM_IDSystem/backend/tests/test_stage001_naming_contract.py -q`
  ran 2 tests and returned `OK`.
- Project-file legacy scan: 86 files scanned, 560 classified legacy hits,
  1 non-blocking review item, and `active blockers = 0`.
- Script and native launcher syntax checks passed with `bash -n` for launcher
  scripts and `clang -fsyntax-only` for `app_bundle/native_launcher.c`.
- `check-render --project KM_IDSystem`: passed with `drift_count=0`.
- Stage001 Phase3 marker check, changed-scope check, and `git diff --check`:
  passed.
- `validate --project KM_IDSystem --semantic`: blocked by the existing sparse
  worktree omission of root governance schemas/workflows/hooks and unrelated
  registered project directories. No unrelated project expansion was performed.

## Data And Secret Boundary

No raw material, `00_ORIGINAL_RAW_DATA`, secrets, local runtime database,
`data/`, `reports/`, `outputs/`, dependency folder, or generated report artifact
was modified or committed by this phase.

## Decision

STAGE-001 Phase 3 passes with one non-blocking company-context review item.
The next run may enter STAGE-001 Phase 4 to prepare the ACC evidence, rollback
summary, and Chinese delivery feedback. The `STAGE-001..STAGE-010` batch still
must not be pushed until all 10 stages are complete, reviewed, and repaired.
