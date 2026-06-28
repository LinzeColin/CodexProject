# PFI v0.2.2 Stage 0 Baseline Report

生成时间：2026-06-28 Australia/Sydney

## 结论

PFI v0.2.2 本轮定位为数据库治理和 E2E 逻辑优化，不是 v0.2.1 前端重做。Stage 0 已按新版 Stage -> Phase -> Task roadmap 补做，任务 ID 为 `S0-P1-T1`、`S0-P1-T2`、`S0-P1-T3`、`S0-P2-T1`、`S0-P2-T2`。本轮已定位当前参数、公式、阈值、分类、数据源、账户角色、测试框架和 Stage 6 E2E 产物，并标记与 v0.2.2 要求冲突的部分。

本轮不修改 `PFI/web/index.html`。  
本轮不修改 `PFI/web/app/shell.js`。  
本轮不新增 `PFI/web/pfi_v022_logic_review.html`。  
`PFI_v0.2.2_UIUX_Logic_Review_Template.html` 只作为后续逻辑审查页的信息结构参考。

## Stage 0 补做任务表

| Task ID | 任务 | 交付物 | 当前结论 |
| --- | --- | --- | --- |
| `S0-P1-T1` | 在开发记录中新增任务条目 `PFI v0.2.2 E2E 逻辑优化` | `PFI/开发记录.md` | 已补做，任务名、目标、范围、非目标为中文。 |
| `S0-P1-T2` | 定位三基文件与本次会修改的核心文件 | 文件清单 | 已补做，覆盖三基、参数 YAML 目标、前端 HTML、测试文件。 |
| `S0-P1-T3` | 明确本次不做的内容 | 非目标清单 | 已补做，明确不做真实交易、自动投资、隐私私有化重构、每次运行联网抓汇率。 |
| `S0-P2-T1` | 新增参数版本号 | `PFI/模型参数文件.md` metadata | 已补做，包含 `task_name=PFI v0.2.2 E2E 逻辑优化` 和 `parameter_version=v0.2.2`。 |
| `S0-P2-T2` | 新增参数变更记录文件 | `PFI/config/parameter_changelog.md` | 已补做，后续参数变化需记录字段、旧值、新值、原因、影响范围。 |

## Stage 0 文件定位清单

| 文件 | Stage 0 状态 |
| --- | --- |
| `PFI/模型参数文件.md` | 已更新 metadata 和 v0.2.2 Stage 0 参数记录。 |
| `PFI/功能清单.md` | 已记录 v0.2.2 Stage 0 当前能力和不改前端范围。 |
| `PFI/开发记录.md` | 已新增 Stage 0 任务章节。 |
| `PFI/config/pfi_parameters.yaml` | Stage 1 目标文件，Stage 0 只定位，不创建。 |
| `PFI/config/parameter_changelog.md` | Stage 0 已创建。 |
| `PFI/web/index.html` | v0.2.1 前端入口，Stage 0 不修改。 |
| `PFI/web/app/shell.js` | v0.2.1 前端交互入口，Stage 0 不修改。 |
| `PFI/tests/test_pfi_parameters_consistency.py` | Stage 1 目标测试，Stage 0 只定位，不创建。 |
| `PFI/tests/test_v022_stage0_database_governance.py` | Stage 0 已创建。 |

## 已读取的当前文件

| 类型 | 文件 |
| --- | --- |
| 三基文件 | `PFI/模型参数文件.md`, `PFI/功能清单.md`, `PFI/开发记录.md` |
| Stage 6 产物 | `PFI/src/pfi_v02/stage6_e2e_stabilization.py`, `PFI/tests/test_stage6_e2e_stabilization.py`, `PFI/docs/pfi_v02/STAGE6_E2E_STABILIZATION.md` |
| 前端入口 | `PFI/web/index.html`, `PFI/web/app/shell.js` |
| 数据源 | `PFI/src/pfi_v02/stage2_registry.py`, `PFI/src/pfi_v02/stage2_import.py` |
| 分析模型 | `PFI/src/pfi_v02/stage3_read_mvp.py`, `PFI/src/pfi_v02/stage4_analysis_mvp.py`, `PFI/src/pfi_v02/stage5_advice_report_alpha.py` |
| v0.2.1 收口 | `PFI/docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md`, `PFI/docs/pfi_v02/STAGE_V021_FINAL_ACCEPTANCE_AUDIT.md` |

