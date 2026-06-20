# 商域图谱 / Enterprise Ecosystem Intelligence - Codex MVP Task Pack

副标题：企业商业版图与供应链递归探索系统

原始任务包语境：美国企业商业版图与供应链递归探索器。

**规格基线**：v4.2.0 + v5.0 production-blocker sync
**目标产品版本**：v0.1（当前 pursuing goal 完成后才可发布为 v0.1）
**基线日期**：2026-06-19  
**目标仓库**：LinzeColin/CodexProject/EEI

## 结论

本包是一套可直接进入 GitHub 和 Codex G0 的产品、模型、数据、研发与验收基线。默认首页从 Watchlist 当前公司进入可视化商业版图，并允许点击任意对象后递归切换研究中心。

当前生产实现进度：T1300/A201 和 T1306/A208 已关闭；T1301/A202、T1302/A203、T1303/A204-A205、T1304/A206、T1305/A207、T1307/A209、T1308/A211 处于进行中。T1302/T1308 已具备首页商业版图 `/v1/explore` API-first production_context hydration、图查询预算、coverage、候选事实 publication gate mock E2E、server-returned nodes/edges 渲染、production_context `sample_candidates`、`/v1/catalogs` inventory hydration 和 relationship_fact_candidate score explanation hydration；T1303 已具备服务端事务激活、operation log、active analysis context、refresh token、前端 API-first active-context hydration、事务激活、rollback 控件和 stale refresh mock E2E；T1304 已具备 scheduler job queue、lease、heartbeat、retry、dead-letter 和 graceful release 状态机合同；T1305 已具备服务端 saved views、版本历史、乐观锁冲突、恢复合同、前端 API-first saved-view adapter mock E2E、409 冲突恢复 UI、live FastAPI/PostgreSQL 多会话 E2E harness 和 GitHub Actions G2 证据；T1306 已具备确定性规模 benchmark smoke harness、10k/100k/1m operator_full、Chromium browser runtime 和 pass/fail JSON 证据；T1307 已具备 browser+worker soak smoke harness；T1308 已具备 WorkspaceContext、16 个 EEI 导航模块状态、route/lens/section/planned 控件、禁用未完成功能、模型中心控件、URL/session/local persistence、server graph render 和 production data panel E2E 证据。但 evidence detail/source snippets 生产 API hydration、模型中心 live backend cross-route E2E、saved-view authn/authz、真实 scheduler handler/部署唤醒、4h/24h soak operator evidence、正式关系事实发布、多对象评分和品牌清权仍阻断 v0.1。

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

先审查 G0 只读计划，再允许 workspace-write。原型使用 fixture；T1300 PostgreSQL 可回滚迁移与 fact/evidence/time/version 分层已实现。T1301 已开始：NVIDIA/ASML 官方来源快照可写入 raw snapshot、实体解析候选、Golden Vertical 关系事实候选、复核队列和证据链，但 A202 仍未关闭。T1302 已开始：生产上下文、递归图/路径 publication policy、relationship_fact_candidate 评分解释合同、`/v1/evidence/{objectType}/{objectId}` 证据 detail/source snippets、production_context `sample_candidates`、首页 `/v1/explore` production_context hydration、server-returned graph rendering、`/v1/catalogs` inventory、score explanation 和 evidence detail hydration 已接入，但 A203 仍未关闭。T1303 已开始：`/v1/scoring/active-context`、`/v1/scoring/profiles/{profileVersionId}/activate`、前端模型中心 API-first hydration、事务激活、rollback 控件和 stale refresh mock E2E 已接入，但 live FastAPI/PostgreSQL cross-route E2E、在线编辑和 score recompute UI 未关闭。T1304 已开始：后台 job queue、lease、heartbeat、retry、dead-letter 和 graceful release 已具备数据库与 CLI 合同，但真实业务 handler、部署唤醒和 soak 未关闭。T1305 已开始：`/v1/saved-views` 支持 version history、expected_version 409 和 restore，前端保存/恢复控件已具备 API-first adapter、显式 local fallback、mock server E2E、409 获取最新冲突恢复 UI 和 live FastAPI/PostgreSQL 双 browser context E2E harness；GitHub Actions `verify-g2-db` run `27862471613` job `82460665725` 已通过，仍需要 authn/authz。T1306 已关闭：`scripts/run_scale_benchmarks.py` 与 `scripts/run_browser_scale_benchmarks.mjs` 输出 API、layout、render、memory、frame、long-task 预算 smoke、10k/100k/1m operator_full 和 Chromium browser runtime JSON。T1307 已开始：`scripts/run_soak_smoke.mjs` 输出 browser+worker heap、DOM、listener、timer、CPU、retry 和 recovery smoke JSON，但 4h/24h operator evidence 未完成。T1308 已开始：`WorkspaceContext`、组件化导航 rail、真实 route/lens/section/planned 控件、禁用未完成模块、模型中心控件、首页商业版图 `/v1/explore` context hydration、server graph rendering、catalog/score/evidence production data panel 和持久化查询合同已有 E2E 证据，但 live backend cross-route E2E 未完成。live/full-text 采集、独立来源交叉验证、正式关系事实发布、完整多对象评分服务、模型事务 live 刷新和正式品牌清权仍是 v0.1 阻断项。
