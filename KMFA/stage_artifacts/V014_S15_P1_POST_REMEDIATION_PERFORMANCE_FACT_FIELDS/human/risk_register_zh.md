# S15-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| legacy 两字段绑定状态回流 | 当前 Stage 13/14 evidence 为唯一动态事实；六字段全部人工复核 | controlled |
| 候选结构被当作绩效事实 | 权威行/值绑定和绩效事实物化独立计数且保持 0 | controlled |
| 项目成本/回款结构引用被误读为值绑定 | 结构连接与权威值绑定分栏展示 | controlled |
| 客情费率口径被自动推断 | 定义、分母、期间和权威值缺失时保持 pending | controlled |
| 绩效字段进入工资奖金计算 | S15-P2/P3、工资、奖金、薪资导出和业务动作全部阻断 | controlled |
| raw/private/secret 进入 Git | 详细探针与截图只写 ignored private runtime，公开证据仅含聚合计数 | controlled |
