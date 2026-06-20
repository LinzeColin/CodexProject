# 商域图谱 / Enterprise Ecosystem Intelligence - Codex MVP Task Pack

副标题：企业商业版图与供应链递归探索系统

原始任务包语境：美国企业商业版图与供应链递归探索器。

**规格基线**：v4.2.0 + v5.0 production-blocker sync
**目标产品版本**：v0.1（当前 pursuing goal 完成后才可发布为 v0.1）
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
| `MODEL_MANAGEMENT.md` | 11 个模型、11 个公式、75 个参数、17 个阈值 |
| `DOMAIN_DATA_CATALOG.md` | 关系、上下游、供应链、行业、板块、业务、资本和公司范围 |
| `DEVELOPMENT_STATUS.md` | 已解决/未解决、130 个任务和四轴状态 |
| `RISK_AND_ACCEPTANCE.md` | 53 项风险、211 条验收和 Gate |
| `REVIEW_AND_ITERATION_INDEX.md` | v5 审查、品牌、测试和迭代入口 |
| `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md` | v5 生产阻塞项到 EEI 任务/验收/参数的同步映射 |
| `TEST_STRATEGY.md` | 静态、单元、契约、集成、E2E、规模和 soak 测试策略 |
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

先审查 G0 只读计划，再允许 workspace-write。原型使用 fixture；T1300 PostgreSQL 可回滚迁移与 fact/evidence/time/version 分层已实现。T1301 已开始：NVIDIA/ASML 官方来源快照可写入 raw snapshot、实体解析候选、Golden Vertical 关系事实候选、复核队列和证据链，但 A202 仍未关闭。T1302 已开始：生产上下文、递归图/路径 publication policy 和 relationship_fact_candidate 评分解释合同已接入，但 A203 仍未关闭。live/full-text 采集、独立来源交叉验证、正式关系事实发布、完整多对象评分服务、模型事务激活、原子刷新、调度、保存视图、规模压测、soak、生产组件化前端和正式品牌清权仍是 v0.1 阻断项。
