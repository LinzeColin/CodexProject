# Known gaps · ADP-S2-P02-T025

- **NOT_DEPLOYED（本任务边界内的事实，不是缺陷）**：`migration.sql` / `rollback.sql` 仅在隔离内存副本（`test-results/t025_verify.py`）上验证，**尚未应用到生产 D1（adp-mirror）**。生产落库与写入路径接线属于后续 S2 任务（T026 Replay 幂等、以及 T027+ 快照/恢复），届时须走各自的 gate 与六主题基线复验。
- **写入路径未接线**：本任务只交付「schema + 迁移 + 回滚 + 隔离验证」。`current_version_no` 的推进、append-only 版本插入、以及「只对实质变化增版本」的判定由 **T026** 实现；本任务不改 worker/D1/R2、不改抓取与六主题动效。
- **content_hash 语义待 T026 固定**：本 schema 只声明 `content_hash TEXT NOT NULL`（sha256 of substantive content），但「实质内容」的规范化与模板噪声过滤规则在 T026 定义；在此之前 `content_hash` 的口径不得被下游当作最终版。
- **artifact_keys_json 为文本 JSON 数组**：D1/SQLite 无原生数组类型，按既有 `*_json` 约定存 JSON 文本；与 R2 内容寻址键（`raw/{source}/{ver}/…`）的强一致校验留待快照任务。
- **无 FK 约束声明**：遵循现有 `schema_cloud.sql` 风格（D1 上 FK 默认不强制），`canonical_id` 关系由应用层 + 本验证脚本的 LEFT JOIN 孤儿检查保证，而非数据库级 FOREIGN KEY。
