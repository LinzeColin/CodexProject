# IDS v0.1 STAGE-020 Phase 4 Closeout

- Task ID: `IDS-V0_1-STAGE020-P4`
- Acceptance ID: `ACC-STAGE-020`
- Stage: `STAGE-020 · 导入成本估算器`
- Phase: `Phase 4`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Marker: `STAGE020_PHASE4_CLOSEOUT_NO_STAGE021_NO_GITHUB_UPLOAD`

## Delivery Evidence

Phase 4 closes out the metadata-only import cost estimator. The delivered
owner-facing helper is:

`KM_IDSystem/scripts/check_import_cost_estimator.py build_cost_owner_feedback_summary`

It returns an in-memory
`ids.stage020.import_cost_estimator.owner_feedback.v1` object with:

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
not a production cost report. It includes:

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
- `future_local_space_bytes_estimate`
- `cost_score_band`
- `risk_items`
- `cost_items`
- `priority_hint`
- `human_product_entrance_payload`

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

1. 系统展示预检报告样例，owner 先查看文件数量、格式、大小、Embedding token、OCR 页数、外部 API 成本、索引体积和本机空间压力。
2. owner 可以选择保存成本估算结果；当前 helper 只提供可序列化内容，不自动落盘。
3. owner 可以选择取消；取消后 document/chunk/job/index/import/manifest/database 写入均保持 0。
4. owner 可以选择分批；系统只生成 metadata batch plan，不启动解析、OCR、Embedding、索引、外部 API 或导入。
5. owner 可以选择跳过高风险文件；压缩包、扫描件、未知格式和可疑候选会进入跳过候选清单。
6. owner 明确确认后，后续 Stage 才能进入批量处理；本 Stage 不授权实际导入。

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

## Failure Explanation Copy

| State | Chinese owner message |
|---|---|
| `COST_SOURCE_NOT_CONFIGURED` | 未配置导入来源；请先选择 owner 批准的本地 `file://` 输入。 |
| `COST_SOURCE_BLOCKED` | 来源不可用或越过安全边界；系统不会继续读取或推断该来源。 |
| `COST_DRIVE_OFFLINE` | 移动硬盘或来源盘处于离线状态；请重新接入后再做成本估算。 |
| `COST_ARCHIVE_REVIEW_REQUIRED` | 发现压缩包候选；需要 owner 复核后再决定是否单独处理。 |
| `COST_HIGH_RISK_FILE_PRESENT` | 发现高风险文件；建议先跳过或拆分批次再复核。 |
| `COST_LARGE_BATCH_PRESENT` | 文件数量较多；建议先分批处理并保留人工确认点。 |
| `COST_OVERSIZED_FILE_PRESENT` | 发现超大文件；建议拆分批次或先跳过后复核。 |
| `COST_UNKNOWN_FORMAT_PRESENT` | 发现未知格式；建议跳过或转交人工处理。 |
| `COST_INSUFFICIENT_SPACE` | 目标空间不足；请释放空间或缩小批次后再继续。 |
| `COST_LOCAL_SPACE_BLOCKED` | 本机空间估算不足；请释放空间、缩小批次或更换目标盘后再继续。 |

## Whole-Stage Review

Review result: `passed_with_local_evidence`.

STAGE-020 已在本地完成。Review checked and resolved:

1. STAGE-020 lacked Phase 4 closeout evidence.
   - Resolution: this file records report sample, risk checklist, owner log, uncertainty, failure copy, rollback, and Chinese owner feedback.
2. Stage005 governance regression did not yet accept `IDS-V0_1-STAGE020-P4`.
   - Resolution: the test was written first and failed; validator state acceptance is extended for the local closeout.
3. Roadmap and batch lock still pointed to Phase 3.
   - Resolution: roadmap, batch lock, event log, and owner rendered files point to `IDS-V0_1-STAGE020-P4`.
4. Batch upload risk remains active after STAGE-020 local completion.
   - Resolution: `BATCH011_020_UPLOAD_LOCK.yaml` keeps `push_allowed=false` and moves the next gate to `BATCH011_020_REVIEW_GATE`.
5. Raw-data boundary needed explicit closeout restatement.
   - Resolution: this closeout records that no `/Users/linzezhang/Downloads/IDS_MetaData` content was read, listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned, or committed.

