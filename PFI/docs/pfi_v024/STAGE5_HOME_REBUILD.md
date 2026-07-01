# PFI v0.2.4 Stage 5 Phase 5.1 - 首页重建

## Scope

本轮只执行 `Stage 5 / Phase 5.1 - 首页重建`。

不执行：

- Phase 5.2 二级页面差异化
- Phase 5.3 交互状态
- Stage 5 whole-stage review
- GitHub main upload

## Goal

首页从“功能入口/操作面板”改为人类任务流首页，只回答六个核心问题：

1. 钱：现在能确认多少钱。
2. 位置：钱和状态来自哪里。
3. 变化：最近真实记录发生了什么。
4. 问题：哪些指标被真实数据状态阻断。
5. 下一步：我现在该处理什么。
6. 依据：这些判断来自哪些真实来源。

## Implementation

- `PFI/web/app/pages/home.js` 新增 `PFI_V024_STAGE5_HOME` API。
- 新增 `buildV024Stage5Phase51Contract()`，锁定本轮只做 Phase 5.1。
- 新增 `buildV024Stage5Phase51HomeViewModel()`，读取 Stage 4 的 `read_model_status` 和 `data_state.js`，生成六问首页、数据状态卡和下一步任务流。
- `PFI/web/index.html` 新增六问首页区，并加载 `./app/pages/home.js`。
- `PFI/web/app/shell.js` 优先使用 v0.2.4 首页 API，并把 `#pfi-read-model-status` 传给首页模型。
- 默认首页移除 `功能面板 / PFI 功能入口 / 功能已准备 / 进入操作面板` 机械层文案。
- `PFI/web/styles.css` 为六问区增加响应式样式。

## Data Trust

本轮只读取已有 Stage 4 read model status：

- 数据根：`MetaDatabase/PFI`
- 记录数：`8815`
- as of：`2026-06-03`
- 消费总流出：`CNY 1,727,278.37`
- 净资产、现金余额、投资市值：保持 `source_missing`，不显示 `CNY 0.00`

未写入、清理、删除、补造或改写用户真实财务数据。
未新增 mock/sample/synthetic/fixture/demo/fake 财务数据。

## Validation

本 phase 的验证锚点：

```bash
node --check PFI/web/app/pages/home.js
node --check PFI/web/app/shell.js
python3 -m pytest PFI/tests/test_v024_stage5_phase51_home_rebuild.py -q
```

完整验证记录见：

- `PFI/reports/pfi_v024/stage_5/phase_5_1/evidence.json`
- `PFI/reports/pfi_v024/stage_5/phase_5_1/terminal.log`

