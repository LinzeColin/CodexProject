# Proposal 状态机说明

## 结论

S13 P1 已完成。任务 ID 为 `MA-V12-S13P1`，验收 ID 为 `ACC-MA-V12-S13P1`，
状态为 `phase_s13_p1_proposal_state_machine_completed_pending_s13_p2`，validator 为
`validate:v1.2-s13-p1`，机器合同为 `proposal_state_machine.v1_2_s13_p1`。

本阶段只做 Proposal 状态机，不做 Diff narrator，不执行 apply，不执行 rollback。下一步是
pending S13 P2。

## 状态

- `draft`
- `pending_human_review`
- `approved_by_human`
- `applying`
- `applied`
- `validated`
- `committed`
- `failed_validation`
- `rollback_or_needs_revision`

主路径是 `draft → pending_human_review → approved_by_human → applying → applied → validated → committed`。
失败路径是 `failed_validation → rollback_or_needs_revision`。

## 当前 proposal

当前报告 `data/derived/proposals/proposal_state_machine_report.json` 汇总 5 个 proposal。
这些 proposal 都来自已脱敏 derived 报告，当前均为 `pending_human_review`，没有被授权，
因此不会进入 `applying`。

proposal expiry 已接入：warn 7 days、stale 30 days、archive 90 days。过期 proposal
不能进入 `applying`。

## 边界

- No GitHub main upload。
- No remote push。
- No raw mutation。
- No proposal apply execution。
- pending S13 P2。

Machine-readable boundary summary: Memory Atlas v1.2 S13 P1; MA-V12-S13P1; ACC-MA-V12-S13P1; phase_s13_p1_proposal_state_machine_completed_pending_s13_p2; validate:v1.2-s13-p1; proposal_state_machine.v1_2_s13_p1; S13 P1; Proposal 状态机; draft; pending_human_review; approved_by_human; applying; applied; validated; committed; failed_validation; rollback_or_needs_revision; proposal expiry; No GitHub main upload; No remote push; No raw mutation; No proposal apply execution; pending S13 P2.
