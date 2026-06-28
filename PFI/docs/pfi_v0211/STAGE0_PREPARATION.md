# PFI v0.2.1.1 Stage 0 准备轮

更新时间：2026-06-29

## 目标

完成 v0.2.1.1 Product UI Recovery 的准备锁定。当前 v0.2.1 前端优化判定为失败版本，不再把现有页面结构、跳转逻辑、默认控制台和演示式组件作为正式 UI 交付基础。

Stage 0 只做准备，不做 UI 重建。

## 本轮已完成

- 读取用户 RTF 纠偏稿：`/Users/linzezhang/Downloads/v0.2.1.1.rtf`。
- 读取受控重构 roadmap：`/Users/linzezhang/Downloads/pfi_v0.2.1_controlled_ui_rebuild_task_pack_roadmap.md`。
- 读取当前 PFI `AGENTS.md`、`HANDOFF.md`、README、三基文件和现有 v0.2.1/v0.2.2 记录。
- 建立 v0.2.1.1 来源清单：`docs/pfi_v0211/SOURCE_TASK_PACK_MANIFEST.md`。
- 建立 6-stage 路线锁：`docs/pfi_v0211/ROADMAP_LOCK.md`。
- 建立机器可读合同：`src/pfi_v02/stage_v0211_ui_recovery.py`。
- 建立 Stage 0 合同测试：`tests/test_v0211_stage0_preparation_contract.py`。
- 建立产品上下文：`PRODUCT.md`。

## Stage/Phase 纠偏

用户最新口径：roadmap 把 Stage 和 Phase 的母子关系搞反。v0.2.1.1 的执行层级改为：

1. Stage 是 pursuing goal 的顶层 run gate。
2. Phase 和 Task 是 Stage 内的子项。
3. 每次 run work 最多完成 1 个 Stage。
4. 本轮只完成 `V0211-S0-T01`。

## 6 个 Stage

| Stage | 名称 | 状态 |
| --- | --- | --- |
| S0 | 准备轮：失败冻结与执行锁 | 本轮完成 |
| S1 | 产品壳与路由 | 未开始 |
| S2 | 页面骨架与去 AI 化 | 未开始 |
| S3 | 真实操作流 | 未开始 |
| S4 | 持久化与同步 | 未开始 |
| S5 | 真实图表与最终验收 | 未开始 |

## Stage 0 禁止修改范围

- 不修改 `PFI/web/index.html`。
- 不修改 `PFI/web/app/shell.js`。
- 不修改 `PFI/src/pfi_os/app/streamlit_app.py`。
- 不刷新 app 入口。
- 不清理缓存或删除文件。
- 不提前做导航、页面、上传、持仓、图表、报告。

## 已锁定的下一轮默认

Stage 1 默认按 RTF 最新稿执行：

- 主导航 10 个正式入口：`首页总览`、`账户与资产`、`账本流水`、`投资管理`、`消费管理`、`数据源与上传`、`建议与复盘`、`报告与洞察`、`市场与研究`、`设置`。
- 旧入口只作为别名，不作为同级主导航。
- 策略实验室只有一个真实页面，默认位置为 `市场与研究 > 策略实验室`。

如果用户下一轮要求改回 Markdown roadmap 的 9 个入口，必须先更新 Stage 1 合同，再动 UI。

## 验证命令

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject/PFI
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v0211_stage0_preparation_contract.py -q -p no:cacheprovider
git diff --check -- PFI
```

## Stage 0 停止条件

以下任一发生，Stage 0 不允许通过：

- 继续声明当前 v0.2.1 前端优化是正式 UI 完成状态。
- 修改正式 Web Shell。
- 把 Stage 1-5 提前塞进 Stage 0。
- 继续以关键词、marker、函数名测试代替后续真实浏览器行为验收。
- 使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为正式页面依据。
