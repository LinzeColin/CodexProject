# TAB FIFA 推荐操作 Dashboard

本报告把首页推荐下注板块归档成正式研究报告。raw 或发布门禁失败时，所有候选只保留为研究参考，不作为当前可执行下注。

## Executive Summary

- status: `research_only_blocked`
- current_action: `暂不新增下注`
- current_executable_new_stake_aud: `AUD 0`
- research_candidate_stake_aud: `AUD 0`
- candidate_count: `0`
- current_research_candidate_count: `0`
- all_candidate_count_before_scope: `12`
- excluded_unavailable_candidate_count: `12`
- excluded_unavailable_stake_aud: `AUD 100`
- average_ev: `0.00%`
- average_edge: `+0.00pp`
- edge_threshold_pass_count: `0/0`
- average_edge_threshold_gap: `+0.00pp`
- average_arbitrage_rate: `0.00%`
- max_risk_of_ruin: `0.00%`
- high_risk_of_ruin_count: `0`
- expected_profit_at_research_stake_aud: `AUD 0`
- average_expected_profit_per_100_aud: `AUD 0`
- ror_review_count: `0`
- value_signal_pass_count: `0/0`
- positive_arbitrage_count: `0`
- price_buffer_positive_count: `0`
- low_or_medium_ror_count: `0`
- analysis_basis_complete_count: `0/0`
- analysis_data_gap_row_count: `0`
- pre_bet_checklist_item_count: `0`
- model_calibrated_count: `0/0`
- model_high_divergence_count: `0`
- model_reverse_consensus_count: `0`
- model_review_required_count: `0`
- average_price_drift_tolerance_pct: `0.00%`
- average_stake_to_cap_ratio: `0.00%`
- average_risk_adjusted_value_score: `0.00%`
- average_market_funding_tendency_score: `0.0` / supportive `0` / weak `0`
- market_funding_proxy: total `AUD 0` / net `AUD 0` / turnover `AUD 0`
- tournament_rule_ready: `1/8`
- prediction_contract_ready: `7/9`
- backtest_control_ready: `2/7`
- portfolio_risk_of_ruin: `0.00%` / `低`
- portfolio_expected_profit_aud: `AUD 0`
- portfolio_worst_case_new_loss_aud: `AUD 0`
- portfolio_combined_mid_usage_pct: `50.00%`
- bankroll_reference_aud: `AUD 4,000`
- gate_message: 公开盘口 raw 未就绪，暂停执行新增下注；先刷新公开盘口，再重跑日报门禁。阻塞类型：refresh_command_failed、route_mismatch、stale_raw。

## 判断依据

