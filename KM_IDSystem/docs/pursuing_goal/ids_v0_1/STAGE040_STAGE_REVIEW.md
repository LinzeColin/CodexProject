# STAGE-040 Whole-Stage Review

## Review Identity

- Task: `IDS-V0_1-STAGE040-REVIEW`
- Acceptance: `ACC-STAGE-040`
- Review gate: `IDS-STAGE040-REVIEW-GATE`
- Result after repairs: `completed_reviewed_local`
- Next task: `IDS-V0_1-BATCH-031-040-REVIEW-GATE`
- Production: disabled

This run independently reviewed Stage 040 Phase 1 through Phase 4 against the
approved taskpack and the v0.1 roadmap/instructions. It did not perform the
ten-stage batch review and did not enter Stage 041.

## Source Reverification

The review checker rehashes the three external approved files and reads only
the exact Stage040 member from the ZIP with Python `zipfile`; it does not
extract the archive.

| Source | Verified SHA-256 |
|---|---|
| `IDS_Taskpack_v0_1_only_中文修订版.zip` | `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3` |
| `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-040_反压策略.md` | `f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d` |
| `IDS_Codex开发Roadmap_v0_1_only_中文修订版.txt` | `a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6` |
| `IDS_Codex使用说明_v0_1_only_中文修订版.txt` | `ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8` |

`/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only governance
boundary. No content under it was listed, opened, hashed, copied, scanned,
dumped, moved, changed, or deleted.

## Findings And Repairs

### STAGE040-REVIEW-F1 - Critical - Repaired

Malformed control metadata could escape the Phase 2 fail-closed path:
non-JSON observation values raised `TypeError`, non-hashable `input_refs`
raised `TypeError`, and invalid string refs could be echoed in the decision.

Repair: reference validation now type-checks before set construction;
non-JSON metadata maps to a fixed invalid digest marker; invalid jobs are
evaluated through an empty safe view; invalid timestamps become `null`.
Focused P2 and review tests prove JSON-serializable output, `input_refs=[]`,
no sentinel echo, and `REQUIRE_MANUAL_REVIEW`.

### STAGE040-REVIEW-F2 - Important - Repaired

Phase 1 projected every resource pause as `已暂停`, although active
`CLAIMED`/`RUNNING` work only requests `PAUSE_REQUESTED` and has not yet
reached `PAUSED`.

Repair: the Phase 1 contract now projects queued/retry-wait jobs as `已暂停`
and claimed/running jobs as `暂停中`, matching the Phase 2 legal state path.

### STAGE040-REVIEW-F3 - Important - Repaired

Phase 1 declared `starvation_allowed=false` while deferring the scheduler,
which could be read as proof of starvation prevention without a scheduler or
measured fairness evidence.

Repair: the contract records `starvation_prevention_proved=false`,
`scheduler_algorithm=NOT_IMPLEMENTED_IN_STAGE040`, and
`per_job_type_concurrency=PHASE2_ADMISSION_GUARD_ONLY`. Priority still cannot
bypass a safety gate, but Stage 040 makes no scheduler-level fairness claim.

Final finding count: `1 Critical / 2 Important / 0 Minor`; all three findings
are repaired and machine checked.

## Acceptance Decision

`ACC-STAGE-040` is closed only as `completed_reviewed_local`. The Phase 1-4
contracts remain isolated and production-disabled. Runtime queue/worker,
retry scheduler, lock, automatic resume, crash recovery, cleanup execution,
database connection, raw metadata access, fake IDS business data, GitHub
upload, and app reinstall remain outside this review.

The next and only authorized task is the separate
`IDS-V0_1-BATCH-031-040-REVIEW-GATE`. That gate must review the complete
ten-stage batch before any upload gate can run.

## Validation

Final staged validation passed:

- Phase 1 checker: `20/20` contract checks true; tests `10/10`.
- Phase 2 checker: `18/18` contract and `8/8` slice checks true; tests `16/16`.
- Phase 3 checker: `18/18` contract and `8/8` scenarios true; tests `11/11`.
- Phase 4 checker: `14/14` contract and `8/8` delivery checks true; tests `10/10`.
- Stage040 review tests: `8/8`; Stage040 aggregate: `55/55`.
- Stage005 governance regression: `150/150`; Stage031-039: `254/254`;
  Stage026-030 compatibility: `75/75`.
- Full IDS v0.1 discovery: `720/720` in `185.743s`.
- Stage004 legacy scan: `valid=true`; events: `192`, duplicate IDs: `0`,
  exact Stage040 review events: `1`.
- Owner render drift: `0`; owner reference issues: `0`; changed-only
  governance: `0 errors / 0 warnings`; `git diff --check`: passed.
- Direct Stage005 remained fail-closed only for the four preserved owner dirty
  paths; its scoped report and all 150 tests passed.

The review checker returned `PASS_REVIEWED_LOCAL_PRODUCTION_DISABLED` with all
external-source, Phase 1-4 contract-chain, Phase 2 slice, finding, governance,
and Git-index checks true. Phase 3 scenarios and Phase 4 delivery were rerun by
their dedicated checkers as listed above. Any source mismatch, failed phase
contract, unresolved finding, governance drift, or Git-index mismatch returns
`FAIL_CLOSED` to `IDS-STAGE040-REVIEW-GATE`.

## Stop Markers

- `NO_BATCH_REVIEW_THIS_RUN`
- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE041_THIS_RUN`
- `NO_RAW_METADATA_ACCESS`
- `NO_FAKE_IDS_BUSINESS_DATA`

## Rollback

Revert only the Stage040 review repairs, hash-chain updates, review artifacts,
and this review's governance transition. Preserve earlier stages, approved
external sources, raw data, evidence, owner-authored dirty files, GitHub
state, and app entries. On any inconsistency, restore the review gate to
blocked; do not proceed to batch review or upload.
