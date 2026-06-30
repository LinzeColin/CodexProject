# PFI v0.2.4 Stage 3 GitHub Main Upload

本轮只执行：`Stage 3 GitHub main upload gate`。
本轮不执行 Stage 4、不重装 app bundle、不修改 launcher C/Info.plist、
不修改真实财务数据逻辑。

## Scope

上传对象是已经完成整阶段复审的 Stage 3 package：

- `Stage 3 / Phase 3.1 - 导航合同`
- `Stage 3 / Phase 3.2 - 路由实现`
- `Stage 3 / Phase 3.3 - 导航验收`
- `Stage 3 whole-stage review - 复审并解决暴露问题`

上传前已将 `codex/pfi` rebase 到当前 `origin/main`，远端新增提交未触碰
`PFI/` 路径。上传后必须用 GitHub remote main 重新验证，不得用本地文档声明
代替远端事实。

## Acceptance

- Stage 3 whole-stage review evidence present.
- Official primary entries remain exactly 10.
- `市场与研究` remains the 9th formal primary entry.
- v0.1 entries remain aliases or redirects, not peer primary entries.
- Real browser navigation validation passes.
- v0.2.4 regression through Stage 3 upload gate passes.
- v0.2.3 Stage 3 navigation compatibility passes.
- `HEAD == origin/main == remote main` after push.

## Non Goals

- Stage 4 remains not started.
- App bundle reinstall is not executed.
- Launcher C and Info.plist are not changed.
- Financial data, metrics, formulas, and user data are not changed.
- No mock/sample/demo/synthetic/fixture/fake financial data is added.
