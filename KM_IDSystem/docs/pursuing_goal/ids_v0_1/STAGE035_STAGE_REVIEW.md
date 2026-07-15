# STAGE-035 Whole-Stage Review - 数据库恢复冒烟测试

- Stage: `STAGE-035 · 数据库恢复冒烟测试`
- Review Task ID: `IDS-V0_1-STAGE035-REVIEW`
- Acceptance ID: `ACC-STAGE-035`
- Reviewed at UTC: `2026-07-10T16:01:39Z`
- Scope: whole-stage review/remediation only; no GitHub upload.
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE036-P1-GATE`

## Goal

Review STAGE-035 end to end after Phase 1 through Phase 4 are locally complete.
This pass verifies the P0 source binding, recovery boundary, machine index,
static preflight checker, eleven scenarios, Phase 4 delivery evidence,
negative safety behavior, raw-data boundary, owner/governance state, and batch
upload lock before any future STAGE-036 work.

The P0 acceptance allows either a runnable recovery capability or an
executable, testable, rollback-capable engineering contract. Because no
owner-authorized real metadata dump is available, this review accepts only the
second form. `PASS_WITH_EXPECTED_BLOCK` proves fail-closed contract behavior;
it does not prove live restore or production readiness.

## Review Checklist

| Area | Result | Evidence |
|---|---|---|
| P0 source binding | Passed. The v0.1-only taskpack contains one STAGE-035 source entry and its SHA-256 matches tracked Phase 1 evidence. | `IDS_Taskpack_v0_1_only_中文修订版.zip`; `STAGE035_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 1 boundary | Passed. It defines owner-authorized real dump identity, isolated target, schema/migration/pool/storage boundaries, preflight, validation, audit, source preservation, owner stop gates, and rollback. | `STAGE035_ENTRY_CONTRACT.md`; `STAGE035_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 static recovery preflight | Passed after review repair. The checker now validates the exact credential-ref policy, migration-validation set, and complete storage-boundary map in addition to the existing dependencies, runtime blocks, raw boundary, and real-data-only policy. | `stage035_database_recovery_smoke_index.json`; `check_database_recovery_smoke.py` |
| Phase 3 scenario validation | Passed. Eleven dynamic scenarios cover migration dry-run requirements, repeat execution, failure rollback, expected recovery block, missing-owner-dump stop gate, raw/unbounded payload blocks, pool, transaction, explainability, and source non-interference. | `STAGE035_PHASE3_SCENARIO_VALIDATION.md`; `test_stage035_database_recovery_smoke.py` |
| Phase 4 closeout | Passed after review repair. `build_stage035_delivery_report` now uses one index snapshot and a machine-readable Phase 4 contract for schema diff, migration output, recovery log, manual confirmation, rollback, backup/restore, known limits, and Chinese feedback. | `STAGE035_PHASE4_CLOSEOUT.md`; `build_stage035_delivery_report` |
| CLI contract | Passed after review repair. Top-level CLI identity is Phase 4 / `IDS-STAGE035-REVIEW-GATE`; Phase 2 and Phase 3 remain nested evidence. | `check_database_recovery_smoke.py`; review regression tests |
| Governance and owner render | Passed after review repair. Structured state checks reject top-level/Stage-node/decision contradictions and an unresolved current Stage node; task `risk` is rendered into owner-facing `risks`. | `validate_stage005_governance_regression.py`; `scripts/lean_governance.py` |
| Raw data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and was not read, listed, hashed, opened, copied, moved, deleted, modified, dumped, scanned, normalized, restored, or committed. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH031_040_UPLOAD_LOCK.yaml` |

## Findings And Fixes

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `STAGE035-REVIEW-F1` | Medium | Phase 4 correctly stopped before review, but no durable STAGE-035 whole-stage review artifact existed. | Added this review artifact with checklist, findings, negative evidence, validation, decision, no-upload boundary, next gate, and rollback. |
| `STAGE035-REVIEW-F2` | Medium | Batch lock and roadmap still represented P4 complete pending review. | Transitioned to `completed_reviewed_local` / `reviewed_local_passed`, next stage STAGE-036, next gate `IDS-STAGE036-P1-GATE`, while retaining `push_allowed=false`. |
| `STAGE035-REVIEW-F3` | Important | Stage005 accepted states through P4 but used whole-file substring matching; contradictory batch top, Stage node, decision, and roadmap values could coexist and still pass. | Reused the repository governance YAML parser, added structured current-state consistency checks, made the real validator require a resolved current Stage node, and added contradiction/missing-node regressions while preserving incomplete historical test snippets. |
| `STAGE035-REVIEW-F4` | Important | The CLI top-level payload was still Phase 2 / `IDS-STAGE035-P3-GATE`; Phase 4 existed only under `delivery_report`. | Promoted Phase 4 delivery identity and gate to the CLI top level, preserving Phase 2/3 as nested evidence and adding exact CLI assertions. |
| `STAGE035-REVIEW-F5` | Important | Phase 4 loaded the same index multiple times, so different snapshots could combine into contradictory PASS evidence. | Added one immutable-in-use snapshot path through Phase 2/3/4 builders; a sequenced-loader regression proves one read and fail-closed behavior. |
| `STAGE035-REVIEW-F6` | Important | `credential_ref_policy`, migration `required_validation_checks`, and the complete storage map were not validated, allowing unsafe in-memory tampering to pass. | Added exact credential policy, exact migration validation set, and exact full storage-boundary validation with negative tests. |
| `STAGE035-REVIEW-F7` | Important | Phase 4 schema/migration/recovery/manual-confirmation/rollback/backup/known-limit evidence was largely code literals and list-length assertions. | Added `phase4_delivery_contract` to the tracked machine index; checker output derives from it and validates exact identities, safety flags, step IDs, limit IDs, Chinese feedback, and fail-closed tampering. |
| `STAGE035-REVIEW-F8` | Minor | Owner render ignored singular task `risk` for KM_IDSystem and displayed `NOT_APPLICABLE`. | Made renderer consistently use the existing `task_risks` fallback and added a focused render regression test. |

