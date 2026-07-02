# PFI v0.2.4 Stage 9 GitHub Main Upload

本轮只执行：`Stage 9 GitHub main upload gate`。
本轮不进入未来版本、不重装 app bundle、不修改 launcher C/Info.plist、不写入、清理、删除、补造或改写真实财务数据。

## Scope

上传对象是已经完成整阶段复审的 Stage 9 package：

- `Stage 9 / Phase 9.1 - 回归规则`
- `Stage 9 / Phase 9.2 - 交付冻结`
- `Stage 9 / Phase 9.3 - 用户验收`
- `Stage 9 whole-stage review - 复审并解决暴露问题`
- `Stage 9 GitHub main upload gate`

上传前 `codex/pfi` 已在当前 `origin/main` 之上，当前上传前基线为：

- `HEAD=7ff69041c55ce675dfcba47bb86add94a5229038`
- `origin/main=53c4cf05a79da556e1ec616fa06a73e87fb9967d`
- ahead/behind 为 `4/0`

上传后必须用 GitHub remote main 重新验证，不得用本地文档声明代替远端事实。

## Acceptance

- Stage 9 whole-stage review evidence present and pass.
- Phase 9.1、Phase 9.2、Phase 9.3 均有 evidence。
- 用户回复 `1` 已作为 Phase 9.3 确认来源记录在 whole-stage review evidence。
- 回归防线覆盖旧 UI signature、入口堆叠、假零、mock/sample/synthetic/fixture/demo/fake 财务数据、机械文案和暗色控制台默认风格。
- Phase 9.2 final evidence index present and candidate pass。
- Stage 9 upload gate regression passes。
- `HEAD == origin/main == remote main` after push。

## Non Goals

- Future version work is not started.
- App bundle reinstall is not executed.
- Launcher C and Info.plist are not changed.
- Financial data, metrics, formulas, and user data are not changed.
- No mock/sample/demo/synthetic/fixture/fake financial data is added.
