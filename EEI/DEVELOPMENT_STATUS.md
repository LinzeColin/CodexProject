# 开发任务、已解决/未解决与执行状态

## 当前结论

| 层级 | 当前状态 |
|---|---|
| 需求、架构、目录、模型与验收 | 已完成 Task Pack 规格 |
| 高保真交互原型 | 已完成，用 fixture 演示 |
| 生产代码与真实数据库 | T1300 PostgreSQL 生产迁移与版本层已实现；T1301 官方锚点 ingestion 基础层进行中；T1302 生产 API/递归图/评分解释合同已开始；T1303 事务激活和 refresh token 合同已开始；T1304 scheduler job queue、lease、heartbeat、retry、dead-letter 状态机已开始但仍未达 MVP |
| 真实数据接入与企业事实 | T1301/A202 进行中；curated official anchors 与 Golden Vertical fact candidates 已入库合约化，但 live/full-text 采集、独立来源交叉验证和事实发布未完成，不得把候选数据当事实 |
| GitHub 治理模板与校验 | 已包含，推送仓库后启用 |

当前共有 **130 个产品开发任务**、**211 条验收标准**、**53 项风险**。新增 T1300-T1309/A201-A211 来自 v5 审查和用户当前待开发清单；T1300/A201 已关闭，T1301/A202、T1302/A203、T1303/A204-A205、T1304/A206 进行中但未关闭，T1305-T1309/A207-A211 仍未完成，避免把规格/原型或部分生产合同误报为生产 MVP 完成。

## 已解决的关键决策（7）

- 默认首页、递归主体探索、数据底座、模型修改流程、14 天校准、视觉覆盖目标、文档治理方式均已冻结。

## v5 同步后仍阻断 v0.1 的生产项（9 个未关闭；T1301/T1302/T1303/T1304 进行中）

1. 真实数据采集、实体解析和证据链：官方锚点与 Golden Vertical 候选事实层已开始，live/full-text、正式事实发布和人工复核批准未完成。
2. 生产 API、递归图查询和评分服务：生产上下文、候选事实隔离和 relationship_fact_candidate 评分解释已开始，多对象评分服务、完整发布边和规模验证未完成。
3. 模型配置版本、事务性激活和原子全局刷新：active_analysis_contexts、全局 active profile 唯一约束、事务激活 API、operation log 和 refresh token 合同已开始，前端全模块真实刷新和模型中心 UI 未完成。
4. 后台调度、自动唤醒、幂等、重试和 dead-letter：scheduler job queue、lease、heartbeat、retry、dead-letter 和 graceful release 状态机已开始，真实业务 handler、部署唤醒和 soak 未完成。
5. 服务端保存视图、冲突控制和恢复。
6. 10k、100k、1m 关系规模测试。
7. 4 小时和 24 小时 soak 测试。
8. 生产组件化前端、真实路由和真实控件连接。
9. EEI 正式品牌法律与市场清权。

已关闭：T1300/A201 PostgreSQL 可回滚迁移、data snapshot、fact version、fact evidence、时间有效性和版本层 schema。

进行中：T1301/A202 curated official NVIDIA/ASML source snapshots, raw snapshots, entity resolution candidates, Golden Vertical fact candidates, review queue and ingestion evidence chain；T1302/A203 production_context, bounded graph/path publication policy and relationship_fact_candidate score explanation contract；T1303/A204-A205 active_analysis_contexts, transactional activation API, operation log and refresh-token stale-client semantics；T1304/A206 background_jobs/background_job_attempts/dead_letter_jobs, job_scheduler.py lease/heartbeat/retry/dead-letter/graceful release contract.

## 仍未解决（7）

- 部署与预算、身份认证、商业数据许可、生产数据规模、图渲染库最终基准、战略模型有效性、140 个对象的真实关系接入。

## 状态文件

- `data/task_backlog.csv`：Codex 开发任务、依赖、Gate、Acceptance ID。
- `data/development_status_ledger.csv`：规格/原型/实现/验证四种状态。
- `data/resolved_unresolved_register.csv`：决策、Open issue、Deferred。
- `data/release_gate_catalog.csv`：G0-G9 进入/退出和停止条件。
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`：v5 压缩包研究、生产缺口和 T1300-T1309/A201-A211 映射。

Codex 每完成一个任务，必须同步状态、测试证据、风险和验收，不得只在聊天中说明。
