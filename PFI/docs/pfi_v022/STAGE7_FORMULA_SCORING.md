# PFI v0.2.2 Stage 7 - 模型公式、阈值与评分标准

版本：`v0.2.2 数据库治理 / E2E 逻辑优化`

本轮目标：把置信度、消费、投资和现金流模型从分散说明升级为统一、可测试、可解释的中文公式与阈值合同。Stage 7 不修改 v0.2.1 HTML Web Shell UIUX 基线，不实现 Stage 8 Runtime Diff、Stage 9 参数中心、Stage 10 建议生命周期，也不新增真实交易、支付、券商提交或自动投资能力。

## Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S7-P1-T1` | Phase 7.1 | 100 分置信度公式 | 本轮完成 |
| `S7-P1-T2` | Phase 7.1 | 每个评分项中文评分标准 | 本轮完成 |
| `S7-P1-T3` | Phase 7.1 | 统一低置信复核阈值 `70` | 本轮完成 |
| `S7-P2-T1` | Phase 7.2 | 消费总流出公式 | 本轮完成 |
| `S7-P2-T2` | Phase 7.2 | 生活消费公式 | 本轮完成 |
| `S7-P2-T3` | Phase 7.2 | 大额消费阈值 `CNY >= 2000` 或原币 `AUD >= 500` | 本轮完成 |
| `S7-P2-T4` | Phase 7.2 | 夜间窗口 `22:00-06:00`，电子产品冲动规则并入夜间/大额逻辑 | 本轮完成 |
| `S7-P3-T1` | Phase 7.3 | 投资市值公式 | 本轮完成 |
| `S7-P3-T2` | Phase 7.3 | 成本、已实现、未实现、总收益公式 | 本轮完成 |
| `S7-P3-T3` | Phase 7.3 | 投资行为评分公式范围 | 本轮完成 |
| `S7-P4-T1` | Phase 7.4 | 现金流窗口 `7/21/30/60/90/180/360` | 本轮完成 |
| `S7-P4-T2` | Phase 7.4 | 储备金安全线公式 | 本轮完成 |
| `S7-P4-T3` | Phase 7.4 | 投资入金挤压生活现金模型 | 本轮完成 |

## 置信度评分

`confidence_score` 使用 100 分制：

| 评分项 | 权重 | 中文评分标准 |
| --- | ---: | --- |
| 字段完整度 | 30 | 关键字段齐全得高分；缺金额、币种、时间、来源或描述时降分。 |
| 金额方向 | 10 | 流入/流出方向与事件类型一致得满分；方向不明或反向时降分。 |
| 规则命中 | 20 | 明确命中分类、事件类型、标签或 Interconnection 规则时得高分。 |
| 商户/对手方 | 15 | 商户、对手方或账户名称可识别且稳定时得高分。 |
| 关联匹配 | 15 | 可匹配同一 `economic_event_id` 或 `interconnection_group_id` 时得高分。 |
| 历史一致性 | 10 | 与历史同类记录金额、周期、商户或账户角色一致时得高分。 |

统一复核阈值：`70`。低于 `70` 的记录进入人工复核；不得按数据源名称设置不同复核线，也不得出现“支付宝 65、银行 75”这类 source-layered threshold。

订阅识别评分：

```text
subscription_score = 金额相似度 * 40% + 周期稳定性 * 30% + 商户相似度 * 20% + 历史重复次数 * 10%
```

`subscription_score >= 75` 时可打 `订阅扣费` 候选标签；低于阈值只进入复核候选，不自动确认。

## 消费模型公式

`消费总流出金额`：

```text
gross_consumption_cny = 生活消费 + 投资入金 + 基金申购 + 黄金申购 + 投资买入 + 金融费用 - 退款抵消
```

`生活消费金额`：

```text
living_consumption_cny = 普通生活消费 - 退款抵消
```

排除项：投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款不得进入生活消费。

大额消费：`amount_cny >= 2000` 或原币 `AUD >= 500`。夜间消费窗口：`22:00-06:00`。电子产品冲动候选不再单独设硬编码阈值，而是由 `大额消费 + 夜间消费 + 计划外/非周期性` 等标签组合解释。

## 投资模型公式

`投资市值`：

```text
market_value_cny = quantity * latest_price * fx_rate_to_cny
```

`剩余成本`：

```text
remaining_cost_cny = remaining_quantity * average_cost * fx_rate_to_cny + allocated_fee_cny + allocated_tax_cny
```

`未实现收益`：

```text
unrealized_pnl_cny = market_value_cny - remaining_cost_cny
```

