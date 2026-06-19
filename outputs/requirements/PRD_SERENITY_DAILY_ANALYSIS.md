# PRD: Serenity Daily Analysis

生成时间：2026-06-12 21:27:38 AEST  
阶段：详细 PRD，不进入实现  
运行画像：Automation Using Model 5.4 Reasoning High  
产品定位：用 Serenity 研究方法驱动的高成长场外基金候选池、纪律审计和调仓提醒系统

## 1. Executive Summary

Serenity Daily Analysis 是一个本地优先的投资研究与纪律提醒 automation。系统每天按北京时间多个窗口采集行情、基金净值、申赎状态、费用、持仓和质量信号，生成以场外基金为优先的 Top5 高成长候选池，并把当前持仓与目标权重进行纪律审计。

系统目标是“超级高度激进但可控”：目标收益优先，强制排除债券、货币、余额宝、保守结构类资产，以及高波动但证据解释不足的对象。系统不自动下单，只输出配置权重、调仓触发条件、操作清单、Mac OS Mail / macOS notification 提醒和人工确认队列。

核心约束：

- 候选池优先级：场外基金优先，Top5 为基金优先候选池。
- 数据源优先级：全局 moomoo 优先；字段级例外为支付宝持仓、支付宝交易规则、基金公司费率和申赎公告。
- 降级策略：允许公开财经聚合源补齐视图，但关键字段缺失或冲突时不能升级为 Action-Ready。
- 最大回撤：40.00% 为硬风险闸，触发 Block / 清仓或降权建议标签。
- 回撤修复时间：从回撤低点恢复至原点的时间必须小于 1 年，否则进入 Manual Review 或 Block。
- 调仓：只做建议、提醒和操作清单，不做自动真实交易。

## 2. Confirmed Decisions

| Dimension | Decision | Notes |
|---|---|---|
| 时区展示 | C，北京时间在前，澳洲时间在后 | 调度以 Asia/Shanghai 为主，Australia/Sydney 只做展示和本地提醒 |
| 运行点 | 北京时间 06:00, 08:00, 09:30, 11:00, 11:30, 13:30, 14:00, 14:30, 15:00, 15:30, 17:00 | 当前日期 2026-06-12 对应 AEST +2 小时；实现必须用 IANA timezone，不硬编码时差 |
| 候选池 | A，场外基金优先 | 个股可作为主题、持仓穿透、产业链证据，不默认作为 Top5 主候选 |
| 执行动作 | B，生成操作清单 | 不自动下单；动作包括维持、减少、增配、暂停新增、清仓建议、Manual Review |
| 数据源优先级 | 全局 moomoo 优先 | 但支付宝持仓、交易状态、基金费率、申赎规则按字段级权威源覆盖 |
| Alipay 持仓 | A 起步，B 后续 | 起步用 CSV/截图/手工表导入；后续再做授权 Browser 辅助提取 |
| 通知 | Mac OS Mail notification | 优先 Apple Mail 发邮件或生成草稿，同时触发 macOS 本地通知 |
| 降级 | B，聚合源补齐 | 聚合源只能补视图，不能覆盖官方冲突或提升执行等级 |
| 交付 | A，先 Task Pack | 本 PRD 通过后再生成 Codex Task Pack，不直接实现 |

## 3. Schedule

主时间轴使用北京时间。

| Run | Beijing Time | Australia/Sydney example on 2026-06-12 | Primary purpose |
|---|---:|---:|---|
| R1 | 06:00 | 08:00 AEST | 隔夜美股、QDII、全球主题预扫描 |
| R2 | 08:00 | 10:00 AEST | A 股开盘前候选池预热 |
| R3 | 09:30 | 11:30 AEST | A 股开盘快照与异常波动检测 |
| R4 | 11:00 | 13:00 AEST | 上午中段比较，和 06:00/08:00/09:30 对比 |
| R5 | 11:30 | 13:30 AEST | 午盘前纪律审计 |
| R6 | 13:30 | 15:30 AEST | 截止前主决策预演，候选池和目标权重锁定 |
| R7 | 14:00 | 16:00 AEST | 15:00 交易截止前主调仓建议窗口 |
| R8 | 14:30 | 16:30 AEST | 截止前最终申赎/费率/证据复核 |
| R9 | 15:00 | 17:00 AEST | 截止点检查，仅做最后提醒与状态冻结 |
| R10 | 15:30 | 17:30 AEST | 截止后复盘，下一交易日预案 |
| R11 | 17:00 | 19:00 AEST | 收盘后数据归档、Top5 差异、邮件总结 |

