# IDS v0.1 STAGE-011 Phase 4 Closeout - Safe-Mode Baseline

- Stage: `STAGE-011`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE011-P4`
- Acceptance ID: `ACC-STAGE-011`
- Recorded UTC: `2026-07-02T11:55:24Z`
- Scope: local closeout, whole-stage review, app-entry preservation, delivery evidence, rollback, default configuration, and owner feedback only.

## Goal

Close out the STAGE-011 safe-mode baseline by recording final environment,
path, storage-budget, safe-mode, and external-API-budget evidence. This closeout
also records recoverable and non-recoverable safe-mode states, app entry/icon
preservation, rollback steps, default configuration notes, and Chinese
owner-facing feedback.

This phase does not start services, install dependencies, create runtime data,
read raw metadata content, call external APIs, generate reports, run OCR, run
Embedding, build indexes, copy backups, write manifests, push to GitHub, or
enter STAGE-012.

Marker: `STAGE011_PHASE4_CLOSEOUT_STAGE_REVIEW_APP_ENTRY_DONE_NO_GITHUB_UPLOAD`.

## Phase Evidence Summary

| Phase | Local result | Evidence |
|---|---|---|
| Phase 1 | Completed. Defined safe-mode scope, input/output boundaries, raw-data rules, pause/resume rules, state names, and no-upload boundary. | `STAGE011_ENTRY_CONTRACT.md`, `STAGE011_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 | Completed. Implemented read-only safe-mode baseline preflight and JSON CLI. | `STAGE011_PHASE2_SAFE_MODE_BASELINE.md`, `KM_IDSystem/scripts/check_safe_mode_baseline.py`, `tests/test_stage011_safe_mode_baseline.py` |
| Phase 3 | Completed. Validated drive lifecycle, storage protection, path blocking, index failure, API budget exhaustion, paused workflows, and no-side-effect guardrails. | `STAGE011_PHASE3_SCENARIO_VALIDATION.md`, `KM_IDSystem/scripts/check_safe_mode_baseline.py`, `tests/test_stage011_safe_mode_baseline.py` |
| Phase 4 | Completed locally in this closeout. ACC-STAGE-011 evidence, whole-stage review, app entry/icon preservation, recoverability, rollback, Chinese owner feedback, and no-upload stop line are recorded. | `STAGE011_PHASE4_CLOSEOUT.md`, `BATCH011_020_UPLOAD_LOCK.yaml`, `roadmap.yaml`, `events.jsonl` |

## Whole-Stage Review

| Review item | Evidence | Finding | Fix status |
|---|---|---|---|
| Phase 1 boundary matches P0 taskpack and keeps raw-data restrictions | `STAGE011_ENTRY_CONTRACT.md`, `STAGE011_PHASE1_SCOPE_BOUNDARY.md` | Pass. Stage hash, source index, no raw read, and no-upload rules are recorded. | No fix needed |
| Phase 2 safe-mode interface remains read-only and operations-only | `check_safe_mode_baseline.py`, focused tests | Pass. The interface composes STAGE-006..010 inputs and keeps no-side-effect flags true. | No fix needed |
| Phase 3 scenario coverage includes required exception matrix | `build_stage011_scenario_report(...)`, focused tests | Pass. Scenario states cover drive, storage, path, index, API budget, and pause workflows. | No fix needed |
| Storage pressure maps to storage safe mode | Phase 3 scenario evidence | Finding found in Phase 3: upstream `STORAGE_BLOCKED` initially mapped to generic path block. | Fixed in Phase 3 by mapping to `SAFE_MODE_STORAGE_BLOCKED` |
| Governance validator recognizes STAGE-011 P4 terminal state | Stage005 governance regression test | Finding found in Phase 4: validator did not allow `IDS-V0_1-STAGE011-P4` closeout. | Fixed in Phase 4 validator update |
| Phase 4 closeout evidence exists | Stage005 governance regression test | Finding found in Phase 4: full discover failed while this closeout file was missing. | Fixed by this closeout |
| App entry and icon are preserved | `scripts/install_app_entries.sh`, installed app checks | Pass. Downloads and Applications entries were installed and verified with icon and signatures. | No fix needed |
| Upload gate remains locked | `BATCH011_020_UPLOAD_LOCK.yaml` | Pass. `push_allowed=false`; STAGE-012..020 remain pending. | No fix needed |
| Raw data boundary remains intact | `IDS_METADATA_RAW_DATA_BOUNDARY.md`, batch lock, tests | Pass. `/Users/linzezhang/Downloads/IDS_MetaData` was not listed, opened, hashed, copied, moved, deleted, modified, dumped, or scanned. | No fix needed |

