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
| Stage 8 | 本地运行 Diff 与 Impacted Metrics | 待 owner 开启 | dependency hash、diff 收紧、LLM 触发规则。 |
| Stage 9 | 可视化与 UI/UX | 待 owner 开启 | 参数中心、Interconnection 可视化、现金流和 drilldown。 |
| Stage 10 | 报告、建议与复盘 | 待 owner 开启 | 双消费口径报告、投资成本行为、建议评分生命周期。 |
| Stage 11 | 测试与验证 | 待 owner 开启 | 金融逻辑、跨板块一致性、可视化一致性测试。 |
| Stage 12 | 文档同步与交付 | 待 owner 开启 | 三基、审查 HTML、总结报告。 |
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
