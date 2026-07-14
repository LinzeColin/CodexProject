# STAGE-037 Whole-Stage Review - 任务状态模型

- Stage: `STAGE-037 · 任务状态模型`
- Review Task ID: `IDS-V0_1-STAGE037-REVIEW`
- Acceptance ID: `ACC-STAGE-037`
- Reviewed at UTC: `2026-07-11T05:54:51Z`
- Scope: whole-stage review and remediation only; no GitHub upload.
- Current state: `completed_reviewed_local`
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE038-P1-GATE`

## Goal

Review STAGE-037 end to end after Phase 1 through Phase 4 completed locally.
The review covers the eight job types, eleven lifecycle states, twenty-one
transitions, CAS/idempotent replay, claim/fencing, retry accounting, pause and
cancel semantics, the future job-control envelope, adversarial scenarios,
Phase 4 evidence binding, Chinese owner projection, governance events, and the
batch no-upload lock.

This is a static engineering-contract decision. It does not prove that a
queue, worker, retry scheduler, lock manager, PostgreSQL state row, cleanup
action, or real IDS job exists or ran.

## Review Checklist

| Area | Result | Evidence |
|---|---|---|
| P0 identity | Passed with recorded source limitation. The tracked entry binds the unique expected v0.1-only filename and SHA-256. | `STAGE037_ENTRY_CONTRACT.md` |
| Phase 1 boundary | Passed. Lifecycle, deactivation, retry, cleanup, raw-data, and downstream ownership boundaries remain explicit. | `STAGE037_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 engine | Passed after repair. Direct and paused retry admission plus cancellation now fail closed; the complete future envelope is machine-partitioned. | `stage037_job_state_model_index.json`; `check_job_state_model.py` |
| Phase 3 scenarios | Passed after repair. Ten deterministic scenarios remain in-memory only and retain all runtime blocks. | `STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md` |
| Phase 4 delivery | Passed after repair. Canonical index, checker, and P1-P4 evidence are Git-tracked, content-hashed, and required to match the Git index before review completion is projected. | `STAGE037_PHASE4_CLOSEOUT.md`; `build_stage037_delivery_report` |
| Governance | Passed after repair. The checker consumes the structured Stage005 governance report, validates this review artifact, and binds the review artifact, batch lock, roadmap, events, and validator to the Git index before projecting the reviewed-local state. | `BATCH031_040_UPLOAD_LOCK.yaml`; `roadmap.yaml`; `events.jsonl` |
| Raw and real data | Passed. The raw metadata root remained path-only and no fake IDS business data was introduced. | `IDS_METADATA_RAW_DATA_BOUNDARY.md` |

## Findings And Fixes

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `STAGE037-REVIEW-F1` | Medium | Phase 4 correctly stopped before review, but no durable whole-stage review artifact or reviewed-local transition existed. | Added this artifact, review event, reviewed-local batch/roadmap state, and the exact Stage038 P1 next gate while preserving `push_allowed=false`. |
| `STAGE037-REVIEW-F2` | Important | `RETRY_WAIT -> QUEUED` could accept a bare `next_eligible_reached=true` without carrying `next_eligible_at` or eligibility evidence. | Eligible retry snapshots now require a bounded `next_eligible_at`; admission also requires `next_eligible_evidence_ref`. Phase 2 still computes no time and runs no scheduler. |
| `STAGE037-REVIEW-F3` | Important | Allowed cancellation transitions could succeed without a dedicated stop reason. | Added bounded `stop_reason` to snapshot/request contracts and every `* -> CANCELLED` reference requirement; missing reason returns `MISSING_STOP_REASON`. |
| `STAGE037-REVIEW-F4` | Important | Phase 1 named the long-term job envelope, but the machine contract did not partition all identity, attempt, work, claim, control, failure, audit, timestamp, and cleanup fields. | Added exact `job_control_envelope_contract` / `ids.job_control_envelope.v1`, its complete field list, Phase 2 snapshot/request subsets, downstream persistence ownership, and no timestamp-fabrication/runtime-persistence guards. |
| `STAGE037-REVIEW-F5` | Important | Canonical snapshot meant default-path loading but did not prove that index, checker, and P1-P4 sources were Git-tracked. | Delivery validity now requires all six canonical sources to be Git-tracked and reports their observed SHA-256 values. |
| `STAGE037-REVIEW-F6` | Important | Stage037 governance assertions could ignore an unknown later Stage037 event and relied partly on unscoped text presence. | Added exact review event semantics, unknown Stage037 event rejection, structured Stage037 reviewed-local batch/roadmap resolution, and exact event-sequence coverage. |
| `STAGE037-REVIEW-F7` | Minor | `PAUSE_REQUESTED` and `PAUSED` both projected as “已暂停”, hiding the safe-checkpoint intermediate state. | `PAUSE_REQUESTED` now projects as “暂停中”; only `PAUSED` projects as “已暂停”. |
| `STAGE037-REVIEW-F8` | Minor | CLI coverage did not directly protect canonical snapshot binding fields. | Added direct assertions for canonical source, single-snapshot reuse, Git tracking, source hashes, and null load error. |
| `STAGE037-REVIEW-F9` | Critical | `RETRY_WAIT -> PAUSED -> QUEUED` could consume a pending retry without proving that its eligibility time had been reached. | A paused snapshot with `retry_pending=true` now requires the preserved `next_eligible_at`, bounded `next_eligible_evidence_ref`, and `next_eligible_reached=true`; ordinary non-retry pause resume remains unchanged. |
| `STAGE037-REVIEW-F10` | Important | The delivery report projected `completed_reviewed_local` and the Stage038 gate without structurally validating the review artifact, batch lock, roadmap, events, and Stage005 governance result. | Review completion now requires an exact valid structured Stage005 governance report plus semantic checks for this artifact; failure returns `blocked_invalid_review_evidence` and the Stage037 review gate. |
| `STAGE037-REVIEW-F11` | Important | Git-tracked path membership did not prove that the reviewed file bytes matched a reproducible Git snapshot. | Delivery and review sources must now be tracked and match the Git index before review completion; the report separately exposes HEAD-match evidence for post-commit verification. |

