# S18-P3 OpMe 轻入口方案

- 集成模式：入口链接与状态索引。
- 耦合等级：轻入口。
- 入口面：read_only_entry, report_index, run_status, handoff_link。
- 交换内容仅限公开安全状态、报告索引、交接指针和 validator 命令指针。
- 不共享数据库、不共享业务运行时、不混合敏感数据，OpMe 不控制 KMFA 业务逻辑。
