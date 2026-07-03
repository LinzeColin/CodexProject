# IDS v0.1 STAGE-026 Phase 4 Closeout

## Scope

- Stage: `STAGE-026 · 压缩包 Manifest`
- Task: `IDS-V0_1-STAGE026-P4`
- Acceptance: `ACC-STAGE-026`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 4 · 压缩包 Manifest 交付证据、整阶段复审、回滚与中文反馈`
- Recorded at UTC: `2026-07-03T07:25:44Z`
- Schema: `ids.stage026.archive_manifest.closeout.v1`

This phase closes out STAGE-026 locally. It records owner-facing archive
manifest closeout evidence and Whole-Stage Review results without creating
screenshots, PDF, JSON output files, runtime reports, archive_manifest runtime
output, databases, evidence ledgers, audit logs, indexes, app-entry changes, or
GitHub changes.

## Delivery Evidence

The Stage 026 delivery surface is the in-memory archive manifest and scenario
validation logic in `KM_IDSystem/scripts/check_archive_manifest.py`.

- `build_archive_manifest` records archive hash, archive entry manifest,
  extracted size, nested depth, failed items, risk items, post-extract
  re-ingest routing, and cleanup allowlist for owner-approved archive/staging
  URIs.
- `build_stage026_scenario_report` validates path traversal, absolute path,
  archive bomb total-size limit, nested archive depth limit, garbled filename,
  and file-count limit scenarios.
- The scenario validation state is
  `ARCHIVE_MANIFEST_SCENARIO_VALIDATION_PASSED`.
- The post-extract re-ingest validation state is
  `POST_EXTRACT_REINGEST_VALIDATED`.
- The cleanup allowlist validation state is
  `ARCHIVE_MANIFEST_CLEANUP_ALLOWLIST_VALIDATED`.

These outputs remain in-memory validation and owner evidence surfaces. They do
not persist production archive manifests or runtime records.

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

STAGE-026 已在本地完成。Review checked and resolved:

1. Phase 1 scope boundary exists and defines archive manifest identifiers,
   staging boundaries, limits, failed/risk item states, and post-extract
   re-ingest routing.
2. Phase 2 implementation exists and routes traversal, absolute path, over
   limit, adapter, missing-source, and raw-root cases to blocked, quarantine,
   or owner-review states.
3. Phase 3 scenario validation exists and covers the required scenario matrix
   with re-ingest and cleanup validation.
4. Phase 4 closeout now records delivery evidence, Whole-Stage Review, raw data
   boundary, rollback, and 中文 owner feedback.
5. `BATCH021_030_UPLOAD_LOCK.yaml` keeps `push_allowed=false`; No GitHub upload
   is allowed until STAGE-021..030 are all complete, reviewed, repaired, and
   app entries are reinstalled after the ten-stage batch upload gate.
6. No app reinstall is performed in this phase.

No finding required production data, service startup, dependency installation,
runtime persistence, app entry reinstall, GitHub upload, PR, merge, or
STAGE-027 work.

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
or commit any content from that root. 中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

Real IDS runtime corpus, database-backed content, analytics inputs, reports,
indexes, manifests, and committed examples must use real user-approved data.
Fake industrial records, fake database rows, fake business documents,
placeholder corpora, fake IDS business data, and fabricated evidence are
forbidden.

Focused tests may use process-owned temporary structural archive fixtures only.
Those fixtures are not IDS corpus, database rows, business evidence, raw
metadata, or committed user data.

## Processing Boundary

- 不写 archive_manifest runtime output.
- 不写 runtime report、database、evidence ledger、audit log、index、document/chunk/job/import row 或 parser output.
- 不启动 hash、manifest、dedup、parser、OCR、Embedding、index、import、backend、frontend、worker 或 external API job.
- 不覆盖、移动、删除、修复、重写、清理或 normalize 原始压缩包、事实源或证据产物.
- cleanup allowlist 只能作为 staging temp file 审查证据，不能被误用为生产删除授权.
- No GitHub upload、PR、merge、app reinstall 或 STAGE-027 work is performed.

## Rollback

rollback:

1. Revert the STAGE-026 Phase 4 closeout file, focused test additions, Stage005
   validator/test changes, batch lock, roadmap/event updates, and rendered
   owner-file changes.
2. Return BATCH021_030 state to STAGE-026 Phase 3 complete and Phase 4 pending.
3. Do not move, delete, overwrite, rewrite, compact, clean, normalize, or
   deduplicate original archives, fact sources, evidence products, manifests,
   audit outputs, runtime databases, reports, outputs, app entries, GitHub
   state, or `/Users/linzezhang/Downloads/IDS_MetaData`.

## 中文 owner feedback

STAGE-026 已在本地完成。当前系统已经具备一个可测试、可复审的压缩包 Manifest
能力：它能在 owner 批准的压缩包和 staging URI 上记录 hash、文件列表、体积、
嵌套层级、失败项、风险项、re-ingest 计划和 cleanup allowlist，并能用场景验证证明
路径穿越、绝对路径、压缩炸弹、嵌套包、乱码文件名和超大文件数都会进入安全状态。

业务上可以把它理解为：系统不会把压缩包直接当作可信数据源导入，而是先形成一份
可审计的 Manifest 和风险清单。安全条目只进入 hash、manifest、dedup、parser 的
后续计划；风险条目进入阻断、隔离或 owner review。当前实现不读取
`/Users/linzezhang/Downloads/IDS_MetaData` 原始数据库内容，不写生产 runtime 输出，也
不启动后续 pipeline。

当前能力仍不是生产导入器、不是清理工具，也不是 GitHub 发布门。真正对真实业务语料
做批量处理、写 manifest/database/index/import/report，或重新安装 app 入口，必须等待
后续明确 Stage 和十阶段批次上传 gate。

## Validation Results

Initial RED evidence:

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage026_archive_manifest -q` failed because `STAGE026_PHASE4_CLOSEOUT.md`, STAGE-026 Phase 4 batch state, roadmap state, and event evidence were missing.
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage026_phase4_archive_manifest_closeout -q` failed because `IDS-V0_1-STAGE026-P4` was not yet accepted by the governance state machine.

Final GREEN evidence is recorded in `KM_IDSystem/docs/governance/roadmap.yaml`
after this run's validation commands are complete.

## Stop Boundary

NO_STAGE027

This run does not execute GitHub upload, PR, merge, app reinstall, service
startup, dependency installation, raw-data processing, archive_manifest runtime
output persistence, or STAGE-027 work.

不执行 GitHub upload、PR、merge 或 app reinstall.
