# 治理与开发文档总索引

**版本**：v4.2.0  
**基线日期**：2026-06-19

## 六个必读入口

| 文件 | 回答的问题 |
|---|---|
| `FUNCTION_CATALOG.md` | 系统有哪些功能、导航、输入输出和实现边界？ |
| `MODEL_MANAGEMENT.md` | 模型、公式、参数、阈值如何查看、修改、刷新和回滚？ |
| `DOMAIN_DATA_CATALOG.md` | 关系、上下游、供应链、行业、板块、业务、资本和公司范围是什么？ |
| `DEVELOPMENT_STATUS.md` | 已解决、未解决、任务、实现和验证状态是什么？ |
| `RISK_AND_ACCEPTANCE.md` | 风险如何管控，发布如何验收？ |
| `GITHUB_REPOSITORY_BACKUP_INDEX.md` | 如何进入 GitHub 并长期防止文档/代码漂移？ |


## 用户要求覆盖矩阵

| 必须明确的内容 | 人类可读文件 | 机器单一事实来源 | GitHub 变更入口 |
|---|---|---|---|
| 功能清单与导航架构 | `FUNCTION_CATALOG.md`、`docs/23_SYSTEM_FUNCTION_MODULE_ARCHITECTURE.md` | `data/function_catalog.csv`、`data/navigation_catalog.csv` | `feature.yml` |
| 模型、公式、参数、阈值 | `MODEL_MANAGEMENT.md`、`docs/30_MODEL_MANAGEMENT.md` | `data/model_registry.csv`、`data/formula_registry.csv`、`data/parameter_catalog.csv`、`data/threshold_registry.csv` | `model_change.yml` |
| 关系与关系家族 | `DOMAIN_DATA_CATALOG.md`、`docs/31_DOMAIN_OBJECT_SCOPE_CATALOG.md` | `data/relationship_family_catalog.csv`、`data/relationship_taxonomy.csv` | `data_relationship.yml` |
| 上下游、供应链阶段和角色 | `docs/17_SUPPLY_CHAIN_RESEARCH_AND_EXPANSION_RULES.md` | `data/supply_chain_stage_taxonomy.csv`、`data/upstream_downstream_role_catalog.csv` | `data_scope_change.yml` |
| 行业、入口板块、业务板块 | `docs/35_DATA_CATALOGS_AND_TAXONOMIES.md` | `data/industry_taxonomy.csv`、`data/sector_taxonomy.csv`、`data/business_segment_taxonomy.csv` | `data_scope_change.yml` |
| 资本对象与金额语义 | `DOMAIN_DATA_CATALOG.md` | `data/capital_object_taxonomy.csv`、`data/data_dictionary.csv` | `data_scope_change.yml` |
| 公司与研究对象范围 | `docs/12_RESEARCH_UNIVERSE_SOURCE_METRICS_SCREENING.md` | `data/company_catalog.csv`、`data/research_universe.csv` | `data_scope_change.yml` |
| 开发任务、已解决/未解决 | `DEVELOPMENT_STATUS.md`、`docs/32_IMPLEMENTATION_STATUS_RESOLVED_UNRESOLVED.md` | `data/task_backlog.csv`、`data/development_status_ledger.csv`、`data/resolved_unresolved_register.csv` | `feature.yml` / PR |
| 风险、控制与触发器 | `RISK_AND_ACCEPTANCE.md`、`docs/33_RISK_CONTROL_ACCEPTANCE_TRACEABILITY.md` | `data/risk_register.csv`、`data/risk_control_traceability.csv` | `risk_control.yml` |
| 验收标准、追踪与发布 Gate | `docs/36_RELEASE_GATES_AND_DEFINITION_OF_DONE.md` | `data/acceptance_matrix.csv`、`data/acceptance_traceability.csv`、`data/release_gate_catalog.csv` | PR 模板 |

所有 PR 必须同步 Markdown、CSV/JSON/YAML 与状态/验收/风险追踪；`governance-validation` 负责阻止目录数量、ID、引用、配置、PDF 和 checksums 漂移。

## 机器单一事实来源

- 功能：17；模型/公式：11/11；参数/阈值：60/17。
- 关系家族/关系：10/52；供应链阶段：16；上下游角色：24。
- 行业/板块：26/13；业务板块/资本对象/领域对象：20/30/32。
- 公司与外部节点：140；任务/验收/风险/Gate：120/200/53/10。

完整机器目录见 `data/content_inventory.csv`；详细开发规范见 `docs/INDEX.md`。
