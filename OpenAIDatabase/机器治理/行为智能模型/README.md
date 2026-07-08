# 行为智能模型

用于放置 facets、semantic clusters、latent signals、collaboration quality、自我迭代和
低价值循环识别的模型配置。

当前 S09 P1 已完成。facet/canonical events 的数据契约已定义在
`机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`，中文解释位于
`人类可读/12_Facet字段与事件语义说明.md`，facet extractor 已实现为
`scripts/extract_memory_atlas_facets.py`，并为 events 输出补齐
`lightweight_evidence_refs`。

S05 P1 只定义 facets 和 canonical events schema，不实现 extractor，不生成
`data/derived/behavior_intelligence/events.json`，不生成 fake events，不修改 raw。

S05 P2 已生成 `data/derived/behavior_intelligence/events.json`。当前 extractor 从
public raw、processed manifest 和 derived snapshot 中抽取事件；缺失来源只写
source_status missing reason，不生成 fake events，不修改 raw，不改变首屏 UI。

S05 P3 在每条 event 中保留 `source_id`、`record_id` 和 `evidence_refs`，证据引用
只指向 raw、manifest、derived 或 missing reason，不实现 Raw-to-Insight Replay UI。
S05 P3 仍不生成 fake events，不修改 raw，不改变首屏 UI。

S05 Review 已通过，确认行为事件与 facets 可被后续 cluster、ROI、latent、visualization
复用。

S06 P1 已完成：`scripts/build_memory_atlas_clusters.py` 从
`data/derived/behavior_intelligence/events.json` 生成
`data/derived/behavior_intelligence/clusters.json`。输出包含主题簇和层级簇，每个
cluster 均保留中文摘要、代表事件、`source/time/project/task/language` 过滤维度和
`evidence_refs`。S06 P1 不识别低价值循环，不生成机会卡片。

当前 S06 P2 已完成：`scripts/build_memory_atlas_low_value_loops.py` 从 events 和
clusters 生成 `data/derived/behavior_intelligence/low_value_loops.json`。输出包含
低价值循环候选、Decision Debt Ledger 和 Action Half-Life，覆盖重复返工、反复讨论未落地、
过度优化和 scope creep。S06 P2 不做心理诊断，不生成 opportunity cards。

当前 S06 P3 已完成：`scripts/build_memory_atlas_opportunities.py` 从 events、clusters
和 low-value loops 生成 `data/derived/behavior_intelligence/opportunities.json`。输出包含
机会发现候选和 why-not-now 卡片，覆盖 automation、productization、template、
compounding 和 defer。S06 P3 不接外部经济数据库，不做心理诊断，不生成无穷压力清单。

当前 S06 Review 已完成：`scripts/build_memory_atlas_data.py` 将主题簇、低价值循环和
机会线索汇总为 `data/derived/visualization/memory_atlas.json` 的
`behavior_intelligence`。Memory Atlas 首页可显示有证据的主题簇、低价值循环和机会线索。
S07 P1 已使用 S06 的 clusters、low-value loops 和 opportunities 生成
Personal Economic Proxy，输出 `data/derived/economic_proxy/personal_economic_proxy.json`。
S07 P2 继续使用 S06 behavior outputs 和 S07 P1 Personal Economic Proxy，生成
Information ROI 与 Visual ROI Gate 输出
`data/derived/information_roi/information_roi_gate.json`。该输出判断 insight、card、chart
是否有足够决策价值；没有决策价值的图表不进 P0。S07 P3 已完成 Formula What-if
配置预览，继续使用 Personal Economic Proxy 与 Information ROI 输出生成
`data/derived/economic_proxy/formula_what_if_preview.json`，用于查看不同权重假设下的
内部 proxy 分变化，不修改 active formula config。S07 Review 已完成，确认
Personal Economic Proxy、Information ROI 和 Formula What-if 均可由行为智能派生输入解释，
且不接入外部经济数据库。

S08 P1 已完成：`机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json`
定义 Codex/Agent 协作质量指标，`scripts/build_memory_atlas_agent_collaboration.py` 生成
`data/derived/agent_collaboration/agent_collaboration_quality_report.json`。指标覆盖
`planning_clarity`、`execution_clarity`、`review_burden`、`rework_count`、
`scope_clarity`、`testability` 和 `rollbackability`，并用 evidence refs 支撑中文解释。
source summary 支持 `chatgpt`、`codex` 和 `other_agent` 通用字段；future agent 没有真实
证据时只保留缺失原因，不生成 fake events 或 fake scores。S08 P1 不创建复杂 Delegation
Contract UI，不创建多 agent 系统，不修改 raw。S08 P1 的下一历史 gate 是 S08 P2，当前已完成。

当前 S08 P2 已完成：`机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json`
定义轻量授权边界，`scripts/build_memory_atlas_agent_authorization.py` 生成
`data/derived/agent_collaboration/agent_authorization_boundary_report.json`。S08 P2 明确
proposal 必须经人类授权并进入 `approved_by_human` 后才能 apply，raw 不可修改，raw
永远不能成为 apply target。S08 P2 不执行 proposal apply，不实现复杂 Delegation
Contract UI，不创建多 agent 系统，不生成 stage flight recorder。S08 P2 的下一历史 gate 是
S08 P3，当前已完成。

当前 S08 P3 已完成：`机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json`
定义 lightweight stage flight recorder 字段，`scripts/build_memory_atlas_stage_flight.py`
生成 `data/derived/agent_collaboration/stage_flight_recorder.json`。S08 P3 只保留 10 个轻量字段、
3 条 phase records、evidence refs 和 validation refs，不携带 raw/transcript 载荷，不生成臃肿
人类文档，只在开发记录中总结必要信息。

当前 S08 Review 已完成：`docs/reviews/memory_atlas_v1_2_s08_review.md` 复审
Codex/Agent 协作质量、授权边界和 stage flight recorder。S08 Review 确认系统能解释
ChatGPT/Codex/其他 agent 的协作质量与边界，且不创建多 agent 系统、不创建复杂 Delegation
Contract UI、不执行 proposal apply、不修改 raw、不上传 GitHub main。下一步是 S09 P1。

当前 S09 P1 已完成：`机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json`
定义潜性信号字段和 Evidence Strength Badge，`scripts/build_memory_atlas_latent_signals.py`
生成 `data/derived/behavior_intelligence/latent_signals.json`。每条 signal 都有 claim、
supporting evidence、contradicting evidence、alternative explanation、confidence 和
next validation。S09 P1 不输出心理诊断或人格标签，不创建 self-iteration suggestions，
不创建 decision debt ledger。下一步是 S09 P2。
