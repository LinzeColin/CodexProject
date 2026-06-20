# 开发任务、已解决/未解决与执行状态

## 当前结论

| 层级 | 当前状态 |
|---|---|
| 需求、架构、目录、模型与验收 | 已完成 Task Pack 规格 |
| 高保真交互原型 | 已完成，用 fixture 演示 |
| 生产代码与真实数据库 | T1300 PostgreSQL 生产迁移与版本层已实现；T1301 官方锚点 ingestion 基础层、Golden Vertical 候选事实、测试审核发布链路和 production owner sign-off 合同进行中；T1302 生产 API/递归图/评分解释合同、entity/event/industry/relationship_fact_candidate/published relationship 评分解释、event fixture PostgreSQL 加载、`/v1/explore` production_context sample_candidates、首页 `/v1/explore` production_context hydration + server node/edge rendering + `/v1/catalogs`、score explanation 与 evidence detail/source snippets hydration 已开始，entity 评分切片已通过 GitHub Actions run `27878398112` / job `82501662399` 验证，event/industry 评分切片已通过 GitHub Actions run `27879503435` / job `82504489377` 的 G2 PostgreSQL integration、browser E2E 和 live FastAPI/PostgreSQL E2E 验证；T1303 事务激活、dedicated rollback endpoint、score recompute 入队 API、data snapshot refresh 入队 API、transactional outbox 事件源、refresh token、前端 API-first 模型中心激活/rollback/stale refresh/recompute、inactive `supply-chain-v3` profile seed 和 live FastAPI/PostgreSQL model activation harness 已通过 GitHub Actions run `27871752533` / job `82484659437` 验证；T1304 scheduler job queue、outbox dispatch、lease、heartbeat、retry、dead-letter 状态机、`score_recompute`/`data_snapshot_refresh`/`curated_ingestion_refresh`/`calibration_run` 入队或执行合同、`apps.worker` supervisor CLI 和 Docker Compose worker process-manager 绑定已接入；T1305 服务端保存视图、版本冲突、恢复合同、`X-EEI-User-Namespace`/`X-EEI-Actor` 命名空间隔离、跨 namespace 404、前端 API-first adapter、409 冲突恢复 UI、live 多会话 E2E harness 和 trusted_gateway HMAC 身份边界已通过 GitHub Actions run `27875473970` / job `82494131119` 验证；T1306 规模 benchmark 和 browser runtime 合同已关闭；T1307 soak smoke harness 已开始但 4h/24h 未关闭；T1308 WorkspaceContext、真实导航控件、模型中心控件、首页图谱 API-first hydration/server rendering、catalog/score/evidence production data panel、Objects and Scope/Industries/System Status live route coverage 和前端持久化合同已通过 GitHub Actions run `27876091338` / job `82495713946` 的 browser/live FastAPI PostgreSQL E2E 验证并关闭 |
| 真实数据接入与企业事实 | T1301/A202 进行中；curated official anchors、Golden Vertical fact candidates 和显式审核决策驱动的测试发布路径已合约化，并由 GitHub Actions run `27877209505` / job `82498609174` 验证 G2 PostgreSQL integration、browser E2E 与 live FastAPI/PostgreSQL E2E；本轮新增 production owner sign-off 合同，本地已验证 `--allow-production-owner-signoff` 门控、owner 字段约束和 owner_signature_hash 落库；但 live/full-text 采集、真实 operator-supplied owner 决策或第二独立来源闭环、owner sign-off 远端 PostgreSQL CI 和来源健康重试链路未完成，不得把测试审核夹具当生产批准 |
| GitHub 治理模板与校验 | 已包含，推送仓库后启用 |

当前共有 **130 个产品开发任务**、**211 条验收标准**、**53 项风险**。新增 T1300-T1309/A201-A211 来自 v5 审查和用户当前待开发清单；T1300/A201、T1305/A207、T1306/A208 和 T1308/A211 已关闭，T1301/A202、T1302/A203、T1303/A204-A205、T1304/A206、T1307/A209 进行中但未关闭，T1309/A210 仍未完成，避免把规格/原型或部分生产合同误报为生产 MVP 完成。

## 已解决的关键决策（7）

- 默认首页、递归主体探索、数据底座、模型修改流程、14 天校准、视觉覆盖目标、文档治理方式均已冻结。

## v5 同步后仍阻断 v0.1 的生产项（6 个未关闭；T1301/T1302/T1303/T1304/T1307 进行中）

