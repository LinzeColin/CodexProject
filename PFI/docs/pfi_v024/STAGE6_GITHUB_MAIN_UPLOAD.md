# PFI v0.2.4 Stage 6 GitHub Main Upload

本轮只执行：`Stage 6 GitHub main upload gate`。
本轮不执行 Stage 7、不重装 app bundle、不修改 launcher C/Info.plist、
不写入、清理、删除、补造或改写真实财务数据。

## Scope

上传对象是已经完成整阶段复审的 Stage 6 package：

- `Stage 6 / Phase 6.1 - 设计系统`
- `Stage 6 / Phase 6.2 - 动效反馈`
- `Stage 6 / Phase 6.3 - 触感与设置隔离`
- `Stage 6 whole-stage review - 复审并解决暴露问题`
- `Stage 6 GitHub main upload gate`

上传前 `codex/pfi` 已 rebase 在当前 `origin/main` 之上，当前上传前基线为
`HEAD=8055087c8b12001622901b888ae094034dc54cc2`，
`origin/main=b2708bff6ef632e82114d89ac886aa5fba7d809c`，
ahead/behind 为 `4/0`。上传后必须用 GitHub remote main 重新验证，
不得用本地文档声明代替远端事实。

## Acceptance

- Stage 6 whole-stage review evidence present and pass.
- Phase 6.1、Phase 6.2、Phase 6.3 均为 candidate pass。
- 默认亮色 UI、设计 token、状态色、动效反馈、触感设置隔离均通过测试。
- Review-time browser validation 生成桌面亮色、移动响应式和设置隔离截图。
- 触感反馈可关闭，只在支持设备生效；不支持设备静默降级。
- 反馈控制台不出现在业务页面。
- 禁止 fallback 到 mock/sample/synthetic/fixture/demo/fake 财务数据。
- Stage 6 upload gate regression passes.
- `HEAD == origin/main == remote main` after push.

## Non Goals

- Stage 7 remains not started.
- App bundle reinstall is not executed.
- Launcher C and Info.plist are not changed.
- Financial data, metrics, formulas, and user data are not changed.
- No mock/sample/demo/synthetic/fixture/fake financial data is added.
