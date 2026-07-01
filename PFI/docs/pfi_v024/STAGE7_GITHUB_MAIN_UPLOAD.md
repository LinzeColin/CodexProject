# PFI v0.2.4 Stage 7 GitHub Main Upload

本轮只执行：`Stage 7 GitHub main upload gate`。
本轮不执行 Stage 8、不重装 app bundle、不修改 launcher C/Info.plist、
不写入、清理、删除、补造或改写真实财务数据。

## Scope

上传对象是已经完成整阶段复审的 Stage 7 package：

- `Stage 7 / Phase 7.1 - 报告结构`
- `Stage 7 / Phase 7.2 - 页面展示`
- `Stage 7 / Phase 7.3 - 验收`
- `Stage 7 whole-stage review - 复审并解决暴露问题`
- `Stage 7 GitHub main upload gate`

上传前 `codex/pfi` 已 rebase 在当前 `origin/main` 之上，当前上传前基线为
`HEAD=d120486894dd1899dcbd129b8f692fe3b124099c`，
`origin/main=efff7ce03de9c7863d739492d2a4682de2ee7660`，
ahead/behind 为 `4/0`。上传后必须用 GitHub remote main 重新验证，
不得用本地文档声明代替远端事实。

## Acceptance

- Stage 7 whole-stage review evidence present and pass.
- Phase 7.1、Phase 7.2、Phase 7.3 均为 candidate pass。
- 报告中心固定 6 类报告：净资产、现金、投资、消费、现金流、数据质量。
- 每份报告保留结论、公式、参数、样本量、数据范围、置信度、缺口和复核入口。
- 数据不足时只生成阻断状态、缺口和数据质量报告，不输出完整财务结论。
- 报告不得退化成单段 AI 文本。
- Phase 7.3 浏览器验收截图 `formula_visibility.png` 存在且有效。
- 禁止 fallback 到 mock/sample/synthetic/fixture/demo/fake 财务数据。
- Stage 7 upload gate regression passes.
- `HEAD == origin/main == remote main` after push.

## Non Goals

- Stage 8 remains not started.
- App bundle reinstall is not executed.
- Launcher C and Info.plist are not changed.
- Financial data, metrics, formulas, and user data are not changed.
- No mock/sample/demo/synthetic/fixture/fake financial data is added.
