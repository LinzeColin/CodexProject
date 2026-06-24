# 可恢复自动运行与后台生命周期合同

```text
STOPPED
→ STARTING（预检）
→ RECOVERING（临时文件/outbox/inflight/残锁对账）
→ LEADER（租约与 fencing）
→ RUNNING
→ DRAINING（停止领取新任务）
→ CHECKPOINTING（数据库/outbox/runtime receipt）
→ CLEANING（仅清理 rebuildable/temp）
→ STOPPED（释放租约并记录退出）
```

## 自动唤醒

- 平台适配器：launchd/systemd/Windows Task Scheduler。
- 安装默认不启用真实 SMTP；首次只跑 dry-run self-test。
- 每次触发先计算唯一 cycle_id，重复触发只附着到已有 cycle。

## 自动关闭

- 信号/超时触发 DRAINING；禁止直接终止并丢弃状态。
- 关闭 receipt 必须包含：inflight、outbox、checkpoint、cleanup、backup、lease release。
- 超过 grace period 时将剩余任务安全 requeue，再退出非零码。

## 缓存清理

| 类别 | 自动清理 |
|---|---|
| 原始证据、Claim、数据库、已发布报告 | 永不 |
| 可重建全文/模型缓存 | TTL + 容量 + LRU |
| staging/temp | 发布成功后或启动 reconciliation 时 |

任何清理先路径白名单、符号链接检查、dry-run 计数，再执行并写删除账本。
