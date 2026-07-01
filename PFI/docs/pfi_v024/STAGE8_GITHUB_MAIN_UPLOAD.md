# PFI v0.2.4 Stage 8 GitHub Main Upload

本轮只执行：`Stage 8 GitHub main upload gate`。
本轮不执行 Stage 9、不重装 app bundle、不修改 launcher C/Info.plist、不写入、清理、删除、补造或改写真实财务数据。

## Scope

上传对象是已经完成整阶段复审的 Stage 8 package：

- `Stage 8 / Phase 8.1 - 自动验收`
- `Stage 8 / Phase 8.2 - 截图验收`
- `Stage 8 / Phase 8.3 - 人工验收`
- `Stage 8 whole-stage review - 复审并解决暴露问题`
- `Stage 8 GitHub main upload gate`

上传前 `codex/pfi` 已 rebase 在当前 `origin/main` 之上，当前上传前基线为：

- `HEAD=8196fcbc129282615d8e4983142c3343eef709cf`
- `origin/main=a508d5e547ce6a0ecc7277c5907d52d8579ff8aa`
- ahead/behind 为 `4/0`

上传后必须用 GitHub remote main 重新验证，不得用本地文档声明代替远端事实。

## Acceptance

- Stage 8 whole-stage review evidence present and pass.
- Phase 8.1、Phase 8.2、Phase 8.3 均有 evidence。
- 用户回复 `1` 已作为人工验收通过来源记录在 whole-stage review evidence。
- 10 个正式一级入口固定，`市场与研究` 是正式一级入口。
- 自动验收 route click、entry version、data state、report center 均 pass。
- 截图验收覆盖 app、localhost、10 个一级入口、移动端响应式和 desktop all pages。
- app/localhost bundle hash 一致，`~/Downloads/PFI.app` 指向当前 checkout。
- 禁止 fallback 到 mock/sample/synthetic/fixture/demo/fake 财务数据。
- Stage 8 upload gate regression passes.
- `HEAD == origin/main == remote main` after push.

## Non Goals

- Stage 9 remains not started.
- App bundle reinstall is not executed.
- Launcher C and Info.plist are not changed.
- Financial data, metrics, formulas, and user data are not changed.
- No mock/sample/demo/synthetic/fixture/fake financial data is added.