- Edge 使用 `模型概率 - 赔率盈亏平衡概率`，衡量概率优势百分点。
- Edge 信息展示对应盘口门槛和门槛差：主流盘口按 2.50% 下限，小市场按 5.00% 中位阈值；门槛差为正才算通过纪律过滤。
- 套利率使用 `max(0, 模型概率 × 十进制赔率 - 1)`，这里是价值套利率，不代表跨平台无风险套利。
- Risk of ruin 使用中位资金池、单注比例、半Kelly偏离和盘口风险标记做保守估计，并输出低/中/偏高/高等级与触发原因；真实账户资金未同步时不读取私有余额。
- 价值信号综合 EV、Edge门槛、价格缓冲和 RoR；价格容忍度为赔率还能下滑的百分比，为负时应放弃。
- 仓位上限占用把单注比例和 2% 上限直接对比；Kelly安全垫为 1 - 当前仓位/半Kelly，低于 0 表示超过半Kelly。
- 市场资金倾向分综合 EV、Edge、套利率、价格容忍度、流动性、盘口深度、RoR 和日均盘口变动浮动率；资金字段是代理指标，不是 TAB 官方成交数据。
- 组合风险把所有当前可研究买入候选放在同一预算压力测试里，检查总研究金额、预算占用、最坏全输亏损、组合期望收益和组合 Risk of ruin。
- 模型校准把开源模型对比报告映射到每条推荐：展示共识方向、分歧、模型均值概率、本地概率偏离和复核动作。
- 当前推荐池只统计 TAB live nav 已确认可研究的板块；缺失或 route mismatch 板块进入排除审计队列，不参与 Top pick、Edge、套利率、Risk of ruin 汇总。
- 开源模型库：`ready_with_license_controls`；参考源 `6`；已吸收 `3`；设计参考 `3`。
- Excel模板未在本机 Downloads 找到，当前使用内置结构画像：7个预期sheet，模块为赛前检查、赔率去水、EV/Edge、Kelly仓位、Poisson/xG、下注日志。
- ChatGPT Excel 模板已吸收为：赛前10分钟清单、赔率去水、EV、Edge、Kelly、Poisson/xG、下注日志、CLV/ROI 复盘口径。
- 价格执行层：从 Excel 的“价格走差就放弃”规则转化为最低可接受赔率、赔率缓冲和价格容忍度，避免报告价过期后继续下注。
- 风控执行层：从 Excel 的单注上限和半Kelly规则转化为仓位上限占用、Kelly安全垫和 Risk of ruin 复核队列。
- 下注纪律层：基础单注 0.5%-1.0% bankroll，单注上限 2.0% bankroll；主流市场 Edge 至少 2%-3%，小市场至少 4%-6%。
- 推荐过滤层：模型概率必须高于盈亏平衡概率，Edge 需要达到对应盘口门槛；未达门槛或 RoR 偏高时只进入观察/复核队列。
- 组合风险层：按用户预算区间 AUD 3,000-5,000 和用户声明已投入参考 AUD 2,000 做压力测试，输出候选组合占用、预计收益、全输亏损和组合RoR。
- 市场资金层：新增市场资金倾向分、总资金代理、净资金代理、成交量代理、流动性、盘口深度和日均盘口变动浮动率；该层只作为资金面代理分析，不伪装为 TAB 官方成交数据。
- 概率工程层：把赛制规则、Dixon-Coles/Bayesian Poisson、Elo/Bradley-Terry/FIFA/SPI 类强度、xG/xT/VAEP、市场赔率基准、Monte Carlo、校准指标和防泄漏规则纳入覆盖矩阵；未上线项标为 planned/partial，不伪装成已实现。
- 板块范围层：当前 TAB live nav 未列出或 route mismatch 的板块只进入排除审计队列，不计入当前推荐池、Top pick、Edge/套利率/RoR 汇总。
- 本地概率层：TAB 市场反推 xG、Poisson/Dixon-Coles、Elo/DC、goalmodel proxy 和质量 overlay。
- 赛事情境层：世界杯需要额外修正中立场、小组赛动机、淘汰赛保守性、国家队样本小、旅行与休息时间。
- 开源参考层：penaltyblog 用于 no-vig/盘口概率/ratings 思路，socceraction 用于 xT/VAEP 基本面路线，openfootball 用于 2026 赛程公开校验。
- 执行门禁层：raw refresh、formal report publish、public artifact safety 和 active backfill 未通过时，所有金额降级为 AUD 0 可执行。
- 复盘优化层：下注日志记录入场赔率、收盘赔率、结果、注额、CLV%、ROI 和平均 Edge，用于每日/周报回测优化。

## 概率工程吸收

- status: `framework_mapped_partial_implementation`
- fixed_random_seed_policy: `20260613`
- truthfulness_note: 本层吸收 ChatGPT 概率工程建议，并标注当前实现状态；未上线的 Dixon-Coles、Bayesian hierarchical、MCMC、xG/xT/VAEP、Monte Carlo 和新闻监控不会被伪装成已实现。
- default_next_upgrade: 优先补齐 opening/closing odds store、Brier/log loss 校准、赛制规则引擎、预测合约字段和 fixed-seed Monte Carlo；再接新闻/伤停 confirmed-vs-rumor 分级。

| 输出对象 | 典型结果 | 当前状态 | 当前证据 | 下一步 |
|---|---|---|---|---|
| 单场 | 胜/平/负概率、比分分布、进球数分布、双方xG、冷门概率 | partial | 推荐行已输出概率、EV、Edge、套利率、RoR；比分矩阵和双方xG仍为模型路线，不作为已验证事实。 | 用 Poisson / Dixon-Coles 统一生成 1X2、OU、BTTS、比分矩阵。 |
| 小组 | 出线概率、第一/第二/第三概率、淘汰概率 | planned | Group Betting 已进入盘口层分析；完整第三名出线与排名模拟仍未解锁为实装结果。 | 实现48队小组规则、净胜球、进球数、纪律分和最佳第三名排序。 |
| 淘汰赛 | 晋级概率、加时/点球概率、对阵路径难度 | planned | Futures 行可做阶段概率研究；路径难度、加时/点球仍需赛制模拟器。 | 接入淘汰赛 bracket、加时/点球概率和路径强度。 |
| 整届世界杯 | 进32强、16强、8强、4强、决赛、夺冠概率 | planned | 开源模型库含 Monte Carlo 路径参考；本报告未把整届模拟结果伪装成已上线。 | 固定 seed 做 Monte Carlo 锦标赛模拟并保存版本化输出。 |
| 风控 | 模型置信度、校准误差、与市场分歧、数据质量风险 | implemented_partial | 已输出模型一致性、复核优先级、Risk of ruin、资料缺口、门禁状态和安全边界。 | 补 Brier score、log loss、校准曲线和按盘口类型的 CLV 复盘。 |

