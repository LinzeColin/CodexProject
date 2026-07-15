# STAGE-036 Whole-Stage Review - 数据库质量约束

- Stage: `STAGE-036 · 数据库质量约束`
- Review Task ID: `IDS-V0_1-STAGE036-REVIEW`
- Acceptance ID: `ACC-STAGE-036`
- Reviewed at UTC: `2026-07-10T21:51:40Z`
- Scope: whole-stage review and remediation only; no GitHub upload.
- Current upload switch: `push_allowed=false`
- Next allowed gate: `IDS-STAGE037-P1-GATE`

## Goal

Review STAGE-036 end to end after Phase 1 through Phase 4 are locally
complete. This review verifies P0 source binding, the Phase 1 boundary, the
Phase 2 static quality-constraint contract, Phase 3 scenario validation,
Phase 4 closeout, executable migration-section selection, rollback ownership,
bounded real-data profile authorization, dependency/snapshot provenance,
governance event semantics, and the batch no-upload lock.

The P0 acceptance permits an executable, testable, rollback-capable
engineering contract. No owner-authorized real-data profile was supplied, so
this review accepts only that contract form. `PASS_WITH_EXPECTED_BLOCK` does
not prove that PostgreSQL was connected, rows were profiled, constraints were
installed, or production readiness was achieved.

## Review Checklist

