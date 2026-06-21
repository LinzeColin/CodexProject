# OpenAIDatabase Development Ledger

## Current Status

- product version: 0.2.0
- product version status: provisional
- current phase: C - personalization architecture
- current gate: TASK-OAI-C-002-PERSONALIZATION-ARCHITECTURE
- confirmed iterations: 4
- reconstructed development events: 15
- current task: TASK-OAI-C-002
- blockers: calibration evidence for heuristic weights is UNKNOWN and tracked by `TASK-OAI-B-001`

Confirmed iterations are not inferred from commit count. This ledger currently
records four confirmed iterations: the baseline run and three TASK-OAI-C-002
follow-up governance and personalization hardening runs.

## Phase Matrix

| Phase | Name | Status | Evidence |
| --- | --- | --- | --- |
| A | Discovery and baseline | completed | `MODEL_SPEC.md`, registries, scoped git log |
| B | Model and data specification | blocked | `TASK-OAI-B-001` calibration evidence gap |
| C | Implementation | completed | Existing app implementation plus TASK-OAI-C-002 personalization architecture, route, export, evaluation harness, and non-empty four-category run-log evidence |
| D | Verification and hardening | planned | Focused tests run in this baseline; full app/deploy acceptance remains planned |
| E | Delivery and operation | completed for governance baseline | OpenAIDatabase project validator passed and `governance/projects.yaml` ci_mode is required |

## Iteration Record

### ITER-20260620-OAI-001

- date: 2026-06-20
- fact level: EXTRACTED for current file evidence, RECONSTRUCTED for git history references
- version before: UNKNOWN root product version; Memory Atlas package version 0.1.0
- version after: 0.1.0 provisional
- base commit: 9516776
- result commit: PENDING
- task IDs: GOV-BASELINE-001, TASK-OAI-A-001, TASK-OAI-A-002, TASK-OAI-A-003, TASK-OAI-A-004
- objective: establish the first auditable governance baseline for OpenAIDatabase without changing model runtime logic
- assumptions: see `model_registry.yaml` ASM-001 through ASM-006
- files read: `README.md`, `AGENTS.md`, `功能清单`, `开发记录`, `模型参数文件`, `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`, `config/data_sources/source_registry.json`, `config/memory_schema.json`, targeted scripts and tests, scoped git log
- files changed: `OpenAIDatabase/docs/governance/*`, `OpenAIDatabase/VERSION`, `OpenAIDatabase/CHANGELOG.md`, legacy governance entry files, `OpenAIDatabase/README.md`, `governance/projects.yaml`
- model changes: governance documentation only; no runtime model behavior changed
- parameter changes: governance documentation only; no active runtime parameter values changed
- commands: `python scripts/validate_project_governance.py --project OpenAIDatabase`; `python3 -m py_compile skills/openai-memory-analysis/scripts/openai_memory_analysis.py scripts/build_memory_atlas_data.py scripts/sync_codex_memory_data.py scripts/audit_memory_atlas_release.py`; `python3 -m unittest tests.test_openai_memory_analysis tests.test_memory_atlas_data tests.test_codex_memory_sync tests.test_memory_atlas_release_audit -q`; `python scripts/validate_project_governance.py --all`; `git diff --check`
- test results: project validator exit 0 with errors 0 warnings 0; py_compile exit 0; unittest exit 0 with 11 tests OK; global validator exit 0 with advisory warnings only for unmigrated projects; git diff check exit 0
- successes: 10 active deterministic models and 82 parameters mapped with stable IDs; focused tests passed
- failures: no calibration evidence for heuristic weights found
- decisions: keep package product version 0.1.0 as provisional; keep old files as indexes
- remaining risks: full app/deploy/browser acceptance not rerun in this governance-only pass
- rollback: remove this project's `docs/governance` baseline, restore legacy files, reset `VERSION` and `CHANGELOG.md`, and change `governance/projects.yaml` OpenAIDatabase ci_mode back to advisory
- next step: GOV-G4-FIFA-BASELINE-001

### ITER-20260621-OAI-001

