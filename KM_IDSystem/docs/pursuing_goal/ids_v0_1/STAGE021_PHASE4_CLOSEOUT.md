# IDS v0.1 STAGE-021 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE021-P4`
- Acceptance ID: `ACC-STAGE-021`
- Stage: `STAGE-021 · 预检确认 UI`
- Phase: `Phase 4`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Marker: `STAGE021_PHASE4_CLOSEOUT_NO_STAGE022_NO_GITHUB_UPLOAD`

## Delivery Evidence

Phase 4 closes out the metadata-only preflight confirmation UI. The delivered
owner-facing helper is:

`KM_IDSystem/scripts/check_preflight_confirmation_ui.py build_preflight_owner_feedback_summary`

It returns an in-memory
`ids.stage021.preflight_confirmation_ui.owner_feedback.v1` object with:

- 预检报告样例
- 风险清单
- 用户确认流程日志
- 估算不确定性
- 失败解释文案
- 回滚方式
- Whole-Stage Review

The helper does not choose an output path, does not persist the report, and does
not create screenshots, PDFs, JSON output files, runtime reports, manifests,
databases, evidence ledgers, audit logs, document rows, chunk rows, job rows,
index rows, or import rows.

## Preflight Report Sample

The report sample is intentionally a compact metadata summary, not raw data and
not a production import report. It includes:

- `overall_state`
- `confirmation_status`
- `file_count_estimate`
- `total_size_bytes_estimate`
- `format_counts`
- `archive_candidate_count`
- `scanned_document_candidate_count`
- `unknown_format_count`
- `oversized_file_count`
- `high_risk_file_count`
- `embedding_token_estimate`
- `external_api_cost_estimate`
- `ocr_page_estimate`
- `index_size_estimate`
- `local_space_pressure`
- `risk_items`
- `cost_items`
- `priority_hint`
- `human_product_entrance_payload`
- `ui_component_contract`

No body text, raw payload, raw database row, source file content, or extracted
business value is included.

## Risk Checklist

The closeout feedback can explain these owner-visible states:

- `COST_SOURCE_NOT_CONFIGURED`
- `COST_SOURCE_BLOCKED`
- `COST_DRIVE_OFFLINE`
- `COST_ARCHIVE_REVIEW_REQUIRED`
- `COST_HIGH_RISK_FILE_PRESENT`
- `COST_LARGE_BATCH_PRESENT`
- `COST_OVERSIZED_FILE_PRESENT`
- `COST_UNKNOWN_FORMAT_PRESENT`
- `COST_INSUFFICIENT_SPACE`
- `COST_LOCAL_SPACE_BLOCKED`
- `COST_LOCAL_SPACE_PRESSURE_HIGH`

## User Confirmation Flow Log

1. 系统展示预检报告样例，owner 先查看文件数量、格式、大小、压缩包、扫描件、OCR/Embedding 估算、风险、成本和优先级。
2. owner 可以选择确认继续；后续 Stage 仍必须保留独立授权，本 Stage 不启动实际导入。
3. owner 可以选择保存预检结果；当前 helper 只提供可序列化内容，不自动落盘。
4. owner 可以选择取消；取消后 document/chunk/job/index/import/manifest/database 写入均保持 0。
5. owner 可以选择分批；系统只生成 metadata batch plan，不启动解析、OCR、Embedding、索引、外部 API 或导入。
6. owner 可以选择跳过高风险文件；压缩包、扫描件、未知格式和可疑候选会进入跳过候选清单。
7. owner 明确确认后，后续 Stage 才能进入批量处理；本 Stage 不授权实际导入。

This satisfies the taskpack requirement for screenshot-or-log evidence using
logs. No screenshot, image, PDF, report, runtime output, or UI automation was
generated in this phase.

## Estimation Uncertainty

- Embedding token 估算使用文件大小元信息代理，不解析正文，也不代表真实 tokenizer 结果。
- OCR 页数估算使用扫描件候选数量和大小代理，不启动 OCR，也不确认图片质量。
- 外部 API 成本估算使用配置单价和元信息工作量代理，不调用任何外部 API。
- 索引体积估算使用 token 代理乘以配置系数，不建立索引。
- 本机空间压力只比较估算输入体积、索引体积和传入 `available_space_bytes`，不替代系统级容量审计。
- 目录处理保持 immediate-child metadata-only，不代表递归扫描或真实生产 corpus 覆盖率。
- 预检确认 UI 只呈现元信息摘要和 owner 决策入口，不代表生产导入已经获批。

## Failure Explanation Copy

| State | Chinese owner message |
|---|---|
| `PREFLIGHT_BLOCKED` | 预检被阻断；来源不可用、越过边界、空间不足或设备离线时，系统不会继续处理。 |
| `PREFLIGHT_OWNER_REVIEW_REQUIRED` | 预检需要 owner 复核；请先查看风险、成本、分批和跳过建议，再决定是否继续。 |
| `PREFLIGHT_READY` | 预检未发现必须阻断项；继续前仍需遵守后续 Stage 的独立授权和审计要求。 |
| `COST_SOURCE_BLOCKED` | 来源不可用或越过安全边界；系统不会继续读取或推断该来源。 |
| `COST_LOCAL_SPACE_BLOCKED` | 本机空间估算不足；请释放空间、缩小批次或更换目标盘后再继续。 |

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

