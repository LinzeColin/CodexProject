# 机器治理

这里放 Memory Atlas v1.2 的机器可读参数、公式、数据契约、同步配置、验收门禁和运行证据。

本目录不替代 apps/scripts/tests/config/data/docs/governance。现有运行代码、测试、配置、
数据和旧治理目录继续留在原位置。

## 子目录

- `参数与公式/`：公式、权重、阈值和参数解释。
- `数据契约/`：source、raw、derived、reports、visualization 的 schema 或契约。
- `同步与备份/`：ChatGPT、Codex、后续其他 agent 的 source registry 和同步策略。
- `可视化配置/`：图表、human question map、visual ROI gate 的机器配置。
- `行为智能模型/`：facets、clusters、latent signals、collaboration quality 的模型配置。
- `运行门禁/`：stage gates、stop conditions、rollback 和需求冻结。
- `测试与验收/`：validator、acceptance matrix 和测试说明。
- `证据与日志/`：run evidence、audit logs、manifest/hash 和 stage evidence。

## 当前阶段

当前为 S08 P2。任务 ID 为 `MA-V12-S08P2`，验收 ID 为
`ACC-MA-V12-S08P2`，validator 为 `validate:v1.2-s08-p2`。
S01 整体复审已通过，S02 整体复审已通过，S03 P1/P2/P3
整体复审已通过。S04 P1 已建立 ChatGPT 只读同步和 official export fallback。
S04 P2 已建立 Codex local sync、future-agent minimal adapter、raw + derived + run log
输出合同，以及 `scripts/atlasctl.py` 的 codex/future-agent dry-run 入口。
S04 P3 已建立 GitHub backup dry-run/apply 本地控制面；apply 只做本地 commit，
不执行远端 push。S04 整体复审已通过。S05 P1 已定义 facet/canonical event
schema。S05 P2 已实现 `scripts/extract_memory_atlas_facets.py`，并通过
`scripts/atlasctl.py analyze --stage facets` 生成
`data/derived/behavior_intelligence/events.json`。S05 P3 已为每条 event 补齐
轻量 `evidence_refs`，用于追溯 raw、manifest、derived 或 missing reason。
S05 Review 已通过，确认 S05 events 与 facets 可被后续 cluster、ROI、latent、
visualization 复用。S06 P1 已生成主题簇和层级簇，支持
`source/time/project/task/language` 过滤合同，并保留 cluster `evidence_refs`。
S06 P2 已生成低价值循环候选、Decision Debt Ledger 和 Action Half-Life，输出
`data/derived/behavior_intelligence/low_value_loops.json`。S06 P3 已生成机会发现候选
和 为什么不是现在 卡片，输出
`data/derived/behavior_intelligence/opportunities.json`。S06 Review 已完成，确认
`data/derived/visualization/memory_atlas.json` 的 `behavior_intelligence` 可显示
主题簇、低价值循环和机会线索。S07 P1 已完成 Personal Economic Proxy，输出
`data/derived/economic_proxy/personal_economic_proxy.json`，公式配置为
`机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`。S07 P2 已完成
Information ROI 与 Visual ROI Gate，输出
`data/derived/information_roi/information_roi_gate.json`，公式配置为
`机器治理/参数与公式/information_roi.v1_2_s07_p2.json`，Visual ROI Gate 配置为
`机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`。S07 P3 已完成 Formula
What-if 配置预览，配置为
`机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`，输出为
`data/derived/economic_proxy/formula_what_if_preview.json`。S07 Review 已完成，确认
Personal Economic Proxy、Information ROI、Visual ROI Gate 和 Formula What-if 均满足
S07 stage gate，且没有外部经济数据库依赖、没有精确收入预测、没有财务建议。S08 P1
已完成 Codex/Agent 协作质量指标，配置为
`机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json`，输出为
`data/derived/agent_collaboration/agent_collaboration_quality_report.json`，用于解释
planning、execution、review、rework、scope clarity、testability 和 rollbackability。
S08 P2 已完成授权边界，配置为
`机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json`，输出为
`data/derived/agent_collaboration/agent_authorization_boundary_report.json`。S08 P2 明确
raw 不可修改，proposal 必须有人类授权并进入 `approved_by_human` 后才能 apply；本 phase
不执行 proposal apply，不创建复杂 Delegation Contract UI，不创建多 agent 系统，不生成
stage flight recorder。下一步是 S08 P3。

当前机器产物：

