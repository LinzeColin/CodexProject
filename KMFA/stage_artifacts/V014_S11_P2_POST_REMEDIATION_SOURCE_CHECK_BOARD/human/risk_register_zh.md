# S11-P2 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 12 pending 或四个已就绪状态回流 | 当前 S11-P1/S10 状态覆盖，历史动态状态禁止复用 | controlled |
| 状态颜色影响可读性 | 蓝灰和白色为主，异常只用文字徽标 | controlled |
| 点击状态没有可见结果 | 13 行逐项验证影响报告、处理规则和下一步 | controlled |
| 会话预演误写持久层 | 事件显式锁定 browser session only，raw/persistent write 均为 false | controlled |
| raw/private/secret 泄漏 | public-safe validator、Git ignore 和候选提交扫描阻断 | controlled |
