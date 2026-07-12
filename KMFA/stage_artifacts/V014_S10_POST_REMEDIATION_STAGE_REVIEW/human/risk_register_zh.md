# Stage 10 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 12 pending 或 B 级状态回流 | 最新 P1/P2/P3 是唯一当前链，旧 review 仅作历史依赖 | controlled |
| 受限预览被误标为正式报告 | HTML、CSV、manifest 和 gate 均传播 D级、未放行、内部复核 | controlled |
| 浏览器控件或下载失效 | 桌面/移动视口、控制项和逐字节下载均重跑 | controlled |
| PDF、Excel 工作簿或私有 CSV 进入提交 | 禁止后缀和 changed-file scan 阻断 | controlled |
| raw/private/secret 泄漏 | fresh raw 快照、Git ignore 和公开安全扫描阻断 | controlled |
