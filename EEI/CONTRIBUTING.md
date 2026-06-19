# Contributing and Change Governance

## 开始前

1. 从 `GOVERNANCE_INDEX.md` 找到受影响的功能、模型和目录。
2. 一次只处理一个 Issue、一个目录和一个验收目标。
3. 在 Issue 中写明读取/修改文件、测试、风险、回滚和 Acceptance ID。
4. 先提交只读计划；确认后才修改代码。

## 必须同步的文件

- 功能或导航：`data/function_catalog.csv`、`FUNCTION_CATALOG.md`。
- 模型或参数：`data/model_registry.csv`、`data/formula_registry.csv`、`data/parameter_catalog.csv`、`MODEL_MANAGEMENT.md`。
- 关系/行业/公司/供应链：相应 taxonomy/catalog 与 `DOMAIN_DATA_CATALOG.md`。
- 开发状态：`data/task_backlog.csv`、`data/development_status_ledger.csv`、`DEVELOPMENT_STATUS.md`。
- 风险/验收：`data/risk_register.csv`、两份 traceability CSV、`RISK_AND_ACCEPTANCE.md`。

## 合并门槛

```bash
python scripts/validate_catalog_integrity.py
python scripts/validate_task_pack.py
python scripts/validate_visual_coverage.py  # UI/原型变更时
bash scripts/preflight.sh
```

PR 必须提供测试输出和回滚方案；变更完成后重新生成 manifest、目录树与 checksums。不得把 fixture、推断或未知值伪装为真实生产事实。
