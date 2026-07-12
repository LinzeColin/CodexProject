# S12-P2 风险登记

| 风险 | 控制 |
|---|---|
| 潜在项目槽位被误读为已归属项目 | 所有预览固定 `potential_impact_not_attribution`，不公开项目名或金额 |
| 高风险预览绕过二次确认 | 浏览器状态机与 validator 同时阻断 |
| 预览通过被误读为业务批准 | 当前批准/发布始终为 0，Q4/D/NO_GO 继续阻断 |
| S12-P2 误执行重跑 | 页面无 rerun 控件，manifest 保持 S12-P3=false |
| raw/private 进入 Git | raw/browser 证据仅写 ignored private runtime，提交前执行安全扫描 |
