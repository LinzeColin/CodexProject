# Memory Atlas 记忆总览与系统使用说明验收

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 1

状态：contract acceptance only。本 phase 不启动浏览器、不执行截图、不修改 React/CSS，不进入 Stage 1 复审。

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

## 1. 验收目的

本验收固定记忆总览和系统使用说明的可用性底线。通过本验收只表示 Stage 1 Phase 1 的合同完整，不表示运行时 UI 已完成截图验收。

## 2. 静态合同检查

| 检查项 | 通过标准 | 失败示例 |
|---|---|---|
| 默认入口定位 | 明确记忆总览是系统操作中枢 | 写成欢迎页、营销页或普通 dashboard |
| 今日状态 | 要求用户先看到当前系统状态 | 只展示指标数值，没有状态判断 |
| Memory Weather | 有天气标签、驱动因素、置信度和证据入口 | 只有装饰性标题 |
| 建议动作 | 明确继续、复盘、整合、探索、暂缓等动作类型 | 只有泛泛提示 |
| 低价值循环 | 明确 black hole 风险和降权/约束入口 | 只写风险数量 |
| 新生机会 | 明确 proto-star 机会和验证入口 | 只写机会标题 |
| 层级资产摘要 | 覆盖核心画像、项目、决策、工作流、知识、机会 | 只显示 memory_tier 原始字段 |
| 主题分类摘要 | 覆盖主题强度、趋势、置信度和记录数入口 | 只显示 tag 列表 |
| 视觉预览 | Mini 记忆星系和记忆时间河脉冲都有入口 | 首页完全列表化 |
| 系统使用说明 | 提供从总览到 Inspector、星系、时间河、搜索复盘的路径 | 只写“点击查看详情” |
| 模式说明 | Presentation / Analysis 区分清楚 | 把 debug JSON 默认暴露给用户 |
| Proposal 说明 | 明确 proposal-only 和 rollback | 暗示前端直接写长期记忆 |

## 3. 文本与布局承载

- 首页说明必须使用中文优先。
- 卡片标题建议不超过 18 个中文字符。
- 首页卡片摘要建议不超过两行。
- 长解释进入 Inspector、展开层或后续明细工作台。
- 表格只放短字段，不承载长段落。
- 低宽度视口不得因为中文长词产生横向撑破。

## 4. 后续截图验收入口

后续实现 phase 必须在以下视口补截图或等价浏览器证据：

| 视口 | 最低验收 |
|---|---|
| Desktop 1440x900 | 首屏能看到今日状态、Memory Weather、建议动作和至少一个视觉预览 |
| Tablet 768x1024 | 首页模块不重叠，系统使用说明可展开阅读 |
| Mobile 390x844 | 主按钮和中文卡片不溢出，长说明不塞进卡片 |

## 5. 安全失败条件

任一情况出现即失败：

1. 合同要求读取 raw/private/cookie/session/secret 数据。
2. 合同允许前端直接修改 active memory 或长期记忆。
3. 合同跳过 Inspector 证据解释。
4. 合同没有说明 Proposal 和 rollback。
5. 合同把 Stage 2-5 的明细、搜索、复盘或 Data Map 实现冒充为本 phase 已完成。
6. 合同要求本 phase 启动浏览器或修改运行时 UI。

## 6. 通过条件

Stage 1 Phase 1 通过时必须有：

1. `docs/product/memory_overview_usage_contract.md`。
2. `docs/acceptance/memory_overview_usage_acceptance.md`。
3. `validate:v1.1.6-stage1-phase1`。
4. 三文件和模型参数记录中登记 `MA-V116-S1P01`。
5. Changelog 明确 no runtime UI、no raw/private data、no direct writeback、no GitHub main upload。

## 7. 回滚

删除本验收文件、本 phase 产品合同、validator、package script 和记录增量即可回滚；不需要运行时回滚。
