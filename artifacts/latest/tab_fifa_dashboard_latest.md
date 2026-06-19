# TAB FIFA 本地业务 Dashboard

本报告是本地 HTML Dashboard 的正式 Markdown/PDF 镜像，用于把核心入口纳入日报归档、数据库和新旧报告覆盖审计。它只生成研究报告，不自动下注。

## Executive Summary

- report_date: `04062026`
- run_id: `20260604T135753Z-212e8e9a`
- status: `ready_for_manual_report`
- technical_ready: `True`
- automation_entry_ready: `False`
- automation_authorized: `False`
- raw_refresh: `5/5` / ready `True`
- public_safety_ready: `True`
- model_high_divergence_count: `14`
- report_compare: `+0 / -0 / changed 0`

## KPI

| 指标 | 值 | 状态 |
|---|---|---|
| 技术自动化 | 通过 | ok |
| 正式调度入口 | 未授权 | neutral |
| 板块就绪 | 5/5 | ok |
| 新增执行金额 | AUD 100 | alert |
| 报告对比 | +0 / 改0 | ok |
| 模型分歧 | 14场高分歧 | warn |
| 本地数据库 | 已保存 | ok |
| 自动化历史 | 8次 | ok |

## 可视化图表摘要

| 图表 | 类型 | 指标 | 说明 |
|---|---|---|---|
| 板块自动化就绪度 | bar | Matches=100%, Futures=100%, Group Betting=100%, Australia Markets=100%, Team Futures Multi=100% | Raw新鲜度、Raw有效性、gate通过、报告存在四项等权计分。 |
| 新旧报告对比 | bar | 新增=0, 移除=0, 变化=0, 保留=38 | 暴露变化 AUD 0 |
| 盘口推荐分布 | bar | Matches=7个, Futures=6个, Group Betting=6个, Australia Markets=14个, Team Futures Multi=5个 | 红色代表该板块存在新增执行金额，蓝色代表观察池。 |
| 跨板块新增金额分配 | bar | Matches=AUD 100, Futures=AUD 0, Group Betting=AUD 0, Australia Markets=AUD 0, Team Futures Multi=AUD 0 | 金额分配只展示研究建议暴露；正式系统不自动下注。 |
| 比赛盘口价值排序 | bar | France v Senegal / Senegal=23.8%, Brazil v Morocco / Morocco=22.4%, England v Croatia / Croatia=17.1%, Netherlands v Japan / Japan=9.0%, South Korea v Czechia / Only One or Neith…=6.2% | 按正EV排序，红色代表进入执行候选。 |
| 概率-赔率边际 | bar | Brazil v Morocco / Morocco=+4.1%, England v Croatia / Croatia=+3.6%, South Korea v Czechia / Only One or Neith…=+3.3%, Belgium v Egypt / Under 2.5 Goals=+3.2%, France v Senegal / Senegal=+3.2% | 边际 = 模型概率 - 赔率盈亏平衡概率；正值才进入价值观察。 |
| 开源模型分歧 | bar | Germany v Curacao / Germany=28.4%, Portugal v DR Congo / Portugal=24.6%, Spain v Cabo Verde / Spain=24.1%, Iraq v Norway / Norway=23.5%, Uzbekistan v Colombia / Colombia=23.1% | 比较当前市场Poisson、Elo+Dixon-Coles、goalmodel proxy 的最大方向分歧。 |
| 模型共识强度 | bar | Germany v Curacao / Germany=71.5% low, Portugal v DR Congo / Portugal=73.6% low, Spain v Cabo Verde / Spain=76.7% low, Iraq v Norway / Norway=75.3% low, Uzbekistan v Colombia / Colombia=71.0% low | 展示当前市场Poisson、Elo+Dixon-Coles、goalmodel proxy 的共识方向概率。 |
| 开源模型采用覆盖 | bar | Hicruben 2026 WC=5项, goalmodel=5项, RyanSCodes DC=4项 | 绿色代表已进入本地概率交叉验证；琥珀色代表设计参考或下一阶段接口。 |
| 模型能力覆盖矩阵 | bar | 1X2=2/2已接入, 评分规则=1/1已接入, 模型分歧=1/1已接入, 晋级路径=1/1已接入, 回测评价=1/1已接入 | 按开源参考覆盖能力聚合；已接入表示进入本地概率交叉验证或报告证据层。 |

## 推荐候选

