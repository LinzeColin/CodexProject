# PFI Big Data Simulator Development Ledger

## Current Status

- product version: 0.1.0
- product version status: provisional
- current phase: A - discovery and baseline
- current gate: GOV-P13-required-passed
- confirmed iteration count: 2
- reconstructed development event count: 1
- current task: GOV-BASELINE-001 / TASK-PFI-A-004 completed
- blockers: calibration/source rationale gaps tracked by `TASK-PFI-B-001` through `TASK-PFI-B-010`

Confirmed iterations are not inferred from commit count. The confirmed iterations in this ledger are the current governance baseline creation event and the validation/promotion event.

## Phase Matrix

| Phase | Name | Status | Evidence |
| --- | --- | --- | --- |
| A | Discovery and baseline | completed | governance registries, validator pass and required promotion in this run |
| B | Model and data specification | blocked | unresolved heuristic calibration/source tasks |
| C | Implementation | completed-existing | existing `qbvs` code; no business behavior changed by this run |
| D | Verification and hardening | completed | project validator passed and focused tests passed |
| E | Delivery and operation | completed | PFI_BIG_DATA_SIMULATOR promoted to required in `governance/projects.yaml` after validation |

## Iteration Record

### ITER-20260620-PFI-001

- date: 2026-06-20
- fact level: EXTRACTED for current code/test evidence, RECONSTRUCTED for scoped git history references
- version before: UNKNOWN standalone VERSION; integration contract 0.1.0
- version after: 0.1.0 provisional
- base commit: 9516776
- result commit: PENDING
- task IDs: GOV-BASELINE-001, TASK-PFI-A-001, TASK-PFI-A-002
- objective: establish first auditable PFI/大数据模拟器 governance baseline without changing runtime behavior
- assumptions: see `model_registry.yaml` ASM-001 through ASM-008
- files read: README.md, AGENTS.md, HANDOFF.md, BACKUP_MANIFEST.md, integration/handshake contracts, targeted qbvs source and tests, scoped git log
- files changed: PFI governance docs/registries, README governance entry, VERSION, CHANGELOG; governance/projects.yaml after P13
- model changes: governance documentation only; no runtime model behavior changed
- parameter changes: governance documentation only; no active runtime parameter values changed
- commands: PENDING validation commands in P12
- test results: PENDING
- successes: 15 active model/rule/gate groups and 213 active parameters mapped with stable IDs
- failures: calibration evidence is unresolved for several heuristic constants and thresholds
- decisions: use integration contract 0.1.0 as provisional product version; do not create legacy Chinese index files because none existed in this project path
- remaining risks: large historical run artifacts are intentionally excluded from this governance-only audit; provider/live account checks are not run
- rollback: remove PFI/大数据模拟器/docs/governance, README governance entry, VERSION, CHANGELOG, and reset governance/projects.yaml PFI_BIG_DATA_SIMULATOR ci_mode to advisory
- next step: run P12 validation and then P13 promotion if clean

### ITER-20260620-PFI-002

- date: 2026-06-20
- fact level: EXTRACTED
- version before: 0.1.0 provisional
- version after: 0.1.0 provisional
- base commit: 9516776
- result commit: PENDING
- task IDs: TASK-PFI-A-002, TASK-PFI-A-003, TASK-PFI-A-004
- objective: validate the PFI/大数据模拟器 governance baseline and promote the project from advisory to required without runtime behavior changes
- assumptions: governance-only changes do not alter QBVS/PFI model/runtime behavior
- files read: PFI governance files, focused PFI test module, `governance/projects.yaml`
- files changed: PFI governance docs/registries and `governance/projects.yaml` PFI_BIG_DATA_SIMULATOR `ci_mode`
- model changes: documentation-only; no runtime model behavior changed
- parameter changes: documentation-only; no active runtime parameter values changed
- commands: `python3 scripts/validate_project_governance.py --project 'PFI/大数据模拟器'`; `PYTHONPATH=. python3 -m pytest tests/test_core.py -q`; `python3 scripts/validate_project_governance.py --all`
- test results: project validator exit 0 with errors 0 warnings 0; focused tests exit 0 with 32 passed in 5.76s; all-project validator exit 0 with 17 advisory warnings for EEI and Serenity-Alipay
- successes: PFI_BIG_DATA_SIMULATOR required validator passed and project was promoted to required
- failures: no focused test failures in this run
- decisions: record large historical runtime artifacts as out of scope for this governance-only migration
- remaining risks: heuristic calibration/source evidence and provider/account-level validations remain blocked B-stage tasks
- rollback: reset PFI_BIG_DATA_SIMULATOR `ci_mode` to advisory and revert PFI governance file changes from this run
- next step: resolve P20 hotfix/rollback blocker because no incident variables were supplied

## Reconstructed Development Events

Scoped git history reviewed with `git log --max-count=50 -- PFI/大数据模拟器`. Visible path commits are treated as RECONSTRUCTED development events only, not confirmed iterations:

- 9ce4336 Back up QBVS as PFI big data simulator

## Unknown Historical Periods

- Work before backup into this monorepo path is UNKNOWN unless supported by durable records outside this scoped audit.
- Prior standalone QBVS iterations are not counted as confirmed iterations in this baseline.
