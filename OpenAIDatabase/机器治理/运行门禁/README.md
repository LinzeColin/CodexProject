# 运行门禁

用于放置 stage gate、stop condition、rollback、需求冻结和运行前检查。

当前阶段是 S11 Review。任务 ID 为 `MA-V12-S11-REVIEW`，验收 ID 为
`ACC-MA-V12-S11-REVIEW`，validator 为 `validate:v1.2-s11-review`。状态为
`stage_s11_review_passed_pending_s12_no_github_main_upload`。

S11 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s11_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_review.cjs`
- `CHANGELOG.md`
- `功能清单.md`
- `开发记录.md`
- `模型参数文件.md`
- `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
- `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`

S11 Review gate：

- `validate:v1.2-s11-review` 可验证 S11 P1/P2/P3/P4 阶段链。
- P0 图谱集合覆盖 12 张 S11 图谱。
- 每张图都有中文 insight header、human question 和 action value。
- 图谱跟随 `source/time/project/task` 过滤。
- Visual ROI Gate 不通过的候选不进入 P0。
- `python3 scripts/atlasctl.py audit --check visual-roi` 返回 PASS。
- 不执行 proposal apply。
- 不修改 raw。
- 不上传 GitHub main。
- 不进入 S12 implementation。

No GitHub main upload。No remote push。No raw mutation。No proposal apply execution。
下一步是 S12 P1。

历史复验兼容记录：S11 P4 完成时当前阶段是 S11 P4。任务 ID 为 `MA-V12-S11P4`，验收 ID 为
`ACC-MA-V12-S11P4`，validator 为 `validate:v1.2-s11-p4`。状态为
`phase_s11_p4_human_question_map_completed_pending_s11_review`。

S11 P4 产物：

- `docs/reviews/memory_atlas_v1_2_s11_p4_human_question_map.md`
- `人类可读/30_HumanQuestionMap说明.md`
- `机器治理/可视化配置/human_question_map.v1_2_s11_p4.json`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p4.cjs`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

S11 P4 gate：

- `validate:v1.2-s11-p4` 可验证 Human Question Map。
- `human_question_map.v1_2_s11_p4` runtime contract 存在。
- 12 张 P0 图谱均绑定中文 insight header、human question、action value 和 Visual ROI Gate。
- Visual ROI Gate 不通过的候选不进入 P0。
- 图谱跟随 `source/time/project/task` 过滤。
- `python3 scripts/atlasctl.py audit --check visual-roi` 返回 PASS。
- 不执行 proposal apply。
- 不修改 raw。
- 不上传 GitHub main。

No GitHub main upload in this phase。
下一步是 S11 Review。

历史复验兼容记录：S11 P3 完成时当前阶段是 S11 P3。任务 ID 为
`MA-V12-S11P3`，验收 ID 为 `ACC-MA-V12-S11P3`，validator 为
`validate:v1.2-s11-p3`。状态为
`phase_s11_p3_workflow_latent_governance_visuals_completed_pending_s11_p4`。

S11 P3 产物：

- `docs/reviews/memory_atlas_v1_2_s11_p3_workflow_latent_governance_visuals.md`
- `人类可读/29_WorkflowLatentGovernance可视化说明.md`
- `机器治理/可视化配置/workflow_latent_governance_visuals.v1_2_s11_p3.json`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p3.cjs`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

S11 P3 gate：

- `validate:v1.2-s11-p3` 可验证 Workflow/latent/governance visuals。
- `workflow_latent_governance_visuals.v1_2_s11_p3` runtime contract 存在。
- `agent_decision_sankey`、`friction_heatmap`、`latent_radar`、`evidence_timeline` 和 `formula_explorer` 均可见且可交互。
- 每个图都有中文 insight header、human question 和 action value。
- 图谱跟随 `source/time/project/task` 过滤。
- `python3 scripts/atlasctl.py audit --check visual-roi` 返回 PASS。
- 不执行 proposal apply。
- 不修改 raw。
- 不上传 GitHub main。

No GitHub main upload in this phase。
下一步是 S11 P4。

历史复验兼容记录：S11 P2 完成时当前阶段是 S11 P2。任务 ID 为
`MA-V12-S11P2`，验收 ID 为 `ACC-MA-V12-S11P2`，validator 为
`validate:v1.2-s11-p2`。状态为
`phase_s11_p2_economic_like_visuals_completed_pending_s11_p3`。

S11 P2 产物：

