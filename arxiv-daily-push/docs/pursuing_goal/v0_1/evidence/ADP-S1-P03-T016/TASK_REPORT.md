# TASK_REPORT · ADP-S1-P03-T016｜建立五板块 Factsheet Schema 与确定性抽取

## 唯一目标（达成）
先抽取稳定事实，再生成文字 —— 交付 common + board extensions schema、日期/文号/DOI/单位抽取器。

## 六个开始前问题（已回答）
1. 唯一目标：建立 Factsheet schema + 确定性抽取器，先抽稳定事实（缺失=null），再谈生成文字。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{schemas/factsheet.schema.json, tools/extract_factsheet.py, factsheet_baseline_200.json}` + 本证据包 + 治理同步。**只读 D1 抽 200 样本，不改 worker/D1**。
3. 绝不能改变：抓取行为、六主题、worker、D1 数据（NOT_DEPLOYED，只读）。
4. 基线：main `e89ba10d`（T015 已合入）；样本 = 线上 D1 cn_items 最近 200 条（read-only，changed_db=False）。
5. 验收：缺失字段为 null；200 个样本 P0 字段有基准。
6. 回滚：`git revert <sha>`（纯 schema/工具/数据样本，NOT_DEPLOYED）。

## Owner 决策（2026-07-16）
S1-P03 的「人工基准」按 Owner 指令**暂用机器基准并标 `provisional_machine`**（待 Owner 抽查复核），不捧造人工标签。

## 交付物
- `schemas/factsheet.schema.json` —— common（title/url/date/authors/doi/categories，每项 value-or-null）+ board_ext（doc_number/agency/venue/units）+ p0_present。
- `tools/extract_factsheet.py` —— 确定性抽取器：date（ISO→YYYY-MM-DD）/DOI（10.xxxx/…）/文号（〔20xx〕N号 等）/单位（%/亿元/万/bps…）/authors；缺失→null。
- `factsheet_baseline_200.json` —— 200 样本 provisional machine baseline（P0 字段抽取，标 provisional_machine）。

## 验收结果（实测，见 test-results/factsheet_tests.txt）
- **缺失字段为 null（不捧造）**：每条 common 六字段均 value-or-null（True）；缺 published_at→date=null、无文号→doc_number=null（负测确认）。
- **200 样本 P0 基准**：200 条全部抽取；schema validate(200)=PASS；P0 覆盖（provisional）：title/url/date 三板块 **100%**；board2 doi 60/86、board3 doc_number 2/85（board3 现为媒体非政策文，故文号少——与 DRIFT-FACT-006 一致，如实反映）。
- **确定性**：重抽字节一致（True，无时间戳/随机）。
- **provisional 标注**：200 条 baseline_status 全 `provisional_machine`。

## Data / Performance / Visual
- Data：只读 D1 抽 200 行（changed_db=False），产出 200 factsheet（未写 D1）。
- Performance/Visual：N/A（未碰运行时/UI）。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：内容生成前先有**确定性事实层**（factsheet），关键字段（日期/DOI/文号/单位）机器抽取、缺失显式 null、可复现——为 T017 缺陷基线、T018 L0-L3 人话版 + Evidence Locator 供事实锚；直击 FACT-002（英文直出/模板化）的治理前提。
- **Cost（逐项，未知不填 0）**：新增请求 = 1 次只读 D1 SELECT（200 行）；D1 rows_read ≈ 200；D1 写 0；R2 0；模型调用 0；人工维护 = Owner 抽查确认 provisional 基准（后续）。经常性云成本 0。

## Known gaps
见 known_gaps.md（人工基准 provisional 待 Owner 抽查；board1 未在近 200 样本；agency 抽取未实现）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（无 UI）、`benchmarks`（无性能）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。`data-samples`=factsheet_baseline_200.json + items_first5.json。

## 完成声明
```text
Task: ADP-S1-P03-T016
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: factsheet.schema.json + extract_factsheet.py + factsheet_baseline_200.json + 证据 + 治理同步（见 changed_files.txt）
Tests: factsheet_tests.txt —— schema(200) PASS + 缺失=null True + 确定性 True + P0 覆盖(title/url/date 100%)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Factsheet schema + 确定性抽取器 + 200 provisional 基准（P0 字段）
Data/Performance/Visual: 只读抽 200 行（未写 D1）
Value: 生成前先有确定性事实层（FACT-002 治理前提）
Cost: 请求=1只读 D1 SELECT / D1 rows_read≈200 / 写0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md（人工基准 provisional 待 Owner 抽查）
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯 schema/工具/样本）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
