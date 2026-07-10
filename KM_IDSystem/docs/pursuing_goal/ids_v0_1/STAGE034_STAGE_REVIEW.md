# STAGE-034 Whole-Stage Review - 数据保留表

- Stage: `STAGE-034 · 数据保留表`
- Review Task ID: `IDS-V0_1-STAGE034-REVIEW`
- Acceptance ID: `ACC-STAGE-034`
- Reviewed at UTC: `2026-07-10T13:54:17Z`
- Scope: whole-stage review/remediation only; no GitHub upload.
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE035-P1-GATE`

## Goal

Review STAGE-034 end to end after Phase 1 through Phase 4 are locally complete.
This pass verifies the P0 source binding, phase evidence, static data-retention
index/checker, negative safety behavior, scenario coverage, closeout evidence,
raw database boundary, owner/governance state, and batch-upload lock before any
future STAGE-035 work.

## Review Checklist

| Area | Result | Evidence |
|---|---|---|
| P0 source binding | Passed. The taskpack contains one STAGE-034 source entry and its SHA-256 matches Phase 1 evidence. | `IDS_Taskpack_v0_1_only_中文修订版.zip`; `STAGE034_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 1 boundary | Passed. It defines five retention subjects, TTL/keep-until, owner hold, dry-run, deletion stop gate, audit evidence, rollback/restore, PostgreSQL storage scope, and raw-data boundaries. | `STAGE034_ENTRY_CONTRACT.md`; `STAGE034_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 data retention table | Passed after review repair. The tracked index and checker validate retention subjects, guardrails, runtime-policy blocks, dependencies, raw boundary, and real-data-only policy. Top-level safety conclusions now derive from those checks instead of constants. | `stage034_data_retention_table_index.json`; `check_data_retention_table.py` |
| Phase 3 scenario validation | Passed. Thirteen static scenarios cover migration dependency, repeat execution, rollback/recovery boundaries, raw/unbounded payload blocks, subjects, TTL/hold, cleanup/deletion gates, connection/transaction boundaries, and error explanations. | `STAGE034_PHASE3_SCENARIO_VALIDATION.md`; `test_stage034_data_retention_table.py` |
| Phase 4 closeout | Passed after review repair. `build_stage034_delivery_report` provides schema diff, migration output, recovery log, known limits, destructive confirmation, rollback, backup/restore, and Chinese feedback. `contract_valid` and `recovery_test_log.check_results` now fail closed. | `STAGE034_PHASE4_CLOSEOUT.md`; `build_stage034_delivery_report` |
| Governance and owner render | Passed after this review update. STAGE-034 moves to `completed_reviewed_local`; next gate is `IDS-STAGE035-P1-GATE`; GitHub upload remains blocked until the STAGE-031..040 batch gate. | `BATCH031_040_UPLOAD_LOCK.yaml`; `roadmap.yaml`; `events.jsonl` |
| Raw data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and was not read, listed, hashed, opened, copied, moved, deleted, modified, dumped, scanned, normalized, or committed. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH031_040_UPLOAD_LOCK.yaml` |

## Findings And Fixes

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `STAGE034-REVIEW-F1` | Medium | Phase 4 correctly stopped before whole-stage review, but no durable STAGE-034 review artifact existed. | Added `STAGE034_STAGE_REVIEW.md` with checklist, findings, validation, boundaries, decision, next gate, and rollback. |
| `STAGE034-REVIEW-F2` | Medium | Batch lock and roadmap correctly represented local-complete pending review, but had not recorded the review decision. | Updated governance to `completed_reviewed_local` / `reviewed_local_passed`, next stage `STAGE-035`, next gate `IDS-STAGE035-P1-GATE`, with `push_allowed=false`. |
| `STAGE034-REVIEW-F3` | Medium | Stage005 governance regression accepted P4 pending-review state but not the precise reviewed-local state for `IDS-V0_1-STAGE034-REVIEW`. | Added RED coverage and extended Stage005 state acceptance only for the reviewed-local no-upload state. |
| `STAGE034-REVIEW-F4` | Important | An in-memory invalid contract could make nested runtime/guardrail checks fail while Phase 2/4 top-level `does_not_*` fields remained true and `recovery_test_log` remained a hard-coded PASS. This produced contradictory safety evidence. | Derived top-level safety fields from actual checks, added `contract_valid` and per-check recovery results, made the recovery result fail closed, and added an in-memory regression test. |

