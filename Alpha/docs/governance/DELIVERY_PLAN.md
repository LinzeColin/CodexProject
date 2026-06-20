# Alpha Delivery Plan

Project: `Alpha`
task_count: 8

## Phase Matrix

| Phase | Name | Status | Tasks |
|---|---|---|---|
| A | Discovery and baseline | completed | `TASK-ALPHA-A-001`..`TASK-ALPHA-A-004` |
| B | Model and data specification | blocked | `TASK-ALPHA-B-001` |
| C | Implementation | planned | `TASK-ALPHA-C-001` |
| D | Verification and hardening | planned | `TASK-ALPHA-D-001` |
| E | Delivery and operation | planned | `TASK-ALPHA-E-001` |

## Acceptance

| Acceptance ID | Task | Requirement | Evidence |
|---|---|---|---|
| ACC-ALPHA-A-001 | TASK-ALPHA-A-001 | P10 audit identifies actual models and safety boundaries without modifying files. | `MODEL_SPEC.md`; `model_registry.yaml`; targeted Alpha evidence |
| ACC-ALPHA-A-002 | TASK-ALPHA-A-002 | P11 migration creates canonical governance files and leaves business code unchanged. | validator exit 0; focused pytest 8 passed |
| ACC-ALPHA-A-003 | TASK-ALPHA-A-003 | P12 verification passes validator and focused tests. | validator exit 0; `git diff --check` exit 0 |
| ACC-ALPHA-A-004 | TASK-ALPHA-A-004 | P13 promotion sets only Alpha enforcement to required after verification. | `governance/projects.yaml` Alpha `ci_mode: required`; `--all` exit 0 |
| ACC-ALPHA-B-001 | TASK-ALPHA-B-001 | Production validation and execution-policy unknowns are resolved or explicitly accepted. | blocked |

## Current Gate

Alpha is required for governance CI, but is not release-ready for live execution. The current governance gate is `GOV-G4-ALPHA-REQUIRED`.

## Rollback

Rollback this governance migration by deleting `Alpha/docs/governance/`, restoring legacy index files, removing `Alpha/VERSION` and `Alpha/CHANGELOG.md`, and reverting Alpha `ci_mode` in `governance/projects.yaml` if promoted.