## 数据源现状

当前 Stage 2 registry 包含 8 类数据源：

| source_id | 中文名称 | 当前口径 |
| --- | --- | --- |
| `alipay_daily` | 支付宝日常账单 | 消费、转账、收入、退款、投资候选；CSV/ZIP/watch folder。 |
| `alipay_fund` | 支付宝基金 | 投资、基金、持仓快照、估值；不假设 CSV。 |
| `moomoo_au` | Moomoo AU | 投资、券商、持仓、订单、成交；只读，不要交易密码。 |
| `cn_broker` | 中国大陆券商 | 投资、券商、A 股持仓/成交；插件/profile 方式。 |
| `abc_bullion` | ABC Bullion | 贵金属投资、持仓快照、估值；不依赖 CSV。 |
| `cba_bank` | CBA 银行 | 银行、现金流、消费、对账；CSV/watch folder。 |
| `wechat_pay` | 微信 | 消费、转账、退款、红包；CSV/XLS/XLSX/ZIP/watch folder。 |
| `other_connector` | 其它平台扩展 | profile/plugin 扩展。 |

Stage 3 账户视图当前有 9 个账户样本，账户类别包括 `daily`、`investment`、`asset`、`cash`、`liability`。v0.2.2 后续不能继续按 source 写死角色，必须迁移到可重叠、带生效日期的 account role schema。

## 当前参数与硬编码阈值

| 参数 / 阈值 | 当前值 | 位置 / 说明 | v0.2.2 处理 |
| --- | ---: | --- | --- |
| CNY -> AUD fixture | `0.21` | `STAGE3_FX_TO_AUD` | 需要改为 CNY 主口径和 AUD/CNY 有效日快照。 |
| USD -> AUD fixture | `1.52` | `STAGE3_FX_TO_AUD` | 后续保留原币辅助展示，核心指标转 CNY。 |
| HKD -> AUD fixture | `0.195` | `STAGE3_FX_TO_AUD` | 同上。 |
| 默认现金事件复核金额 | `1000` | `classification_rules.py` | 应进入参数 YAML。 |
| 低置信复核阈值 | `0.70` | `stage4_analysis_mvp.py` | v0.2.2 草案保留 70 分，但需统一评分公式。 |
| 大额消费阈值 | `500 AUD` | `build_consumption_anomalies()` | v0.2.2 要求 `2000 CNY 或 500 AUD`。 |
| 当前夜间窗口 | `23:00-05:00` | `build_consumption_anomalies()` | v0.2.2 要求 `22:00-06:00`。 |
| 电子产品冲动阈值 | `300 AUD + 夜间` | `build_consumption_anomalies()` | v0.2.2 要求删除独立规则，并入夜间/大额标签。 |
| 月预算 | `3600 AUD` | `build_consumption_summary()` | 需参数化并转 CNY 主口径。 |
| 月收入 | `7200 AUD` | `build_cashflow_forecast()` | 需参数化并转 CNY 主口径。 |
| 生活 reserve | `5000 AUD` | `build_cashflow_forecast()` | 需参数化并转 CNY 主口径。 |
| 集中度观察阈值 | `35%` | `build_investment_risk()` | v0.2.2 草案要求观察 35%、高风险 50%。 |
| 追涨阈值 | `3%` | `build_investment_behavior_review()` | 应进入参数 YAML。 |
| 杀跌阈值 | `-5%` | `build_investment_behavior_review()` | 应进入参数 YAML。 |
| 短持阈值 | `3 天` | `build_investment_behavior_review()` | 应进入参数 YAML。 |
| Stage 5 Top N | `3` | `build_stage5_delivery_model()` | 应进入参数 YAML。 |
| 上传文件上限 | `50 MB` | v0.2.1 Stage 5 参数 | 前端预检参数，非数据库治理核心。 |
| 导入待复核估算 | `4%` | v0.2.1 Stage 5 参数 | 前端估算，真实逻辑后续由置信度计算。 |
| 点击反馈延迟 | `180 ms` | v0.2.1 Stage 7 参数 | UI 参数，Stage 0 不动。 |