- `数据契约/source_data_model.v1_2_s02_p1.json`
- `数据契约/facet_event_schema.v1_2_s05_p1.json`
- `../data/derived/behavior_intelligence/events.json`
- `../data/derived/behavior_intelligence/clusters.json`
- `../data/derived/behavior_intelligence/low_value_loops.json`
- `../data/derived/behavior_intelligence/opportunities.json`
- `../data/derived/visualization/memory_atlas.json`
- `../data/derived/economic_proxy/personal_economic_proxy.json`
- `../data/derived/economic_proxy/formula_what_if_preview.json`
- `../data/derived/information_roi/information_roi_gate.json`
- `../data/derived/agent_collaboration/agent_collaboration_quality_report.json`
- `../data/derived/agent_collaboration/agent_authorization_boundary_report.json`
- `参数与公式/personal_economic_proxy.v1_2_s07_p1.json`
- `参数与公式/information_roi.v1_2_s07_p2.json`
- `参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`
- `可视化配置/visual_roi_gate.v1_2_s07_p2.json`
- `行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json`
- `行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json`
- `同步与备份/sync_source_registry.json`
- `同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- `../人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`
- `../人类可读/06_Raw明文公开与只读归档说明.md`
- `../人类可读/07_凭证排除说明.md`
- `../人类可读/08_Raw机器账本说明.md`
- `../人类可读/09_ChatGPT只读同步与官方导出Fallback.md`
- `../人类可读/10_Codex与FutureAgent同步.md`
- `../人类可读/11_GitHub备份DryRun与Apply.md`
- `../人类可读/12_Facet字段与事件语义说明.md`
- `../人类可读/13_行为簇与层级簇说明.md`
- `../人类可读/14_低价值循环与DecisionDebt说明.md`
- `../人类可读/15_机会发现与为什么不是现在卡片.md`
- `../人类可读/16_PersonalEconomicProxy公式说明.md`
- `../人类可读/17_InformationROI与VisualROIGate说明.md`
- `../人类可读/18_FormulaWhatIf配置预览说明.md`
- `../人类可读/19_Agent协作质量指标说明.md`
- `../人类可读/20_Agent授权边界说明.md`
- `../data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `data/public_raw/README.md`
- `../docs/reviews/memory_atlas_v1_2_s02_review.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md`
- `../docs/reviews/memory_atlas_v1_2_s03_review.md`
- `../docs/reviews/memory_atlas_v1_2_s04_p1_chatgpt_sync.md`
- `../docs/reviews/memory_atlas_v1_2_s04_p2_codex_agent_sync.md`
- `../docs/reviews/memory_atlas_v1_2_s04_p3_github_backup.md`
- `../docs/reviews/memory_atlas_v1_2_s04_review.md`
- `../docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md`
- `../docs/reviews/memory_atlas_v1_2_s05_p2_facet_extractor.md`
- `../docs/reviews/memory_atlas_v1_2_s05_p3_evidence_refs.md`
- `../docs/reviews/memory_atlas_v1_2_s05_review.md`
- `../docs/reviews/memory_atlas_v1_2_s06_p1_cluster_builder.md`
- `../docs/reviews/memory_atlas_v1_2_s06_p2_low_value_loops.md`
- `../docs/reviews/memory_atlas_v1_2_s06_p3_opportunity_discovery.md`
- `../docs/reviews/memory_atlas_v1_2_s06_review.md`
- `../docs/reviews/memory_atlas_v1_2_s07_p1_economic_proxy.md`
- `../docs/reviews/memory_atlas_v1_2_s07_p2_information_roi.md`
- `../docs/reviews/memory_atlas_v1_2_s08_p1_agent_collaboration.md`
- `../docs/reviews/memory_atlas_v1_2_s08_p2_authorization_boundary.md`
- `../docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md`
- `../docs/reviews/memory_atlas_v1_2_s07_review.md`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`
- `scripts/raw_archive_manifest.py`
- `scripts/sync_chatgpt_memory_data.py`
- `scripts/sync_future_agent_data.py`
- `scripts/github_backup.py`
- `scripts/extract_memory_atlas_facets.py`
- `scripts/build_memory_atlas_clusters.py`
- `scripts/build_memory_atlas_low_value_loops.py`
- `scripts/build_memory_atlas_opportunities.py`
- `scripts/build_memory_atlas_economic_proxy.py`
- `scripts/build_memory_atlas_agent_authorization.py`
- `scripts/atlasctl.py`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p1.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p2.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_review.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p1.cjs`

`运行门禁/v1.2需求冻结清单.json` 继续固定：

- 四线范围。
- 14 Stage 与每次 run 最多一个 phase 的执行规则。
- raw 公开授权。
- 凭证排除。
- 后续其他 agent 数据源扩展规则。

下一步是 S08 P3；本目录仍不替代 apps/scripts/tests/config/data/docs/governance。