STAGE-021 已在本地完成。Review checked and resolved:

1. STAGE-021 lacked Phase 4 closeout evidence.
   - Resolution: this file records report sample, risk checklist, owner flow log, uncertainty, failure copy, rollback, and Chinese owner feedback.
2. Stage005 governance regression did not yet accept `IDS-V0_1-STAGE021-P4`.
   - Resolution: the test was written first and failed; validator state acceptance is extended for the local closeout.
3. Roadmap and BATCH021_030 lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files point to `IDS-V0_1-STAGE021-P4`.
4. Batch upload risk remains active after STAGE-021 local completion.
   - Resolution: `BATCH021_030_UPLOAD_LOCK.yaml` keeps `push_allowed=false` and moves the next gate to `IDS-STAGE022-P1-GATE`.
5. Raw-data boundary needed explicit closeout restatement.
   - Resolution: this closeout records that no `/Users/linzezhang/Downloads/IDS_MetaData` content was read, listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned, or committed.

No finding required production data, service startup, dependency installation,
app entry reinstall, GitHub upload, PR, merge, or STAGE-022 work.

## Raw Data Boundary

The local IDS metadata database root remains:

`/Users/linzezhang/Downloads/IDS_MetaData`

Codex must not read, list, hash, open, copy, move, delete, modify, dump, scan,
or commit any content from that root. 中文边界原文：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
`/Users/linzezhang/Downloads/IDS_MetaData` 内容。

## Real Data Only Policy

IDS runtime corpus, database-backed content, analytics inputs, reports, indexes,
manifests, and committed examples must use real user-approved data. Fake
industrial records, fake database rows, fake business documents, placeholder
corpora, fake IDS business data, and fabricated evidence are forbidden.

Focused tests may use temporary process-owned structural directories and scalar
boundary values only as test harness state. Those files are not IDS corpus, not
database rows, not business evidence, and are not committed as user data.

## Rollback

回滚方式:

1. Revert the Stage021 Phase4 helper additions, focused tests, closeout evidence, batch lock, roadmap/event updates, Stage005 validator/test changes, and rendered owner-file changes.
2. Do not move, delete, overwrite, rewrite, compact, clean, or normalize original materials.
3. Do not clean `/Users/linzezhang/Downloads/IDS_MetaData`, runtime databases, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, app entries, or GitHub state.
4. After rollback, STAGE-021 should return to Phase 3 complete and Phase 4 pending.

## Chinese Owner Feedback

STAGE-021 已在本地完成。当前系统已经具备一个只读、可测试的预检确认 UI 合同：它可以在批量导入前展示文件数量、格式、体积、压缩包、扫描件、OCR/Embedding 估算、风险、成本、优先级和确认状态，并把继续、暂停、保存、取消、分批、跳过高风险文件等 owner 选择呈现为明确的无副作用决策入口。

业务上可以把它理解为：系统先给出“当前导入是否可继续、是否需要人工复核、是否建议分批、是否应跳过高风险文件”的预检确认结论。当前实现不会解析正文，不会启动 OCR 或 Embedding，不会建立索引，不会调用外部 API，不会写入数据库，也不会创建 document、chunk 或 job。

当前能力仍不是生产导入器。真正读取真实业务语料、写 manifest/database/index/import/report 或进入批量处理，必须等待后续明确 Stage 和 owner 授权。

## Validation Results

Initial RED evidence:

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage021_preflight_confirmation_ui -q` failed because `build_preflight_owner_feedback_summary` and `STAGE021_PHASE4_CLOSEOUT.md` were missing.
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage021_phase4_preflight_confirmation_ui_closeout -q` failed because `IDS-V0_1-STAGE021-P4` was not yet accepted by the governance state machine.

Final GREEN evidence:

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage021_preflight_confirmation_ui -q` ran 13 tests OK.
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage021_phase4_preflight_confirmation_ui_closeout -q` ran 1 test OK.
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression -q` ran 56 tests OK.
- `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py` returned `valid=true`.
- `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q` ran 186 tests OK.
- `python3 -B scripts/lean_governance.py check-render --project KM_IDSystem` returned `drift_count=0`.
- `KM_IDSystem/docs/governance/events.jsonl` parsed as 100 JSONL events.
- `python3 -B -m py_compile` passed for Stage021 helper/test, Stage005 regression test, and Stage005 validator.
- `git diff --check` passed.
- old underscore task-id spelling scan returned no matches.
- added-line legacy pre-rename path scan returned no additions.
- semantic validate was run as a sparse-worktree diagnostic and exited 1 with 29 known missing root/registered-project paths and no KM_IDSystem product error.

## Stop Boundary

NO_STAGE022

This run does not execute GitHub upload, PR, merge, app reinstall, service startup, dependency installation, raw-data processing, or STAGE-022 work.

不执行 GitHub upload、PR、merge 或 app reinstall.
