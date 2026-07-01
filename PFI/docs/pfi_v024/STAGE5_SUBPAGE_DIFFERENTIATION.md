# PFI v0.2.4 Stage 5 Phase 5.2 - 二级页面差异化

## Scope

本轮只执行 `Stage 5 / Phase 5.2 - 二级页面差异化`。

不执行：

- Phase 5.3 交互状态
- Stage 5 whole-stage review
- GitHub main upload

## Goal

把既有二级页面目录提升为 v0.2.4 Stage 5 的显式页面合同，证明每个正式一级入口都不是模板克隆：

- 每个一级入口至少 3 个二级页面。
- 每个二级页面的 URL、state、title、layout、primary action、data object 不同。
- 页面目录与 Stage 3 secondary routes 对齐，没有孤儿页面或缺失 route。
- shell runtime 优先使用 `PFI_V024_STAGE5_PAGES`。

## Implementation

- 新增 `PFI/web/app/pages/stage5Subpages.js`。
- `stage5Subpages.js` 从既有真实页面目录生成 `PFI_V024_STAGE5_PAGES`，不复制数据、不造新财务事实。
- `PFI/web/index.html` 显式加载 `stage4Subpages.js`、`stage5Subpages.js`、`home.js` 后再加载 `shell.js`。
- `PFI/web/app/shell.js` 增加 `loadStage5SubpageCatalog()`，并在渲染二级页时优先读取 v0.2.4 Stage 5 catalog。
- `PFI/src/pfi_os/app/streamlit_app.py` 同步内联 `stage5Subpages.js`，避免 app bundle 与静态 HTML 漂移。

## Route Validation

当前验证结果：

- official primary entries: `10`
- total subpages: `45`
- minimum subpages per primary entry: `4`
- missing workspaces: `0`
- workspaces below minimum: `0`
- duplicate route aliases: `0`
- duplicate state keys: `0`
- missing Stage 3 secondary routes: `0`
- orphan Stage 5 routes: `0`
- title-only clone groups: `0`

机器可读结果见：

- `PFI/reports/pfi_v024/stage_5/phase_5_2/route_validation.json`

## Data Trust

本轮不写入、清理、删除、补造或改写用户真实财务数据。
本轮不新增 mock/sample/synthetic/fixture/demo/fake 财务数据。

## Validation

```bash
node --check PFI/web/app/pages/stage5Subpages.js
node --check PFI/web/app/shell.js
python3 -m pytest PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py -q
```