| 模块 | 推荐状态 | 作用 | 关键输出 | 当前状态 |
|---|---|---|---|---|
| 赛制规则引擎 | 必做 | 精确模拟小组、第三名、淘汰赛路径。 | 小组排名、最佳第三、32强对阵。 | planned |
| 球队强度评级 | 必做 | 建立球队先验实力。 | 攻击强度、防守强度、中立场胜率。 | partial_reference |
| 单场进球模型 | 必做 | 预测比分和胜平负。 | 比分矩阵、P(胜/平/负)、总进球。 | partial_proxy |
| xG / xT / VAEP 特征 | 强烈推荐 | 衡量过程质量，而非只看比分。 | 射门质量、推进威胁、机会创造。 | design_reference |
| 球员与阵容层 | 强烈推荐 | 捕捉伤停、轮换、核心球员缺阵。 | 球员缺阵影响、首发强度。 | manual_checklist |
| 市场赔率基准 | 推荐 | 作为强基准和外部共识。 | 市场隐含概率、模型分歧。 | implemented |
| Monte Carlo 模拟 | 必做 | 评估整届赛事路径。 | 出线率、晋级率、夺冠率。 | planned |
| 概率校准 | 必做 | 防止看似准确但概率失真。 | Log loss、Brier、校准曲线。 | partial |
| 新闻/伤停监控 | 推荐 | 临赛前修正模型。 | 阵容更新、天气、旅行、纪律。 | manual_checklist |
| 回测与版本管理 | 必做 | 让预测可复现。 | 数据版本、模型版本、预测时间戳。 | partial |

## 赛制模拟与预测合约

赛制规则和预测字段是进入 automation 的硬前置：未实现的路径模拟不能被当作真实概率，缺少 timestamp/source version/odds phase 的推荐不能进入自动日报执行层。

| 赛制规则 | 决策用途 | 当前状态 | Automation门禁 |
|---|---|---|---|
| 48队 / 12组 / 每组4队 | 所有小组出线、Group Winner、To Qualify、Stage of Elimination 概率的基础分母。 | planned | 未实装前，长线阶段盘只保留研究候选，不把路径概率伪装成真实模拟结果。 |
| 每队小组三场 | 赛程密度、轮换、净胜球需求和末轮动机修正。 | planned | 需要 fixtures/versioned schedule 才能进入 Monte Carlo。 |
| 小组前二 + 8个最佳第三晋级32强 | 第三名出线概率、保守比赛策略和小组末轮价值盘筛选。 | planned | 必须实现 best-third ranking 后，才解锁完整小组出线概率。 |
| 小组排名 Tie-breakers | 同分下的净胜球、进球数、相互战绩、纪律分等排序影响组内盘口概率。 | planned | 未实现细则前，净胜球和纪律分盘口只作为人工复核项。 |
| 32强至决赛单场淘汰 | 晋级路径、对阵难度、加时/点球风险和资金锁定时间。 | planned | 必须生成 bracket path version 才能发布阶段概率。 |
| 加时与点球 | 淘汰赛晋级盘和90分钟赛果盘需要分开建模，不能混用概率。 | planned | 报告必须区分 90分钟、含加时、含点球 的盘口定义。 |
| 中立场与主办国例外 | 主客场标签不能直接照搬俱乐部模型；主办国和场地旅行需要额外修正。 | manual_checklist | 赛前原因必须注明中立场/旅行/休息天数是否已复核。 |
| 时间滚动资金约束 | 早期下注结算后会影响后续预算；不能静态把预算长期锁死。 | implemented_partial | 私有持仓未同步前，新增执行金额保持 AUD 0。 |

| 预测合约字段 | 必须 | 决策用途 | 当前状态 |
|---|---|---|---|
| prediction_timestamp | True | 每条概率和操作建议必须知道生成时点，便于按4小时频率追踪新旧变化。 | implemented |
| model_version | True | 同一盘口跨日报比较时区分模型变化、数据变化和赔率变化。 | policy_defined |
| data_source_version | True | 区分 TAB raw、公开赛程、开源模型和新闻源的版本。 | partial |
| odds_phase | True | opening / current / closing odds 分开记录，支持 CLV 和价格走差判断。 | planned |
| feature_time_scope | True | 赛前、赛中、赛后特征严格隔离，避免把赛后信息泄漏进赛前预测。 | policy_defined |
| news_confidence | True | confirmed 新闻可修正概率，rumor 只进入风险提示和降仓判断。 | planned |
| random_seed | True | Monte Carlo 和抽样模型可复现，避免同一输入重复运行给出漂移概率。 | policy_defined |
| market_definition | True | 区分90分钟、晋级、冠军、阶段淘汰、球员进球等盘口定义。 | implemented_partial |
| execution_gate_state | True | raw/private/report safety 未过时，候选只能 research-only，金额降为 AUD 0。 | implemented |

