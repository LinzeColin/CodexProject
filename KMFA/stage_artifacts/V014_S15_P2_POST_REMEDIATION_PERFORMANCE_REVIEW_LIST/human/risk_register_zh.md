# S15-P2 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 合成项目行回流 | 4 条事实行和 16 条事项只作历史夹具，当前行数锁为 0 | controlled |
| 空表被误读为已完成绩效 | 明示 Q4 / D / NO_GO，事实行与实际异常项目均为 0 | controlled |
| 字段事项被误读为项目异常 | 六项均标记字段级且不含 project_ref | controlled |
| 复核清单进入工资奖金 | 绩效分数、工资、奖金、薪资导出全部阻断 | controlled |
| raw/private/secret 进入 Git | 快照、诊断与截图只写 ignored private runtime | controlled |
