# TAB FIFA 盘口研究智能层

本报告把下注推荐、报告历史、主动测试、开源模型对齐和自动化门禁合并成一个业务可读视图。它只提供研究建议，不自动下注。

## Executive Summary

- 当前可信报告日期：`04062026`
- 当前可信 run：`20260604T135753Z-212e8e9a`
- 当前操作判断：保留上一份可信报告；当前 attempted run 不发布为下注日报
- 推荐买入候选：`7` 条，展示金额合计 `AUD 100.00`
- 主动测试缺口：分析缺口日 `5`，日报缺口日 `8`，待补队列 `8`

## Automation Dashboard

- 读取路径：先看 raw 和发布门禁，再看主动测试缺口、补跑队列、私有持仓，最后看开源模型和新旧报告对比。
- 就绪项：`3`，阻塞项：`4`，平均得分：`32.64%`

| 模块 | 状态 | 得分 | 证据 | 下一步 |
|---|---|---:|---|---|
| 公开盘口 raw | 阻塞 | 0.00% | raw_refresh.ready=False；blockers=refresh_command_failed, route_mismatch, stale_raw。 | 先恢复 5 个 TAB FIFA 板块 raw freshness，再允许补跑或发布。 |
| 4-5小时分析节奏 | 部分 | 11.11% | 1/9 天完整；待补队列 8。 | 点击主动测试并按补跑优先队列修复缺口。 |
| 每日PDF报告 | 阻塞 | 0.00% | 日报缺口日 8。 | raw ready 后安全补跑缺失日报；补跑不发布 latest。 |
| 本地数据库 | 就绪 | 100.00% | report_runs 20；automation_runs 9。 | 继续把每次报告、审计、补跑和对比写入 SQLite。 |
| 新旧报告对比 | 就绪 | 100.00% | 新增 0 / 移除 0 / 变化 0。 | 每份新报告必须展示与上一可信报告的变化。 |
| 开源模型参考 | 就绪 | 50.00% | 已转化 3/6 个 GitHub 参考；覆盖 38 类能力。 | 下一步接入真实赛果 track record、校准曲线和淘汰赛 Monte Carlo。 |
| 发布门禁 | 阻塞 | 0.00% | formal_report_publish_ready=False。 | fresh raw + private snapshot + preflight + public safety 全部通过才发布。 |
| 私有持仓快照 | 阻塞 | 0.00% | status=raw_ready_import_needed；report_date=04062026。 | 完成只读持仓读取 bootstrap，更新已下注金额和累计收益率。 |

## 新旧报告对比与本地数据库

- 对比 run：`20260605T232012Z-bad22171`，报告日期：`06062026`，状态：`blocked_by_gate`
- 新增 `0`，移除 `0`，变化 `0`，保留 `38`。
- 暴露变化：`AUD 0.00`；图表 `10`；推荐 `38`。

## 推荐下注板块

| 板块 | 盘口 | 下注 | 赔率 | 概率 | EV | 金额 | 一致性 | 置信度 | 原因 |
|---|---|---|---:|---:|---:|---:|---|---|---|
| 2026 World Cup Matches | Brazil v Morocco / Result | Morocco | 5.50 | 22.25% | 22.38% | AUD 15 | 待校准 | 待校准 | 模型概率 22.25% 高于赔率盈亏平衡 18.18%，边际 +4.07pp，EV 22.38%。 建议金额 AUD 15，属于分散小仓位。 赛前仍需复核伤停、阵容和新闻。 |
| 2026 World Cup Matches | France v Senegal / Result | Senegal | 7.00 | 17.09% | 19.63% | AUD 15 | 待校准 | 待校准 | 模型概率 17.09% 高于赔率盈亏平衡 14.29%，边际 +2.80pp，EV 19.63%。 建议金额 AUD 15，属于分散小仓位。 赛前仍需复核伤停、阵容和新闻。 |
| 2026 World Cup Matches | England v Croatia / Result | Croatia | 4.75 | 24.64% | 17.03% | AUD 15 | 待校准 | 待校准 | 模型概率 24.64% 高于赔率盈亏平衡 21.05%，边际 +3.59pp，EV 17.03%。 建议金额 AUD 15，属于分散小仓位。 赛前仍需复核伤停、阵容和新闻。 |
| 2026 World Cup Matches | Netherlands v Japan / Result | Japan | 3.50 | 31.05% | 8.69% | AUD 15 | 待校准 | 待校准 | 模型概率 31.05% 高于赔率盈亏平衡 28.57%，边际 +2.48pp，EV 8.69%。 建议金额 AUD 15，属于分散小仓位。 赛前仍需复核伤停、阵容和新闻。 |
| 2026 World Cup Matches | Belgium v Egypt / Total Goals Over/Under | Under 2.5 Goals | 1.87 | 56.97% | 6.54% | AUD 15 | 待校准 | 待校准 | 模型概率 56.97% 高于赔率盈亏平衡 53.48%，边际 +3.49pp，EV 6.54%。 建议金额 AUD 15，属于分散小仓位。 赛前仍需复核伤停、阵容和新闻。 |
| 2026 World Cup Matches | South Korea v Czechia / Both Teams to Score | Only One or Neither to score | 1.87 | 56.02% | 4.76% | AUD 15 | 待校准 | 待校准 | 模型概率 56.02% 高于赔率盈亏平衡 53.48%，边际 +2.55pp，EV 4.76%。 建议金额 AUD 15，属于分散小仓位。 赛前仍需复核伤停、阵容和新闻。 |
| 2026 World Cup Matches | Brazil v Morocco / Total Goals Over/Under | Under 2.5 Goals | 1.80 | 57.44% | 3.40% | AUD 10 | 待校准 | 待校准 | 模型概率 57.44% 高于赔率盈亏平衡 55.56%，边际 +1.89pp，EV 3.40%。 建议金额 AUD 10，属于分散小仓位。 赛前仍需复核伤停、阵容和新闻。 |
| 2026 World Cup Futures | Belgium / To Qualify for Quarter Final | Belgium | 2.75 | 28.92% |  | AUD 0 | 待校准 | 待校准 | 证据不足以形成强下注结论，当前应以观察为主。 |
| 2026 World Cup Group Betting | Group K / Group Winner | Colombia | 3.00 | 29.63% |  | AUD 0 | 待校准 | 待校准 | 证据不足以形成强下注结论，当前应以观察为主。 |
| 2026 World Cup Australia Markets | AUS Group Match Wins / AUS Group Match Wins | AUS Win 0 Grp Matches | 1.75 | 49.44% |  | AUD 0 | 待校准 | 待校准 | 证据不足以形成强下注结论，当前应以观察为主。 |