- `docs/reviews/memory_atlas_v1_2_s11_p2_economic_like_visuals.md`
- `人类可读/28_EconomicLike经济可视化说明.md`
- `机器治理/可视化配置/economic_like_visuals.v1_2_s11_p2.json`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p2.cjs`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

S11 P2 gate：

- `validate:v1.2-s11-p2` 可验证 Economic-like visuals。
- `economic_like_visuals.v1_2_s11_p2` runtime contract 存在。
- `task_treemap`、`automation_vs_augmentation`、`roi_scatter` 和 `opportunity_radar` 均可见且可交互。
- 每个图都有中文 insight header、human question 和 action value。
- 图谱跟随 `source/time/project/task` 过滤。
- `python3 scripts/atlasctl.py audit --check visual-roi` 返回 PASS。
- 不执行 proposal apply。
- 不修改 raw。
- 不上传 GitHub main。

No GitHub main upload in this phase。
下一步是 S11 P3。

历史复验兼容记录：S11 P1 完成时当前阶段是 S11 P1。任务 ID 为
`MA-V12-S11P1`，验收 ID 为 `ACC-MA-V12-S11P1`，validator 为
`validate:v1.2-s11-p1`。状态为
`phase_s11_p1_clio_like_visuals_completed_pending_s11_p2`。

S11 P1 产物：

- `docs/reviews/memory_atlas_v1_2_s11_p1_clio_like_visuals.md`
- `人类可读/27_ClioLike多维可视化说明.md`
- `机器治理/可视化配置/clio_like_visuals.v1_2_s11_p1.json`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p1.cjs`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

S11 P1 gate：

- `validate:v1.2-s11-p1` 可验证 Clio-like visuals。
- `clio_like_visuals.v1_2_s11_p1` runtime contract 存在。
- `cluster_tree`、`bubble_map` 和 `topic_cluster_explorer` 均可见且可交互。
- 每个图都有中文 insight header、human question 和 action value。
- 图谱跟随 `source/time/project/task` 过滤。
- 下一步是 S11 P2。

历史复验兼容记录：S10 Review 完成时当前阶段是 S10 Review。任务 ID 为
`MA-V12-S10-REVIEW`，验收 ID 为 `ACC-MA-V12-S10-REVIEW`，validator 为
`validate:v1.2-s10-review`，状态为
`stage_s10_review_passed_pending_s11_no_github_main_upload`。

历史复验兼容记录：S10 P3 完成时当前阶段是 S10 P3。任务 ID 为 `MA-V12-S10P3`，验收 ID 为
`ACC-MA-V12-S10P3`，validator 为 `validate:v1.2-s10-p3`。状态为
`phase_s10_p3_machine_detail_folding_completed_pending_s10_review`。

S10 P3 产物：

- `docs/reviews/memory_atlas_v1_2_s10_p3_machine_detail_folding.md`
- `人类可读/26_机器字段高级详情说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p3.cjs`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/i18n/zh-CN.ts`
- `apps/memory-atlas/src/styles.css`
- `scripts/atlasctl.py`

S10 P3 gate：

- `validate:v1.2-s10-p3` 可验证机器字段默认折叠。
- `machine_detail_folding.v1_2_s10_p3` runtime contract 存在。
- 默认首页、搜索、复盘、总结闭环和 Inspector 的机器字段默认折叠。
- 中文“高级详情”入口可访问 schema、query、matched_reason、evidence_refs、proposal_candidate、proposal id 和 Agent 字段。
- `python scripts/atlasctl.py audit --check chinese-ux` 返回 S10 P3 PASS。
- 不执行 proposal apply。
- 不修改 raw。
- S10 Review 下一轮再复审 S10 P1/P2/P3。

No GitHub main upload in this phase。
下一步是 S10 Review。

历史复验兼容记录：S10 P2 完成时当前阶段是 S10 P2，任务 ID 为 `MA-V12-S10P2`，
验收 ID 为 `ACC-MA-V12-S10P2`，validator 为 `validate:v1.2-s10-p2`；
此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

S10 P2 产物：

- `docs/reviews/memory_atlas_v1_2_s10_p2_global_chinese_ux.md`
- `人类可读/25_全局中文说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p2.cjs`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/i18n/zh-CN.ts`
- `scripts/atlasctl.py`

S10 P2 gate：

- `validate:v1.2-s10-p2` 可验证全局中文。
- `global_chinese_ux.v1_2_s10_p2` runtime contract 存在。
- 核心导航、标题、空状态、错误、图表 insight header 默认中文。
- 机器术语保留英文时必须有中文解释。
- `python scripts/atlasctl.py audit --check chinese-ux` 返回 S10 P2 PASS。
- 不执行 proposal apply。
- 不修改 raw。
- S10 P3 下一轮再处理机器字段默认折叠和高级详情入口。