## Source And Dependency Evidence

- P0 stage entry:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-035_数据库恢复冒烟测试.md`
- P0 stage SHA-256:
  `2bb4847b6514e63d8f8e07be5c890e05b5d0875cd206ccf9e82b21a6ebccca62`
- P0 matching entry count: `1`
- All fourteen tracked `source_refs` resolve through the Phase 2 checker.
- Current tracked index schema:
  `ids.stage035.database_recovery_smoke.index.v1`
- Current Phase 4 machine contract schema:
  `ids.stage035.database_recovery_smoke.delivery_contract.v1`
- Current Phase 4 report schema:
  `ids.stage035.database_recovery_smoke.phase4.v1`

## Negative Safety Evidence

All negative checks use in-memory copies of tracked engineering contracts.
They do not create fixture files or runtime outputs.

1. A 65-case sweep set each of 27 runtime actions true, removed each runtime
   key, changed ten Phase 2 safety-critical fields, and changed one Phase 4
   source-preservation field. The 64 Phase 2 safety cases failed closed through
   Phase 2, Phase 3, and Phase 4. The Phase 4-only case correctly preserved
   historical Phase 2/3 validity while making Phase 4 fail closed.
2. Review regressions change the credential policy to allow plaintext, empty
   migration validation checks, and enable raw log-body storage. Every case
   returns `delivery_contract_valid=false` and `FAIL_CLOSED`.
3. A sequenced loader returns conflicting index versions. The repaired Phase 4
   path reads once and cannot combine inconsistent snapshots.
4. Changing `preserve_source_database` to allow source mutation makes
   `rollback_steps_valid=false`, `delivery_contract_valid=false`, and recovery
   result `FAIL_CLOSED`.
5. Changing batch top status, Stage task, or decision task independently, or
   removing the current Stage node, makes the structured governance consistency
   check fail. The real validator always runs this check in strict mode.

## Validation Evidence

- RED:
  - Nine focused review/governance tests produced the expected failures for
    missing review evidence, missing reviewed-local state, Phase 2 CLI top
    identity, multiple index reads, unvalidated safety fields, missing Phase 4
    machine contract, substring-only governance checks, an unresolved current
    Stage node, and missing risk rendering.
- GREEN/final validation:
  - Nine focused review/governance tests pass for the review artifact/state,
    Phase 4 CLI identity, one-snapshot behavior, security-field tampering,
    machine-contract tampering, structured contradiction/missing-node
    rejection, and owner risk rendering.
  - STAGE-035 focused tests ran 30 OK; STAGE-031..035 aggregate tests ran 89
    OK; STAGE-026..030 compatibility tests ran 75 OK; Stage005 governance
    regression ran 125 OK; full IDS v0.1 pursuing-goal discovery ran 474 OK.
  - `check_database_recovery_smoke.py` returned rc=0 with top-level Phase 4,
    16 delivery checks true, nine Phase 4 machine-contract checks true,
    `PASS_WITH_EXPECTED_BLOCK`, all live results `NOT_EXECUTED`, and
    `IDS-STAGE035-REVIEW-GATE`.
  - The 65-case mutation audit returned zero fail-open cases.
  - Stage005 validator returned `valid=true`, including eight structured
    current-state checks, with no missing files/events, JSONL errors,
    forbidden/unexpected changed paths, tracked runtime files, or raw-data
    boundary gaps.
  - Syntax compilation passed in memory for nine changed Python files;
    `events.jsonl` parsed with 166 events and zero duplicate IDs; canonical
    render updated three owner files and `check-render` returned
    `drift_count=0` and `reference_issue_count=0`; `git diff --check` passed.
  - Semantic validation reported sync errors=0 and warnings=0, then returned
    the expected sparse-worktree diagnostic rc=1 with 29 missing root
    governance or unrelated registered-project paths. Sparse checkout was not
    expanded.

## Decision

`ACC-STAGE-035` is locally reviewed and passes after the eight findings above
are repaired and final validation is green. STAGE-035 moves from
`completed_local_pending_review` to `completed_reviewed_local`.

This is engineering-contract acceptance, not production PostgreSQL readiness.
No live schema, migration, connection, dump, backup, restore, healthcheck,
recovery smoke, row validation, raw-data processing, or production operation
was executed.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE036_THIS_RUN`

The STAGE-031..040 batch remains locked until all ten stages complete, each
stage has local review/remediation evidence, and the separate batch review and
batch upload gates run. Do not run a single-stage GitHub upload gate.

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
normalize, restore, or commit any content from that root. 中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports,
indexes, manifests, and committed examples must use real user-approved data.
Fake industrial records, fake database rows, fake source documents, fake IDS
business data, placeholder corpus, fabricated dump, and fabricated evidence
are forbidden. 不得使用虚构 IDS 业务数据.

## Next Gate

The next run may enter `IDS-V0_1-STAGE036-P1` from
`IDS-STAGE036-P1-GATE`. This review run does not enter STAGE-036.

## Rollback

Rollback this review/remediation pass by reverting the
`IDS-V0_1-STAGE035-REVIEW` commit. That removes this review artifact, review
event, checker/index repairs, regression tests, structured governance check,
risk-render repair, and reviewed-local governance transition while preserving
the Phase 1 through Phase 4 commits. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs,
manifests, evidence ledgers, audit logs, indexes, PostgreSQL data directories,
app entries, GitHub state, batch review gate, upload gate, or STAGE-036.
