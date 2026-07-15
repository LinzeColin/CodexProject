# STAGE-033 Whole-Stage Review - 数据库体积护栏

- Stage: `STAGE-033 · 数据库体积护栏`
- Review Task ID: `IDS-V0_1-STAGE033-REVIEW`
- Acceptance ID: `ACC-STAGE-033`
- Reviewed at UTC: `2026-07-04T00:02:57Z`
- Scope: whole-stage review/fix only; no GitHub upload.
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE034-P1-GATE`

## Goal

Review STAGE-033 end to end after Phase 1 through Phase 4 are locally complete.
This pass verifies the P0 source binding, phase evidence, static database
size-guard checker, scenario coverage, delivery evidence, no-side-effect
boundary, owner/governance state, raw database boundary, and batch-upload lock
before any future STAGE-034 work.

## Review Checklist

| Area | Result | Evidence |
|---|---|---|
| P0 source binding | Passed. P0 zip SHA and STAGE-033 stage file SHA match the Phase 1 evidence and taskpack source. | `IDS_Taskpack_v0_1_only_中文修订版.zip`; `STAGE033_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 1 boundary | Passed. It defines PostgreSQL storage scope, blocked raw/OCR/large-file payloads, derived artifact limits, database size budgets, table/index/payload guardrails, retention and cleanup boundaries, audit evidence, and rollback verification. | `STAGE033_ENTRY_CONTRACT.md`; `STAGE033_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 database size guard checker | Passed. `check_database_size_guard.py` validates storage scope, raw/OCR/large-file blocks, policy thresholds, table/index/row payload guardrails, cleanup stop gates, connection-pool budget dependency, quality constraints, raw-data boundary, real-data-only policy, and rollback verification from tracked contracts only. | `KM_IDSystem/scripts/check_database_size_guard.py`; `stage033_database_size_guard_index.json` |
| Phase 3 scenario validation | Passed. Static scenarios cover migration dry-run dependency, repeat execution, failure rollback, recovery smoke, raw large-file blocking, OCR full-text blocking, derived artifact limits, database size budget, connection-pool boundary, transaction boundary, and constraint error explanations. | `STAGE033_PHASE3_SCENARIO_VALIDATION.md`; `test_stage033_database_size_guard.py` |
| Phase 4 closeout | Passed. Closeout records schema diff, migration output, recovery test log, known limits, destructive migration confirmation, rollback_steps, backup_restore_steps, and Chinese owner feedback through `build_stage033_delivery_report`. | `STAGE033_PHASE4_CLOSEOUT.md`; `build_stage033_delivery_report` |
| Governance and owner render | Passed after this review update. STAGE-033 moves to `completed_reviewed_local`; next gate is `IDS-STAGE034-P1-GATE`; GitHub upload remains blocked until the STAGE-031..040 batch gate. | `BATCH031_040_UPLOAD_LOCK.yaml`; `roadmap.yaml`; `events.jsonl` |
| Raw data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and was not read, listed, hashed, opened, copied, moved, deleted, modified, dumped, scanned, normalized, or committed. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH031_040_UPLOAD_LOCK.yaml` |

## Findings And Fixes

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `STAGE033-REVIEW-F1` | Medium | Phase 4 correctly stopped before whole-stage review, but no durable STAGE-033 review artifact existed yet. | Added `STAGE033_STAGE_REVIEW.md` and recorded review checklist, findings, validation, no-upload boundary, rollback, raw database boundary, real-data-only policy, and next gate. |
| `STAGE033-REVIEW-F2` | Medium | `BATCH031_040_UPLOAD_LOCK.yaml` and roadmap still represented STAGE-033 as local-complete pending review. | Updated governance to `completed_reviewed_local` / `reviewed_local_passed`, with next stage `STAGE-034` and next gate `IDS-STAGE034-P1-GATE`, while preserving `push_allowed=false`. |
| `STAGE033-REVIEW-F3` | Medium | Stage005 governance regression accepted P4 pending-review state but not the precise reviewed-local state for `IDS-V0_1-STAGE033-REVIEW`. | Added RED coverage and extended Stage005 state acceptance only for the reviewed-local no-upload state. |
| `STAGE033-REVIEW-F4` | None | No implementation defect found in the static database size-guard checker or evidence chain. | No product code fix required; only governance/evidence closure was updated. |

