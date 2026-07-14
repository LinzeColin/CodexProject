# S18-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 合成性能被误读为生产吞吐 | 明确仅为内存 synthetic file metadata，不形成生产容量结论 | 已控制 |
| 旧固定 348ms 被当作当前事实 | 当前 elapsed 由 perf_counter_ns 实际执行产生，旧值仅作结构夹具 | 已控制 |
| 0.01 元被静默忽略 | 实际 zero-delta probe 强制 1 分 mismatch 失败并进入差异队列 | 已控制 |
| 重复导入重复写入 | 后两次新增为 0，最终状态 hash 与首次一致 | 已控制 |
| raw 被性能测试污染 | raw 仅作 ignored private 前后快照，压力输入全部在内存生成 | 已控制 |
