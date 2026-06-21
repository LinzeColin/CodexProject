# FIFA Development Ledger

fact_level: EXTRACTED
product_version: 0.1.0
current_phase: B
current_gate: GOV-SEMANTIC-FIFA-in-progress
confirmed_iteration_count: 2
reconstructed_event_count: 4
current_task: GOV-SEMANTIC-FIFA-001 in_progress
blockers: TASK-FIFA-B-001, TASK-FIFA-B-002, TASK-FIFA-C-001, TASK-FIFA-C-002, TASK-FIFA-D-001, TASK-FIFA-D-002, TASK-FIFA-E-001, TASK-FIFA-E-002

## Current Status

- Product version: `0.1.0` (EXTRACTED from `FIFA/tab-research-pipeline/package.json`)
- Governance spec version: `1.0.0`
- Confirmed iterations: `2`
- Reconstructed development events: `4`
- Unknown historical periods: pre-monorepo project work before the available scoped Git log cannot be converted into confirmed iterations.
- Business behavior delta: none in this governance baseline.

## Phase Matrix

| Phase | Name | Status | Evidence |
| --- | --- | --- | --- |
| A | Discovery and baseline | completed | `TASK-FIFA-A-001` |
| B | Model and data specification | in_progress | `GOV-SEMANTIC-FIFA-001`, `TASK-FIFA-B-001`, `TASK-FIFA-B-002` |
| C | Implementation | blocked | `TASK-FIFA-C-001`, `TASK-FIFA-C-002` require authorized/manual data paths |
| D | Verification and hardening | blocked | `TASK-FIFA-D-001`, `TASK-FIFA-D-002` require private snapshot and manual signature |
| E | Delivery and operation | blocked | `TASK-FIFA-E-001`, `TASK-FIFA-E-002` |

## Iteration Records

### ITER-20260621-FIFA-001

- Date: 2026-06-21
- Fact level: EXTRACTED
- Version before: 0.1.0
- Version after: 0.1.0
- Base commit: 92b2969822a267d8a72d8d3c484e25f55858c8b5
- Result commit: PENDING
- Task IDs: GOV-SEMANTIC-FIFA-001, ACC-SEMANTIC-FIFA-001
- Goal: add machine semantic extractor metadata for FIFA active parameters and formula implementation fingerprints without changing runtime behavior or active business values.
- Assumptions: code literals, function defaults, module assignments, regex selectors, and AST fingerprints can be machine-checked; composite rule semantics and multi-field boolean requirements remain human-review-bound under GOV-SEMANTIC-FIFA-001.
- Read files: FIFA governance registries; FIFA tab-research-pipeline odds, model, bankroll, recommendation, raw refresh, live board discovery, safety, provider KPI, provider alternate plan, manual verification, automation candidate, and automation readiness modules; focused test references.
- Modified files: FIFA parameter and formula registries, delivery task ledger, version matrix, development ledger/events, root project metadata, run manifest, generated status pages, and focused governance tests.
- Model changes: no runtime model behavior change; 10 active formulas now include implementation refs, fingerprints, verification commit, verification time, and evidence hash.
- Parameter changes: no runtime behavior change; 91 active parameters now include machine source selectors and 17 active parameters are task-bound HUMAN_REVIEW_REQUIRED.
- Commands: python3 scripts/validate_semantic_extractors.py FIFA; python3 scripts/validate_project_governance.py --project FIFA --semantic; remaining all-project, changed-only, dashboard, governance, and FIFA focused tests are recorded in the delivery task as they complete.
- Test results: semantic extractor exit 0 with 91 parameters and 10 formulas checked; FIFA semantic validator exit 0 with errors 0 warnings 0 at this point in the run.
- Success items: exact active-value drift checks added for machine-extractable FIFA constants; formula implementation fingerprints added for all active formulas; project semantic coverage now task-bound and in_progress.
- Failure items: 17 active parameters are not machine-proved because they encode composite rule semantics, multi-field requirements, or list completeness that requires human review or future extractor support.
- Decisions: keep FIFA semantic coverage in_progress rather than machine_verified until HUMAN_REVIEW_REQUIRED items are resolved.
- Remaining risks: heuristic calibration and curation completeness remain open under TASK-FIFA-B-001 and TASK-FIFA-B-002; semantic proof is structural/AST-based and does not validate betting correctness.
- Rollback: revert this semantic metadata branch; no FIFA runtime code rollback is required.
- Next step: run all-project semantic drift, changed-only sync, focused governance tests, generated status determinism, and FIFA focused checks.

### ITER-20260620-001

- Date: 2026-06-20
- Fact level: EXTRACTED
- Version before: 0.1.0
- Version after: 0.1.0
- Base commit: 9516776
- Result commit: PENDING
- Task IDs: TASK-FIFA-A-001
- Goal: Establish the first auditable FIFA governance baseline and promote FIFA governance CI mode to required after validation.
- Assumptions: Research-only safety boundary remains unchanged; no business logic changes are allowed.
- Read files: `FIFA/README.md`, `FIFA/AGENTS.md`, `FIFA/docs/HANDOFF.md`, `FIFA/docs/DEVELOPMENT_STATUS.md`, `FIFA/功能清单`, `FIFA/开发记录`, `FIFA/模型参数文件`, selected `FIFA/tab-research-pipeline` model/gate modules, selected tests, and scoped Git log.
- Modified files: `FIFA/docs/governance/*`, `FIFA/VERSION`, `FIFA/CHANGELOG.md`, `FIFA/README.md`, legacy Chinese governance entry files, and `governance/projects.yaml`.
- Model changes: Governance documentation only; runtime model behavior unchanged.
- Parameter changes: Governance documentation only; active parameter values are extracted from current code.
- Commands: `python scripts/validate_project_governance.py --project FIFA`; `python3 scripts/validate_project_governance.py --project FIFA`; `python3 -m py_compile run_daily_report.py scripts/tab_fifa_app_server.py tests/test_pipeline.py`; `bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh`; `node --check scripts/refresh_tab_readonly.mjs`; `node --check scripts/discover_tab_live_boards.mjs`; `python3 -m unittest tests.test_pipeline -q`.
- Test results: `python` binary unavailable exit 127; project validator with `python3` exit 0; syntax checks exit 0; real-HOME full suite exit 1 because external Downloads entry is missing; temp-HOME fixture full suite with original user site-packages exit 0 and ran 206 tests OK.
- Success items: model/formula/parameter registries created; legacy softmax model separated as deprecated; FIFA project validator passed; focused checks passed with isolated external Downloads fixture.
- Failure items: statistical calibration evidence for many heuristic thresholds was not found.
- Decisions: use machine registries as the single source of truth; Markdown is explanatory/index layer.
- Remaining risks: heuristic thresholds and curation maps lack auditable calibration records.
- Rollback: revert the FIFA governance files and reset FIFA `ci_mode` to `advisory` in `governance/projects.yaml`.
- Next step: Run validator and focused tests, then update completed evidence.

## Reconstructed Events

Scoped Git history (`git log --max-count=50 -- FIFA`) contains four monorepo events. These are not counted as confirmed iterations:

- 7fffb44 Initialize Codex project hub.
- 68e6359 Remove project submodule pointers before monorepo import.
- 80cc573 Merge commit as `FIFA`.
- 7a6f738 Add project continuity records.
