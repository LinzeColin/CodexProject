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
