# TASK_REPORT · ADP-S1-P02-T012｜定义统一 Source Registry Schema

## 唯一目标（达成）
覆盖现有五板块与中国 A0–A2，并区分 official evidence 与 discovery —— 交付 schema、authority enum、source identity、enable/health/cursor fields。

## 六个开始前问题（已回答）
1. 唯一目标：定义统一来源注册表 schema（单一来源事实基座），编码权威分级与官方/发现区分。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{schemas/source_registry.schema.json, tools/validate_source_registry.py, source_registry.sample.json}` + 本证据包 + 治理同步。
3. 绝不能改变：现有抓取行为/六主题/worker（本任务只定义 schema，NOT_DEPLOYED，不迁移不改 worker）。
4. 基线：main `00c855a5`（T011 已合入）。
5. 验收：A0/A1/A2 以外的中国官方等级验证失败；媒体不得标为官方证据。
6. 回滚：`git revert <sha>`（纯 schema/工具，NOT_DEPLOYED）。

## 交付物
- `schemas/source_registry.schema.json` —— draft-07：source identity（source_id 唯一/name/board/platform/website/feed_url/method）、**authority enum**（china_official/intl_official/journal/preprint/media/search/aggregator）、authority_level（china_official 限 A0/A1/A2）、official_evidence、**enable/health/cursor**（enabled/health_status/cursor/cadence）。条件规则：china_official→level∈{A0,A1,A2}；media/search/aggregator→official_evidence=false。
- `tools/validate_source_registry.py` —— schema 校验 + 两条硬规则 + source_id 唯一性。
- `source_registry.sample.json` —— 覆盖五板块 + 中国 A0/A1/A2 + 媒体/聚合 discovery 的合法样例（7 源）。

## 验收结果（实测，见 test-results/registry_schema_tests.txt）
- **正例**：合法样例 → VALID（exit 0）。
- **A0/A1/A2 以外中国官方等级失败**：china_official level `A3` → INVALID（schema + 硬规则双拦截）；china_official 缺 level → INVALID。
- **媒体不得标官方证据**：media `official_evidence=true` → INVALID（schema const false + 硬规则）。
- **source identity 唯一**：重复 source_id → INVALID。

## Data / Performance / Visual
N/A —— 纯 schema/工具，无数据/性能/UI；未碰 worker（NOT_DEPLOYED）。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：来源单一事实的 schema 基座——权威分级（中国 A0-A2）与官方/发现区分被机器强制，media 永不能冒充官方证据；为 T013 迁移、T014 编译器、T015 drift CI 打底，直击 DRIFT-FACT-006。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 0；R2 0；模型调用 0；人工维护 = 新来源填一行并过 validator。经常性云成本 0。

## Known gaps
见 known_gaps.md（本任务只定义 schema，不迁移真实来源=T013；sample 的省/市为占位示例）。

## 不适用证据项
`migration.sql/rollback.sql`（无 D1 schema）、`benchmarks`、`screenshots-or-videos`、`data-samples`、`deployment_manifest.preview.json`(T009覆盖) —— N/A。

## 完成声明
```text
Task: ADP-S1-P02-T012
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: schema + validator + sample + 证据 + 治理同步（见 changed_files.txt）
Tests: registry_schema_tests.txt —— 正例 VALID + 4 负例(A3/缺level/media官方/重复id)全 INVALID；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: source_registry.schema.json + validate_source_registry.py + sample（五板块+A0-A2+discovery）
Data/Performance/Visual: N/A
Value: 来源单一事实 schema 基座（权威分级+官方/发现区分强制），直击 DRIFT-FACT-006
Cost: 请求0 / D1 0 / R2 0 / 模型 0 / 人工=新源填一行过 validator；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯 schema/工具）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