`已实现收益`：

```text
realized_pnl_cny = sell_proceeds_cny - sold_cost_cny - fee_cny - tax_cny
```

`总收益`：

```text
total_pnl_cny = realized_pnl_cny + unrealized_pnl_cny + dividends_cny + interest_cny - total_fee_cny - total_tax_cny + fx_pnl_cny
```

费用、税费和汇率影响必须可追溯；数据不足时显示中文空状态或 `需要复核`，不得伪造收益。

投资行为公式覆盖：交易频率、换手率、持仓周期、追涨候选、杀跌候选、现金拖累、集中度暴露。当前阈值为频繁交易 `6 次及以上` 或换手率 `>= 50%`；集中度观察线 `35%`，高风险线 `50%`。

## 现金流模型公式

现金流窗口固定为：

```text
7/21/30/60/90/180/360
```

未来现金余额：

```text
future_cash_balance(H) =
current_life_cash + expected_income + expected_refund
- fixed_expenses - flexible_expenses - debt_repayment
- planned_investment_deposit + planned_investment_return
```

储备金安全线：

```text
reserve_floor_cny = max(user_min_reserve_cny, average_fixed_monthly_expense_cny * reserve_months)
```

默认 `reserve_months = 3`，用户自定义最小储备金优先纳入比较。

现金流压力分：

```text
cashflow_pressure_score = clamp(
  0,
  100,
  100 - 50 * reserve_coverage + 20 * fixed_cost_pressure
  + 15 * income_uncertainty + 15 * large_spend_pressure
)
```

投资入金挤压生活现金：

```text
investment_squeeze_cny = max(0, reserve_floor_cny - future_cash_balance_after_investment)
```

当 planned investment deposit 使未来生活现金低于储备金安全线时，标记 `投资挤压现金`，并在现金流报告中解释是投资计划挤压生活现金，不把它误判成普通生活消费。

Stage 7 锁定的现金流可视化合同包括：现金流阶梯图、现金流瀑布图、储备金安全带、未来大额流出时间轴、消费-投资挤压图、现金流窗口对比表。真正参数中心或前端页面属于后续 Stage 9，不在本轮改 Web Shell。

## Acceptance Criteria

- 置信度总权重严格等于 100，评分项为 30/10/20/15/15/10。
- 每个评分项都有中文评分标准，包含低分、中分、高分或满分说明。
- 低置信复核阈值统一为 `70`，禁止按来源分层阈值。
- 消费总流出包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用。
- 生活消费排除投资入金、基金申购、黄金申购、投资买入、内部转账、信用卡还款。
- 大额消费、夜间消费、订阅识别、投资市值、成本收益、行为评分、现金流窗口、储备金安全线、投资挤压模型均有机器可读参数和中文说明。
- `config/pfi_parameters.yaml` schema 升级为 `PFIParametersV022Stage7`，并保留 Stage 1-6 历史 task ids。
- `tests/test_v022_stage7_formula_scoring.py` 不是字符串 marker 测试，必须执行样本计算并校验结果。

## Stop Condition

- 置信度权重合计不是 100。
- 评分项缺中文标准。
- 出现按 source 名称分层的复核阈值。
- 投资入金、基金申购、黄金申购或投资买入没有进入消费总流出。
- 投资入金、基金申购、黄金申购或投资买入进入生活消费。
- 现金流窗口缺少 `7/21/30/60/90/180/360` 任一窗口。
- 储备金安全线不能同时支持用户自定义最小储备金和固定支出倍数。
- 投资入金挤压生活现金无法解释。
- 本轮提前修改 Stage 8 Runtime Diff、Stage 9 参数中心或真实交易能力。

当前检查结论：以上停止条件均未触发。

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage7_formula_scoring.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前本地 closeout 结果：

- Stage 7 目标测试：`7 passed`。
- Stage 0-7 v0.2.2 回归：`58 passed`。
- 完整 PFI pytest：`216 passed`。
- Web Shell 语法：`node --check web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- Diff 空白检查：`git diff --check -- PFI` 通过。
- macOS app acceptance lite：`29 pass / 0 fail / 2 info`。
- 8501 健康检查：`ok`。
- 真实浏览器验收：数据源与上传点击后 `首页总览`、`账户与资产`、`投资管理`、`消费管理`、`数据源与上传`、`AUD/CNY`、`上传中心`、`导入中心` 全部可见；正式 UI 禁用词扫描 0 命中；console errors `0`；截图 `/tmp/pfi-v022-stage7-upload-verified-final.png`。