## 主动测试时间线热力图

| 日期 | 00-05 | 05-10 | 10-15 | 15-20 | 20-24 | 有效分析 | 日报 | 状态 |
|---|---|---|---|---|---|---:|---|---|
| 06/06/2026 | 缺 | 有 | 有 | 缺 | 缺 | 7 | 缺失 | 缺口 |
| 07/06/2026 | 缺 | 缺 | 缺 | 缺 | 缺 | 0 | 缺失 | 缺口 |
| 08/06/2026 | 缺 | 缺 | 缺 | 缺 | 缺 | 0 | 缺失 | 缺口 |
| 09/06/2026 | 缺 | 缺 | 缺 | 缺 | 缺 | 0 | 缺失 | 缺口 |
| 10/06/2026 | 缺 | 缺 | 缺 | 缺 | 缺 | 0 | 缺失 | 缺口 |
| 11/06/2026 | 缺 | 缺 | 缺 | 缺 | 缺 | 0 | 缺失 | 缺口 |
| 12/06/2026 | 缺 | 缺 | 缺 | 有 | 有 | 4 | 缺失 | 缺口 |
| 13/06/2026 | 缺 | 有 | 有 | 缺 | 缺 | 8 | 缺失 | 缺口 |

## 主动测试历史趋势

- 历史审计次数：`12`
- 最新完整率：`11.11%`
- 最新缺口数：`13`
- Raw 可用审计次数：`0`
- 趋势方向：`deteriorating`

| 审计时间 | 完整率 | 缺口数 | 补跑队列 | Raw | 补跑状态 |
|---|---:|---:|---:|---|---|
| 06-12 19:05 | 12.50% | 13 | 7 | blocked | blocked_by_raw_refresh |
| 06-12 19:07 | 12.50% | 13 | 7 | blocked | blocked_by_raw_refresh |
| 06-12 19:09 | 12.50% | 13 | 7 | blocked | blocked_by_raw_refresh |
| 06-12 19:11 | 12.50% | 13 | 7 | blocked | blocked_by_raw_refresh |
| 06-12 19:30 | 12.50% | 13 | 7 | blocked | blocked_by_raw_refresh |
| 06-12 22:15 | 12.50% | 13 | 7 | blocked | blocked_by_raw_refresh |
| 06-12 22:22 | 12.50% | 13 | 7 | blocked | blocked_by_raw_refresh |
| 06-13 06:38 | 11.11% | 14 | 8 | blocked | blocked_by_raw_refresh |
| 06-13 10:16 | 11.11% | 14 | 8 | blocked | blocked_by_raw_refresh |
| 06-13 13:20 | 11.11% | 13 | 8 | blocked | blocked_by_raw_refresh |
| 06-13 13:20 | 11.11% | 13 | 8 | blocked | blocked_by_raw_refresh |
| 06-13 14:43 | 11.11% | 13 | 8 | blocked | blocked_by_raw_refresh |

