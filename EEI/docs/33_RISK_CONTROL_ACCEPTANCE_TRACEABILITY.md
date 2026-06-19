# 风险、控制、验收与发布门禁

## 结论

风险、验收与任务必须形成闭环：`需求/功能 -> 任务 -> Acceptance -> 测试证据 -> 风险控制 -> Release Gate`。

| 项目 | 数量 | 机器文件 |
|---|---:|---|
| 风险 | 53 | `data/risk_register.csv` |
| 验收标准 | 200 | `data/acceptance_matrix.csv` |
| 验收追踪 | 212 | `data/acceptance_traceability.csv` |
| 风险控制追踪 | 53 | `data/risk_control_traceability.csv` |
| 发布门禁 | 10 | `data/release_gate_catalog.csv` |

## 最高优先风险

1. 公开资料缺口和私营集团结构不透明。
2. 供应链递归扩展造成误判与不可读关系毛线团。
3. 金额、承诺和估值语义被错误求和。
4. 参数激活与快照切换造成跨视图版本不一致。
5. 文档、目录、代码和 GitHub Issue 发生漂移。
6. 战略信号被误读为投资收益预测。

## 发布停止条件

- 任一 P0 验收未映射任务或测试；
- 任一高风险无 owner/control/trigger；
- 权重、阈值或公式不能解释/回滚；
- 同屏混用不同数据/分数快照；
- fixture 被标为真实数据；
- 首页视觉覆盖低于 90 或核心页平均低于 80；
- reduced motion、键盘或等价列表缺失。