## Safety Evidence

All negative cases are in-memory contract mutations using tracked
task/acceptance/control references. They are not fake IDS rows, jobs, source
documents, logs, reports, or execution evidence.

1. Direct or paused eligible retry without its schedule ref, eligibility
   evidence, or reached guard fails closed.
2. Cancellation without a bounded stop reason fails closed.
3. Envelope field removal/addition invalidates the exact machine contract.
4. Untracked or missing canonical delivery sources invalidate delivery.
5. Unknown Stage037 governance events are rejected.
6. Invalid structured governance, review-artifact semantics, or Git-index
   mismatch keeps the report at the Stage037 review gate.
7. Runtime, database, cleanup, raw-data, fake-data, upload, and app switches
   remain false.

## Source Limitation

The three user-provided taskpack ZIP paths checked exactly during this review
were not present at their prior Downloads locations. No broader Downloads scan
was performed. P0 identity therefore relies on the repository's tracked source
filename and SHA-256 binding. This review did not claim fresh byte-for-byte
verification against a currently available external ZIP.

## Validation Evidence

- TDD RED reproduced the paused-retry eligibility bypass, absent structured
  review binding, absent Git-index binding, and stale event finding count before
  each repair. The corresponding focused tests are green.
- Stage037: `39` tests OK; Stage005 governance regression: `139` tests OK.
- Stage031-037 aggregate: `169` tests OK; Stage026-030 compatibility: `75`
  tests OK; full IDS v0.1 pursuing-goal discovery: `568` tests OK.
- Checker: `17/17` delivery checks, `14/14` Phase 4 checks, `22/22` Phase 2
  checks, `10/10` scenarios, and `8/8` review-governance checks. All delivery
  and review sources match the Git index; HEAD matching is reported separately
  and is verified after the local commit rather than used as a pre-commit gate.
- Stage005 validator: `valid=true`, with no event semantic, missing-file,
  forbidden-path, unexpected-path, tracked-runtime, or raw-boundary issue.
- `events.jsonl`: `176` parsed events and zero duplicate event ids. In-memory
  compilation passed for `10` changed Python files.
- Owner render: `drift_count=0`, `reference_issue_count=0`; `git diff --check`
  passed; changed-only governance synchronization returned `errors=0` and
  `warnings=0`.
- Full semantic governance returned only the expected `29` sparse-worktree
  missing root/unrelated-project paths. Sparse checkout was not expanded.
- Independent review sequence: first review found `1 Critical / 2 Important /
  0 Minor`; the next review confirmed those closed and found one stale-event
  Minor; final narrow re-review returned `0 Critical / 0 Important / 0 Minor`
  and `Ready for local commit=Yes`.

## Decision

`ACC-STAGE-037` is locally reviewed after all eleven findings above are repaired.
The current transition is `completed_reviewed_local`. This is a static
contract result, not runtime or production readiness.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE038_THIS_RUN`

The STAGE-031..040 batch remains locked. A single-stage upload, PR, merge,
issue mutation, app reinstall, batch review, or upload gate is not authorized.

## Raw Data Boundary

The local IDS metadata database root is recorded only as:

`/Users/linzezhang/Downloads/IDS_MetaData`

不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描该目录内容。

## Real Data Only Policy

Runtime corpus, database-backed content, analytics, reports, indexes,
manifests, and committed examples may use only real owner-approved data. No
fake business data, fake database rows, placeholder corpus, fabricated jobs,
logs, profiles, dumps, or evidence are allowed.

## Next Gate

The next run may enter `IDS-V0_1-STAGE038-P1` from
`IDS-STAGE038-P1-GATE`. This review does not enter STAGE-038.

## Rollback

Revert only the `IDS-V0_1-STAGE037-REVIEW` commit to remove review evidence,
review repairs, and the reviewed-local transition while retaining the four
Phase commits. Do not touch raw metadata, PostgreSQL, source/runtime data,
reports, indexes, app entries, GitHub state, batch gates, or STAGE-038 files.
