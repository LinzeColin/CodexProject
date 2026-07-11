# S16-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 固定 5/2/4 回流 | legacy 仅作历史夹具；当前项目匹配、未归集池和异常候选均为 0 | controlled |
| 结构候选被当作交易事实 | 权威行和值绑定独立计数且保持 0 | controlled |
| 候选计数与 raw 不一致 | 双次探针、processed/private 计数和 raw 快照交叉校验 | controlled |
| 无合同付款或重复付款被误报 | 仅锁定规则；无行级证据时不物化实际候选 | controlled |
| 采购或付款动作被放开 | 采购、审批、付款、银行和业务执行门禁全部为 false | controlled |
| raw/private/secret 进入 Git | 明细、名称、字段和诊断只写 ignored private runtime | controlled |
