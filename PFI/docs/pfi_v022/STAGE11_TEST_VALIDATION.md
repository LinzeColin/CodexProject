# Stage 11 - 测试与验证

版本：`v0.2.2 数据库治理`

本轮目标：把 Stage 4-10 建立的金融事实层、双消费口径、投资资产口径、现金流追溯、图表来源和图表新鲜度收口为可重复运行的本地测试门。Stage 11 不实现 Stage 12 文档同步与最终交付，不执行 Stage 13 后置触发型复核，不修改 v0.2.1 主 Web Shell UIUX 基线，不新增真实交易、自动投资、支付或券商提交能力。

## 真实输入来源与复审修正

Stage 11 复审后，正式测试与验证只允许读取真实 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`、本地参数 hash、真实 read model 和中文真实空态；不得使用模拟记录、构造金额、构造交易 ID 或虚构持仓作为验收依据。

当前真实输入摘要：

- 标准化支付宝流水：`8815` 条。
- 真实事件计数：`ordinary_consumption=3831`、`fund_subscription=21`、`refund=250`、`bullion_purchase=12`、`internal_transfer=1260`。
- 真实消费总流出：`CNY 1,727,278.37`。
- 真实生活消费：`CNY 1,545,600.44`。
- 真实支付宝基金申购：`21` 条，合计 `CNY 4,120.00`，进入消费总流出，不进入生活消费；当前无真实基金持仓快照，不伪造持仓增加。
- 真实退款：`250` 条，抵消金额 `CNY 132,707.90`，不作为投资收益或收入伪造。
- 暂无真实 CBA -> Moomoo 双边转账、暂无真实信用卡还款、暂无真实计划事件、暂无真实持仓快照时，测试必须显示中文真实空态，并保持相关金额为 `None` 或空集合。
- 图表性能检查使用真实 `8815` 条标准化流水记录，仍要求显示 `compute time` 与 `cache status`，但不生成替代记录。

## Phase 11.1 - 金融逻辑单元测试

| Task ID | 测试项 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S11-P1-T1` | 投资入金计入消费总流出 | CBA -> Moomoo 当前暂无真实双边转账或入金分组时显示中文真实空态，不构造入金金额 | 本轮复审修正 |
| `S11-P1-T2` | 基金申购计入消费总流出 | 真实支付宝基金申购：消费总流出增加，生活消费不增加；无真实持仓快照时不伪造投资持仓增加 | 本轮复审修正 |
| `S11-P1-T3` | 退款抵消 | 退款抵消原消费，且不影响投资收益 | 本轮完成 |
| `S11-P1-T4` | 信用卡还款不重复计入生活消费 | 当前暂无真实信用卡还款事件时显示中文真实空态，不构造还款金额 | 本轮复审修正 |

停止条件检查：投资入金未进入消费总流出、基金申购被当普通生活消费、退款重复计入收入、还款造成重复消费时停止。

## Phase 11.2 - 跨板块一致性测试

| Task ID | 测试项 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S11-P2-T1` | 首页与消费页一致 | 首页消费总流出 = 消费页消费总流出 = 月报消费总流出 | 本轮完成 |
| `S11-P2-T2` | 首页与投资页一致 | 首页投资资产 = 投资页投资资产 = 投资报告投资资产 | 本轮完成 |
| `S11-P2-T3` | 现金流与账本一致 | 现金流预测来源能追溯到真实账本事件；暂无真实计划事件时显示中文真实空态 | 本轮复审修正 |

停止条件检查：三处消费金额不一致、三处投资资产不一致、现金流无法解释时停止。

## Phase 11.3 - 可视化一致性测试

| Task ID | 测试项 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S11-P3-T1` | 图表数据来源测试 | 每个图表可追溯 `metric_id`、`formula_id`、`parameter_hash`、`data_hash` | 本轮完成 |
| `S11-P3-T2` | 图表及时性测试 | 数据变化后受影响图表标记 `needs_update` 或 `updated` | 本轮完成 |
| `S11-P3-T3` | 图表性能测试 | 真实 `8815` 条标准化流水下图表生成不明显卡死，并显示 `compute time` / `cache status` | 本轮复审修正 |

停止条件检查：图表数字无来源、图表显示旧数据、无性能状态或明显卡顿时停止。

新增停止条件检查：正式测试门出现模拟记录、构造金额、构造交易 ID、构造持仓或把中文真实空态替换成伪造数值时停止。

## 交付文件

- `PFI/src/pfi_v02/stage_v022_test_validation.py`
- `PFI/src/pfi_v02/stage_v022_database_governance.py`
- `PFI/tests/test_v022_stage11_test_validation.py`
- `PFI/docs/pfi_v022/STAGE11_TEST_VALIDATION.md`
- `PFI/config/pfi_parameters.yaml`
- `PFI/config/parameter_changelog.md`
- `PFI/模型参数文件.md`
- `PFI/功能清单.md`
- `PFI/开发记录.md`
- `PFI/HANDOFF.md`
- `PFI/README.md`

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage11_test_validation.py tests/test_v022_review_stage11.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_review_stage9.py tests/test_v022_stage10_report_advice_review.py tests/test_v022_review_stage10.py tests/test_v022_stage11_test_validation.py tests/test_v022_review_stage11.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 本轮复审验证结果

- Stage 11 目标 + 复审测试：`11 passed, 15 subtests passed`。
- Stage 0-11 v0.2.2 相关回归：`104 passed, 363 subtests passed`。
- Web shell 语法检查：`node --check web/app/shell.js` 通过。
- 项目治理检查：`python3 scripts/validate_project_governance.py --project PFI` 返回 `errors: 0`、`warnings: 0`。
- 空白检查：`git diff --check -- PFI` 通过。
- 8501 health：`curl -fsS http://127.0.0.1:8501/_stcore/health` 返回 `ok`。
- 真实 8501 浏览器矩阵：`/tmp/pfi_stage11_review_recheck/summary.json` 通过；桌面和移动端均验证 7 个首页 workflow 卡片可见、`.workflow-meta=0`、一级入口和首页真实按钮可点击、全局搜索 `406/8815` 可用、禁用词 `0`、console/page errors `0`、水平溢出 `0px`。

## 非目标

- Stage 12 文档同步与最终交付不在本轮实现。
- Stage 13 后置触发型复核不在本轮实现。
- 不修改 v0.2.1 主 Web Shell UIUX 基线。
- 不联网、不调用外部 LLM、不生成真实 agent 任务。
- 不新增真实交易、自动投资、支付或券商提交。