1. 真实数据采集、实体解析和证据链：官方锚点、Golden Vertical 候选事实层和显式审核发布脚本已开始，reviewed-publication 数据库路径已由 GitHub Actions run `27877209505` / job `82498609174` 验证；production owner sign-off 合同已本地实现，但 owner sign-off 远端 PostgreSQL CI、live/full-text、真实 operator-supplied owner 决策或第二独立来源闭环未完成。
2. 生产 API、递归图查询和评分服务：生产上下文、候选事实隔离、entity/event/industry/relationship_fact_candidate/published relationship 评分解释、event fixture PostgreSQL 加载、`/v1/evidence/{objectType}/{objectId}` 证据 detail/source snippets、nullable evidence 字段标准化、`sample_candidates` 发现合同、首页 `/v1/explore` context hydration/server node-edge rendering、catalog inventory、score explanation 与 evidence detail 前端 hydration 已开始，entity 评分切片已由 GitHub Actions run `27878398112` / job `82501662399` 验证，event/industry 评分切片已由 GitHub Actions run `27879503435` / job `82504489377` 验证 G2 PostgreSQL integration、browser E2E 和 live FastAPI/PostgreSQL E2E；其他非关系对象评分、完整生产批准边和规模/soak 发布证据未完成。
3. 模型配置版本、事务性激活和原子全局刷新：active_analysis_contexts、全局 active profile 唯一约束、事务激活 API、dedicated rollback endpoint、`POST /v1/scoring/recompute` 入队 API、`POST /v1/data/snapshots/refresh` 入队 API、operation log、transactional outbox、refresh token、前端 API-first active-context hydration、事务激活、rollback、recompute 控件、stale refresh mock E2E、inactive `supply-chain-v3` candidate profile、真实 `score_recompute` worker handler、真实 `data_snapshot_refresh` worker handler 和 live FastAPI/PostgreSQL activation/stale-refresh/rollback harness 已开始，在线编辑和部署唤醒未完成。
4. 后台调度、自动唤醒、幂等、重试和 dead-letter：scheduler job queue、outbox dispatch、lease、heartbeat、retry、dead-letter、graceful release 状态机、`score_recompute` 入队/执行合同、`data_snapshot_refresh` 入队/执行合同、`curated_ingestion_refresh` 执行合同、`calibration_run` 入队/执行合同、`apps.worker` supervisor CLI 和 Docker Compose worker process-manager 绑定已开始，4h/24h soak 未完成。
5. 4 小时和 24 小时 soak 测试：browser+worker smoke harness 已开始，4h/24h operator run 未完成。
6. EEI 正式品牌法律与市场清权。

已关闭：T1300/A201 PostgreSQL 可回滚迁移、data snapshot、fact version、fact evidence、时间有效性和版本层 schema；T1305/A207 服务端保存视图、冲突控制、版本恢复、跨 namespace 保护和 trusted_gateway HMAC 身份边界，GitHub Actions run `27875473970` / job `82494131119` PASS；T1306/A208 10k/100k/1m operator_full 和 browser runtime scale benchmark；T1308/A211 生产组件化前端、真实路由、真实控件、production data panel 和 live backend cross-route E2E，GitHub Actions run `27876091338` / job `82495713946` PASS。

进行中：T1301/A202 curated official NVIDIA/ASML source snapshots, raw snapshots, entity resolution candidates, Golden Vertical fact candidates, review queue, ingestion evidence chain, explicit fixture review decision contract, production owner sign-off contract and reviewed-publication script writing relationships/fact_versions idempotently, with GitHub Actions run `27877209505` / job `82498609174` proving the fixture reviewed-publication PostgreSQL path and local checks proving the owner-signoff gate/hash contract pending remote PostgreSQL CI；T1302/A203 production_context, bounded graph/path publication policy, entity/event/industry/relationship_fact_candidate/published relationship score explanation contracts, event fixture PostgreSQL loading, evidence detail/source snippets contract, sample_candidates discovery, commercial-map `/v1/explore` context hydration/server rendering and catalog/score/evidence hydration, with GitHub Actions run `27878398112` / job `82501662399` proving the entity score explanation PostgreSQL/browser/live FastAPI slice and GitHub Actions run `27879503435` / job `82504489377` proving the event/industry PostgreSQL/browser/live FastAPI slice；T1303/A204-A205 active_analysis_contexts, transactional activation API, dedicated rollback endpoint, score recompute enqueue API, data snapshot refresh enqueue API, transactional_outbox event source, worker score recompute execution, worker data snapshot refresh execution, operation log, refresh-token stale-client semantics, inactive `supply-chain-v3` seed, frontend model-center API-first activation/rollback/recompute/stale refresh mock E2E and live model activation/stale-refresh/rollback harness；T1304/A206 background_jobs/background_job_attempts/dead_letter_jobs, transactional_outbox dispatch, `score_recompute` enqueue/execution contract, `data_snapshot_refresh` enqueue/execution contract, `curated_ingestion_refresh` execution contract, `calibration_run` enqueue/execution contract, job_scheduler.py lease/heartbeat/retry/dead-letter/graceful release contract and `apps.worker` health/once/supervise contract；T1307/A209 browser+worker soak smoke harness。

## 仍未解决（7）

- 部署与预算、身份认证、商业数据许可、生产数据规模、图渲染库最终基准、战略模型有效性、140 个对象的真实关系接入。

## 状态文件

- `data/task_backlog.csv`：Codex 开发任务、依赖、Gate、Acceptance ID。
- `data/development_status_ledger.csv`：规格/原型/实现/验证四种状态。
- `data/resolved_unresolved_register.csv`：决策、Open issue、Deferred。
- `data/release_gate_catalog.csv`：G0-G9 进入/退出和停止条件。
- `docs/phase/V5_TASK_PACK_SYNCHRONIZATION.md`：v5 压缩包研究、生产缺口和 T1300-T1309/A201-A211 映射。

Codex 每完成一个任务，必须同步状态、测试证据、风险和验收，不得只在聊天中说明。