| 校准/回测控制 | 作用 | 当前状态 | Automation用途 |
|---|---|---|---|
| Brier score | 衡量概率预测平方误差，防止只看命中率。 | planned | 按盘口类型和模型版本分桶。 |
| Log loss | 惩罚过度自信的错误预测。 | planned | 用于降低高置信但校准差的模型权重。 |
| Calibration curve | 检查 55%、60%、70% 概率区间真实命中率是否匹配。 | planned | 日/周报展示校准漂移。 |
| CLV by market | 判断入场价格是否长期优于收盘价。 | partial | 正 CLV 策略保留，负 CLV 策略降权。 |
| ROI with sample guard | 真实收益必须结合样本量，避免小样本误判。 | partial | 按单场/长线/小市场分开评估。 |
| Closing odds store | 记录 closing odds 才能回测 CLV、RAEV 和价格纪律。 | planned | 赛前定时抓取并锁定 closing 快照。 |
| Settled position import | 把已下注、已结算、赢亏和余额变化同步到资金模型。 | blocked_by_private_profile | 只读 私有持仓 登录态未完成前不能解锁新增执行金额。 |

## 概率工程 Pipeline 与防泄漏规则

| Pipeline步骤 | 当前状态 | 控制规则 |
|---|---|---|
| 数据抓取 | partial | 公开 raw refresh 门禁；失败时不解锁执行金额。 |
| 数据校验 | implemented_partial | public artifact safety、board scope、route mismatch、staged raw gate。 |
| 特征生成 | partial | EV/Edge/RoR/市场资金代理已生成；xG/xT/VAEP仍为规划层。 |
| 模型训练 | planned | Bayesian hierarchical / ML 模型尚未声称上线。 |
| 概率校准 | partial | 开源模型分歧复核已接入；Brier/log loss/校准曲线待补。 |
| 赛制模拟 | planned | 48队规则、第三名出线、淘汰赛路径待实装。 |
| 报告生成 | implemented | JSON/Markdown/PDF/首页均输出研究-only报告。 |
| 模型监控 | partial | source model freshness、raw freshness、backfill queue、CLV/ROI路线。 |
| 结果回测 | partial | CLV/ROI回测 Dashboard 已有入口；样本与 settled 持仓仍受 private gate 影响。 |
| 异常告警 | partial | raw/private blockers、缺失报告、stale source 显示在 Dashboard。 |

| 防泄漏/可复现要求 | 必须 | 当前状态 | 证据 |
|---|---|---|---|
| 每条预测 timestamp | True | implemented | payload generated_at、snapshot_id 和 report_date。 |
| 每次运行固定 random seed | True | policy_defined | seed policy=20260613；完整 Monte Carlo 尚未上线。 |
| 每个数据源版本号 | True | partial | source_model_registry、latest_commit、raw health 有版本/时间；新闻源版本待补。 |
| opening / closing 赔率区分 | True | planned | 当前有入场/收盘赔率复盘口径；完整 opening/closing odds store 待补。 |
| confirmed / rumor 新闻区分 | True | planned | 赛前清单要求复核，尚未接新闻源分级。 |
| 赛前/赛中/赛后特征隔离 | True | policy_defined | 下注报告仅使用赛前研究数据；赛中/赛后特征隔离规则已写入政策。 |

## 模型监控指标

| 指标 | 作用 | 当前状态 |
|---|---|---|
| CLV | 验证是否比收盘市场更早捕捉信息。 | partial |
| ROI | 复盘真实收益，但样本不足时不能单独评价模型。 | partial |
| Brier score | 衡量概率预测平方误差。 | planned |
| Log loss | 惩罚过度自信的错误概率。 | planned |
| 校准曲线 | 检查预测概率与真实命中频率是否一致。 | planned |
| 模型-市场分歧 | 识别 value bet 与逆共识复核队列。 | implemented_partial |

## 目标与指标落地

| 模块 | 目标 | 常用指标 | 输出 | 当前状态 |
|---|---|---|---|---|
| 赔率/盘口分析 | 判断市场价格是否合理。 | 欧赔、亚盘、大小球、隐含概率、返还率、盘口变化。 | 是否存在 value bet。 | implemented_partial |
| 球队实力分析 | 估计双方真实强弱。 | Elo、近期xG/xGA、净胜球、射门质量、控球推进、定位球。 | 基础胜平负概率。 | partial_reference |
| 进球模型 | 估计比分分布。 | 泊松、双泊松、Dixon-Coles、xG-adjusted Poisson。 | 1X2、大小球、BTTS、比分概率。 | planned |
| 阵容与战术 | 判断模型外信息。 | 伤停、轮换、首发、赛程、压迫强度、边路错位。 | 修正胜率和进球期望。 | manual_checklist |
| 赛事语境 | 处理动机和赛制。 | 小组赛/淘汰赛、必须赢、轮换、净胜球需求。 | 调整节奏和风险偏好。 | planned |
| 市场选择 | 选最适合的玩法。 | 1X2、亚洲让球、大小球、角球、牌数、球员数据。 | 选择赔率误差最大的市场。 | implemented_partial |
| 资金管理 | 防止破产。 | 固定比例、半 Kelly、最大回撤、止损。 | 每注金额。 | implemented_partial |
| 复盘验证 | 检查方法是否有效。 | CLV、ROI、样本量、Brier score、校准曲线。 | 保留/淘汰策略。 | partial |

