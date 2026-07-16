# Phase 8.3 风险与回滚

- 风险：自研 WCAG 扫描器误判或漏判。控制：记录 engine 和 axe 不可用事实；分别使用 computed style、CDP AX tree、真实键盘和像素回归交叉验证。
- 风险：路由变化后焦点丢失或屏幕阅读器不知页面变化。控制：键盘输入模态下焦点移到 active heading，polite/atomic route announcer 同步 canonical route。
- 风险：焦点样式被旧主题覆盖。控制：3px outline、3px offset 和 forced-colors 规则；真实键盘检查 outline 和 viewport 遮挡。
- 风险：财务/数据不可逆操作缺少预防。控制：导入确认在 preview-ready 前 disabled；持仓/设置 save/reset 与可解析描述绑定。
- 风险：44px 目标改变布局。控制：desktop/mobile 20 PNG 与 Phase 8.1 基线做 dimension 和 pixelmatch 回归，最大 diff 7.8533% 低于 12% 门限。
- 风险：trace 泄露路径或值。控制：不保留 resource body，脱敏后扫描；正式浏览器仅使用 ephemeral loopback。

回滚：revert 本 Phase 单一提交，并把 frontend release hash 同步回滚。本轮未改财务数据、数据库、模型、公式或参数，不需要数据回滚。
