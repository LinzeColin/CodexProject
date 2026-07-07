# Memory Atlas v1.1.7 Stage 7 Phase 7.2 Review Summary Iteration Runtime Acceptance

- task_id: `MA-V117-S7P02`
- acceptance_id: `ACC-MA-V117-S7P02`
- status: `phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review`
- runtime_version: `review_summary_iteration_runtime.v1_1_7_stage7_phase2`
- review_schema_version: `memory_atlas_review_summary.v1_1_7_stage7_phase2`
- validator: `validate:v1.1.7-stage7-phase2`
- browser_validator: `validate:review-summary-iteration-browser`

## Required runtime

The production `summary` view must expose a versioned Review / Summary / Iteration runtime root and a safe debug signal. It must render:

- `review_period_selector`
- `theme_change_panel`
- `opportunity_panel`
- `low_value_loop_panel`
- `decision_change_panel`
- `next_action_panel`
- `proposal_decision_panel`
- `iteration_backlog`

The runtime must answer:

1. 本期主导主题是什么
2. 哪些主题增强
3. 哪些主题衰退
4. 哪些新机会出现
5. 哪些低价值循环出现
6. 哪些决策变化
7. 下一步动作是什么
8. 是否需要生成 proposal

## Required schema

The visible output must include `review_id`, `review_schema_version`, `time_window`, `source_scope`, `dominant_topics`, `strengthening_topics`, `declining_topics`, `new_opportunities`, `low_value_loops`, `decision_changes`, `next_actions`, `proposal_candidate`, `evidence_refs`, `confidence` and `iteration_backlog`.

## Required checks

- `validate:v1.1.7-stage7-phase2` must pass for static contract, records, branch and no-upload checks.
- `validate:review-summary-iteration-browser` must pass on a local browser session with screenshot evidence.
- Debug signal must report `directActiveMemoryWriteback=false` and `rawPrivateDataIncluded=false`.

## Boundaries

- No Stage 8 summary closure.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No GitHub main upload before the whole Stage 0-10 project is complete.