## 机器学习候选模型

机器学习模型当前只作为候选路线和复核矩阵，不替代已验证的盘口门禁；上线前必须通过数据泄漏检查、概率校准和回测。

| 模型 | 适合任务 | 优点 | 风险 | 当前决策 |
|---|---|---|---|---|
| Logistic Regression | 胜平负、是否晋级。 | 可解释、稳定。 | 非线性不足。 | baseline_candidate |
| Random Forest | 非线性特征。 | 鲁棒。 | 概率校准一般。 | benchmark_candidate |
| XGBoost / LightGBM | 表格特征融合。 | 表现强。 | 容易数据泄露。 | candidate_after_leakage_gate |
| CatBoost | 类别特征多。 | 对类别友好。 | 参数调优复杂。 | candidate_after_data_volume_check |
| Neural Network | 大规模事件序列。 | 表达能力强。 | 国际赛样本不足。 | defer_until_event_data |
| Graph Neural Network | 球员网络/传球网络。 | 战术表达强。 | 数据门槛高。 | research_reference_only |
| Transformer | 事件序列建模。 | 可捕捉上下文。 | 对公开数据要求高。 | research_reference_only |

## 技术面与模型公式

- 技术面规则覆盖：EV / RAEV / CLV、去水公平概率、Value bet Edge 纪律。

| 名称 | 公式 | 决策规则 | 当前状态 |
|---|---|---|---|
| EV 期望下注 | EV = 模型认为的胜利概率 × 盘口赔率 - 1 | EV 大于 0 才可能进入价值候选；仍需 Edge、RoR、价格容忍度和门禁复核。 | implemented |
| RAEV 去水后价值 | RAEV = 模型认为的胜利概率 × 去水后盘口公平赔率 - 1 | 用于区分真实模型优势和庄家水位造成的表面优势。 | planned |
| 去水公平概率 | 去水 = 将同一市场所有隐含概率归一化为 100% | 先把赔率转隐含概率，再去除水位，最后比较模型概率和公平概率。 | partial |
| Value bet纪律 | Edge = 模型概率 - 去水公平概率；Edge ≥ 2%-3% 且 EV > 0 才下注 | 小市场使用更高缓冲；资料缺口或盘口异常时降级为观察。 | implemented_partial |
| CLV 信息捕获 | CLV = 下注时赔率是否优于 closing odds | 长期正 CLV 才说明可能比市场更早捕捉信息；单次正 CLV 不等于策略有效。 | partial |

| 模型 | 公式 | 用途 | 当前状态 |
|---|---|---|---|
| Poisson Model | 主队进球数 ~ Poisson(lambda_home)；客队进球数 ~ Poisson(lambda_away) | 用 lambda_home / lambda_away 生成比分分布、胜平负和总进球概率。 | planned |
| Dixon-Coles-Adjusted Poisson Model | 在普通双泊松上修正 0-0、1-0、0-1、1-1 等低比分相关性。 | 减少低比分市场误差，尤其用于 1X2、OU、BTTS 和 Correct Score。 | planned |

## 基本面分析层

基本面层级按 Team / Player / Tactical / News 拆开；confirmed 信息才进入概率修正，rumor 只进入风险提示。

| 层级 | 输入 | 决策用途 | 当前状态 |
|---|---|---|---|
| Team Level | Home/Away、阵容、伤停、赛程、近期胜率、进球时间分布。 | 调整基础胜平负概率、进球期望和轮换风险。 | manual_checklist |
| Player Level | 核心球员缺阵、首发强度、替补深度、纪律停赛。 | 修正球队强度和临场不确定性。 | planned |
| Tactical Style | 压迫强度、边路错位、定位球、控球推进、射门质量。 | 识别盘口类型适配度，例如总进球、BTTS、角球或牌数。 | design_reference |
| News Context | confirmed 新闻、rumor 新闻、天气、旅行、赛前发布会。 | 临赛前复核，confirmed 才进入概率修正，rumor 只进风险提示。 | planned |

## 市场资金分析

该板块使用公开盘口可见信息推断资金面压力，不声称读取到 TAB 官方成交资金或订单簿。

- data_status: `proxy_inferred_from_public_odds`
- total_funds_proxy_aud: `AUD 0`
- net_funds_proxy_aud: `AUD 0`
- turnover_proxy_aud: `AUD 0`
- average_liquidity_score: `0.00%`
- average_market_depth_score: `0.00%`
- average_daily_line_move_float_rate: `0.00%`

