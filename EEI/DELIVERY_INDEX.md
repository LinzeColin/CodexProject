# v4.2.0 交付索引

## 当前交付

1. **产品功能层**：17 个功能板块，含导航、目的、可视化、输入输出、数据/API、任务、验收和风险。
2. **模型治理层**：11 个模型、11 个公式、60 个参数、17 个核心阈值；支持文件和在线修改、预览、版本、激活与回滚。
3. **领域数据层**：10 个关系家族、52 种关系、16 个供应链阶段、26 个行业分类、13 个板块、140 个研究对象。
4. **开发治理层**：120 项任务、200 条验收、53 项风险和 10 个发布 Gate。

## 文件入口

- 功能：`FUNCTION_CATALOG.md` / `data/function_catalog.csv`
- 模型：`MODEL_MANAGEMENT.md` / `data/model_registry.csv` / `data/formula_registry.csv` / `data/parameter_catalog.csv`
- 领域：`DOMAIN_DATA_CATALOG.md` / `data/content_inventory.csv`
- 状态：`DEVELOPMENT_STATUS.md` / `data/development_status_ledger.csv`
- 风险验收：`RISK_AND_ACCEPTANCE.md` / `data/risk_control_traceability.csv` / `data/acceptance_traceability.csv`
- GitHub：`GITHUB_REPOSITORY_BACKUP_INDEX.md` / `.github/`
- 原型：`prototype/standalone.html`
- 视觉覆盖：`scripts/validate_visual_coverage.py` / `artifacts/visual_coverage_validation.txt`

## 边界

规格和原型已完成；生产实现、真实数据库与真实企业关系仍为 `NOT_STARTED`。
