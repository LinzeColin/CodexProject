# v4.2 MVP 构建：一次一个 Gate、可追溯实现

仅在 G0 计划获批、Git 工作区干净且本轮唯一 Issue 已明确后进入写入阶段。不要一次性重构全仓。

## 事实来源

- 功能与导航：`data/function_catalog.csv`、`data/navigation_catalog.csv`。
- 模型/公式/参数/阈值：`data/model_registry.csv`、`data/formula_registry.csv`、`data/parameter_catalog.csv`、`data/threshold_registry.csv`、`config/`。
- 关系/上下游/供应链/行业/业务/资本/公司：`data/content_inventory.csv` 所列目录。
- 任务/状态：`data/task_backlog.csv`、`data/development_status_ledger.csv`、`data/resolved_unresolved_register.csv`。
- 验收/风险/Gate：`data/acceptance_traceability.csv`、`data/risk_control_traceability.csv`、`data/release_gate_catalog.csv`。

## 实施顺序

1. 先锁定本 Gate 的 Acceptance ID、风险、文件、测试和回滚。
2. 先实现最小纵向切片：数据语义 -> 迁移/存储 -> API/事件 -> 计算 -> 可视化 -> 证据/日志 -> 测试。
3. 模型与参数修改必须支持校验、影响预览、保存不可变版本、操作日志、原子激活、全局重算/增量重算、刷新事件和回滚。
4. 商业图谱必须保留关系方向、有效期、金额/比例语义、证据状态、来源和 unknown；不得把推断显示为确认事实。
5. 首页、数据库、模型、功能结构、开发治理均以视觉工作台为主，不得只提交表格或静态截图。
6. 每个 Gate 完成后同步：功能目录、模型/领域目录、开发状态、验收追踪、风险控制、CHANGELOG 和测试证据。

## 交互与视觉门槛

- 默认 Watchlist 主图；左上游、中主体、右下游，上方资本/控制，下方政策/风险。
- 单击选择、明确“设为研究中心”、路径返回、浏览器历史、刷新恢复和保存视图行为一致。
- 使用统一 motion tokens；提供 loading/success/error/rollback 多模态反馈；尊重 reduced motion；触觉不是唯一反馈。
- 默认图有节点/边预算、聚合、语义缩放和按需展开，避免不可读的全量毛线团。
- 数据库工作台必须展示实体、关系、快照、来源、血缘、质量、新鲜度和表/字段详情，而不是装饰性“数据库风格”。

## 完成报告

输出 diff summary、测试结果、Acceptance ID、状态变更、证据路径、剩余风险、未解决问题和回滚命令。未通过 required test 时不得标记 Gate PASS。
