# EVA_OS Development Ledger

## Current Status

- product version: 0.1.0
- product version status: provisional
- current phase: A - discovery and baseline
- current gate: GOV-P13-required-passed
- confirmed iteration count: 2
- reconstructed development event count: 4
- current task: GOV-BASELINE-001 / TASK-EVA-A-004 completed
- blockers: calibration/source rationale gaps tracked by `TASK-EVA-B-001` through `TASK-EVA-B-008`

Confirmed iterations are not inferred from commit count. The confirmed iterations in this ledger are the current governance baseline creation event and the validation/promotion event.

## Phase Matrix

| Phase | Name | Status | Evidence |
| --- | --- | --- | --- |
| A | Discovery and baseline | completed | governance registries, validator pass and required promotion in this run |
| B | Model and data specification | blocked | unresolved heuristic calibration/source tasks |
| C | Implementation | completed-existing | existing EVA_OS code; no business behavior changed by this run |
| D | Verification and hardening | completed-with-env-blocker | validator passed; focused executable subset passed; `tests/test_strategy_templates.py` blocked by missing local `docx` dependency |
| E | Delivery and operation | completed | EVA_OS promoted to required in `governance/projects.yaml` after validation |

## Iteration Record

### ITER-20260620-EVA-001

- date: 2026-06-20
- fact level: EXTRACTED for current code/test evidence, RECONSTRUCTED for scoped git history references
- version before: UNKNOWN standalone VERSION; pyproject 0.1.0
- version after: 0.1.0 provisional
- base commit: 9516776
- result commit: PENDING
- task IDs: GOV-BASELINE-001, TASK-EVA-A-001, TASK-EVA-A-002
- objective: establish first auditable EVA_OS governance baseline without changing runtime behavior
- assumptions: see `model_registry.yaml` ASM-001 through ASM-007
- files read: README.md, AGENTS.md, HANDOFF.md, PLANS.md, CODEX_TASK_PACK.md, pyproject.toml, legacy Chinese governance files, targeted model/rule/gate source and tests, scoped git log
- files changed: EVA_OS governance docs/registries, README governance entry, VERSION, CHANGELOG, legacy index files; governance/projects.yaml after P13
- model changes: governance documentation only; no runtime model behavior changed
- parameter changes: governance documentation only; no active runtime parameter values changed
- commands: PENDING validation commands in P12
- test results: PENDING
- successes: 16 active model/rule/gate groups and 189 active parameters mapped with stable IDs
- failures: calibration evidence is UNKNOWN for several heuristic constants and thresholds
- decisions: use pyproject 0.1.0 as provisional product version; keep legacy files as indexes
- remaining risks: full macOS acceptance and live provider checks are not part of this governance-only run
- rollback: remove EVA_OS/docs/governance, restore legacy files/README/VERSION/CHANGELOG, and reset governance/projects.yaml EVA_OS ci_mode to advisory
- next step: run P12 validation and then P13 promotion if clean

### ITER-20260620-EVA-002

- date: 2026-06-20
- fact level: EXTRACTED
- version before: 0.1.0 provisional
- version after: 0.1.0 provisional
- base commit: 9516776
- result commit: PENDING
- task IDs: TASK-EVA-A-002, TASK-EVA-A-003, TASK-EVA-A-004
- objective: validate the EVA_OS governance baseline and promote the project from advisory to required without runtime behavior changes
- assumptions: governance-only changes do not alter EVA_OS model/runtime behavior
- files read: EVA_OS governance files, focused EVA_OS test modules, `governance/projects.yaml`
- files changed: EVA_OS governance docs/registries and `governance/projects.yaml` EVA_OS `ci_mode`
- model changes: documentation-only; no runtime model behavior changed
- parameter changes: documentation-only; no active runtime parameter values changed
- commands: `python3 scripts/validate_project_governance.py --project EVA_OS`; `PYTHONPATH=src python3 -m pytest ... -q`; `python3 scripts/validate_project_governance.py --all`
- test results: project validator exit 0 with errors 0 warnings 0; focused executable subset exit 0 with 99 passed and 1 warning; `tests/test_strategy_templates.py` collection blocked by missing local `docx`; all-project validator exit 0 with 29 advisory warnings for unmigrated projects
- successes: EVA_OS required validator passed and project was promoted to required
- failures: local environment lacks `docx`, so one focused test module could not be collected
- decisions: record the dependency blocker as evidence rather than installing dependencies or modifying business code
- remaining risks: full macOS acceptance, provider checks and the `docx`-dependent strategy review export test remain outside this governance-only run
- rollback: reset EVA_OS `ci_mode` to advisory and revert EVA_OS governance file changes from this run
- next step: start PFI_BIG_DATA_SIMULATOR P10 read-only audit

## Reconstructed Development Events

Scoped git history reviewed with `git log --max-count=50 -- EVA_OS`. Visible path commits are treated as RECONSTRUCTED development events only, not confirmed iterations:

- 7a6f738 Add project continuity records
- 0d0f9fd Merge commit fc5428386b3d3f396f69b3dc637574183a99ba1d as EVA_OS
- 68e6359 Remove project submodule pointers before monorepo import
- 7fffb44 Initialize Codex project hub

## Unknown Historical Periods

- Work before the monorepo import is UNKNOWN unless supported by durable records outside this scoped audit.
- Prior standalone EVA_OS iterations are not counted as confirmed iterations in this baseline.