No finding required production data, service startup, dependency installation,
app entry reinstall, GitHub upload, PR, merge, or STAGE-021 work.

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

1. Revert the Stage020 Phase4 helper additions, focused tests, closeout evidence, batch lock, roadmap/event updates, Stage005 validator/test changes, and rendered owner-file changes.
2. Do not move, delete, overwrite, rewrite, compact, clean, or normalize original materials.
3. Do not clean `/Users/linzezhang/Downloads/IDS_MetaData`, runtime databases, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, or GitHub state.
4. After rollback, STAGE-020 should return to Phase 3 complete and Phase 4 pending.

## Chinese Owner Feedback

STAGE-020 已在本地完成。当前系统已经具备一个只读、可测试的导入成本估算能力：它可以在批量导入前估算文件数量、格式、体积、Embedding token、外部 API 成本、OCR 页数、索引体积和本机空间压力，并给出风险、成本、优先级和确认状态。

业务上可以把它理解为：系统先给出“成本是否可接受、是否需要人工复核、是否建议分批、是否应跳过高风险文件”的成本预检结论。当前实现不会解析正文，不会启动 OCR 或 Embedding，不会建立索引，不会调用外部 API，不会写入数据库，也不会创建 document、chunk 或 job。

当前能力仍不是生产导入器。真正读取真实业务语料、写 manifest/database/index/import/report 或进入批量处理，必须等待后续明确 Stage 和 owner 授权。

## Validation Results

Completed local validation:

- Stage020 Phase4 RED failed as expected: focused unittest ran 12 tests with 1 failure and 1 error because `build_cost_owner_feedback_summary` and `STAGE020_PHASE4_CLOSEOUT.md` did not exist.
- Stage005 Phase4 RED failed as expected: governance regression ran 47 tests with 1 failure because `IDS-V0_1-STAGE020-P4` was not yet accepted by the governance state machine.
- Stage005 intermediate RED failed as expected after state-machine wiring: governance regression ran 47 tests with 1 failure because the required Stage020 P4 event was still missing.
- Stage020 focused GREEN: `Ran 12 tests in 0.115s`, `OK`.
- Stage005 governance regression GREEN: `Ran 47 tests in 0.112s`, `OK`.
- Stage005 validator: `valid: true`, `missing_required_files: []`, `missing_event_ids: []`, `unexpected_changed_paths: []`, `forbidden_changed_paths: []`.
- events JSONL parse: `events_jsonl_ok count=93`.
- Full IDS v0.1 pursuing-goal unittest discover: `Ran 164 tests in 2.275s`, `OK`.
- `py_compile` completed for the Phase4 helper, Stage020 focused test, Stage005 validator, and Stage005 regression test.
- Owner render wrote `功能清单.md`, `开发记录.md`, and `模型参数文件.md`; check-render returned `drift_count: 0`.
- `git diff --check` passed.
- Exact legacy underscore task-id spelling scan returned no matches.
- Legacy pre-rename path diff scan returned `legacy_path_hits_in_diff=0`.
- Semantic validate was run as a sparse-worktree diagnostic only. It exited 1 with 29 expected missing root/registered-project paths from the sparse checkout, and did not report a KM_IDSystem semantic error.

## Forbidden Actions Preserved

This phase must not:

- start Docker, backend, frontend, workers, OCR, Embedding, indexing, import, report, backup, manifest, evidence, audit, scanner, or API jobs;
- install dependencies;
- create `.venv/`, `node_modules/`, `data/`, `reports/`, `outputs/`, runtime databases, persisted manifests, evidence ledgers, document rows, chunk rows, job rows, indexes, OCR output, Embedding output, checkpoints, screenshots, PDFs, JSON output files, or backup payloads;
- read, list, hash, open, copy, move, delete, modify, dump, scan, or commit `/Users/linzezhang/Downloads/IDS_MetaData` content;
- move, delete, overwrite, normalize, compact, rename, repair, or deduplicate original files in place;
- use fake IDS business data, fake database rows, fake source documents, placeholder corpora, or fabricated evidence;
- 不执行 GitHub upload、PR、merge 或 app reinstall;
- enter STAGE-021.

## Stop Line

`NO_STAGE021`

This run closes STAGE-020 locally only. It does not perform the
STAGE-011..020 batch review/upload gate, does not push to GitHub, does not open
or merge a PR, and does not reinstall app entries.
