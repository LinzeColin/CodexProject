# Phase 8.3 缺陷记录

当前 open blocking/important defect：`0`。

已整改：

1. 初始自研 contrast scanner 未正确解析 Chromium `color(srgb …)` 序列化，产生误报；补齐 sRGB 解析后只保留真实失败。
2. 旧 v0.2.1 暗色反馈卡文字和背景规则串入 Phase 8 亮色 Shell，造成 3 类真实对比度问题；已由 Phase 8.3 高优先级亮色规则修复，20 路由复扫为 0 failure。
3. 导入确认初始可点击但运行时才拒绝无预览请求；已改为预览通过前显式 disabled，并为 5 个财务/数据控制补齐错误预防描述。

限制：本地依赖没有 `axe-core`，因此没有声称 axe pass；采用可复现 WCAG 2.2 AA contrast/target/name/structure + CDP AX + keyboard 实测。用户主观质感确认和整阶段独立审查仍待下一 run。

执行环境事件（非产品缺陷）：一次历史回归测试意外触发 `lsregister -dump`；发现后立即中止，未执行 Finder 或 GUI 文件操作，后续验证已排除该测试路径。
