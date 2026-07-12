# 20 Agent 授权边界说明

## 结论

S08 P2 已完成。任务 ID 为 `MA-V12-S08P2`，验收 ID 为
`ACC-MA-V12-S08P2`，状态为
`phase_s08_p2_authorization_boundary_completed_pending_s08_p3`。

本阶段只做轻量授权边界：人类授权后才能 apply，raw 不可修改，proposal 需要先被人类
确认。这里不做复杂 Delegation Contract UI，不做多 agent 系统，也不执行真正的 apply。
下一步只允许进入 S08 P3。

## 人类负责什么

- 判断 proposal 是否值得 apply。
- 检查 proposal 的目标文件、风险、回滚方案和验证命令。
- 明确批准或拒绝 proposal。
- 只有批准后，proposal 才能进入 `approved_by_human`。

## Agent 负责什么

- 生成 proposal 草案。
- 标明 `proposal_id`、`target_type`、`target_files`、`validation_commands` 和
  `rollback_plan`。
- 做机器输出检查，确认 raw 不可修改、credential 不可作为目标、没有未授权 apply。
- 输出 `data/derived/agent_collaboration/agent_authorization_boundary_report.json`。

## 不能做什么

- raw 不可修改，`data/public_raw/` 不能作为 apply target。
- credentials 不能作为 transcript 或 proposal target。
- 未进入 `approved_by_human` 的 proposal 不能 apply。
- S08 P2 不实现复杂 Delegation Contract UI。
- S08 P2 不创建多 agent 系统。
- S08 P2 不生成 stage flight recorder；这留给 S08 P3。
- No GitHub main upload in this phase。

## 怎么验证

- `python scripts/atlasctl.py analyze --stage agent-authorization --dry-run`
- `python scripts/atlasctl.py audit --check agent-authorization`
- `validate:v1.2-s08-p2`

如果验证通过，说明当前系统能解释授权边界：raw 不可改、proposal 需人类授权、apply
不在本 phase 执行、复杂 Delegation Contract UI 不在本 phase 实现。