调度要求：

- 使用交易日历判断 A 股、港股、美股、QDII 相关基金的有效交易日。
- 15:00 运行不能假设仍可在当天成交；实际实现中 R6 13:30、R7 14:00、R8 14:30 是主操作窗口，R9 15:00 只做截止告警和状态标记。
- Australia/Sydney 夏令时会改变时差，必须通过 timezone database 计算。

## 4. Users And Jobs To Be Done

目标用户：个人高风险偏好投资者，需要用自动化减少观察、筛选、纪律执行和交易窗口错过带来的收益损耗。

核心任务：

1. 每个工作日多次刷新高成长场外基金候选池。
2. 将 A 股和美股高成长方向映射到可在支付宝等场外路径操作的基金。
3. 对 Top5 候选给出权重建议、回撤、收益、费率、申赎状态、管理费、风险和证据链。
4. 对当前持仓进行偏离检查和纪律动作标记。
5. 触发调仓、风险或数据异常时，通过 Mac OS Mail / macOS notification 提醒。
6. 保存所有 run 的原始数据、特征、评分、决策和报告，支持日/周/月同比和环比分析。

## 5. Scope

### In Scope

- 场外基金优先 Top5 候选池。
- 高成长主题研究：A 股、港股、美股、QDII、跨市场科技成长、AI、半导体、机器人、创新药、先进制造、算力基础设施等。
- Serenity 产业链逻辑：先看产业链层级，再筛基金暴露度。
- 数据采集：净值、历史 K 线、申赎状态、费用、分红、持仓快照、主题/行业暴露。
- 数据质量：缺失率、时间滞后、异常值、重复行情、来源追溯、冲突检测。
- 评分与过滤：超激进但可控、回撤和恢复时间硬闸、证据覆盖度。
- 纪律审计：目标权重 vs 当前持仓权重，触发维持/减少/增配/暂停新增。
- 归档：SQLite 本地数据库，后续可导出 CSV/JSON/Markdown/PDF。
- 通知：Mac OS Mail 邮件或草稿、本地 macOS notification。
- 以跑赢沪指和 S&P 500 为策略目标、过滤条件、纪律门槛和复盘评价指标。

### Out Of Scope

- 自动真实下单。
- 保证未来收益或承诺未来一定跑赢沪指/标普 500。系统必须以跑赢二者为策略目标和纪律门槛，但不能把未来结果包装成确定性承诺。
- 绕过支付宝、基金公司或券商的交易规则。
- 使用未授权账号抓取、绕过验证码、绕过平台风控。
- 基于传闻或无法核验截图输出 Action-Ready 交易建议。
- 对用户完整财务状况做适当性判断。

## 6. Data Source Policy

### 6.1 Global Priority

默认源优先级：

1. moomoo / OpenD / moomoo API
2. 支付宝持仓和交易页面导入
3. 基金公司官网、基金合同、招募说明书、公告、官方净值
4. 官方交易平台快照
5. 公开财经聚合源

### 6.2 Field-Level Exceptions

| Field | Preferred source | Reason |
|---|---|---|
| 股票/指数 K 线 | moomoo / OpenD | 行情时间序列优先 |
| 个股、ETF、指数快照 | moomoo / OpenD | 实时性优先 |
| 当前持仓 | Alipay import | 用户实际持仓以交易平台为准 |
| 基金申购/赎回状态 | 基金公司公告 + Alipay 页面 | 可执行性以场外路径为主 |
| 申购费、赎回费、管理费、托管费 | 基金公司文件 + Alipay 页面 | 费用需要官方或销售平台确认 |
| 基金净值 | 基金公司官网优先，聚合源补齐 | 净值以官方披露为准 |
| 基金持仓 | 基金定期报告 | 穿透暴露必须用官方报告 |
| QDII 确认/到账规则 | 基金详情页和基金公司公告 | T+1/T+2/T+3 可能不同 |