历史复验兼容记录：S10 P1 完成时当前阶段是 S10 P1，任务 ID 为 `MA-V12-S10P1`，
验收 ID 为 `ACC-MA-V12-S10P1`，validator 为 `validate:v1.2-s10-p1`；
此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

S10 P1 产物：

- `docs/reviews/memory_atlas_v1_2_s10_p1_home_arrival_briefing.md`
- `人类可读/24_首页上次来以后发生了什么说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p1.cjs`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/src/i18n/zh-CN.ts`
- `scripts/atlasctl.py`

S10 P1 gate：

- `validate:v1.2-s10-p1` 可验证首页 arrival briefing。
- 首页首屏先回答“上次来以后发生了什么”。
- 展示新增重要资料、增强结论、减弱或过期结论、待授权 proposal、同步失败。
- 每类状态有中文下一步。
- 机器细节默认折叠。
- `python scripts/atlasctl.py audit --check chinese-ux` 返回 PASS。
- 不执行 proposal apply。
- 不修改 raw。
- S10 P2 下一轮再处理全局中文和 Chinese UX linter 增强。

No GitHub main upload in this phase。
下一步是 S10 P2。

历史复验兼容记录：S09 Review 完成时当前阶段是 S09 Review，任务 ID 为
`MA-V12-S09-REVIEW`，验收 ID 为 `ACC-MA-V12-S09-REVIEW`，validator 为
`validate:v1.2-s09-review`；此句只用于保留已完成 stage review 的复验语义，不代表当前阶段。

历史复验兼容记录：S09 P3 完成时当前阶段是 S09 P3，任务 ID 为 `MA-V12-S09P3`，
验收 ID 为 `ACC-MA-V12-S09P3`，validator 为 `validate:v1.2-s09-p3`；
此句只用于保留已完成 phase 的复验语义，不代表当前阶段。

S09 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s09_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_review.cjs`
- `data/derived/behavior_intelligence/latent_signals.json`
- `data/derived/behavior_intelligence/self_iteration_suggestions.json`
- `data/derived/behavior_intelligence/decision_debt_ledger.json`

S09 Review gate：

- `validate:v1.2-s09-review` 可验证 S09 P1/P2/P3 整体复审。
- S09 P3 的持久产物、validator 注册和 `decision-debt-safety` audit 会被 S09 Review 复核。
- `python scripts/atlasctl.py audit --check latent-safety` 返回 PASS。
- `python scripts/atlasctl.py audit --check self-iteration-safety` 返回 PASS。
- `python scripts/atlasctl.py audit --check decision-debt-safety` 返回 PASS。
- latent signals 保留证据、反证、替代解释、Evidence Strength Badge 和 next validation。
- self-iteration suggestions 保留 proposal expiry、action half-life 和 no-apply boundary。
- Decision Debt Ledger 保留最小下一步，不生成压力清单。
- 不执行 proposal apply。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S10 P1。

S09 P3 产物：

- `docs/reviews/memory_atlas_v1_2_s09_p3_decision_debt.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_p3.cjs`
- `scripts/build_memory_atlas_decision_debt.py`
- `scripts/atlasctl.py`
- `机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json`
- `data/derived/behavior_intelligence/decision_debt_ledger.json`
- `人类可读/23_决策债说明.md`

S09 P3 gate：

- `validate:v1.2-s09-p3` 可验证 Decision Debt Ledger。
- `python scripts/atlasctl.py analyze --stage decision-debt --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check decision-debt-safety` 返回 PASS。
- 每条记录有 evidence refs、linked self-iteration suggestions 和最小下一步。
- 每个最小下一步有预期交付件和停止条件。
- 不生成压力清单。
- 不执行 proposal apply。
- 不修改 raw。
- S09 Review 下一轮再处理。

No GitHub main upload in this phase。
下一步是 S09 Review。

S09 P2 产物：

- `docs/reviews/memory_atlas_v1_2_s09_p2_self_iteration.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_p2.cjs`
- `scripts/build_memory_atlas_self_iteration.py`
- `scripts/atlasctl.py`
- `机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json`
- `data/derived/behavior_intelligence/self_iteration_suggestions.json`
- `人类可读/22_自我迭代建议说明.md`

S09 P2 gate：

