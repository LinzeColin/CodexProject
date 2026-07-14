# Stage 18 整体复审回滚计划

1. 回退本 review local commit、新 review 证据和 3 个时态耦合修复。
2. 删除 ignored private runtime 中本 review 快照和诊断，不触碰 raw。
3. 恢复 S18-P3 为 current pointer，保留 P1/P2/P3 已验证证据。
4. 不执行生产恢复、连接器补偿、GitHub upload、App 重装或业务动作。
