# PFI v0.2.4 Stage 5 GitHub Main Upload

本轮只执行：`Stage 5 GitHub main upload gate`。
本轮不执行 Stage 6、不重装 app bundle、不修改 launcher C/Info.plist、
不写入、清理、删除、补造或改写真实财务数据。

## Scope

上传对象是已经完成整阶段复审的 Stage 5 package：

- `Stage 5 / Phase 5.1 - 首页重建`
- `Stage 5 / Phase 5.2 - 二级页面差异化`
- `Stage 5 / Phase 5.3 - 交互状态`
- `Stage 5 whole-stage review - 复审并解决暴露问题`
- `Stage 5 GitHub main upload gate`

上传前 `codex/pfi` 已在当前 `origin/main` 之上，当前上传前基线为
`HEAD=7f25524895c782fb398bb46d95f577563bdc3c36`，
`origin/main=bb195504ff65d54533ede164d2212608c6972906`，
ahead/behind 为 `4/0`。上传后必须用 GitHub remote main 重新验证，
不得用本地文档声明代替远端事实。

## Acceptance

- Stage 5 whole-stage review evidence present and pass.
- Phase 5.1、Phase 5.2、Phase 5.3 均为 candidate pass。
- 10 个正式一级入口和 45 个二级页面保留。
- 复审截图覆盖 10 个一级入口和 10 个核心二级页面。
- 静态 browser validation 不再产生可选 `/api/read-model-status` 404。
- 禁止 fallback 到 mock/sample/synthetic/fixture/demo/fake 财务数据。
- Stage 5 upload gate regression passes.
- `HEAD == origin/main == remote main` after push.

## Non Goals

- Stage 6 remains not started.
- App bundle reinstall is not executed.
- Launcher C and Info.plist are not changed.
- Financial data, metrics, formulas, and user data are not changed.
- No mock/sample/demo/synthetic/fixture/fake financial data is added.
