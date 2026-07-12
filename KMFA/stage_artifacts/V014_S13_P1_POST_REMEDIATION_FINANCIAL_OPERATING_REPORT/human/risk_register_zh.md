# S13-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 结构接入被误读为数值接入 | 每个主题显示结构已接入、数值未证明；raw value bound=0/4 | controlled |
| 历史 12 pending 或 B 级样板回流 | 历史产物只作 policy fixture，当前状态仅取 Stage 12 post-remediation review | controlled |
| 初稿被当成正式报告 | D/NO_GO、formal=false、decision basis=false 在页面和 manifest 双重锁定 | controlled |
| 现金或贷款状态触发业务动作 | cash forecast、loan action、payment/bank operation 全部 false | controlled |
| raw/private/secret 进入 Git | raw 快照与对齐诊断只写 ignored private runtime，公开证据仅聚合计数 | controlled |
