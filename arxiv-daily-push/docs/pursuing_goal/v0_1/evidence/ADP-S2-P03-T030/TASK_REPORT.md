# TASK_REPORT · ADP-S2-P03-T030｜Queue/Workflows 编排与成本决策实验

## 唯一目标（达成）
先比较 **Cron+Queue 与 Workflows**，用**幂等实验 + 成本 benchmark** 决定是否引入新增复杂度；结论**保持简单路径**。交付 at-least-once envelope、DLQ、idempotency test、step/operation 成本 benchmark、ADR。**收尾整个 Stage S2。**

## 六个开始前问题（已回答）
1. **唯一目标**：编排可靠性/成本决策；Workflows 仅当可靠性收益 > 新增步骤费+维护复杂度才采用，否则保持简单路径。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/idempotency_harness.py, ORCHESTRATION_ADR.md}` + 本证据包（orchestration_report / test-results / 报告）+ 治理同步。
3. **绝不能改变**：抓取行为、六主题动效、worker、生产 D1/R2、cron、生产编排；不引入付费依赖。NOT_DEPLOYED。
4. **基线**：main `6f165a14`（T029 已合入）；依赖 T023 成本、T026 版本幂等、DIR-007 免费档硬约束。
5. **验收**：Workflows 只有在可靠性收益高于新增步骤费用和维护复杂度时采用；否则保持简单路径。
6. **回滚**：`git revert <sha>`（纯决策 + 实验，生产未变更）。

## 交付物
- `tools/idempotency_harness.py` —— **at-least-once 投递 + 幂等处理器 + DLQ** 仿真（证明 exactly-once 效果）+ **operation-cost benchmark**（三路径月 Queue ops / Workflow steps / D1 ops + 免费/付费归属 + DIR-007）。
- `ORCHESTRATION_ADR.md` —— Cron+Queue vs Workflows 的 ADR，含约束、候选路径表、可靠性论证、**决策**与重估条件。
- `evidence/.../orchestration_report.json` —— 机器可读仿真 + benchmark + 决策。

## 验收结果（实测，见 test-results/orchestration_tests.txt，ACCEPTANCE = PASS，exit 0）
- **at-least-once envelope + DLQ 被实际演练**：40 逻辑任务 → **55 次投递（确有重复）**、幂等键去重 → **36 个效果各应用一次**、**4 个 poison → 全部进 DLQ**、**无任何效果应用两次**。
- **idempotency test（exactly-once 效果）**：`exactly_once_effect=True`、`no_effect_applied_twice=True`、`poison_all_in_dlq=True` —— 免费档 **Cron + 幂等键（D1 upsert）+ D1 DLQ** 即得 at-least-once 下 exactly-once 效果。
- **step/operation 成本 benchmark**：Path A（Cron+D1 幂等）**免费、DIR-007 OK、0 queue ops / 0 workflow steps**；Path B（Queue）与 Path C（Workflows）**均需 Workers Paid**、新增 ~1170 queue ops / ~480 workflow steps/月、**DIR-007 不通过**。
- **决策符合验收**：**保持 Path A（免费简单路径），不引入 Queues/Workflows**——本规模无可靠性增益，且 B/C 需离开免费档（DIR-007 阻断）+ 更高成本/复杂度。

## 关键决定性事实
**Cloudflare Queues 与 Workflows 均需 Workers Paid（$5/月起），Free 档不可用** → 采用即触发 **DIR-007** 停线（须 Owner 付费授权）。当前 Cron（免费）+ D1（免费）+ worker 内幂等（T022 HEAD-check）已近 exactly-once → 无需付费编排。

## Data / Performance / Visual
Data = 仿真结果 + 成本 benchmark（机器报告）。无性能路径、无 UI 改动；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED，未改编排）。

## Value / Cost（S2 Durable Evidence & Versioning）
- **Value**：以证据（幂等仿真 + 成本 benchmark）作出编排决策——每日流水线**保持免费、简单、可靠**（exactly-once 效果 + DLQ），避免为不存在的可靠性缺口引入付费编排与维护复杂度；决策与 DIR-007 一致。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = 决策 + 仿真，未接生产。经常性云成本 delta = $0/月。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（D1 DLQ 账本是设计未接线）；benchmark 为结构性计数非厂商单价；仿真非真实 Queue（真实需付费档）；样本规模固定；未含跨步持久化场景（触发 ADR 重估条件）。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`（性能）、`deployment_manifest.preview.json` —— N/A。`data-samples` = orchestration_report.json。

## 完成声明
```text
Task: ADP-S2-P03-T030
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/idempotency_harness.py + ORCHESTRATION_ADR.md + T030 证据包（orchestration_report/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: orchestration_tests.txt —— at-least-once+DLQ 演练(55投递/36效果各一次/4 poison→DLQ)+exactly-once 效果+成本 benchmark(A免费/B·C需付费DIR-007阻断)+决策保持简单路径，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 编排成本决策 ADR（保持免费 Cron 幂等路径，不引入 Queues/Workflows）
Data/Performance/Visual: Data=仿真+成本 benchmark；无性能/UI
Value: 每日流水线保持免费/简单/可靠（exactly-once+DLQ），决策与 DIR-007 一致
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（决策+实验，未改编排）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
