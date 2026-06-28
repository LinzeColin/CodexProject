# PFI v0.2.2 Roadmap Lock

版本：`v0.2.2 数据库治理 / E2E 逻辑优化`

Roadmap 形态：`Stage -> Phase -> Task`

权威任务包：`PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md`

追求目标：

```text
建立一个以 CNY 为主口径、以统一账本为事实层、以 Interconnection 为核心关联机制、以参数文件为模型治理中心、以中文可视化为人工验收入口的个人金融 E2E 逻辑系统。
```

## Stage 顺序

| Stage | 名称 | 本轮状态 | 说明 |
| --- | --- | --- | --- |
| Stage 0 | 任务锁定与文件定位 | 已补做复核 | 完成 `S0-P1-T1..S0-P2-T2`；独立复核文件为 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`。 |
| Stage 1 | 模型参数文件重构 | 本轮完成 | 中文参数总目录、机器可读 YAML、一致性测试。 |
| Stage 2 | CNY 基准与汇率规则 | 本轮完成 | CNY 主显示、原币辅助、06:00 有效汇率日、本地快照读取。 |
| Stage 3 | 数据源、账户角色与可扩展结构 | 本轮完成 | Source Profile、capabilities、`other_source_template`、账户角色重叠和生效期。 |
| Stage 4 | Economic Event 与 Interconnection 逻辑 | 本轮完成 | `economic_event_id`、`interconnection_group_id`、事件影响 flags、Interconnection Matrix、Metric Dependency Graph、no-double-count。 |
| Stage 5 | 统一账本事件、消费双口径与分类体系 | 本轮完成 | event type、双消费口径、12 大类 / 50 中类。 |
| Stage 6 | 标签系统与自定义视图 | 本轮完成 | 标签注册、赋值、规则、默认/自定义标签、变更历史、标签报告和自定义视图。 |
| Stage 7 | 模型公式、阈值与评分标准 | 本轮完成 | 置信度评分、消费、投资、现金流公式和现金流压力分。 |
| Stage 8 | 本地运行 Diff 与 Impacted Metrics | 本轮完成 | dependency hash、diff 收紧、LLM 触发规则、中文 Codex Review Ticket 模板。 |
| Stage 9 | 可视化与 UI/UX | 本轮完成 | 参数中心、Interconnection Map、Metric Dependency Graph、现金流可视化和 Metric Drilldown Debugger。 |
| Stage 10 | 报告、建议与复盘 | 本轮完成 | 双消费口径报告、投资成本行为、Interconnection 数据质量报告、行动建议评分和生命周期。 |
| Stage 11 | 测试与验证 | 本轮完成 | 金融逻辑、跨板块一致性、可视化一致性测试。 |
| Stage 12 | 文档同步与交付 | 本轮完成 | 三基、审查 HTML、Roadmap 与验证报告、最终中文摘要、2 轮 × 6 Agent 自检。 |
| Stage 13 | 后置触发型复核 | 非默认执行 | 仅在 diff/test/owner 指定触发时执行。 |

## Stage 0 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S0-P1-T1` | Phase 0.1 | `PFI/开发记录.md` 新增 `PFI v0.2.2 E2E 逻辑优化` 任务章节 | 本轮补做 |
| `S0-P1-T2` | Phase 0.1 | 文件清单，覆盖三基、参数 YAML、前端 HTML、测试文件 | 本轮补做 |
| `S0-P1-T3` | Phase 0.1 | 非目标清单：不做真实交易、自动投资、隐私私有化重构、每次运行联网抓汇率 | 本轮补做 |
| `S0-P2-T1` | Phase 0.2 | `PFI/模型参数文件.md` metadata 新增 `task_name` 和 `parameter_version` | 本轮补做 |
| `S0-P2-T2` | Phase 0.2 | `PFI/config/parameter_changelog.md` | 本轮补做 |

## Stage 0 Acceptance Criteria

- 已列出现有参数与硬编码阈值。
- 已列出现有消费、投资、现金流、建议模块的计算口径。
- 已标记哪些逻辑与 v0.2.2 要求冲突。
- 已确认不会破坏已有 v0.2 Stage 6 基础。
- 已锁定 HTML 模板只是未来逻辑审查参考，不是本轮 UI 修改要求。
- 已按 Stage -> Phase -> Task roadmap 补做 Stage 0，不再只保留 milestone 摘要。
- 已创建参数变更记录文件 `PFI/config/parameter_changelog.md`。
- 已在 `PFI/模型参数文件.md` 记录 `task_name=PFI v0.2.2 E2E 逻辑优化` 和 `parameter_version=v0.2.2`。

## Stage 0 Stop Condition

- 无法定位现有模型参数文件。
- 无法定位现有前端入口。
- 无法判断现有测试框架。
- Stage 0 改动触碰 v0.2.1 正式前端显示。

当前检查结论：以上停止条件均未触发。