- `validate:v1.2-s09-p2` 可验证 self-iteration suggestions。
- `python scripts/atlasctl.py analyze --stage self-iteration --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check self-iteration-safety` 返回 PASS。
- 建议覆盖 memory、config、AGENTS、style 和 personalization。
- 每条建议有 action half-life。
- 每个 proposal 有 `expires_at` 和 warn/stale/archive 有效期规则。
- proposal 保持 `pending_human_review`，本 phase 不执行 apply。
- 不修改 raw。
- 不创建 decision debt ledger；S09 P3 再处理。

No GitHub main upload in this phase。
下一步是 S09 P3。

S09 P1 产物：

- `docs/reviews/memory_atlas_v1_2_s09_p1_latent_signals.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_p1.cjs`
- `scripts/build_memory_atlas_latent_signals.py`
- `scripts/atlasctl.py`
- `机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json`
- `data/derived/behavior_intelligence/latent_signals.json`
- `人类可读/21_潜性信号说明.md`

S09 P1 gate：

- `validate:v1.2-s09-p1` 可验证 latent signals。
- `python scripts/atlasctl.py analyze --stage latent --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check latent-safety` 返回 PASS。
- 每条 latent signal 有 claim、supporting evidence、contradicting evidence、alternative explanation、confidence、Evidence Strength Badge 和 next validation。
- 不输出心理诊断或人格标签。
- 不创建 self-iteration suggestions；S09 P2 再处理。
- 不创建 decision debt ledger；S09 P3 再处理。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S09 P2。

S08 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s08_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_review.cjs`
- `data/derived/agent_collaboration/agent_collaboration_quality_report.json`
- `data/derived/agent_collaboration/agent_authorization_boundary_report.json`
- `data/derived/agent_collaboration/stage_flight_recorder.json`

S08 Review gate：

- `validate:v1.2-s08-review` 可验证 S08 P1/P2/P3 整体复审。
- `validate:v1.2-s08-p3` 在 clean tree 可通过。
- `python scripts/atlasctl.py audit --check agent-collaboration` 返回 PASS。
- `python scripts/atlasctl.py audit --check agent-authorization` 返回 PASS。
- `python scripts/atlasctl.py audit --check stage-flight` 返回 PASS。
- Codex/Agent 协作质量覆盖 planning、execution、review、rework、scope clarity、testability 和 rollbackability。
- 授权边界保留 raw no-apply 和 `approved_by_human` 门禁。
- stage flight recorder 保持 10 个轻量字段和 3 条 phase records。
- 不创建多 agent 系统。
- 不创建复杂 Delegation Contract UI。
- 不执行 proposal apply。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S09 P1。

S08 P3 产物：

- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p3.cjs`
- `scripts/build_memory_atlas_stage_flight.py`
- `scripts/atlasctl.py`
- `机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json`
- `data/derived/agent_collaboration/stage_flight_recorder.json`

S08 P3 gate：

- `validate:v1.2-s08-p3` 可验证 lightweight stage flight recorder。
- `python scripts/atlasctl.py analyze --stage stage-flight --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check stage-flight` 返回 PASS。
- stage flight recorder 只包含 10 个轻量字段。
- phase records 覆盖 S08 P1、S08 P2、S08 P3。
- 不携带 raw 或 transcript payload。
- 不生成臃肿人类文档。
- 只在开发记录中总结必要信息。
- 不创建复杂 Delegation Contract UI。
- 不创建多 agent 系统。
- 不修改 raw。

No GitHub main upload in this phase。
S08 P3 的下一历史 gate 是 S08 Review，当前已完成。

S08 P2 产物：

- `docs/reviews/memory_atlas_v1_2_s08_p2_authorization_boundary.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p2.cjs`
- `scripts/build_memory_atlas_agent_authorization.py`
- `scripts/atlasctl.py`
- `机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json`
- `data/derived/agent_collaboration/agent_authorization_boundary_report.json`
- `人类可读/20_Agent授权边界说明.md`

S08 P2 gate：

- `validate:v1.2-s08-p2` 可验证 Agent 授权边界。
- `python scripts/atlasctl.py analyze --stage agent-authorization --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check agent-authorization` 返回 PASS。
- `agent-authorization` 输出包含 4 个机器输出检查。
- raw 不可修改，raw 永远不能作为 apply target。
- proposal 必须有人类授权并进入 `approved_by_human` 后才能 apply。
- 当前 phase 不执行 proposal apply；apply 自动化留给 S13。
- 不创建复杂 Delegation Contract UI。
- 不创建多 agent 系统。
- 不生成 stage flight recorder；运行证据留给 S08 P3。
- 不修改 raw。

