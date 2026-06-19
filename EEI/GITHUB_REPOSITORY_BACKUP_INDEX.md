# GitHub 开发文档与备份总索引

**版本**：v4.2.0  
**基线日期**：2026-06-19

## 结论

解压后的目录可直接初始化为 GitHub 仓库。功能、模型、关系、供应链、行业、板块、公司、任务、风险和验收均保存在版本化文件中；任何变更都必须经 Issue/PR、自动校验和状态同步，不能只保留在聊天记录。

## 仓库结构

| 层 | 内容 | 关键文件 |
|---|---|---|
| 产品 | 功能、导航、用户问题、输入输出 | `FUNCTION_CATALOG.md`、`data/function_catalog.csv` |
| 模型 | 公式、参数、阈值、版本、刷新、回滚 | `MODEL_MANAGEMENT.md`、`data/model_registry.csv`、`config/` |
| 研究本体 | 关系、上下游、供应链、行业、业务、资本、公司 | `DOMAIN_DATA_CATALOG.md`、`data/content_inventory.csv` |
| 研发执行 | 任务、依赖、状态、已解决/未解决 | `DEVELOPMENT_STATUS.md`、`data/task_backlog.csv` |
| 风险质量 | 风险、控制、验收、测试证据、Gate | `RISK_AND_ACCEPTANCE.md`、`data/*traceability.csv` |
| GitHub 治理 | Issue Forms、PR 模板、CODEOWNERS、Actions | `.github/` |

## 强制同步规则

1. 功能变化：更新 Function ID、导航、输入输出、主可视化、表/API、任务、验收和风险。
2. 模型变化：更新 Formula/Parameter/Threshold ID、前后值、影响预览、版本、日志和回滚。
3. 领域变化：更新关系方向/证据门槛、供应链阶段、行业/板块、业务/资本对象和迁移规则。
4. 实现变化：更新四轴状态（规格、原型、生产实现、验证）及测试证据。
5. PR 合并前运行目录、Task Pack 与视觉覆盖校验；失败不得合并。
6. `governance-validation` 设有目录治理与浏览器视觉覆盖两个 Job，并校验 checksums。

## 当前真实状态

- Task Pack、目录、文档、GitHub 模板与交互原型：已完成。
- 生产数据库、真实采集、关系核验、后端、评分引擎、增量刷新和生产前端：未开始。
- 原型中的公司关系与数字：交互 fixture，不是实时投资事实。