独立补做验收：`docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，用于 GitHub 单独检查 Stage 0。

## Stage 0 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前本地 closeout 结果：Stage 8 目标测试 `8 passed`；Stage 0-8 v0.2.2 回归 `66 passed`；完整 PFI pytest `224 passed`；治理 `errors 0 / warnings 0`；Web shell 语法和 `git diff --check -- PFI` 通过；App 入口验收 `29 pass / 0 fail / 2 info`；8501 health `ok`；真实浏览器点击 `数据源与上传` 成功，`PFI`、`首页总览`、`数据源与上传`、`AUD/CNY` 可见，正式 UI 禁用词扫描 0 命中，console errors `0`，截图 `/tmp/pfi-v022-stage8-app-verified.png`。

当前本地 closeout 结果：Stage 7 目标测试 `7 passed`；Stage 0-7 v0.2.2 回归 `58 passed`；完整 PFI pytest `216 passed`；治理 `errors 0 / warnings 0`；Web shell 语法和 `git diff --check -- PFI` 通过；App 入口验收 `29 pass / 0 fail / 2 info`；8501 health `ok`；真实浏览器点击 `数据源与上传` 后关键入口、上传中心、导入中心和 `AUD/CNY` 均可见，正式 UI 禁用词扫描 0 命中，console errors `0`。

## Stage 8 - 本地运行 Diff 与 Impacted Metrics Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S8-P1-T1` | Phase 8.1 | run snapshot，包含原始数据、标准化交易、账本事件、interconnection、参数、分类、标签、汇率快照 hash | 本轮完成 |
| `S8-P1-T2` | Phase 8.1 | 运行策略：无 diff 不联网、不生成 Codex ticket、不触发 LLM | 本轮完成 |
| `S8-P1-T3` | Phase 8.1 | 依赖图：有 diff 时只重算受影响指标 | 本轮完成 |
| `S8-P2-T1` | Phase 8.2 | P0 核心指标影响范围 | 本轮完成 |
| `S8-P2-T2` | Phase 8.2 | P1 分析指标影响范围 | 本轮完成 |
| `S8-P2-T3` | Phase 8.2 | P2 展示指标影响范围 | 本轮完成 |
| `S8-P2-T4` | Phase 8.2 | diff report 标记不应受影响指标 | 本轮完成 |
| `S8-P3-T1` | Phase 8.3 | LLM 分析触发规则 | 本轮完成 |
| `S8-P3-T2` | Phase 8.3 | `PFI/review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md` | 本轮完成 |
| `S8-P3-T3` | Phase 8.3 | 无需 LLM 场景清单 | 本轮完成 |

## Stage 8 Acceptance Criteria

- 每次运行计算依赖 hash，至少覆盖原始数据、标准化交易、账本事件、interconnection、参数、分类、标签、汇率快照。
- 无 diff 不联网、不生成 Codex ticket、不触发 LLM。
- 有 diff 时只重算受影响指标，不全量重算所有板块。
- P0 核心指标仅包括净资产、生活现金、投资资产、消费总流出、生活消费、投资收益、现金流窗口、待复核数量、Interconnection 异常数量。
- P1 分析指标包括分类占比、标签视图、订阅、夜间、大额、商户集中度、投资风格、交易频率、费用拖累、现金拖累。
- P2 展示指标包括图表排序、趋势图、辅助说明、tooltip、参数中心展示。
- 每个 diff report 标记“不应受影响指标”；仅标签显示名变化不应改变净资产、投资收益、现金流窗口。
- 只有业务语义变化、公式逻辑变化、分类冲突、标签冲突、跨板块不一致、测试无法解释时生成本地中文 Codex Review Ticket。

## Stage 8 Stop Condition

- 无法判断数据是否变化。
- 无 diff 仍触发联网、agent、Codex ticket 或 LLM。
- 小 diff 导致全局重算。
- Impacted metrics 过宽导致误报。
- 分析指标与核心指标混在一起。
- 展示变化被误判为财务核心变化。
- 标签改名导致金额变化。
- Ticket 只有技术日志，没有中文业务解释。

当前检查结论：Stage 8 实现均为本地纯函数和本地模板，不联网、不调用外部 LLM，不提前实现 Stage 9 可视化与 UI/UX。

## Stage 8 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage8_runtime_diff.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py PFI/tests/test_v022_stage5_ledger_taxonomy.py PFI/tests/test_v022_stage6_tags_views.py PFI/tests/test_v022_stage7_formula_scoring.py PFI/tests/test_v022_stage8_runtime_diff.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前本地 closeout 结果：Stage 7 目标测试 `7 passed`；Stage 0-7 v0.2.2 回归 `58 passed`；完整 PFI pytest `216 passed`；治理 `errors 0 / warnings 0`；Web shell 语法和 `git diff --check -- PFI` 通过；App 入口验收 `29 pass / 0 fail / 2 info`；8501 health `ok`；真实浏览器点击 `数据源与上传` 后关键入口、上传中心、导入中心和 `AUD/CNY` 均可见，正式 UI 禁用词扫描 0 命中，console errors `0`，截图 `/tmp/pfi-v022-stage7-upload-verified-final.png`。

## Stage 1 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S1-P1-T1` | Phase 1.1 | `PFI/模型参数文件.md` 中文参数目录 | 本轮完成 |
| `S1-P1-T2` | Phase 1.1 | `PFI/config/pfi_parameters.yaml` | 本轮完成 |
| `S1-P1-T3` | Phase 1.1 | `PFI/tests/test_pfi_parameters_consistency.py` | 本轮完成 |
| `S1-P2-T1` | Phase 1.2 | 公式中文解释 | 本轮完成 |
| `S1-P2-T2` | Phase 1.2 | 阈值说明表 | 本轮完成 |
| `S1-P2-T3` | Phase 1.2 | 公式变量中文别名 | 本轮完成 |

## Stage 1 Acceptance Criteria

- `模型参数文件.md` 已包含货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化、测试。
- 已新增机器可读参数文件 `PFI/config/pfi_parameters.yaml`。
- `pfi_parameters.yaml` 与 Markdown 参数含义一致，字段中文说明可在 Markdown 查到。
- 已新增 `PFI/tests/test_pfi_parameters_consistency.py`。
- 测试能确认 Markdown、YAML、前端合同和 HTML 显示中的核心参数一致。
- 每个核心公式有中文名称、用途、输入、输出、计算逻辑和示例。
- 每个核心阈值有当前值、为什么存在、触发后影响哪些页面、能否用户修改。
- 公式变量有中文别名，例如 `gross_consumption_cny = 消费总流出金额`。

