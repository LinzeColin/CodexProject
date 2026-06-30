# PFI v0.2.3 Stage 4 二级页面差异化

Stage 4 目标是让二级入口像真实业务页面跳转，而不是同一模板换标题。组件可以复用，但页面必须拥有不同主对象、主布局、主操作、空状态、错误状态、数据来源说明和验收截图。

## Phase 4.1 范围

本 phase 只交付 `Stage 4 Phase 4.1 — 资产/账本/投资二级页`：

- `账户与资产`：账户地图、账户清单、资产趋势、账户对账。
- `账本流水`：流水列表、筛选搜索、分类复核、导出流水。
- `投资管理`：投资总览、持仓、交易记录、收益分析。

Phase 4.1 不改 `消费管理`、`数据源与上传`、`报告与洞察`、`市场与研究`、`设置`、`建议与复盘` 的二级页面差异化；这些属于 Phase 4.2 和 Phase 4.3。

## 实现合同

- 二级页合同在 `PFI/web/app/pages/stage4Subpages.js` 中声明。
- `PFI/web/app/shell.js` 在启动时加载 Stage 4 pages catalog。
- 命中 Phase 4.1 route 时，页面更新 `URL/hash`、state、breadcrumb、标题、主对象、主操作、空状态和错误状态。
- Stage 3 的 10 个正式一级入口和兼容 route 合同保持不变。
- 未加载真实数据时只显示中文真实空态，不显示财务假值。

## Phase 4.1 验收

验收证据：

- `PFI/reports/pfi_v023/stage_4/phase_4_1/browser_validation.json`
- `PFI/reports/pfi_v023/stage_4/phase_4_1/screenshots/accounts_subpages.png`
- `PFI/reports/pfi_v023/stage_4/phase_4_1/screenshots/ledger_subpages.png`
- `PFI/reports/pfi_v023/stage_4/phase_4_1/screenshots/investment_subpages.png`

测试：

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_stage4_subpage_differentiation.py -q
```

## 明确未做

- Stage 4 Phase 4.2 消费/数据/报告二级页。
- Stage 4 Phase 4.3 市场/设置/建议二级页。
- Stage 4 整体复审。
- GitHub main 上传；中间 phase 完成不上传。
