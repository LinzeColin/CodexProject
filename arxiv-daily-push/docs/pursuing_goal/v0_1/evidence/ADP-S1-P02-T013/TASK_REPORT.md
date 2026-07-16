# TASK_REPORT · ADP-S1-P02-T013｜迁移现有全部来源到 Registry

## 唯一目标（达成）
不改变现有抓取行为，先消除 YAML、Worker、D1 和 UI 多份来源真相 —— 交付 migration mapping、registry rows、legacy exception list。

## 六个开始前问题（已回答）
1. 唯一目标：把线上真身（worker REGISTRY 33 源）迁入统一 Registry，消除多份来源真相，抓取行为不变。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{source_registry.json, SOURCE_MIGRATION_MAPPING.csv, SOURCE_LEGACY_EXCEPTIONS.md}` + 本证据包 + 治理同步。**不改 worker/config/D1**（纯数据迁移文档）。
3. 绝不能改变：现有抓取行为、六主题、worker、D1 数据（NOT_DEPLOYED，不碰运行时）。
4. 基线：main `288c76ce`（T012 已合入）；线上真身 = worker_cloud.js REGISTRY（build bd67a78020a3）；33 源，与 D1 cn_sources=33 一致。
5. 验收：迁移前后 fixture 输出相同；每个线上 source_id 在 Registry 唯一。
6. 回滚：`git revert <sha>`（纯文档，NOT_DEPLOYED，不改写生产数据）。

## 交付物
- `source_registry.json` —— 33 条 registry rows（迁自 worker REGISTRY，符合 T012 schema，VALID）。
- `SOURCE_MIGRATION_MAPPING.csv` —— 33 行 worker id → registry source_id（1:1，保 id；权威真相=worker REGISTRY）。
- `SOURCE_LEGACY_EXCEPTIONS.md` —— 例外：EXC-1 board3 媒体标「官方」(DRIFT-FACT-006/FACT-003)、EXC-2 config↔worker board3 不一致、EXC-3 聚合源非官方证据。

## 验收结果（实测，见 test-results/ 与 benchmarks/）
- **迁移前后 fixture 相同**：`benchmarks/before.json`(worker 源集) == `benchmarks/after.json`(registry 源集)——source_id 集合 + 每板块成员完全一致（Python `before==after` = True）。
- **每个线上 source_id 唯一**：33 个 source_id 无重复（True）。
- **registry 符合 T012 schema**：`validate_source_registry.py source_registry.json` → **VALID**（media official_evidence=false，无 china_official 非法等级）。
- **分类**：preprint 3 / journal 17 / media 4 / intl_official 8 / aggregator 1；official_evidence=true 28、=false 5。

## Data / Performance / Visual
- Data before→after：source set 不变（33→33，逐 id 一致）；仅新增 Registry 表征（authority 分级 + 官方/发现区分）。无 D1 写入。
- Performance / Visual：N/A（未碰运行时/UI）。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：来源真相从「worker/config/D1/UI 多份」收敛为**一份 Registry**（33 源），board3 媒体误标「官方」被纠正为 media/非官方证据（DRIFT-FACT-006 止血基础）；抓取行为零变化。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 行读写 0（未碰 D1，源数与 T006 快照 33 一致，未重查）；R2 0；模型调用 0；人工维护 = 新增/改源改 Registry 一处 + 过 validator。经常性云成本 0。

## Known gaps
见 known_gaps.md（board3 尚无真 A0-A2 政府源；config 未对齐；worker/D1 未改由 T014 编译器统一）。

## 不适用证据项
`migration.sql/rollback.sql`（未改 D1 schema；纯文档数据迁移）、`screenshots-or-videos`（无 UI）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。`data-samples` = source_registry.json + benchmarks。

## 完成声明
```text
Task: ADP-S1-P02-T013
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: source_registry.json + mapping + exceptions + 证据 + 治理同步（见 changed_files.txt）
Tests: registry_validate.txt(VALID) + benchmarks before==after(fixture 一致) + source_id 唯一；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 33 源单一 Registry + 迁移映射 + 例外清单；board3 媒体纠正为非官方证据
Data/Performance/Visual: source set 33→33 逐 id 一致（无 D1 写入）
Value: 来源真相收敛为一份（DRIFT-FACT-006 止血基础），抓取行为零变化
Cost: 请求0 / D1 0 / R2 0 / 模型 0 / 人工=新源改 Registry 一处过 validator；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯文档，未改写生产数据）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
