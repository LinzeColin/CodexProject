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

当前为 v1.2 Final Review。任务 ID 为 `MA-V12-FINAL-REVIEW`，验收 ID 为
`ACC-MA-V12-FINAL-REVIEW`，validator 为 `validate:v1.2-final-review`。状态为
`v1_2_final_review_passed_pending_github_main_sync_no_upload_yet`。Final Review 已完成
四线14Stage 的 `S01-S14 Review` 链复审，并确认 raw append-only、credential audit、
Chinese UX、visual ROI、report contract、proposal apply、owner-daily 和 final audit 主题。
下一步是 pending GitHub main sync、app reinstall 和 local cleanup；进入该 phase 前需要
remote branch reconciliation required。

No GitHub main upload。No remote push。No raw mutation。

历史复验兼容记录：

当前为 S14 Review。任务 ID 为 `MA-V12-S14-REVIEW`，验收 ID 为
`ACC-MA-V12-S14-REVIEW`，validator 为 `validate:v1.2-s14-review`。状态为
`stage_s14_review_passed_pending_v1_2_final_review_no_github_main_upload`。S14 Review 已完成
S14 P1、S14 P2、S14 P3 的整体复审。`owner-daily`、`atlasctl_unified_cli.v1_2_s14_p1`、
`atlasctl_final_audit.v1_2_s14_p2` 和 `stage_pass_gate_status.v1_2_s14_p3.json` 共同满足
S14 stage gate。下一步是 pending v1.2 Final Review。

No GitHub main upload。No remote push。No raw mutation。

当前为 S13 Review。任务 ID 为 `MA-V12-S13-REVIEW`，验收 ID 为
`ACC-MA-V12-S13-REVIEW`，validator 为 `validate:v1.2-s13-review`。状态为
`stage_s13_review_passed_pending_s14_no_github_main_upload`。S13 Review 已完成
Proposal 状态机、Diff narrator 和 Apply 与回滚的整体复审。`proposal_state_machine.v1_2_s13_p1`、
`diff_narrator.v1_2_s13_p2` 和 `proposal_apply.v1_2_s13_p3` 共同满足 S13 stage gate。
下一步只允许进入 pending S14 P1。

No GitHub main upload。No remote push。No raw mutation。

历史复验兼容记录：S13 P3 完成时当前为 S13 P3。任务 ID 为 `MA-V12-S13P3`，验收 ID 为
`ACC-MA-V12-S13P3`，validator 为 `validate:v1.2-s13-p3`。状态为
`phase_s13_p3_apply_rollback_completed_pending_s13_review`。S13 P3 已完成 Apply 与回滚，
合同版本为 `proposal_apply.v1_2_s13_p3`。`sample_unauthorized` 未授权 fail-closed，
`sample` 授权 dry-run 可进入 apply、validation 和 rollback point 路径。此句只用于保留
已完成 phase 的复验语义，不代表当前阶段。当时下一步为 pending S13 Review。S13 Review
已完成，下一步是 S14 P1。

No GitHub main upload。No remote push。No raw mutation。

历史复验兼容记录：S13 P2 完成时当前为 S13 P2。任务 ID 为 `MA-V12-S13P2`，验收 ID 为
`ACC-MA-V12-S13P2`，validator 为 `validate:v1.2-s13-p2`。状态为
`phase_s13_p2_diff_narrator_completed_pending_s13_p3`。S13 P2 已完成 Diff narrator，
合同版本为 `diff_narrator.v1_2_s13_p2`。每个 proposal 都有中文解释：改了什么、
为什么改、影响什么、如何验证、如何回滚；机器 diff 保留在治理证据文件，不进入人类首页。
此句只用于保留已完成 phase 的复验语义，不代表当前阶段。S13 P3 已完成，下一步是
S13 Review。

No GitHub main upload。No remote push。No raw mutation。No proposal apply execution。

历史复验兼容记录：S13 P1 完成时当前为 S13 P1。任务 ID 为 `MA-V12-S13P1`，验收 ID 为
`ACC-MA-V12-S13P1`，validator 为 `validate:v1.2-s13-p1`。状态为
`phase_s13_p1_proposal_state_machine_completed_pending_s13_p2`。S13 P1 已完成
Proposal 状态机，合同版本为 `proposal_state_machine.v1_2_s13_p1`。proposal 默认进入
`pending_human_review`，只有人类授权后才能进入 `approved_by_human`；本 phase 只产出
状态机 dry-run 报告，不执行 apply、diff narrator 或 rollback。此句只用于保留已完成 phase
的复验语义，不代表当前阶段。S13 P2 已完成，下一步是 S13 P3。

No GitHub main upload。No remote push。No raw mutation。No proposal apply execution。

