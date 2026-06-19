# Codex Master Task - v4.2

## Mission

从本 Task Pack 推进到可运行 MVP，同时保持功能、模型、数据范围、任务、风险与验收的仓库级一致性。

## First action: G0 read-only

1. 阅读 `GOVERNANCE_INDEX.md` 和六个根目录治理文档。
2. 运行 `python scripts/validate_task_pack.py`。
3. 输出本轮唯一 Issue、读取/修改文件、测试、风险、回滚和 Acceptance ID。
4. 不扫描无关目录，不改代码。

## Canonical source of truth

- Functions: `data/function_catalog.csv`
- Models/formulas/parameters: `data/model_registry.csv`, `data/formula_registry.csv`, `data/parameter_catalog.csv`
- Domain scope: relationship/stage/industry/segment/capital/company catalogs
- Tasks/status: `data/task_backlog.csv`, `data/development_status_ledger.csv`
- Acceptance/risk: traceability CSVs and release gates

## MVP success

实现 17 板块中的 P0 范围；首页视觉 90+、系统 80+；模型可在线/文件调整并跨视图刷新；任何数字可追溯到数据、公式、版本和证据。
