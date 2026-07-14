# IDS v0.1 BATCH-031-040 Independent Review Gate

- Batch ID: `IDS-V0_1-BATCH-031-040`
- Task ID: `IDS-V0_1-BATCH-031-040-REVIEW-GATE`
- Stage range: `STAGE-031..STAGE-040`
- Acceptance range: `ACC-STAGE-031..ACC-STAGE-040`
- Reviewed at UTC: `2026-07-14T10:44:16Z`
- IDS metadata raw root: `/Users/linzezhang/Downloads/IDS_MetaData`
- Current upload switch: `push_allowed=false`
- Decision: `No GitHub upload`
- App boundary: `NO_APP_REINSTALL`
- Stage boundary: `NO_STAGE041_THIS_RUN`
- Next allowed gate: `IDS-V0_1-BATCH-031-040-UPLOAD-GATE`

## Review Objective

Independently review the completed and individually reviewed
`STAGE-031..STAGE-040` batch before any upload. The review binds the exact
approved external sources, ten Stage review artifacts, Stage036-040 interface
chain, stage checkers, governance route, and Git index. It does not authorize
GitHub upload, PR, merge, issue mutation, app reinstall, production runtime, or
`STAGE-041` work.

## Review Result

| Gate | Result | Evidence |
|---|---|---|
| Source identity | Passed. The approved taskpack archive, roadmap and instructions hashes match, and exactly one member for each Stage031-040 was rehashed. | `batch_review/stage031_040_batch_review_contract.json`; `check_batch031_040_review.py` |
| Ten Stage reviews | Passed. All ten Stage nodes are `completed_reviewed_local`, all review artifacts match their recorded SHA-256, and all stage checkers pass. | Stage031-040 review artifacts and checkers |
| Cross-Stage contract | Passed. Stage037 owns the exact 8 job types, 11 states, 4 terminal states and 21 transitions; Stage038-040 preserve the contract; Stage041-044 runtime ownership remains deferred. | `stage031_040_batch_review_contract.json`; Stage036-040 machine contracts |
| Fail-closed gate | Passed. Unknown contract fields, any failed Stage, missing governance evidence, untracked evidence, or index drift blocks review eligibility. | `test_batch031_040_review_gate.py` |
| Upload boundary | Passed. The only next task is the separate upload gate; `push_allowed=false`. | `BATCH031_040_UPLOAD_LOCK.yaml`; `roadmap.yaml` |
| Raw-data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and read-only; its contents were not read, listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned, or normalized. | `IDS_METADATA_RAW_DATA_BOUNDARY.md` |

## Review Findings And Repairs

| Finding ID | Severity | Finding | Repair |
|---|---|---|---|
| `BATCH031-040-REVIEW-F1` | Critical | No machine-checkable ten-stage gate bound all approved sources, Stage reviews, cross-stage interfaces, and Git-index state before upload eligibility. | Added the strict batch contract, checker, and fail-closed tests; post-repair self-review also removed a malformed `stage_id` conversion exception so invalid identities return a blocked report. |
| `BATCH031-040-REVIEW-F2` | Important | Stage031-037 lacked one uniform batch-level source-member and Git-index integrity layer comparable to later Stage review checkers. | Added exact member/review hashes and checker/test bindings for all ten stages. |
| `BATCH031-040-REVIEW-F3` | Important | The reviewed-no-upload transition, event semantics, and route to a separate upload gate did not exist. | Added the explicit batch state, Stage005 governance semantics, review event, and upload-only next gate while keeping upload disabled. |

All three findings are repaired. No finding is deferred.

## Validation

- RED: `test_batch031_040_review_gate` ran 8 tests and produced 4 failures plus
  1 error before the review evidence and governance transition existed; the
  strict shape and fail-closed tamper tests already passed.
- GREEN validation commands:
  - `python3 -B KM_IDSystem/scripts/check_batch031_040_review.py`
  - `python3 -B -m unittest -q KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_batch031_040_review_gate`
  - `python3 -B -m unittest -q KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression`
  - `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  - `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  - `python3 -B scripts/lean_governance.py check-render --project KM_IDSystem`
  - JSONL parse/duplicate-ID check, `git diff --check`, and scoped changed-only governance validation
- GREEN results:
  - Batch checker returned `PASS_REVIEWED_READY_FOR_UPLOAD_GATE_NO_GITHUB_UPLOAD`; all source, Stage, cross-Stage, governance, finding, truth and Git-index checks are true.
  - Batch review tests passed `8/8`; Stage005 governance regression passed `151/151`.
  - Stage031-039 aggregate passed `254/254`; Stage040 aggregate passed `55/55`.
  - Full IDS v0.1 pursuing-goal discovery passed `729/729` after repairing six historical Stage038/039 reviewed-no-upload compatibility assertions exposed by the first full run.
  - Final checker self-review added a malformed Stage identity negative case; invalid identity values now fail closed without an exception.
  - Direct Stage005 validation is fail-closed only on the four preserved owner dirty paths; event semantics, phase state, source reverification, data boundary and required files all pass.
  - Owner render check returned `drift_count=0` and `reference_issue_count=0`; Stage004 legacy-name scan returned `valid=true`.
  - `events.jsonl` parsed `193` events with no duplicate IDs and exactly one batch-review event; changed-only governance returned `errors=0`, `warnings=0`; `py_compile` and both worktree/index `git diff --check` passed.
  - Full semantic validation remains diagnostic-only in this sparse worktree: it reports the known 29 missing root-schema/tooling and unrelated-project paths, with no `KM_IDSystem` semantic error. Sparse scope was not expanded.

## Stop Boundary

This run stops after independent local review, repair, validation, and local
commit. It performs `No GitHub upload`, leaves `push_allowed=false`, performs
`NO_APP_REINSTALL`, and enforces `NO_STAGE041_THIS_RUN`. The next run may only
enter `IDS-V0_1-BATCH-031-040-UPLOAD-GATE`; it must fail closed if the Git index
or any bound source/review artifact has changed.

## Rollback

Revert only this batch review contract/checker/test/evidence, the batch lock,
Stage005 governance additions, roadmap/event changes, HANDOFF/CHANGELOG, and
rendered owner views. Preserve all Stage031-040 artifacts, the four owner dirty
paths, raw metadata, runtime data, databases, reports, outputs, GitHub state,
app entries, and `STAGE-041` state.