历史复验兼容记录：S12 Review 完成时当前为 S12 Review。任务 ID 为
`MA-V12-S12-REVIEW`，验收 ID 为 `ACC-MA-V12-S12-REVIEW`，validator 为
`validate:v1.2-s12-review`。状态为
`stage_s12_review_passed_pending_s13_no_github_main_upload`。S12 Review 已完成
Command Palette、Personalization Prompt 和 ChatGPT 深度探索复审；S12 P1、S12 P2、
S12 P3 均通过，`prefill_only` 保持 no-send，`auto_submit` 保持 FAIL_CLOSED。
此句只用于保留已完成 review 的复验语义，不代表当前阶段。S13 P1 已完成，下一步是 S13 P2。

No silent send。No cookie/token/secret export。No GitHub main upload。No remote push。
No raw mutation。No proposal apply execution。

历史复验兼容记录：S12 P3 完成时当前为 S12 P3。任务 ID 为 `MA-V12-S12P3`，验收 ID 为
`ACC-MA-V12-S12P3`，validator 为 `validate:v1.2-s12-p3`。状态为
`phase_s12_p3_chatgpt_deep_explore_completed_pending_s12_review`。S12 P3 已完成
`chatgpt_deep_explore.v1_2_s12_p3`，提供用户触发的 ChatGPT 深度探索入口。默认
`prefill_only`，`auto_submit` 受配置和显式确认控制。此句只用于保留已完成 phase 的复验语义，
不代表当前阶段。S12 Review 已完成，下一步是 S13 P1。

历史复验兼容记录：S12 P2 完成时当前为 S12 P2。任务 ID 为 `MA-V12-S12P2`，验收 ID 为
`ACC-MA-V12-S12P2`，validator 为 `validate:v1.2-s12-p2`。状态为
`phase_s12_p2_personalization_prompt_completed_pending_s12_p3`。S12 P2 已完成
`personalization_prompt.v1_2_s12_p2`，生成 ChatGPT、Codex、other agent 三类 prompt，
并包含中文人类说明和机器可复制文本。下一步只允许进入 S12 P3。

No GitHub main upload。No remote push。No raw mutation。No proposal apply execution。

历史复验兼容记录：S12 P1 完成时当前为 S12 P1。任务 ID 为 `MA-V12-S12P1`，验收 ID 为
`ACC-MA-V12-S12P1`，validator 为 `validate:v1.2-s12-p1`。状态为
`phase_s12_p1_command_palette_completed_pending_s12_p2`。S12 P1 已完成
`command_palette.v1_2_s12_p1` 命令面板，命令只包含同步 ChatGPT、同步 Codex、
生成本周报告、查看待授权 proposal 和生成 personalization prompt。当时下一步是 S12 P2。
此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

历史复验兼容记录：S11 Review 完成时当前为 S11 Review。任务 ID 为 `MA-V12-S11-REVIEW`，
验收 ID 为 `ACC-MA-V12-S11-REVIEW`，validator 为 `validate:v1.2-s11-review`。状态为
`stage_s11_review_passed_pending_s12_no_github_main_upload`。S11 Review 已完成
S11 P1、S11 P2、S11 P3 和 S11 P4 复审，确认 12 张 P0 图谱均绑定中文问题、行动价值、
Visual ROI Gate 和 `source/time/project/task` 过滤。此句只用于保留已完成 review
的复验语义，不代表当前阶段。S12 P2 是下一阶段。

历史复验兼容记录：S11 P4 完成时当前为 S11 P4。任务 ID 为 `MA-V12-S11P4`，验收 ID 为
`ACC-MA-V12-S11P4`，validator 为 `validate:v1.2-s11-p4`。状态为
`phase_s11_p4_human_question_map_completed_pending_s11_review`。S11 P4 已完成
Human Question Map，运行时合同为 `human_question_map.v1_2_s11_p4`；12 张 P0 图谱均绑定
中文问题、行动价值、Visual ROI Gate 和 `source/time/project/task` 过滤。下一步只允许进入
S11 Review。

No GitHub main upload。No raw mutation。No proposal apply execution。

历史复验兼容记录：S11 P3 完成时当前为 S11 P3，任务 ID 为 `MA-V12-S11P3`，
验收 ID 为 `ACC-MA-V12-S11P3`，validator 为 `validate:v1.2-s11-p3`，
下一步是 S11 P4；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

历史复验兼容记录：S11 P2 完成时当前为 S11 P2，任务 ID 为 `MA-V12-S11P2`，
验收 ID 为 `ACC-MA-V12-S11P2`，validator 为 `validate:v1.2-s11-p2`，
下一步是 S11 P3；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

历史复验兼容记录：S11 P1 完成时当前为 S11 P1，任务 ID 为 `MA-V12-S11P1`，
验收 ID 为 `ACC-MA-V12-S11P1`，validator 为 `validate:v1.2-s11-p1`，
下一步是 S11 P2；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

历史复验兼容记录：S10 Review 完成时当前为 S10 Review，任务 ID 为
`MA-V12-S10-REVIEW`，验收 ID 为 `ACC-MA-V12-S10-REVIEW`，validator 为
`validate:v1.2-s10-review`，下一步是 S11 P1；此句只用于保留已完成 review
的复验语义，不代表当前阶段。