## Stage 1 Stop Condition

- 参数仍散落在代码和文档中且没有统一目录。
- Markdown 和 YAML 核心参数不一致。
- 核心阈值多处不一致且没有明确标记为后续阶段差异。
- 公式只有英文变量或代码名，用户无法理解。

当前检查结论：以上停止条件均未触发。

## Stage 1 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_pfi_parameters_consistency -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## Stage 2 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S2-P1-T1` | Phase 2.1 | 首页、投资、消费、现金流、报告主显示以 `CNY` 为基准 | 本轮完成 |
| `S2-P1-T2` | Phase 2.1 | 原币辅助显示，例如 `CNY 2,343.70 / 原币 AUD 500.00 / AUD/CNY=4.6874` | 本轮完成 |
| `S2-P1-T3` | Phase 2.1 | 账本金额字段：`原始金额`、`原始币种`、`CNY金额`、`汇率快照ID` | 本轮完成 |
| `S2-P2-T1` | Phase 2.2 | 06:00 Australia/Sydney 有效汇率日规则 | 本轮完成 |
| `S2-P2-T2` | Phase 2.2 | 普通本地运行只读快照，不默认联网刷新 | 本轮完成 |
| `S2-P2-T3` | Phase 2.2 | `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json` 含来源、读取时间、pair、hash | 本轮完成 |

## Stage 2 Acceptance Criteria

- 系统主口径为 `CNY`，Web Shell 首页和动态金额标签不再以 `AUD` 作为主显示。
- 原币信息保留为辅助展示，不覆盖 CNY 主口径。
- 账本金额字段可生成 `原始金额`、`原始币种`、`CNY金额`、`汇率快照ID`。
- 06:00 之前使用前一自然日快照，06:00 及之后使用当天快照。
- 普通运行不得自动访问网络；只有显式 `--allow-network` 刷新才调用外部汇率 API。
- `data/fx_snapshots/AUD_CNY/2026-06-28.json` 是真实读取快照，包含 `source_provider`、`source_url`、`fetched_at`、`pair_base`、`pair_quote`、`hash`。
- 当有效快照缺失时返回 `汇率数据待更新`，不得编造实时汇率，也不得强制刷新网络。

## Stage 2 Stop Condition

- CNY 主显示仍被 AUD 主显示覆盖。
- 原始金额、原始币种、CNY 金额或快照 ID 任一字段缺失。
- 普通运行会默认联网抓取汇率。
- 快照缺少来源、读取时间、pair 或 hash。
- 06:00 有效日边界不可测试。

当前检查结论：以上停止条件均未触发。

## Stage 2 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_fx_effective_date -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m pfi_v02.stage_v022_fx read
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## Stage 3 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S3-P1-T1` | Phase 3.1 | 通用数据源 Profile Schema，支持 `wallet/bank/broker/fund_platform/bullion_platform/payment_platform/manual_snapshot/other` | 本轮完成 |
| `S3-P1-T2` | Phase 3.1 | `capabilities` 描述数据源能力，覆盖现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账 | 本轮完成 |
| `S3-P1-T3` | Phase 3.1 | `other_source_template` | 本轮完成 |
| `S3-P2-T1` | Phase 3.2 | 账户角色 Schema，允许一个账户同时多角色 | 本轮完成 |
| `S3-P2-T2` | Phase 3.2 | `role_effective_from` / `role_effective_to` | 本轮完成 |
| `S3-P2-T3` | Phase 3.2 | 按角色和事件类型计算，不按 source 名称硬编码 | 本轮完成 |

## Stage 3 Acceptance Criteria

- source profile schema 支持 `wallet`、`bank`、`broker`、`fund_platform`、`bullion_platform`、`payment_platform`、`manual_snapshot`、`other`。
- capabilities 覆盖现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账。
- 至少提供 `other_source_template`，新增 source 不需要修改核心计算代码。
- 一个账户可同时是主钱包、消费账户、投资入金来源、收入账户。
- 账户角色支持 `role_effective_from` 和 `role_effective_to`。
- 所有计算按 role 和 event type，不按支付宝、微信、银行卡、券商等 source 名称硬编码。

## Stage 3 Stop Condition

- 新增数据源必须修改核心计算代码。
- 数据源能力写死在名称里。
- 无法添加新 source。
- 一个账户只能有一个角色。
- 角色历史无法追踪。
- 公式按 source 名称写死。

当前检查结论：以上停止条件均未触发。

## Stage 3 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage3_source_account_profiles -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date PFI.tests.test_v022_stage3_source_account_profiles -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## Stage 4 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S4-P1-T1` | Phase 4.1 | `economic_event_id`，同一真实经济事件只有一个 ID | 本轮完成 |
| `S4-P1-T2` | Phase 4.1 | `interconnection_group_id`，银行转 Moomoo、支付宝基金申购、退款、信用卡还款可形成关联组 | 本轮完成 |
| `S4-P1-T3` | Phase 4.1 | event type affects flags，写清首页、消费、投资、现金流、报告处理方式 | 本轮完成 |
| `S4-P2-T1` | Phase 4.2 | `PFI/docs/pfi_v02/INTERCONNECTION_MATRIX.md` | 本轮完成 |
| `S4-P2-T2` | Phase 4.2 | Matrix 字段：是否计入消费总流出、生活消费、投资、净资产、现金流 | 本轮完成 |
| `S4-P2-T3` | Phase 4.2 | 退款抵消、信用卡还款不重复、投资入金/基金申购双口径规则 | 本轮完成 |

## Stage 4 Acceptance Criteria