### 6.3 Degradation B Rule

用户选择降级 B，系统允许在 moomoo、支付宝或官方源暂时缺失时，使用公开财经聚合源补齐研究视图。但执行等级必须受限：

- 聚合源补齐后最多输出 Watch，除非官方级源达到 2 个且无冲突。
- 若关键字段缺失：净值、申赎状态、费率、当前持仓、基金是否开放，则不得输出 Action-Ready。
- 若源冲突，优先展示冲突解释和 source_chain，不得静默选择有利数据。
- 缺失数据不允许硬下结论；可输出候选线索和补数清单。

## 7. Candidate Universe

### 7.1 Primary Universe

场外基金优先，包括：

- 主动权益基金
- 指数增强基金
- 行业主题基金
- QDII / QDII-LOF 场外份额
- 跨市场高成长主题基金
- 高成长混合型基金

### 7.2 Exclusion Universe

强制排除：

- 债券基金
- 货币基金
- 余额宝及类现金管理
- 保守结构类产品
- 目标收益不足且无法解释高波动的基金
- 申购暂停、赎回异常、费率或状态缺失严重的基金
- 最大回撤 >= 40.00% 且无明确修复路径的基金
- 从最大回撤低点恢复到原点耗时 >= 1 年的基金
- 公开证据链不足且主要依赖营销文案或短期涨幅的基金

### 7.3 Stock Role

个股不作为默认 Top5 主候选，但可用于：

- 识别高成长产业链层级；
- 解释基金重仓股暴露；
- 判断基金收益来源是否可持续；
- 对基金持仓做主题穿透；
- 生成后续可选的股票观察池。

## 8. Serenity Research Logic

候选池排序先看产业链层级，再看基金产品。

核心链路：

1. 市场故事：AI、半导体、算力、机器人、创新药等方向是否出现真实需求变化。
2. 系统变化：哪个技术或经济变量改变了供需关系。
3. 稀缺层级：带宽、功耗、封装、材料、设备、良率、产能、审批、客户认证等哪里最难扩张。
4. 公司和基金映射：哪些基金实际暴露在这些稀缺层级。
5. 证据强度：公告、定期报告、基金持仓、公司财报、交易所文件、订单和项目进度。
6. 风险反证：什么事实会说明这个方向错了。

输出必须区分：

- FACT：可核验事实；
- INFERENCE：基于事实的推断；
- OPINION：研究判断；
- OBSERVATION：行情或数据观察。

## 9. Scoring Model

总分 100。目标收益优先，但必须通过风险和数据质量硬闸。

| Check | Weight | Failure State | Downgrade | Output Action |
|---|---:|---|---|---|
| 数据完整性：净值、持仓、费率、赎回状态 | 25 | 关键缺失 1 项 | -20 到 -40 | Watch |
| 时间完整性：缺失 > 2 天 | 15 | 连续缺失 > 2 天 | -30，manual_review_required | Manual Review |
| 来源可信度：源链顺序/冲突 | 15 | 官方级源 < 2 或冲突 | -35，显示冲突解释 | Manual Review |
| 收益与基准比较：1m/3m+10 交易日 | 15 | 沪指/标普 500 相关基准均落后 | 负向加权，不建议加仓 | Avoid New / Reduce |
| 风险指标：MDD、波动、恢复时间 | 20 | MDD >= 40.00% 或恢复时间 >= 1 年 | 硬降级 | Block + Manual Review |
| 操作可执行性：申赎、限额、费率 | 10 | 限额、T 日、费率异常 | 延后窗口 | Postpone |

等级映射：