## Validation Evidence

- P0 source check:
  - stage file inside zip:
    `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-033_数据库体积护栏.md`
  - stage file SHA-256:
    `454efae78a2a493bce9af351384a0d0d634c197f32d0936d8466382d6b67f777`
- Static helper smoke:
  - `ids.stage033.database_size_guard.phase4.v1`
  - task: `IDS-V0_1-STAGE033-P4`
  - next gate: `IDS-STAGE033-REVIEW-GATE`
  - `constraint_error_explanations=PASS`
  - `no_raw=True`
  - `no_fake=True`
- RED evidence:
  - Stage033 review RED failed as expected because `STAGE033_STAGE_REVIEW.md`
    did not exist.
  - Stage005 reviewed-local RED failed as expected because
    `IDS-V0_1-STAGE033-REVIEW` and `IDS-STAGE034-P1-GATE` were not accepted
    by the governance state machine.
- GREEN/final validation after review repair:
  - Stage033 review focused tests ran 2 tests OK.
  - Stage005 reviewed-local focused test ran 1 test OK.
  - Stage033 focused tests ran 16 tests OK.
  - Stage031/Stage032 compatibility tests ran 26 tests OK.
  - Stage005 governance regression ran 114 tests OK.
  - Stage031-033 aggregate compatibility/focused tests ran 42 tests OK.
  - Full IDS v0.1 pursuing-goal discovery ran 416 tests OK.
  - Stage005 validator returned `valid=true` with no missing files/events,
    JSONL errors, forbidden changes, unexpected changes, tracked runtime files,
    or data-boundary gaps.
  - `check_database_size_guard.py` returned the tracked static Phase 4
    delivery report with `no_raw=True` and `no_fake=True`; it did not connect
    to PostgreSQL, run size queries, execute cleanup, read raw metadata, or
    write runtime outputs.
  - `py_compile` passed for the changed tests, validator, and checker.
  - `events.jsonl` parsed with 156 events, 0 duplicate ids, and 0 JSON errors.
  - Owner render/check-render passed: render updated 3 owner files and
    check-render returned `drift_count=0`.
  - `git diff --check` passed.
  - Full semantic validate returned the expected sparse-worktree diagnostic
    rc=1 with sync validation errors=0, warnings=0, and 29 missing root
    schema/workflow/hook/unrelated registered-project errors; this run did not
    expand sparse checkout.

## Decision

`ACC-STAGE-033` is locally reviewed and passed. No runtime code fix is required.
STAGE-033 moves from `completed_local_pending_review` to
`completed_reviewed_local`.

This run does not upload to GitHub, open a PR, merge, expand sparse checkout,
install dependencies, create `.venv`, create `node_modules`, create
`data/reports/outputs`, start Docker, connect PostgreSQL, create live schema or
migration files, create DSNs or credential-bearing configs, execute size query,
VACUUM, reindex, cleanup, retention deletion, migration
dry-run/apply/rollback/backup/restore/schema diff, perform batch review, or
enter STAGE-034.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE034_THIS_RUN`

The STAGE-031..040 batch remains locked until all ten stages complete, each
stage has local review/repair evidence, and the separate batch review/upload
gates run.

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
normalize, or commit any content from that root. 中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports, indexes,
manifests, and committed examples must use real user-approved data. Fake
industrial records, fake database rows, fake source documents, fake IDS
business data, placeholder corpus, and fabricated evidence are forbidden.
不得使用虚构 IDS 业务数据.

## Next Gate

The next run may enter `IDS-V0_1-STAGE034-P1` from `IDS-STAGE034-P1-GATE`.
Do not run a single-stage GitHub upload gate. Upload remains blocked until the
full `STAGE-031..040` batch is complete, reviewed, repaired, and explicitly
batch-gated.

## Rollback

Rollback this review pass by reverting the `IDS-V0_1-STAGE033-REVIEW` commit.
That removes this review artifact, the review event, and the governance status
transition, while preserving the Phase 1 through Phase 4 local implementation
commits. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data,
reports, outputs, manifests, evidence ledgers, audit logs, indexes, PostgreSQL
data directories, app entries, GitHub state, batch review gate, upload gate, or
STAGE-034.