No GitHub main upload in this phase。
S08 P2 的下一历史 gate 是 S08 P3，当前已完成。

S08 P1 产物：

- `docs/reviews/memory_atlas_v1_2_s08_p1_agent_collaboration.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p1.cjs`
- `scripts/build_memory_atlas_agent_collaboration.py`
- `scripts/atlasctl.py`
- `机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json`
- `data/derived/agent_collaboration/agent_collaboration_quality_report.json`
- `人类可读/19_Agent协作质量指标说明.md`

S08 P1 gate：

- `validate:v1.2-s08-p1` 可验证 Codex/Agent 协作质量指标。
- `python scripts/atlasctl.py analyze --stage agent-collaboration --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check agent-collaboration` 返回 PASS。
- `agent-collaboration` 输出覆盖 planning clarity、execution clarity、review burden、
  rework count、scope clarity、testability 和 rollbackability。
- 每个指标有公式来源、中文解释和 evidence refs。
- source summary 支持 `chatgpt`、`codex` 和 `other_agent` 通用字段。
- 人类摘要回答人负责什么、Agent 负责什么、返工来自哪里、哪些任务适合继续交给
  Codex/agent、哪些必须人工判断。
- 不创建复杂 Delegation Contract UI。
- 不创建多 agent 系统。
- 不定义授权 apply 边界；授权边界留给 S08 P2。
- 不生成 stage flight recorder；运行证据留给 S08 P3。
- 不修改 raw。

No GitHub main upload in this phase。
S08 P1 的下一历史 gate 是 S08 P2，当前已完成。