- Score >= 85：Action-Ready
- 70 <= Score < 85：Watch
- 55 <= Score < 70：Manual Review
- Score < 55：Block / Skip

硬闸优先于总分：

- MDD >= 40.00%：直接 Block 或清仓/降权建议标签。
- 回撤修复时间 >= 1 年：Manual Review；若同时存在数据缺失或基准落后，Block。
- 申赎暂停或赎回状态缺失：不得 Action-Ready。
- 官方级源少于 2 个：不得 Action-Ready。

## 10. Benchmark Rules

比较周期：

- 最近 1 个月收益
- 最近 3 个月收益
- 最近 10 个交易日收益

基准：

- A 股暴露：上证指数为硬基准，必要时补充沪深 300、创业板指或中证相关行业指数。
- 美股暴露：S&P 500 为硬基准，必要时补充 Nasdaq 100 或行业指数。
- 混合暴露：按基金持仓或主题暴露拆分基准权重；无法拆分时同时展示沪指和 S&P 500。

动作规则：

- 若 1m、3m、10D 全部弱于相关基准，不允许新增或增配。
- 若 1m 弱但 3m 强，进入 Watch，等待下一运行点确认。
- 若 10D 强但证据链不足，标记 short_term_momentum_only，不允许 Action-Ready。
- 若收益领先但波动解释不足，进入 Manual Review。

## 11. Risk Rules

| Rule | Threshold | Action |
|---|---:|---|
| 最大回撤 | >= 40.00% | Block / 清仓或降权建议 |
| 回撤修复时间 | >= 1 年 | Manual Review 或 Block |
| 7 日回撤恶化 | > 5.00% | Risk Alert |
| 单标过度放大 | 连续 > 2 次 | Risk Alert + Reduce |
| 目标/当前权重偏离 | > 1.00% | Rebalance Candidate |
| Top5 变动率 | > 20.00% | Rebalance Candidate |
| Top5 新增 | >= 1 只 | Rebalance Candidate |
| Top5 替换 | >= 2 只 | Rebalance Candidate |
| 关键字段变动 | > 1 sigma | Regime Check |
| 连续缺失净值/持仓 | > 2 天 | Manual Review |
| 费率/赎回状态缺失 | 任一缺失 | No-New-Order |
| 官方级源数量 | < 2 | Manual Review |

## 12. Discipline Actions

动作标签：

- Maintain：维持，不新增交易。
- Increase：增配建议，需 Action-Ready 且处于有效交易窗口。
- Reduce：减配建议，用于偏离、风险恶化或证据走弱。
- Pause New：暂停新增，用于数据缺失、冲突、交易状态不明。
- Postpone：延后到下一交易窗口。
- Clear / Exit Candidate：清仓或移出候选池建议，适用于硬风险闸。
- Manual Review：人工确认后才可操作。
- Block / Skip：不执行调仓建议。

调仓输出不是直接买卖指令，必须附带：

- 触发原因；
- 当前权重和目标权重；
- 目标金额或比例；
- 交易窗口；
- 申赎/费率影响；
- 失效条件；
- 数据源与时间戳；
- 人工确认状态。

## 13. Trading Window Rules

场外基金规则必须逐基金读取，不得统一假设。

默认假设：

- 中国场外基金通常以交易日 15:00 为重要截止点；
- 15:00 前有效申请通常按当日净值处理；
- 15:00 后通常进入下一交易日；
- T+1、T+2、T+3 等确认和到账规则因基金类型、QDII、销售平台和基金公司规则不同而变化；
- 以支付宝路径执行时，以支付宝基金详情页、基金公司公告、基金合同和招募说明书为准。

实现要求：

- 每只基金必须有 `cutoff_time`、`confirm_lag`、`redeem_lag`、`fee_schedule`、`subscription_status`、`redemption_status`。
- R6 13:30 是主决策预演窗口。
- R7 14:00 是主调仓建议窗口。
- R8 14:30 是截止前最终复核窗口。
- R9 15:00 是截止点提醒和状态冻结窗口，不保证仍可提交当日有效订单。
- R10 15:30 只输出下一交易日预案。
- R11 17:00 输出收盘后归档和日内差异总结。