## 当前计算口径

### 消费

当前 Stage 4 的 `build_consumption_summary()` 先过滤 `_consumption_records()`，即排除 `is_transfer` 和 `is_investment`。当前输出：

- `month_spend_aud = 3542.18`
- `monthly_budget_aud = 3600.00`
- `budget_remaining_aud = 57.82`
- `fixed_spend_aud = 2377.99`
- `flexible_spend_aud = 1164.19`
- `excluded_transfer_aud = 5000.00`
- `excluded_investment_aud = 168.00`

冲突：v0.2.2 要求同时保留 `消费总流出金额` 和 `生活消费金额`。投资入金、基金申购、黄金申购和投资买入应进入消费总流出，但不进入生活消费。

### 投资

当前 Stage 4 投资模型包含：

- 投资市值、成本、未实现盈亏。
- 收益归因：market、active_decision、fees、fx、cash_drag。
- 风险：集中度、回撤、币种暴露、流动性。
- 行为复盘：追涨、杀跌、短持、频繁交易。

冲突：当前投资金额和收益派生以 AUD fixture 为主，且投资入金/基金申购没有被正式映射到消费总流出。

### 现金流

当前现金流窗口为 `30/90/180` 天。  
v0.2.2 要求现金流窗口为 `7/21/30/60/90/180/360` 天。

当前公式：

```text
可投资现金 = max(0, life_cash + projected_income - projected_spend - reserve_floor)
```

冲突：公式存在，但参数、CNY 主口径、固定/弹性支出、还款、计划投资入金、计划投资回流尚未进入统一参数治理。

### 建议

当前 Stage 5 生成 8 条建议，Top N 默认为 3。建议带 evidence、expected_effect、tradeoff、suggested_action、owner_decision、status 和 priority。

冲突：行动建议评分公式尚未按 v0.2.2 草案统一为“财务影响 25% + 风险降低 20% + 紧急程度 15% + 置信度 15% + 可逆性 10% + 执行成本反比 10% + 学习价值 5%”。

## 分类与标签现状

当前存在 Stage 1 分类规则和 Stage 4 行为标签，但没有：

- 12 大类 / 每类最多 5 个中类 / 中类总数最多 50 的正式 taxonomy。
- 分类与标签分离的数据结构。
- 默认标签 registry。
- 用户自定义标签新增、重命名、禁用、删除。
- 标签 assignment / rule / changelog 的 SQLite 持久化。

这不是 Stage 0 阻塞，但必须作为 Stage 6 的核心交付。

## Interconnection 现状

当前已具备：

- `dedupe_key` 用于转账或信用卡还款去重。
- Stage 6 ledger loop 覆盖转账、投资买入、消费、退款、费用、估值、基金赎回、贵金属买入、信用卡还款。
- Stage 6 有 20 个总验收 gate，当前全部 PASS。

当前缺口：

- 没有 `interconnection_group_id`。
- 没有 `economic_event_id`。
- 没有 event flags：`affects_total_outflow_consumption`、`affects_living_consumption`、`affects_investment`、`affects_net_worth`、`affects_cashflow`。
- 没有 Interconnection Matrix 和 Metric Dependency Graph。
- 没有 no-double-count 测试。