| 时间 | 盘口 | 下注 | 资金倾向分 | 倾向 | 总资金代理 | 净资金代理 | 成交量代理 | 流动性 | 盘口深度 | 日均盘口变动浮动率 |
|---|---|---|---:|---|---:|---:|---:|---|---|---:|

## 模型共识校准

| 下注 | 模型一致性 | 共识方向 | 共识概率 | 模型均值 | 本地概率差 | 最大分歧 | 复核优先级 | 复核动作 |
|---|---|---|---:|---:|---:|---:|---|---|

## Excel模板吸收范围

- template_read_status: `not_found`
- sheet_count: `7`
- template_formula_count: `0`
- detected_topics: `赛前检查、赔率去水、EV/Edge、Kelly仓位、Poisson/xG、下注日志、CLV/ROI`
- evidence_terms: ``

| Sheet | 样例字段 | 当前用途 |
|---|---|---|
| 状态总览 | 结构画像 | 总览模板模块，确认本报告采用范围与默认方案。 |
| 赛前10分钟清单 | 结构画像 | 作为最后下注检查清单；未通过则暂停执行或降仓。 |
| 赔率与Edge | 结构画像 | 计算盈亏平衡概率、EV、Edge、Kelly 和建议仓位。 |
| 泊松模型 | 结构画像 | 提供 xG/λ 到 1X2、大小球、BTTS 的概率结构。 |
| 下注日志 | 结构画像 | 记录赔率、结果、Profit、ROI、CLV，用于日报/周报校准。 |
| 示例分析 | 结构画像 | 只吸收分析结构，不把虚拟示例当真实下注依据。 |
| 参数与说明 | 结构画像 | 统一术语、公式、Edge门槛和资金纪律解释。 |

## Excel模板证据增强

| 资料 | Excel证据 | 报告落地 |
|---|---|---|
| 赛前 No Bet 过滤 | 模板明确把盘口价格、去水、首发、伤停、动机、疲劳、战术、节奏和资金管理作为赛前10分钟检查项。 | 写入逐行 pre_bet_checklist 和 data_gaps，任一关键项未确认时保持研究-only或降仓。 |
| EV/Edge/Kelly 计算链 | 模板公式覆盖 0 个单元；赔率表包含隐含概率、去水公平概率、EV、满Kelly、折扣Kelly、建议注额。 | 转化为 Edge信息、套利率、最低可接受赔率、半Kelly、Kelly安全垫和仓位上限占用。 |
| Poisson/xG 概率结构 | 模板用主/客队 λ 生成比分矩阵、1X2、大小球和 BTTS 概率，并提示低比分相关性需谨慎。 | 作为概率基本面解释和盘口概率交叉验证，不单独绕过价格价值门槛。 |
| 复盘与模型校准 | 模板下注日志记录入场赔率、收盘赔率、结果、注额、ROI、CLV% 和平均 Edge。 | 进入日报/周报旧报告对比、CLV/ROI 复盘和概率校准队列。 |
| 世界杯特殊修正 | 模板参数说明要求 FIFA/世界杯国家队比赛额外修正中立场、小组赛动机、淘汰赛保守性和样本小。 | 写入中文原因和赛前事件风险，不把俱乐部联赛模型直接照搬到世界杯。 |

## Excel决策规则


## 风控纪律

- 基础单注：0.5%-1.0% bankroll；单注上限：2.0% bankroll。
- Edge 阈值：主流市场 2%-3%；小市场 4%-6%。
- 优先玩法：亚洲让球 / 大小球 > 1X2 > 角球/牌数 > 正确比分。
- 赛前复核：赛前10分钟复核价格、去水、首发、伤停、动机、赛程疲劳、战术匹配和大小球节奏。
- 禁止动作：追损、加倍、情绪下注、无首发重仓、无记录下注。
- 世界杯修正：中立场、小组赛动机、淘汰赛保守性、国家队样本小、旅行与休息时间。
- 复盘优先级：先看 CLV，再看 ROI；样本不足时不因短期输赢推翻模型。

## 组合风险与预算压力

- verification_status: 用户声明参考值，待持仓快照同步确认；未同步前不解锁执行。
- recommended_action: `无组合研究候选`

