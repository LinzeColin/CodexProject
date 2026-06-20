# OpenAIDatabase Development Ledger

## Current Status

- product version: 0.1.0
- product version status: provisional
- current phase: E - governance required baseline
- current gate: GOV-G4-OPENAIDATABASE-REQUIRED
- confirmed iterations: 1
- reconstructed development events: 15
- current task: GOV-BASELINE-001
- blockers: calibration evidence for heuristic weights is UNKNOWN and tracked by `TASK-OAI-B-001`

Confirmed iterations are not inferred from commit count. The only confirmed
iteration in this ledger is the current governance baseline run.

## Phase Matrix

| Phase | Name | Status | Evidence |
| --- | --- | --- | --- |
| A | Discovery and baseline | completed | `MODEL_SPEC.md`, registries, scoped git log |
| B | Model and data specification | blocked | `TASK-OAI-B-001` calibration evidence gap |
| C | Implementation | completed | Existing scripts and app implementation, no business code changed by this run |
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
