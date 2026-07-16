# PFI v0.2.5 Stage 10 Phase 10.2 依赖 Diff 与缓存

## Run Contract

- Phase：`V025-S10-P10.2`
- Tasks：`S10-P2-T1..T4`
- Acceptance：`ACC-PFI-V025-STAGE10-WHOLE-REVIEW`；本轮只形成 Phase candidate，不执行整阶段验收。
- Risk：`T2_RUNTIME_DEPENDENCY_CACHE_PRIVACY`
- 实现基线：`67b86b4b119e6782d6171cecb286435f8e729f80`
- 产品提交：`a64f3b51576ebe507bd65b3f5b54c5b2a3b74c41`
- 明确不做：Phase 10.3 trace/log/failure matrix、Stage 10 whole-stage review、真实财务库验收、公式/参数/模型值变更、外网、push、PFI.app install、production/final acceptance。

## 九域依赖事实

- `PFIV025DependencyRegistryV1` 固定登记 `raw/source/ledger/interconnection/parameter/formula/fx/read_model/report` 九域、上游 DAG、直接受影响指标、缓存域和安全 provenance。
- `raw/source/ledger` 的生产观察器只以 SQLite `mode=ro + query_only` 读取 hash/ID/status 等非金额投影；不读取或返回 amount、description、raw bytes，也不创建或迁移数据库。
- `parameter/formula/fx/report` 只哈希本地 canonical 文件；`interconnection` 在 economic-event adapter 未完成时保持 `blocked_economic_event_adapter`，不伪造 ready。
- snapshot 只含 hash、status、aggregate count 与固定 provenance；明确 `contains_private_values=false`、`financial_values_emitted=0`、`network_calls=0`。

## 精确 Diff 与零动作路径

- diff 只把实际 hash 变化登记为 `changed_domains`，再沿 DAG 计算 `recompute_domains`；指标影响使用 changed-domain 的显式 metric map，避免把交易原始层变化误报为全部指标变化。
- 九域逐一变化均通过行为测试；`raw` 变化只影响 `consumption_outflow_cny/report_summary_status`，不会误报净资产、现金或投资指标。
- 完全相同 snapshot 得到 `no_diff=true`、`recompute_scope=none`、空 impacted metrics/cache scopes，且 network/Codex/LLM call count 均为 0。
- parameter/formula/fx/read-model 变化覆盖完整指标集合是显式依赖结果，不被标记为“误报”；report 单域变化只失效 report render。

## Streamlit 与前端缓存闭环

- 既有 Stage 1 `st.cache_data(ttl=30, persist=None)` 适配器继续作为真实 Streamlit 缓存层；其 composite key 的 `data_hash` 现绑定九域 `dependency_snapshot_hash`。
- release-cache CLI 与 runtime API 从同一个 atomic context 生成 dimensions/snapshot；普通 runtime API 在显式 DB path 存在时绑定该 path，避免 cache policy 与 operational authority 脱节。
- 前端 `version.js` fail closed 校验九域 hash、snapshot/data hash 等值、parameter/formula/fx/read-model 分量等值、Streamlit/前端/process key 等值、TTL=30、非持久化以及 ordinary/no-diff 零网络/零 Codex/零 LLM。
- release-critical frontend/backend closure 已纳入 registry 与 runtime diff 模块；frontend/backend manifest hash 均与当前源文件闭合。

## 验证结论与边界

- Phase target `7/7`；Phase 10.1、Stage 1 cache/release identity/whole-review remediation 合并回归 `45/45`；Stage 7 import/holding 与 Stage 9 report contract 回归 `40/40`；修复 Streamlit AppTest 对 `__main__` 的测试间污染后最终合并 `85/85`。
- Node 在模拟 DOM 中执行真实 `version.js`，接受完整 policy，并拒绝 ordinary-run network flag 漂移；不是字符串存在性测试。
- SQLite 验证只使用执行 canonical migration 后的空隔离结构库；观察前后数据库 SHA-256 不变，未生成 WAL/SHM，未放入虚构财务行。
- 本 Phase 没有读取 canonical 私有 PFI DB，也没有财务验收；tracked evidence 使用 isolated-empty hash snapshot，不能解释为真实数据 ready。
- 未使用 Finder、LaunchServices 或 GUI 文件操作。普通 dependency/cache 审计没有网络调用；回归验证仅使用临时本机 loopback、没有外网；未执行 push、install 或交易动作。

## 当前状态与下一 Gate

- Phase 10.2=`candidate_pass`；Stage 10=`8/12 in_progress`；v0.2.5=`128/156 (82.05%)`。
- Phase 10.3 与 Stage 10 whole-stage independent review/user acceptance 均 `not_started`。
- 下一唯一工作单元：`S10-P3-T1`，Acceptance 仍为 `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`。