S07 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s07_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_review.cjs`
- `scripts/atlasctl.py`
- `data/derived/economic_proxy/personal_economic_proxy.json`
- `data/derived/information_roi/information_roi_gate.json`
- `data/derived/economic_proxy/formula_what_if_preview.json`
- `机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`
- `机器治理/参数与公式/information_roi.v1_2_s07_p2.json`
- `机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`

S07 Review gate：

- `validate:v1.2-s07-review` 可验证 S07 P1/P2/P3 链路。
- `validate:v1.2-s07-p3` 在 clean tree 可通过。
- Personal Economic Proxy 可生成。
- 每个分数有中文解释、公式来源和参数引用。
- Information ROI 覆盖 insight、card、chart。
- Visual ROI Gate 保证没有决策价值的图表不进 P0。
- Formula What-if 可查看或配置，且 `proposal_required_before_apply=true`。
- 外部经济数据库只保留 v2 占位，不深做。
- 不声称精确收入预测，不提供财务建议。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S08 P1。

S07 P3 产物：

- `docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs`
- `scripts/build_memory_atlas_formula_what_if.py`
- `scripts/atlasctl.py`
- `机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`
- `data/derived/economic_proxy/formula_what_if_preview.json`
- `人类可读/18_FormulaWhatIf配置预览说明.md`

S07 P3 gate：

- `validate:v1.2-s07-p3` 可验证 Formula What-if 配置预览。
- `python scripts/atlasctl.py analyze --stage formula-what-if --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check formula-what-if` 返回 PASS。
- 输出包含 `scenarios`、`adjustable_weights`、`parameter_change_proposal`、公式来源和参数引用。
- `proposal_required_before_apply=true`。
- `active_config_write=false`。
- 不接入外部经济数据库。
- 不是精确收入预测，不是财务建议。
- 不实现运行时 UI。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 Review。

S07 P2 产物：

- `docs/reviews/memory_atlas_v1_2_s07_p2_information_roi.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p2.cjs`
- `scripts/build_memory_atlas_information_roi.py`
- `scripts/atlasctl.py`
- `机器治理/参数与公式/information_roi.v1_2_s07_p2.json`
- `机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`
- `data/derived/information_roi/information_roi_gate.json`
- `人类可读/17_InformationROI与VisualROIGate说明.md`

S07 P2 gate：

- `validate:v1.2-s07-p2` 可验证 Information ROI 与 Visual ROI Gate。
- `python scripts/atlasctl.py analyze --stage information-roi --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check visual-roi` 返回 PASS。
- 每个 ROI item 有公式来源、参数引用和证据引用。
- P0 visual 必须有 human question、action 和 gate pass。
- 没有决策价值的图表不进 P0。
- 不接入外部经济数据库。
- 不是精确收入预测，不是财务建议。
- 不实现 S07 P3 what-if UI。
- 不修改运行时 UI。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 P3。

S07 P1 产物：

- `docs/reviews/memory_atlas_v1_2_s07_p1_economic_proxy.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p1.cjs`
- `scripts/build_memory_atlas_economic_proxy.py`
- `scripts/atlasctl.py`
- `机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`
- `data/derived/economic_proxy/personal_economic_proxy.json`
- `人类可读/16_PersonalEconomicProxy公式说明.md`

S07 P1 gate：

- `validate:v1.2-s07-p1` 可验证 Personal Economic Proxy。
- `python scripts/atlasctl.py analyze --stage economic-proxy --dry-run` 返回 no-write payload。
- `python scripts/atlasctl.py audit --check formulas` 返回 PASS。
- 每个 score card 有中文解释、公式来源、参数引用和证据引用。
- 不接入外部经济数据库；外部经济数据库只作为 v2 interface 预留。
- 不是精确收入预测，不是财务建议。
- 不实现 S07 P2 information ROI gate。
- 不实现 S07 P3 what-if UI。
- 不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 P2。

S06 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s06_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_review.cjs`
- `scripts/build_memory_atlas_data.py`
- `data/derived/visualization/memory_atlas.json`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/types.ts`
- `apps/memory-atlas/src/styles.css`
- `scripts/build_memory_atlas_opportunities.py`
- `scripts/atlasctl.py`
- `data/derived/behavior_intelligence/clusters.json`
- `data/derived/behavior_intelligence/low_value_loops.json`
- `data/derived/behavior_intelligence/opportunities.json`

S06 Review gate：

- `validate:v1.2-s06-review` 可验证 S06 P1/P2/P3 输出和显示接入。
- `data/derived/visualization/memory_atlas.json` 包含 `behavior_intelligence`。
- Memory Atlas 首页通过 `data-s06-review-display` 显示主题簇、低价值循环和机会线索。
- 输出包含 160 个 clusters、23 个低价值循环和 12 条候选机会。
- `python scripts/atlasctl.py audit --check insight-evidence` 返回 PASS 且 `bad_items` 为空。
- 不接外部经济数据库，不做心理诊断，不生成无穷压力清单，不修改 raw。

No GitHub main upload in this phase。
下一步是 S07 P1。

前置 S01 Review 已通过：`MA-V12-S01-REVIEW` / `ACC-MA-V12-S01-REVIEW` /
`validate:v1.2-s01-review`。

前置 S02 P1 已通过：`MA-V12-S02P1` / `ACC-MA-V12-S02P1` /
`validate:v1.2-s02-p1`。

前置 S02 P2 已通过：`MA-V12-S02P2` / `ACC-MA-V12-S02P2` /
`validate:v1.2-s02-p2`。

S02 P3 产物：

- `机器治理/同步与备份/sync_source_registry.json`
- `docs/reviews/memory_atlas_v1_2_s02_p2_source_registry.md`
- `人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`
- `docs/reviews/memory_atlas_v1_2_s02_p3_human_sync_explanation.md`

前置 S02 P3 已通过：`MA-V12-S02P3` / `ACC-MA-V12-S02P3` /
`validate:v1.2-s02-p3`。

前置 S02 Review 已通过：`MA-V12-S02-REVIEW` / `ACC-MA-V12-S02-REVIEW` /
`validate:v1.2-s02-review`。

S02 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s02_review.md`

source registry 必须包含：

- `chatgpt`：ChatGPT browser connector 与 official export fallback。
- `codex`：Codex local sync。
- `future_agent_template`：后续 other_agent 的 future_agent_adapter。
- 每个 source 的 `public_backup_mode`。
- 每个 source 的 transcript/credential boundary。

`v1.2需求冻结清单.json` 继续固定：

- 四线范围和 14 Stage 执行规则。
- 用户授权后的 raw/transcript 明文公开 GitHub 边界。
- raw 只读、只追加、不覆盖、不增删改。
- 凭证排除边界。
- 后续其他 agent 的 source registry 扩展规则。

S03 P1 产物：

- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md`

S03 P1 gate：

- public raw path 已定义。
- manifest/hash 文件合同已定义。
- append-only 规则已定义。
- hash drift fail 规则已定义。

No GitHub main upload in this phase。
不实现 connector，不导入真实 transcript，不生成 S03 P3 manifest ledger。

前置 S03 P1 已通过：`MA-V12-S03P1` / `ACC-MA-V12-S03P1` /
`validate:v1.2-s03-p1`。

S03 P2 产物：

- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`
- `人类可读/07_凭证排除说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md`

