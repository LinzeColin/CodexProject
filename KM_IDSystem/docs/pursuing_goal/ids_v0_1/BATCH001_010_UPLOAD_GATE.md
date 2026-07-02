# IDS v0.1 BATCH-001-010 Upload Gate

- Batch ID: `IDS-V0_1-BATCH-001-010`
- Task ID: `IDS-V0_1-BATCH-001-010-UPLOAD-GATE`
- Stage range: `STAGE-001..STAGE-010`
- Acceptance range: `ACC-STAGE-001..ACC-STAGE-010`
- Gate checked at UTC: `2026-07-02T10:29:44Z`
- Target repository: `LinzeColin/CodexProject`
- Target branch: `main`

## Goal

Evaluate whether the completed local `STAGE-001..STAGE-010` batch may be
uploaded to GitHub `main` as one batch. This gate does not start `STAGE-011`
and does not expand the sparse worktree.

## Local Gate Result

| Gate item | Result | Evidence |
|---|---|---|
| Ten-stage completion | Passed. `STAGE-001` through `STAGE-010` each have four completed phases in the batch lock. | `BATCH001_010_UPLOAD_LOCK.yaml` |
| Acceptance status | Passed. `ACC-STAGE-001` through `ACC-STAGE-009` are `local_passed`; `ACC-STAGE-010` is `local_passed_reviewed`. | `BATCH001_010_UPLOAD_LOCK.yaml` |
| Durable evidence files | Passed. All evidence refs listed in the batch lock exist in the sparse worktree. | local evidence-ref check |
| Tenth-stage review | Passed. `STAGE-010` has `STAGE010_STAGE_REVIEW.md` and no runtime code fix was required. | `STAGE010_STAGE_REVIEW.md` |
| Owner render | Passed. Must remain `drift_count=0` before upload. | `scripts/lean_governance.py check-render --project KM_IDSystem` |
| Changed scope | Passed locally before this gate. This gate only touches `KM_IDSystem/` governance/evidence and owner files. | `git status`, changed-scope check |
| GitHub open PR/issue precheck | Passed at gate start. GitHub connector returned no open PRs and no open issues for `LinzeColin/CodexProject`. | GitHub connector search |

## Remote Main Strategy

`origin/main` and the local batch branch have diverged:

- `origin/main` contains 38 commits not in this branch.
- this branch contains 41 batch commits not in `origin/main` before this gate.

Therefore this run must not push `HEAD:main` directly from the diverged branch.
The safe upload strategy is:

1. Push `codex/ids-v0-1-stages-001-010` to GitHub.
2. Open a PR targeting `main`.
3. Merge the PR if GitHub accepts the merge without conflict.
4. Verify no open PRs and no open issues remain after merge.
5. Do not expand sparse checkout or alter unrelated project files locally.

## Validation Plan

Before GitHub upload, run the focused batch validation:

- `python3 -B -m unittest` for STAGE-001 backend naming/lifecycle tests,
  ProductMetaDatabase contract tests, and STAGE-003 through STAGE-010 v0.1
  tests.
- ProductMetaDatabase and STAGE-003/004/005 validators.
- STAGE-010 CLI and scenario smoke.
- bundled Python `scripts/lean_governance.py check-render --project KM_IDSystem`.
- `git diff --check`.
- changed-scope check.
- bundled Python `scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  as a diagnostic only; the known sparse-worktree/root/other-project missing
  errors must not be solved by expanding unrelated projects.

## Gate Findings And Fixes

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `BATCH001-010-GATE-F1` | Medium | The first batch test run used system Python 3.9, which cannot import backend code using Python 3.10 union type syntax such as `Path | None`. This is a runtime selection issue, not a product regression. | Rerun Python tests with the bundled Codex Python runtime for Python 3.10+ compatibility. |
| `BATCH001-010-GATE-F2` | Medium | `validate_stage005_governance_regression.py` only allowed Stage005 Phase 2-4 current-state markers and rejected the later legal batch upload gate. | Added a RED test for the completed batch upload gate state, then minimally extended the validator whitelist for `IDS-V0_1-BATCH-001-010-UPLOAD-GATE` and the new gate evidence file. GREEN run: `Ran 5 tests ... OK`. |

## Final Local Validation Evidence

- bundled Python focused batch tests:
  - command: `python3 -B -m unittest` with STAGE-001 backend tests,
    ProductMetaDatabase tests, and STAGE-003 through STAGE-010 v0.1 tests.
  - result: `Ran 49 tests ... OK`
- validators:
  - `product_meta_database/validate_product_meta_database.py`: `valid=true`
  - `validate_stage003_finance_meta_rename.py`: `valid=true`
  - `validate_stage004_legacy_name_scan.py`: `valid=true`
  - `validate_stage005_governance_regression.py`: `valid=true`
- owner render:
  - bundled Python `scripts/lean_governance.py check-render --project KM_IDSystem`
    returned `drift_count=0`.
- changed-scope check:
  - changed files are limited to this gate artifact, batch lock, Stage005
    validator/test forward-compatibility fix, roadmap, events, and the three
    owner files.
- formatting:
  - `git diff --check` passed.
- STAGE-010 local path smoke:
  - CLI state: `PATH_CONTRACT_OK`
  - CLI guardrails: all `does_not_*` flags true
  - scenario smoke: `overall_valid=true`
- semantic governance diagnostic:
  - sync validation: `errors=0`, `warnings=0`
  - semantic validation: known 28 sparse-worktree/root/other-project missing
    errors; no `KM_IDSystem` semantic error was reported.

## Stop Conditions

- Any focused test or validator fails for a product-scoped reason.
- `check-render` reports drift.
- changed scope escapes `KM_IDSystem/` or allowed root governance paths.
- GitHub reports open PRs/issues that must be resolved before upload.
- PR creation or merge fails.
- The upload requires expanding Alpha, PFI, EEI, KMFA, Memory Atlas, Serenity,
  or other unrelated project directories.

## Decision

Local batch gate is allowed to proceed to GitHub upload in this run after the
validation plan passes. `STAGE-011` remains blocked until the GitHub main upload
is verified and there are no open PRs or issues left behind.

## Rollback

If this gate fails before GitHub upload, revert this gate commit and leave
`BATCH001_010_UPLOAD_LOCK.yaml` at the prior local reviewed state. If a PR is
created but cannot be merged, close the PR or leave an explicit blocker; do not
start `STAGE-011` while upload is unresolved.