| 板块 | 比赛/对象 | 盘口 | 选择 | 赔率 | 概率 | EV | 金额 | 操作 | 模型/理由 |
|---|---|---|---|---:|---:|---:|---:|---|---|
| Matches | France v Senegal | Result | Senegal | 7.50 | 16.5% | 23.8% | AUD 15 | 买入 | 模型交叉验证：三模型概率：市场Poisson 16.51%，goalmodel 15.06%，Elo-DC 12.27%；共识方向France，均值60.68%，置信度medium；最大模型分歧4.84%；当前选择与共识不完全一致，需小仓或观察。 |
| Matches | Brazil v Morocco | Result | Morocco | 5.50 | 22.3% | 22.4% | AUD 15 | 买入 | 模型交叉验证：三模型概率：市场Poisson 22.25%，goalmodel 20.66%，Elo-DC 21.08%；共识方向Brazil，均值51.13%，置信度high；最大模型分歧1.18%；当前选择与共识不完全一致，需小仓或观察。 |
| Matches | England v Croatia | Result | Croatia | 4.75 | 24.6% | 17.1% | AUD 15 | 买入 | 模型交叉验证：三模型概率：市场Poisson 24.65%，goalmodel 23.00%，Elo-DC 22.73%；共识方向England，均值47.93%，置信度high；最大模型分歧1.92%；当前选择与共识不完全一致，需小仓或观察。 |
| Matches | Netherlands v Japan | Result | Japan | 3.60 | 30.3% | 9.0% | AUD 15 | 买入 | 模型交叉验证：三模型概率：市场Poisson 30.27%，goalmodel 28.61%，Elo-DC 24.21%；共识方向Netherlands，均值43.92%，置信度medium；最大模型分歧6.06%；当前选择与共识不完全一致，需小仓或观察。 |
| Matches | South Korea v Czechia | Both Teams to Score | Only One or Neither to score | 1.87 | 56.8% | 6.2% | AUD 15 | 买入 | 模型交叉验证：三模型概率：市场Poisson 56.80%，goalmodel 55.05%，Elo-DC 47.22%；共识方向South Korea，均值41.00%，置信度low；最大模型分歧17.45%；当前选择与共识不完全一致，需小仓或观察。 |
| Matches | Belgium v Egypt | Total Goals Over/Under | Under 2.5 Goals | 1.80 | 58.8% | 5.8% | AUD 15 | 买入 | 模型交叉验证：三模型概率：市场Poisson 58.76%，goalmodel 58.76%，Elo-DC 49.36%；共识方向Belgium，均值56.19%，置信度medium；最大模型分歧9.48%；当前选择与共识不完全一致，需小仓或观察。 |
| Matches | Brazil v Morocco | Total Goals Over/Under | Under 2.5 Goals | 1.80 | 57.4% | 3.4% | AUD 10 | 买入 | 模型交叉验证：三模型概率：市场Poisson 57.44%，goalmodel 57.44%，Elo-DC 49.36%；共识方向Brazil，均值51.13%，置信度high；最大模型分歧1.18%；当前选择与共识不完全一致，需小仓或观察。 |
| Futures | Belgium | To Qualify for Quarter Final | Belgium | 2.75 | 28.9% | 待同步 | AUD 0 | 观察 | Better suited to quarter/semi qualification than outright winner. |
| Futures | Colombia | To Qualify for Quarter Final | Colombia | 3.30 | 24.1% | 待同步 | AUD 0 | 观察 | Potentially live in qualification-stage futures if draw path supports it. |
| Futures | Japan | To Qualify for Quarter Final | Japan | 3.75 | 21.2% | 待同步 | AUD 0 | 观察 | Model already likes Japan in match market; futures price is worth monitoring, not automatic staking. |
| Futures | Morocco | To Qualify for Quarter Final | Morocco | 4.50 | 17.7% | 待同步 | AUD 0 | 观察 | Strong underdog profile; outright price is long but quarter-final path price may be more usable. |
| Futures | Croatia | To Qualify for Quarter Final | Croatia | 4.50 | 17.7% | 待同步 | AUD 0 | 观察 | Tournament profile is stronger than outright price implies, but age/squad risk must be checked. |

## 模型共识交叉验证

| 比赛 | 共识方向 | 均值概率 | 置信 | 最大分歧 | 评级来源 |
|---|---|---:|---|---:|---|
| Germany v Curacao | Germany | 71.5% | low | 28.4% | partial_hicruben_market_implied |
| Portugal v DR Congo | Portugal | 73.6% | low | 24.6% | partial_hicruben_market_implied |
| Spain v Cabo Verde | Spain | 76.7% | low | 24.1% | partial_hicruben_market_implied |
| Iraq v Norway | Norway | 75.3% | low | 23.5% | market_implied_fallback |
| Uzbekistan v Colombia | Colombia | 71.0% | low | 23.1% | partial_hicruben_market_implied |
| Austria v Jordan | Austria | 73.3% | low | 22.2% | partial_hicruben_market_implied |
| Paraguay v Australia | Australia | 36.0% | low | 22.2% | hicruben_elo_seed |
| Australia v Turkiye | Turkiye | 57.9% | low | 21.3% | partial_hicruben_market_implied |
| Argentina v Algeria | Argentina | 70.2% | low | 20.5% | hicruben_elo_seed |
| South Korea v Czechia | South Korea | 41.0% | low | 17.4% | hicruben_elo_seed |

## Automation / 门禁

- technical_preflight_ready: `False`
- automation_entry_ready: `False`
- raw_refresh_ready: `True`
- safety_ready: `True`
- blocker_count: `3`
- blocker: current-day private position snapshot missing; latest 私有持仓 capture diagnostic: access_denied via fresh-context (TAB 私有持仓 page access denied)
- blocker: user has not authorized recurring automation
- blocker: technical automation preflight failed; refusing to publish latest artifacts: current-day private position snapshot missing; latest 私有持仓 capture diagnostic: access_denied via fresh-context (TAB 私有持仓 page access denied)

## 新旧对比与本地归档

- added_count: `0`
- removed_count: `0`
- changed_count: `0`
- retained_count: `38`
- exposure_change_aud: `AUD 0`

安全边界：本 Dashboard 只读展示公开研究、报告历史、模型分歧和门禁状态；不点击赔率、不添加投注单、不自动下注。