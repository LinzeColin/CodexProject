# PFI v0.2.3 Stage 1-3 Group Review

## Scope

本文件覆盖第二阶段第一组整体复审：Stage 1、Stage 2、Stage 3。
本轮按用户补充要求对标
`/Users/linzezhang/Downloads/pfi_v023_phase1_human_product_experience_preview.html`，
只复审入口一致性、真实数据状态机与非假零门禁、10 个一级入口与真实路由系统。

本轮不进入 Stage 4-11 分组复审，不执行最终项目级整体 closeout，不清理用户数据。

## Preview Benchmark

对标原型提供的 Stage 1-3 体验基准：

- 10 个一级入口固定，包含 `市场与研究`。
- 旧入口只作为兼容 route、二级入口或命令入口。
- 首页缺少真实账户、现金、持仓数据时显示状态文案，不显示 `CNY 0.00`。
- 本机真实支付宝流水可用时，消费和待复核指标保留真实读数。
- 设置、命令面板和验收/说明抽屉存在，但不能污染业务页面。

截图和 DOM 证据保存在：
`PFI/reports/pfi_v023/group_reviews/stage_1_3/preview_benchmark/`。

## Finding Fixed

复审发现：

- 当前 localhost app 入口和当前 `PFI/web/index.html` 已保持 10 个一级入口。
- localhost iframe 内存在 `PFI_STAGE1_ENTRY_METADATA`，Stage 1 当前 app 入口绑定有效。
- Stage 2/6 的机器 evidence 已记录 `净资产`、`现金余额`、`投资市值`
  为 `not_mounted` 且 `value=null`。
- 但前端 runtime read model 把缺少账户/持仓数据的 `0` 当作可显示财务数值，
  导致首页显示 `CNY 0.00`，与 preview 和非假零门禁冲突。

修复：

- `PFI/web/app/shell.js` 新增真实账户/持仓 read model 存在性判断。
- `formatCnyAmount()` 和 `toCnyAmount()` 不再把 `null`、`undefined` 或非数值转换为 0。
- 只有真实数值 0 才显示 `CNY 0.00`；缺失账户/现金/持仓数据显示 `暂无真实数据`。

## Evidence

- Group review evidence：
  `PFI/reports/pfi_v023/group_reviews/stage_1_3/evidence.json`
- Review audit：
  `PFI/reports/pfi_v023/group_reviews/stage_1_3/review_audit.json`
- Preview benchmark：
  `PFI/reports/pfi_v023/group_reviews/stage_1_3/preview_benchmark/comparison_raw.json`
- Terminal log：
  `PFI/reports/pfi_v023/group_reviews/stage_1_3/terminal.log`

## Validation

本轮最小验证集：

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_stage2_data_state_machine.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_stage1_app_entry_bundle_contract.py PFI/tests/test_v023_stage3_navigation_routes.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_regression.py -q
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/shell.js
```

本轮完整验证集在最终 evidence 写入后执行并记录。

## Remaining Work

第二阶段仍需继续：

- Stage 4-6 分组整体复审。
- Stage 7-9 分组整体复审。
- Stage 10-11 分组整体复审。
- 第三阶段 v0.2.3 项目级整体复审、同步 GitHub、备份和非必要文件清理。
