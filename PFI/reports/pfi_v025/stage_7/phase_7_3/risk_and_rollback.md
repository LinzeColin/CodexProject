# Phase 7.3 风险与回滚

## 风险

- 参数中心或互联图若通过 sidecar HTML 交付，会绕过正式 Shell 的 route、identity 与缓存合同。
- 历史统计若与当前 read model 混合，可能把旧事实误报为当前结果；所有指标必须标记来源、数据范围和四类 hash。
- 同一经济事件若被重复计入，会放大指标；lineage 必须证明 `same_economic_event_per_metric_max_count=1`。
- not-ready 指标若显示 0，会制造虚假财务结论；必须保持 `value=null` 并显示可行动中文阻断原因。
- 浏览器 history 若把 query 编码进 pathname，会破坏深链恢复；route 与 query 必须分离并保留 `domain/node/metric`。
- Playwright raw response/trace 可能捕获私有值或绝对路径；trace 必须重写清洗并复扫，失败即删除并停止。

## 回滚

1. revert 本 Phase 单一提交，包括只读 use case、Runtime API endpoint、正式 Shell 三条路由、测试、release identity 与 evidence。
2. 不修改或删除 canonical 财务源；本 Phase 无 schema migration、无数据库写入。
3. 删除 Phase 7.3 本地 evidence 即可撤销报告产物；不得触碰私有 runtime 数据。
4. 保留 Phase 7.1/7.2 candidate baseline；不得以回滚为由进入 Stage 7 whole-stage review、Stage 8、push 或重装 App。

## 当前边界

- Phase 7.3=`candidate_pass`；Stage 7 phase tasks=`12/12 candidate_complete`，但 Stage 7=`in_progress`，whole-stage review=`not_started`。
- `finder_used=false`、`external_network_performed=false`、`push_performed=false`、`app_install_performed=false`。
- `real_financial_data_read=true`、`real_financial_data_mutated=false`、`database_changed=false`、`financial_values_persisted=0`。
