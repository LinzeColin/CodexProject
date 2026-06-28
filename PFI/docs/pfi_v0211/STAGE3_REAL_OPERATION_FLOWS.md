# PFI v0.2.1.1 Stage 3 真实操作流

更新时间：2026-06-29

## 目标

本轮只完成 `S3 真实操作流`。目标是把 Stage 2 的中文页面骨架推进到可点击、可反馈、可复核的正式操作路径：

- 数据源与上传：上传中心、解析预览、字段映射、确认入库、待复核队列。
- 账本流水：账本筛选、分类选择、保存复核、导出流水。
- 投资管理：持仓编辑表单、未提交草稿标识、保存修改入口。
- 设置：设置页内保存设置、恢复默认和状态反馈。

## 最小范围

- 修改 `PFI/web/index.html` 和 `PFI/web/app/shell.js`。
- 更新 `PFI/src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 3 合同。
- 新增 `PFI/tests/test_v0211_stage3_real_operation_flow_contract.py`。
- 同步 `README.md`、`HANDOFF.md`、`CHANGELOG.md` 和三基文件。

## 操作流

| 操作流 | 入口 | 本轮完成 | 空状态和边界 |
| --- | --- | --- | --- |
| 上传与导入 | 数据源与上传 | 选择文件、解析预览、字段映射提示、确认入库状态、待复核入口 | 未选择真实文件时提示“请先选择真实文件”，不制造记录数 |
| 账本复核与导出 | 账本流水 | 筛选、分类选择、保存复核、导出当前表格 | 无真实流水时导出空表头，不生成虚构流水 |
| 持仓编辑 | 投资管理 > 持仓 | 持仓表单、未提交草稿标识、保存按钮、恢复默认 | 浏览器缓存只允许明确标注的未提交草稿；生产保存必须走本机服务 |
| 设置保存 | 设置 | 账户偏好、主题语言、保存设置、恢复默认、保存状态 | 设置操作只在设置页显示，业务页不默认展示反馈控制台 |

## 非目标

- 不声明 Stage 4 持久化与同步完成。
- 不声明 Stage 5 真实图表与最终验收完成。
- 不新增测试数据、样例流水、模拟持仓或虚构财务事实。
- 不把生产保存写进 `localStorage`、`sessionStorage` 或 `IndexedDB`。
- 不用 toast 代替页面状态、表格、摘要或状态条反馈。

## 验收

本 Stage 的验收条件：

- `build_v0211_stage3_contract()` 存在并锁定 `V0211-S3-T01`。
- 上传、账本、持仓、设置四条操作流都有 HTML 状态面板和 JS 行为函数。
- `保存持仓修改` 外层路径不调用浏览器缓存生产保存；后端保存仍走 `/api/holdings`。
- 正式默认可见文本不出现开发者词或测试/模拟数据污染。
- 浏览器点击一级入口、二级入口和主要功能按钮后，页面状态有中文反馈。

## 本轮验证结果

- Stage 3 目标测试：`4 passed`。
- Stage 0/1/2/3 合同回归：`19 passed`。
- Stage 3 相关前端回归：`41 passed`。
- 完整 PFI 测试：`340 passed, 729 subtests passed`。
- Web Shell 语法：`node --check PFI/web/app/shell.js` 通过。
- `git diff --check -- PFI`：通过。
- Chrome headless 静态浏览器矩阵：`17 pass / 0 fail`，console error `0`，exception `0`。
- 浏览器证据：`/tmp/pfi_v0211_stage3_browser/summary.json`、`/tmp/pfi_v0211_stage3_browser/desktop.png`、`/tmp/pfi_v0211_stage3_browser/mobile.png`。

本轮完成后，下一轮只能进入 `S4 持久化与同步`，不能提前声明 `S5 真实图表与最终验收` 完成。
