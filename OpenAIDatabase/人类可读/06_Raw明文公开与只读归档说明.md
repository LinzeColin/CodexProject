# Raw 明文公开与只读归档说明

任务 ID：`MA-V12-S03P1`。

验收 ID：`ACC-MA-V12-S03P1`。

状态：`phase_s03_p1_public_raw_path_defined_pending_s03_p2`。

S03 P1 只定义公开 raw 路径和只读完整性规则，不导入真实 transcript。

## 公开路径

- ChatGPT：`data/public_raw/chatgpt`
- Codex：`data/public_raw/codex`
- 后续其他 agent：`data/public_raw/agents/{agent_id}`

机器策略文件是 `raw_public_archive_policy.v1_2_s03_p1.json`，位于
`机器治理/同步与备份/`。

## 只读规则

- 新 raw 文件以后可以追加，规则是只追加。
- 已存在 raw 文件不能修改。
- 已存在 raw 文件不能删除。
- 已存在 raw 文件不能覆盖。
- 已存在 raw 文件 hash 变化时必须 hash drift fail。
- raw archive 永远不是 proposal apply target。

## 本 phase 不做什么

- 凭证检查在 S03 P2。
- manifest 生成在 S03 P3。
- connector 和真实同步在 S04。
- No GitHub main upload in this phase。

本页只给人类解释路径和边界，不展示机器 manifest 明细。
