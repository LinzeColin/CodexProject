# Phase 10.3 Risk and Rollback

- Trace/span/log 只证明 durable runtime 的执行关联、状态转换和故障恢复，不证明任何财务事实、报告或模型结论正确。
- 正式 Shell 只读取 SQLite durable-job API。poll timer 仅调度下一次读取；状态、revision、retry、error 和 progress units 均来自持久事件，不能由浏览器时间推进。
- 失败矩阵使用隔离 SQLite 与本机 loopback；canonical 私有 PFI DB 未使用，Stage 11 的 SQLite 版本、迁移、备份恢复和隐私边界未验收。
- Timeout 明确失败并使用现有 cache fallback；unsafe external-network declaration 在 runtime work 前失败。未知故障不能转为 synthetic success。
- Redaction 覆盖已登记的路径、email、secret/token、敏感字段和金额形态。新增日志字段或敏感类别必须先增加 fail-closed 行为测试。
- release manifest 只更新 frontend/backend source closure；build ID 与 version 不变。PFI.app 未安装，GitHub 未 push。
- 本轮没有读取真实财务行、输出财务值或修改 model/formula/parameter 数值；Finder、LaunchServices 和 GUI 文件操作均未使用。

Rollback：先 revert Phase 10.3 证据/治理提交，再 revert 产品提交 `9d2a8eb9f7b3e91492cdabffa9965339cd3bba2e`。本 Phase 未触碰 canonical 私有数据库、persistent production cache 或安装面；回退后停止本地进程即可恢复 Phase 10.2 状态。
