# TASK_REPORT · ADP-S0-P02-T007｜生成 Verified/Unknown/Assumption Drift Report

## 唯一目标（达成）

把公开事实、Owner 指令、推断、未知和过期事实分开 —— 交付 FACT_LEDGER.csv、DRIFT_REPORT.md、阻断清单。

## 六个开始前问题（已回答，方允许编码）

1. 唯一目标：汇总 T004-T006，产出分类事实台账 + 漂移报告 + 阻断清单，P0 未知派到明确任务。
2. 允许修改文件：仅 `docs/pursuing_goal/v0_1/{FACT_LEDGER.csv, DRIFT_REPORT.md, BLOCKING_LIST.md}` + 本证据包 + 治理同步文件；无代码/worker/schema。
3. 绝不能改变：已上线 MVP、六主题、高级动效、实时稳定；不修复漂移（只登记分类）。NOT_DEPLOYED。
4. 基线：main `a4a9954b`（= origin/main，T006 已合入）；T004/T005/T006 基线与证据已在库。
5. 验收：任何需求不得由 UNKNOWN 直接推导；P0 未知项分配到明确任务；CSV 可解析。
6. 回滚：`git revert <sha>`；纯文档汇总，NOT_DEPLOYED，无生产影响。

## 交付物

- `docs/pursuing_goal/v0_1/FACT_LEDGER.csv` —— 20 行分类台账（VERIFIED_PUBLIC/OWNER_DIRECTIVE/VERIFIED_PRIVATE/UNVERIFIED_PRIVATE/ASSUMPTION/DRIFT/STALE/PARTIAL），每行含 verification_status + assigned_task_or_gate。
- `docs/pursuing_goal/v0_1/DRIFT_REPORT.md` —— Verified/Unknown/Assumption/Stale/Drift 分区汇总。
- `docs/pursuing_goal/v0_1/BLOCKING_LIST.md` —— 阻断清单（A 阻断项→S0 Exit Owner，B 漂移→具名任务，C 不阻断，D 硬约束）。

## 验收结果

- **CSV 可解析**：`csv.DictReader` → 20 行 7 列；分类分布 VERIFIED_PUBLIC 4 / DRIFT 5 / OWNER_DIRECTIVE 3 / VERIFIED_PRIVATE 3 / UNVERIFIED_PRIVATE 2 / PARTIAL 1 / STALE 1 / ASSUMPTION 1。
- **P0 未知全部分配**：FACT-013、FACT-015（唯二 UNVERIFIED）→ 均 `S0_EXIT_owner`；FACT-014 PARTIAL → 后续 S1 部署纪律；3 处 DRIFT → 具名后续任务。
- **无需求由 UNKNOWN 推导**：DRIFT_REPORT §3 + BLOCKING_LIST §D 明确「UNKNOWN ≠ 需求、≠ 0」；FACT-016 假设显性标注，实测 D1 1.05MB 反驳 20TB 臆造。
- **五类分离**：公开事实 / Owner 指令 / 推断(PARTIAL) / 未知 / 过期(STALE) / 漂移 / 假设 完全分区。

## Data / Performance / Visual

N/A —— 纯文档汇总，无数据/性能/UI 变更。

## Value / Cost

- Value：将幻觉风险变成**可审计缺口**；后续任务引用事实前查 classification/verification_status，防止按未知/过期/漂移开发。
- Cost：**0 经常性云成本**；NOT_DEPLOYED。UNKNOWN 私有事实（FACT-013/015）见 known_gaps（不记为 0）。

## 不适用证据项

`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（无 UI）、`benchmarks`（无性能）、`data-samples`（无数据）、`test-results`（无代码测试；CSV 解析见 commands.log；治理门见提交步骤）、`deployment_manifest.preview.json`（NOT_DEPLOYED）—— 均 N/A。

## 完成声明

```text
Task: ADP-S0-P02-T007
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: 3 交付（FACT_LEDGER.csv/DRIFT_REPORT.md/BLOCKING_LIST.md）+ 证据 + 治理同步（见 changed_files.txt）
Tests: CSV 解析 PASS（20 行；FACT-013/015 均分配 S0_EXIT_owner，commands.log）；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: FACT_LEDGER.csv（20 行分类）+ DRIFT_REPORT.md + BLOCKING_LIST.md
Data/Performance/Visual: N/A
Value: 幻觉风险 → 可审计缺口；P0 未知全部具名
Cost: 0 经常性云成本（FACT-013/015 UNKNOWN 待 S0 Exit，不记为 0）
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯文档汇总）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
