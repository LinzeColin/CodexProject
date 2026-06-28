# PFI 参数变更记录

参数版本：`v0.2.2`

任务名：`PFI v0.2.2 E2E 逻辑优化`

本文件从 Stage 0 开始记录参数、公式、阈值、分类、标签、Interconnection、汇率和 Runtime Diff 规则的变更。每条记录必须说明旧值、新值、原因和影响范围。

## 变更记录

| 时间 | Stage/Phase/Task | 字段 | 旧值 | 新值 | 原因 | 影响范围 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-28 | `S0-P2-T1` | `parameter_version` | `v0.2.1 前端优化` | `v0.2.2` | 锁定本轮为数据库治理和 E2E 逻辑优化。 | 三基文件、Stage 0 baseline、后续参数一致性测试。 |
| 2026-06-28 | `S0-P2-T1` | `task_name` | `OWNER-APPROVED-NEXT-ROADMAP` | `PFI v0.2.2 E2E 逻辑优化` | 用户提供 Stage -> Phase -> Task roadmap，需建立正式任务入口。 | 开发记录、模型参数文件、功能清单、roadmap lock。 |
| 2026-06-28 | `S0-P1-T3` | `uiux_scope` | `v0.2.1 HTML Web Shell` | `v0.2.1 HTML Web Shell 继续作为 UIUX 基线；v0.2.2 Stage 0 不改前端显示` | 用户明确 HTML 模板只是帮助理解，不是要求修改 UIUX。 | Stage 0 合同、baseline report、测试。 |
| 2026-06-28 | `S0-P2-T2` | `parameter_changelog` | `无独立文件` | `PFI/config/parameter_changelog.md` | Roadmap Stage 0 Phase 0.2 要求新增参数变更记录文件。 | 后续所有参数变更必须写入本文件。 |
| 2026-06-28 | `S1-P1-T1` | `parameter_directory` | `散落在三基、Stage 0 baseline、代码 fixture 和前端合同` | `模型参数文件.md` 新增 Stage 1 参数治理总目录 | Stage 1 要求货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化和测试集中可读。 | 三基文件、后续参数中心、参数一致性测试。 |
| 2026-06-28 | `S1-P1-T2` | `machine_readable_parameter_file` | `无` | `PFI/config/pfi_parameters.yaml` | Stage 1 要求新增机器可读参数文件；字段中文说明可在 Markdown 查到。 | 参数读取、合同测试、后续 Stage 2-13 参数源。 |
| 2026-06-28 | `S1-P1-T2` | `parameter_yaml_naming` | `草案名 PFI/config/pfi_v022_parameters.yaml` | `canonical PFI/config/pfi_parameters.yaml` | Stage -> Phase -> Task roadmap 和 Stage 0 文件定位指定 `pfi_parameters.yaml`；只保留一个机器可读参数源避免漂移。 | 参数治理、文档、测试、后续实现。 |
| 2026-06-28 | `S1-P1-T3` | `parameter_consistency_test` | `无` | `PFI/tests/test_pfi_parameters_consistency.py` | Stage 1 要求测试确认 Markdown/YAML/前端显示的核心阈值一致。 | 测试、GitHub 验收、后续参数变更防漂移。 |
| 2026-06-28 | `S1-P2-T1` | `formula_explanations` | `部分公式只散见于代码或 Stage 0 baseline` | `每个核心公式有中文名称、用途、输入、输出、计算逻辑、示例` | 用户要求人类可读；不能只有英文变量或代码名。 | 模型参数文件、报告解释、后续参数中心。 |
| 2026-06-28 | `S1-P2-T2` | `threshold_rationale` | `阈值解释不集中` | `每个核心阈值有当前值、存在原因、影响页面、能否用户修改` | 用户质疑阈值设计依据，需要集中解释和可验收。 | 消费管理、投资管理、现金流、建议与复盘、测试。 |
| 2026-06-28 | `S1-P2-T3` | `variable_alias_dictionary` | `无统一中文别名` | `gross_consumption_cny = 消费总流出金额；living_consumption_cny = 生活消费金额；future_cash_balance = 未来现金余额` | 公式变量必须能被非专业用户理解。 | 模型参数文件、后续 UI 参数中心、报告说明。 |
| 2026-06-28 | `S1-P1-T3` | `Markdown/YAML/前端显示一致性` | `未建立 Stage 1 gate` | `一致性测试覆盖 CNY、CNY/AUD=4.70、06:00、70 分、CNY 2000、AUD 500、22:00-06:00、7/21/30/60/90/180/360` | 防止参数文件、YAML、UI fixture 和测试 fixture 分裂。 | 参数治理、前端合同、Stage 2 入口。 |
| 2026-06-28 | `S2-P1-T1` | `currency.base_currency` | `CNY 已锁定但部分前端主金额仍显示 AUD` | `CNY 主显示` | Stage 2 要求首页、投资、消费、现金流、报告主口径统一为 CNY。 | Web Shell 主金额、参数文件、合同测试。 |
| 2026-06-28 | `S2-P1-T2` | `currency.frontend_fx_badge_pair` | `CNY/AUD` | `AUD/CNY` | 任务包目标为 `AUD/CNY=4.81`，含义是 1 AUD 折 CNY；当前真实快照为 4.6874。 | 顶部徽标、README、模型参数、Web Shell、测试。 |
| 2026-06-28 | `S2-P1-T2` | `fx.frontend_badge_format` | `CNY/AUD=4.70（YYYYMMDD--HH:MM）` | `AUD/CNY=4.69（YYYYMMDD--HH:MM）` | 当前展示应对应真实 `AUD/CNY` 本地快照，保留 06:00 时间格式。 | Web Shell、参数一致性测试、Stage 2 文档。 |
| 2026-06-28 | `S2-P1-T3` | `ledger.amount_fields` | `未统一记录 Stage 2 必填金额字段` | `原始金额、原始币种、CNY金额、汇率快照ID` | 账本必须同时保留原始币种和 CNY 主口径，后续审计可追溯快照。 | 统一账本、导入管线、报告、测试。 |
| 2026-06-28 | `S2-P2-T1` | `fx.effective_date_cutoff` | `06:00 已记录但未实现函数` | `effective_fx_date(timezone=Australia/Sydney, cutoff=06:00)` | Stage 2 要求 06:00 前使用前一日，06:00 及之后使用当天。 | 汇率快照读取、报告 gate、测试。 |
| 2026-06-28 | `S2-P2-T2` | `fx.default_network_refresh` | `false，文档约束` | `false，代码强制` | 普通本地运行不得默认联网刷新汇率。 | 本地运行、CLI、测试、隐私边界。 |
| 2026-06-28 | `S2-P2-T2` | `fx.explicit_refresh_requires_allow_network` | `无` | `true` | 只有显式 `--allow-network` 才可访问外部汇率 API。 | CLI、运维说明、测试。 |
| 2026-06-28 | `S2-P2-T3` | `fx.snapshot_directory` | `无正式目录` | `PFI/data/fx_snapshots/AUD_CNY/` | Stage 2 要求本地保存每日快照，包含来源、读取时间、pair 和 hash。 | 数据目录、GitHub 验收、报告 gate。 |
| 2026-06-28 | `S2-P2-T3` | `fx.latest_snapshot` | `无真实快照` | `fx_AUD_CNY_20260628 / rate=4.6874 / hash=2e0d770f16f07543bfe03f9189f1be923b2ef4518a346c79788655600040018b` | 建立真实汇率读取证据，后续普通运行只读本地快照。 | Web Shell 徽标、合同测试、审计报告。 |
| 2026-06-28 | `S2-P2-T3` | `fx.missing_snapshot_status` | `未统一` | `汇率数据待更新` | 缺失有效快照时必须中文提示并阻止正式报告，不得伪造实时汇率。 | Web Shell、报告、测试、风控。 |
| 2026-06-28 | `S3-P1-T1` | `data_sources.source_profile_schema` | `Stage 2 仅记录 required_source_ids 和中文 capability 列表` | `source profile schema 支持 wallet/bank/broker/fund_platform/bullion_platform/payment_platform/manual_snapshot/other` | 新增数据源不能再靠核心代码或 source 名称硬编码。 | 数据源与上传、账本流水、账户与资产、报告与洞察。 |
| 2026-06-28 | `S3-P1-T2` | `data_sources.capabilities` | `中文能力列表` | `cash_ledger/investment_trade/fund_trade/bullion_trade/balance_snapshot/fee/refund/transfer` | 能力需要机器可读，便于后续 parser、ledger 和报告按能力组合。 | 数据源 profile、导入、测试、参数中心。 |
| 2026-06-28 | `S3-P1-T3` | `data_sources.other_source_template` | `无` | `other_source_template` | 未来新增 source 必须有模板，不应修改核心计算代码。 | 数据源接入、手工快照、复核队列。 |
| 2026-06-28 | `S3-P2-T1` | `account_roles.account_role_schema` | `multiple_roles_per_account=true 但缺少完整 schema` | `required_fields=account_id/source_id/role/role_effective_from/role_effective_to；multiple_roles_per_account=true` | 一个账户可同时是主钱包、消费账户、投资入金来源和收入账户。 | 账户与资产、消费管理、投资管理、现金流。 |
| 2026-06-28 | `S3-P2-T2` | `account_roles.role_effective_date_required` | `文档约束` | `true，字段为 role_effective_from / role_effective_to` | 角色随时间变化时必须能解释历史账本。 | 账户角色、账本复核、报告追溯。 |
| 2026-06-28 | `S3-P2-T3` | `event_types.role_event_calculation_policy` | `只写明后续按角色和事件类型判断` | `metric_basis=role_and_event_type；forbid_source_name_hardcode=true` | 消费金额不等于支付宝+微信+银行卡，而是事件影响标记和账户角色共同决定。 | 消费管理、账本流水、投资管理、现金流、报告与洞察。 |
| 2026-06-28 | `S4-P1-T1` | `interconnection.economic_event_id` | `缺少真实经济事件 ID` | `required=true；同一真实事件只有一个 economic_event_id` | 多来源记录必须能归并为同一真实资金事件，避免银行扣款、券商入金、持仓变化重复计算。 | 账本流水、首页总览、消费管理、投资管理、现金流、报告与洞察。 |
| 2026-06-28 | `S4-P1-T2` | `interconnection.interconnection_group_id` | `缺少跨来源关联组 ID` | `required=true；同一资金链路归入同一 interconnection_group_id` | CBA -> Moomoo、支付宝基金申购、退款、信用卡还款等需要可追踪的关联组。 | 账本复核、账户与资产、投资管理、消费管理、报告审计。 |
| 2026-06-28 | `S4-P1-T3` | `interconnection.event_type_policies` | `只存在粗粒度 affects_consumption` | `为每个 event_type 定义 total_consumption_outflow/living_consumption/investment/net_worth/cashflow flags` | 首页、消费、投资、现金流和报告必须使用同一指标口径。 | 指标计算、报告解释、测试、参数中心。 |
| 2026-06-28 | `S4-P2-T1` | `interconnection.interconnection_matrix` | `无正式中文矩阵` | `PFI/docs/pfi_v02/INTERCONNECTION_MATRIX.md` | Stage 4 要求每类事件可读、可验收、可复核。 | GitHub 验收、三基文件、后续 UI 参数中心。 |
| 2026-06-28 | `S4-P2-T2` | `interconnection.matrix_fields` | `无统一字段` | `event_type/中文名/是否影响消费总流出/生活消费/投资/净资产/现金流/展示面/抵消规则` | 矩阵字段必须覆盖 roadmap 要求的所有口径。 | Interconnection Matrix、合同测试、报告说明。 |
| 2026-06-28 | `S4-P2-T3` | `consumption_model.double_count_rules` | `投资入金、基金申购、信用卡还款、退款规则未形成统一机器口径` | `投资入金和基金申购进入消费总流出但不进入生活消费；退款抵消原消费；信用卡还款不重复计入生活消费` | 满足 Stage 4 stop condition：不得出现投资入金未进入消费总流出、基金申购未进入消费总流出或投资入金错误进入生活消费。 | 消费总流出、生活消费、投资现金、基金资产、现金流、报告与洞察。 |
| 2026-06-28 | `REVIEW-S4` | `interconnection.core_dedupe_key` | `主要按 economic_event_id 去重` | `优先按 interconnection_group_id + event_type 去重；缺少关联组时按 economic_event_id + event_type 兜底` | 防止同一关联组内银行侧、券商侧、基金份额侧或支付侧因来源 economic_event_id 不一致而重复进入核心金额。 | 消费总流出、投资现金、现金流、报告与洞察、复审测试。 |
| 2026-06-28 | `REVIEW-S4` | `interconnection.metric_dependency_graph.cashflow` | `income, refund, credit_card_repayment, internal_transfer, fx_conversion` | `investment_deposit, fund_subscription, bullion_purchase, investment_buy, investment_sell, income, fee, refund, credit_card_repayment, internal_transfer, fx_conversion` | 现金流必须覆盖投资与费用现金事件，避免首页、现金流和报告漏看投资动作的现金压力。 | 首页总览、投资管理、现金流、报告与洞察、参数一致性。 |
| 2026-06-28 | `S5-P1-T1` | `event_types.stage5_ledger_event_type_table` | `Stage 4 event_type_policies，未单独包含估值事件` | `13 类统一账本事件，包含估值和汇率兑换` | Stage 5 要求事件类型表足以表达真实资金流、估值和汇率兑换。 | 账本流水、首页总览、消费管理、投资管理、现金流、报告与洞察、测试。 |
| 2026-06-28 | `S5-P1-T2` | `event_types.required_affects_flags` | `Stage 4 flags 已用于 Interconnection` | `Stage 5 事件类型表强制五个 flags：消费总流出、生活消费、投资、净资产、现金流` | 每种事件必须绑定影响口径，避免首页、消费页和报告解释不一致。 | 指标计算、参数中心、报告说明、合同测试。 |
| 2026-06-28 | `S5-P2-T1` | `consumption_model.gross_consumption_includes` | `Stage 4 已覆盖普通消费、投资入金、基金申购、黄金申购、投资买入、费用` | `正式锁定为生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，退款抵消` | Stage 5 要求新增消费总流出金额并进入首页、消费页和报告模板。 | 首页总览、消费管理、报告与洞察、测试。 |
| 2026-06-28 | `S5-P2-T2` | `consumption_model.living_consumption_excludes` | `Stage 4 规则已排除投资入金、基金申购、投资买入` | `排除投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款` | 保证生活消费不被投资资金流和还款污染。 | 消费管理、预算、报告、测试。 |
| 2026-06-28 | `S5-P2-T3` | `consumption_model.double_consumption_surfaces` | `无正式 Stage 5 展示面参数` | `homepage, consumption_page, report 同时展示消费总流出与生活消费` | 避免只显示一个消费数字导致误解。 | 首页总览、消费管理、报告与洞察、测试。 |
| 2026-06-28 | `S5-P3-T1..S5-P3-T4` | `consumption_categories.default_taxonomy` | `只有数量上限，无正式 12 大类 / 50 中类 taxonomy` | `12 个 L1、50 个 L2、每个 L1 有 future_merge_to / merge_candidate` | Stage 5 要求建立默认消费分类，并预留后续压缩到 10 类或更少的字段。 | 账本流水、消费管理、报告与洞察、参数中心、测试。 |
| 2026-06-28 | `S6-P1-T1` | `tags.tag_tables` | `只有默认标签组和生命周期说明` | `pfi_tags, pfi_tag_assignments, pfi_tag_rules, pfi_tag_history, pfi_custom_views` | Stage 6 要求标签 registry、赋值、规则、历史和自定义视图可持久化。 | 账本流水、报告与洞察、数据库治理、测试。 |
| 2026-06-28 | `S6-P1-T2` | `tags.assignment_policy` | `无机器可验收赋值表` | `同一 transaction/economic_event/holding/account 可拥有多个 tag_id` | 标签区别于主分类，必须支持多维分析。 | 账本筛选、报告聚合、建议复盘。 |
| 2026-06-28 | `S6-P1-T3` | `tags.tag_rule_dimensions` | `无自动标签规则维度` | `amount_cny, time_window, l1_category, event_type, account_role` | 支持按金额、时间、分类、事件类型、账户角色自动打标签。 | 消费复盘、投资复盘、现金流观察、测试。 |
| 2026-06-28 | `S6-P2-T1` | `tags.default_tag_library` | `default_tag_groups 只有组名` | `通用、消费、投资、数据质量、现金流、复盘默认标签库` | 默认标签必须覆盖关键分析维度。 | 账本流水、消费管理、投资管理、数据质量、报告。 |
| 2026-06-28 | `S6-P2-T2` | `tags.custom_tag_lifecycle` | `新增、重命名、停用、删除、恢复说明` | `新增、重命名、停用、删除写入 SQLite；系统默认标签不可物理删除` | 自定义标签必须可修改并可追溯，默认标签保持历史锚点。 | 设置、账本流水、标签历史、测试。 |
| 2026-06-28 | `S6-P2-T3` | `tags.history_policy` | `无正式历史表` | `pfi_tag_history 记录 old_value, new_value, impact_object, reason_zh, changed_at` | 标签变更必须可查，避免历史解释断裂。 | 审计、复盘、GitHub 验收。 |
| 2026-06-28 | `S6-P3-T1..S6-P3-T3` | `tags.custom_view_defaults` | `无自定义标签视图` | `订阅检查、投资追涨复盘、夜间大额复盘` | 常用标签组合需要可保存和本地 HTML 展示。 | 账本流水、报告与洞察、本地 HTML、测试。 |
| 2026-06-28 | `S7-P1-T1` | `confidence.score_weights` | `Stage 1 草案权重，缺少正式 Stage 7 合同` | `字段完整度30、金额方向10、规则命中20、商户/对手方15、关联匹配15、历史一致性10，总分100` | 置信度必须可解释、可测试，并与复核队列一致。 | 导入、分类、Interconnection、账本复核、报告。 |
| 2026-06-28 | `S7-P1-T2` | `confidence.score_standards` | `部分说明分散在文档和测试中` | `每个评分项记录中文低分/中分/高分或满分标准` | 用户需要理解为什么一条记录低置信，不能只显示技术分数。 | 账本复核、报告解释、数据质量标签。 |
| 2026-06-28 | `S7-P1-T3` | `confidence.review_threshold` | `70 分，缺少禁止 source 分层声明` | `统一 70；source_layered_thresholds_allowed=false` | 不允许按支付宝、银行、券商等来源设置不同复核线，避免口径漂移。 | 导入、分类、复核队列、测试。 |
| 2026-06-28 | `S7-P2-T1` | `consumption_model.gross_consumption_formula` | `Stage 5 双消费口径` | `生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消` | Stage 7 需要把双消费口径固化为正式公式和机器参数。 | 首页总览、消费管理、现金流、报告与洞察。 |
| 2026-06-28 | `S7-P2-T2` | `consumption_model.living_consumption_formula` | `Stage 5 排除规则` | `普通生活消费 - 退款抵消；排除投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款` | 防止投资动作污染生活消费分析。 | 消费管理、预算、报告、分类复核。 |
| 2026-06-28 | `S7-P2-T3` | `consumption_model.large_spend_threshold` | `CNY 2000 / AUD 500 草案阈值` | `CNY >= 2000 或 original AUD >= 500` | 大额消费既要支持 CNY 主口径，也要保留原币异常识别。 | 消费管理、标签、复盘、测试。 |
| 2026-06-28 | `S7-P2-T4` | `time.night_window` | `22:00-06:00；电子产品冲动候选未收口` | `22:00-06:00；电子产品冲动并入夜间/大额/计划外组合` | 减少单一品类硬编码，使用标签组合解释行为。 | 消费复盘、标签规则、报告。 |
| 2026-06-28 | `S7-P3-T1` | `investment_model.market_value_formula` | `Stage 1 参数草案` | `market_value_cny = quantity * latest_price * fx_rate_to_cny` | 投资市值必须以 CNY 主口径并可追溯原币和汇率。 | 投资管理、首页摘要、趋势图、报告。 |
| 2026-06-28 | `S7-P3-T2` | `investment_model.return_formulas` | `收益说明不完整` | `remaining_cost_cny、unrealized_pnl_cny、realized_pnl_cny、total_pnl_cny 均显式记录费用、税费、FX` | 成本和收益不能只看市价差，需要解释手续费、税费和汇率。 | 投资管理、报告、行为复盘、测试。 |
| 2026-06-28 | `S7-P3-T3` | `investment_model.behavior_formula_scope` | `频率、集中度等阈值分散` | `frequency, turnover, holding_period, chase, panic_sell, cash_drag, concentration` | 投资行为复盘需要统一公式范围，后续建议评分才能复用。 | 投资管理、策略实验室、建议与复盘、报告。 |
| 2026-06-28 | `S7-P4-T1` | `cashflow.windows_days` | `30/90/180 或分散草案` | `7/21/30/60/90/180/360` | 现金流预测需要短中长期窗口统一口径。 | 现金流、首页、报告、测试。 |
| 2026-06-28 | `S7-P4-T2` | `cashflow.reserve_floor_formula` | `无正式公式` | `max(user_min_reserve_cny, average_fixed_monthly_expense_cny * reserve_months)` | 储备金安全线要同时支持用户底线和固定支出倍数。 | 现金流、安全带、建议、报告。 |
| 2026-06-28 | `S7-P4-T3` | `cashflow.investment_squeeze_formula` | `无正式模型` | `investment_squeeze_cny = max(0, reserve_floor_cny - future_cash_balance_after_investment)` | 需要解释投资入金是否挤压生活现金，避免把投资计划误判为普通生活消费。 | 现金流、投资管理、报告、复盘。 |
| 2026-06-28 | `S8-P1-T1` | `runtime_refresh_policy.dependency_hash_keys` | `无正式 Stage 8 hash 清单` | `raw_data_hash, normalized_transactions_hash, ledger_events_hash, interconnection_hash, parameter_hash, category_hash, tag_hash, fx_snapshot_hash` | 每次运行必须能判断依赖是否变化。 | Runtime Diff、缓存刷新、报告生成。 |
| 2026-06-28 | `S8-P1-T2` | `runtime_refresh_policy.no_diff_behavior` | `无正式 no-diff 行为` | `不联网、不生成 Codex ticket、不触发 LLM` | 防止无变化运行浪费 token、联网或制造复审任务。 | 运行刷新、复核队列、测试。 |
| 2026-06-28 | `S8-P1-T3` | `runtime_refresh_policy.ordinary_diff_behavior` | `diff 影响范围未收紧` | `只生成本地 diff report，只重算受影响指标` | 防止小 diff 导致全局重算。 | 指标计算、报告、缓存。 |
| 2026-06-28 | `S8-P2-T1..S8-P2-T3` | `impacted_metrics_policy` | `未区分 P0/P1/P2` | `P0 核心指标、P1 分析指标、P2 展示指标分离` | 防止展示变化或标签变化误报为财务核心变化。 | 首页、消费、投资、现金流、报告、参数中心。 |
| 2026-06-28 | `S8-P2-T4` | `impacted_metrics_policy.tag_display_name_not_impacted` | `无` | `净资产、投资收益、现金流窗口` | 仅标签显示名变化不应改变核心金额或现金流口径。 | 标签系统、Runtime Diff、测试。 |
| 2026-06-28 | `S8-P3-T1..S8-P3-T3` | `llm_agent_review_triggers` | `无正式触发规则` | `业务语义变化、公式逻辑变化、分类冲突、标签冲突、跨板块不一致、测试无法解释才生成本地票据` | 普通本地重算不得触发 LLM；重要冲突需要可执行中文复核票据。 | `PFI/review_queue/`、开发记录、测试复核。 |
| 2026-06-28 | `S9-P1-T1` | `visualization_uiux.parameter_center_domains` | `无正式 Stage 9 参数中心域` | `货币、汇率、分类、标签、阈值、公式、置信度、现金流窗口` | Stage 9 要求用户可以人工检查核心参数域。 | 参数中心、本地 HTML、合同测试。 |
| 2026-06-28 | `S9-P1-T2` | `visualization_uiux.required_parameter_fields` | `无` | `中文名、当前值、作用、影响范围、是否可修改` | 避免只显示代码变量名，保证中文可读。 | 参数中心、三基文件、HTML 审查页。 |
| 2026-06-28 | `S9-P1-T3` | `visualization_uiux.parameter_impact_preview_fields` | `无` | `记录数、标签数、建议数、图表数` | 修改参数前必须预估影响范围。 | 参数中心、运行复核、报告预估。 |
| 2026-06-28 | `S9-P2-T1` | `visualization_uiux.interconnection_map` | `Stage 4/8 只有逻辑和依赖图` | `source -> raw -> normalized -> group -> event -> ledger -> metrics -> UI` | Stage 9 要求 Mermaid graph 而不是纯文字说明。 | `docs/pfi_v022/INTERCONNECTION_MAP.md`、Metric Dependency Graph。 |
| 2026-06-28 | `S9-P2-T2` | `visualization_uiux.local_html_path` | `无 Stage 9 HTML` | `PFI/web/interconnection-map.html` | 提供本地可打开、可点击追踪的审查页。 | 浏览器验收、GitHub 交付检查。 |
| 2026-06-28 | `S9-P2-T3` | `visualization_uiux.data_status_fields` | `无统一可视化数据状态字段` | `数据来源覆盖率、最近更新时间、参数版本、公式版本、汇率快照 ID、ledger_hash、interconnection_hash、是否存在未匹配记录、是否存在低置信记录、是否存在缓存、是否需要重算、UI 指标是否与报告一致` | 每个图表必须证明数据来源和新鲜度。 | 首页总览、图表、报告一致性、测试。 |
| 2026-06-28 | `S9-P3-T1..S9-P3-T4` | `visualization_uiux.cashflow_visualizations` | `Stage 7 锁定公式，无 Stage 9 本地可视化` | `现金流阶梯图、现金流瀑布图、储备金安全带、投资入金挤压图` | 现金流需要可视化呈现 7/21/30/60/90/180/360 和投资入金挤压。 | 现金流可视化、首页、报告预检。 |
| 2026-06-28 | `S9-P4-T1..S9-P4-T3` | `visualization_uiux.metric_drilldown_debugger` | `无 Stage 9 drilldown 合同` | `本月消费、投资资产、现金流窗口的纳入、排除、调整、公式、参数、质量状态` | 首页核心数字必须可追溯，不只显示结果。 | 首页总览、Metric Drilldown Debugger、报告一致性。 |
| 2026-06-28 | `S10-P1-T1` | `report_advice_review.monthly_report_required_consumption_metrics` | `Stage 5/7 已有双消费公式，但月报必填项未锁定` | `消费总流出、生活消费` | 月报必须同时解释现金流出压力和生活支出，避免只看一个消费数字。 | 月报、报告与洞察、首页摘要、消费管理。 |
| 2026-06-28 | `S10-P1-T2` | `report_advice_review.investment_report_required_sections` | `投资报告可能偏收益展示` | `收益、成本、费用、汇率、交易频率、风格、现金拖累` | 投资复盘不能只看收益，必须解释成本和行为。 | 投资报告、投资管理、策略实验室复盘。 |
| 2026-06-28 | `S10-P1-T3` | `report_advice_review.data_quality_report_interconnection_metrics` | `数据质量报告未强制关联 Interconnection 和 Runtime Diff 指标` | `未匹配转账、重复候选、低置信、标签变更、参数变更、hash diff` | 数据质量报告必须能解释跨来源关联、重复候选和运行差异。 | 数据质量报告、账本复核、Runtime Diff、Interconnection。 |
| 2026-06-28 | `S10-P2-T1` | `report_advice_review.recommendation_label` | `推荐` | `行动建议与复盘` | 避免用户把推荐误解为买卖指令或自动投资建议。 | 建议与复盘、报告、首页 Top N。 |
| 2026-06-28 | `S10-P2-T1` | `report_advice_review.automatic_investment_advice_allowed` | `未单独参数化` | `false` | 行动建议只生成复盘任务，不生成自动投资、付款或券商提交。 | 建议与复盘、投资报告、风控合同。 |
| 2026-06-28 | `S10-P2-T2` | `report_advice_review.scoring_weights` | `Stage 5 建议有优先级但没有正式评分权重` | `财务影响25、风险降低20、紧急程度15、置信度15、可逆性10、执行成本反比10、学习价值5` | 建议排序必须有可解释依据，执行难度以执行成本反比分表达。 | 建议排序、报告解释、复盘优先级。 |
| 2026-06-28 | `S10-P2-T3` | `report_advice_review.lifecycle_statuses` | `Stage 5 状态草案不完整` | `pending、accepted、rejected、snoozed、reviewed、effect_measured` | 建议必须能从待处理进入用户决策、复核和效果复盘。 | 建议生命周期、效果复盘、报告。 |
| 2026-06-28 | `S10-P2-T3` | `report_advice_review.required_recommendation_fields` | `无正式必备字段清单` | `证据来源、相关交易、相关参数、相关公式、预期影响金额 CNY、置信度、是否需要人工复核、用户决策状态、效果复盘状态` | 每条建议必须可追溯、可复核、可衡量效果。 | 建议与复盘、报告、审计。 |
| 2026-06-28 | `S11-P1-T1..S11-P1-T4` | `test_validation.financial_logic_case_ids` | `无正式 Stage 11 金融逻辑测试门` | `cba_to_moomoo_investment_deposit、alipay_fund_purchase、refund_offsets_original_consumption、credit_card_repayment_no_double_count` | 锁定投资入金、基金申购、退款、信用卡还款四个停止条件测试。 | 消费总流出、生活消费、投资现金、投资持仓、退款、信用卡还款。 |
| 2026-06-28 | `S11-P2-T1..S11-P2-T2` | `test_validation.cross_surface_required_equalities` | `无正式跨板块相等关系参数` | `首页消费总流出 = 消费页消费总流出 = 月报消费总流出；首页投资资产 = 投资页投资资产 = 投资报告投资资产` | 防止首页、业务页和报告使用不同事实层或指标口径。 | 首页总览、消费管理、投资管理、报告与洞察。 |
| 2026-06-28 | `S11-P2-T3` | `test_validation.cashflow_traceability_required` | `无正式现金流追溯参数` | `true` | 现金流预测必须能解释到账本事件和计划事件。 | 现金流、账本事件、计划事件、报告。 |
| 2026-06-28 | `S11-P3-T1` | `test_validation.visualization_required_trace_fields` | `Stage 9 有数据状态字段，但没有 Stage 11 测试门必填字段` | `metric_id、formula_id、parameter_hash、data_hash` | 图表数字必须可追溯来源、公式、参数和数据 hash。 | 账户图表、投资图表、消费图表、现金流图表。 |
| 2026-06-28 | `S11-P3-T2` | `test_validation.visualization_freshness_statuses` | `无正式图表新鲜度测试状态` | `needs_update、updated` | 数据变化后受影响图表不得继续显示旧数据。 | Runtime Diff、图表刷新、报告一致性。 |
| 2026-06-28 | `S11-P3-T3` | `test_validation.performance_record_count` | `无正式 Stage 11 大量模拟记录数量` | `12000` | 性能测试需要证明大量模拟记录下不明显卡死，并显示 compute time/cache status。 | 可视化性能、缓存状态、用户验收。 |
| 2026-06-28 | `S12-P1-T1..S12-P1-T3` | `delivery.tri_base_required_terms` | `无正式 Stage 12 三基交付参数` | `参数中心、标签系统、Interconnection 可视化、双消费口径、现金流图表、diff ticket、公式、阈值、评分、分类、可视化规则` | 三基文件必须同步本次所有参数、公式、阈值、评分、分类、标签和可视化规则。 | 模型参数文件、功能清单、开发记录。 |
| 2026-06-28 | `S12-P2-T1` | `delivery.review_html_path` | `无 Stage 12 UI/UX 审查 HTML` | `PFI/web/pfi_v022_logic_review.html` | 交付本地中文、可打开、可点击的审查页，覆盖参数、分类、标签、图表、diff、Interconnection。 | 本地浏览器验收、用户人工复核。 |
| 2026-06-28 | `S12-P2-T2` | `delivery.roadmap_structure` | `Roadmap 可退回 milestone 表达` | `Stage -> Phase -> Task` | 防止最终交付物丢失 Phase/Task 追踪。 | Roadmap、验证报告、GitHub 验收。 |
| 2026-06-28 | `S12-P2-T3` | `delivery.final_summary_path` | `无最终中文摘要路径` | `PFI/reports/pfi_v022_summary.md` | 最终摘要必须说明做了什么、怎么验收、哪些未做、哪些需要用户人工复核。 | 用户验收、Stage 13 准备。 |
| 2026-06-28 | `S12-P2-T3` | `delivery.six_agent_review_rounds` | `无正式交付前自检轮数` | `2` | 交付前必须保留 2 轮 × 6 Agent 自检证据。 | 自检报告、风险说明、交付门。 |
| 2026-06-28 | `S12-P2-T3` | `delivery.six_agent_blocking_issue_count` | `无阻塞项计数参数` | `0` | 存在阻塞项时不得继续交付。 | 2 轮 × 6 Agent 自检、最终摘要。 |
| 2026-06-28 | `S13-P1-T1` | `post_review.trigger_condition` | `Stage 13 未执行` | `交付前人工指定` | 本轮 pursuing goal 明确触发 Stage 13，允许生成本地 Codex Review Ticket。 | 后置复核、最终完成审计。 |
| 2026-06-28 | `S13-P1-T1` | `post_review.review_ticket_path` | `无 Stage 13 ticket` | `PFI/review_queue/codex_review_stage13_owner_specified_20260628.md` | 生成本地 Codex Review Ticket，记录触发条件和复核范围。 | 复核队列、开发记录。 |
| 2026-06-28 | `S13-P1-T2` | `post_review.scope_files` | `无受限复核范围参数` | `9 个 PFI scope files` | 仅对异常区域进行复核，禁止全仓无差别扫描。 | 上下文成本、误改风险、测试。 |
| 2026-06-28 | `S13-P1-T2` | `post_review.full_repo_scan_allowed` | `未参数化` | `false` | 禁止全仓无差别扫描。 | Stage 13 后置复核边界。 |
| 2026-06-28 | `S13-P1-T2` | `post_review.network_allowed` | `未参数化` | `false` | 后置复核不联网。 | 隐私、安全、可重复验证。 |
| 2026-06-28 | `S13-P1-T3` | `post_review.blocking_issue_count` | `无阻塞项计数` | `0` | 阻塞项为 0 才允许 goal closeout。 | 最终验收、开发记录。 |
| 2026-06-28 | `Stage13-Downloads` | `post_review.downloads_cleanup_archive` | `Downloads 保留 PFI 预同步临时目录` | `PFI/docs/pfi_v022/downloads_cleanup/PFI_V022_PRE_CANONICAL_SYNC_ARCHIVE_20260628.tar.gz` | 清理前归档，减少 Downloads 污染并保留 GitHub 证据。 | Downloads 清理、GitHub 备份。 |
| 2026-06-28 | `Stage13-Downloads` | `post_review.downloads_cleanup_candidates` | `无清理白名单` | `6 个 PFI_V022_STAGE*_PRE_CANONICAL_SYNC_* 目录` | 只清理 PFI 临时目录，不触碰 PFI.app、taskpack、roadmap、zip、md。 | 本机清理、用户源文件保护。 |
| 2026-06-28 | `REVIEW-S2` | `currency.base_currency.impact_surfaces` | `首页总览、投资管理、消费管理、报告与洞察` | `首页总览、投资管理、消费管理、现金流、报告与洞察` | Stage 2 验收明确要求现金流也以 CNY 为主显示，复审发现参数影响面漏项。 | 首页总览、投资管理、消费管理、现金流、报告与洞察、复审测试。 |
| 2026-06-28 | `REVIEW-S2` | `ledger_amount_fields.field_labels_zh` | `无` | `original_amount=原始金额, original_currency=原始币种, amount_cny=CNY金额, fx_snapshot_id=汇率快照ID` | 保留机器字段的同时提供中文验收字段映射，避免用户只看到英文 key。 | 账本流水、汇率追溯、三基文件、Stage 2 复审测试。 |
| 2026-06-28 | `REVIEW-S3` | `account_roles.role_registry` | `main_wallet, consumption_account, investment_funding_source, income_account, investment_account, asset_custody, liability_account` | `新增 savings_account, external_counterparty；income_account 中文标签统一为收入接收账户` | taskpack 默认角色包含储蓄账户和外部对手方，复审发现 Stage 3 枚举漏项。 | 数据源与上传、账户与资产、账本流水、Stage 3 复审测试。 |
| 2026-06-28 | `REVIEW-S3` | `data_sources.other_source_template.account_roles_allowed` | `main_wallet, consumption_account, income_account, investment_funding_source` | `追加 savings_account, external_counterparty` | 未来新增 source 应能通过 profile 表达储蓄账户和外部对手方，不应要求改核心代码。 | source profile、other_source_template、自定义 source 扩展、Stage 3 复审测试。 |

## 记录规则

每次后续 Stage 修改参数时，必须新增一行，字段如下：

- `时间`：本地日期。
- `Stage/Phase/Task`：例如 `S1-P1-T2`。
- `字段`：参数 key、公式名或规则名。
- `旧值`：变更前的值；首次新增写 `无`。
- `新值`：变更后的值。
- `原因`：中文业务解释。
- `影响范围`：直接影响的页面、报告、测试、指标或数据表。

禁止只改代码或 UI 而不记录参数变更。
