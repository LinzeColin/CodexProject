# PFI v0.2.4 Stage 8 Phase 8.3 Risk and Rollback

## Risk

- 人工验收尚未由用户确认；本 phase 只能进入 `ready_for_user_acceptance`。
- `/Applications/PFI.app` 缺失，可能影响用户从 Applications 打开 app 的路径；`~/Downloads/PFI.app` 在 Phase 8.2 已验证指向当前 checkout。
- 如果用户在人工验收中发现路由、视觉、数据状态或报告中心问题，不能跳过 Stage 8 whole-stage review 直接进入 Stage 9。

## Rollback

- 本 phase 不修改业务前端逻辑、不修改真实财务数据、不重装 app bundle。
- 回滚仅需撤销本 phase 的合同、文档和 `PFI/reports/pfi_v024/stage_8/phase_8_3/` evidence 文件。
- 若后续要修复 `/Applications/PFI.app`，应在独立 app 入口修复轮执行并重新验证 app/localhost entry binding。

## Stop Conditions

- 用户未确认人工验收前停止在 Stage 8 Phase 8.3。
- 不执行 Stage 8 whole-stage review。
- 不执行 Stage 9。
- 不上传 GitHub main。