- 同一真实事件只有一个 `economic_event_id`。
- 同一 `interconnection_group_id` 不会重复计入核心金额。
- 每个 event type 有明确 affects flags。
- 首页、投资、消费、现金流、报告口径一致。
- 投资入金计入消费总流出，不计入生活消费，计入投资现金。
- 基金申购计入消费总流出，不计入生活消费，计入基金资产。
- 投资买入计入消费总流出，不计入生活消费，计入投资持仓。
- 退款抵消原消费或对应总流出。
- 信用卡还款不重复计入生活消费。
- Agent 1 复核消费、投资、现金流口径。
- Agent 2 复核 source -> transaction -> group -> economic event -> ledger -> metric 链路。

## Stage 4 Stop Condition

- 同一记录被重复计入核心金额。
- `投资入金未进入消费总流出`。
- `基金申购未进入消费总流出`。
- `投资入金错误进入生活消费`。
- 同一 `interconnection_group_id` 因重复来源记录导致核心金额重复计算。

当前检查结论：以上停止条件均未触发。

## Stage 4 Validation

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## Stage 5 - 统一账本事件、消费双口径与分类体系 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S5-P1-T1` | Phase 5.1 | 账本事件类型表，覆盖消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换 | 本轮完成 |
| `S5-P1-T2` | Phase 5.1 | event type policy，每个事件绑定消费总流出、生活消费、投资、净资产、现金流影响口径 | 本轮完成 |
| `S5-P2-T1` | Phase 5.2 | `消费总流出金额` 公式与展示模板 | 本轮完成 |
| `S5-P2-T2` | Phase 5.2 | `生活消费金额` 公式与展示模板 | 本轮完成 |
| `S5-P2-T3` | Phase 5.2 | 首页、消费页、报告双口径模板 | 本轮完成 |
| `S5-P3-T1` | Phase 5.3 | 12 个以内 L1 大类 | 本轮完成 |
| `S5-P3-T2` | Phase 5.3 | 每个 L1 最多 5 个 L2 | 本轮完成 |
| `S5-P3-T3` | Phase 5.3 | 总 L2 不超过 50 的测试 | 本轮完成 |
| `S5-P3-T4` | Phase 5.3 | 每个 L1 预留 `future_merge_to` / `merge_candidate` | 本轮完成 |

## Stage 5 Acceptance Criteria

- 统一账本事件类型表足以表达真实资金流，包含估值和汇率兑换。
- 每个 event type 都写明 `affects_total_consumption_outflow`、`affects_living_consumption`、`affects_investment`、`affects_net_worth`、`affects_cashflow`。
- `消费总流出金额` 包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，并由退款抵消。
- `生活消费金额` 只包含普通生活消费，排除投资入金、基金申购、黄金申购、投资买入、内部转账和信用卡还款。
- 首页、消费页、报告同时展示 `消费总流出` 与 `生活消费`，并解释差异。
- 分类约束为 `L1 ≤ 12`、每类 `L2 ≤ 5`、总 `L2 ≤ 50`。
- 每笔交易主分类数量为 `1`；多维分析标签留到 Stage 6。
- 每个 L1 都有 `future_merge_to` 或 `merge_candidate`，后续可压缩到 10 类或更少。

## Stage 5 Stop Condition

- 事件类型不足以表达真实资金流。
- 任一事件影响口径缺失。
- 投资入金未计入消费总流出。
- 基金申购未计入消费总流出。
- 黄金申购或投资买入未计入消费总流出。
- 投资入金、基金申购、黄金申购或投资买入错误进入生活消费。
- 首页、消费页、报告只显示一个消费数字导致误解。
- 分类超过 12 大类、任一大类超过 5 中类、或总中类超过 50。
- 后续无法合并分类。

当前检查结论：以上停止条件均未触发。Stage 6 标签持久化、自定义标签增删改、标签历史、标签筛选视图不在本轮实现。

## Stage 5 Validation

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage5_ledger_taxonomy.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py PFI/tests/test_v022_stage5_ledger_taxonomy.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前本地 closeout 结果：Stage 5 目标测试 `5 passed`；Stage 0-5 v0.2.2 回归 `45 passed`；完整 PFI pytest `203 passed`；治理 `errors 0 / warnings 0`；Web shell 语法、Streamlit compile、`git diff --check -- PFI` 通过；App 入口验收 `29 pass / 0 fail / 2 info`；浏览器 8501 console errors `0`。

## Stage 6 - 标签系统与自定义视图 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S6-P1-T1` | Phase 6.1 | `pfi_tags` 标签注册表，包含 ID、中文名、范围、类型、是否系统默认、是否可编辑、是否启用 | 本轮完成 |
| `S6-P1-T2` | Phase 6.1 | `pfi_tag_assignments` 标签赋值表，同一交易、经济事件、持仓、账户可拥有多个标签 | 本轮完成 |
| `S6-P1-T3` | Phase 6.1 | `pfi_tag_rules` 标签规则表，支持金额、时间、分类、事件类型、账户角色自动打标签 | 本轮完成 |
| `S6-P2-T1` | Phase 6.2 | 默认标签库，覆盖通用、消费、投资、数据质量、现金流、复盘 | 本轮完成 |
| `S6-P2-T2` | Phase 6.2 | 自定义标签新增、重命名、停用、删除 | 本轮完成 |
| `S6-P2-T3` | Phase 6.2 | `pfi_tag_history` 标签变更历史 | 本轮完成 |
| `S6-P3-T1` | Phase 6.3 | 标签组合筛选账本 | 本轮完成 |
| `S6-P3-T2` | Phase 6.3 | 标签驱动报告聚合 | 本轮完成 |
| `S6-P3-T3` | Phase 6.3 | `pfi_custom_views` 与 `PFI/web/pfi_v022_tag_views.html` 自定义标签视图 | 本轮完成 |

