# Memory Atlas v1.2 S13 P1 Proposal 状态机

任务 ID：`MA-V12-S13P1`。

验收 ID：`ACC-MA-V12-S13P1`。

状态：`phase_s13_p1_proposal_state_machine_completed_pending_s13_p2`。

Validator：`validate:v1.2-s13-p1`。

合同版本：`proposal_state_machine.v1_2_s13_p1`。

## 结论

S13 P1 已完成 Proposal 状态机。当前 phase 只固定状态、失败路径、proposal expiry 和
未授权不 apply 的机器合同；不生成 S13 P2 Diff narrator，不执行 S13 P3 apply，不执行 rollback。
下一步是 pending S13 P2。

## 状态机

主路径：

`draft → pending_human_review → approved_by_human → applying → applied → validated → committed`

失败路径：

`failed_validation → rollback_or_needs_revision`

当前 S13 P1 输出里 5 个 proposal 均处于 `pending_human_review`，均有 `expires_at`，
均保留 `validation_commands` 和 `rollback_plan_zh`，且 `apply_execution_allowed=false`。

## proposal expiry

proposal expiry 已集成到 `proposal_state_machine.v1_2_s13_p1`：

- warn: 7 days
- stale: 30 days
- archive: 90 days
- expired proposal 不能进入 `applying`

## 产物

- `机器治理/运行门禁/proposal_state_machine.v1_2_s13_p1.json`
- `data/derived/proposals/proposal_state_machine_report.json`
- `scripts/build_memory_atlas_proposal_state_machine.py`
- `scripts/atlasctl.py proposals --dry-run`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s13_p1.cjs`
- `人类可读/34_Proposal状态机说明.md`

## 边界

- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- No Diff narrator generation in S13 P1。
- No rollback execution in S13 P1。
- pending S13 P2。

## 验证

- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s13-p1`
- `python3 OpenAIDatabase/scripts/atlasctl.py proposals --dry-run`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s12-review`
- `git diff --check -- OpenAIDatabase PRODUCT.md`
- `git diff -- OpenAIDatabase/data/public_raw OpenAIDatabase/data/raw --exit-code`

Machine-readable boundary summary: Memory Atlas v1.2 S13 P1; MA-V12-S13P1; ACC-MA-V12-S13P1; phase_s13_p1_proposal_state_machine_completed_pending_s13_p2; validate:v1.2-s13-p1; proposal_state_machine.v1_2_s13_p1; S13 P1; Proposal 状态机; draft; pending_human_review; approved_by_human; applying; applied; validated; committed; failed_validation; rollback_or_needs_revision; proposal expiry; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; pending S13 P2.
