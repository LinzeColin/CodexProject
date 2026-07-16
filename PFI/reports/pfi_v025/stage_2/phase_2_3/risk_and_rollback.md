# Phase 2.3 风险与回滚

- 隔离风险：SQLite 副本必须位于 `0700` 临时目录、文件 mode `0600`，所有退出路径删除；cleanup 不完整即 blocked。
- 一致性风险：Git object identity 与 SQLite source fingerprint 在读取前后必须相同；任何变化均不得作为 pass evidence。
- 隐私风险：tracked evidence 只允许 aggregate/hash/status；不保存 header、row、table name、账户标识、真实文件名或绝对私密路径。
- no-fake 风险：真实输入缺失、解析失败或 count 不一致时保持 blocked，不生成财务 fixture。
- 性能风险：`tracemalloc` 只表示 Python allocation；三轮观察值不是硬 SLA。
- 治理风险：Phase 2.3 candidate 不等于 Stage 2 whole-stage review 或用户验收；Stage 3 entry 保持 false。

回滚只撤销 Phase 2.3 code/script/schema/test/docs/evidence/governance commit；不恢复、删除、搬迁或改写 source 数据。