## Stage 6 Acceptance Criteria

- `pfi_tags` 或本地等价存储包含标签 ID、中文名、范围、类型、是否系统默认、是否可编辑、是否启用。
- `pfi_tag_assignments` 允许一笔交易、经济事件、持仓或账户拥有多个标签。
- `pfi_tag_rules` 支持金额、时间、分类、事件类型和账户角色自动打标签。
- 默认标签库覆盖通用、消费、投资、数据质量、现金流、复盘。
- 自定义标签可新增、重命名、停用、删除；系统默认标签不可物理删除。
- `pfi_tag_history` 记录旧值、新值、时间、影响对象和原因。
- 标签组合可筛选账本，例如夜间 + 大额 + 计划外。
- 报告可按标签聚合消费、投资、异常、复盘项。
- 本地 HTML 可展示和保存自定义标签视图，例如订阅检查、投资追涨复盘。

## Stage 6 Stop Condition

- 标签不能持久化。
- 一笔记录只能有一个标签。
- 标签只能手动添加。
- 默认标签缺失关键分析维度。
- 自定义标签无法修改。
- 标签历史不可追踪。
- 标签无法筛选账本。
- 标签不参与报告。
- 自定义视图不能保存。

当前检查结论：以上停止条件均未触发。Stage 7 现金流窗口和评分公式、Stage 8 Runtime Diff、Stage 9 参数中心不在本轮实现。

## Stage 6 Validation

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage6_tags_views.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py PFI/tests/test_v022_stage5_ledger_taxonomy.py PFI/tests/test_v022_stage6_tags_views.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前本地 closeout 结果：Stage 6 目标测试 `6 passed`；Stage 0-6 v0.2.2 回归 `51 passed`；完整 PFI pytest `209 passed`；治理 `errors 0 / warnings 0`；Web shell 语法和 `git diff --check -- PFI` 通过；App 入口验收 `29 pass / 0 fail / 2 info`；真实 8501 浏览器禁用词扫描 0 命中、console errors `0`；Stage 6 HTML 浏览器任务、表、默认标签组、自定义视图均可见，console errors `0`。

## Stage 9 - 可视化与 UI/UX Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S9-P1-T1` | Phase 9.1 | 参数中心页面/模块，覆盖货币、汇率、分类、标签、阈值、公式、置信度、现金流窗口 | 本轮完成 |
| `S9-P1-T2` | Phase 9.1 | 参数中文说明，包含中文名、当前值、作用、影响范围、是否可修改 | 本轮完成 |
| `S9-P1-T3` | Phase 9.1 | 参数变更影响预览，覆盖记录数、标签数、建议数、图表数 | 本轮完成 |
| `S9-P2-T1` | Phase 9.2 | `docs/pfi_v022/INTERCONNECTION_MAP.md` Mermaid 图 | 本轮完成 |
| `S9-P2-T2` | Phase 9.2 | `web/interconnection-map.html` 本地可点击关系图 | 本轮完成 |
| `S9-P2-T3` | Phase 9.2 | 每个图表的数据状态字段 | 本轮完成 |
| `S9-P3-T1` | Phase 9.3 | 现金流阶梯图，窗口为 `7/21/30/60/90/180/360` | 本轮完成 |
| `S9-P3-T2` | Phase 9.3 | 现金流瀑布图，含当前现金、收入、退款、固定支出、弹性支出、信用卡、投资入金、投资回流 | 本轮完成 |
| `S9-P3-T3` | Phase 9.3 | 储备金安全带，含绿色、黄色、红色 | 本轮完成 |
| `S9-P3-T4` | Phase 9.3 | 投资入金挤压图，说明生活现金和储备金影响 | 本轮完成 |
| `S9-P4-T1` | Phase 9.4 | 首页核心数字 drilldown：本月消费、投资资产、现金流窗口 | 本轮完成 |
| `S9-P4-T2` | Phase 9.4 | 纳入、排除、调整说明 | 本轮完成 |
| `S9-P4-T3` | Phase 9.4 | 置信度、匹配率、最后更新时间、计算耗时、缓存状态 | 本轮完成 |

## Stage 9 Acceptance Criteria

- 参数中心显示货币、汇率、分类、标签、阈值、公式、置信度、现金流窗口。
- 每个参数显示中文名、当前值、作用、影响范围、是否可修改。
- 参数变更影响预览显示可能影响的记录数、标签数、建议数、图表数。
- Interconnection Map 以 Mermaid 图展示 `source -> raw -> normalized -> group -> event -> ledger -> metrics -> UI`。
- `PFI/web/interconnection-map.html` 为 HTML 单文件可打开，不依赖外网。
- HTML 可点击追踪数据源、事件类型、分类、标签、公式、影响板块。
- 每个图表显示数据来源覆盖率、最近更新时间、参数版本、公式版本、汇率快照 ID、ledger_hash、interconnection_hash、是否存在未匹配记录、是否存在低置信记录、是否存在缓存、是否需要重算、UI 指标是否与报告一致。
- 现金流阶梯图展示 7/21/30/60/90/180/360 天预测余额。
- 现金流瀑布图展示当前现金、收入、退款、固定支出、弹性支出、信用卡、投资入金、投资回流。
- 储备金安全带展示绿色、黄色、红色现金安全区间。
- 投资入金挤压图显示投资入金对生活现金和储备金的影响。
- Metric Drilldown Debugger 展示来源记录、公式、参数、排除项、抵消项、纳入、排除、调整和质量状态。

## Stage 9 Stop Condition

