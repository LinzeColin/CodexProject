# STAGE-038 Whole-Stage Review - Worker 队列基线

- Stage: `STAGE-038 · Worker 队列基线`
- Review Task ID: `IDS-V0_1-STAGE038-REVIEW`
- Acceptance ID: `ACC-STAGE-038`
- Reviewed at UTC: `2026-07-12T23:30:00Z`
- Scope: whole-stage review and remediation only; no GitHub upload.
- Current state: `completed_reviewed_local`
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE039-P1-GATE`

## Goal And Decision Boundary

Review Phase 1 through Phase 4 against the unique approved Stage038 taskpack
member. The reviewed capability remains an isolated, in-memory engineering
baseline that acknowledges submission before completion, runs one background
worker over real Git-tracked control references, applies the STAGE-037 state
model, and fails closed on bounded resource and safety gates.

This review does not claim a production queue, persistent claim, automatic
retry, dead-letter runtime, measured fairness, production lease/fencing,
automatic lifecycle, process-crash recovery, cleanup execution, PostgreSQL
action, IDS business job, or raw metadata access.

## Source Reverification

The three exact user-named sources and the unique Stage038 archive member were
rehashed during this review without extracting the archive or enumerating
Downloads:

- `source_archive_sha256=55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- `source_member_sha256=613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634`
- `roadmap_sha256=a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6`
- `instructions_sha256=ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8`

All values match the Phase 1 source-reverification evidence.

## Acceptance Matrix

| Taskpack requirement | Review result | Evidence |
|---|---|---|
| Async queue avoids inline long work | Passed for the isolated baseline. Submission acknowledgement is observed before operation start and completion. | `check_worker_queue_baseline.py`; Phase 2 tests |
| State, input, output, error, checkpoint | Passed. STAGE-037 transitions and bounded refs are machine checked. | Phase 2/3 reports |
| Retry/dead letter boundary | Passed as an explicit no-runtime boundary. `max_retries=0`; same-operation replay is not a new attempt; STAGE-039 owns policy. | Phase 3 exception scenario; Phase 4 failure log |
| Backpressure and pause conditions | Passed after repair. Capacity, removable-drive, actual free-space, API-budget, and same-source conflict signals stop before unsafe admission. | Phase 3/4 reports |
| Lock granularity | Passed for in-process baseline evidence. Same input shares one conflict key across archive/parse/index/report; production lock runtime remains STAGE-041-owned. | Phase 3 scenarios |
| Cleanup protection | Passed as non-destructive contract evidence. Only temporary partial output and rebuildable cache are eligible; protected truth/evidence/report/audit classes remain denied. | Phase 3/4 cleanup checks |
| Automatic/manual recovery and shutdown | Passed as explicit limits. Automatic recovery is empty; orderly isolated shutdown drains accepted work, releases locks, and closes admission. | Phase 4 report |
| Failure, stop, audit, rollback | Passed. Every transition has bounded audit evidence; stop gates and non-destructive rollback remain explicit. | Phase 1-4 evidence |
| Chinese enterprise feedback | Passed. Owner states are short and action-oriented without production-readiness claims. | STAGE-037 projection; Phase 2-4 reports |
| Original and real-data safety | Passed. No raw metadata content, fake IDS business data, database row, report, manifest, or cleanup runtime was used. | Truth contracts and governance boundary |

## Findings And Repairs

| Finding ID | Severity | Finding | Repair |
|---|---|---|---|
| `STAGE038-REVIEW-F1` | Important | Phase 2, 3, and 4 machine contracts accepted unknown root or nested fields, including contradictory runtime-enablement flags. | Added exact root and nested key-set validation at all three layers plus mutation tests that reject injected fields before runtime. |
| `STAGE038-REVIEW-F2` | Important | Phase 1 required API-budget insufficiency to pause relevant jobs, but Phase 3/4 proved only capacity, drive, disk, and same-source signals. | Added a no-call API-budget control-gate scenario returning `PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT`, bound it into the Phase 3 contract and Phase 4 delivery checks, and preserved STAGE-040 ownership. |
| `STAGE038-REVIEW-F3` | Important | Phase 4 told the owner to create a new job after failure, while deterministic identity makes same-input/same-operation submission return the existing terminal entry. | Executed and recorded terminal duplicate replay, replaced the false recovery instruction, set `same_operation_resubmission_available=false`, and assigned retry/new-attempt policy to STAGE-039. |
| `STAGE038-REVIEW-F4` | Important | Phase 4 correctly stopped before review, but no durable whole-stage review artifact or Git-index-bound review gate existed. | Added this artifact, a fail-closed review checker, Stage005 structured review validation, exact event semantics, reviewed-local batch/roadmap state, and the Stage039 P1 next gate. |

