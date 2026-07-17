# KMFA v1.5 S01-P2 风险登记册

| 风险 ID | 严重度 | 当前证据 | 解决 Stage | 停止条件 |
|---|---|---|---|---|
| RISK-P2-001 | CRITICAL | 无真实 App source/build/API/DB | S02、S20 | 运行对象或持久化边界不明确时不得实现业务流 |
| RISK-P2-002 | CRITICAL | 真实权威数据仍未 zero-delta | S05-S07、S23 | 任意一分未解释差异不得发布 |
| RISK-P2-003 | CRITICAL | 旧公开安全策略允许 raw/plaintext 授权例外 | S03 | 例外未废止前不得建立上传门禁 |
| RISK-P2-004 | CRITICAL | raw 保护目前主要是协议与审计 | S03 | 发现 raw 新增、修改、删除、移动立即停止 |
| RISK-P2-005 | HIGH | lineage 记录不完整 | S02、S09 | 关键金额不可追溯时不得进入报告 |
| RISK-P2-006 | HIGH | 旧静态 UI 易被误当真实产品 | S14、S23 | DOM/按钮证据不得作为验收结论 |
| RISK-P2-007 | HIGH | 权限和通知仅为策略/样例 | S15、S22 | 无真实负向 E2E 时不得发布 |
| RISK-P2-008 | HIGH | v0.1.4 App 无 tracked builder | S24 | 未建立旧 App 私有备份前不得替换 |
| RISK-P2-009 | HIGH | 多 registry 人工同步易漂移 | S13 | ID/版本不一致时阻断合并 |
| RISK-P2-010 | HIGH | S01-P1 仍 NOT_PASSED | S01-P3/Stage review | 不得把 P2 通过等同 Stage 01 通过 |
