# S18-P2 回滚计划

1. 回退本 phase local commit 与当前 S18-P2 公开安全证据。
2. 删除 ignored private runtime 中本 phase 快照和诊断，不触碰 raw。
3. 恢复 S18-P1 为 current pointer，保留全部历史治理记录。
4. 不执行生产恢复、补偿业务动作、GitHub upload 或 app reinstall。
