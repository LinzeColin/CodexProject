# Memory Atlas proposal queue 持久化与版本链验收

适用版本：Memory Atlas v1.1.6 Stage 3 Phase 2

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS、不写 localStorage、不生成真实 proposal queue、不执行 agent apply。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定 proposal_queue_persistence 的本地队列、append-only 版本链、rollback proposal 和安全边界。通过本验收只表示 Stage 3 Phase 2 的合同完整，不表示运行时持久化、agent apply 或截图验收已完成。

## 2. 存储检查

必须覆盖：

| 项 | 通过标准 | 失败示例 |
|---|---|---|
| `storage_key` | 固定为 `memory-atlas.writeback.proposals.v1` | 多个隐式 key |
| `storage_scope` | 固定为 `browser_local_only` | 自动上传 GitHub main |
| `queue_mutation_policy` | 固定为 `append_only` | 静默覆盖旧 proposal |
| `proposal_queue_persistence` | 明确是本合同标识 | 与 runtime implementation 混同 |

## 3. Queue schema 检查

队列对象至少包含：

- `queue_schema_version`。
- `storage_key`。
- `storage_scope`。
- `queue_mutation_policy`。
- `created_at`。
- `updated_at`。
- `proposals`。
- `proposal_history`。

缺少任一字段即失败。

## 4. Proposal record 检查

每个 `proposal_record` 至少包含：

- `proposal_id`。
- `proposal_schema_version`。
- `revision`。
- `parent_proposal_id`。
- `supersedes_proposal_id`。
- `rollback_to_proposal_id`。
- `parent_snapshot_id`。
- `target_ref`。
- `target_type`。
- `target_id`。
- `field`。
- `old_value_ref`。
- `proposed_value`。
- `diff_summary`。
- `reason`。
- `evidence_refs`。
- `status`。
- `created_at`。
- `updated_at`。
- `created_by`。
- `requires_conflict_check` 或 safety 等价字段。
- `requires_agent_or_human_apply` 或 safety 等价字段。
- `rollback_hint`。

缺少任一字段即失败。

## 5. 版本链检查

| 规则 | 通过标准 | 失败示例 |
|---|---|---|
| `proposal_revision` | 新版本 revision = latest + 1 | 直接覆盖旧 proposal |
| `parent_proposal_id` | 修改必须引用上一版 | 无法追溯来源 |
| `supersedes_proposal_id` | 替代旧 proposal 时明确写入 | 历史链被擦除 |
| `rollback_proposal` | 回滚生成新 proposal | 直接覆盖 active memory |
| `rollback_to_proposal_id` | 回滚目标可引用 | 只写自然语言说明 |
| `proposal_history` | 记录状态变化 | 拒绝/替代后无记录 |

## 6. 状态检查

允许状态：

- `draft`
- `needs_review`
- `ready_for_agent_apply`
- `rejected`
- `superseded`

失败状态：

- `stale_snapshot`
- `schema_mismatch`
- `forbidden_payload`

任一失败状态出现时，proposal 不得进入 `ready_for_agent_apply`。

## 7. 安全检查

必须满足：

1. `direct_frontend_mutation_of_active_memory = false`。
2. `requires_conflict_check = true`。
3. `requires_agent_or_human_apply = true`。
4. forbidden payload 覆盖 plaintext secrets、raw conversation text、record hashes、local absolute paths。
5. 不保存 raw/private/cookie/session/secret、本地绝对私有路径、未脱敏证据全文或 active memory row 全量拷贝。

## 8. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | proposal queue、revision、status、rollback hint 和 safety 字段可见 |
| Tablet 768x1024 | proposal_history 可折叠但不丢失版本链 |
| Mobile 390x844 | storage key、status、reason、rollback_hint 和安全说明不溢出 |

## 9. 安全失败条件

任一情况出现即失败：

1. 合同允许前端直接修改 active memory 或长期记忆。
2. 合同要求读取或保存 raw/private/cookie/session/secret 数据。
3. 合同缺少 requires_conflict_check 或 requires_agent_or_human_apply。
4. 合同缺少 rollback_hint、parent_snapshot_id 或 parent_proposal_id。
5. 合同允许覆盖旧 proposal 而不保留 proposal_history。
6. 合同把 agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 2.0 冒充为本 phase 已完成。
7. 合同要求本 phase 启动浏览器、修改运行时 UI 或写 localStorage。

## 10. 通过条件

Stage 3 Phase 2 通过时必须有：

1. `docs/product/proposal_queue_persistence_contract.md`。
2. `docs/acceptance/proposal_queue_persistence_acceptance.md`。
3. `validate:v1.1.6-stage3-phase2`。
4. 三文件和模型参数记录中登记 `MA-V116-S3P02`。
5. Changelog 明确 No runtime UI、No raw/private data read、No direct writeback、No GitHub main upload。

## 11. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时或数据回滚。
