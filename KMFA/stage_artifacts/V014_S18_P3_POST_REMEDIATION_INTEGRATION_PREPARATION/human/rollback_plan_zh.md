# S18-P3 回滚计划

1. 回退本 phase local commit 与当前 S18-P3 公开安全证据。
2. 删除 ignored private runtime 中本 phase 快照和诊断，不触碰 raw。
3. 恢复 S18-P2 为 current pointer，保留历史 S18-P3 证据不变。
4. 不执行连接器补偿动作、生产恢复、GitHub upload、App 重装或业务动作。