## Adversarial Evidence

The RED review matrix reproduced all four gaps before implementation:

1. contradictory top-level and nested fields kept Phase 2, 3, and 4
   `contract_valid=true`;
2. no API-budget scenario or delivery proof existed;
3. a failed same-operation resubmission returned `EXISTING_QUEUE_ENTRY` with
   no second invocation while owner text claimed a new job was available;
4. the review checker, review artifact, reviewed-local governance transition,
   and review event were absent.

The repaired matrix rejects contract injection, proves the API-budget pause,
records the same-operation limitation, and requires every review source to be
Git-tracked and byte-identical to the Git index before review completion.

An attempted automated read-only reviewer was terminated and excluded from
evidence after it widened scope into unrelated worktrees and started a
GitNexus index. Its generated files and root instruction modification were
fully removed; the startup worktree state was restored before implementation.

## Validation Evidence

- Phase 2-4 repaired tests: `25` tests OK before Review gate implementation.
- Final Stage038: `38/38` tests OK.
- Final Stage005 before evidence refresh: `146/146` tests OK.
- Stage031-038 aggregate: `207/207` tests OK.
- Stage026-030 compatibility: `75/75` tests OK.
- Full IDS v0.1 discovery: `613/613` tests OK.
- Review checker: `10/10` review checks and `7/7` governance checks true;
  `review_valid=true` and every review source matched the Git index.
- Direct Stage005 failed closed only on the four preserved owner dirty paths;
  scoped Stage005 returned `valid=true`.
- Events: `182` parsed, zero duplicate ids, one Stage038 review event.
- Static and governance checks: `11` staged Python files compiled in memory;
  render drift/reference counts zero; diff check passed; changed-only governance
  returned zero errors and zero warnings.
- Full semantic validation returned only the expected `29` sparse-worktree
  missing root or unrelated-project paths; sparse scope was not expanded.
- Post-commit HEAD equality is the final local binding check.
- Review source binding requires Git tracking and Git-index equality; HEAD
  equality is reported separately and is verified after the local commit.
- No sparse-checkout expansion was performed.

## Decision

`ACC-STAGE-038` is locally reviewed after all four findings are repaired.
The transition is `completed_reviewed_local`; this remains an isolated
engineering baseline, not production readiness.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE039_THIS_RUN`

`BATCH031_040` remains locked. A single-stage upload, PR, merge, issue
mutation, app reinstall, batch review, or upload gate is not authorized.

## Raw Data Boundary

The local IDS metadata database root is recorded only as:

`/Users/linzezhang/Downloads/IDS_MetaData`

不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描该目录内容。

## Real Data Only Policy

Runtime corpus, database-backed content, analytics, reports, indexes,
manifests, and committed examples may use only real owner-approved data. Fake
business data, fake database rows, placeholder corpus, fabricated jobs, logs,
profiles, dumps, and evidence remain forbidden.

## Next Gate

The next separate run may enter `IDS-V0_1-STAGE039-P1` from
`IDS-STAGE039-P1-GATE`. This review does not enter STAGE-039.

## Rollback

Revert only the `IDS-V0_1-STAGE038-REVIEW` commit to remove the review
evidence, review repairs, and reviewed-local transition while retaining the
four Phase commits. Do not touch raw metadata, databases, source/runtime data,
reports, indexes, app entries, GitHub state, or the four owner-authored dirty
paths.
