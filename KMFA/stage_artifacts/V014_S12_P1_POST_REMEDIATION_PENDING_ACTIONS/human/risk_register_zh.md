# v0.1.4 S12-P1 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 将旧 pending=12 当成当前状态 | 只引用 current Stage 11 `3/9/2/1` | controlled |
| 虚构项目归属 | 4 个项目槽位保持 unknown/null | controlled |
| 候选事件被误解为已批准 | session-only、刷新清空、approved count=0 | controlled |
| 静默改写已批准事件 | 仅允许追加反向候选，legacy chain 只作 fixture | controlled |
| 提前执行影响预览或重跑 | 页面与 manifest 均无 P2/P3 控件或执行 | controlled |
| raw/private 泄漏 | raw 四向快照、ignored private evidence、提交前安全扫描 | controlled |
