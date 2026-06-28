# PFI v0.2.2 Stage 7 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 7；不复审 Stage 8-13，不做整体项目复审，不重装 app 入口，不同步 GitHub。

复审结论：Stage 7 模型公式、阈值与评分标准合同通过；原目标测试中的构造财务记录已改为真实 `MetaDatabase` 支付宝流水或真实空态。
上线阻塞项：1

剩余阻塞项是全局 legacy 测试/样例/模拟数据审计仍未关闭；Stage 7 本轮已不再用 `MOCK` 持仓或手写交易作为验收依据。

## 复审范围

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S7-P1-T1` | 100 分置信度评分公式，权重为字段完整度 30、金额方向 10、规则命中 20、商户/对手方 15、关联匹配 15、历史一致性 10。 | 通过 |
| `S7-P1-T2` | 每个评分项有中文低分、中分、高分或满分标准。 | 通过 |
| `S7-P1-T3` | 统一低置信复核阈值 `70`，禁止 source 分层阈值。 | 通过 |
| `S7-P2-T1` | `消费总流出金额` 包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，并由退款抵消。 | 通过 |
| `S7-P2-T2` | `生活消费金额` 只包含普通生活消费，并排除投资资金流和内部移动。 | 通过 |
| `S7-P2-T3` | 大额消费阈值为 `CNY >= 2000` 或原币 `AUD >= 500`。 | 通过 |
| `S7-P2-T4` | 夜间窗口 `22:00-06:00`；电子产品冲动规则并入夜间/大额/计划外标签组合。 | 通过 |
| `S7-P3-T1` | 投资市值公式为 `quantity * latest_price * fx_rate_to_cny`。 | 通过 |
| `S7-P3-T2` | 成本、已实现收益、未实现收益、总收益公式纳入费用、税费和汇率影响。 | 通过 |
| `S7-P3-T3` | 行为公式覆盖频率、换手率、持仓周期、追涨、杀跌、现金拖累、集中度。 | 通过 |
| `S7-P4-T1` | 现金流窗口固定为 `7/21/30/60/90/180/360`。 | 通过 |
| `S7-P4-T2` | 储备金安全线支持用户自定义最低储备金和固定支出倍数。 | 通过 |
| `S7-P4-T3` | 投资入金挤压生活现金模型可解释。 | 通过 |

## 发现与修复

修复 1：Stage 7 验收不再依赖构造财务事实。

- 问题：`tests/test_v022_stage7_formula_scoring.py` 原来使用 `MOCK` 持仓、`date(2026, 6, 1)` 和手写卖出交易验证投资公式。这与用户要求冲突：PFI 交付和验收不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据或虚构财务事实。
- 修复：新增 `load_stage7_alipay_formula_inputs_from_metadatabase()`，从 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` 读取真实支付宝流水，派生 Stage 7 置信度、消费公式和现金流公式输入。
- 投资边界：当前 `MetaDatabase/PFI` 只有支付宝流水，没有真实持仓快照或可确认卖出交易；因此投资市值、收益和行为评分验收使用中文空态，不伪造收益。

修复 2：真实流水进入公式验收。

- 数据源：`MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`。
- 真实记录数：`8815`。
- 派生事件类型：`ordinary_consumption=3831`、`investment_return=3133`、`internal_transfer=1260`、`cash_inflow=308`、`refund=250`、`fund_subscription=21`、`bullion_purchase=12`。
- 当前真实消费公式结果：`gross_consumption_cny=1727278.37`，`living_consumption_cny=1545600.44`，`refund_offset_cny=132707.90`。
- 当前真实现金流推导结果：`future_cash_balance_cny=10275324.15`，`reserve_floor_cny=102753.57`，`cashflow_pressure_score=0.00`。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 置信度权重不等于 100 | 未触发；权重合计为 100。 |
| 评分项缺少中文评分标准 | 未触发；6 个评分项均有中文分段说明。 |
| 出现 source 分层复核阈值 | 未触发；统一阈值为 `70`，`source_layered_thresholds_allowed=false`。 |
| 投资入金、基金申购、黄金申购或投资买入未进入消费总流出 | 未触发；真实 `fund_subscription` 和 `bullion_purchase` 已进入总流出。 |
| 投资入金、基金申购、黄金申购或投资买入进入生活消费 | 未触发；生活消费只含普通消费并由退款抵消。 |
| 现金流窗口缺少 `7/21/30/60/90/180/360` | 未触发。 |
| 储备金安全线不能同时支持用户自定义最小储备金和固定支出倍数 | 未触发。 |
| 投资入金挤压生活现金无法解释 | 未触发；输出包含中文解释。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 7 模块 | `PFI/src/pfi_v02/stage_v022_formula_scoring.py` |
| 原 Stage 7 合同测试 | `PFI/tests/test_v022_stage7_formula_scoring.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage7.py` |
| Stage 7 验收报告 | `PFI/docs/pfi_v022/STAGE7_FORMULA_SCORING.md` |
| Roadmap lock | `PFI/docs/pfi_v022/ROADMAP_LOCK.md` |
| 真实标准化流水 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage7_formula_scoring.py tests/test_v022_review_stage7.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_review_stage7.py -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 最新验证结果

- Stage 7 目标 + 复审测试：`10 passed, 38 subtests passed`。
- Stage 0-7 v0.2.2 相关回归：`61 passed, 245 subtests passed`。
- Web shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- 空白检查：`git diff --check -- PFI` 通过。
- 8501 health：`ok`。
- 真实浏览器矩阵：`/tmp/pfi_stage7_review_recheck/summary.json` 通过；桌面 15 个一级入口、7 个首页功能按钮、全局搜索 `8815/406`、策略实验室同路由、业务页反馈隔离、禁用词扫描、console errors 均通过；移动端 5 个底部入口可见，水平溢出 `0px`。截图为 `/tmp/pfi_stage7_review_recheck/desktop.png` 和 `/tmp/pfi_stage7_review_recheck/mobile.png`。

## 剩余风险

- 本轮只证明 Stage 7 已按真实 MetaDatabase 流水和真实空态完成复审；不能自动证明 Stage 8-13 或整体项目复审完成。
- PFI 仓库仍存在 legacy `demo/sample/synthetic/fixture/mock/fake/测试样例` 命中；后续不能只用完整 pytest 作为产品验收依据。
- 当前没有真实持仓快照或卖出交易，因此投资收益不应显示伪造数值；后续需要真实持仓数据后再做投资公式实数验收。
- 本轮不重装 app 入口；整体 pursuing goal 完成后再统一刷新 app 入口。
- 本轮不同步 GitHub；当前 worktree 存在 side thread 和历史混合改动，后续同步前必须先做 PFI-only diff review。
