# 开发文档索引

## 先看结论

此目录是后续 GitHub 开发备份的详细规范层；根目录六份索引是快速入口，`data/`/`models/`/`config/` 是机器单一事实来源。

| 主题 | 规范 | 机器源 |
|---|---|---|
| 产品需求与边界 | `01_PRODUCT_REQUIREMENTS.md`、`02_SCOPE_AND_BOUNDARIES.md` | `data/function_catalog.csv` |
| UI/UX 与可视化 | `19_VISUAL_FIRST_WORKSPACE_SPEC.md`、`27_MOTION_HAPTIC_INTERACTION_SYSTEM.md`、`28_VISUAL_COVERAGE_UI_ACCEPTANCE.md` | `config/ui/` |
| 功能与导航 | `29_FUNCTION_CATALOG_AND_SCOPE.md` | `data/function_catalog.csv`、`data/navigation_catalog.csv` |
| 模型/公式/参数/阈值 | `30_MODEL_MANAGEMENT.md` | `data/model_registry.csv`、`data/formula_registry.csv`、`data/parameter_catalog.csv`、`data/threshold_registry.csv` |
| 关系/上下游/业务/资本/公司 | `31_DOMAIN_OBJECT_SCOPE_CATALOG.md`、`35_DATA_CATALOGS_AND_TAXONOMIES.md` | `data/content_inventory.csv` 所列目录 |
| 已解决/未解决与任务 | `32_IMPLEMENTATION_STATUS_RESOLVED_UNRESOLVED.md` | `data/task_backlog.csv`、`data/development_status_ledger.csv` |
| 风险/控制/验收 | `33_RISK_CONTROL_ACCEPTANCE_TRACEABILITY.md`、`36_RELEASE_GATES_AND_DEFINITION_OF_DONE.md` | `data/risk_control_traceability.csv`、`data/acceptance_traceability.csv` |
| GitHub 备份与防漂移 | `34_GITHUB_DOCUMENTATION_AND_BACKUP.md` | `.github/`、`scripts/validate_governance.py` |

**基线规模**：17 功能、11 模型、84 参数、10 关系家族、52 关系、16 供应链阶段、140 研究对象、120 任务、200 验收、53 风险。
