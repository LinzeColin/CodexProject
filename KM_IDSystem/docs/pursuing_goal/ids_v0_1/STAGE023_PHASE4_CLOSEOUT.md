# IDS v0.1 STAGE-023 Phase 4 Closeout

## Scope
- Stage: `STAGE-023 · 预检场景测试`
- Task: `IDS-V0_1-STAGE023-P4`
- Acceptance: `ACC-STAGE-023`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 4 · 预检场景测试 交付证据、回滚与中文反馈`
- Recorded at UTC: `2026-07-03T02:09:54Z`

This phase closes out STAGE-023 locally. It records owner-facing evidence and
whole-stage review results without creating screenshots, PDF, JSON output files,
runtime reports, manifests, databases, evidence ledgers, audit logs, indexes, or
app-entry changes.

## 预检报告样例
The closeout helper `build_preflight_scenario_owner_feedback_summary(...)`
returns an in-memory `report_sample` from
`ids.stage023.preflight_scenario_tests.v1`. It includes:
- `scenario_validation_summary`
- `human_product_entrance_payload`
- `ui_component_contract`
- `embedding_token_estimate`
- `ocr_page_estimate`
- `index_size_estimate`
- `risk_items`
- `cost_items`

The UI component remains `PreflightScenarioTestsPanel`, and the required
scenario vocabulary remains `empty_directory`, `small_directory`,
`large_directory`, `offline_drive`, `bad_file`, `archive_present`, and
`insufficient_space`.

## 风险清单
The closeout risk checklist covers:
- `SCENARIO_SOURCE_NOT_CONFIGURED`
- `SCENARIO_SOURCE_BLOCKED`
- `SCENARIO_OFFLINE_DRIVE`
- `SCENARIO_ARCHIVE_REVIEW_REQUIRED`
- `SCENARIO_BAD_FILE_PRESENT`
- `SCENARIO_HIGH_RISK_FILE_PRESENT`
- `SCENARIO_LARGE_DIRECTORY_REVIEW_REQUIRED`
- `SCENARIO_OVERSIZED_FILE_PRESENT`
- `SCENARIO_UNKNOWN_FORMAT_PRESENT`
- `SCENARIO_INSUFFICIENT_SPACE`
- `SCENARIO_LOCAL_SPACE_BLOCKED`
- `SCENARIO_EMPTY_DIRECTORY`

High-risk files, bad-file candidates, archive candidates, scanned candidates,
unknown formats, oversized files, offline-drive sources, and insufficient-space
states remain owner-review or blocked paths until a later gated flow.

## 用户确认流程日志
1. 系统展示预检报告样例，owner 先查看文件数量、格式、大小、压缩包、扫描件、坏文件、OCR/Embedding 估算、风险、成本和优先级建议。
2. owner 可以选择保存预检结果；当前 helper 只提供可序列化内容，不自动落盘。
3. owner 可以选择取消；取消后 document/chunk/job/index/import/manifest/database/scenario_result 写入均保持 0。
4. owner 可以选择分批；系统只生成 metadata batch plan，不启动解析、OCR、Embedding、索引、外部 API 或导入。
5. owner 可以选择跳过高风险文件；压缩包、扫描件、未知格式、坏文件、超大文件和可疑候选会进入跳过候选清单。
6. owner 明确确认后，后续 Stage 才能进入批量处理；本 Stage 不授权实际导入。

## 估算不确定性
- Embedding token 估算使用文件大小元信息代理，不解析正文，也不代表真实 tokenizer 结果。
- OCR 页数估算使用扫描件候选数量和大小代理，不启动 OCR，也不确认图片质量。
- 外部 API 成本估算使用配置单价和元信息工作量代理，不调用任何外部 API。
- 索引体积估算使用 token 代理乘以配置系数，不建立索引。
- 本机空间压力只比较估算输入体积、索引体积和传入 available_space_bytes，不替代系统级容量审计。
- 坏文件识别只使用 0 字节、扩展名和文件名提示，不解析正文，也不修复源文件。
- 目录处理保持 immediate-child metadata-only，不代表递归扫描或真实生产 corpus 覆盖率。

## 失败解释文案
- `PREFLIGHT_SCENARIO_BLOCKED`: 预检场景被阻断；来源不可用、设备离线或空间不足时，系统不会继续处理。
- `PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED`: 预检场景需要 owner 复核；请先查看风险、成本、分批和跳过建议，再决定是否继续。
- `PREFLIGHT_SCENARIO_READY`: 未发现必须阻断项；继续前仍需遵守后续 Stage 的独立授权和审计要求。
- `SCENARIO_BAD_FILE_PRESENT`: 发现坏文件候选；系统不会修复、删除、复制或移动源文件。
- `SCENARIO_ARCHIVE_REVIEW_REQUIRED`: 发现压缩包候选；系统不会自动解压或解析。
- `SCENARIO_LOCAL_SPACE_BLOCKED`: 本机空间估算不足；请释放空间、缩小批次或更换目标盘后再继续。

## Whole-Stage Review
- Result: `passed_with_local_evidence`
- STAGE-023 已在本地完成.
- Completed phases: `Phase 1`, `Phase 2`, `Phase 3`, `Phase 4`
- Acceptance: `ACC-STAGE-023`
- Next gate: `IDS-STAGE024-P1-GATE`
- Batch upload: `push_allowed=false`
- GitHub upload: not started
- App reinstall: not started
- Unresolved findings: none

## Raw Data And Processing Boundary
- 只读取元信息.
- 不解析正文.
- 不修改原始文件.
- 不启动 OCR.
- 不启动 Embedding.
- 不建立索引.
- 不启动实际导入.
- 不启动 scenario runner.
- 不调用外部 API.
- 不写 manifest、database、evidence ledger、audit log、runtime data、reports、outputs、document/chunk/job/index/import/scenario result row.
- 不生成 runtime 输出、screenshot、PDF、JSON 输出文件或 production preflight report.
- 不安装依赖、不启动服务.
- 不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_STAGE024`: this run must not start STAGE-024 work.

## 回滚方式
1. Revert Stage023 Phase4 helper additions, focused tests, closeout evidence, Stage005 validator/test changes, BATCH021_030 lock, roadmap/event updates, and rendered owner-file changes.
2. Do not move, delete, overwrite, rewrite, compact, clean, normalize, repair, or deduplicate original files in place.
3. Do not clean `/Users/linzezhang/Downloads/IDS_MetaData`, runtime databases, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, app entries, or GitHub state.
4. After rollback, STAGE-023 should return to Phase 3 complete and Phase 4 pending.
