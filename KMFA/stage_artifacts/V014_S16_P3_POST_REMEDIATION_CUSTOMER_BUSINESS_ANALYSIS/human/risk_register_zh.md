# S16-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 固定客户信号和摘要回流 | legacy 仅作历史夹具；当前客户摘要和风险事项均为 0 | controlled |
| 结构候选被当作客户事实 | 客户、项目和值绑定独立计数并保持 0 | controlled |
| 未归属项目毛利被分配给客户 | 绑定契约要求客户、项目、期间和来源四锚点 | controlled |
| 客户摘要被当作自动排名 | 自动排名、客户联络、催收和法律决策门禁全部为 false | controlled |
| 候选计数与 raw 不一致 | 双次探针、processed/private 计数和 raw 快照交叉校验 | controlled |
| raw/private/secret 进入 Git | 明细、名称、字段、日期、金额和诊断只写 ignored private runtime | controlled |