- date: 2026-06-21
- fact level: EXTRACTED
- version before: 0.1.0 provisional
- version after: 0.2.0 provisional
- base commit: 71a697e
- result commit: PENDING
- task IDs: TASK-OAI-C-002
- objective: add GitHub-backed OpenAIDatabase personal context architecture for three-layer sources, generated ChatGPT/Codex exports, Codex config, on-demand routing, evaluation harness, and four run-log categories
- assumptions: see `model_registry.yaml` ASM-001, ASM-004, ASM-007
- files read: `OpenAIDatabase/README.md`, `OpenAIDatabase/AGENTS.md`, existing config/scripts/tests/governance files, `data/derived/profile/CORE_PROFILE.md`
- files changed: `OpenAIDatabase/config/context_sources/*`, `OpenAIDatabase/config/codex/*`, `OpenAIDatabase/config/evaluation/*`, `OpenAIDatabase/docs/PERSONAL_CONTEXT_ARCHITECTURE.md`, `OpenAIDatabase/context/*`, `OpenAIDatabase/scripts/build_personalization_exports.py`, `OpenAIDatabase/scripts/route_agent_resources.py`, `OpenAIDatabase/scripts/evaluate_personalization_context.py`, `OpenAIDatabase/scripts/sync_codex_memory_data.py`, `OpenAIDatabase/tests/test_personalization_architecture.py`, `OpenAIDatabase/data/derived/personalization/*`, `OpenAIDatabase/data/run_logs/*`, governance registries, `VERSION`, `CHANGELOG.md`, `README.md`, `AGENTS.md`
- model changes: added MOD-011 personalization export and resource routing
- parameter changes: added PARAM-083 through PARAM-092
- commands: `python3 scripts/build_personalization_exports.py --database-dir .`; `python3 scripts/route_agent_resources.py --database-dir . --intent startup`; `python3 scripts/evaluate_personalization_context.py --database-dir .`; `python3 -m py_compile scripts/build_personalization_exports.py scripts/route_agent_resources.py scripts/evaluate_personalization_context.py scripts/sync_codex_memory_data.py scripts/build_agent_context_pack.py`; `python3 -m unittest tests.test_personalization_architecture -q`; `python3 -m unittest discover -s tests -p "test_*.py" -q`; `python3 scripts/validate_project_governance.py --all`; `git diff --check`
- test results: export PASS; route PASS; evaluation PASS with failures empty; py_compile exit 0; personalization architecture unittest exit 0 with 2 tests OK; OpenAIDatabase unittest discover exit 0 with 32 tests OK; governance --all exit 0 errors 0 warnings 0; git diff --check exit 0
- successes: generated ChatGPT/Codex personalization exports and machine export; recorded export/evaluation run logs; added focused tests; project and root governance validators pass
- failures: none observed before final validation
- decisions: bump provisional product version to 0.2.0 for backward-compatible personalization architecture capability
- remaining risks: evaluation pattern scan is not a full secret scanner; full Memory Atlas app/browser/deploy acceptance remains TASK-OAI-D-001
- rollback: revert TASK-OAI-C-002 commit and restore VERSION, CHANGELOG, and governance entries to 0.1.0
- next step: run focused validation and push branch to GitHub

### ITER-20260621-OAI-002

