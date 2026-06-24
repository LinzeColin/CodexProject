# 安全、并发与副作用最小基线

## 信任边界

1. 论文、网页、PDF、报告和元数据均为 `UNTRUSTED_DATA`。
2. 模型只产生结构化建议，不直接写仓库、发邮件、恢复数据库或执行命令。
3. 执行层只接受 Schema 合法、来源可追踪、策略允许的动作。
4. 用户公开画像不等于凭据可公开；密码、Token、SMTP 密钥和私钥永不入库/日志。

## 外部副作用

- 邮件：事务发件箱 + 唯一 `mail_key` + immutable revision + lease/fencing + 稳定 Message-ID。
- 文件：staging → validate → fsync → atomic replace；manifest 用真实文件 SHA-256。
- 恢复：根目录约束 → 临时目标 → SQLite/Schema/哈希检查 → 原库预备份 → 原子切换。
- Scheduler：结构化平台适配器，不拼接 shell；安装、状态、卸载均有 receipt。

## 并发原则

- 不承诺网络层 exactly-once；采用 at-least-once transport + application idempotency。
- 所有 claim/transition 带 `row_version` 与 `fencing_token`。
- 过期 worker 永远不能提交新状态。
- M4 水位线必须绑定同一 `cycle_id`。
