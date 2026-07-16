# TASK_REPORT · ADP-S3-P02-T034｜接入国务院政策文件与国家法律法规入口

## 唯一目标（达成）
建立 gov.cn **政策/法规原文、文号、日期、状态和附件的 A0 样板** —— 首个真实 A0 官方适配器。交付 connectors、2016/2020/2024/current fixtures、cursor。**官方原文和附件可回放；日期类型不混淆（成文≠发布）；历史游标可恢复。**

## 六个开始前问题（已回答）
1. **唯一目标**：gov.cn 政策/法规 A0 适配器；原文/文号/日期/状态/附件；可回放、日期不混淆、游标可恢复。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/adapter_gov_policy.py, ADAPTER_GOV_POLICY_SPEC.md}` + 本证据包（fixtures/expected/real_parse_smoke/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接 worker。**真抓走开发环境**，NOT_DEPLOYED。
4. **基线**：main `0dbdb451`（T033 收尾 S3-P01）；用 T031 SDK + T032 契约 + T033 身份。真实 DOM 实测确认（元信息表 + 成文≠发布）。
5. **验收**：官方原文和附件可回放；日期类型不混淆；历史游标可恢复。
6. **回滚**：`git revert <sha>`（适配器 + fixtures，生产未变更）。

## 交付物
- `tools/adapter_gov_policy.py` —— `GovCnPolicyConnector`（T031 SDK 7 能力）：`parse_policy` 完整 A0 模板（标题/发文字号/发文机关/**类型化日期 dates.{written,published}**/状态/附件）；`norm_date`（中文/ISO→YYYY-MM-DD，不臆造）；`discover`+`cursor`（断点续爬）；`verify`（走 T033→A0）；`build_registry`（gov-cn-policy + gov-cn-fagui）。
- `ADAPTER_GOV_POLICY_SPEC.md` —— 真实 DOM、类型化日期、能力、边界。
- `evidence/.../fixtures/{policy_2016,2020,2024,current,listing}.html` + `expected/*.json`（golden）+ `real_parse_smoke.json`（实测真文件）。

## 验收结果（实测，见 test-results/adapter_tests.txt，ACCEPTANCE = PASS，exit 0）
- **官方原文和附件可回放**：2016/2020/2024/current 四期解析 **== golden**，二次解析**逐字一致**（replayable），附件 **0/0/1/2** 可回放。
- **日期类型不混淆**：四期 `written==成文`、`published==发布`、`NormalizedDoc.doc_date==发布`，**从不交换/合并**（若合并会被断言拦截）。
- **历史游标可恢复**：discover 全量 **4 项**；`cursor(last_date=2020-12-21)` 只返回其后 `[2024-03-01, 2026-07-10]`；cursor 推进到最新 `2026-07-10`。
- **registry**：`gov-cn-policy` + `gov-cn-fagui` 两源。
- **live 实抓（Owner 决策）**：适配器实测解析 3 篇真实 gov.cn 文件——**国办发〔2020〕50号**（成文 2020-12-07/发布 2020-12-21）、**国令第711号**（2019-04-03/2019-04-15）、**国办函〔2021〕132号**（**成文 2021-12-22/发布 2022-01-04 跨年**），日期类型全部 distinct。

## Data / Performance / Visual
Data = 4 期 fixture + golden + 真文件 live 解析。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED，真抓走开发环境）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：**首个真实 A0 适配器**把国务院政策/法规官方原文（文号/成文·发布日期/状态/附件）结构化，跨 2016–current 可回放、游标可恢复——用 A0 官方原文替换新闻噪声的第一块落地；类型化日期避免把成文/发布混淆（真实跨年案例）。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 适配器 + era fixtures。经常性云成本 delta = $0/月（live 抓取走开发环境）。**接 worker cron 后**每 fetch = Worker 子请求，须核 DIR-007。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接 worker cron）；fixtures 结构化样本非整页（2020 镜像真值）；法规入口共用政策解析（flk.npc.gov.cn 若异需专用解析）；status 关键词匹配；索引号等未全字段化；live 不逐字复现。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = fixtures/ + expected/ + real_parse_smoke.json。

## 完成声明
```text
Task: ADP-S3-P02-T034
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/adapter_gov_policy.py + ADAPTER_GOV_POLICY_SPEC.md + T034 证据包（fixtures/expected/real_parse_smoke/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: adapter_tests.txt —— 四期 parse==golden+replay逐字一致+附件0/0/1/2可回放；日期不混淆(written=成文/published=发布/doc_date=发布)；游标可恢复(discover4/cursor2020-12-21→[2024,2026]/推进2026-07-10)；registry policy+fagui，ACCEPTANCE=PASS(exit 0)；real_parse_smoke 实测3真文件(含2021→2022跨年)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 国务院政策/法规 A0 适配器（原文/文号/类型化日期/状态/附件，可回放）
Data/Performance/Visual: Data=4期fixture+golden+真文件解析；无性能/UI
Value: 首个真实A0适配器，A0官方原文替换新闻噪声第一块落地
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0；真抓走开发环境
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（未接 worker cron）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