## Source And Dependency Evidence

- P0 stage entry:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-034_数据保留表.md`
- P0 stage SHA-256:
  `af3196bb6ce76bbf22888abbb8c178b3deb0570e6cd2e19235853bac649b818d`
- P0 matching entry count: `1`
- All eleven tracked `source_refs` resolved to existing files.
- Current tracked index schema:
  `ids.stage034.data_retention_table.index.v1`
- Current Phase 4 report schema:
  `ids.stage034.data_retention_table.phase4.v1`

## Negative Safety Evidence

The review used an in-memory copy of the tracked index and did not create a
temporary file. It changed only the in-memory values:

- `connect_to_postgres=true`
- `execute_cleanup=true`
- `cleanup_dry_run_guard.auto_delete_allowed=true`

Before repair, nested checks/scenarios failed while top-level
`does_not_connect_to_postgres`, `does_not_execute_cleanup`, and Phase 4
recovery result still claimed success. After repair:

- Phase 2 and Phase 3 top-level safety values become `false`.
- Phase 3 `cleanup_dry_run` becomes `FAIL`.
- Phase 4 `contract_valid=false`.
- Phase 4 `recovery_test_log.result=FAIL`.
- The tracked valid index continues to produce `contract_valid=true` and a
  `PASS` recovery result.

## Validation Evidence

- RED:
  - Stage034 review tests failed because the invalid contract still produced
    contradictory top-level safety evidence and no review artifact existed.
  - Stage005 reviewed-local test failed because
    `IDS-V0_1-STAGE034-REVIEW` / `IDS-STAGE035-P1-GATE` were not accepted.
- GREEN/final validation:
  - `check_data_retention_table.py` returned rc=0; the tracked valid contract
    produced `contract_valid=true`, ten recovery checks all true, and recovery
    result `PASS`.
  - STAGE-034 focused tests ran 17 tests OK; Stage005 governance regression ran
    119 tests OK; STAGE-026..030 compatibility tests ran 75 tests OK;
    STAGE-031..034 aggregate tests ran 59 tests OK; full IDS v0.1 pursuing-goal
    discovery ran 438 tests OK.
  - Stage005 validator returned `valid=true` with no missing files/events,
    JSONL errors, forbidden or unexpected changed paths, tracked forbidden
    runtime files, or raw-data boundary gaps.
  - Syntax compilation passed in memory for seven changed Python files;
    `events.jsonl` parsed with 161 events and zero duplicate ids; owner render
    updated three existing files and `check-render` returned `drift_count=0`
    and `reference_issue_count=0`; `git diff --check` passed.
  - Semantic validation reported sync errors=0, then returned the expected
    sparse-worktree diagnostic rc=1 with 29 missing root governance or unrelated
    registered-project paths. The sparse checkout was not expanded.

## Decision

`ACC-STAGE-034` is locally reviewed and passed after repairing the
contradictory safety evidence. STAGE-034 moves from
`completed_local_pending_review` to `completed_reviewed_local`.

This is engineering-contract acceptance, not production PostgreSQL readiness.
No live schema, migration, connection, retention scheduler, cleanup, deletion,
backup, restore, recovery, or raw-data processing was executed.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE035_THIS_RUN`

The STAGE-031..040 batch remains locked until all ten stages complete, each
stage has local review/repair evidence, and the separate batch review/upload
gates run. Do not run a single-stage GitHub upload gate.

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
normalize, or commit any content from that root. 中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports,
indexes, manifests, and committed examples must use real user-approved data.
Fake industrial records, fake database rows, fake source documents, fake IDS
business data, placeholder corpus, and fabricated evidence are forbidden.
不得使用虚构 IDS 业务数据.

## Next Gate

The next run may enter `IDS-V0_1-STAGE035-P1` from
`IDS-STAGE035-P1-GATE`. This review run does not enter STAGE-035.

## Rollback

Rollback this review pass by reverting the
`IDS-V0_1-STAGE034-REVIEW` commit. That removes this review artifact, review
event, checker repair, regression tests, and reviewed-local governance
transition while preserving the Phase 1 through Phase 4 commits. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs,
manifests, evidence ledgers, audit logs, indexes, PostgreSQL data directories,
app entries, GitHub state, batch review gate, upload gate, or STAGE-035.
