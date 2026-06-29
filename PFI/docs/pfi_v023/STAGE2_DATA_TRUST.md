# PFI v0.2.3 Stage 2 Phase 2.1 数据状态合同

本 phase 只交付 `Stage 2 Phase 2.1 — 数据状态合同`。目标是把真实数据状态机、核心指标字段、中文状态文案和禁止假财务数据扫描规则固定下来，作为后续真实数据审计与页面门禁的基础。

## 本 Phase 范围

- 定义 `PFI/src/pfi_v02/stage_v023_data_state.py`。
- 定义 `PFI/web/app/dataStatus.js`。
- 定义核心指标必须包含的字段：`metric_id`、`label`、`value`、`currency`、`status`、`source`、`as_of`、`evidence_hash`、`message_zh`。
- 定义状态：`ready`、`confirmed_zero`、`not_loaded`、`not_mounted`、`path_error`、`permission_error`、`parse_error`、`outdated`、`filter_empty`、`calculation_error`、`review_required`。
- 定义中文空状态和错误状态文案。
- 定义禁止假财务数据扫描规则。

## 非假零规则

未加载真实数据时不显示 CNY 0.00。只有以下状态允许显示财务数值：

- `ready`：真实数据已加载，并且包含 `source`、`as_of`、`evidence_hash`。
- `confirmed_zero`：真实数据确认数值为零，并且包含 `source`、`as_of`、`evidence_hash`。

其他状态必须显示中文说明，不得把缺失、路径错误、权限错误、解析失败、过期、筛选为空或计算失败渲染成财务 0。

## 明确未做

本 phase 不做真实数据源路径审计，不统计文件数、记录数、账户数、持仓数或 read model hash；这些属于 Phase 2.2。本 phase 不做页面门禁接入、核心指标 UI 接入或截图验收；这些属于 Phase 2.3。

## 验收

- `test_v023_stage2_data_state_machine.py` 验证 schema、状态、证据链、中文文案、JS 合同和 evidence。
- `test_v023_no_mock_financial_data.py` 验证禁止假财务数据扫描规则。
- `node --check PFI/web/app/dataStatus.js` 验证 JS 合同语法。

## Stage 2 Phase 2.2 真实数据审计

本 phase 只交付 `Stage 2 Phase 2.2 — 真实数据审计`。审计范围是定位当前本机真实个人财务数据源路径，并统计文件数、记录数、日期范围、账户/持仓/read model 状态。

当前本机真实个人财务数据源状态为 not_mounted：

- `/Users/linzezhang/MetaDatabase/PFI`：不存在。
- `/Users/linzezhang/Documents/MetaDatabase/PFI`：不存在。
- `/Users/linzezhang/Documents/Codex/MetaDatabase/PFI`：不存在。
- `PFI/MetaDatabase`：只包含 README 指针，不包含真实个人财务数据文件。
- `PFI/data`：只包含 v0.2.2 FX 快照和系统验收文件，不作为 v0.2.3 个人财务 read model。

因此本 phase 不生成、复制或伪造任何个人财务数据；核心指标状态保持 `not_mounted`，未挂载时不得显示 `CNY 0.00`。

本 phase 不做页面门禁接入、核心指标 UI 接入或截图验收；这些属于 Phase 2.3。

## Stage 2 Phase 2.3 页面门禁

本 phase 只交付 `Stage 2 Phase 2.3 — 页面门禁`。交付边界是把 Phase 2.1 的状态机和 Phase 2.2 的本机真实数据审计结果渲染成可验收的页面门禁模型、HTML 输出和浏览器截图证据。

页面门禁必须展示：

- 核心指标状态：`净资产`、`现金余额`、`投资市值`。
- 数据检查板：文件数、原始记录数、标准化记录数、账户数、持仓数、read model hash、as of。
- 路径错误、权限失败、解析失败三类错误状态及人工处理动作。

当前本机真实个人财务数据源仍为 `not_mounted`，因此页面门禁展示 `未挂载真实个人财务数据源`。不得把缺失数据、路径错误、权限失败或解析失败显示成 `CNY 0.00`。

本 phase 只改 `PFI/web/app/dataStatus.js` 的可调用门禁 renderer 和 `PFI/reports/pfi_v023/stage_2/phase_2_3/` 下的验收证据。`PFI/web/index.html` 与 `PFI/web/app/shell.js` 不在本 phase 修改范围内；正式导航接线属于后续 Stage 3。
