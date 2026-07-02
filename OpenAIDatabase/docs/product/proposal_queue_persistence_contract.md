# Memory Atlas proposal queue 持久化与版本链合同

适用版本：Memory Atlas v1.1.6 Stage 3 Phase 2

状态：contract-only。本 phase 不修改运行时 UI、CSS、路由、数据生成、写回逻辑、agent apply 逻辑或长期记忆。

## 1. 目标

Stage 3 Phase 2 定义 proposal queue persistence 和版本链合同。Stage 3 Phase 1 已定义 proposal-only adjustment workspace，本 phase 进一步固定 proposal draft 如何进入本地队列、如何保留 revision、parent_proposal_id、supersedes_proposal_id、rollback_to_proposal_id 和 proposal_history。

本 phase 只定义持久化语义、schema、状态转移、安全边界和验收，不实现浏览器 localStorage、不创建真实 proposal queue、不执行 agent apply、不写 active memory、不进入 Search 2.0、Review / Summary / Iteration 或 Data Map 2.0。

## 2. 存储边界

| item | 值 | 说明 |
|---|---|---|
| `contract_id` | `proposal_queue_persistence` | 本合同的机器可读标识 |
| `storage_key` | `memory-atlas.writeback.proposals.v1` | 后续实现的本地队列键名 |
| `storage_scope` | `browser_local_only` | 仅浏览器本地草案，不上传 GitHub main |
| `queue_mutation_policy` | `append_only` | 记录追加，不静默覆盖旧 proposal |
| `apply_boundary` | `agent_or_human_apply_required` | 可交接，不表示已写入 |

队列持久化只保存 redacted proposal metadata 和用户输入的脱敏 reason。不得保存 raw/private/cookie/session/secret、本地绝对私有路径、未脱敏证据全文、record hash 或 active memory row 全量拷贝。

## 3. Queue object schema

队列对象必须包含：

```json
{
  "queue_schema_version": "memory_atlas_proposal_queue.v1",
  "storage_key": "memory-atlas.writeback.proposals.v1",
  "storage_scope": "browser_local_only",
  "queue_mutation_policy": "append_only",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "proposals": [],
  "proposal_history": []
}
```

`proposals` 保存当前可见 proposal_record。`proposal_history` 保存状态变化、supersede、reject 和 rollback_proposal 事件。两者都必须遵守 forbidden payload。

## 4. Proposal record schema

每个 `proposal_record` 至少包含：

```json
{
  "proposal_id": "string",
  "proposal_schema_version": "memory_atlas_proposal_workspace.v1",
  "revision": 1,
  "parent_proposal_id": null,
  "supersedes_proposal_id": null,
  "rollback_to_proposal_id": null,
  "parent_snapshot_id": "string",
  "target_ref": "redacted-target-ref",
  "target_type": "tier_asset",
  "target_id": "string",
  "field": "importance",
  "old_value_ref": "redacted-snapshot-ref",
  "proposed_value": "high",
  "diff_summary": "string",
  "reason": "string",
  "evidence_refs": ["redacted-evidence-id"],
  "status": "draft",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "created_by": "human_or_agent",
  "safety": {
    "direct_frontend_mutation_of_active_memory": false,
    "requires_conflict_check": true,
    "requires_agent_or_human_apply": true,
    "forbidden_payload": ["plaintext secrets", "raw conversation text", "record hashes", "local absolute paths"]
  },
  "rollback_hint": "string"
}
```

## 5. 版本链规则

`proposal_revision` 必须遵守：

1. 新 proposal 的 `revision = 1`。
2. 修改同一 proposal 时生成新 proposal_record，不覆盖旧记录。
3. 新记录的 `revision = latest.revision + 1`。
4. 新记录必须写 `parent_proposal_id`。
5. 替代旧 proposal 时写 `supersedes_proposal_id`。
6. 回滚时创建 `rollback_proposal`，写 `rollback_to_proposal_id`。
7. rollback 也是 proposal，不直接覆盖 active memory。

## 6. 状态与失败状态

允许状态：

- `draft`
- `needs_review`
- `ready_for_agent_apply`
- `rejected`
- `superseded`

失败状态必须显式可见：

- `stale_snapshot`：parent_snapshot_id 与当前 snapshot 不一致。
- `schema_mismatch`：queue_schema_version 或 proposal_schema_version 不匹配。
- `forbidden_payload`：payload 触及 raw/private/cookie/session/secret、本地绝对路径、record hash 或 active memory 全量拷贝。

出现失败状态时，proposal 不得进入 `ready_for_agent_apply`。

## 7. Agent apply 边界

queue 中的 `ready_for_agent_apply` 只表示可交接。后续 agent/human apply 必须：

1. 重新读取当前 redacted snapshot。
2. 校验 parent_snapshot_id。
3. 执行 conflict check。
4. 写 proposal history。
5. 生成 rollback proposal 或 rollback hint。
6. 需要单独 gate、单独验收和单独 Git 变更。

本 phase 不实现 agent apply，也不生成真实 apply 指令。

## 8. 与 Stage 3 Phase 1 的关系

Stage 3 Phase 1 定义工作区区域和 proposal draft schema。Stage 3 Phase 2 固定队列持久化与版本链：

- `proposal_queue` 读取 `memory-atlas.writeback.proposals.v1`。
- `proposal_diff_preview` 不能从 raw/private 重建 diff。
- `safety_review_panel` 必须读取 safety 字段。
- `rollback_panel` 必须读取 rollback_hint、parent_proposal_id 和 rollback_to_proposal_id。

## 9. 非目标

本 phase 不覆盖：

- React/CSS runtime UI。
- 浏览器截图和 Playwright 验收。
- 真实 localStorage 写入。
- agent apply CLI 或自动 apply。
- active memory 写回。
- Search 2.0。
- Review / Summary / Iteration。
- Data Map 2.0。
- GitHub main upload。

## 10. 验收

Stage 3 Phase 2 通过条件：

1. 合同覆盖 proposal_queue_persistence、storage_key、browser_local_only 和 append_only。
2. 合同覆盖 proposal_record、proposal_revision、proposal_history 和 rollback_proposal。
3. 合同覆盖 queue_schema_version、proposal_id、revision、parent_proposal_id、supersedes_proposal_id、rollback_to_proposal_id、parent_snapshot_id、target_ref、target_type、target_id、field、old_value_ref、proposed_value、diff_summary、reason、evidence_refs、status、created_at、updated_at、requires_conflict_check、requires_agent_or_human_apply 和 rollback_hint。
4. 合同覆盖 draft、needs_review、ready_for_agent_apply、rejected、superseded、stale_snapshot、schema_mismatch 和 forbidden_payload。
5. 合同明确 no direct active memory write、raw/private 边界和 agent apply 后续 gate。
6. 本 phase 不修改运行时。

## 11. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不生成真实队列，因此不需要数据回滚。