- date: 2026-06-21
- fact level: EXTRACTED
- version before: 0.2.0 provisional
- version after: 0.2.0 provisional
- base commit: 40e0a72
- result commit: PENDING
- task IDs: TASK-OAI-C-002
- objective: make project `AGENTS.md` concise while preserving detailed OpenAIDatabase rules through canonical document references
- assumptions: the detailed durable rules already live in `docs/PERSONAL_CONTEXT_ARCHITECTURE.md`, `docs/USER_REQUIREMENTS.md`, config contracts, and governance files
- files read: `OpenAIDatabase/AGENTS.md`, `OpenAIDatabase/docs/PERSONAL_CONTEXT_ARCHITECTURE.md`
- files changed: `OpenAIDatabase/AGENTS.md`, `OpenAIDatabase/docs/governance/DEVELOPMENT_LEDGER.md`, `OpenAIDatabase/docs/governance/development_events.jsonl`
- model changes: none
- parameter changes: none
- commands: `python3 scripts/evaluate_personalization_context.py --database-dir .`; `python3 -m unittest tests.test_personalization_architecture -q`; `python3 scripts/validate_project_governance.py --project OpenAIDatabase`; `git diff --check`
- test results: evaluation PASS with failures empty; personalization architecture unittest exit 0 with 2 tests OK; project governance validator exit 0 errors 0 warnings 0; git diff --check exit 0
- successes: reduced AGENTS to startup, canonical contracts, sync requirement, hard boundaries, and minimum validation
- failures: none observed before validation
- decisions: keep product version at 0.2.0 because this is documentation consolidation only
- remaining risks: if future agents ignore referenced documents, they may miss detailed Memory Atlas visual rules
- rollback: revert this AGENTS simplification commit
- next step: push AGENTS simplification follow-up to GitHub

### ITER-20260621-OAI-003

- date: 2026-06-21
- fact level: EXTRACTED
- version before: 0.2.0 provisional
- version after: 0.2.0 provisional
- base commit: 4213f88
- result commit: PENDING
- task IDs: TASK-OAI-C-002
- objective: close the four-category run-log evidence gap by recording a redacted sync baseline and requiring each configured run-log category to contain JSONL records
- assumptions: a sync baseline can truthfully record `NOT_RUN` when raw local session re-ingest is intentionally out of scope
- files read: `OpenAIDatabase/data/run_logs/*`, `OpenAIDatabase/scripts/evaluate_personalization_context.py`, `OpenAIDatabase/tests/test_personalization_architecture.py`
- files changed: `OpenAIDatabase/data/run_logs/sync_runs/2026-06-21.jsonl`, `OpenAIDatabase/data/run_logs/evaluation_runs/2026-06-21.jsonl`, `OpenAIDatabase/scripts/evaluate_personalization_context.py`, `OpenAIDatabase/docs/governance/DEVELOPMENT_LEDGER.md`, `OpenAIDatabase/docs/governance/development_events.jsonl`, `OpenAIDatabase/docs/governance/delivery_tasks.yaml`, `OpenAIDatabase/docs/governance/TRACEABILITY_MATRIX.csv`, `OpenAIDatabase/docs/governance/VERSION_MATRIX.yaml`, `OpenAIDatabase/CHANGELOG.md`
- model changes: none
- parameter changes: none
- commands: `python3 scripts/evaluate_personalization_context.py --database-dir .`; `python3 -m unittest tests.test_personalization_architecture -q`; `python3 scripts/validate_project_governance.py --project OpenAIDatabase`; `python3 scripts/validate_project_governance.py --all`
- test results: evaluation PASS with failures empty and `run_log_records` included; personalization architecture unittest exit 0 with 2 tests OK; project governance validator exit 0 errors 0 warnings 0; all-project governance validator exit 0 errors 0 warnings 0
- successes: all four run-log categories now contain JSONL records; evaluator detects missing log records instead of accepting empty directories
- failures: none observed in focused validation
- decisions: keep product version at 0.2.0 because this is evaluation evidence hardening, not a new product capability
- remaining risks: the `sync_runs` baseline is `NOT_RUN`; a future real sync must append PASS/FAIL evidence after reading local Codex session data
- rollback: revert the sync-log baseline and evaluator hardening commit
- next step: run focused validation and push follow-up to GitHub

## Reconstructed Development Events

Scoped git history reviewed with:

```bash
git log --max-count=50 --date=short --pretty=format:'%h %ad %s' -- OpenAIDatabase
```

The 15 visible path commits from 2026-06-19 through 2026-06-20 are treated as
RECONSTRUCTED development events only, not confirmed iterations.

## Unknown Historical Periods

- Work before the monorepo import on 2026-06-19 is not reconstructable from the scoped path log in this checkout.
- Earlier standalone repository iterations, if any, are UNKNOWN unless supported by durable records outside this scoped audit.
