# IDS v0.1 Stage 0 Phase 4 Closeout

## Run Contract

- Stage: `STAGE-0`
- Phase: `STAGE0-P4`
- Status: `local_closeout_ready_for_github_upload`
- Acceptance: Stage 0 local evidence is complete; the remaining proof is GitHub branch push, PR merge to `main`, remote parity, and no residual PR/issue evidence from this run.
- Non-goals: no `STAGE-001` implementation, no runtime code changes, no dependency install, no `IDS_DATA_ROOT`, no generated data/report outputs.

## Local Evidence Completed

| Phase | Evidence | Status |
|---|---|---|
| P1 | `STAGE0_PHASE1_SOURCE_PRIORITY.md`, `V0_1_ROOT_LOCK.yaml` | complete |
| P2 | `V0_1_STAGE_EXECUTION_INDEX.csv`, `V0_1_STAGE_EXECUTION_INDEX.json`, `STAGE001_ENTRY_CONTRACT.md`, `STAGE0_PHASE2_STAGE_EXECUTION_INDEX.md` | complete |
| P3 | `STAGE0_PHASE3_REVIEW.md` | complete |
| P4 | this closeout file plus rendered governance entries | local closeout ready |

## Final Local Validation Plan

Before commit:

1. Verify local CSV equals the P0 taskpack machine index.
2. Verify JSON index has 168 stage records and `STAGE-001..STAGE-168`.
3. Verify `STAGE001_ENTRY_CONTRACT.md` binds `ACC-STAGE-001` and the P0 stage file hash.
4. Verify `events.jsonl` parses as JSONL.
5. Verify `check-render --project KM_IDSystem` returns `drift_count=0`.
6. Verify changed scope excludes runtime code, data, reports, dependencies, raw materials, and unrelated projects.

After commit and push:

1. Push branch to GitHub.
2. Create PR targeting `main`.
3. Merge PR into `main`.
4. Confirm remote `main` contains the Stage 0 commit.
5. Confirm no residual open PR/issue remains for this Stage 0 upload.

## Sparse Validation Limitation

Local full governance validate is known to be blocked in this sparse worktree because root schemas, root workflows/hooks, and unrelated registered project directories are not present. Stage 0 does not expand unrelated projects to satisfy that validator. P4 uses focused local evidence plus GitHub merge/parity evidence instead.

## Stage 0 Outcome

Stage 0 establishes the execution contract for IDS v0.1 and prepares the next run to enter `STAGE-001 / ACC-STAGE-001` under a one-phase-per-run rule. It does not implement `STAGE-001`.

## Rollback

Before merge: close the PR or reset the branch to the previous commit. After merge: revert the Stage 0 commit from `main`. No runtime data, reports, backend/frontend behavior, taskpack source files, or raw materials are affected.
