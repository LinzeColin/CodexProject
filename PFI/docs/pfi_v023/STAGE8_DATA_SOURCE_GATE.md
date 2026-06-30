# PFI v0.2.3 Stage 8 Data Source Gate

## Stage 8 Phase 8.1 数据源模型

Phase 8.1 只定义数据源状态模型，不实现正式检查板 UI，不执行上传/导入流程，不自动读取新数据。

本 phase 覆盖：

- `T8.1.1` 定义 data source status。
- `T8.1.2` 统计记录数和日期范围。
- `T8.1.3` 输出 blocked metrics。
- `T8.1.4` 错误原因中文化。

当前数据源模型只读取 Stage 6 核心 read model：

- `MetaDatabase/PFI Alipay 日流水`：`ready`，8815 条规范化流水，4 个原始文件，数据范围 `2022-06-06` 至 `2026-06-03`。
- `账户余额 read model`：`not_mounted`，阻断 `net_worth_cny` 与 `cash_balance_cny`。
- `持仓市值 read model`：`not_mounted`，阻断 `net_worth_cny` 与 `investment_market_value_cny`。

显示规则：

- 每个数据源必须展示 status、records、date range、last updated 和 blocked metrics。
- 未挂链数据源显示中文原因和下一步动作，不显示 `CNY 0.00`。
- Phase 8.1 只保存只读 evidence pack 和页面快照，不执行自动导入。

错误原因中文化覆盖：

- `not_loaded`
- `not_mounted`
- `path_error`
- `permission_error`
- `parse_error`
- `outdated`
- `filter_empty`
- `calculation_error`
- `review_required`

Phase 8.1 证据：

- `PFI/reports/pfi_v023/stage_8/phase_8_1/data_source_gate.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_1/data_source_gate_page_model.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_1/error_reason_catalog.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_1/screenshots/data_source_gate.png`

Phase 8.2 检查板 UI 未执行。
Phase 8.3 禁止假数据回退未执行。
Stage 8 whole-stage review 未执行。
GitHub main upload 未执行。