- 用户无法人工检查参数。
- 只有代码变量名，没有中文解释。
- 参数变更无法预估影响。
- Interconnection 只有文字，没有 graph。
- HTML 图不可点击或不可追踪。
- 图表无法证明数据新鲜度。
- HTML 依赖外部 CDN、远程脚本、远程字体或网络。
- UI 只显示结果，不显示公式、参数和数据来源。
- Stage 10 报告、建议与复盘被提前实现。

当前检查结论：以上停止条件均未触发。Stage 9 交付物为本地纯 HTML、文档和合同模块；不改 v0.2.1 主 Web Shell UIUX 基线，不联网，不调用外部 LLM，不提前实现 Stage 10。

## Stage 9 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage9_visualization_uiux.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_stage9_visualization_uiux.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

浏览器验收：打开 `PFI/web/interconnection-map.html`，点击 `data-map-node` 和 `data-drilldown-metric` 后详情区必须变化；页面必须离线可读且 console errors 为 0。

当前本地 closeout 结果：Stage 9 目标测试 `8 passed`；Stage 0-9 v0.2.2 回归 `74 passed`；完整 PFI pytest `232 passed`；治理 `errors 0 / warnings 0`；Web shell 语法和 `git diff --check -- PFI` 通过；App 入口验收 `29 pass / 0 fail / 2 info`；Stage 9 HTML 浏览器验收模块缺失 `0`、状态字段渲染 `144`、console errors `0`、外部网络请求 `0`，截图 `/tmp/pfi-v022-stage9-html-verified.png`；真实 8501 PFI 入口验证 `PFI`、`首页总览`、`数据源与上传`、`AUD/CNY` 可见，Stage 9 审查页未进入主 UI，console errors `0`，截图 `/tmp/pfi-v022-stage9-app-verified.png`。

## Stage 10 - 报告、建议与复盘 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S10-P1-T1` | Phase 10.1 | 月报模板加入双消费口径：消费总流出和生活消费 | 本轮完成 |
| `S10-P1-T2` | Phase 10.1 | 投资报告加入收益、成本、费用、汇率、交易频率、风格、现金拖累 | 本轮完成 |
| `S10-P1-T3` | Phase 10.1 | 数据质量报告加入未匹配转账、重复候选、低置信、标签变更、参数变更、hash diff | 本轮完成 |
| `S10-P2-T1` | Phase 10.2 | 将“推荐”定义为行动建议与复盘，明确不是自动投资建议 | 本轮完成 |
| `S10-P2-T2` | Phase 10.2 | 建立行动建议评分公式 | 本轮完成 |
| `S10-P2-T3` | Phase 10.2 | 建立建议生命周期：`pending`、`accepted`、`rejected`、`snoozed`、`reviewed`、`effect_measured` | 本轮完成 |

## Stage 10 Acceptance Criteria

- 月报同时显示消费总流出和生活消费。
- 投资报告显示收益、成本、费用、汇率、交易频率、风格、现金拖累。
- 数据质量报告显示未匹配转账、重复候选、低置信、标签变更、参数变更、hash diff。
- “推荐”必须解释为行动建议与复盘，不得被误解成买卖指令或自动投资建议。
- 行动建议与复盘覆盖数据修复建议、消费复盘建议、投资行为复盘建议、现金流风险建议、订阅优化建议、参数调整建议。
- 行动建议评分包含财务影响、风险降低、紧急程度、置信度、可逆性、执行成本反比分、学习价值。
- 每条建议包含证据来源、相关交易、相关参数、相关公式、预期影响金额 CNY、置信度、是否需要人工复核、用户决策状态、效果复盘状态。
- 建议生命周期支持 `pending`、`accepted`、`rejected`、`snoozed`、`reviewed`、`effect_measured`。

## Stage 10 Stop Condition

- 报告只显示一个消费口径。
- 投资报告只有收益。
- 数据质量报告不含 Interconnection 关联指标。
- 推荐被误解成买卖指令。
- 建议没有排序依据。
- 建议无法复盘效果。
- Stage 11 测试与验证被提前实现。

当前检查结论：以上停止条件均未触发。Stage 10 交付物为本地合同、参数、报告口径和建议生命周期模型；不改 v0.2.1 主 Web Shell UIUX 基线，不联网，不调用外部 LLM，不提前实现 Stage 11。

## Stage 10 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage10_report_advice_review.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_stage10_report_advice_review.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前验证结果：

- Stage 10 目标测试：`7 passed`。
- Stage 0-10 v0.2.2 回归：`81 passed`。
- 完整 PFI pytest：`239 passed`。
- `node --check web/app/shell.js`：通过。
- `python3 scripts/validate_project_governance.py --project PFI`：`errors 0 / warnings 0`。
- `git diff --check -- PFI`：通过。
- macOS app acceptance lite：`29 pass / 0 fail / 2 info`。
- 真实 8501 浏览器验收：关键中文入口和 `AUD/CNY` 可见，Stage 10 审查文档未注入主 UI，console errors `0`，截图 `/tmp/pfi-v022-stage10-app-verified.png`。

## Stage 11 - 测试与验证 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S11-P1-T1` | Phase 11.1 | 投资入金计入消费总流出测试 | 本轮完成 |
| `S11-P1-T2` | Phase 11.1 | 基金申购计入消费总流出测试 | 本轮完成 |
| `S11-P1-T3` | Phase 11.1 | 退款抵消测试 | 本轮完成 |
| `S11-P1-T4` | Phase 11.1 | 信用卡还款测试 | 本轮完成 |
| `S11-P2-T1` | Phase 11.2 | 首页与消费页一致测试 | 本轮完成 |
| `S11-P2-T2` | Phase 11.2 | 首页与投资页一致测试 | 本轮完成 |
| `S11-P2-T3` | Phase 11.2 | 现金流与账本一致测试 | 本轮完成 |
| `S11-P3-T1` | Phase 11.3 | 图表数据来源测试 | 本轮完成 |
| `S11-P3-T2` | Phase 11.3 | 图表及时性测试 | 本轮完成 |
| `S11-P3-T3` | Phase 11.3 | 图表性能测试 | 本轮完成 |