S03 P2 gate：

- credential is not memory。
- `credentials_not_transcript` 已接入同步与审计。
- 普通 transcript 不被凭证门禁拦截。
- 凭证 pattern 导致 gate fail。

前置 S03 P2 已通过：`MA-V12-S03P2` / `ACC-MA-V12-S03P2` /
`validate:v1.2-s03-p2`。

S03 P3 产物：

- `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- `scripts/raw_archive_manifest.py`
- `机器治理/证据与日志/raw_archive_manifests/raw_manifest.s03_p3_baseline.jsonl`
- `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- `人类可读/08_Raw机器账本说明.md`
- `docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md`

S03 P3 gate：

- raw manifest/hash 可生成。
- manifest row 可映射 source/file/hash/imported_at。
- 修改已有 raw 文件导致 validation fail。
- 删除已登记 manifest entry 导致 validation fail。
- raw manifest 是机器文件，不是人类主要页面。

No GitHub main upload in this phase。
前置 S03 P3 已通过：`MA-V12-S03P3` / `ACC-MA-V12-S03P3` /
`validate:v1.2-s03-p3`。

S03 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s03_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs`

S03 Review gate：

- raw 可公开备份。
- append-only 和 hash drift/deleted manifest entry fail 均可验证。
- credential exclusion 可验证，credential pattern 会失败。
- raw manifest/hash 可生成并映射 source/file/hash/imported_at。
- human files 不被 raw manifest 明细污染。

No GitHub main upload in this review。
前置 S03 Review 已通过：`MA-V12-S03-REVIEW` / `ACC-MA-V12-S03-REVIEW` /
`validate:v1.2-s03-review`。

S04 P1 产物：

- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `scripts/sync_chatgpt_memory_data.py`
- `scripts/atlasctl.py`
- `人类可读/09_ChatGPT只读同步与官方导出Fallback.md`
- `docs/reviews/memory_atlas_v1_2_s04_p1_chatgpt_sync.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs`

S04 P1 gate：

- ChatGPT browser connector 边界为只读。
- 密码/验证码立即停止。
- 不发送消息、不删除、不归档、不重命名会话。
- official export ZIP/conversations.json fallback 可用。
- dry-run 不写文件。
- credential pattern 先失败，不进入 public raw。

No GitHub main upload in this phase。
下一步是 S04 P2；本 phase 不实现 Codex local sync、后续 agent adapter 或 GitHub backup apply。

当前阶段是 S04 P2。任务 ID 为 `MA-V12-S04P2`，验收 ID 为
`ACC-MA-V12-S04P2`，validator 为 `validate:v1.2-s04-p2`。

S04 P2 产物：

- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `scripts/sync_codex_memory_data.py`
- `scripts/sync_future_agent_data.py`
- `scripts/atlasctl.py`
- `人类可读/10_Codex与FutureAgent同步.md`
- `docs/reviews/memory_atlas_v1_2_s04_p2_codex_agent_sync.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p2.cjs`

S04 P2 gate：

- `python scripts/atlasctl.py sync --source codex --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py sync --source future-agent --dry-run` 可运行且不写文件。
- Codex local sync 输出 raw + derived + run log 合同。
- future-agent minimal adapter 输出 raw + derived + run log 合同。
- future-agent apply 缺少输入时不能生成伪数据。

No GitHub main upload in this phase。
下一步是 S04 P3；本 phase 不实现 GitHub backup dry-run/apply。

前置 S04 P3 已通过：`MA-V12-S04P3` / `ACC-MA-V12-S04P3` /
`validate:v1.2-s04-p3`。

S04 P3 产物：

- `机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json`
- `scripts/github_backup.py`
- `scripts/atlasctl.py`
- `人类可读/11_GitHub备份DryRun与Apply.md`
- `docs/reviews/memory_atlas_v1_2_s04_p3_github_backup.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p3.cjs`

S04 P3 gate：

- `python scripts/atlasctl.py push --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py push --apply` 只做本地 git add/commit。
- backup scope 覆盖 `data/public_raw`、`data/derived`、`data/run_logs`、
  `docs/reviews` 和 `reports`。
- 失败时输出中文原因和 fallback 建议。
- 不执行远端 push，不上传 GitHub main，不重装 app。

S04 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s04_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_review.cjs`

S04 Review gate：

