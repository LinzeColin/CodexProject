# S12-P3 风险登记

| 风险 | 控制 |
|---|---|
| 会话模拟被误读为真实重跑 | persistent counts 固定为 0，页面与 manifest 明确 session-only |
| 高风险计划绕过确认 | 高风险按钮在二次确认前禁用，浏览器证据和 validator 双重校验 |
| 旧版本被覆盖 | 四层步骤均要求保留旧版本、追加模拟新版本 |
| 同源引用漂移 | 每份计划四层共享唯一 public-safe source anchor，容忍度为 0 分 |
| 潜在项目槽位被误读为归属 | 固定 `potential_impact_not_attribution`，不提交项目名或业务值 |
| raw/private 进入 Git | raw 与浏览器证据仅写 ignored private runtime，提交前执行安全扫描 |