| 指标 | 数值 | 解释 |
|---|---:|---|
| 预算区间 | AUD 3,000 - AUD 5,000 | 用户目标总预算区间；中位预算 AUD 4,000。 |
| 已投入参考 | AUD 2,000 | 用户声明参考值，待持仓快照同步确认。 |
| 研究候选总金额 | AUD 0 | 当前可研究买入候选的总研究金额。 |
| 组合预计收益 | AUD 0 | 按各行 EV × 注额加总。 |
| 每AUD100组合预期 | AUD 0 | 注额加权 EV 转成金额。 |
| 最坏全输新增亏损 | AUD 0 | 只计算本轮研究候选，不含未同步持仓。 |
| 组合Risk of ruin | 0.00% | 等级 低；复核 通过。 |
| 中位预算总占用 | 50.00% | 已投入参考 + 本轮候选金额，占 AUD 4,000 中位预算比例。 |
| 预算下沿余量 | AUD 1,000 | 以 AUD 3,000 下沿测算，负数代表应降仓。 |

## 缺失板块排除审计

这些行来自历史/旧日报候选，但当前 TAB live nav 未确认板块可读，因此不进入当前推荐池。

| 板块 | 盘口 | 下注 | 原动作 | 原金额 | 范围状态 | 原因 |
|---|---|---|---|---:|---|---|
| 2026 World Cup Matches | Brazil v Morocco / Result | Morocco | 买入 | AUD 15 | 板块缺失排除 | Matches 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Matches | France v Senegal / Result | Senegal | 买入 | AUD 15 | 板块缺失排除 | Matches 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Matches | England v Croatia / Result | Croatia | 买入 | AUD 15 | 板块缺失排除 | Matches 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Matches | Netherlands v Japan / Result | Japan | 买入 | AUD 15 | 板块缺失排除 | Matches 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Matches | Belgium v Egypt / Total Goals Over/Under | Under 2.5 Goals | 买入 | AUD 15 | 板块缺失排除 | Matches 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Matches | South Korea v Czechia / Both Teams to Score | Only One or Neither to score | 买入 | AUD 15 | 板块缺失排除 | Matches 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Matches | Brazil v Morocco / Total Goals Over/Under | Under 2.5 Goals | 买入 | AUD 10 | 板块缺失排除 | Matches 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Futures | Belgium / To Qualify for Quarter Final | Belgium | 观察/不下注 | AUD 0 | 板块缺失排除 | Futures 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Group Betting | Group K / Group Winner | Colombia | 观察/不下注 | AUD 0 | 板块缺失排除 | Group Betting 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Australia Markets | AUS Group Match Wins / AUS Group Match Wins | AUS Win 0 Grp Matches | 观察/不下注 | AUD 0 | 板块缺失排除 | Australia Markets 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Team Futures Multi | Belgium / Reach Quarter Final | Belgium | 观察/不下注 | AUD 0 | 板块缺失排除 | Team Futures Multi 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |
| 2026 World Cup Futures | Colombia / To Qualify for Quarter Final | Colombia | 观察/不下注 | AUD 0 | 板块缺失排除 | Futures 当前状态为 discovery_missing，不能用旧盘口生成当前下注建议。 |

## 判断依据来源

| 类型 | 来源/公式 | 当前作用 |
|---|---|---|
| Excel模板 | football_betting_analysis_ABC_template.xlsx；Excel模板未在本机 Downloads 找到，当前使用内置结构画像：7个预期sheet，模块为赛前检查、赔率去水、EV/Edge、Kelly仓位、Poisson/xG、下注日志。 | 下注前清单、赔率去水、EV、Edge、Kelly、下注日志和 CLV/ROI 复盘 |
| Edge | Edge = 模型概率 - 赔率盈亏平衡概率 | 判断模型概率是否超过赔率盈亏平衡 |
| 套利率 | 套利率 = max(0, 模型概率 × 十进制赔率 - 1)，这是价值套利率，不是跨平台无风险套利证明。 | 衡量价值率；不是跨平台 surebet |
| Risk of ruin | Risk of ruin 为基于中位资金池、单注比例、半Kelly偏离和盘口风险标记的保守启发式估计，并输出低/中/偏高/高等级。 | 控制单注比例、半Kelly偏离和盘口风险 |
| 最低可接受赔率 | 最低可接受赔率 = 1 / (模型概率 - Edge门槛)；若 TAB 实时赔率低于该值，则即使 EV 为正也不建议执行。 | 防止实时赔率下滑后继续执行过期价值 |
| 预计收益 | 预计收益 = 建议研究金额 × EV；每 AUD100 预期收益 = 100 × EV，用于跨盘口快速比较。 | 把 EV 转成金额，便于按预算排序 |
| 价格容忍度 | 价格容忍度 = (当前赔率 - 最低可接受赔率) / 当前赔率；为负表示价格已经走差。 | 判断 TAB 实时赔率是否仍有执行空间 |
| 仓位上限占用 | 仓位上限占用 = 单注资金比例 / 2%单注上限；超过100%时必须降仓或放弃。 | 判断是否接近或超过单注上限 |
| 风险调整价值分 | 风险调整价值分 = EV + max(0, Edge门槛差) - Risk of ruin；用于同一报告内排序，不等于真实收益保证。 | 统一比较价值与 RoR 的相对优先级 |
| 市场资金倾向分 | 市场资金倾向分 = 50 + EV/Edge/套利率/价格容忍度价值压力 + 流动性/盘口深度压力 - RoR/盘口浮动/风险事件压力；0-100分，属于盘口资金代理指标。 | 给首页新增资金倾向列，并作为资金面复核排序依据 |
| 市场资金代理 | 总资金/净资金/成交量/流动性/盘口深度/日均盘口变动浮动率均由市场类型、赔率区间、价值信号、价格容忍度、仓位比例和风险标记估算；TAB公开页未披露真实成交资金。 | 输出总资金、净资金、成交量、流动性、盘口深度和盘口浮动率代理 |
| 组合RoR | 组合RoR = 注额加权行级RoR + 集中度惩罚 + 偏高RoR行惩罚 + 预算压力惩罚；用于研究候选组合压力测试，不等于真实破产概率。 | 把多条研究候选合并成预算压力测试 |
| 开源参考 | Hicruben 2026 WC, goalmodel, RyanSCodes DC, penaltyblog, socceraction, openfootball worldcup.json | 提供 no-vig、xG/Poisson/DC、事件基本面、赛程校验等补充判断依据 |

