# PFI v0.2.4 Stage 4 GitHub Main Upload

本轮只执行：`Stage 4 GitHub main upload gate`。
本轮不执行 Stage 5、不重装 app bundle、不修改 launcher C/Info.plist、
不写入、清理、删除、补造或改写真实财务数据。

## Scope

上传对象是已经完成整阶段复审的 Stage 4 package：

- `Stage 4 / Phase 4.1 - 状态机定义`
- `Stage 4 / Phase 4.2 - read model 挂链`
- `Stage 4 / Phase 4.3 - 验收`
- `Stage 4 whole-stage review - 复审并解决暴露问题`

上传前已将 `codex/pfi` rebase 到当前 `origin/main`。远端新增提交只触碰
`OpenAIDatabase/`，未触碰 `PFI/` 路径。上传后必须用 GitHub remote main
重新验证，不得用本地文档声明代替远端事实。

## Acceptance

- Stage 4 whole-stage review evidence present.
- 每个核心指标都有 `status`、`source_id`、`as_of`、`record_count` 和 `calculation_state`。
- 未加载、未挂链或失败状态不显示 `CNY 0.00`。
- `confirmed_zero` 必须携带 source、as_of、record_count、formula、confidence。
- 首页、账户、投资、消费和报告共享同一 read model status。
- 禁止 fallback 到 mock/sample/synthetic/fixture/demo/fake 财务数据。
- Stage 4 upload gate regression passes.
- `HEAD == origin/main == remote main` after push.

## Non Goals

- Stage 5 remains not started.
- App bundle reinstall is not executed.
- Launcher C and Info.plist are not changed.
- Financial data, metrics, formulas, and user data are not changed.
- No mock/sample/demo/synthetic/fixture/fake financial data is added.
