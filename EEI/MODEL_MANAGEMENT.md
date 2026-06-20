# 模型管理、公式、参数、门槛与即时刷新

## 结论与使用路径

默认使用均衡配置；用户可在 `模型与参数` 页面在线修改，也可编辑 `config/model_runtime_defaults.yaml` 后 dry-run 导入。任何修改先预览，不覆盖历史版本；全局激活完成后通过原子快照刷新所有可视化。

## 模型清单

| 模型 | 名称 | 公式 | 评分对象 | 作用 | 状态 |
|---|---|---|---|---|---|
| MOD-001 | 综合研究优先级 | F-NP-001 | node | 节点大小、排序、路径、Watchlist | active |
| MOD-002 | 证据质量 | F-EQ-001 | evidence | 证据等级、发布门槛、解释 | active |
| MOD-003 | 时间相关性 | F-RF-001 | fact_event | 所有时间衰减 | active |
| MOD-004 | 关系重要性 | F-EM-001 | relationship | 边显示、宽度、Top-N | active |
| MOD-005 | 供应链关键性 | F-SC-001 | relationship_path | 瓶颈、替代性、关键路径 | active |
| MOD-006 | 控制影响 | F-CI-001 | entity_relationship | 所有权与控制视图 | active |
| MOD-007 | 资本动量 | F-CM-001 | entity_period | 资金与并购视图 | active |
| MOD-008 | 政策暴露 | F-PE-001 | entity_jurisdiction | 政策雷达和风险 | active |
| MOD-009 | 战略信号 | F-SS-001 | entity_theme_period | 战略主题和反证 | active |
| MOD-010 | 变化告警 | F-AS-001 | change_event | 变化优先级和 Watchlist 告警 | active |
| MOD-011 | 依赖风险 | F-DR-001 | entity_path | 跨关系族依赖风险 | planned |


## 配置与文档文件

| 文件 | 作用 |
|---|---|
| `data/model_registry.csv` | 模型目录、公式、对象、输出和状态 |
| `data/formula_registry.csv` | 完整公式、范围、缺失值和默认阈值 |
| `data/parameter_catalog.csv` | 75 个可调/治理参数、范围、步长、在线控件与刷新范围 |
| `data/threshold_registry.csv` | 17 个核心发布/显示/视觉/性能门槛及其机器参数映射 |
| `config/model_runtime_defaults.yaml` | 人类可编辑导入模板 |
| `config/model_profiles/balanced-v2.json` | 默认机器配置 |
| `config/thresholds/default-v2.json` | 默认阈值 |
| `specs/model_config_schema.json` | 配置契约 |
| `scripts/compile_model_runtime_defaults.py` | YAML 校验/编译 |

## 修改流程

```bash
python scripts/compile_model_runtime_defaults.py --dry-run
python scripts/validate_model_config.py config/model_profiles/balanced-v2.json config/thresholds/default-v2.json
python scripts/apply_model_config.py --dry-run --profile config/model_profiles/balanced-v2.json --thresholds config/thresholds/default-v2.json
```

在线修改分五步：草稿输入 -> 即时预览 -> 会话应用 -> 保存不可变版本 -> 激活全局快照。失败不得部分发布。

当前 T1303/A204-A205 生产切片已开始：PostgreSQL 通过 `active_analysis_contexts` 保存全局 active profile、data snapshot、score snapshot、`refresh_token` 和 `refresh_generation`；`POST /v1/scoring/profiles/{profileVersionId}/activate` 在单事务内切换 active profile、创建 score snapshot、写入 operation log 并推进 refresh token；`POST /v1/scoring/profiles/{profileVersionId}/rollback` 使用同一事务内核执行专用回滚；`POST /v1/scoring/recompute` 校验当前 active profile 和 refresh token 后，以 active context 生成幂等 `score_recompute` 后台任务；`scripts/job_scheduler.py run-once --job-type score_recompute` 已能执行 worker handler，创建新的 `scoring_runs`、写入 `relationship_fact_candidate` 的 `score_results`、记录 `execute_score_recompute` operation log，并推进 active context refresh token。带过期 `expected_active_profile_version_id` 或 `client_refresh_token` 的请求返回 409，旧 active profile 保持不变；worker 发现 stale context 时以 `skipped_stale_context` 完成，避免过期 job 无限重试。前端模型中心已具备 API-first active-context hydration、事务激活、rollback 控件、recompute 入队控件和 stale refresh mock E2E；首页商业版图 `/v1/explore` 请求也会携带当前 scoring profile id。在线编辑、worker 数据刷新/outbox、部署唤醒和 live FastAPI/PostgreSQL 跨页面真实 refresh E2E 仍未完成。

## 关键门槛

- 顶层权重合计 `1.0 ± 0.0001`；单项不超过 `0.70`。
- 分数/阈值 `0-100`；半衰期 `30-1825` 天。
- 未知和缺失不得填 0；按可用输入归一化并显示 coverage。
- 推断关系默认需要至少 2 个相互独立来源。
- 浏览器预览 P95 `<250ms`；会话应用 P95 `<700ms`。
- 大范围重算继续显示上一个成功快照，完成后原子切换。
- 当前 `score_recompute` 已具备 API/job 入队、幂等键、409 stale-client 防护、UI 控件和 worker 执行 handler；但在部署唤醒、transactional outbox 和 4h/24h soak 完成前，不得把该能力解释为无人值守生产刷新闭环。

## v5 生产运行参数

新增参数覆盖 T1300-T1309：迁移锁与回滚要求、实体解析置信度、独立来源数量、scheduler lease/heartbeat/retry/dead-letter、保存视图冲突重试、10k/100k/1m 关系规模预算、4h/24h soak 时长和品牌清权开关。这些参数记录在 `data/parameter_catalog.csv`，当前只是 MVP 运行合同，不能替代尚未实现的生产服务。

详细文档：`docs/24_MODEL_FORMULA_PARAMETER_THRESHOLD_CENTER.md`、`docs/25_LIVE_RECALCULATION_REFRESH_ARCHITECTURE.md`。
