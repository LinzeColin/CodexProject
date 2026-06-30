# PFI v0.2.4 Stage 4 Data State Machine

当前已完成：`Stage 4 whole-stage review - 复审并解决暴露问题`。
GitHub main upload 尚未执行。

## Scope

Phase 4.1 冻结真实数据状态机合同：

- 核心状态枚举。
- 指标状态 schema。
- 中文阻断原因。
- 禁止假零规则。

Phase 4.2 把该合同挂到共享 read model status：

- `/api/read-model-status` 输出当前本机真实数据状态。
- `#pfi-read-model-status` 为 app bundle 提供嵌入式兜底。
- `data_state.js` 生成 home/accounts/investment/consumption/insights 的同源 surface view model。
- `shell.js` 使用同一状态对象覆盖核心卡片，不再让缺失状态落到 `CNY 0.00`。

Phase 4.3 验收该合同：

- `tests/test_v024_stage4_phase43_acceptance.py` 覆盖缺失指标不显示财务 0、`confirmed_zero` 必须有证据链。
- `validate_v024_stage4_phase43_chrome.py` 生成 Chrome headless 截图和 browser validation。
- `data_state.js` 和 `shell.js` 保持 null `record_count` / `confidence` 为未知，避免误显示 `0 条记录`。

Stage 4 whole-stage review 复审该合同：

- Phase 4.1、Phase 4.2、Phase 4.3 均为 candidate pass。
- 每个核心指标都有 `status`、`source_id`、`as_of`、`record_count` 和 `calculation_state`。
- 首页、账户、投资、消费和报告共享同一 `read_model_hash`。
- Phase 4.3 browser validation 和两张截图纳入整阶段验收。
- 复审发现 3 项均已 fixed；GitHub main upload 仍为未执行。

## Status Values

| status | 中文含义 | 是否可显示财务 0 |
| --- | --- | --- |
| `ready` | 真实数据已加载 | 可显示真实值 |
| `confirmed_zero` | 真实数据确认数值为零 | 可显示 0，但必须有证据 |
| `not_loaded` | 未加载真实数据 | 不可显示 0 |
| `source_missing` | 真实数据源未挂链 | 不可显示 0 |
| `path_error` | 数据路径错误 | 不可显示 0 |
| `parse_failed` | 解析失败 | 不可显示 0 |
| `outdated_snapshot` | 快照过期 | 只能显示旧值日期，不可伪装为当前值 |
| `permission_denied` | 权限失败 | 不可显示 0 |
| `calculation_failed` | 计算失败 | 不可显示 0 |
| `filtered_empty` | 当前筛选无结果 | 不可当作全局 0 |

## Required Metric Fields

每个核心指标必须携带：

`metric_id`、`value`、`currency`、`status`、`source_id`、`record_count`、
`as_of`、`formula_id`、`confidence`、`blocking_reason_zh`、`calculation_state`。

## Phase 4.2 Current Read Model Status

| metric_id | status | value policy | source |
| --- | --- | --- | --- |
| `net_worth_cny` | `source_missing` | 不显示财务 0 | 等待账户余额与持仓 read model |
| `cash_balance_cny` | `source_missing` | 不显示财务 0 | 等待账户余额 read model |
| `investment_market_value_cny` | `source_missing` | 不显示财务 0 | 等待持仓市值 read model |
| `consumption_outflow_cny` | `ready` | 显示真实流水消费总流出 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |
| `report_summary_status` | `ready` | 显示状态，不当作财务金额 | `MetaDatabase/PFI/alipay_daily/processed/alipay_import_manifest.json` |

当前 source summary：`MetaDatabase/PFI` ready，`8815` 条记录，`4` 个原始文件，as of `2026-06-03`。

## Phase 4.3 Acceptance

| check | result | evidence |
| --- | --- | --- |
| 缺失/未挂链指标不显示财务 0 | pass | `reports/pfi_v024/stage_4/phase_4_3/screenshots/data_missing_state.png` |
| `confirmed_zero` 缺证据不可通过 | pass | `tests/test_v024_stage4_phase43_acceptance.py` |
| 真零显示必须含 source、as_of、record_count、formula | pass | `reports/pfi_v024/stage_4/phase_4_3/screenshots/confirmed_zero_gate.png` |
| 前端 null 记录数不显示成 0 | pass | `web/app/data_state.js`、`web/app/shell.js` |

当前真实生产 `confirmed_zero` 指标数量：`0`。Phase 4.3 只证明零值显示门禁，不把零值门禁页作为生产财务事实。

## Remaining Non Goals

- 不重装 app bundle。
- 不上传 GitHub main。
- 不进入 Stage 5。