## Excel赛前控制映射

| 控制项 | Excel依据 | 报告映射 | 决策用途 |
|---|---|---|---|
| 盘口价格 | 当前赔率是否仍高于最低可买价；价格走差就放弃，不补买。 | 最低可接受赔率、赔率缓冲、价格容忍度。 | 低于最低赔率时从买入候选降级为观察/放弃。 |
| 盘口去水与Edge | 模型概率需高于公平概率并超过 Edge 阈值。 | 模型概率、盈亏平衡概率、Edge、Edge门槛、门槛差。 | Edge 未达门槛时不因 EV 单项为正直接执行。 |
| Kelly与单注上限 | 基础单注0.5%-1.0% bankroll，单注上限2%，使用半Kelly或四分之一Kelly。 | 半Kelly、仓位比例、仓位上限占用、Kelly安全垫。 | 超过半Kelly或2%上限时进入降仓/放弃队列。 |
| Poisson/xG | λ 负责概率结构，不负责判断赔率是否便宜。 | Poisson/xG、Elo/DC、goalmodel proxy 与 TAB 盘口概率交叉校验。 | 只用于概率校准和基本面解释，不绕过赔率价值门槛。 |
| 赛前10分钟 | 首发、伤停、动机、疲劳、战术、节奏和资金管理任一关键项不通过则 No Bet。 | 赛前事件风险、风险触发因素、RoR复核状态。 | 赛前信息不完整时保持研究候选，执行前必须复核。 |
| CLV/ROI复盘 | 先看 CLV，再看 ROI；不要只复盘输赢。 | 下注日志、入场/收盘赔率、收益率、新旧报告对比。 | 用于日报/周报概率校准，不用短期输赢推翻模型。 |
| Risk of ruin | 模板未直接给出破产概率公式，本系统用资金比例、半Kelly偏离和风险事件做保守估计。 | Risk of ruin、RoR等级、RoR复核队列、风险调整价值分。 | RoR 达到复核线时降仓或延后执行。 |

## 逐行判断依据包

| 下注 | 证据强度 | 概率价值依据 | 价格执行依据 | 风险控制依据 | 资料缺口 | 赛前复核清单 |
|---|---|---|---|---|---|---|

## Edge/RoR 决策诊断

| 下注 | 价值信号 | 当前赔率 | 最低可接受赔率 | 赔率缓冲 | 价格容忍度 | 每AUD100预期 | 本注预计收益 | 上限占用 | Kelly安全垫 | 风险调整分 | RoR复核 | 结论 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|

## 三指标解释包

| 下注 | Edge解释 | 套利率解释 | Risk of ruin解释 | 综合动作 |
|---|---|---|---|---|

## 新旧推荐变化

- compare_status: `compared`
- previous_generated_at: `2026-06-13T14:36:47.703202+10:00`
- candidate_count_delta: `-10`
- research_stake_delta_aud: `-100.0`
- executable_stake_delta_aud: `0.0`
- top_pick_changed: `True`

## 推荐操作清单

| 时间 | 板块 | 盘口 | 下注 | 赔率 | 金额 | 操作 | 分析一致性 | 模型复核 | 盘口价值 | 市场资金倾向分 | Edge | Edge门槛差 | 套利率 | Risk of ruin | RoR等级 | EV | 概率 | 置信度 | 原因 |
|---|---|---|---|---:|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|---|

> 本报告在 raw 或日报发布门禁失败时会把所有候选降级为研究-only，当前可执行新增金额为 AUD 0。

> 该报告只生成下注研究和操作建议，不自动下注、不点击赔率、不添加投注单。