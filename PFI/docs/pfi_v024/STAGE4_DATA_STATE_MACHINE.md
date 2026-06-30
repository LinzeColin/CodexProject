# PFI v0.2.4 Stage 4 Data State Machine

本轮只执行：`Stage 4 / Phase 4.1 - 状态机定义`。
不执行 Phase 4.2 read model 挂链、不修改首页核心卡片、不上传 GitHub main。

## Scope

Phase 4.1 只冻结真实数据状态机合同：

- 核心状态枚举。
- 指标状态 schema。
- 中文阻断原因。
- 禁止假零规则。

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

## Non Goals

- 不读取本机真实数据路径。
- 不挂接 `read_model_status.py`。
- 不改首页、账户、投资、消费、报告页面的显示逻辑。
- 不重装 app bundle。
- 不上传 GitHub main。