历史复验兼容记录：S10 P3 完成时当前为 S10 P3，任务 ID 为 `MA-V12-S10P3`，
验收 ID 为 `ACC-MA-V12-S10P3`，validator 为 `validate:v1.2-s10-p3`，
下一步是 S10 Review；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

历史复验兼容记录：S10 P2 完成时当前为 S10 P2，任务 ID 为 `MA-V12-S10P2`，
验收 ID 为 `ACC-MA-V12-S10P2`，validator 为 `validate:v1.2-s10-p2`，
下一步是 S10 P3；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

历史复验兼容记录：S10 P1 完成时当前为 S10 P1，任务 ID 为 `MA-V12-S10P1`，
验收 ID 为 `ACC-MA-V12-S10P1`，validator 为 `validate:v1.2-s10-p1`，
下一步是 S10 P2；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

历史复验兼容记录：S09 P3 完成时当前为 S09 P3，任务 ID 为 `MA-V12-S09P3`，
验收 ID 为 `ACC-MA-V12-S09P3`，validator 为 `validate:v1.2-s09-p3`，
下一步是 S09 Review；此句只用于保留已完成 phase 的复验语义，不代表当前阶段。
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
stage flight recorder。S08 P3 已完成 lightweight stage flight recorder，字段配置为
`机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json`，输出为
`data/derived/agent_collaboration/stage_flight_recorder.json`。S08 P3 只记录轻量运行证据，
不携带 raw/transcript 载荷，不生成臃肿人类文档，只在开发记录中总结必要信息。S08 Review
已完成，确认 S08 P1/P2/P3 满足 stage gate：系统能解释 ChatGPT/Codex/其他 agent 的协作质量
与边界，且没有高负担治理框架。S09 P1 已完成 latent signals，配置为
`机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json`，输出为
`data/derived/behavior_intelligence/latent_signals.json`。S09 P2 已完成
self-iteration suggestions，配置为
`机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json`，输出为
`data/derived/behavior_intelligence/self_iteration_suggestions.json`。S09 P3 已完成 Decision
Debt Ledger，配置为 `机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json`，输出为
`data/derived/behavior_intelligence/decision_debt_ledger.json`。S09 Review 已完成，输出为
`docs/reviews/memory_atlas_v1_2_s09_review.md`，validator 为
`validate:v1.2-s09-review`。S10 P1 已完成首页 arrival briefing，输出为
`docs/reviews/memory_atlas_v1_2_s10_p1_home_arrival_briefing.md`，validator 为
`validate:v1.2-s10-p1`。S10 P2 已完成全局中文，输出为
`docs/reviews/memory_atlas_v1_2_s10_p2_global_chinese_ux.md`，validator 为
`validate:v1.2-s10-p2`。S10 P3 已完成机器字段默认折叠，输出为
`docs/reviews/memory_atlas_v1_2_s10_p3_machine_detail_folding.md`，validator 为
`validate:v1.2-s10-p3`。下一步是 S10 Review。

当前机器产物：

- `数据契约/source_data_model.v1_2_s02_p1.json`
- `数据契约/facet_event_schema.v1_2_s05_p1.json`
- `../data/derived/behavior_intelligence/events.json`
- `../data/derived/behavior_intelligence/clusters.json`
- `../data/derived/behavior_intelligence/low_value_loops.json`
- `../data/derived/behavior_intelligence/opportunities.json`
- `../data/derived/behavior_intelligence/latent_signals.json`
- `../data/derived/behavior_intelligence/self_iteration_suggestions.json`
- `../data/derived/behavior_intelligence/decision_debt_ledger.json`
- `../docs/reviews/memory_atlas_v1_2_s10_p2_global_chinese_ux.md`
- `../人类可读/25_全局中文说明.md`
- `../docs/reviews/memory_atlas_v1_2_s09_review.md`
- `../data/derived/visualization/memory_atlas.json`
- `../data/derived/economic_proxy/personal_economic_proxy.json`
- `../data/derived/economic_proxy/formula_what_if_preview.json`
- `../data/derived/information_roi/information_roi_gate.json`
- `../data/derived/agent_collaboration/agent_collaboration_quality_report.json`
- `../data/derived/agent_collaboration/agent_authorization_boundary_report.json`
- `../data/derived/agent_collaboration/stage_flight_recorder.json`
- `../docs/reviews/memory_atlas_v1_2_s08_review.md`
- `参数与公式/personal_economic_proxy.v1_2_s07_p1.json`
- `参数与公式/information_roi.v1_2_s07_p2.json`
- `参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`
- `可视化配置/visual_roi_gate.v1_2_s07_p2.json`
- `行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json`
- `行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json`
- `行为智能模型/latent_signals.v1_2_s09_p1.json`
- `行为智能模型/self_iteration.v1_2_s09_p2.json`
- `行为智能模型/decision_debt.v1_2_s09_p3.json`
- `证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json`
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
- `scripts/build_memory_atlas_stage_flight.py`
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

下一步是 S09 P1；本目录仍不替代 apps/scripts/tests/config/data/docs/governance。