## 功能成熟度对齐

| 功能 | 当前状态 | 当前实现 | 下一步 |
|---|---|---|---|
| 4-5 小时一次分析节奏 | 部分落地 | 主动测试按 5 个时间窗回测有效分析次数，并生成缺口队列。 | 缺口日需要安全补跑；正式 automation 尚需用户授权。 |
| 每日一份中文报告 | 部分落地 | 正式 PDF、report index、Downloads app 已接入；失败门禁时保留上次可信报告。 | 当前日期序列仍有日报缺口，需要补跑后复测。 |
| 本地数据库与新旧对比 | 已落地 | 本系统使用 SQLite 记录 run、板块、推荐、图表、diff、缺失数据和审计。 | 继续补足真实赛果/结算字段后可做完整命中率回测。 |
| 业务首页 Dashboard | 已落地 | Downloads app 首屏展示推荐下注板块、金额、EV、概率/赔率编辑和主动测试按钮。 | 继续减少工程状态词，把缺口、赔率变化和行动建议前置。 |
| 开源模型参考 | 已落地 | 已桥接 Elo、Dixon-Coles、goalmodel 思路，输出模型分歧和能力覆盖。 | 下一步把晋级路径 Monte Carlo 与赛果回测连到同一评价表。 |
| 主动回测/缺失补齐 | 部分落地 | 主动测试可识别缺失分析和日报；补跑使用 no-latest-publish 重建模式。 | 补跑不能伪装历史原时点盘口；需要标记为当前数据重建。 |
| 私有持仓读取 | 阻塞 | 已有只读专用浏览器 profile 和导入链，但当前未完成私有快照 bootstrap。 | 需要一次性完成本地浏览器授权；系统不保存密码、不自动下注。 |
| 自动化准入门禁 | 已落地 | 已有 hermetic verifier、public safety、PDF QA、raw freshness、report publish gates。 | 正式 recurring automation 仍处于用户未授权状态。 |

## 开源模型参考采用

| 参考 | 方法 | 许可 | 采用状态 | 用法 |
|---|---|---|---|---|
| Hicruben 2026 WC | Elo + Dixon-Coles + Monte Carlo | MIT | 已转化为本地 proxy | 用于48队强弱先验、低比分修正和比赛结果概率交叉验证；其walk-forward/reliability/track-record思路进入本地模型审计，Monte Carlo路径作为晋级/淘汰赛模拟接口。 |
| goalmodel | Expected goals probability model | GPL-3.0 | 已转化为本地 proxy | 用于市场隐含概率反推xG，并把同一xG分布转换为1X2、大小球、BTTS和评分规则敏感性检查。 |
| RyanSCodes DC | Dixon-Coles weighted history | No release license declared | 设计参考 | 作为后续回测/时间衰减权重设计参考；当前不复制其Python 2.7实现。 |
| penaltyblog | Poisson + Dixon-Coles + bookmaker odds utilities | MIT | 已转化为本地 proxy | 用于强化本地 no-vig、EV、Edge、大小球/让球和模型不确定性口径；本地仍使用自有实现，不直接依赖外部包执行下注。 |
| socceraction | SPADL + xT + VAEP action value | MIT | 设计参考 | 用于未来把球员事件、战术和基本面转成 xT/VAEP 解释层；当前无事件流原始数据时只作设计参考和缺口提示。 |
| openfootball worldcup.json | World Cup public schedule JSON | Public Domain / CC0-style dedication | 设计参考 | 用于赛程、日期、阶段和本地数据库 seed 的公开交叉验证；不提供赔率，不替代 TAB 实时盘口 raw。 |

## 下一步

| 优先级 | 事项 | 操作 | 预期效果 |
|---|---|---|---|
| P0 | 补齐主动测试发现的缺口 | 运行安全补跑后重新点击主动测试，目标是每日至少 4 次分析且 1 份报告。 | 提升日报连续性；补跑报告仍标记为重建版本。 |
| P0 | 刷新实时公开盘口并重跑日报 | 先让 5 个 TAB FIFA 板块 raw snapshot 回到 freshness 门槛内，再运行日报。 | 解决当前 attempted run 不能发布的问题之一。 |
| P0 | 完成私有持仓读取 bootstrap | 使用本地只读浏览器 profile 完成一次授权，然后导入当日持仓快照。 | 同步已下注金额、未结算暴露和累计收益率所必需。 |
| P1 | 等待用户授权后安装 recurring automation | 保持当前手动触发；成熟后再接入每 4-5 小时一次的调度。 | 避免在门禁未清前产生误导性自动日报。 |
| P2 | 接入赛果与结算结果 | 为每条历史建议增加结果、命中率、Brier/log-loss 和资金曲线字段。 | 把现在的节奏回测升级为真实下注研究回测。 |