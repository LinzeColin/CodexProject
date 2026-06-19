# TAB FIFA 策略表现 / CLV / ROI 回测 Dashboard

本报告把历史推荐、EV/Edge、仓位、门禁状态和回测准备度汇总为策略复盘面板。没有真实结算或收盘赔率时，不计算虚假 ROI/CLV。

## Executive Summary

- status: `tracking_ready_outcome_pending`
- recommendation_count: `2318`
- buy_recommendation_count: `427`
- research_stake_aud: `AUD 5,210`
- expected_profit_aud: `AUD 671`
- stake_weighted_ev: `12.89%`
- average_edge: `+3.05pp`
- realized_roi_status: `outcome_pending`
- clv_tracking_status: `clv_pending`
- backtest_readiness_score: `75.00%`
- recommended_next_action: 先导入只读 私有持仓 结算快照；在此之前只展示 EV/Edge 样本，不计算真实 ROI。

## 新旧变化

- compare_status: `compared`
- previous_generated_at: `2026-06-13T14:37:24.990391+10:00`
- buy_count_delta: `7`
- stake_delta_aud: `AUD 70`
- stake_weighted_ev_delta: `+0.00pp`

## 板块表现

| 板块 | 推荐数 | 买入样本 | 研究金额 | 预期收益 | 加权EV | 平均Edge | 真实结果 |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026 World Cup Matches | 427 | 427 | AUD 5,210 | AUD 671 | 12.89% | +3.05pp | outcome_pending |
| 2026 World Cup Australia Markets | 854 | 0 | AUD 0 | AUD 0 | 0.00% | +0.00pp | outcome_pending |
| 2026 World Cup Futures | 366 | 0 | AUD 0 | AUD 0 | 0.00% | +0.00pp | outcome_pending |
| 2026 World Cup Group Betting | 366 | 0 | AUD 0 | AUD 0 | 0.00% | +0.00pp | outcome_pending |
| 2026 World Cup Team Futures Multi | 305 | 0 | AUD 0 | AUD 0 | 0.00% | +0.00pp | outcome_pending |

## EV 分桶

| EV桶 | 买入样本 | 研究金额 | 预期收益 | 加权EV | 结算ROI | 状态 |
|---|---:|---:|---:|---:|---|---|
| EV < 0 | 0 | AUD 0 | AUD 0 | 0.00% | outcome_pending | empty_bucket |
| 0% <= EV < 5% | 100 | AUD 1,025 | AUD 41 | 3.96% | outcome_pending | tracking_ready_outcome_pending |
| 5% <= EV < 10% | 135 | AUD 1,610 | AUD 118 | 7.35% | outcome_pending | tracking_ready_outcome_pending |
| EV >= 10% | 192 | AUD 2,575 | AUD 512 | 19.90% | outcome_pending | tracking_ready_outcome_pending |
| EV missing | 0 | AUD 0 | AUD 0 | 0.00% | outcome_pending | empty_bucket |

> 本报告不伪造赛果、收盘赔率、CLV 或 ROI；缺失时统一标记 outcome_pending / clv_pending。

> 该报告只用于自动化策略复盘和概率校准，不自动下注、不点击赔率、不添加 下注单。