| Area | Result | Evidence |
|---|---|---|
| P0 source binding | Passed. The unique v0.1-only STAGE-036 source is bound by the tracked SHA-256. | `STAGE036_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 1 boundary | Passed. Existing schema facts, row-dependent candidates, STAGE-037 extension points, real-data-only policy, and no-live boundaries remain explicit. | `STAGE036_ENTRY_CONTRACT.md`; `STAGE036_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 static quality-constraint contract | Passed after repair. The index, SQL, checker, bounded query contract, non-live authorization contract, executable section runner, dependency hashes, and ownership markers are fail closed. v0.1 cannot emit `up` SQL because no trusted signature or target-database binding verifier exists. | `stage036_database_quality_constraints_index.json`; `002_database_quality_constraints.sql`; `stage036_quality_profile_queries.json`; `run_stage036_migration_section.py` |
| Phase 3 scenario validation | Passed after repair. Fourteen static scenarios reuse one loaded index/migration/baseline snapshot and preserve the expected real-profile block. | `STAGE036_PHASE3_SCENARIO_VALIDATION.md`; `build_stage036_scenario_validation_report` |
| Phase 4 closeout | Passed after repair. Delivery validity now requires real Path objects, canonical paths, Git tracking, and exact raw index/migration/baseline hashes. | `STAGE036_PHASE4_CLOSEOUT.md`; `build_stage036_delivery_report` |
| Rollback and ownership | Passed after repair. Up and down sections pin `pg_catalog, public`; unowned collisions fail before create/drop, and rollback checks ownership before destructive statements. | `002_database_quality_constraints.sql`; review regressions |
| Governance events | Passed after repair. P1, P2, P3, P4, and review bind exact event types, tasks, acceptances, key evidence, no-upload notes, and review/next-stage gates. | `validate_stage005_governance_regression.py`; `events.jsonl` |
| Raw data boundary | Passed. The raw metadata root remains path-only and untouched. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH031_040_UPLOAD_LOCK.yaml` |

## Findings And Fixes

| Finding ID | Severity | Decision | Fix |
|---|---|---|---|
| `STAGE036-REVIEW-F1` | Medium | Phase 4 correctly stopped before review, but durable whole-stage review evidence and reviewed-local governance state were absent. | Added this review, review event, `completed_reviewed_local` / `reviewed_local_passed` state, and the exact `IDS-STAGE037-P1-GATE` next boundary while retaining `push_allowed=false`. |
| `STAGE036-REVIEW-F2` | Critical | The tracked `-- migrate:up/down` markers were comments; direct `psql` could consume both sections, while the documented `psql --section` option did not exist. | Added a hash-pinned stdout-only section runner. `down` emits only rollback SQL inside its own fail-fast transaction; v0.1 `up` always exits nonzero with empty stdout because trusted authorization-signature and target-database-binding verifiers do not exist. |
| `STAGE036-REVIEW-F3` | Critical | Rollback could reach drops before proving ownership, and unqualified object resolution or same-name objects could target objects not owned by this migration. | Pinned `search_path`, public-qualified every object, placed the registry/ownership gates before every destructive statement, and made any pre-existing target object block apply before create/add operations. |
| `STAGE036-REVIEW-F4` | Important | Unknown safety or authorization fields could be ignored, allowing an unsafe extension to coexist with `contract_valid=true`. | Added exact key-shape validation across root, migration, candidates, guardrails, raw boundary, real-data guard, and authorization envelope. |
| `STAGE036-REVIEW-F5` | Important | Malformed nested JSON and missing SQL sources could raise exceptions rather than return an invalid contract. | Added defensive object/list/text normalization and missing-source handling; malformed contracts now return `FAIL_CLOSED` with no live action. |
| `STAGE036-REVIEW-F6` | Important | Three nonempty GUC strings did not prove authorization scope, bounded candidate queries, zero violations, expiry, backup, rollback, target identity, or evidence provenance. | Added a non-secret authorization-envelope schema and nine fixed bounded count queries/hashes, but retained fail-closed v0.1 behavior: an envelope is evidence structure only and cannot authorize `up`. |
| `STAGE036-REVIEW-F7` | Important | A path-like object could spoof `resolve()`, index raw bytes were not hash-bound, and Git tracking was not checked before reporting `tracked_snapshot_bound=true`. | Require real `Path` instances, canonical paths, `git ls-files --error-unmatch`, exact raw index/migration/baseline/profile-query/runner hashes, and Git tracking for all five delivery sources. |
| `STAGE036-REVIEW-F8` | Important | Stage030-035 dependencies were bound only by schema-version strings, so safety semantics could drift without invalidating Stage036. | Bound all six dependency indexes by exact SHA-256 in both the index and checker; any content drift fails Phase 2 closed. |
| `STAGE036-REVIEW-F9` | Important | Stage005 semantically checked only the STAGE036 P4 event, so P1-P3 event type/task/evidence tampering could be ignored. | Added declarative P1-P4/review semantic specifications, exact event top-level keys, and regressions for ignored earlier phases, malformed containers, contradictory gates, live results, and push values. |
| `STAGE036-REVIEW-F10` | Minor | The Stage-level stop condition still said that entering Phase 4 was forbidden after Phase 4 had already completed. | Replaced the stale boundary with the current rule: this review cannot enter STAGE-037, upload GitHub, reinstall the app, or run batch gates. |
| `STAGE036-REVIEW-F11` | Critical | The first runner repair could still accept mutable/empty query evidence, boolean zero, and reference strings without trusted target binding, allowing `up` authorization to be spoofed. | Bound the exact index, profile-query file, runner, and nine query hashes; require `type(value) is int and value == 0`; and permanently block v0.1 `up` emission until trusted signature and target binding verifiers exist. |
| `STAGE036-REVIEW-F12` | Critical | Same-name pre-existing tables, indexes, or constraints could be mistaken for migration-owned objects without proving exact definitions. | Added a pre-existing-object gate that blocks apply when any Stage036 target object already exists; repeat apply now fails closed instead of skipping or accepting unknown definitions. |
| `STAGE036-REVIEW-F13` | Critical | Rollback could drop constraints before the state-registry nonempty check and relied on an external caller to provide transaction atomicity. | Moved the registry guard before all drops and made `down` emit `ON_ERROR_STOP`, `BEGIN`, and `COMMIT` around the rollback section. |
| `STAGE036-REVIEW-F14` | Important | `tracked_snapshot_bound=true` did not include the profile-query contract or runner, leaving two executable security sources outside Git/hash binding. | Expanded the tracked snapshot to all five delivery sources and bound exact profile-query and runner SHA-256 values. |
| `STAGE036-REVIEW-F15` | Important | Stage030-035 dependency files were read once for parsing and again for hashing, permitting time-of-check/time-of-use drift. | Each dependency source is now read exactly once; the same text is parsed and hashed, with a read-count regression for all six files. |
| `STAGE036-REVIEW-F16` | Important | P1-P3 events could carry gate/live claims or unknown top-level safety fields without semantic rejection. | Require the exact 13 event keys; forbid gate and live-result assignments in P1-P3; require exact unique P4/review gate, live-result, and `push_allowed=false` assignments. |
| `STAGE036-REVIEW-F17` | Important | The checker still reported review pending after governance had transitioned to reviewed-local. | The checker now returns `stage_review_status=completed_reviewed_local` and `next_gate=IDS-STAGE037-P1-GATE` while GitHub upload and app reinstall stay false. |
| `STAGE036-REVIEW-F18` | Minor | The unauthorized-runner regression cleared only a test alias and could inherit the actual authorization-envelope environment variable. | The regression now clears `IDS_STAGE036_AUTHORIZATION_ENVELOPE` explicitly. |
| `STAGE036-REVIEW-F19` | Important | Final checker verification exposed contradictory owner-facing output: machine state was reviewed-local while the top-level feedback and known limit still said the review had not run. | Preserve the Phase 4 contract as historical evidence, but project current reviewed-local owner feedback and limit text at the checker top level; regression rejects the stale review-pending claims. |

## Source And Hash Evidence

- P0 stage entry:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-036_数据库质量约束.md`
- P0 SHA-256:
  `13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b`
