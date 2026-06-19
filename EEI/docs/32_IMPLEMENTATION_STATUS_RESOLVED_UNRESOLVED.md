# 32 - 开发状态：已解决、已原型、已定义、未解决与范围外

## 1. 结论

必须区分“文档完成”和“产品完成”。当前交付是规格与原型级 Task Pack，真实产品实现尚未开始。

## 2. 状态定义

- `RESOLVED`：需求或目录决策已冻结并有单一事实来源。
- `RESOLVED_FOR_TEMPLATE`：GitHub/工程模板已经提供，仍需在真实仓库启用。
- `PROTOTYPED`：可交互展示已完成，但没有生产数据/服务保证。
- `SPECIFIED`：接口、结构或验收已定义，代码未实现。
- `NOT STARTED`：生产实现未开始。
- `OUT OF MVP`：明确不属于当前 MVP。

## 3. 四轴状态与台账

每个功能、模型和关键工作流分别记录 `spec_status`、`prototype_status`、`implementation_status`、`validation_status`。规格或原型完成不得自动推导为生产实现完成。

当前真实状态：

- 规格、目录、模型边界、GitHub 模板：已完成；
- 高保真交互原型：已完成，使用 fixture；
- 生产数据库、真实采集、图查询、评分引擎、增量刷新和生产前端：未开始；
- 已冻结决策 7 项，开放问题 7 项；130 个开发任务，211 条验收，53 项风险。

机器单一事实来源：

- `data/development_status_ledger.csv`：规格/原型/实现/验证四轴状态；
- `data/resolved_unresolved_register.csv`：已解决、开放问题与延后范围；
- `data/task_backlog.csv`：任务、依赖、Gate 和验收映射；
- `data/release_gate_catalog.csv`：G0-G9 进入、退出和停止条件。

## 4. 当前下一门禁

G0 只读计划必须先确认：将读取/修改的文件、任务范围、测试命令、数据/模型迁移、风险、回滚和验收映射。未通过 G0 不进入代码写入。
