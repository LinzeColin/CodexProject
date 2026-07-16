# Phase 8.1 风险与回滚

- 风险：旧 v0.2.1 dark/glass 规则位于同一历史样式文件后部。控制：使用带 Phase marker 的 scoped selector，并在 cascade 尾部锁定 light root token。
- 风险：页面原型规则在移动端 specificity 高于通用单列规则。控制：移动媒体查询对 `[data-stage8-archetype]` 使用等价 specificity，实测 10/10 页面无横向溢出。
- 风险：图表在无真实序列时仍绘制 canvas。控制：组件状态为 empty/error 时隐藏 canvas，保留明确中文状态；shell 的 series empty branch 不执行曲线绘制。
- 风险：组件 observer 自触发。控制：状态更新幂等、微任务去重；修复后 20 路由无 page/console error。
- 风险：Playwright trace 泄露本地路径。控制：resource body 移除、绝对路径脱敏、二次字符串扫描为 0。
- 风险：连续页面截图复用 compositor layer。控制：最终每个路由独立 browser context，软件栅格化；20 张 PNG 直接解码，黑像素文件数为 0。

回滚：revert 本 Phase 单一提交即可恢复既有 UI；本轮未改数据库、财务数据、公式、模型或参数，不需要数据回滚。Release manifest 的 frontend hash 必须与前端文件一起回滚。