## 与 v0.2.2 要求冲突清单

| ID | 主题 | 当前状态 | v0.2.2 要求 | 后续 Stage |
| --- | --- | --- | --- | --- |
| `V022-S0-CONFLICT-001` | CNY / 汇率 | Stage 3/4/5 多数指标按 AUD fixture 派生；v0.2.1 顶栏为 CNY/AUD。 | CNY 主口径，AUD/CNY 格式，06:00 有效日。 | M1/M2 |
| `V022-S0-CONFLICT-002` | 消费口径 | 只有 `affects_consumption`，生活消费排除 transfer/investment。 | 双口径：消费总流出金额 + 生活消费金额。 | M1/M3/M5 |
| `V022-S0-CONFLICT-003` | Interconnection | 有 dedupe 和 ledger loop，无 economic_event_id。 | 建立 Interconnection Group 和 Economic Event。 | M3 |
| `V022-S0-CONFLICT-004` | 现金流窗口 | 只有 30/90/180。 | 7/21/30/60/90/180/360。 | M5 |
| `V022-S0-CONFLICT-005` | 分类与标签 | 有分类和行为标签，无正式 taxonomy 和标签持久化。 | 12 大类 / 50 中类，标签持久化。 | M4 |
| `V022-S0-CONFLICT-006` | Runtime Diff | 有 Stage 6 gate，无 dependency hash 和 Review Ticket。 | 无 diff 不联网不触发 agent；重要 diff 生成中文 ticket。 | M6 |

## Stage 6 基础保护

Stage 0 不改变 Stage 6 代码或前端显示。当前 Stage 6 产物仍作为 v0.2.2 的可回归基线：

- `build_stage6_e2e_stabilization_model()`
- `tests/test_stage6_e2e_stabilization.py`
- 20 个总验收 gate。
- v0.2.1 Stage 0-8 合同测试。

后续 v0.2.2 每个 Stage 应在自身测试之外回归 Stage 6 或完整 PFI 单测，避免破坏已验收基础。

## Agent 自检

### Agent 1：金融逻辑审查

状态：通过。

结论：已识别当前“投资事件不计生活消费”的逻辑与 v0.2.2 “投资入金/基金申购计入消费总流出”的新要求之间的差异。后续必须引入双消费口径，不能把生活消费和总流出混成一个指标。

### Agent 3：参数、公式、阈值审查

状态：通过。

结论：已列出散落在代码、Markdown、Web fixture 和测试中的关键阈值。后续 Stage 1 必须把核心参数写入 `PFI/模型参数文件.md` 和机器可读参数 YAML，并用一致性测试防止数值漂移。

## Stage 0 验收结论

| 验收项 | 状态 |
| --- | --- |
| 已按 Stage -> Phase -> Task roadmap 补做 Stage 0 | 通过 |
| 已创建参数变更记录文件 | 通过 |
| 已新增 `task_name` 和 `parameter_version` metadata | 通过 |
| 已列出现有参数与硬编码阈值 | 通过 |
| 已列出现有消费、投资、现金流、建议模块计算口径 | 通过 |
| 已标记与 v0.2.2 要求冲突的逻辑 | 通过 |
| 已确认不破坏 Stage 6 基础 | 通过 |
| 已明确 HTML 模板不是本轮 UI 修改要求 | 通过 |

Stage 0 可以进入用户检查和后续 Stage 1 准备。

## Stage 0 补做复核

2026-06-28 已追加独立补做验收入口：`docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`。

该文件单独复核 `S0-P1-T1`、`S0-P1-T2`、`S0-P1-T3`、`S0-P2-T1`、`S0-P2-T2`，并把 Milestone 0 的 acceptance criteria、stop condition、Agent 1 / Agent 3 自检和验证命令整理为中文可验收清单。后续 Stage 3 不应重复 Stage 0，只应从数据源、账户角色与可扩展结构继续。