## App Entry And Icon Preservation

The current app entry was installed during Phase 4 after user instruction.

Installed entries:

- `/Users/linzezhang/Downloads/IDS Industrial Data System.app`
- `/Applications/IDS Industrial Data System.app`
- `/Users/linzezhang/Downloads/IDS Industrial Data System.command`
- `/Applications/IDS Industrial Data System.command`

Verification:

- both `.app` bundles exist;
- both `.command` launchers exist and are executable;
- both `.app` bundles have `CFBundleName=IDS Industrial Data System`;
- both `.app` bundles have `CFBundleDisplayName=IDS Industrial Data System`;
- both `.app` bundles have `CFBundleIconFile=OpMeIcon`;
- both `.app` bundles contain `Contents/Resources/OpMeIcon.icns`;
- both `.app` bundles have executable `Contents/MacOS/IDSIndustrialDataSystem`;
- both `.app` bundles passed `codesign --verify --deep --strict`;
- source icon assets remain tracked as `app_bundle/assets/OpMeIcon.png`
  (`1024x1024`) and `app_bundle/assets/OpMeIcon.icns`.

The installed app entry points at this long-lived worktree:

`/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS/KM_IDSystem`

Batch upload policy remains unchanged: after STAGE-011..020 all complete,
review, and repair, the batch gate must reinstall app entries again and verify
GitHub, app entry, and local development records are consistent.

## Final Validation

Final local validation for this closeout:

- Stage005 governance regression:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage005_governance_regression.py -q`
  returned `Ran 11 tests ... OK`.
- Stage005 validator:
  `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
  returned `valid=true`, `issue_count=0`, and
  `unexpected_changed_paths=[]`.
- Focused STAGE-011 tests:
  `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage011_safe_mode_baseline.py -q`
  returned `Ran 5 tests ... OK`.
- D02 STAGE-006..011 regression:
  `python3 -B -m unittest` on STAGE-006 through STAGE-011 tests returned
  `Ran 37 tests ... OK`.
- Full v0.1 pursuing-goal discover:
  `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
  returned `Ran 51 tests ... OK`.
- Python syntax check:
  `python3 -B -m py_compile` for `check_safe_mode_baseline.py` and
  `validate_stage005_governance_regression.py` returned exit code `0`.
- App entry verification:
  Downloads and Applications `.app` bundles exist, `.command` launchers are
  executable, both `.app` bundles declare `CFBundleIconFile=OpMeIcon`, and
  both passed `codesign --verify --deep --strict`.
- `git diff --check` returned exit code `0`.
- `scripts/lean_governance.py validate --project KM_IDSystem` returned exit
  code `1` with 29 known sparse/root/registered-project diagnostics and no
  `KM_IDSystem` project regression.
- `scripts/lean_governance.py check-render --project KM_IDSystem` returned
  `drift_count=0` after owner-file rendering.

## Final Decision

`ACC-STAGE-011` is locally satisfied at stage-closeout level as a read-only,
testable, rollback-safe safe-mode baseline for IDS operations.

The accepted capability is intentionally narrow:

- It is an IDS operations entrance diagnostic, not a customer-facing workflow.
- It does not start Docker, backend, frontend, workers, OCR, Embedding,
  indexing, cleanup, backup, manifest, report, or API jobs.
- It does not create, write, repair, or recursively scan `IDS_DATA_ROOT`.
- It does not open, hash, copy, move, delete, dump, scan, or mutate
  `/Users/linzezhang/Downloads/IDS_MetaData`.
- It fails closed for drive offline, reconnected/path-changed, permission
  denied, storage blocked, path blocked, index failed, API budget exceeded, and
  unknown states.
- It keeps future v0.2+ architecture open by making safe mode a deterministic
  preflight and scenario contract rather than a runtime side effect.

## Recoverable States

| State | Recovery path |
|---|---|
| `SAFE_MODE_CLEAR` | Bounded preflight may continue. Do not auto-start data-moving work. |
| `SAFE_MODE_ROOT_NOT_CONFIGURED` | Configure `IDS_DATA_ROOT`, rerun safe-mode preflight, and record operator-visible revalidation. |
| `SAFE_MODE_DRIVE_OFFLINE` | Reconnect external drive, rerun root/path/storage checks, and require explicit revalidation before resume. |
| `SAFE_MODE_REVALIDATION_REQUIRED` | Revalidate path, permission, structure, and storage evidence before any paused workflow resumes. |
| `SAFE_MODE_PERMISSION_DENIED` | Repair filesystem permissions, rerun preflight, and keep data-moving workflows paused until evidence is clean. |
| `SAFE_MODE_STORAGE_BLOCKED` | Free internal disk space or bound planned output, rerun storage budget, and require explicit confirmation. |
| `SAFE_MODE_PATH_BLOCKED` | Correct source URI, processed path, backup path, manifest path, or report export path before side effects. |
| `SAFE_MODE_INDEX_FAILED` | Repair or rebuild index in a later authorized stage, then rerun preflight before dependent retrieval/report workflows. |
| `SAFE_MODE_API_BUDGET_EXCEEDED` | Pause external API calls, confirm budget/quota/key/provider state, or use offline mode only. |
| `SAFE_MODE_UNKNOWN` | Fail closed; require manual operator review and classifiable evidence. |

## Non-Recoverable Stop States

These are stop conditions, not automatic repair tasks:

- Any command that may delete, move, overwrite, enumerate recursively, open,
  dump, or mutate original source materials or `/Users/linzezhang/Downloads/IDS_MetaData`.
- Any action that creates unbounded reports, indexes, embeddings, OCR outputs,
  caches, backup payloads, manifests, runtime files, or generated data.
- Any action that uses fake IDS business data, fake database rows, fake source
  documents, or fabricated evidence.
- Any action that resumes data-moving work after a path, storage, indexing, or
  API budget block without explicit revalidation.
- Any irreversible schema migration, data migration, or runtime state creation.
- Any secret or plaintext API key entering tracked evidence.
- Any push, PR, or merge before STAGE-011..020 are complete, reviewed,
  repaired, batch-gated, and ready for app-entry reinstall.

## Default Configuration Notes

- `IDS_DATA_ROOT` must be explicit. STAGE-011 does not guess, create, or repair
  the external root.
- `source_uri` must remain a local `file://` URI supplied by the caller.
- Derived outputs require explicit, bounded paths and planned output budgets.
- Internal storage thresholds remain inherited from STAGE-009: minimum free
  space `100GiB`, warning free space `200GiB`, and maximum used ratio `85%`.
