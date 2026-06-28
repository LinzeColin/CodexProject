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
| 2026-06-28 | `S5-P1-T1` | `event_types.stage5_ledger_event_type_table` | `Stage 4 event_type_policies，未单独包含估值事件` | `13 类统一账本事件，包含估值和汇率兑换` | Stage 5 要求事件类型表足以表达真实资金流、估值和汇率兑换。 | 账本流水、首页总览、消费管理、投资管理、现金流、报告与洞察、测试。 |
| 2026-06-28 | `S5-P1-T2` | `event_types.required_affects_flags` | `Stage 4 flags 已用于 Interconnection` | `Stage 5 事件类型表强制五个 flags：消费总流出、生活消费、投资、净资产、现金流` | 每种事件必须绑定影响口径，避免首页、消费页和报告解释不一致。 | 指标计算、参数中心、报告说明、合同测试。 |
| 2026-06-28 | `S5-P2-T1` | `consumption_model.gross_consumption_includes` | `Stage 4 已覆盖普通消费、投资入金、基金申购、黄金申购、投资买入、费用` | `正式锁定为生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，退款抵消` | Stage 5 要求新增消费总流出金额并进入首页、消费页和报告模板。 | 首页总览、消费管理、报告与洞察、测试。 |
| 2026-06-28 | `S5-P2-T2` | `consumption_model.living_consumption_excludes` | `Stage 4 规则已排除投资入金、基金申购、投资买入` | `排除投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款` | 保证生活消费不被投资资金流和还款污染。 | 消费管理、预算、报告、测试。 |
| 2026-06-28 | `S5-P2-T3` | `consumption_model.double_consumption_surfaces` | `无正式 Stage 5 展示面参数` | `homepage, consumption_page, report 同时展示消费总流出与生活消费` | 避免只显示一个消费数字导致误解。 | 首页总览、消费管理、报告与洞察、测试。 |
| 2026-06-28 | `S5-P3-T1..S5-P3-T4` | `consumption_categories.default_taxonomy` | `只有数量上限，无正式 12 大类 / 50 中类 taxonomy` | `12 个 L1、50 个 L2、每个 L1 有 future_merge_to / merge_candidate` | Stage 5 要求建立默认消费分类，并预留后续压缩到 10 类或更少的字段。 | 账本流水、消费管理、报告与洞察、参数中心、测试。 |

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