## Stage 11 Acceptance Criteria

- 投资入金计入消费总流出：CBA -> Moomoo 时消费总流出增加，生活消费不增加，投资现金增加。
- 基金申购计入消费总流出：支付宝基金申购时消费总流出增加，生活消费不增加，投资持仓增加。
- 退款抵消原消费，且不影响投资收益。
- 信用卡还款不重复计入生活消费。
- 首页消费总流出 = 消费页消费总流出 = 月报消费总流出。
- 首页投资资产 = 投资页投资资产 = 投资报告投资资产。
- 现金流预测来源能追溯到账本事件和计划事件。
- 每个图表可追溯 `metric_id`、`formula_id`、`parameter_hash`、`data_hash`。
- 数据变化后受影响图表自动标记 `needs_update` 或 `updated`。
- 大量模拟记录下图表生成不明显卡死，并显示 `compute time` 和 `cache status`。

## Stage 11 Stop Condition

- 投资入金未进入消费总流出时停止。
- 基金申购被当普通生活消费时停止。
- 退款重复计入收入时停止。
- 还款造成重复消费时停止。
- 首页、消费页、月报三处金额不一致时停止。
- 首页、投资页、投资报告三处金额不一致时停止。
- 现金流无法解释时停止。
- 图表数字无来源时停止。
- 图表显示旧数据时停止。
- 无性能状态或明显卡顿时停止。
- Stage 12 文档同步与最终交付被提前实现时停止。

当前检查结论：以上停止条件均未触发。Stage 11 交付物为本地测试门、参数和验证合同；不改 v0.2.1 主 Web Shell UIUX 基线，不联网，不调用外部 LLM，不提前实现 Stage 12/13。

## Stage 11 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage11_test_validation.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_stage10_report_advice_review.py tests/test_v022_stage11_test_validation.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前运行结果：

- Stage 11 合同测试：`6 passed`。
- Stage 0-11 v0.2.2 回归：`87 passed`。
- 完整 PFI pytest：`245 passed`。
- Web shell 语法检查：`node --check web/app/shell.js` 通过。
- 项目治理：`errors: 0`，`warnings: 0`。
- `git diff --check -- PFI` 通过。
- macOS app 入口轻量验收：`29 pass / 0 fail / 2 info`，8501 健康。
- 真实 8501 浏览器验收：`PFI`、`首页总览`、`数据源与上传`、`建议与复盘`、`报告与洞察`、`AUD/CNY` 可见；点击 `报告与洞察` 有响应；禁止正式 UI 出现 `Stage 11 - 测试与验证`、`STAGE11_TEST_VALIDATION`、`自动买入`、`自动卖出`；console errors `0`；截图 `/tmp/pfi-v022-stage11-app-verified.png`。

## Stage 12 - 文档同步与交付 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S12-P1-T1` | Phase 12.1 | 更新模型参数文件，包含参数中心、公式、阈值、评分、分类、标签、可视化规则 | 本轮完成 |
| `S12-P1-T2` | Phase 12.1 | 更新功能清单，列出参数中心、标签系统、Interconnection 可视化、双消费口径、现金流图表、diff ticket | 本轮完成 |
| `S12-P1-T3` | Phase 12.1 | 更新开发记录，记录完成任务、变更文件、测试结果、未完成项、下轮建议 | 本轮完成 |
| `S12-P2-T1` | Phase 12.2 | 生成 UI/UX 审查 HTML `PFI/web/pfi_v022_logic_review.html` | 本轮完成 |
| `S12-P2-T2` | Phase 12.2 | 生成 Roadmap 与验证报告，结构为 Stage -> Phase -> Task | 本轮完成 |
| `S12-P2-T3` | Phase 12.2 | 生成最终变更摘要 `PFI/reports/pfi_v022_summary.md` | 本轮完成 |

## Stage 12 Acceptance Criteria

- 模型参数文件包含本次所有参数、公式、阈值、评分、分类、标签、可视化规则。
- 功能清单列出参数中心、标签系统、Interconnection 可视化、双消费口径、现金流图表、diff ticket。
- 开发记录记录完成任务、变更文件、测试结果、未完成项、下轮建议。
- UI/UX 审查 HTML 中文、可打开、可点击，覆盖参数、分类、标签、图表、diff、Interconnection。
- Roadmap 与验证报告采用 Stage -> Phase -> Task，不是 milestone 列表。
- 最终中文摘要说明做了什么、怎么验收、哪些未做、哪些需要用户人工复核。
- 2 轮 × 6 Agent 自检报告包含每个 Agent 的两轮结论，每个问题都有已修复、非阻塞或阻塞状态，阻塞项为 0。

## Stage 12 Stop Condition

- 参数缺失时停止。
- 功能未记录时停止。
- 无开发记录时停止。
- HTML 无法本地打开时停止。
- Roadmap 仍是 milestone 列表时停止。
- 没有中文摘要时停止。
- 第二轮没有交叉验证第一轮问题时停止。
- Agent 报告只写“通过”没有证据时停止。
- 存在阻塞项仍继续交付时停止。
- Stage 13 后置触发型复核被提前执行时停止。

当前检查结论：以上停止条件均未触发。Stage 12 交付物为三基同步、本地审查 HTML、Roadmap 与验证报告、最终摘要和 2 轮 × 6 Agent 自检；不改 v0.2.1 主 Web Shell UIUX 基线，不联网，不调用外部 LLM，不提前执行 Stage 13。

