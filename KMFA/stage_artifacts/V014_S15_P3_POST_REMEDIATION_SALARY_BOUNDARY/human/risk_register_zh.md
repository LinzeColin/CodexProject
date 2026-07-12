# S15-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 合成项目读取行回流 | 4 条读取行和 16 个复核引用只作历史夹具 | controlled |
| 接口契约被误读为 live 集成 | API、connector、导出、同步和外部写入全部为 false | controlled |
| 结构草案被用于工资奖金 | 事实行、读取记录和薪资数值均为 0 | controlled |
| 人工边界被自动化绕过 | 四个检查点均必须人工且未执行 | controlled |
| raw/private/secret 进入 Git | 快照、诊断与截图只写 ignored private runtime | controlled |
