# STAGE-039 Whole-Stage Review - Retry And Dead-Letter Policy

- Stage: `STAGE-039 · 重试与死信策略`
- Review Task ID: `IDS-V0_1-STAGE039-REVIEW`
- Acceptance ID: `ACC-STAGE-039`
- Reviewed at UTC: `2026-07-13T02:17:00Z`
- Scope: whole-stage review and remediation only; no GitHub upload.
- Current state: `completed_reviewed_local`
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE040-P1-GATE`

## Goal And Decision Boundary

Review Phase 1 through Phase 4 against the unique approved Stage039 taskpack
member, the Stage037 state model, and the reviewed Stage038 queue baseline.
The accepted capability remains a bounded, isolated, non-production retry and
dead-letter control-policy slice. It classifies exact safe error codes,
reserves retry without consuming budget, increments budget only on due atomic
admission, preserves resource pauses, and routes exhaustion to immutable
`DEAD_LETTERED` evidence.

This review does not claim a persistent scheduler, production queue, successful
automatic recovery, automatic resume, process recovery, production locking,
cleanup execution, database action, raw metadata access, real IDS business
job, or production readiness.

## Acceptance Matrix

| Requirement | Review result | Evidence |
|---|---|---|
| Job/worker and state boundaries | Passed. Stage037 remains the only state authority; terminal states remain immutable. | Phase 1 and Phase 4 graphs |
| Retry and dead-letter semantics | Passed. Reservation consumes no budget, two due admissions consume exactly one each, and exhaustion reaches `DEAD_LETTERED` at `retry_count=2`. | Phase 2 and Phase 4 reports |
| Failure classification | Passed. Two exact retryable codes are allowlisted; missing, unknown, permanent, policy-blocked, and unsafe cases fail closed. | Phase 1-3 contracts and tests |
| Resource pauses and backpressure signals | Passed for bounded evidence only. Drive, disk, API budget, capacity, and same-source conflict signals do not claim Stage040 runtime. | Phase 3 and Phase 4 evidence |
| Idempotency and terminal rerun lineage | Passed after repair. A future implementation must use a new linked-job identity; Stage039 validates only a non-persisted candidate and creates no job. | Phase 1 contract; Phase 3 scenario |
| Protected evidence and cleanup | Passed as denial/allowlist evidence only. No deletion path ran. | Phase 3 and Phase 4 evidence |
| Governance models, formulas, parameters | Passed after repair. Total registry counts are 8/8/55; active counts remain 7/7/49; Stage039 values are `planned` / `PROPOSED` and calibration-task linked. | Governance registries and `MODEL_SPEC.md` |
| Chinese owner feedback and rollback | Passed. Feedback distinguishes controlled eligibility from manual action and does not promise recovery. | Phase 2-4 evidence |
| Original and real-data safety | Passed. No database or raw metadata content was accessed and no fake IDS business data was used. | Truth contracts and batch boundary |

## Findings And Repairs

| Finding ID | Severity | Finding | Repair |
|---|---|---|---|
| `STAGE039-REVIEW-F1` | Important | Phase 2 registered `MOD-008`, `FORM-008`, and `PARAM-050..055` with unsupported `isolated_non_production` / `ASSUMPTION` governance enums and omitted calibration-task links. | Changed registry status/fact semantics to `planned` / `PROPOSED`, bound unresolved production calibration to existing `TASK-OPME-B-001`, and synchronized canonical project facts. |
| `STAGE039-REVIEW-F2` | Important | `MODEL_SPEC.md` still declared 7 models, 7 formulas, and 49 parameters after adding the planned Stage039 policy entries. | Declared total counts 8/8/55 and separately preserved active counts 7/7/49. |
| `STAGE039-REVIEW-F3` | Important | P1, P2, P4, and HANDOFF wording could be read as evidence that Stage039 created a new terminal-rerun job, while Phase 3 only validates `candidate_only=true`, `persisted=false`, and `job_created=false`. | Separated the future linked-job identity requirement from current implementation truth and changed recovery wording to candidate validation only. |
| `STAGE039-REVIEW-F4` | Important | Phase 4 correctly stopped before review, but Stage039 had no durable whole-stage review artifact, fail-closed review checker, review event, or reviewed-local governance transition. | Added this artifact, `check_retry_dead_letter_stage_review.py`, review tests, review event, and exact Stage040 P1 next gate while retaining `push_allowed=false`. |

## Adversarial Evidence

The review RED test failed all six cases because the whole-stage review checker
and artifact did not exist. The project-wide semantic validator independently
reported 21 Stage039 registry/schema/count findings before remediation. The
repaired checker now requires exact registry status, fact level, task links,
total and active counts, Phase 3 manual-rerun truth, valid Phase 4 delivery,
structured Stage005 governance, and Git-index equality for every review source.

## Validation Evidence

- TDD review RED: `6/6` tests failed before the review checker and evidence existed.
- Repaired Phase 1-4 Stage039 tests: `41/41` passed before review-gate implementation.
- Final Stage004 compatibility: `3/3` tests passed after narrowly classifying
  only canonical `TASK-OPME-*` / `FEAT-OPME-*` governance identifiers in the
  new review checker; a display label `OpMe` remains active debt.
- Final Stage039: `47/47` tests passed.
- Final Stage005 governance regression: `146/146` tests passed.
- Stage031-039 aggregate: `254/254` tests passed.
- Stage026-030 compatibility: `75/75` tests passed.
- Full IDS v0.1 discovery: `661/661` tests passed.
- Review checker: all `9/9` review checks and `8/8` registry repair checks are
  true; every review source is Git tracked and matches the Git index.
- Project semantic validation removed all `21` Stage039 registry/schema/count
  findings. The remaining `29` diagnostics are only expected sparse root and
  unrelated-project paths; sparse scope was not expanded.
- Owner render: `drift_count=0`, `reference_issue_count=0`.
- Events: `187` parsed, zero duplicate IDs, exactly one Stage039 review event.
- `git diff --check` passed before final evidence refresh; final staged checks
  are repeated before commit.
- Sparse checkout was not expanded.

## Decision

`ACC-STAGE-039` is locally reviewed after all four Important findings are
repaired. The transition is `completed_reviewed_local`; this is not production
readiness.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE040_THIS_RUN`

`BATCH031_040` remains locked. A single-stage upload, PR, merge, issue mutation,
app reinstall, batch review, or upload gate is not authorized.

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

The next separate run may enter `IDS-V0_1-STAGE040-P1` from
`IDS-STAGE040-P1-GATE`. This review does not enter STAGE-040.

## Rollback

Revert only the `IDS-V0_1-STAGE039-REVIEW` commit to remove the review evidence,
repairs, and reviewed-local transition while retaining the four Phase commits.
Do not touch raw metadata, databases, source/runtime data, reports, indexes,
app entries, GitHub state, or the four owner-authored dirty paths.