- S04 P1、S04 P2、S04 P3 validator 链路在 clean tree 可复跑。
- `python scripts/atlasctl.py sync --source chatgpt --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py sync --source codex --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py sync --source future-agent --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py build-atlas --dry-run` 可运行且不写文件。
- `python scripts/atlasctl.py push --dry-run` 可运行且不远端 push。
- S04 整体复审已通过。

No GitHub main upload in this review。
No remote push in this review。
前置 S04 Review 已通过：`MA-V12-S04-REVIEW` / `ACC-MA-V12-S04-REVIEW` /
`validate:v1.2-s04-review`。

S05 P1 产物：

- `机器治理/数据契约/facet_event_schema.v1_2_s05_p1.json`
- `人类可读/12_Facet字段与事件语义说明.md`
- `docs/reviews/memory_atlas_v1_2_s05_p1_facet_schema.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p1.cjs`

S05 P1 gate：

- facet schema 定义 `source`、`topic`、`intent`、`task_type`、`project`、
  `output_type`、`language`、`tool`、`turn_count`、`friction`、`value_signal`
  和 `future_agent_source`。
- 字段名必须是英文。
- 人类文件必须用中文解释字段含义。
- schema 覆盖 ChatGPT、Codex 和 future agent。
- 不实现 extractor，不生成 fake events，不修改 raw，不把机器字段堆到首屏。

No GitHub main upload in this phase。
No remote push in this phase。
前置 S05 P1 已通过：`MA-V12-S05P1` / `ACC-MA-V12-S05P1` /
`validate:v1.2-s05-p1`。

S05 P2 产物：

- `scripts/extract_memory_atlas_facets.py`
- `scripts/atlasctl.py analyze --stage facets`
- `data/derived/behavior_intelligence/events.json`
- `docs/reviews/memory_atlas_v1_2_s05_p2_facet_extractor.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p2.cjs`

S05 P2 gate：

- extractor 可从 ChatGPT、Codex 和 future_agent/other_agent 的 raw 或 derived 输入抽取
  canonical events。
- 缺失字段必须 fallback，不得抛出无意义异常。
- 缺失来源必须写 source_status missing_reason，不得生成 fake events。
- 每条 event 必须包含 `raw_ref`、`manifest_ref`、`derived_ref` 或
  `evidence_missing_reason`。
- 不修改 raw，不上传 GitHub main，不远端 push，不改变首屏 UI。

No GitHub main upload in this phase。
No remote push in this phase。
No raw mutation in this phase。

S05 P3 产物：

- `scripts/extract_memory_atlas_facets.py`
- `scripts/atlasctl.py analyze --stage facets`
- `data/derived/behavior_intelligence/events.json`
- `docs/reviews/memory_atlas_v1_2_s05_p3_evidence_refs.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs`

S05 P3 gate：

- 每条 event 必须包含 `source_id` 和轻量 `evidence_refs`。
- `evidence_refs` 必须指向 `raw_ref`、`manifest_ref`、`derived_ref` 或
  `evidence_missing_reason`。
- 不实现 Raw-to-Insight Replay UI。
- 不生成 fake events，不修改 raw，不上传 GitHub main，不远端 push。

No GitHub main upload in this phase。
No remote push in this phase。
No raw mutation in this phase。

S05 Review 产物：

- `docs/reviews/memory_atlas_v1_2_s05_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs`

S05 Review gate：

- S05 P1、S05 P2、S05 P3 validator 链路在 clean tree 可复跑。
- canonical event 可覆盖 ChatGPT/Codex/future agent。
- 每条 event 有 evidence ref 或缺失原因。
- 人类文件能解释 facet 含义。
- 不输出纯机器字段给首屏。
- 行为事件与 facets 可被后续 cluster、ROI、latent、visualization 复用。
- 不生成 fake events，不修改 raw，不上传 GitHub main，不远端 push。

No GitHub main upload in this review。
No remote push in this review。
No raw mutation in this review。
下一步是 S06 P1。

S06 P1 产物：

- `scripts/build_memory_atlas_clusters.py`
- `scripts/atlasctl.py analyze --stage clusters`
- `scripts/atlasctl.py audit --check insight-evidence`
- `data/derived/behavior_intelligence/clusters.json`
- `人类可读/13_行为簇与层级簇说明.md`
- `docs/reviews/memory_atlas_v1_2_s06_p1_cluster_builder.md`

S06 P1 gate：

- 生成主题簇和层级簇。
- 支持 `source/time/project/task/language` 过滤合同。
- 每个 cluster 有中文摘要和 `evidence_refs`。
- 不识别低价值循环，不生成机会卡片，不修改 raw。

下一步是 S06 P2。
