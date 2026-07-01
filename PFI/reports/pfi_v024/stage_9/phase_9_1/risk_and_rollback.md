# Stage 9 Phase 9.1 Risk And Rollback

## Scope

本轮只建立 Stage 9 Phase 9.1 regression guardrails。未修改 app bundle、launcher、业务 UI runtime、财务数据、指标公式或真实用户数据。

## Risks

- Guardrail 过宽会把代码 API 或报告/设置中的合法参数说明误判为旧 UI。
- Guardrail 过窄会漏掉旧 UI signature、入口堆叠、假零或 mock 财务数据回归。
- Phase 9.1 只建立规则，不代表 Stage 9 交付冻结或用户验收完成。

## Rollback

- 删除本轮新增的 `stage_v024_stage9_regression_freeze.py`、`test_v024_stage9_phase91_regression_guardrails.py`、`STAGE9_REGRESSION_FREEZE.md` 和 `reports/pfi_v024/stage_9/phase_9_1/`。
- 回退 README、HANDOFF、RUN_CONTRACT、CHANGELOG 和三基文件中的 Stage 9.1 状态更新。
- 重新运行 Stage 8 upload 和 whole-review 回归，确认 Stage 8 状态未被破坏。

## Stop Rule

若 guardrail 回归失败，回到对应 Stage 或对应 runtime 文件修复；不得用 Phase 9.2 closeout 或 README 文案覆盖失败。
