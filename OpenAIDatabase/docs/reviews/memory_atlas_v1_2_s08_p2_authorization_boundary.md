# Memory Atlas v1.2 S08 P2 Agent Authorization Boundary

## 结论

S08 P2 已完成。任务 ID 为 `MA-V12-S08P2`，验收 ID 为
`ACC-MA-V12-S08P2`，状态为
`phase_s08_p2_authorization_boundary_completed_pending_s08_p3`。

本 phase 将授权边界落成轻量机器配置和输出检查，而不是复杂 Delegation Contract UI。
核心规则是：raw 不可修改，proposal 只能在人类授权后才能 apply，授权状态必须显式进入
`approved_by_human`。当前 S08 P2 不执行 proposal apply，不创建多 agent 系统，
不生成 stage flight recorder；运行证据留给 pending S08 P3。

No GitHub main upload in this phase。

## 产物

- `机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json`
- `scripts/build_memory_atlas_agent_authorization.py`
- `scripts/atlasctl.py`
- `data/derived/agent_collaboration/agent_authorization_boundary_report.json`
- `人类可读/20_Agent授权边界说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p2.cjs`
- `tests/test_s08p2_agent_authorization.py`

## 授权边界

S08 P2 固定的授权边界如下：

- raw 不可修改，`data/public_raw/`、`data/raw/`、`data/raw_encrypted/` 等路径不能成为 apply target。
- credentials 不是 transcript，credential-like target 不允许进入 proposal apply。
- proposal 必须包含 `proposal_id`、`target_type`、`target_files`、`approval`、
  `validation_commands` 和 `rollback_plan`。
- proposal state machine 必须经过 `pending_human_review`，只有人类批准后才能进入
  `approved_by_human`。
- 当前 phase 只生成机器检查和派生报告，不执行 proposal apply；实际 apply 自动化延后到 S13。
- 不实现复杂 Delegation Contract UI；现阶段只需要机器配置、输出检查和中文解释。

## 输出检查

`agent_authorization_boundary_report.json` 记录 4 个机器输出检查：

- `S08P2-CHECK-001`：raw 不可修改，raw 永远不能成为 apply target。
- `S08P2-CHECK-002`：proposal apply 前必须有人类授权，授权状态必须包含
  `approved_by_human`。
- `S08P2-CHECK-003`：本 phase 不执行 proposal apply，只定义边界。
- `S08P2-CHECK-004`：不创建复杂 Delegation Contract UI，不创建多 agent 系统。

每个检查都包含中文解释和 evidence refs。该输出可由
`python scripts/atlasctl.py audit --check agent-authorization` 验证。

## 验收方式

- `python scripts/atlasctl.py analyze --stage agent-authorization --dry-run`
- `python scripts/atlasctl.py audit --check agent-authorization`
- `validate:v1.2-s08-p2`
- `ACC-MA-V12-S08P2`

验收通过条件：

- `agent_authorization_boundary_report.json` 存在且状态为
  `phase_s08_p2_authorization_boundary_completed_pending_s08_p3`。
- `human_approval_required=true`。
- `current_phase_executes_apply=false`。
- `raw_apply_target_allowed=false`。
- `proposal_apply_execution=false`。
- `complex_delegation_contract_ui=false`。
- `stage_flight_recorder=deferred_to_s08_p3`。

## 停止条件

遇到以下情况必须停止：

- 试图修改、覆盖、删除或重写 raw。
- 在没有人类授权状态 `approved_by_human` 的情况下 apply proposal。
- 在 S08 P2 中实现复杂授权框架、复杂 Delegation Contract UI 或多 agent 系统。
- 在 S08 P2 中生成 stage flight recorder。
- 在所有 v1.2 stage 完成前上传 GitHub main 或创建远端开发分支。

## 下一步

下一步只允许进入 pending S08 P3。S08 P3 的范围是 lightweight stage flight recorder。
本文件不代表 S08 Review、S09、最终 GitHub main 上传、app 重装或本机深度清理已经完成。
