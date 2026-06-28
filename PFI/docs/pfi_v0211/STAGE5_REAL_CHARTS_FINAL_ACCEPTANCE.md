# PFI v0.2.1.1 Stage 5 真实图表与最终验收

更新时间：2026-06-29

## 目标

本轮完成 `S5 真实图表与最终验收`。目标是把账户、投资、消费三类趋势图从正式数据层读取，并用真实浏览器验证入口、按钮、搜索、持仓、报告和设置路径。

本 Stage 不新增正式假数据，不用关键词测试替代行为验收。

## 图表数据源

| 页面 | 图表 | 正式来源 | 无数据状态 |
| --- | --- | --- | --- |
| 账户与资产 | 现金总额、净资产、总资产、总负债趋势 | `/api/trends` -> SQLite 运行读模型 | 账户趋势需要先保存持仓或导入账户流水。 |
| 投资管理 | 投资市值、总收益、未实现盈亏、现金仓位趋势 | `/api/trends` -> SQLite 持仓快照 | 投资趋势需要先保存持仓，当前不伪造收益。 |
| 消费管理 | 本月支出、预算剩余、固定支出、弹性支出、现金流预测 | `/api/trends` -> `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` | 消费趋势需要先导入真实流水，当前不伪造支出或预算。 |

当前真实消费图表读取 `8815` 条标准化支付宝流水。当前正式持仓库可以为空；为空时账户与投资显示中文空状态，不生成模拟收益。

## 前端修复

- 正式 Web Shell 不再使用硬编码数字数组作为图表回退。
- 运行 API 不可用时，趋势图只显示中文空状态。
- 旧项目验收功能面板不再暴露合成验收或测试数据路径。
- 全局搜索保留真实业务入口、真实数据数字和中文模糊搜索。

## 验收

- `build_v0211_stage5_contract()` 锁定 `/api/trends`、SQLite 和 MetaDatabase 三类真实来源。
- 账户、投资、消费趋势图读取真实数据层或显示中文空状态。
- 所有一级入口、二级入口和主要按钮需要真实浏览器 E2E 点击验证。
- 持仓编辑保存、刷新、重启和报告同步需要回归通过。
- 桌面端和移动端需要截图、console/page error 和水平溢出证据。
- 验收不是关键词测试：必须覆盖路由、状态、数据、SQLite 查询和浏览器行为。

## 本轮验证结果

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m pytest PFI/tests/test_v0211_stage5_6_final_acceptance_contract.py -q -p no:cacheprovider`：`5 passed`。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m pytest PFI/tests/test_v0211_stage0_preparation_contract.py PFI/tests/test_v0211_stage1_product_shell_contract.py PFI/tests/test_v0211_stage2_page_skeleton_contract.py PFI/tests/test_v0211_stage3_real_operation_flow_contract.py PFI/tests/test_v0211_stage4_persistence_sync_contract.py PFI/tests/test_v0211_stage5_6_final_acceptance_contract.py -q -p no:cacheprovider`：`28 passed`。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m pytest PFI/tests -q -p no:cacheprovider`：`349 passed, 729 subtests passed`。
- `node --check PFI/web/app/shell.js`：通过。
- `git diff --check -- PFI`：通过。
- 真实浏览器矩阵：10 个一级入口均可点击；每个入口验证 3 个二级入口；首页 8 个功能按钮可用；全局搜索 `8815`、`406` 可命中真实支付宝流水；`#/investment/strategy-lab` 跳转到 `#/market-research/strategy-lab`；持仓编辑写入临时 SQLite 后新开页面读回；账户趋势来源为 `SQLite 运行读模型`；消费趋势来源为 `MetaDatabase 真实支付宝流水`；设置反馈只在设置页显示；移动端横向溢出 `0px`；console/page error 为 `0`。

## 停止条件

以下任一出现，本 Stage 不通过：

- 图表仍从硬编码数组、前端缓存或测试数据派生。
- 正式 UI 出现运行边界、Task Pack、runtime、Boundary、Evidence 等开发词。
- 正式页面出现 demo/sample/synthetic/fixture/mock/fake 或测试样例数据。
- 任一一级入口、二级入口、主要按钮、搜索、上传、持仓、报告或设置不可用。