## Stage 12 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage12_delivery.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_stage10_report_advice_review.py tests/test_v022_stage11_test_validation.py tests/test_v022_stage12_delivery.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前运行结果：

- Stage 12 合同测试：`5 passed`。
- Stage 0-12 v0.2.2 回归：`92 passed`。
- 完整 PFI pytest：`250 passed`。
- Web shell 语法检查：`node --check web/app/shell.js` 通过。
- 项目治理：`errors: 0`，`warnings: 0`。
- `git diff --check -- PFI` 通过。
- macOS app 入口轻量验收：`29 pass / 0 fail / 2 info`，8501 健康。
- Stage 12 本地 HTML 浏览器验收：7 个区块可点击，缺失必填词 `0`，console errors `0`，外部请求 `0`，截图 `/tmp/pfi-v022-stage12-html-verified.png`。
- 真实 8501 浏览器验收：`PFI`、`首页总览`、`数据源与上传`、`建议与复盘`、`报告与洞察`、`AUD/CNY` 可见；点击 `报告与洞察` 有响应；禁止正式 UI 出现 `Stage 12 - 文档同步与交付`、`pfi_v022_logic_review`、`STAGE12_DELIVERY_REPORT`、`自动买入`、`自动卖出`；console errors `0`；截图 `/tmp/pfi-v022-stage12-app-verified.png`。

## Stage 7 - 模型公式、阈值与评分标准 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S7-P1-T1` | Phase 7.1 | 100 分置信度评分公式，权重为字段完整度 30、金额方向 10、规则命中 20、商户/对手方 15、关联匹配 15、历史一致性 10 | 本轮完成 |
| `S7-P1-T2` | Phase 7.1 | 每个评分项中文评分标准 | 本轮完成 |
| `S7-P1-T3` | Phase 7.1 | 统一低置信复核阈值 `70`，禁止 source 分层阈值 | 本轮完成 |
| `S7-P2-T1` | Phase 7.2 | `消费总流出金额` 公式 | 本轮完成 |
| `S7-P2-T2` | Phase 7.2 | `生活消费金额` 公式 | 本轮完成 |
| `S7-P2-T3` | Phase 7.2 | 大额消费阈值 `CNY >= 2000` 或原币 `AUD >= 500` | 本轮完成 |
| `S7-P2-T4` | Phase 7.2 | 夜间窗口 `22:00-06:00`，电子产品冲动规则并入夜间/大额逻辑 | 本轮完成 |
| `S7-P3-T1` | Phase 7.3 | `market_value_cny = quantity * latest_price * fx_rate_to_cny` | 本轮完成 |
| `S7-P3-T2` | Phase 7.3 | 成本、已实现收益、未实现收益、总收益公式 | 本轮完成 |
| `S7-P3-T3` | Phase 7.3 | 频率、换手率、持仓周期、追涨、杀跌、现金拖累、集中度行为公式 | 本轮完成 |
| `S7-P4-T1` | Phase 7.4 | 现金流窗口 `7/21/30/60/90/180/360` | 本轮完成 |
| `S7-P4-T2` | Phase 7.4 | `reserve_floor_cny = max(user_min_reserve_cny, average_fixed_monthly_expense_cny * reserve_months)` | 本轮完成 |
| `S7-P4-T3` | Phase 7.4 | 投资入金挤压生活现金模型 | 本轮完成 |

## Stage 7 Acceptance Criteria

- 置信度总分为 100，权重严格等于 30/10/20/15/15/10。
- 每个评分项都有中文评分标准，低分、中分、高分或满分可解释。
- 复核阈值统一为 `70`；不得按支付宝、微信、银行、券商等 source 名称分层。
- `消费总流出金额` 包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，并由退款抵消。
- `生活消费金额` 只包含普通生活消费，排除投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款。
- 大额消费、夜间消费、订阅扣费、投资市值、成本收益、行为公式、现金流窗口、储备金安全线和投资挤压模型均进入参数文件。
- 现金流压力分使用储备金覆盖、固定支出压力、收入不确定性和大额支出压力综合计算。
- `tests/test_v022_stage7_formula_scoring.py` 执行样本计算并校验数值，不只检查 marker 或函数名。
- Stage 7 不提前实现 Stage 8 Runtime Diff、Stage 9 参数中心或真实交易能力。

## Stage 7 Stop Condition

- 置信度权重不等于 100。
- 评分项缺少中文评分标准。
- 出现 source 分层复核阈值。
- 投资入金、基金申购、黄金申购或投资买入未进入消费总流出。
- 投资入金、基金申购、黄金申购或投资买入进入生活消费。
- 现金流窗口缺少 `7/21/30/60/90/180/360`。
- 储备金安全线不能同时支持用户自定义最小储备金和固定支出倍数。
- 投资入金挤压生活现金无法解释。

当前检查结论：以上停止条件均未触发。Stage 8 Runtime Diff、Stage 9 参数中心、Stage 10 建议生命周期不在本轮实现。

## Stage 7 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage7_formula_scoring.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests/test_v022_stage0_database_governance.py PFI/tests/test_pfi_parameters_consistency.py PFI/tests/test_v022_fx_effective_date.py PFI/tests/test_v022_stage3_source_account_profiles.py PFI/tests/test_v022_interconnection_no_double_count.py PFI/tests/test_v022_consumption_investment_outflow.py PFI/tests/test_v022_stage5_ledger_taxonomy.py PFI/tests/test_v022_stage6_tags_views.py PFI/tests/test_v022_stage7_formula_scoring.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src PFI/.venv/bin/python -B -m pytest PFI/tests -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```
