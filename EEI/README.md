# 商域图谱 / Enterprise Ecosystem Intelligence - Codex MVP Task Pack

副标题：企业商业版图与供应链递归探索系统

原始任务包语境：美国企业商业版图与供应链递归探索器。

**版本**：v4.2.0  
**产品版本**：v0.1  
**基线日期**：2026-06-19  
**目标仓库**：LinzeColin/CodexProject/EEI

## 结论

本包是一套可直接进入 GitHub 和 Codex G0 的产品、模型、数据、研发与验收基线。默认首页从 Watchlist 当前公司进入可视化商业版图，并允许点击任意对象后递归切换研究中心。

| 入口 | 用途 |
|---|---|
| `prototype/standalone.html` | 离线可交互高保真原型 |
| `GOVERNANCE_INDEX.md` | 治理总入口 |
| `GITHUB_REPOSITORY_BACKUP_INDEX.md` | GitHub 文档/代码备份与防漂移 |
| `FUNCTION_CATALOG.md` | 17 个功能和导航架构 |
| `data/product_navigation_catalog.csv` | 16 个用户侧导航模块冻结源 |
| `MODEL_MANAGEMENT.md` | 11 个模型、11 个公式、60 个参数、17 个阈值 |
| `DOMAIN_DATA_CATALOG.md` | 关系、上下游、供应链、行业、板块、业务、资本和公司范围 |
| `DEVELOPMENT_STATUS.md` | 已解决/未解决、120 个任务和四轴状态 |
| `RISK_AND_ACCEPTANCE.md` | 53 项风险、200 条验收和 Gate |
| `US_Corporate_Power_Map_Governance_Blueprint_v4.2.pdf` | 可审阅 PDF 总蓝图 |

## 数据与模型规模

- 10 个关系家族、52 种关系、16 个供应链阶段、24 类上下游/使能角色。
- 26 个行业分类、13 个板块、20 类业务板块、30 类资本对象、140 个研究对象。
- 首页可视化验收目标 `>=90%`；核心系统平均 `>=80%`。

## Codex 启动

```bash
python scripts/validate_catalog_integrity.py
python scripts/validate_task_pack.py
python scripts/validate_visual_coverage.py
bash scripts/preflight.sh
codex exec --sandbox read-only - < prompts/01_PLAN_ONLY.md | tee artifacts/01_plan_output.txt
```

先审查 G0 只读计划，再允许 workspace-write。原型使用 fixture；真实采集、数据库、生产 API 和生产前端尚未实现。