## 14. Data Model Draft

### 14.1 Core Tables

`run_log`

- run_id
- run_time_bj
- run_time_au
- schedule_slot
- model_profile
- status
- data_quality_status
- notification_status
- created_at

`asset_master`

- asset_id
- asset_code
- asset_name
- asset_type
- market
- fund_company
- risk_level
- is_excluded
- exclusion_reason

`source_log`

- source_id
- run_id
- asset_id
- source_name
- source_type
- source_priority
- url_or_path
- observed_at
- fetched_at
- evidence_level
- field_list
- conflict_group

`fund_nav_snapshot`

- run_id
- asset_id
- nav_date
- nav
- accumulated_nav
- daily_return
- nav_source_id
- freshness_status

`market_kline_snapshot`

- run_id
- asset_id
- bar_interval
- start_time
- end_time
- open
- high
- low
- close
- volume
- turnover
- source_id

`fund_rule_snapshot`

- run_id
- asset_id
- subscription_status
- redemption_status
- cutoff_time
- confirm_lag
- redeem_lag
- subscription_fee
- redemption_fee
- management_fee
- custody_fee
- sales_service_fee
- min_purchase_amount
- source_id

`position_snapshot`

- run_id
- asset_id
- platform
- current_amount
- current_weight
- cost_basis
- unrealized_pnl
- imported_by
- source_id

`score_snapshot`

- run_id
- asset_id
- total_score
- data_score
- timeliness_score
- source_score
- return_score
- risk_score
- executable_score
- evidence_coverage
- grade
- hard_block_reason

`recommendation_snapshot`

- run_id
- asset_id
- rank
- target_weight
- current_weight
- deviation
- action_label
- trigger_reason
- next_check_by
- manual_review_required

`comparison_snapshot`

- run_id
- asset_id
- compare_type
- base_run_id
- delta_rank
- delta_score
- delta_weight
- top5_changed
- key_field_sigma

`notification_log`

- notification_id
- run_id
- channel
- severity
- title
- body_path
- send_status
- sent_at
- error_message

### 14.2 Required Audit Queues

- `manual_review_queue`
- `missing_data_log`
- `decision_record`
- `audit_log`
- `conflict_log`
- `rebalance_event_log`

## 15. Report Output

每次 run 输出：

1. Top5 候选池和权重建议。
2. 当前持仓 vs 目标权重偏离。
3. 收益对比：1m、3m、10 交易日。
4. 回撤、最大回撤、7 日回撤恶化、恢复时间。
5. 申购费、赎回费、管理费、托管费、销售服务费。
6. 申赎状态、确认周期、赎回到账周期。
7. 数据质量摘要。
8. 证据链和冲突说明。
9. 纪律动作：维持、减少、增配、暂停新增、Postpone、Manual Review、Block。
10. 下一次检查时间和本建议失效条件。

报告等级：

- Urgent：风险失控、硬回撤闸、清仓/降权建议。
- Alert：偏离 > 1.00% 且证据充分，或 Top5 触发重平衡。
- Warn：数据冲突、申赎/费率异常、证据不足。
- Info：常规纪律检视，无新增交易动作。

## 16. Notification Requirements

主通道：

- Mac OS Mail notification。
- 期望方式：Apple Mail 发送邮件或生成草稿，同时触发本地 macOS notification。
- 收件人：linzezhang35@gmail.com。

通知模板：

### Urgent

标题：

`[Serenity AUTO][ALERT][Urgent] 组合偏离+信号突变 | {run_id} | {date}`

正文字段：

- 运行时间：{run_time_bj} / {run_time_au}
- 触发类型：{trigger_reason}
- Top5 变更：{old_top5} -> {new_top5}
- 偏离最大标的：{asset_code} | 当前:{current_w}% 目标:{target_w}%
- 风险快照：MDD={mdd} | 近 N 日回撤={drawdown_n} | 是否超阈值={rule_hit}
- 基准对比：沪指 1m/3m/10D {cn_index}，S&P 500 1m/3m/10D {us_index}
- 关键证据更新：{source_chain + conflict_note}
- 调仓建议：{action}
- 失效兜底：{manual_review_flags}
- 下一步动作截止：{next_check_by}
- 来源与时间戳：{sources_json}

