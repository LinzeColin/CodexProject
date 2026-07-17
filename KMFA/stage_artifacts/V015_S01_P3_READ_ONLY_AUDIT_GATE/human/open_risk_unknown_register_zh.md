# KMFA v1.5 S01-P3 开放风险与未知项

## 汇总

| 指标 | 数量 |
|---|---:|
| 总风险 | 24 |
| P0 / P1 | 18 / 6 |
| FIELD | 4 |
| DATA_SOURCE | 5 |
| ACCESS | 4 |
| RUNTIME_DEPENDENCY | 6 |
| UI_BREAKPOINT | 5 |
| P0 无 owner/Stage/stop | 0 |
| 已关闭风险 | 0 |

全部条目状态均为 `OPEN_WITH_PLAN`。完整机器表见 `machine/open_risk_unknown_register_public_safe.csv`。

## 最高优先级停止线

1. **运行对象**：真实 App/source/build/API/DB/persistence 未建立前，不得实现业务流；静态页面不得替代 runtime。
2. **raw 与公开安全**：出现 raw 写删改移覆盖，或旧 owner raw/plaintext 上传例外仍存在时立即停止。
3. **黄金数据**：权威源未锁定或任意一分差异未解释时保持 NO_GO。
4. **真实身份权限**：无认证、最小权限及跨角色/跨主体负向 E2E 时不得开放业务操作。
5. **旧 UI**：新 IA、设计系统和用户语言未锁定前，不得继承旧静态页面验收状态；按钮能点不构成证据。
6. **测试与发布**：并发、故障、浸泡、恢复、可访问性和静默错误矩阵未完成时不得发布。
7. **远端漂移**：GitHub main 已外部移动；未重新获取、审查并安全合并最新 main 前，不得执行最终上传或 App 替换。

## Owner 语义

负责人使用角色而非虚构个人姓名。每条风险均绑定唯一 owner role、S02-S24 解决 Stage、可执行停止条件、需求/能力 ID 和现有证据。

风险计划完整只表示 P3-T02 输出合格，不表示风险已解决，也不改变 `RUNTIME_OBJECT_MISSING`、P1 NOT_PASSED 或 Stage 01 NO_GO。
