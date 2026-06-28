# PFI v0.2.2 Stage 1 Parameter Governance

生成时间：2026-06-28 Australia/Sydney

## 结论

Stage 1 已完成模型参数文件重构。PFI 现在有一个中文可读参数总目录、一个机器可读参数文件和一组参数一致性测试。本轮只做参数治理，不修改 v0.2.1 HTML Web Shell，不实现 Stage 2 汇率快照读取，不生成 Stage 9/12 的 HTML 逻辑审查页。

## 任务完成表

| Task ID | 任务 | 交付物 | 验收结论 |
| --- | --- | --- | --- |
| `S1-P1-T1` | 重构 `模型参数文件.md` 目录 | 中文参数目录 | 已覆盖货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化、测试。 |
| `S1-P1-T2` | 新增机器可读参数文件 | `PFI/config/pfi_parameters.yaml` | 已创建。文件使用 JSON-compatible YAML，字段含中文 label / description，含义可在 Markdown 查到。 |
| `S1-P1-T3` | 新增参数一致性测试 | `PFI/tests/test_pfi_parameters_consistency.py` | 已创建。覆盖 Markdown、YAML、前端合同、HTML 中的 CNY、CNY/AUD、4.70、06:00、70 分、CNY 2000、AUD 500 等核心参数。 |
| `S1-P2-T1` | 所有公式增加中文解释 | `PFI/模型参数文件.md` | 已覆盖金额折算、消费总流出、生活消费、置信度、未来现金余额、投资市值、行动建议评分。 |
| `S1-P2-T2` | 所有阈值增加中文解释 | 阈值说明表 | 每个核心阈值已记录当前值、存在原因、影响页面和是否允许用户修改。 |
| `S1-P2-T3` | 公式变量建立中文别名 | 变量字典 | 已建立 `gross_consumption_cny = 消费总流出金额`、`living_consumption_cny = 生活消费金额`、`future_cash_balance = 未来现金余额` 等别名。 |

## 参数文件命名决策

| 项目 | 决策 |
| --- | --- |
| 参数草案提到的文件 | `PFI/config/pfi_v022_parameters.yaml` |
| Stage 1 canonical 文件 | `PFI/config/pfi_parameters.yaml` |
| 原因 | 新版 Stage -> Phase -> Task roadmap 与 Stage 0 文件定位均指定 `pfi_parameters.yaml`；只保留一个机器可读参数源，避免两个 YAML 文件漂移。 |

## 核心一致性范围

| 参数 | Canonical 值 | 一致性检查 |
| --- | --- | --- |
| 主货币 | `CNY` | YAML、Markdown、v0.2.1 前端合同。 |
| 当前前端汇率徽标 | `CNY/AUD=4.70（YYYY/MM/DD HH:MM）` | YAML、Markdown、`PFI/web/index.html`、v0.2.1 前端合同。 |
| 汇率有效时间 | `06:00` | YAML、Markdown、`PFI/web/index.html`、v0.2.1 前端合同。 |
| 普通运行默认联网抓汇率 | `false` | YAML、Markdown。 |
| 低置信复核阈值 | `70 分` | YAML、Markdown。 |
| 大额消费阈值 | `CNY 2000` 或 `AUD 500` | YAML、Markdown。 |
| 夜间窗口 | `22:00-06:00` | YAML、Markdown。 |
| 现金流窗口 | `7/21/30/60/90/180/360` | YAML、Markdown。 |
| 集中度阈值 | 观察 `35%`，高风险 `50%` | YAML、Markdown。 |

## 非目标

- 不修改 `PFI/web/index.html`。
- 不修改 `PFI/web/app/shell.js`。
- 不新增 `PFI/web/pfi_v022_logic_review.html`。
- 不提前实现 Stage 2 的汇率快照读取。
- 不新增标签数据库 schema。
- 不做真实交易、自动投资、支付、券商提交或外部账户写入。

## Stage 1 验收结论

| 验收项 | 状态 |
| --- | --- |
| 中文参数总目录完整 | 通过 |
| 机器可读参数文件存在 | 通过 |
| Markdown/YAML/前端核心参数一致性测试存在 | 通过 |
| 公式中文解释完整 | 通过 |
| 阈值中文解释完整 | 通过 |
| 变量中文别名存在 | 通过 |
| v0.2.1 前端显示未被 Stage 1 修改 | 通过 |

Stage 1 可以进入用户检查和后续 Stage 2 准备。
