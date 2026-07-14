# S17-P1 权限与安全风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 静态角色被误读为 live 身份系统 | 明确不创建用户、凭据、身份提供方或 session | controlled |
| 未显式授权动作被放行 | deny-by-default 与 16 项授权探针 | controlled |
| 敏感材料进入公开仓库 | 15 类拒绝策略、tracked 后缀/private 扫描和 strict scan | controlled |
| 审计探针被误读为真实事件 | probe_only=true 且 persistent event write=false | controlled |
| 通知日志契约触发实际发送 | notification 仅 schema，delivery/full body=false | controlled |
| raw 被安全检查污染 | 前后及跨 phase 指纹一致，所有写动作=false | controlled |