### Info

标题：

`[Serenity AUTO][INFO] 纪律检视完成 - 无新增交易动作 | {run_id}`

正文字段：

- 本次 Top5 名单与上次一致率
- 偏离最大值与建议
- 触发条件不满足或得分不足
- 下次复核时间

### Warn

标题：

`[Serenity AUTO][WARN] 数据质量不足，已切 Manual Review | {run_id}`

正文字段：

- 降级原因
- 缺失字段清单
- 涉及标的和 source_chain
- 当前禁止动作：No-New-Order
- 需补充数据项与预计恢复时间

## 17. Acceptance Criteria

### Functional

- 能按北京时间 9 个运行点生成 run_id 和快照。
- 每次 run 至少保存 run_log、source_log、score_snapshot、recommendation_snapshot。
- Top5 候选池只包含未被强制排除的场外基金优先对象。
- 能读取或导入支付宝持仓快照，并计算当前权重。
- 能输出目标权重、偏离值、动作标签和触发原因。
- 能比较当日不同 run 的 Top5、分数、权重和关键字段变化。
- 能比较前一日、前一周、前一月。
- 能按 1m、3m、10 交易日和基准对比。
- 能触发 Mac OS Mail / notification。

### Data Quality

- 每个关键字段都必须有 source_chain。
- 官方级源少于 2 个时不得 Action-Ready。
- 净值/持仓连续缺失 > 2 天必须进入 Manual Review。
- 费率或赎回状态缺失必须 No-New-Order。
- 聚合源补齐必须标记为 fallback_aggregated。
- 源冲突必须写入 conflict_log。

### Risk

- MDD >= 40.00% 必须硬降级。
- 回撤修复时间 >= 1 年必须 Manual Review 或 Block。
- 高波动但解释不足不得进入 Top5 Action-Ready。
- 单标过度放大连续 > 2 次必须告警。

### Safety

- 不自动下单。
- 不存储明文密码、token、cookie。
- 邮件发送失败必须记录并降级到本地通知或草稿。
- 所有建议必须带人工确认状态。

## 18. Open Questions For Next Gate

这些问题不阻塞 PRD，但会影响 Task Pack 和实现：

1. 初始基金候选全集从哪里来：支付宝自选/持仓、moomoo 基金列表、还是指定主题基金名单？
2. 支付宝持仓导入格式：CSV、截图 OCR、手工表格，还是先给模板？
3. Mac OS Mail 是否已经配置可发送 `linzezhang35@gmail.com`？
4. 是否允许 automation 读取 Apple Mail / local notification 权限？
5. 是否需要把报告同时生成 PDF，还是 MVP 先 Markdown + SQLite + 邮件正文？
6. 是否需要单独输出“股票观察池”，用于解释基金持仓和主题，不参与 Top5？

## 19. Recommended Next Step

下一步生成 Codex Task Pack，仍不直接实现。建议目录：

- `outputs/task_pack/00_PROJECT_BRIEF.md`
- `outputs/task_pack/01_REQUIREMENTS.md`
- `outputs/task_pack/02_ARCHITECTURE.md`
- `outputs/task_pack/03_DATA_SCHEMA.md`
- `outputs/task_pack/04_API_AND_INTERFACES.md`
- `outputs/task_pack/05_SCHEDULER_AND_RUN_CONTRACT.md`
- `outputs/task_pack/06_SCORING_AND_RISK_RULES.md`
- `outputs/task_pack/07_NOTIFICATION_RULES.md`
- `outputs/task_pack/08_ACCEPTANCE_CRITERIA.md`
- `outputs/task_pack/09_TESTING_CHECKLIST.md`
- `outputs/task_pack/10_CODEX_PROMPT.md`
