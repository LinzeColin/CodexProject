# PFI v0.2.3 Stage 4 二级页面差异化

Stage 4 目标是让二级入口像真实业务页面跳转，而不是同一模板换标题。组件可以复用，但页面必须拥有不同主对象、主布局、主操作、空状态、错误状态、数据来源说明和验收截图。

## Phase 4.1 范围

本 phase 只交付 `Stage 4 Phase 4.1 — 资产/账本/投资二级页`：

- `账户与资产`：账户地图、账户清单、资产趋势、账户对账。
- `账本流水`：流水列表、筛选搜索、分类复核、导出流水。
- `投资管理`：投资总览、持仓、交易记录、收益分析。

Phase 4.1 不改 `消费管理`、`数据源与上传`、`报告与洞察`、`市场与研究`、`设置`、`建议与复盘` 的二级页面差异化；这些属于 Phase 4.2 和 Phase 4.3。

## Phase 4.2 范围

本 phase 只交付 `Stage 4 Phase 4.2 — 消费/数据/报告二级页`：

- `消费管理`：消费总览、分类分析、预算、订阅、异常消费。
- `数据源与上传`：上传中心、导入中心、数据源管理、待复核、导入历史。
- `报告与洞察`：月报、季报、年报、自定义报告、导出。

Phase 4.2 不改 `市场与研究`、`设置`、`建议与复盘` 的二级页面差异化；这些属于 Phase 4.3。

## Phase 4.3 范围

本 phase 只交付 `Stage 4 Phase 4.3 — 市场/设置/建议二级页`：

- `市场与研究`：市场观察、研究笔记、公司研究、基金研究、策略实验室。
- `设置`：账户偏好、数据与系统、隐私与本地存储、反馈偏好、备份恢复。
- `建议与复盘`：建议列表、建议详情、决策记录、复盘记录。
- v0.1 兼容入口 `/market/watch`、`/market/research`、`/market/lab`、`/settings/data` 均落到 Phase 4.3 差异化页面。

Phase 4.3 不运行 Stage 4 整体复审，不上传 GitHub main；这些属于 Phase 4 完整复审与 closeout。

## Stage 4 整体复审

Stage 4 closeout 只复审 Stage 4 二级页面差异化合同，不进入 Stage 5 或后续功能。复审记录在 `PFI/reports/pfi_v023/stage_4/stage4_review/evidence.json`，浏览器复核记录在 `PFI/reports/pfi_v023/stage_4/stage4_review/browser_review.json`。

复审发现并修复：

- `home_subpages_missing_from_stage4_catalog`：Task Pack Stage 4 要求每个正式一级入口都有 3–5 个二级页面。Phase 4.1–4.3 已覆盖 9 个正式入口，但 `首页总览` 未进入 Stage 4 catalog。复审补齐 `财务状态`、`待办事项`、`快捷操作`、`最近报告` 四个首页二级页；这只是二级页差异化补齐，不进入 Stage 5 首页任务流重建。

复审结论：

- Stage 3 的 10 个正式一级入口保持不变。
- 10 个正式一级入口均有 3–5 个二级页面。
- Stage 4 当前共有 45 个差异化二级页面。
- 二级页面拥有不同布局、主对象、主操作、空状态、错误状态和数据来源说明。
- URL/hash、state、breadcrumb、标题和 active 状态随二级入口变化。
- v0.1 兼容入口仍只作为兼容 route，不恢复为一级入口。
- Stage 4 没有引入禁用的伪造财务数据。

## 实现合同

- 二级页合同在 `PFI/web/app/pages/stage4Subpages.js` 中声明。
- `PFI/web/app/shell.js` 在启动时加载 Stage 4 pages catalog。
- 命中 Phase 4.1、Phase 4.2 或 Phase 4.3 route 时，页面更新 `URL/hash`、state、breadcrumb、标题、主对象、主操作、空状态和错误状态。
- Stage 3 的 10 个正式一级入口和兼容 route 合同保持不变。
- 未加载真实数据时只显示中文真实空态，不显示财务假值。
- Phase 4.2 页面增加数据门禁区域；门禁未通过时只显示缺口和复核动作，不生成财务结论。
- Phase 4.3 页面保留 v0.1 public alias，但 alias 只能进入归属二级页，不能重新变成一级入口。

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

## Phase 4.2 验收

验收证据：

- `PFI/reports/pfi_v023/stage_4/phase_4_2/browser_validation.json`
- `PFI/reports/pfi_v023/stage_4/phase_4_2/screenshots/consumption_subpages.png`
- `PFI/reports/pfi_v023/stage_4/phase_4_2/screenshots/sync_subpages.png`
- `PFI/reports/pfi_v023/stage_4/phase_4_2/screenshots/insights_subpages.png`

测试：

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_stage4_subpage_differentiation.py -q
```

## Phase 4.3 验收

验收证据：

- `PFI/reports/pfi_v023/stage_4/phase_4_3/browser_validation.json`
- `PFI/reports/pfi_v023/stage_4/phase_4_3/screenshots/market_research_subpages.png`
- `PFI/reports/pfi_v023/stage_4/phase_4_3/screenshots/settings_subpages.png`
- `PFI/reports/pfi_v023/stage_4/phase_4_3/screenshots/recommendations_subpages.png`

测试：

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_stage4_subpage_differentiation.py -q
```

## 明确未做

Stage 4 不做 Stage 5 首页任务流重建，不做 Stage 6 或后续功能。GitHub main 上传在 closeout commit 之后用 `git push` 和 `git ls-remote` 终端验证证明，不写成提交内的自引用事实。
