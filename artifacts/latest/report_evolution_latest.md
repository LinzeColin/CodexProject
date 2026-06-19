# TAB FIFA Report Evolution / 新旧报告变化总控台

本 Dashboard 汇总日报 diff、报告族覆盖、推荐操作变化、策略表现变化和产品完成度变化。它服务于每日 automation 复盘，不自动下注。

## Executive Summary

- status: `tracking_ready`
- evolution_score: `100.00%`
- report_diff_count: `20`
- current_report_family_count: `21`
- old_new_compare_count: `21`
- catalog_compare_status: `compared`
- recommended_next_action: 保持该 Dashboard 随每日报告生成；raw/private/preflight 通过前继续 fail-closed。

## 报告目录新旧变化

- current_snapshot: `report-visual-inventory-2026-06-13T144504-599834-1000`
- previous_snapshot: `report-visual-inventory-2026-06-13T143803-813702-1000`
- report_count_delta: `0`
- changed_report_count: `1`

| 报告 | 当前状态 | 上次状态 | 得分变化 | 图表变化 | 附表变化 | 缺口 |
|---|---|---|---:|---:|---:|---|
| 主动测试时间线 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 自动化候选配置 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| Automation Doctor | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| Automation 成熟度验收 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 自动化就绪审计 | 完整 | 完整 | +0.00pp | 0 | -2 |  |
| 可用板块策略 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 本地业务 Dashboard | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 公开赛程校验 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 目标验收追踪 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| TAB Live 板块发现 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 开源模型对比 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 模型分歧复核 Dashboard | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 持仓监控 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 产品完成度 Dashboard | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| Raw 恢复与补跑控制台 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 推荐操作 Dashboard | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 新旧报告变化总控台 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 报告索引 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 研究智能层 | 完整 | 完整 | +0.00pp | 0 | 0 |  |
| 开源模型库 Dashboard | 完整 | 完整 | +0.00pp | 0 | 0 |  |

## 业务信号变化

| 信号 | 状态 | 当前值 | 新旧状态 | 风险说明 |
|---|---|---|---|---|
| 推荐操作 | research_only_blocked | 候选 0 / 可执行 AUD 0 | compared | raw blocked 时执行金额保持 0。 |
| 策略表现 | tracking_ready_outcome_pending | 买入样本 427 / 加权EV 12.89% | compared | ROI=outcome_pending；CLV=clv_pending。 |
| 产品完成度 | in_progress | 8/4/1 ready/partial/blocked | compared | 当前可执行新增金额 AUD 0。 |

> 本报告只汇总已有数据库和公开产物；不伪造 TAB live odds、结算结果、CLV 或 ROI。

> 只生成研究报告和本地数据库快照，不点击赔率、不添加 下注单、不提交下注。