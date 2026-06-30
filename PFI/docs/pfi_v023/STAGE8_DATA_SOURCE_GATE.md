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

## Stage 8 Phase 8.2 检查板 UI

Phase 8.2 只实现数据源检查板 UI model 和只读证据，不执行上传/导入，不读取新数据，不推进 Phase 8.3。

本 phase 覆盖：

- `T8.2.1` 数据源矩阵：每个数据源展示 status、records、date range、last updated、blocked metrics。
- `T8.2.2` 上传/导入状态：展示当前只读 gate、auto import disabled 和可跳转处理入口。
- `T8.2.3` 解析预览/字段映射入口：已挂链 Alipay 流水展示解析预览；账户余额与持仓市值 read model 保持阻断；字段映射入口引用 Stage 6 已审计字段。
- `T8.2.4` 跳转到报告/复核：提供 `/reports`、`/ledger/review`、`/accounts/reconcile`、`/investment/holdings`。

当前检查板状态：

- `MetaDatabase/PFI Alipay 日流水`：`ready`，8815 条规范化流水，4 个原始文件，数据范围 `2022-06-06` 至 `2026-06-03`，解析预览可用，字段映射入口指向账本复核。
- `账户余额 read model`：`not_mounted`，阻断 `net_worth_cny` 与 `cash_balance_cny`，解析预览与字段映射入口保持阻断，处理入口为账户余额复核。
- `持仓市值 read model`：`not_mounted`，阻断 `net_worth_cny` 与 `investment_market_value_cny`，解析预览与字段映射入口保持阻断，处理入口为投资持仓复核。

Phase 8.2 证据：

- `PFI/reports/pfi_v023/stage_8/phase_8_2/dashboard_ui.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_2/dashboard_page_model.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_2/screenshots/data_source_dashboard.png`

## Stage 8 Phase 8.3 禁止假数据回退

Phase 8.3 只实现数据源检查板的禁止假数据回退策略、失败状态截图、过期状态截图和真为 0 状态证明；不执行 Stage 8 whole-stage review，不上传 GitHub main，不推进 Stage 9。

本 phase 覆盖：

- `T8.3.1` 禁止 fallback 测试：缺失、失败、过期或未挂链状态不得自动替换成非真实财务输入，也不得显示 `CNY 0.00`。
- `T8.3.2` 失败状态截图：`path_error` 与 `parse_error` 必须显示中文原因、失败细节和下一步动作。
- `T8.3.3` 过期状态截图：`outdated` 必须显示快照日期。
- `T8.3.4` 真为 0 状态证明：当前 Stage 8 没有真实 `confirmed_zero` 财务指标被渲染；零值只允许在 `status=confirmed_zero` 且 `source`、`as_of`、`evidence_hash` 完整时显示。

Phase 8.3 证据：

- `PFI/reports/pfi_v023/stage_8/phase_8_3/no_fallback_policy.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_3/state_evidence_cases.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_3/no_fallback_page_model.json`
- `PFI/reports/pfi_v023/stage_8/phase_8_3/screenshots/failure_state.png`
- `PFI/reports/pfi_v023/stage_8/phase_8_3/screenshots/outdated_state.png`
- `PFI/reports/pfi_v023/stage_8/phase_8_3/screenshots/zero_proof.png`

Stage 8 whole-stage review 未执行。
GitHub main upload 未执行。
