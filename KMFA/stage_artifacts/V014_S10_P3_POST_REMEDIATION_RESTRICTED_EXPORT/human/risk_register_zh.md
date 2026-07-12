# S10-P3 修补后受限导出风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 B 级或 12 pending 状态回流 | 当前 S10-P2 是唯一动态输入，历史导出只提供框架 | controlled |
| 受限预览被误用为正式报告 | 首屏、CSV 和记录同时传播 D级、未放行和使用限制 | controlled |
| HTML/CSV 泄漏业务值 | 只输出章节名称与聚合状态，validator 扫描业务值、raw 和 secret | controlled |
| PDF/Excel 工作簿误提交 | PDF 仅私有策略且未执行，Excel 只使用兼容 CSV | controlled |