- P0 matching entry count: `1`
- Migration SHA-256:
  `52cd624f9e3bec197fa20a14405c7fe2ea149362115c33e9de0145b315dd455a`
- Baseline schema SHA-256:
  `9fa7b8e535fe799c0aed14d738f568b33a19fc2835eeb492c8217bc35b588479`
- Stage036 index SHA-256:
  `016abaa478da1c6cc98513e432429a26402fde5b0b5ac050ec4ceb03aeb33271`
- Stage036 profile-query contract SHA-256:
  `ced8f7f68f43c98d10426a92fdc064b8dbec58f0fd30786fd21decd4ff282ea1`
- Stage036 migration runner SHA-256:
  `dd8640f698df47c1cbe82b1f03ae7580bd2c001639ee3c158bdcb7ffde4c2804`
- Stage030-035 dependency indexes are bound by six exact SHA-256 values in
  `dependency_contract.dependency_index_sha256`.

## Negative Safety Evidence

All adversarial contracts are in-memory mutations. They do not create fake IDS
rows, fixtures, profiles, execution evidence, reports, or runtime outputs.

1. Unknown authorization and safety fields make contract shape validation fail.
2. Null nested containers and missing SQL sources return invalid reports without
   exceptions.
3. The v0.1 `up` runner always returns nonzero with empty stdout, including
   when reference-shaped authorization input is supplied; `down` emits only a
   fail-fast, explicitly transactional rollback section.
4. Dependency hash drift, raw index hash drift, noncanonical paths, spoofed
   path objects, or untracked canonical sources make delivery fail closed.
5. Unowned table/index/constraint collisions block apply and rollback before
   destructive operations.
6. P1-P4/review event type, task, evidence, gate, live-result, or upload-note
   contradictions are rejected.

## Validation Evidence

- Stage036 focused suite: `41 tests OK`.
- Stage005 governance regression suite: `133 tests OK`; validator
  `valid=true`.
- Stage031-036 aggregate suite: `130 tests OK`.
- Stage026-030 compatibility suite: `75 tests OK`.
- Full IDS v0.1 pursuing-goal discovery: `523 tests OK`.
- Checker: `17/17` delivery checks, `10/10` Phase 4 checks, and `9/9`
  source-integrity checks true; status `completed_reviewed_local`; next gate
  `IDS-STAGE037-P1-GATE`; all four live results `NOT_EXECUTED`.
- Runner: `down` emits one explicit transaction; `up` exits nonzero with empty
  stdout and never connects to PostgreSQL.
- Canonical events: `171` objects, zero duplicate IDs, zero semantic errors;
  development events: `9` objects.
- Ten changed Python files parse successfully; owner render check reports
  `drift_count=0` and `reference_issue_count=0`; `git diff --check` passes.
- Changed-only governance synchronization reports zero project sync errors and
  zero warnings. Full semantic validation remains intentionally limited by the
  sparse worktree and reports only the known 29 missing root/unrelated-project
  paths; sparse checkout was not expanded.

No database, raw metadata, runtime output, GitHub, app-install, or STAGE-037
action was part of this validation.

## Decision

`ACC-STAGE-036` is locally reviewed after all nineteen findings from two
independent review rounds plus final checker-output verification are repaired.
The second review explicitly closed its prior `3 Critical`, `4 Important`, and
`1 Minor` findings with no remaining Critical or Important issue; final
verification then found and repaired `F19` before commit.
The final transition is `completed_reviewed_local`; it is an engineering
contract decision, not live PostgreSQL or real-row quality evidence.

## No-Upload Boundary

- `NO_GITHUB_UPLOAD`
- `NO_APP_REINSTALL`
- `NO_STAGE037_THIS_RUN`

The STAGE-031..040 batch remains locked. A single-stage upload, PR, merge,
issue mutation, app reinstall, batch review, or upload gate is not authorized.

## Raw Data Boundary

The local IDS metadata database root is recorded only as:

`/Users/linzezhang/Downloads/IDS_MetaData`

不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

Runtime corpus, database-backed content, profiles, analytics, reports, indexes,
manifests, and committed examples may use only real owner-approved data. 不得使用虚构 IDS 业务数据、虚构数据库行、fake source documents、placeholder
corpus、fabricated profile、fabricated dump 或伪造证据。

## Next Gate

The next run may enter `IDS-V0_1-STAGE037-P1` from
`IDS-STAGE037-P1-GATE`. This review does not enter STAGE-037.

## Rollback

Revert only the `IDS-V0_1-STAGE036-REVIEW` commit to remove review evidence,
review repairs, and the reviewed-local transition while retaining the four
Phase commits. Do not execute SQL or touch raw metadata, PostgreSQL data,
source/runtime databases, rows, dumps, backups, reports, outputs, app entries,
GitHub state, batch gates, or STAGE-037 files.
