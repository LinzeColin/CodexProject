# IDS v0.1 BATCH-011-020 Review Gate

- Batch ID: `IDS-V0_1-BATCH-011-020`
- Task ID: `IDS-V0_1-BATCH-011-020-REVIEW-GATE`
- Stage range: `STAGE-011..STAGE-020`
- Acceptance range: `ACC-STAGE-011..ACC-STAGE-020`
- Gate checked at UTC: `2026-07-02T22:10:49Z`
- Target repository: `LinzeColin/CodexProject`
- Target branch for later upload: `main`
- IDS metadata raw root: `/Users/linzezhang/Downloads/IDS_MetaData`
- Upload lock: `BATCH011_020_UPLOAD_LOCK.yaml`
- Current upload switch: `push_allowed=false`
- Decision: `No GitHub upload`
- next allowed gate: IDS-V0_1-BATCH-011-020-UPLOAD-GATE

## Goal

Review the completed local `STAGE-011..STAGE-020` batch before any GitHub
upload, PR, merge, app reinstall, or `STAGE-021` work. This gate records local
evidence, repair findings, owner-render status, and the IDS raw data boundary.
It does not run the upload gate.

## Local Gate Result

| Gate item | Result | Evidence |
|---|---|---|
| Ten-stage completion | Passed. `STAGE-011` through `STAGE-020` each have four completed phases in the batch lock. | `BATCH011_020_UPLOAD_LOCK.yaml` |
| Acceptance status | Passed. `ACC-STAGE-011` through `ACC-STAGE-020` are `local_passed`. | `BATCH011_020_UPLOAD_LOCK.yaml` |
| Durable evidence files | Passed by local governance references. Stage evidence refs remain under `KM_IDSystem/docs/pursuing_goal/ids_v0_1/` and helper scripts remain under `KM_IDSystem/scripts/`. | `BATCH011_020_UPLOAD_LOCK.yaml`; Stage evidence files |
| Tenth-stage review | Passed locally in this review gate. The upload gate is still separate. | `BATCH011_020_REVIEW_GATE.md` |
| Owner render | Passed. Bundled Python render refreshed owner files and check-render returned `drift_count=0`, `reference_issue_count=0`. | `scripts/lean_governance.py check-render --project KM_IDSystem` |
| Changed scope | Passed. Changed files are limited to this review gate, batch lock, Stage005 governance regression, roadmap, event log, and rendered owner files. | `git diff --name-only`; Stage005 validator changed-scope check |
| GitHub upload | Not executed. This local review does not push, create PR, merge, close PRs/issues, or reinstall app entries. | `No GitHub upload`; `push_allowed=false` |
| IDS metadata raw data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains recorded as a read-only real-data source path; raw database content was not read, listed, scanned, hashed, copied, modified, deleted, moved, dumped, normalized, or committed. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH011_020_UPLOAD_LOCK.yaml` |

## repair finding

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `BATCH011-020-REVIEW-F1` | Medium | STAGE-020 Phase 4 correctly stopped before upload, but no durable batch review artifact existed yet for `STAGE-011..STAGE-020`. | Added `BATCH011_020_REVIEW_GATE.md` and updated the batch lock to `reviewed_ready_for_upload_no_github_upload` while preserving `push_allowed=false`. |
| `BATCH011-020-REVIEW-F2` | Medium | Stage005 governance regression accepted the ready-for-review state, but not the completed local review state. | Added a RED test for `IDS-V0_1-BATCH-011-020-REVIEW-GATE` and extended the validator whitelist only for the precise reviewed-no-upload state. |
| `BATCH011-020-REVIEW-F3` | High | The local real database root must be recorded for GitHub governance while raw data must remain untouched and uncommitted. | Kept `/Users/linzezhang/Downloads/IDS_MetaData` as a tracked path-only boundary and preserved the real-data-only policy; this run did not inspect raw database contents. |

## Validation Plan

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression -q`
- `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
- `python3 -B -m py_compile KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py`
- JSONL parse for `KM_IDSystem/docs/governance/events.jsonl`
- `python -B scripts/lean_governance.py render --project KM_IDSystem --write`
- `python -B scripts/lean_governance.py check-render --project KM_IDSystem`
- `git diff --check`
- legacy underscored task-id scan and pre-rename path diff scan
- `python -B scripts/lean_governance.py validate --project KM_IDSystem --semantic` as sparse-worktree diagnostic only

## Validation Result

- RED evidence:
  - Stage005 review-gate RED failed as expected with 49 tests and 2 failures
    because `BATCH011_020_REVIEW_GATE.md` did not exist and the reviewed
    no-upload batch state was not yet accepted.
- GREEN evidence:
  - Stage005 governance regression passed: `Ran 49 tests ... OK`.
  - Stage005 validator returned `valid=true` with no missing required files,
    no missing event IDs, no invalid JSONL lines, no forbidden changed paths,
    no unexpected changed paths, and all IDS metadata data-boundary checks true.
  - Full IDS v0.1 pursuing-goal unittest discover passed:
    `Ran 166 tests ... OK`.
  - `py_compile` passed for Stage005 validator and regression test.
  - `events.jsonl` parse passed with `events_jsonl_ok count=94`.
  - Bundled Python render updated owner files; check-render returned
    `drift_count=0` and `reference_issue_count=0`.
  - `git diff --check` passed.
  - old underscored task-id variant scan returned no hits.
  - legacy pre-rename path added-line scan returned no hits after the Stage 0
    path wording was corrected to `KM_IDS` and `KM_IDSystem`; full diff hits
    are deletion lines for the old wording.
  - Semantic validate remains diagnostic-only in this sparse worktree: it exits
    1 with 29 known root-governance or registered-project missing-path errors
    and no `KM_IDSystem` semantic error.
- Boundary evidence:
  - This run did not read, list, hash, open, copy, move, delete, modify, dump,
    scan, normalize, or commit `/Users/linzezhang/Downloads/IDS_MetaData`
    raw metadata database content.
  - This run did not push to GitHub, create or merge a PR, close issues, start
    services, install dependencies, generate runtime outputs, write manifests
    or databases, reinstall app entries, run the upload gate, or enter
    `STAGE-021`.

## Upload Boundary

This gate makes the next local step eligible to be the explicit upload gate only
after final validation passes. It does not authorize direct push to `main`.
The next allowed task remains `IDS-V0_1-BATCH-011-020-UPLOAD-GATE`, which must
handle push, PR, merge, app-entry reinstall, app/local/GitHub parity checks, and
open PR/issue cleanup as its own run.

## Rollback

Revert this review gate artifact, batch lock status fields, Stage005 validator
and test updates, roadmap/event changes, and rendered owner-file changes only.
Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports,
outputs, persisted manifests, evidence ledgers, audit logs, indexes, app
entries, GitHub state, or `STAGE-021`.
