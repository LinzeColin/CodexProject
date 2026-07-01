# PFI v0.2.4 Stage 8 Whole-Stage Review Risk and Rollback

## Risk

- 当前本地分支 ahead 3 / behind 1；远端新增提交不触碰 PFI，但 upload gate 前仍必须 rebase/同步并重新验证。
- `/Applications/PFI.app` 当前缺失；Stage 8 复审只确认 `~/Downloads/PFI.app` 是可用且指向当前 checkout 的 app 入口，不在本轮重装 app bundle。
- Stage 9 不得在 Stage 8 GitHub main upload 前启动。

## Rollback

- 本轮未修改业务前端逻辑、launcher、app bundle 或真实财务数据。
- 回滚仅需撤销 Stage 8 whole-stage review 合同、文档、状态文件和 `PFI/reports/pfi_v024/stage_8/whole_stage_review/` evidence。
- 若 upload gate 前 rebase 暴露 PFI 冲突，应停止在 upload gate，先解决冲突并重跑 Stage 8 复审相关验证。

## Stop Conditions

- 不执行 GitHub main upload。
- 不执行 Stage 9 regression freeze。
- 不重装 app bundle。
- 不写入、清理、删除、补造或改写真实财务数据。
