# STAGE-031 Whole-Stage Review - Schema 迁移安全

- Stage: `STAGE-031 · Schema 迁移安全`
- Review Task ID: `IDS-V0_1-STAGE031-REVIEW`
- Acceptance ID: `ACC-STAGE-031`
- Reviewed at UTC: `2026-07-03T09:26:34Z`
- Scope: whole-stage review/fix only; no GitHub upload.
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE032-P1-GATE`

## Goal

Review STAGE-031 end to end after Phase 1 through Phase 4 are locally complete.
This pass verifies the P0 source binding, phase evidence, schema migration
safety checker, static scenario coverage, delivery evidence, no-side-effect
boundary, owner/governance state, and batch-upload lock before entering
STAGE-032.

## Review Checklist

| Area | Result | Evidence |
|---|---|---|
| P0 source binding | Passed. P0 zip SHA and STAGE-031 stage file SHA match the Phase 1 evidence and taskpack source. | `IDS_Taskpack_v0_1_only_中文修订版.zip`; `STAGE031_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 1 boundary | Passed. It defines dry-run, backup, validation, rollback, recovery smoke, audit evidence, destructive review state, and owner stop-gate contracts. | `STAGE031_ENTRY_CONTRACT.md`; `STAGE031_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 safety checker | Passed. `check_schema_migration_safety.py` validates dry-run, backup checkpoint, validation, rollback, recovery smoke, audit, owner stop-gate, connection pool, database size, storage-quality, raw metadata, and real-data-only guardrails from tracked contracts only. | `KM_IDSystem/scripts/check_schema_migration_safety.py`; `stage031_migration_safety_index.json` |
| Phase 3 scenario validation | Passed. Static scenarios cover migration dry-run, repeat execution, failure rollback, backup/restore checkpoint, recovery smoke, raw payload block, connection pool boundary, transaction boundary, and constraint error explanations. | `STAGE031_PHASE3_SCENARIO_VALIDATION.md`; `test_stage031_schema_migration_safety.py` |
| Phase 4 closeout | Passed. Closeout records schema diff, migration 输出, 恢复测试日志, known limits, destructive migration confirmation, rollback, 备份恢复步骤, and Chinese owner feedback. | `STAGE031_PHASE4_CLOSEOUT.md`; `build_stage031_delivery_report` |
| Governance and owner render | Passed after this review update. STAGE-031 moves to `completed_reviewed_local`; next gate is `IDS-STAGE032-P1-GATE`; GitHub upload remains blocked until the STAGE-031..040 batch gate. | `BATCH031_040_UPLOAD_LOCK.yaml`; `roadmap.yaml`; `events.jsonl` |
| Raw data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and was not read, listed, hashed, opened, copied, moved, deleted, modified, dumped, scanned, normalized, or committed. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH031_040_UPLOAD_LOCK.yaml` |

## Findings And Fixes

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `STAGE031-REVIEW-F1` | Medium | Phase 4 correctly stopped before whole-stage review, but no durable STAGE-031 review artifact existed yet. | Added `STAGE031_STAGE_REVIEW.md` and recorded review checklist, findings, validation, no-upload boundary, rollback, and next gate. |
| `STAGE031-REVIEW-F2` | Medium | `BATCH031_040_UPLOAD_LOCK.yaml` and roadmap still represented STAGE-031 as local-complete pending review. | Updated governance to `completed_reviewed_local` / `reviewed_local_passed`, with next stage `STAGE-032` and next gate `IDS-STAGE032-P1-GATE`, while preserving `push_allowed=false`. |
| `STAGE031-REVIEW-F3` | Medium | Stage005 governance regression accepted P4 pending-review state but not the precise reviewed-local state for `IDS-V0_1-STAGE031-REVIEW`. | Added RED coverage and extended Stage005 state acceptance only for the reviewed-local no-upload state. |
| `STAGE031-REVIEW-F4` | None | No implementation defect found in the static schema migration safety checker or evidence chain. | No product code fix required; only governance/evidence closure was updated. |
| `STAGE031-REVIEW-F5` | Medium | Owner render write-mode failed on this Mac's Python 3.9 because `Path.write_text(..., newline=...)` is unsupported. | Updated `scripts/lean_governance.py` to write rendered owner files through `path.open("w", encoding="utf-8", newline="\n")`, preserving LF output while restoring project-level render verification. |

## Validation Evidence

- P0 source check:
  - zip SHA-256: `55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
  - stage file inside zip:
    `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-031_Schema迁移安全.md`
  - stage file SHA-256:
    `17a91f01a284d4046a0a17f17f02a5be60b2c351b82a91c87c9c75106800be88`
- Static helper smoke:
  - `ids.stage031.schema_migration_safety.phase4.v1`
  - task: `IDS-V0_1-STAGE031-P4`
  - next gate: `IDS-STAGE031-REVIEW-GATE`
  - `safety_all=True`
  - `guardrails_all=True`
  - `scenario_all=True`
  - `phase4_no_upload=True`
  - `no_raw=True`
- RED evidence:
  - Stage031 review RED failed as expected because `STAGE031_STAGE_REVIEW.md`
    did not exist.
  - Stage005 reviewed-local RED failed as expected because
    `IDS-V0_1-STAGE031-REVIEW` was not accepted by the governance state
    machine.
- GREEN/final validation after review repair:
  - Stage031 focused tests: `Ran 13 tests in 0.025s` / `OK`.
  - Stage005 governance regression: `Ran 104 tests` / `OK`.
  - Stage026-030 compatibility tests: `Ran 75 tests` / `OK`.
  - Full v0.1 pursuing-goal discovery: `Ran 377 tests` / `OK`.
  - Stage005 validator: `valid=true`, `issues=[]`, no missing files, no
    missing event IDs, no JSONL errors, no forbidden changed paths, no
    unexpected changed paths, no tracked forbidden runtime files.
  - Owner render repair: `render --project KM_IDSystem --write` updated 3
    owner files after the Python 3.9 LF-write compatibility fix; final
    `check-render` returned `drift_count=0`.
  - Static schema migration safety helper returned the tracked phase4 report
    with `safety_all=True`, `guardrails_all=True`, `scenario_all=True`,
    `phase4_no_upload=True`, and `no_raw=True`.
  - `py_compile`, events JSONL parse, and `git diff --check` passed.
  - Full semantic validate remains a sparse-worktree diagnostic; this run did
    not expand sparse checkout or read unrelated projects.

## Decision

`ACC-STAGE-031` is locally reviewed and passed. No runtime code fix is required.
STAGE-031 moves from `completed_local_pending_review` to
`completed_reviewed_local`.

This run does not upload to GitHub, open a PR, merge, expand sparse checkout,
install dependencies, create `.venv`, create `node_modules`, create
`data/reports/outputs`, start Docker, connect PostgreSQL, execute migration
dry-run/apply/rollback/backup/restore/schema diff, perform batch review, or
enter STAGE-032.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE032_THIS_RUN`

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

The next run may enter `IDS-V0_1-STAGE032-P1` from `IDS-STAGE032-P1-GATE`.
Do not run a single-stage GitHub upload gate. Upload remains blocked until the
full `STAGE-031..040` batch is complete, reviewed, repaired, and explicitly
batch-gated.

## Rollback

Rollback this review pass by reverting the `IDS-V0_1-STAGE031-REVIEW` commit.
That removes this review artifact, the review event, and the governance status
transition, while preserving the Phase 1 through Phase 4 local implementation
commits. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data,
reports, outputs, manifests, evidence ledgers, audit logs, indexes, PostgreSQL
data directories, app entries, GitHub state, batch review gate, upload gate, or
STAGE-032.
