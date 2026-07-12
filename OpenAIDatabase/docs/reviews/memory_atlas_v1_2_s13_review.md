# Memory Atlas v1.2 S13 Review

任务 ID：`MA-V12-S13-REVIEW`。

验收 ID：`ACC-MA-V12-S13-REVIEW`。

状态：`stage_s13_review_passed_pending_s14_no_github_main_upload`。

Validator：`validate:v1.2-s13-review`。

## 结论

S13 Review 已完成。S13 P1、S13 P2、S13 P3 的阶段链满足 Proposal 授权
Apply、Diff narrator 与回滚的 stage gate。S13 只完成 proposal-only → 人类授权 →
自动 apply dry-run → validation → rollback path 的安全闭环，不代表 S14、GitHub main
upload、app reinstall 或本机深度清理已完成。下一步只允许进入 pending S14 P1。

复审未发现 critical/high 阻断项。已确认 Proposal 状态机要求人类授权后才可进入
`approved_by_human` 和 `applying`；Diff narrator 以中文解释改了什么、为什么改、影响什么、
如何验证、如何回滚，完整机器 diff 保留在治理证据文件；Apply 与回滚路径确认
`sample_unauthorized` 未授权 `FAIL_CLOSED`，`sample` 授权 dry-run 具备
`validation_after_apply` 和 rollback point，模拟 validation failure 会进入
`rollback_or_needs_revision`。

真实 pending proposal 未获人类授权前不 apply。当前真实 pending proposal applied 数为 0。

## 复审范围

| Phase | 目标 | 验收 | 复审结论 |
|---|---|---|---|
| S13 P1 | Proposal 状态机 | `validate:v1.2-s13-p1`; `ACC-MA-V12-S13P1`; `proposal_state_machine.v1_2_s13_p1` | PASS |
| S13 P2 | Diff narrator | `validate:v1.2-s13-p2`; `ACC-MA-V12-S13P2`; `diff_narrator.v1_2_s13_p2` | PASS |
| S13 P3 | Apply 与回滚 | `validate:v1.2-s13-p3`; `ACC-MA-V12-S13P3`; `proposal_apply.v1_2_s13_p3` | PASS |

## 状态机复审

S13 P1 锁定 Proposal 状态机：

`draft → pending_human_review → approved_by_human → applying → applied → validated → committed`

失败路径：

`failed_validation → rollback_or_needs_revision`

复审确认：

- proposal expiry 已集成。
- 当前 proposal 默认为 `pending_human_review`。
- 未进入 `approved_by_human` 前不会 apply。
- S13 P1 不执行 Diff narrator、proposal apply 或 rollback。
- raw 不作为 apply target。

## Diff narrator 复审

S13 P2 复审确认每个 proposal 都有中文 Diff narrator，包含：

- 改了什么。
- 为什么改。
- 影响什么。
- 如何验证。
- 如何回滚。

完整机器 diff 保留在
`机器治理/证据与日志/proposal_diffs/diff_narrator_machine_diff.v1_2_s13_p2.json`，
不进入人类首页。S13 P2 不执行 proposal apply，不执行 rollback，不修改 raw。

## Apply 与回滚复审

S13 P3 复审确认：

- `sample_unauthorized` 未授权时 `FAIL_CLOSED`，`writes_files=false`，
  `applies_proposal=false`。
- `sample` 授权 dry-run 返回 `PASS`、`would_apply=true`、
  `validation_after_apply=true`、`rollback_point_created=true`。
- `sample` 模拟 validation failure 返回 `FAIL_CLOSED`，并进入
  `rollback_or_needs_revision`。
- raw archive、public raw、private imports、credentials、cookies 和 tokens 不作为 apply
  target。
- 当前真实 pending proposal applied 数为 0。

## 边界

- No GitHub main upload。
- No remote push。
- No raw mutation。
- No app reinstall。
- No local deep clean。
- 真实 pending proposal 未获人类授权前不 apply。
- pending S14 P1。

## 验证命令

- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s13-review`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s13-p1`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s13-p2`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s13-p3`
- `python3 OpenAIDatabase/scripts/atlasctl.py proposals --dry-run`
- `python3 OpenAIDatabase/scripts/atlasctl.py proposals --view diff-narrator --dry-run`
- `python3 OpenAIDatabase/scripts/atlasctl.py apply --proposal sample_unauthorized --dry-run`
- `python3 OpenAIDatabase/scripts/atlasctl.py apply --proposal sample --dry-run`
- `python3 OpenAIDatabase/scripts/atlasctl.py apply --proposal sample --dry-run --simulate-validation-failure`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run build`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run lint`
- `python3 OpenAIDatabase/scripts/privacy_guard.py --database-dir OpenAIDatabase --scan-only`
- `python3 OpenAIDatabase/scripts/raw_archive_manifest.py audit --database-dir OpenAIDatabase`
- `git diff --check -- OpenAIDatabase`
- `git diff -- OpenAIDatabase/data/public_raw OpenAIDatabase/data/raw --exit-code`

## Machine-readable boundary summary

Memory Atlas v1.2 S13 Review; MA-V12-S13-REVIEW; ACC-MA-V12-S13-REVIEW;
stage_s13_review_passed_pending_s14_no_github_main_upload; validate:v1.2-s13-review;
S13 Review; S13 P1; S13 P2; S13 P3; proposal_state_machine.v1_2_s13_p1;
diff_narrator.v1_2_s13_p2; proposal_apply.v1_2_s13_p3; Proposal 状态机;
Diff narrator; Apply 与回滚; draft; pending_human_review; approved_by_human;
failed_validation; rollback_or_needs_revision; proposal expiry; 改了什么; 为什么改;
影响什么; 如何验证; 如何回滚; sample_unauthorized; sample; FAIL_CLOSED;
validation_after_apply; rollback point; No GitHub main upload; No remote push;
No raw mutation; 真实 pending proposal 未获人类授权前不 apply; pending S14 P1.