- `index_state` defaults to `OK` only for bounded preflight tests; failed,
  stale, partial, unknown, or unrecognized states fail closed.
- `api_budget_state` defaults to `OK` only for bounded preflight tests; exceeded,
  over-budget, rate-limited, missing-key, provider-unsafe, unknown, or
  unrecognized states fail closed.
- `customer_visible=false`; this is an IDS operations entrance control.
- `auto_resume=false` for every safe-mode state and bounded preflight.

## Owner Feedback

中文 owner 结论：

- STAGE-011 已在本地完成安全模式基线：磁盘不足、外接盘离线/重连/路径变化、
  权限异常、路径不安全、索引失败、外部 API 超预算都会进入可解释的安全模式。
- 安全模式不会自动恢复数据任务；恢复前必须重新预检并留下可见证据。
- 本阶段没有读写原始数据库，没有生成报告、索引、OCR、Embedding、备份或
  manifest，也没有调用外部 API。
- App 入口已经安装到 Downloads 和 Applications，`.app` 使用 `OpMeIcon.icns`
  图标，`.command` 入口也已放置并可执行。
- 这只是 STAGE-011 本地完成，不代表 STAGE-011..020 批次可上传。GitHub main
  上传和批次级 app 入口重装都要等 STAGE-011 至 STAGE-020 全部完成、复审、
  修复后一起做，不能按单个 Stage 触发。

## Rollback

Rollback this phase by reverting the local `IDS-V0_1-STAGE011-P4` commit.

Rollback does not require data cleanup, dependency cleanup, service restart,
raw metadata repair, external-drive cleanup, report cleanup, runtime database
cleanup, manifest cleanup, index cleanup, OCR/Embedding cleanup, or API quota
cleanup because Phase 4 is evidence/governance plus app-entry installation.

If app entry rollback is needed, remove only these installed entries:

- `/Users/linzezhang/Downloads/IDS Industrial Data System.app`
- `/Applications/IDS Industrial Data System.app`
- `/Users/linzezhang/Downloads/IDS Industrial Data System.command`
- `/Applications/IDS Industrial Data System.command`

Do not alter `/Users/linzezhang/Downloads/IDS_MetaData`.
