# IDS v0.1 STAGE-005 Phase 2 Governance Regression Slice

## Identity

- Stage: `STAGE-005`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE005-P2`
- Acceptance ID: `ACC-STAGE-005`
- Stage title: `仓库治理回归验证`
- Recorded at UTC: `2026-07-02T06:47:25Z`

## Goal

Create the smallest repeatable governance-regression validation slice for
STAGE-005. This phase adds a deterministic validator and focused unittest
coverage for README, governance, scripts, tests, path references, batch-upload
lock, event JSONL, accepted-name preservation, and sparse-worktree diagnostic
classification.

This phase does not modify runtime code, does not start services, does not
install dependencies, does not scan unrelated projects, and does not enter
Phase 3.

## Implemented Slice

Phase 2 added:

- `validate_stage005_governance_regression.py`
- `tests/test_stage005_governance_regression.py`
- this Phase 2 evidence file
- governance, batch-lock, events, and rendered Chinese owner entry updates

The validator checks:

- required README, handoff, governance, stage, script, validator, and test
  files exist;
- `events.jsonl` parses and required Stage 1-5 events are present;
- batch upload remains locked and STAGE-005 points to Phase 2;
- roadmap points to `IDS-STAGE005-P2` and next gate `IDS-STAGE005-P3-GATE`;
- no tracked runtime-output files exist under `data/`, `reports/`, `outputs/`,
  `.venv/`, `frontend/node_modules/`, or `frontend/dist/`;
- changed paths remain inside the allowed Phase 2 governance and rendered-owner
  paths;
- owner-facing current product name and legacy-alias policy are still present;
- `IDS / Industrial Data System`, `ProductMetaDatabase`, and
  `FinanceMetaDatabase` remain accepted names in tracked text;
- sparse-worktree semantic validation errors can be classified separately from
  real `KM_IDSystem/` regressions.

## TDD Evidence

Red:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
- Result before implementation: 2 expected failures because
  `validate_stage005_governance_regression.py` did not exist.

Green:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
- Result after implementation: 2 tests returned `OK`.
- Command:
  `Codex bundled python -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- Result after implementation: `valid=true`, `issues=[]`,
  `missing_required_files=[]`, `event_json_errors=[]`,
  `forbidden_changed_paths=[]`, `tracked_forbidden_runtime_files=[]`, and
  `unexpected_changed_paths=[]`.

## Sparse-Worktree Boundary

STAGE-005 explicitly distinguishes:

- sparse-worktree diagnostics, such as missing root governance schemas,
  `.github` workflows, `.agents` skills, `.codex` hooks, or registered
  unrelated project directories;
- real `KM_IDSystem/` regressions, such as missing
  `KM_IDSystem/docs/governance/roadmap.yaml`.

Sparse diagnostics remain reported as validation limitations. They must not be
fixed by expanding unrelated projects during this stage.

## Boundary

No backend route, frontend route, launcher behavior, runtime database, schema
migration, worker, external API path, raw-material copy, generated data,
report output, dependency folder, GitHub push, PR, or merge was added.

No `data/`, `reports/`, `outputs/`, `.venv/`, `frontend/node_modules/`, or
`frontend/dist/` files were added to tracking.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE005-P2` commit. This
removes the validator, unittest, Phase 2 evidence, and governance status
updates. Because this phase is governance/validator-only, rollback does not
require data cleanup, schema rollback, service restart, dependency
restoration, report cleanup, runtime file restore, GitHub PR cleanup, or
changes to STAGE-001 through STAGE-004 evidence.

## Decision

STAGE-005 Phase 2 is locally satisfied when the focused unittest, validator,
render check, marker/scope checks, `git diff --check`, and sparse diagnostic
validation complete. The next run may enter STAGE-005 Phase 3 for broader
README/governance/script/test/path-reference and abnormal-scenario validation.
The `STAGE-001..010` batch remains locked from upload.
