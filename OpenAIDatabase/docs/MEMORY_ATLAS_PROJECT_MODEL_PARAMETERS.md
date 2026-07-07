## 102. Memory Atlas v1.1.7 Stage 10 Phase 10.1 Final Hardening Upload Readiness

状态：`phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review`。

验收 ID：`ACC-MA-V117-S10P01`。

合同 ID：`memory_atlas_v1_1_7_final_hardening_upload_readiness_contract`。

模型参数：

- `validate:v1.1.7-stage10-phase1` 是本 phase 必跑 validator。
- Product contract 固定为 `docs/product/memory_atlas_v1_1_7_final_hardening_upload_readiness_contract.md`。
- Acceptance 固定为 `docs/acceptance/memory_atlas_v1_1_7_stage10_phase1_final_hardening_upload_readiness_acceptance.md`。
- Stage 10 Phase 10.1 覆盖 `performance_safety_accessibility_matrix`、`release_rollback_matrix`、`final_validation_matrix`、`github_main_upload_matrix`、`governance_sync_matrix` 和 `new_machine_recovery_matrix`。
- Performance target 固定为 desktop target 45-60 FPS 和 reduced-motion fallback 后续证明。
- Stage 9 review must be complete。
- Stage 10 Phase 10.1 完成后 pending Stage 10 review。
- No intermediate GitHub upload。
- No GitHub main upload in this phase。

参数记录：

- `PARAM-MA-V117-S10P01-001 stage10_phase1_contract_id = memory_atlas_v1_1_7_final_hardening_upload_readiness_contract`
- `PARAM-MA-V117-S10P01-002 stage10_phase1_status = phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review`
- `PARAM-MA-V117-S10P01-003 stage10_phase1_required_validator = validate:v1.1.7-stage10-phase1`
- `PARAM-MA-V117-S10P01-004 stage10_phase1_hardening_matrices = performance_safety_accessibility_matrix;release_rollback_matrix;final_validation_matrix;github_main_upload_matrix;governance_sync_matrix;new_machine_recovery_matrix`
- `PARAM-MA-V117-S10P01-005 stage10_phase1_performance_target = desktop target 45-60 FPS;reduced-motion fallback`
- `PARAM-MA-V117-S10P01-006 stage10_phase1_entry_condition = Stage 9 review must be complete`
- `PARAM-MA-V117-S10P01-007 stage10_phase1_next_gate = pending Stage 10 review`
- `PARAM-MA-V117-S10P01-008 upload_boundary = No intermediate GitHub upload;No GitHub main upload in this phase`

验收信号：

- `validate:v1.1.7-stage10-phase1` checks Stage 9 continuity, contracts, records, changed_scope, runtime_boundary, canonical local branch and no remote development branch.

Machine-readable boundary summary: Stage 10 Phase 10.1; MA-V117-S10P01; ACC-MA-V117-S10P01; phase_10_1_final_hardening_upload_readiness_contract_created_pending_stage10_review; memory_atlas_v1_1_7_final_hardening_upload_readiness_contract; validate:v1.1.7-stage10-phase1; performance_safety_accessibility_matrix; release_rollback_matrix; final_validation_matrix; github_main_upload_matrix; governance_sync_matrix; new_machine_recovery_matrix; desktop target 45-60 FPS; reduced-motion fallback; Stage 9 review must be complete; pending Stage 10 review; No intermediate GitHub upload; No GitHub main upload in this phase; No raw/private read; No direct active-memory writeback; No proposal queue write; No agent apply.

## 101. Memory Atlas v1.1.7 Stage 9 Review

状态：`stage_9_review_passed_pending_stage10_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S9-REVIEW`。

模型参数：

- `validate:v1.1.7-stage9` 是本 review 必跑 validator。
- Review artifact 固定为 `docs/reviews/memory_atlas_v1_1_7_stage9_review.md`。
- Stage 9 覆盖 Phase 9.1 Cross-board shared state、synchronized filters 和 Inspector explanation layer。
- Runtime version 固定为 `cross_board_shared_state.v1_1_7_stage9_phase1`。
- Inspector layer version 固定为 `inspector_explanation_layer.v1_1_7_stage9_phase1`。
- 同步输出固定为 `shared_state_filters`、`synchronized_filters` 和 `inspector_explanation_layer`。
- Stage 9 review 通过后 pending Stage 10。
- No Stage 10 work。
- No GitHub main upload before whole Stage 0-10 completion。

参数记录：

- `PARAM-MA-V117-S9-REVIEW-001 stage9_review_status = stage_9_review_passed_pending_stage10_no_github_main_upload`
- `PARAM-MA-V117-S9-REVIEW-002 stage9_review_required_validator = validate:v1.1.7-stage9`
- `PARAM-MA-V117-S9-REVIEW-003 stage9_review_artifact = docs/reviews/memory_atlas_v1_1_7_stage9_review.md`
- `PARAM-MA-V117-S9-REVIEW-004 stage9_review_phase_coverage = Phase 9.1;Cross-board shared state;synchronized filters;Inspector explanation layer`
- `PARAM-MA-V117-S9-REVIEW-005 stage9_review_runtime_versions = cross_board_shared_state.v1_1_7_stage9_phase1;inspector_explanation_layer.v1_1_7_stage9_phase1`
- `PARAM-MA-V117-S9-REVIEW-006 stage9_review_next_gate = pending Stage 10`
- `PARAM-MA-V117-S9-REVIEW-007 upload_boundary = No GitHub main upload before whole Stage 0-10 completion`

验收信号：

- `validate:v1.1.7-stage9` checks Phase 9.1, records, canonical local branch and no-upload boundary.

Machine-readable boundary summary: Stage 9 Review; MA-V117-S9-REVIEW; ACC-MA-V117-S9-REVIEW; stage_9_review_passed_pending_stage10_no_github_main_upload; validate:v1.1.7-stage9; Phase 9.1; Cross-board shared state; synchronized filters; Inspector explanation layer; cross_board_shared_state.v1_1_7_stage9_phase1; inspector_explanation_layer.v1_1_7_stage9_phase1; shared_state_filters; synchronized_filters; inspector_explanation_layer; pending Stage 10; No Stage 10 work; No GitHub main upload; No raw/private read; No direct active-memory writeback; No proposal queue write; No agent apply.

## 100. Memory Atlas v1.1.7 Stage 9 Phase 9.1 Cross-board Shared State

状态：`phase_9_1_cross_board_shared_state_completed_pending_stage9_review`。

验收 ID：`ACC-MA-V117-S9P01`。

模型参数：

- Runtime version 固定为 `cross_board_shared_state.v1_1_7_stage9_phase1`。
- Inspector layer version 固定为 `inspector_explanation_layer.v1_1_7_stage9_phase1`。
- `validate:v1.1.7-stage9-phase1` 是本 phase 必跑 validator。
- `validate:cross-board-shared-state-browser` 是本 phase 浏览器 validator。
- Cross-board shared state 必须覆盖 home、galaxy、notion、roi、obsidian、timeline、contribution、wordcloud、search、summary。
- synchronized filters 必须包含 `shared_state_filters`、`synchronized_filters` 和 `inspector_explanation_layer`。
- No Stage 9 review。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage9_phase1.cjs`
- `apps/memory-atlas/scripts/validate_cross_board_shared_state_browser.cjs`

参数记录：

- `PARAM-MA-V117-S9P01-001 stage9_phase1_status = phase_9_1_cross_board_shared_state_completed_pending_stage9_review`
- `PARAM-MA-V117-S9P01-002 stage9_phase1_required_validator = validate:v1.1.7-stage9-phase1`
- `PARAM-MA-V117-S9P01-003 stage9_phase1_browser_validator = validate:cross-board-shared-state-browser`
- `PARAM-MA-V117-S9P01-004 shared_state_runtime_version = cross_board_shared_state.v1_1_7_stage9_phase1`
- `PARAM-MA-V117-S9P01-005 inspector_layer_version = inspector_explanation_layer.v1_1_7_stage9_phase1`
- `PARAM-MA-V117-S9P01-006 synchronized_outputs = shared_state_filters;synchronized_filters;inspector_explanation_layer`
- `PARAM-MA-V117-S9P01-007 boundary = No Stage 9 review;No Stage 10;No GitHub main upload;No raw/private read;No direct active-memory writeback;No proposal queue write`

验收信号：

- `window.__memoryAtlasStage9Phase1` reports runtime version, Inspector layer version, surfaces, shared_state_filters, synchronized_filters, focus, revision, Inspector explanation coverage and safety flags.
- Browser screenshot validates the production runtime after synchronized filter board switching.

Machine-readable boundary summary: Phase 9.1; Cross-board shared state; MA-V117-S9P01; ACC-MA-V117-S9P01; phase_9_1_cross_board_shared_state_completed_pending_stage9_review; validate:v1.1.7-stage9-phase1; validate:cross-board-shared-state-browser; cross_board_shared_state.v1_1_7_stage9_phase1; inspector_explanation_layer.v1_1_7_stage9_phase1; shared_state_filters; synchronized_filters; inspector_explanation_layer; Inspector explanation layer; No Stage 9 review; No Stage 10; No GitHub main upload; No raw/private read; No direct active-memory writeback; No proposal queue write; No agent apply.

## 99. Memory Atlas v1.1.7 Stage 8 Review

状态：`stage_8_review_passed_pending_stage9_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S8-REVIEW`。

模型参数：

- `validate:v1.1.7-stage8` 是本 review 必跑 validator。
- Review artifact 固定为 `docs/reviews/memory_atlas_v1_1_7_stage8_review.md`。
- Stage 8 覆盖 Phase 8.1 Summary and iteration closure。
- Stage 8 review 通过后 pending Stage 9。
- No GitHub main upload before whole Stage 0-10 completion。

参数记录：

- `PARAM-MA-V117-S8-REVIEW-001 stage8_review_status = stage_8_review_passed_pending_stage9_no_github_main_upload`
- `PARAM-MA-V117-S8-REVIEW-002 stage8_review_required_validator = validate:v1.1.7-stage8`
- `PARAM-MA-V117-S8-REVIEW-003 stage8_review_artifact = docs/reviews/memory_atlas_v1_1_7_stage8_review.md`
- `PARAM-MA-V117-S8-REVIEW-004 stage8_review_phase_coverage = Phase 8.1;Summary and iteration closure`
- `PARAM-MA-V117-S8-REVIEW-005 stage8_review_next_gate = pending Stage 9`
- `PARAM-MA-V117-S8-REVIEW-006 upload_boundary = No GitHub main upload before whole Stage 0-10 completion`

验收信号：

- `validate:v1.1.7-stage8` checks Phase 8.1, records, canonical remote, local branch and no-upload boundary.

Machine-readable boundary summary: Stage 8 Review; MA-V117-S8-REVIEW; ACC-MA-V117-S8-REVIEW; stage_8_review_passed_pending_stage9_no_github_main_upload; validate:v1.1.7-stage8; Phase 8.1; Summary and iteration closure; pending Stage 9; No Stage 9 work; No GitHub main upload; No raw/private read; No direct active-memory writeback; No proposal queue write; No agent apply.

## 98. Memory Atlas v1.1.7 Stage 8 Phase 8.1 Summary Iteration Closure

状态：`phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review`。

验收 ID：`ACC-MA-V117-S8P01`。

模型参数：

- Runtime version 固定为 `summary_iteration_closure_runtime.v1_1_7_stage8_phase1`。
- Closure schema version 固定为 `memory_atlas_summary_closure.v1_1_7_stage8_phase1`。
- Source review schema version 固定为 `memory_atlas_review_summary.v1_1_7_stage7_phase2`。
- `validate:v1.1.7-stage8-phase1` 是本 phase 必跑 validator。
- `validate:summary-iteration-closure-browser` 是本 phase 浏览器 validator。
- Summary and iteration closure 输出必须显示 `change_comparison`、`stale_conflict_signals` 和 `proposal_candidates`。
- Runtime 必须显示 conflict check、human/agent apply gate、rollback hint 和 proposal-only safety。
- No Stage 8 review。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage8_phase1.cjs`
- `apps/memory-atlas/scripts/validate_summary_iteration_closure_browser.cjs`

参数记录：

- `PARAM-MA-V117-S8P01-001 stage8_phase1_status = phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review`
- `PARAM-MA-V117-S8P01-002 stage8_phase1_required_validator = validate:v1.1.7-stage8-phase1`
- `PARAM-MA-V117-S8P01-003 stage8_phase1_browser_validator = validate:summary-iteration-closure-browser`
- `PARAM-MA-V117-S8P01-004 summary_iteration_closure_runtime_version = summary_iteration_closure_runtime.v1_1_7_stage8_phase1`
- `PARAM-MA-V117-S8P01-005 summary_iteration_closure_schema_version = memory_atlas_summary_closure.v1_1_7_stage8_phase1`
- `PARAM-MA-V117-S8P01-006 output_fields = change_comparison;stale_conflict_signals;proposal_candidates`
- `PARAM-MA-V117-S8P01-007 boundary = No Stage 8 review;No GitHub main upload;No raw/private read;No direct active-memory writeback;No proposal queue write`

验收信号：

- `window.__memoryAtlasStage8Phase1` reports runtime version, closure schema version, source review schema version, panel ids, closure counts and safety flags.
- Browser screenshot validates the production `summary` view.

Machine-readable boundary summary: Phase 8.1; Summary and iteration closure; MA-V117-S8P01; ACC-MA-V117-S8P01; phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review; validate:v1.1.7-stage8-phase1; validate:summary-iteration-closure-browser; summary_iteration_closure_runtime.v1_1_7_stage8_phase1; memory_atlas_summary_closure.v1_1_7_stage8_phase1; change_comparison; stale_conflict_signals; proposal_candidates; No Stage 8 review; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply.

## 97. Memory Atlas v1.1.7 Stage 7 Review

状态：`stage_7_review_passed_pending_stage8_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S7-REVIEW`。

模型参数：

- `validate:v1.1.7-stage7` 是本 review 必跑 validator。
- Review artifact 固定为 `docs/reviews/memory_atlas_v1_1_7_stage7_review.md`。
- Stage 7 覆盖 Phase 7.1 Search 2.0 和 Phase 7.2 Review / Summary / Iteration。
- Stage 7 review 通过后 pending Stage 8。
- No GitHub main upload before whole Stage 0-10 completion。

参数记录：

- `PARAM-MA-V117-S7-REVIEW-001 stage7_review_status = stage_7_review_passed_pending_stage8_no_github_main_upload`
- `PARAM-MA-V117-S7-REVIEW-002 stage7_review_required_validator = validate:v1.1.7-stage7`
- `PARAM-MA-V117-S7-REVIEW-003 stage7_review_artifact = docs/reviews/memory_atlas_v1_1_7_stage7_review.md`
- `PARAM-MA-V117-S7-REVIEW-004 stage7_review_phase_coverage = Phase 7.1;Phase 7.2;Search 2.0;Review / Summary / Iteration`
- `PARAM-MA-V117-S7-REVIEW-005 stage7_review_next_gate = pending Stage 8`
- `PARAM-MA-V117-S7-REVIEW-006 upload_boundary = No GitHub main upload before whole Stage 0-10 completion`

验收信号：

- `validate:v1.1.7-stage7` checks Stage 6 continuity, Phase 7.1, Phase 7.2,
  records, canonical remote, local branch and no-upload boundary.

Machine-readable boundary summary: Stage 7 Review; MA-V117-S7-REVIEW; ACC-MA-V117-S7-REVIEW; stage_7_review_passed_pending_stage8_no_github_main_upload; validate:v1.1.7-stage7; Phase 7.1; Phase 7.2; Search 2.0; Review / Summary / Iteration; pending Stage 8; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply.

## 96. Memory Atlas v1.1.7 Stage 7 Phase 7.2 Review / Summary / Iteration Runtime

状态：`phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review`。

验收 ID：`ACC-MA-V117-S7P02`。

模型参数：

- Runtime version 固定为 `review_summary_iteration_runtime.v1_1_7_stage7_phase2`。
- Review schema version 固定为 `memory_atlas_review_summary.v1_1_7_stage7_phase2`。
- `validate:v1.1.7-stage7-phase2` 是本 phase 必跑 validator。
- `validate:review-summary-iteration-browser` 是本 phase 浏览器 validator。
- Review / Summary / Iteration 输出必须显示 `proposal_candidate`、`evidence_refs` 和 `iteration_backlog`。
- Runtime 必须回答八个复盘问题，并显示 review period、proposal-only 决策和 iteration backlog。
- No Stage 8 summary closure。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase2.cjs`
- `apps/memory-atlas/scripts/validate_review_summary_iteration_browser.cjs`

参数记录：

- `PARAM-MA-V117-S7P02-001 stage7_phase2_status = phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review`
- `PARAM-MA-V117-S7P02-002 stage7_phase2_required_validator = validate:v1.1.7-stage7-phase2`
- `PARAM-MA-V117-S7P02-003 stage7_phase2_browser_validator = validate:review-summary-iteration-browser`
- `PARAM-MA-V117-S7P02-004 review_summary_iteration_runtime_version = review_summary_iteration_runtime.v1_1_7_stage7_phase2`
- `PARAM-MA-V117-S7P02-005 review_summary_iteration_schema_version = memory_atlas_review_summary.v1_1_7_stage7_phase2`
- `PARAM-MA-V117-S7P02-006 output_fields = proposal_candidate;evidence_refs;iteration_backlog`
- `PARAM-MA-V117-S7P02-007 boundary = No Stage 8 summary closure;No GitHub main upload;No raw/private read;No direct active-memory writeback`

验收信号：

- `window.__memoryAtlasStage7Phase2` reports runtime version, schema version, question count, panel ids, evidence refs, iteration item count and safety flags.
- Browser screenshot validates the production `summary` view.

Machine-readable boundary summary: Phase 7.2; Review / Summary / Iteration; MA-V117-S7P02; ACC-MA-V117-S7P02; phase_7_2_review_summary_iteration_runtime_completed_pending_stage7_review; validate:v1.1.7-stage7-phase2; validate:review-summary-iteration-browser; review_summary_iteration_runtime.v1_1_7_stage7_phase2; memory_atlas_review_summary.v1_1_7_stage7_phase2; proposal_candidate; evidence_refs; iteration_backlog; No Stage 8 summary closure; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply.

## 95. Memory Atlas v1.1.7 Stage 7 Phase 7.1 Search 2.0 Runtime

状态：`phase_7_1_search_2_0_runtime_completed_pending_stage7_review`。

验收 ID：`ACC-MA-V117-S7P01`。

模型参数：

- Runtime version 固定为 `search_2_0_runtime.v1_1_7_stage7_phase1`。
- Session Summary version 固定为 `search_2_0_session_summary.v1_1_7_stage7_phase1`。
- `validate:v1.1.7-stage7-phase1` 是本 phase 必跑 validator。
- `validate:search-2-0-browser` 是本 phase 浏览器 validator。
- Search 2.0 结果必须显示 `matched_reason` 和 `evidence_refs`。
- Result actions 必须覆盖 `jump_to_starfield`, `jump_to_river`, `open_inspector`。
- No Review / Summary / Iteration runtime。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage7_phase1.cjs`
- `apps/memory-atlas/scripts/validate_search_2_0_browser.cjs`

参数记录：

- `PARAM-MA-V117-S7P01-001 stage7_phase1_status = phase_7_1_search_2_0_runtime_completed_pending_stage7_review`
- `PARAM-MA-V117-S7P01-002 stage7_phase1_required_validator = validate:v1.1.7-stage7-phase1`
- `PARAM-MA-V117-S7P01-003 stage7_phase1_browser_validator = validate:search-2-0-browser`
- `PARAM-MA-V117-S7P01-004 search_2_0_runtime_version = search_2_0_runtime.v1_1_7_stage7_phase1`
- `PARAM-MA-V117-S7P01-005 search_2_0_session_summary_version = search_2_0_session_summary.v1_1_7_stage7_phase1`
- `PARAM-MA-V117-S7P01-006 result_fields = matched_reason;evidence_refs;proposal_candidate`
- `PARAM-MA-V117-S7P01-007 result_actions = jump_to_starfield;jump_to_river;open_inspector`

验收信号：

- Static validator checks Stage 6 continuity, Search 2.0 runtime hooks, browser validator contract, records, canonical remote and no-upload boundary。
- Browser validator checks result fields, `window.__memoryAtlasStage7Phase1`, zero-result recovery, Starfield/River/Inspector jumps, console cleanliness and screenshot。

Machine-readable boundary summary: Phase 7.1; Search 2.0; MA-V117-S7P01; ACC-MA-V117-S7P01; phase_7_1_search_2_0_runtime_completed_pending_stage7_review; validate:v1.1.7-stage7-phase1; validate:search-2-0-browser; search_2_0_runtime.v1_1_7_stage7_phase1; search_2_0_session_summary.v1_1_7_stage7_phase1; matched_reason; evidence_refs; No Review / Summary / Iteration runtime; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply.

## 94. Memory Atlas v1.1.7 Stage 6 Review

状态：`stage_6_review_passed_pending_stage7_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S6-REVIEW`。

模型参数：

- `validate:v1.1.7-stage6` 是 Stage 6 review 必跑 validator。
- Review 覆盖 Phase 6.1、Phase 6.2。
- Phase 6.1 固定 `data_map_structure_model.v1_1_7_stage6_phase1` 和 `data_map_relation_explanation.v1_1_7_stage6_phase1`。
- Phase 6.2 固定 `data_map_detail_panel.v1_1_7_stage6_phase2` 和 `data_map_proposal_entry.v1_1_7_stage6_phase2`。
- Next gate 是 pending Stage 7。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/reviews/memory_atlas_v1_1_7_stage6_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6.cjs`

参数记录：

- `PARAM-MA-V117-S6-REVIEW-001 stage6_review_status = stage_6_review_passed_pending_stage7_no_github_main_upload`
- `PARAM-MA-V117-S6-REVIEW-002 stage6_review_required_validator = validate:v1.1.7-stage6`
- `PARAM-MA-V117-S6-REVIEW-003 stage6_review_phase_coverage = Phase 6.1;Phase 6.2`
- `PARAM-MA-V117-S6-REVIEW-004 stage6_review_next_gate = pending Stage 7`
- `PARAM-MA-V117-S6-REVIEW-005 stage6_review_boundary = No GitHub main upload`

验收信号：

- Static validator checks Stage 5 review continuity, Phase 6.1/6.2 validators, Stage 6 review artifact, records, canonical remote and no-upload boundary。

Machine-readable boundary summary: Stage 6 Review; MA-V117-S6-REVIEW; ACC-MA-V117-S6-REVIEW; stage_6_review_passed_pending_stage7_no_github_main_upload; validate:v1.1.7-stage6; Phase 6.1; Phase 6.2; pending Stage 7; No Stage 7 work; No Search 2.0 work; No Review / Summary / Iteration runtime work; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply.

## 93. Memory Atlas v1.1.7 Stage 6 Phase 6.2 Details & Editing

状态：`phase_6_2_data_map_detail_proposal_completed_pending_stage6_review`。

验收 ID：`ACC-MA-V117-S6P02`。

模型参数：

- Detail Panel version 固定为 `data_map_detail_panel.v1_1_7_stage6_phase2`。
- Proposal Entry version 固定为 `data_map_proposal_entry.v1_1_7_stage6_phase2`。
- `validate:v1.1.7-stage6-phase2` 是本 phase 必跑 validator。
- `validate:data-map-detail-proposal-browser` 是本 phase 浏览器 validator。
- Phase 6.2 Details & Editing 覆盖 `数据导图详情面板` 和 `数据导图 proposal 入口`。
- 详情字段：`asset`, `theme`, `suggested action`, `importance`, `priority`。
- proposal-only。
- No Stage 6 review。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase2.cjs`
- `apps/memory-atlas/scripts/validate_data_map_detail_proposal_browser.cjs`

参数记录：

- `PARAM-MA-V117-S6P02-001 stage6_phase2_status = phase_6_2_data_map_detail_proposal_completed_pending_stage6_review`
- `PARAM-MA-V117-S6P02-002 stage6_phase2_required_validator = validate:v1.1.7-stage6-phase2`
- `PARAM-MA-V117-S6P02-003 stage6_phase2_browser_validator = validate:data-map-detail-proposal-browser`
- `PARAM-MA-V117-S6P02-004 detail_panel_version = data_map_detail_panel.v1_1_7_stage6_phase2`
- `PARAM-MA-V117-S6P02-005 proposal_entry_version = data_map_proposal_entry.v1_1_7_stage6_phase2`
- `PARAM-MA-V117-S6P02-006 detail_fields = asset;theme;suggested action;importance;priority`

验收信号：

- Static validator checks Stage 6 Phase 6.1 continuity, Data Map contract, production runtime hooks, browser validator contract, records, canonical remote and no-upload boundary。
- Browser validator checks node click, detail fields, proposal export, `window.__memoryAtlasStage6Phase2`, console cleanliness and screenshot。

Machine-readable boundary summary: Phase 6.2; Details & Editing; MA-V117-S6P02; ACC-MA-V117-S6P02; phase_6_2_data_map_detail_proposal_completed_pending_stage6_review; validate:v1.1.7-stage6-phase2; validate:data-map-detail-proposal-browser; data_map_detail_panel.v1_1_7_stage6_phase2; data_map_proposal_entry.v1_1_7_stage6_phase2; 数据导图详情面板; 数据导图 proposal 入口; proposal-only; No Stage 6 review; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply.

## 92. Memory Atlas v1.1.7 Stage 6 Phase 6.1 Structure Model

状态：`phase_6_1_data_map_structure_model_completed_pending_stage6_review`。

验收 ID：`ACC-MA-V117-S6P01`。

模型参数：

- Structure Model version 固定为 `data_map_structure_model.v1_1_7_stage6_phase1`。
- Relation Explanation version 固定为 `data_map_relation_explanation.v1_1_7_stage6_phase1`。
- `validate:v1.1.7-stage6-phase1` 是本 phase 必跑 validator。
- `validate:data-map-structure-browser` 是本 phase 浏览器 validator。
- 四层结构：`source_layer`, `profile_layer`, `project_decision_layer`, `action_opportunity_layer`。
- 每层必须声明 node types、fields、interaction、detail entry。
- Relation fields: `source`, `strength`, `evidence`, `time`。
- No Phase 6.2。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage6_phase1.cjs`
- `apps/memory-atlas/scripts/validate_data_map_structure_browser.cjs`

参数记录：

- `PARAM-MA-V117-S6P01-001 stage6_phase1_status = phase_6_1_data_map_structure_model_completed_pending_stage6_review`
- `PARAM-MA-V117-S6P01-002 stage6_phase1_required_validator = validate:v1.1.7-stage6-phase1`
- `PARAM-MA-V117-S6P01-003 stage6_phase1_browser_validator = validate:data-map-structure-browser`
- `PARAM-MA-V117-S6P01-004 structure_model_version = data_map_structure_model.v1_1_7_stage6_phase1`
- `PARAM-MA-V117-S6P01-005 relation_explanation_version = data_map_relation_explanation.v1_1_7_stage6_phase1`
- `PARAM-MA-V117-S6P01-006 structure_layers = source_layer;profile_layer;project_decision_layer;action_opportunity_layer`
- `PARAM-MA-V117-S6P01-007 relation_fields = source;strength;evidence;time`

验收信号：

- Static validator checks Stage 5 review continuity, Data Map contract, production runtime hooks, browser validator contract, records, canonical remote and no-upload boundary。
- Browser validator checks four layers, relation click explanation, `window.__memoryAtlasStage6Phase1`, console cleanliness and screenshot。

Machine-readable boundary summary: Phase 6.1; Structure Model; Relation Explanation; MA-V117-S6P01; ACC-MA-V117-S6P01; phase_6_1_data_map_structure_model_completed_pending_stage6_review; validate:v1.1.7-stage6-phase1; validate:data-map-structure-browser; data_map_structure_model.v1_1_7_stage6_phase1; data_map_relation_explanation.v1_1_7_stage6_phase1; source_layer; profile_layer; project_decision_layer; action_opportunity_layer; No Phase 6.2; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply.

## 91. Memory Atlas v1.1.7 Stage 5 Review

状态：`stage_5_review_passed_pending_stage6_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S5-REVIEW`。

模型参数：

- `validate:v1.1.7-stage5` 是 Stage 5 review 必跑 validator。
- Review 覆盖 Phase 5.1、Phase 5.2、Phase 5.3。
- Phase 5.1 固定 `memory_river_interaction_contract.v1_1_7_stage5_phase1` 和 `memory_river_feedback_contract.v1_1_7_stage5_phase1`。
- Phase 5.2 固定 `memory_river_c3_spike.v1_1_7_stage5_phase2`。
- Phase 5.3 固定 `memory_river_integration.v1_1_7_stage5_phase3`、default memory-river 和 legacy rollback。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/reviews/memory_atlas_v1_1_7_stage5_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5.cjs`
- `apps/memory-atlas/package.json`

参数记录：

- `PARAM-MA-V117-S5-REVIEW-001 stage5_review_status = stage_5_review_passed_pending_stage6_no_github_main_upload`
- `PARAM-MA-V117-S5-REVIEW-002 stage5_review_required_validator = validate:v1.1.7-stage5`
- `PARAM-MA-V117-S5-REVIEW-003 stage5_review_phase_coverage = Phase 5.1;Phase 5.2;Phase 5.3`
- `PARAM-MA-V117-S5-REVIEW-004 stage5_review_next_gate = pending Stage 6`

验收信号：

- Stage validator checks Stage 4 review continuity, Phase 5.1 / Phase 5.2 / Phase 5.3 validators, review artifact, records, canonical remote and no-upload boundary。
- Browser evidence remains covered by `validate:memory-river-spike-browser` and `validate:memory-river-integration-browser`。

Machine-readable boundary summary: Stage 5 Review; MA-V117-S5-REVIEW; ACC-MA-V117-S5-REVIEW; stage_5_review_passed_pending_stage6_no_github_main_upload; validate:v1.1.7-stage5; Phase 5.1; Phase 5.2; Phase 5.3; pending Stage 6; No GitHub main upload; No Stage 6 work; No Data Map work.

## 90. Memory Atlas v1.1.7 Stage 5 Phase 5.3 Timeline Integration

状态：`phase_5_3_timeline_integration_completed_pending_stage5_review`。

验收 ID：`ACC-MA-V117-S5P03`。

模型参数：

- Integration version 固定为 `memory_river_integration.v1_1_7_stage5_phase3`。
- `validate:v1.1.7-stage5-phase3` 是本 phase 必跑 validator。
- `validate:memory-river-integration-browser` 是本 phase 浏览器 validator。
- Timeline 默认 renderer 为 default memory-river。
- Legacy renderer 保留为 `legacy`，legacy rollback 路径为 in-app toggle、`timelineRenderer=legacy`、`timeline=legacy`、localStorage 和 env override。
- Required browser checks: default Memory River, legacy rollback, URL rollback, brush interaction, selected range metadata, evidence layers, screenshot, console safety。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/config/visualFlags.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase3.cjs`
- `apps/memory-atlas/scripts/validate_memory_river_integration_browser.cjs`

参数记录：

- `PARAM-MA-V117-S5P03-001 stage5_phase3_status = phase_5_3_timeline_integration_completed_pending_stage5_review`
- `PARAM-MA-V117-S5P03-002 stage5_phase3_required_validator = validate:v1.1.7-stage5-phase3`
- `PARAM-MA-V117-S5P03-003 stage5_phase3_browser_validator = validate:memory-river-integration-browser`
- `PARAM-MA-V117-S5P03-004 integration_version = memory_river_integration.v1_1_7_stage5_phase3`
- `PARAM-MA-V117-S5P03-005 timeline_renderer_default = default memory-river`
- `PARAM-MA-V117-S5P03-006 rollback_mode = legacy rollback`

验收信号：

- Static validator checks Stage 5 Phase 5.2 continuity, feature flag version, runtime hook, plan/acceptance docs, records, canonical remote and no-upload boundary。
- Browser validator checks default Memory River, legacy rollback, URL rollback, brush interaction, selected range metadata, evidence layers, console cleanliness and screenshot。

Machine-readable boundary summary: Phase 5.3; MA-V117-S5P03; ACC-MA-V117-S5P03; phase_5_3_timeline_integration_completed_pending_stage5_review; validate:v1.1.7-stage5-phase3; validate:memory-river-integration-browser; memory_river_integration.v1_1_7_stage5_phase3; default memory-river; legacy rollback; No GitHub main upload; No Stage 5 review; No Stage 6.

## 89. Memory Atlas v1.1.7 Stage 5 Phase 5.2 C3 River Spike

状态：`phase_5_2_c3_river_spike_completed_pending_stage5_review`。

验收 ID：`ACC-MA-V117-S5P02`。

模型参数：

- Spike version 固定为 `memory_river_c3_spike.v1_1_7_stage5_phase2`。
- `validate:v1.1.7-stage5-phase2` 是本 phase 必跑 validator。
- `validate:memory-river-spike-browser` 是本 phase 浏览器 validator。
- Time scale levels: `year`, `month`, `week`, `day`。
- Required runtime controls: `zoom`, `brush_selection`, `selected_range_summary`, `theme_lanes`, `black_hole_band`, `proto_star_marker`, `reduced_motion`。
- Required theme trends: `rising`, `declining`, `stable`, `conflict`。
- No production Timeline replacement。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/experiments/memory-river-spike/fixture.ts`
- `apps/memory-atlas/src/experiments/memory-river-spike/main.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase2.cjs`
- `apps/memory-atlas/scripts/validate_memory_river_spike_browser.cjs`

参数记录：

- `PARAM-MA-V117-S5P02-001 stage5_phase2_status = phase_5_2_c3_river_spike_completed_pending_stage5_review`
- `PARAM-MA-V117-S5P02-002 stage5_phase2_required_validator = validate:v1.1.7-stage5-phase2`
- `PARAM-MA-V117-S5P02-003 stage5_phase2_browser_validator = validate:memory-river-spike-browser`
- `PARAM-MA-V117-S5P02-004 spike_version = memory_river_c3_spike.v1_1_7_stage5_phase2`
- `PARAM-MA-V117-S5P02-005 time_scale_levels = year;month;week;day`
- `PARAM-MA-V117-S5P02-006 theme_trends = rising;declining;stable;conflict`

验收信号：

- Static validator checks Stage 5 Phase 5.1 continuity, spike files, product/acceptance docs, records, production isolation, canonical remote and no-upload boundary。
- Browser validator checks year/month/week/day time levels, zoom, brush selected range themes/events, Black Hole / Proto-Star positioning, reduced motion, console cleanliness and screenshot。

Machine-readable boundary summary: Stage 5 Phase 5.2 C3 River Spike; MA-V117-S5P02; ACC-MA-V117-S5P02; phase_5_2_c3_river_spike_completed_pending_stage5_review; validate:v1.1.7-stage5-phase2; validate:memory-river-spike-browser; memory_river_c3_spike.v1_1_7_stage5_phase2; Phase 5.2; No production Timeline replacement; No GitHub main upload; No raw/private read; No direct active-memory writeback; No agent apply; No Stage 5.3.

## 88. Memory Atlas v1.1.7 Stage 5 Phase 5.1 Interaction Contract

状态：`phase_5_1_interaction_contract_completed_pending_stage5_review`。

验收 ID：`ACC-MA-V117-S5P01`。

模型参数：

- Interaction Contract 固定为 `memory_river_interaction_contract.v1_1_7_stage5_phase1`。
- Feedback Contract 固定为 `memory_river_feedback_contract.v1_1_7_stage5_phase1`。
- `validate:v1.1.7-stage5-phase1` 是本 phase 必跑 validator。
- 必备交互：`zoom`, `brush`, `theme_lanes`, `event_points`, `status_bands`, `detail_panel`。
- 必备反馈控制：`visual_feedback`, `optional_audio`, `pseudo_haptic`, `reduced_motion`, `feedback_disable_control`, `audio_default_off`, `vibration_not_required`。
- No Stage 5.2。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/product/memory_river_interaction_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage5_phase1_interaction_contract_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage5_phase1.cjs`

参数记录：

- `PARAM-MA-V117-S5P01-001 stage5_phase1_status = phase_5_1_interaction_contract_completed_pending_stage5_review`
- `PARAM-MA-V117-S5P01-002 stage5_phase1_required_validator = validate:v1.1.7-stage5-phase1`
- `PARAM-MA-V117-S5P01-003 interaction_contract_version = memory_river_interaction_contract.v1_1_7_stage5_phase1`
- `PARAM-MA-V117-S5P01-004 feedback_contract_version = memory_river_feedback_contract.v1_1_7_stage5_phase1`
- `PARAM-MA-V117-S5P01-005 required_interactions = zoom;brush;theme_lanes;event_points;status_bands;detail_panel`
- `PARAM-MA-V117-S5P01-006 required_feedback_controls = visual_feedback;optional_audio;pseudo_haptic;reduced_motion;feedback_disable_control;audio_default_off;vibration_not_required`

验收信号：

- Memory River interaction contract addendum。
- `validate:v1.1.7-stage5-phase1` 检查 Stage 4 review continuity、interaction contract、feedback contract、records、package script 和 no-runtime/no-upload boundary。
- Boundary includes No GitHub main upload, No Stage 5.2, No C3 River Spike, No Timeline replacement, No runtime UI/CSS, No raw/private read, No direct active-memory writeback and No agent apply。

## 87. Memory Atlas v1.1.7 Stage 4 Review Gate

状态：`stage_4_review_passed_pending_stage5_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S4-REVIEW`。

模型参数：

- Stage 4 Review 覆盖 Phase 4.1 / Phase 4.2 / Phase 4.3，不进入 Stage 5。
- `validate:v1.1.7-stage4` 是整阶段必跑 validator。
- Phase 4.1 Visual Contract Update、Phase 4.2 C3 Starfield Spike 和 Phase 4.3 Integration 是本 gate 的完整覆盖范围。
- Stage 4 review status 固定为 `stage_4_review_passed_pending_stage5_no_github_main_upload`，pending Stage 5。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/reviews/memory_atlas_v1_1_7_stage4_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4.cjs`
- `apps/memory-atlas/package.json`

参数记录：

- `PARAM-MA-V117-S4-REVIEW-001 stage4_review_status = stage_4_review_passed_pending_stage5_no_github_main_upload`
- `PARAM-MA-V117-S4-REVIEW-002 stage4_review_required_validator = validate:v1.1.7-stage4`
- `PARAM-MA-V117-S4-REVIEW-003 stage4_review_phase_scope = Phase 4.1;Phase 4.2;Phase 4.3`
- `PARAM-MA-V117-S4-REVIEW-004 stage4_review_deferred_work = pending Stage 5;Memory River refactor;Stage 6+ hardening;local app packaging;Cloudflare deploy;GitHub main upload`

验收信号：

- Stage 4 review artifact。
- `validate:v1.1.7-stage4` 检查 Stage 3 continuity、Phase 4.1 / Phase 4.2 / Phase 4.3 validators、records、package script 和 no-upload boundary。
- Boundary includes No GitHub main upload, No Stage 5 work, No raw/private read, No direct active-memory writeback, No agent apply and No build/deploy/app install。

## 86. Memory Atlas v1.1.7 Stage 4 Phase 4.3 Integration

状态：`phase_4_3_integration_completed_pending_stage4_review`。

验收 ID：`ACC-MA-V117-S4P03`。

模型参数：

- Production Galaxy Integration 固定为 `memory_starfield_integration.v1_1_7_stage4_phase3`。
- Snapshot Mapping 固定为 `memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3`。
- `validate:v1.1.7-stage4-phase3` 是本 phase 静态必跑 validator。
- `validate:memory-starfield-integration-browser` 是本 phase 浏览器必跑 validator。
- `default_renderer_mode = memory-starfield`。
- `legacy_renderer_mode = legacy`。
- `mapping_source_priority = redacted_snapshot -> atlas_nodes_fallback`。
- No Stage 5。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/GalaxyScene.tsx`
- `apps/memory-atlas/src/config/visualFlags.ts`
- `apps/memory-atlas/src/models/starfieldMapping.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase3.cjs`
- `apps/memory-atlas/scripts/validate_memory_starfield_integration_browser.cjs`

参数记录：

- `PARAM-MA-V117-S4P03-001 stage4_phase3_status = phase_4_3_integration_completed_pending_stage4_review`
- `PARAM-MA-V117-S4P03-002 stage4_phase3_required_validator = validate:v1.1.7-stage4-phase3`
- `PARAM-MA-V117-S4P03-003 stage4_phase3_browser_validator = validate:memory-starfield-integration-browser`
- `PARAM-MA-V117-S4P03-004 integration_version = memory_starfield_integration.v1_1_7_stage4_phase3`
- `PARAM-MA-V117-S4P03-005 mapping_version = memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3`
- `PARAM-MA-V117-S4P03-006 renderer_modes = default=memory-starfield;rollback=legacy`

验收信号：

- Browser validator 证明默认 new memory-starfield、legacy rollback、snapshot mapping、formula panel 和 screenshot。
- Static validator 检查 Stage 4.2 continuity、Feature Flag、Snapshot Mapping、records、package script 和 no-upload boundary。
- Boundary includes No Stage 5, No GitHub main upload, No raw/private read, No direct active-memory writeback and No agent apply。

## 85. v1.1.7 Stage 4 Phase 4.2 C3 Starfield Spike

状态：`phase_4_2_c3_starfield_spike_completed_pending_stage4_review`。

验收 ID：`ACC-MA-V117-S4P02`。

模型参数：

- C3 Starfield Spike 版本固定为 `memory_starfield_c3_spike.v1_1_7_stage4_phase2`。
- `validate:v1.1.7-stage4-phase2` 是本 phase 静态必跑 validator。
- `validate:memory-starfield-spike-browser` 是本 phase 浏览器必跑 validator。
- 粒子下限：`>=10k particles`。
- 桌面浏览器 FPS 下限：`>=30 FPS`。
- 必备运行特征：GPU particle spike、Flow Field / Curl Noise、Cluster Gravity、Hover Cards B2、screenshot。
- No production Galaxy replacement。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/experiments/memory-starfield-spike/main.ts`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/shaders/flowField.ts`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/fixture.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase2.cjs`
- `apps/memory-atlas/scripts/validate_memory_starfield_spike_browser.cjs`

参数记录：

- `PARAM-MA-V117-S4P02-001 stage4_phase2_status = phase_4_2_c3_starfield_spike_completed_pending_stage4_review`
- `PARAM-MA-V117-S4P02-002 stage4_phase2_required_validator = validate:v1.1.7-stage4-phase2`
- `PARAM-MA-V117-S4P02-003 stage4_phase2_browser_validator = validate:memory-starfield-spike-browser`
- `PARAM-MA-V117-S4P02-004 spike_version = memory_starfield_c3_spike.v1_1_7_stage4_phase2`
- `PARAM-MA-V117-S4P02-005 runtime_thresholds = >=10k particles;>=30 FPS;trajectoryTrailCount>=256;gravitySourceCount>=6`
- `PARAM-MA-V117-S4P02-006 required_runtime_features = GPU particle spike;Flow Field / Curl Noise;Cluster Gravity;Hover Cards B2;screenshot`

验收信号：

- Browser validator 证明 `>=10k particles`、`>=30 FPS`、`curl_noise_shader`、particle trails、gravity sources、Hover Cards B2 和 screenshot。
- Static validator 检查 Stage 4.1 continuity、spike source、fixture safety、production isolation、records、package script 和 no-upload boundary。
- Boundary includes No production Galaxy replacement, No production route/navigation change, No GitHub main upload, No raw/private read, No direct active-memory writeback and No agent apply。

## 84. v1.1.7 Stage 4 Phase 4.1 Visual Contract Update

状态：`phase_4_1_visual_contract_update_completed_pending_stage4_review`。

验收 ID：`ACC-MA-V117-S4P01`。

模型参数：

- Visual Contract Update 固定 `memory_starfield_visual_contract.v1_1_7_stage4_phase1`。
- Memory Terrain Layer 固定 `memory_terrain_layer.v1_1_7_stage4_phase1`。
- `validate:v1.1.7-stage4-phase1` 是本 phase 必跑 validator。
- 必备视觉原语：`nebula_field`, `flow_field`, `particle_trails`, `gravity_sources`, `black_hole_core`, `proto_star_cloud`, `memory_terrain_layer`。
- 必备地形语义：`long_term_theme`, `growth_band`, `migration_flow`, `relic`, `black_hole`, `opportunity`。
- C3 Starfield Spike 是未来生产 renderer replacement 前的验证路径。
- No Phase 4.2。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/product/memory_starfield_visual_contract.md`
- `docs/architecture/memory_terrain_layer.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage4_phase1_visual_contract_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage4_phase1.cjs`

参数记录：

- `PARAM-MA-V117-S4P01-001 stage4_phase1_status = phase_4_1_visual_contract_update_completed_pending_stage4_review`
- `PARAM-MA-V117-S4P01-002 stage4_phase1_required_validator = validate:v1.1.7-stage4-phase1`
- `PARAM-MA-V117-S4P01-003 visual_contract_version = memory_starfield_visual_contract.v1_1_7_stage4_phase1`
- `PARAM-MA-V117-S4P01-004 terrain_contract_version = memory_terrain_layer.v1_1_7_stage4_phase1`
- `PARAM-MA-V117-S4P01-005 required_visual_primitives = nebula_field;flow_field;particle_trails;gravity_sources;black_hole_core;proto_star_cloud;memory_terrain_layer`
- `PARAM-MA-V117-S4P01-006 required_terrain_classes = long_term_theme;growth_band;migration_flow;relic;black_hole;opportunity`

验收信号：

- Visual Contract Update product contract。
- `validate:v1.1.7-stage4-phase1` 检查 Stage 3 continuity、visual contract、terrain layer、records、package script 和 no-upload boundary。
- Boundary includes No Phase 4.2, No runtime renderer replacement, No GitHub main upload, No raw/private read, No direct active-memory writeback, No agent apply and No build/deploy/app install。

## 83. v1.1.7 Stage 3 Review Gate

状态：`stage_3_review_passed_pending_stage4_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S3-REVIEW`。

模型参数：

- Stage 3 Review 只复审 Phase 3.1 / Phase 3.2，不进入 Stage 4。
- `validate:v1.1.7-stage3` 是整阶段必跑 validator。
- Phase 3.1 Default Home Structure 和 Phase 3.2 Home Detail Operations 是本 gate 的完整覆盖范围。
- Stage 3 review status 固定为 `stage_3_review_passed_pending_stage4_no_github_main_upload`，pending Stage 4。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/reviews/memory_atlas_v1_1_7_stage3_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3.cjs`
- `apps/memory-atlas/package.json`

参数记录：

- `PARAM-MA-V117-S3-REVIEW-001 stage3_review_status = stage_3_review_passed_pending_stage4_no_github_main_upload`
- `PARAM-MA-V117-S3-REVIEW-002 stage3_review_required_validator = validate:v1.1.7-stage3`
- `PARAM-MA-V117-S3-REVIEW-003 stage3_review_phase_scope = Phase 3.1;Phase 3.2`
- `PARAM-MA-V117-S3-REVIEW-004 stage3_review_deferred_work = pending Stage 4;Memory Starfield refactor;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

验收信号：

- Stage 3 review artifact。
- `validate:v1.1.7-stage3` 检查 Stage 2 continuity、Phase 3.1 / Phase 3.2 validators、records、package script 和 no-upload boundary。
- Boundary includes No GitHub main upload, No Stage 4 work, No raw/private read, No direct active-memory writeback, No agent apply and No build/deploy/app install。

## 82. v1.1.7 Stage 3 Phase 3.2 Home Detail Operations

状态：`phase_3_2_home_detail_operations_completed_pending_stage3_review`。

验收 ID：`ACC-MA-V117-S3P02`。

模型参数：

- Stage 3 Phase 3.2 固定 Home Detail Operations，不进入 No Stage 3 Review。
- `validate:v1.1.7-stage3-phase2` 是本 phase 必跑 validator。
- Operation version 固定为 `memory_overview_detail_operations.v1_1_7_stage3_phase2`。
- Operation sections: `top_actions`, `level_assets`, `theme_categories`。
- Section versions: `top_actions_section.v1_1_7_stage3_phase2`, `level_assets_section.v1_1_7_stage3_phase2`, `theme_categories_section.v1_1_7_stage3_phase2`。
- Asset groups: `core_profile`, `project`, `decision`, `temporary`, `stale`。
- Theme category states: `rising`, `declining`, `conflict`, `opportunity`, `stable`。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_overview_product_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage3_phase2_home_detail_operations_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase2.cjs`

参数记录：

- `PARAM-MA-V117-S3P02-001 stage3_phase2_status = phase_3_2_home_detail_operations_completed_pending_stage3_review`
- `PARAM-MA-V117-S3P02-002 stage3_phase2_required_validator = validate:v1.1.7-stage3-phase2`
- `PARAM-MA-V117-S3P02-003 home_detail_operations = memory_overview_detail_operations.v1_1_7_stage3_phase2`
- `PARAM-MA-V117-S3P02-004 operation_sections = top_actions;level_assets;theme_categories`
- `PARAM-MA-V117-S3P02-005 asset_groups = core_profile;project;decision;temporary;stale`
- `PARAM-MA-V117-S3P02-006 theme_category_states = rising;declining;conflict;opportunity;stable`

验收信号：

- Home Detail Operations product contract。
- `validate:v1.1.7-stage3-phase2` 检查三类首页明细区、records、package script 和 no-upload boundary。
- Boundary includes No Stage 3 Review, No GitHub main upload, No raw/private read, No direct active-memory writeback, No agent apply and No build/deploy/app install。

## 81. v1.1.7 Stage 3 Phase 3.1 Default Home Structure

状态：`phase_3_1_default_home_structure_completed_pending_stage3_review`。

验收 ID：`ACC-MA-V117-S3P01`。

模型参数：

- Stage 3 Phase 3.1 固定 Default Home Structure，不进入 No Stage 3 Phase 3.2。
- `validate:v1.1.7-stage3-phase1` 是本 phase 必跑 validator。
- Structure version 固定为 `memory_overview_default_home.v1_1_7_stage3_phase1`。
- 默认 route 固定为 `home`。
- Required sections: `status_summary`, `suggested_actions`, `weather`, `black_holes`, `proto_stars`, `assets`, `themes`, `entry_points`。
- Rollback core 4 sections: `status_summary`, `suggested_actions`, `weather`, `entry_points`。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_overview_product_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage3_phase1_default_home_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage3_phase1.cjs`

参数记录：

- `PARAM-MA-V117-S3P01-001 stage3_phase1_status = phase_3_1_default_home_structure_completed_pending_stage3_review`
- `PARAM-MA-V117-S3P01-002 stage3_phase1_required_validator = validate:v1.1.7-stage3-phase1`
- `PARAM-MA-V117-S3P01-003 default_home_structure_version = memory_overview_default_home.v1_1_7_stage3_phase1`
- `PARAM-MA-V117-S3P01-004 default_home_sections = status_summary;suggested_actions;weather;black_holes;proto_stars;assets;themes;entry_points`
- `PARAM-MA-V117-S3P01-005 stage3_phase1_deferred_work = No Stage 3 Phase 3.2;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

验收信号：

- Default Home Structure product contract。
- `validate:v1.1.7-stage3-phase1` 检查默认 route、8 个 section marker、records、package script 和 no-upload boundary。
- Boundary includes No Stage 3 Phase 3.2, No GitHub main upload, No raw/private read, No direct active-memory writeback, No agent apply and No build/deploy/app install。

## 80. v1.1.7 Stage 2 Review Gate

状态：`stage_2_review_passed_pending_stage3_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S2-REVIEW`。

模型参数：

- Stage 2 Review 只复审 Phase 2.1 / Phase 2.2，不进入 Stage 3。
- `validate:v1.1.7-stage2` 是整阶段必跑 validator。
- Phase 2.1 Editable Draft Model 和 Phase 2.2 Proposal UI 是本 gate 的完整覆盖范围。
- Stage 2 review status 固定为 `stage_2_review_passed_pending_stage3_no_github_main_upload`，pending Stage 3。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/reviews/memory_atlas_v1_1_7_stage2_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2.cjs`
- `apps/memory-atlas/package.json`

参数记录：

- `PARAM-MA-V117-S2-REVIEW-001 stage2_review_status = stage_2_review_passed_pending_stage3_no_github_main_upload`
- `PARAM-MA-V117-S2-REVIEW-002 stage2_review_required_validator = validate:v1.1.7-stage2`
- `PARAM-MA-V117-S2-REVIEW-003 stage2_review_phase_scope = Phase 2.1;Phase 2.2`
- `PARAM-MA-V117-S2-REVIEW-004 stage2_review_deferred_work = pending Stage 3;Default Home Structure;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

验收信号：

- Stage 2 review artifact。
- `validate:v1.1.7-stage2` 检查 Stage 1 continuity、Phase 2.1 / Phase 2.2 validators、records、package script 和 no-upload boundary。
- Boundary includes No GitHub main upload, No Stage 3 work, No raw/private read, No direct active-memory writeback, No agent apply and No build/deploy/app install。

## 79. v1.1.7 Stage 2 Phase 2.2 Proposal UI

状态：`phase_2_2_proposal_ui_completed_pending_stage2_review`。

验收 ID：`ACC-MA-V117-S2P02`。

模型参数：

- Stage 2 Phase 2.2 只实现 Proposal UI 初始能力，不进入 Search 2.0、Review workflow 或 Data Map 2.0。
- Proposal UI 初始字段为 `importance` 和 `priority`。
- Proposal export schema 固定为 `memory_atlas_proposal_export.v1`。
- Diff preview 必须显示 `original_value`、`proposed_value`、`impact_summary` 和 `rollback_metadata`。
- Export / Rollback Contract 必须保留 `proposal_only`、`requires_conflict_check` 和 `requires_agent_or_human_apply`。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `apps/memory-atlas/src/components/ProposalEditor.tsx`
- `apps/memory-atlas/src/components/ProposalDiffPreview.tsx`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase2.cjs`

参数记录：

- `PARAM-MA-V117-S2P02-001 stage2_phase2_status = phase_2_2_proposal_ui_completed_pending_stage2_review`
- `PARAM-MA-V117-S2P02-002 stage2_phase2_required_validator = validate:v1.1.7-stage2-phase2`
- `PARAM-MA-V117-S2P02-003 proposal_ui_fields = importance;priority`
- `PARAM-MA-V117-S2P02-004 proposal_ui_components = ProposalEditor;ProposalDiffPreview`
- `PARAM-MA-V117-S2P02-005 export_schema_version = memory_atlas_proposal_export.v1`
- `PARAM-MA-V117-S2P02-006 stage2_phase2_deferred_work = Stage 2 review;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

验收信号：

- ProposalEditor runtime component。
- ProposalDiffPreview runtime component。
- `validate:v1.1.7-stage2-phase2` 检查 UI、合同、参数、记录和改动范围。
- Boundary includes No GitHub main upload, No raw/private read, No direct writeback, No agent apply and No build/deploy/app install。

## 78. v1.1.7 Stage 2 Phase 2.1 Editable Draft Model

状态：`phase_2_1_editable_draft_model_completed_pending_stage2_review`。

验收 ID：`ACC-MA-V117-S2P01`。

模型参数：

- Stage 2 Phase 2.1 只建立 Editable Draft Model 和 Draft State Store，不进入 Proposal UI。
- 可编辑字段白名单固定为 `importance`、`priority`、`status`、`theme_override`、`action_state`、`note`。
- Draft schema version 固定为 `memory_atlas_proposal_draft.v1`。
- Draft store key 固定为 `memory-atlas.proposal-drafts.v1`。
- Draft Store 必须支持 refresh warning 和 undo draft change。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/architecture/proposal_edit_model.md`
- `apps/memory-atlas/src/state/proposalDraftStore.ts`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage2_phase1.cjs`
- `config/visualization/model_parameters.universe_state.yaml`

参数记录：

- `PARAM-MA-V117-S2P01-001 stage2_phase1_status = phase_2_1_editable_draft_model_completed_pending_stage2_review`
- `PARAM-MA-V117-S2P01-002 stage2_phase1_required_validator = validate:v1.1.7-stage2-phase1`
- `PARAM-MA-V117-S2P01-003 editable_field_whitelist = importance;priority;status;theme_override;action_state;note`
- `PARAM-MA-V117-S2P01-004 draft_schema_version = memory_atlas_proposal_draft.v1`
- `PARAM-MA-V117-S2P01-005 draft_store_key = memory-atlas.proposal-drafts.v1`
- `PARAM-MA-V117-S2P01-006 draft_required_behaviors = refresh warning;undo draft change;serialize;parse;load;save;clear`
- `PARAM-MA-V117-S2P01-007 stage2_phase1_deferred_work = Phase 2.2 Proposal UI;Proposal Diff Preview;proposal JSON export;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

验收信号：

- Proposal edit model contract。
- Draft State Store implementation。
- `validate:v1.1.7-stage2-phase1` 检查模型、store、参数、记录和改动范围。
- Boundary includes No Proposal UI, No GitHub main upload, No raw/private read, No direct writeback, No agent apply and No build/deploy/app install。

## 77. v1.1.7 Stage 1 Review Gate

状态：`stage_1_review_passed_pending_stage2_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S1-REVIEW`。

模型参数：

- Stage 1 Review 只复审 Phase 1.1 / Phase 1.2 / Phase 1.3 / Phase 1.4，不进入 Stage 2。
- `validate:v1.1.7-stage1` 是整阶段必跑 validator。
- Phase 1.1 Universe State、Phase 1.2 Next Action、Phase 1.3 Level Asset、Phase 1.4 Topic Classification 是本 gate 的完整覆盖范围。
- Stage 1 review status 固定为 `stage_1_review_passed_pending_stage2_no_github_main_upload`，pending Stage 2。
- No GitHub main upload before whole Stage 0-10 completion。

运行时文件：

- `docs/reviews/memory_atlas_v1_1_7_stage1_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1.cjs`
- `apps/memory-atlas/package.json`

参数记录：

- `PARAM-MA-V117-S1-REVIEW-001 stage1_review_status = stage_1_review_passed_pending_stage2_no_github_main_upload`
- `PARAM-MA-V117-S1-REVIEW-002 stage1_review_required_validator = validate:v1.1.7-stage1`
- `PARAM-MA-V117-S1-REVIEW-003 stage1_review_phase_scope = Phase 1.1;Phase 1.2;Phase 1.3;Phase 1.4`
- `PARAM-MA-V117-S1-REVIEW-004 stage1_review_deferred_work = pending Stage 2;Stage 2 proposal editor;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

验收信号：

- Stage 1 review artifact。
- Deterministic Stage 1 validator。
- Records include `MA-V117-S1-REVIEW` / `ACC-MA-V117-S1-REVIEW` / `stage_1_review_passed_pending_stage2_no_github_main_upload`。
- Boundary includes No GitHub main upload, No Stage 2 work, No raw/private read, No direct writeback, No proposal write, No agent apply and No build/deploy/app install。

## 76. v1.1.7 Stage 1 Phase 1.4 Topic Classification Detail

状态：`phase_1_4_topic_classification_detail_completed_pending_stage1_review`。

验收 ID：`ACC-MA-V117-S1P04`。

模型参数：

- Topic Classification 只从已筛选的 redacted atlas nodes、graph edges、Next Action map 和 Level Asset map 派生。
- ThemeDetailPanel 是只读解释层；任何主题、优先级、状态或 proposal 调整仍必须进入后续 Stage 2 proposal-only editor。
- `topic_state` 支持 dominant、rising、declining、emerging、conflict、black_hole、stale。
- `topic_strength` 使用主题记录数占比、ROI 和 recent_count 派生。
- `matched_reason` 必须说明主题为何重要或为何需要复盘。
- `starfield_handoff` 和 `river_handoff` 必须只传递 derived topic focus，不传 raw/private 数据。

运行时文件：

- `docs/architecture/theme_category_model.md`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/ThemeDetailPanel.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase4.cjs`

参数记录：

- `PARAM-MA-V117-S1P04-001 stage1_phase4_status = phase_1_4_topic_classification_detail_completed_pending_stage1_review`
- `PARAM-MA-V117-S1P04-002 stage1_phase4_required_validator = validate:v1.1.7-stage1-phase4`
- `PARAM-MA-V117-S1P04-003 topic_required_fields = topic_id;topic_label;parent_topic;category;topic_state;topic_strength;trend;roi_score;conflict_score;confidence;record_count;recent_count;representative_record_ids;evidence_refs;matched_reason;linked_asset_ids;linked_action_ids;starfield_handoff;river_handoff;proposal_hint;rollback_hint;proposal_only`
- `PARAM-MA-V117-S1P04-004 topic_classification_sort_weights = strength_weight=0.38;trend_weight=0.24;confidence_weight=0.22;conflict_penalty_weight=0.16`
- `PARAM-MA-V117-S1P04-005 topic_top_limit = Top 10`
- `PARAM-MA-V117-S1P04-006 theme_detail_panel_fields = topic_state;topic_strength;trend;roi_score;conflict_score;confidence;record_count;recent_count;representative_record_ids;evidence_refs;matched_reason;linked_asset_ids;linked_action_ids;starfield_handoff;river_handoff;proposal_hint;rollback_hint;proposal_only`
- `PARAM-MA-V117-S1P04-007 stage1_phase4_deferred_work = Stage 1 review;Stage 2 proposal editor;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

验收信号：

- Topic Classification model contract。
- ThemeDetailPanel runtime component。
- Home Overview Topic Classification cards。
- `validate:v1.1.7-stage1-phase4` 检查模型、实现、样式、记录和改动范围。

# Memory Atlas Project Model Parameters

更新时间：2026-07-01

本文件定义 Memory Atlas 当前真实使用的模型假设、输入、处理方法、输出、公式、函数、阈值、门槛和迭代策略。它不是功能清单，也不是开发记录。功能、交付运行方式、验收标准和历史过程记录见 `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`。

## 0. 文档边界

- 模型：假设、输入、处理、方法、策略、输出、迭代。
- 参数：公式、函数、权重、阈值、等级门槛、筛选规则、失败条件。
- 不属于模型参数：页面功能列表、开发日志、提交记录、部署说明、UI 需求。这些只在影响公式或阈值时引用。
- 真实性规则：没有实现的模型必须标为“当前未实现”，不得为了完整感编造公式。

## 1. 记忆权重模型

模型假设：

- 对未来 agent 最有价值的记忆由三类信号共同决定：记忆层级、重要性、置信度。
- 核心画像应该比一般项目上下文和临时信息有更高基础权重。
- 高置信和高重要信息应更容易被可视化放大和召回。

输入：

- `memory_tier`
- `importance`
- `confidence`

处理方法：

- 先把层级归一到 `核心画像`、`一般`、`临时`。
- 再用加权和计算 `weight_score`。

参数与阈值：

- `TIER_WEIGHT = {"核心画像": 1.0, "一般": 0.66, "临时": 0.28}`
- `IMPORTANCE_WEIGHT = {"高": 1.0, "中": 0.62, "低": 0.32}`
- `CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.72, "low": 0.45}`
- `memory_weight = tier_score * 0.5 + importance_score * 0.3 + confidence_score * 0.2`
- 输出四位小数。

输出：

- `metrics.weight_score`
- 影响 Galaxy/Graph 节点大小、ROI 排序、视觉亮度和 agent 召回优先级。

迭代规则：

- 如果用户认为“核心画像”召回过少，优先提高 tier 权重。
- 如果低置信内容噪声过高，优先降低 low confidence 权重或增加人工确认门槛。

## 2. ROI Leverage 模型

模型假设：

- 一条记忆的 ROI 不只取决于重要性，还取决于是否是决策、是否敏感、是否过期。
- 敏感信息可以存在于数据库体系中，但公开可视化与 GitHub 备份必须降低其直接可用性。

输入：

- `memory_weight`
- `category`
- `sensitivity`
- `validity`
- `date`

处理方法：

- 按日期计算新鲜度。
- 决策类增加杠杆分。
- 敏感或 secret 信息扣分。

参数与阈值：

- `recency_days = today - date`
- `sensitivity_penalty = 0.35` 当 `sensitivity in {"sensitive", "secret"}`，否则 `0.1`
- `decision_impact = 1` 当 `category == "decision"`，否则 `0`
- `leverage_score = max(0, memory_weight + decision_impact * 0.15 - sensitivity_penalty)`
- 过期状态：
  - `validity == "临时"` 且 `recency_days > 30` => `stale_short_term`
  - `recency_days > 180` => `needs_review`
  - 其他有日期记录 => `current`
  - 无日期 => `unknown`

输出：

- `metrics.roi.leverage_score`
- `metrics.roi.staleness_status`
- `metrics.roi.recommended_action`

迭代规则：

- ROI Dashboard 默认按 `leverage_score` 排序。
- 后续可以加入“实际执行收益/时间投入/机会窗口”字段，但当前没有真实执行收益数据，不应伪造。

## 3. 全局活动强度模型 activity_score.v2

模型假设：

- 用户和 agent 的使用强度不能只看对话数；消息、记忆增量、候选、决策、工具调用、错误、中断都代表不同成本和价值信号。
- 工具调用和决策比普通消息更能代表执行投入。

输入：

- `conversation_count`
- `message_count`
- `memory_count`
- `candidate_count`
- `decision_count`
- `tool_call_count`
- `error_event_count`
- `abort_count`

处理方法：

- 对每个日/周/月桶聚合计数后计算活动分。
- 再按该周期内最大分归一成 0-5 等级。

参数与阈值：

- `activity_score = conversation_count * 5 + message_count + memory_count * 3 + candidate_count + decision_count * 4 + tool_call_count * 2 + error_event_count + abort_count * 2`
- `activity_level = 0` 当 `score <= 0` 或 `max_score <= 0`
- 否则 `activity_level = ceil(score / max_score * 5)`，限制在 1-5。
- 分位数：
  - `p50 = ceil(0.50 * n) - 1`
  - `p75 = ceil(0.75 * n) - 1`
  - `p90 = ceil(0.90 * n) - 1`
  - `p95 = ceil(0.95 * n) - 1`

输出：

- `contribution.daily/weekly/monthly`
- Contribution Grid 的热度、增量分析、时间尺度对比。

迭代规则：

- 如果工具调用过多但实际产出低，应新增“有效交付完成数”而不是继续提高工具调用权重。
- 如果错误/中断代表返工成本，可以从正向活动分拆成“摩擦分”。

## 4. Codex 本地行为活动模型

模型假设：

- Codex 行为分析只能使用脱敏摘要，不直接上传原始 transcript、绝对路径、secrets。
- 一个 session 的强度由消息数、用户消息、工具调用、主题覆盖和错误事件共同表示。

输入：

- 本机 Codex session jsonl 摘要。
- `message_count`
- `user_message_count`
- `tool_call_count`
- `topic_labels`
- `error_event_count`

处理方法：

- 解析本机 Codex 历史，生成 redacted session manifest。
- 主题和偏好信号只保存标签与计数。

参数与阈值：

- `session_activity_score = message_count + user_message_count * 2 + tool_call_count * 3 + len(topic_labels) * 4 + error_event_count * 2`
- Codex 日聚合 `activity_level = ceil(score * 5 / max_score)`，限制在 1-5。
- `backup_policy = redacted_summary_only_no_raw_transcript_no_plaintext_secret`

输出：

- `data/processed/codex/codex_activity_snapshot.json`
- `data/derived/agent_context/agent_context_pack.json`
- Memory Atlas 的 Codex 数据源视图、行为模式、agent personalization。

迭代规则：

- 新增微信/小红书/抖音等来源时，必须先适配 canonical event contract，不能把平台私有字段直接塞进 Atlas。
- 如果要分析真实 productivity，应新增“完成事项/提交/报告/验证通过”信号。

## 5. Contribution Grid 热度映射模型

模型假设：

- 人眼需要看到低频与空值差异，不能让低频都黑掉。
- 高值不能线性压扁低值，使用 log 映射更适合长尾互动数据。

输入：

- `activity_score`
- `max_activity_score`
- `activity_level`

处理方法：

- 先用等级锚点保证 1-5 等级可见。
- 再用 `log1p(score) / log1p(max_score)` 捕捉长尾。
- 最后插值到近黑、冷蓝灰、深海蓝、钴蓝、亮蓝、冰蓝色带。

参数与阈值：

- `heatLevelAnchors = [0, 0.16, 0.34, 0.54, 0.74, 0.93]`
- `rawRatio = score / maxScore`
- `logRatio = log1p(score) / log1p(maxScore)`
- `ratio = max(levelAnchor, logRatio * 0.82 + rawRatio * 0.18)`
- `heatIntensity = clamp(0.04 + ratio * 0.96, min=0.08, max=1)`
- 空值颜色：`#0f1116`
- 色带 stops：`#0f1116 -> #17223a -> #1d3f77 -> #1f6db2 -> #1f9bd1 -> #48c7e8 -> #7ee0f8 -> #a7ecff`

输出：

- 日/周/月/年 Contribution Grid 色值。
- 周/月/年内部趋势段。

迭代规则：

- 如果低频仍不可见，提高 `levelAnchor[1]` 或提高 `logRatio` 权重。
- 如果高频差异不明显，提高 `rawRatio` 权重。

## 6. Timeline 动态窗口模型

模型假设：

- Timeline 的核心价值是看到阶段、突增、转折和事件序列，而不是只看事件列表。
- 真实事件日期是主轴，月份网格只是背景定位。

输入：

- `timeline[]`
- `nodeMap`
- UI 控制：`zoom`、`center`、`cursor`

处理方法：

- 全量事件先按日期排序。
- `zoom` 控制可见时间窗口大小。
- `center` 控制窗口中心。
- `cursor` 控制播放游标，用于区分已经经过与未来窗口事件。
- 密度轨用 48 个全局时间 bin；画布背景密度用 36 个可见窗口 bin。

参数与阈值：

- `zoom` 范围：1 到 8。
- `center` 范围：0 到 1。
- `cursor` 范围：0 到 1。
- `visibleSpan = totalSpan / zoom`
- `cursorMs = windowStartMs + visibleSpan * cursor`
- 可见事件上限：最近 260 个窗口内事件，避免单屏过载。
- 轨道上限：7 条，按层级/分类聚合。
- 事件半径：
  - 高重要：9
  - 决策：8
  - 其他：5

输出：

- `events`
- `eventTicks`
- `densityBands`
- `densityBars`
- `rangeLabel`
- `cursorLabel`
- 可交互 hover/detail/click 同步 Inspector。

迭代规则：

- 如果高连接/高密度阶段仍难读，下一轮增加 brushing、局部展开、阶段聚类摘要。
- 如果事件太多，优先加入按层级/主题的视觉聚合，不退回列表。

## 7. 写回提案版本控制模型

模型假设：

- 前端可以帮助用户形成写回建议，但不能直接修改长期记忆。
- 所有修改必须可审计、可导出、可回滚、可由 agent 二次核验。

输入：

- 当前节点 `node`
- 草稿文本 `draftText`
- 用户填写的原因/证据/回滚说明
- 本地 proposal history

处理方法：

- 新增提案时生成 `proposal_id`、`revision`、`parent_proposal_id`。
- 计算可读 diff。
- 生成 agent apply 指引。
- 回滚时新增 `rollback_to_version` 提案，而不是直接覆盖旧版本。

参数与阈值：

- `revision = latest.revision + 1`
- `rollback_unit = policy.rollback_unit || "per_memory_version"`
- `length_delta = len(proposed_text) - len(base_text)`
- `changed_segments = added_readable_segments + removed_readable_segments`
- 禁止 payload：`plaintext secrets`、`raw conversation text`、`record hashes`、`local absolute paths`
- 状态固定为 `draft_pending_agent_apply`

输出：

- 本地 `memory-atlas.writeback.proposals.v1`
- 最新 proposal JSON
- 版本链 JSON
- rollback proposal JSON

迭代规则：

- 后续 agent apply 时必须重新读取数据库、冲突检测、写 proposal history、git commit。
- 若 active memory 已有更新版本，必须先生成冲突报告，不能静默覆盖。

## 8. Shared State Store 状态模型

review_status: `stage_6_whole_stage_review_passed`

模型假设：

- Memory Atlas 的各板块不应各自重复维护 selection、filter、time range
  和 focus 状态；否则 Home、Galaxy、Timeline、Inspector、ROI Dashboard 会
  产生不一致焦点。
- 全局状态必须小而显式，只记录可解释 identity 和 filter schema，不保存
  raw transcript、secret、完整数据库对象或不可回滚写入。
- 视图只能通过显式 action 更新 shared state，派生视图读取 state，避免双向
  effect 循环。

输入：

- `activeView`
- selected `AtlasNode`
- Timeline brush `SharedTimelineTimeRangeSelection`
- Atlas filter fields: `query`, `source`, `tier`, `category`, `theme`
- ROI filter schema field: `roi`
- contribution period identity and summary metrics

处理方法：

- `sharedAtlasReducer` 接收 `select_node`、`select_time_range`、
  `clear_time_range`、`set_filters`、`set_filter`、`clear_filter`、
  `reset_filters`、`select_contribution_period`、`switch_view` 和
  `clear_focus` action。
- `selectionFromNode` 只提取 `nodeId`、`nodeKind`、`clusterId`、`recordId`
  和当前 `timeRangeId`。
- `focusFromSelection` 把同一 `SharedAtlasFocusTarget` 投射给 Home、Galaxy、
  Timeline、Inspector 和 ROI Dashboard。
- `clearSharedAtlasFilter` 只清理指定 filter；例如清理 `source` 不会同时清理
  `tier`、`category` 或 `theme`。

参数与失败条件：

- `schema_version = memory_atlas_shared_state.v1`
- `loopGuard.mode = single-dispatch-reducer`
- `loopGuard.derivedViews = read-only`
- 默认 Atlas filters：
  - `query = ""`
  - `source = "all"`
  - `tier = "all"`
  - `category = "all"`
  - `theme = "all"`
- 默认 ROI filter：`roi = "all"`
- 失败条件：
  - action 后 `focus.home`、`focus.galaxy`、`focus.timeline`、
    `focus.inspector`、`focus.roiDashboard` 不一致。
  - 清理单个 filter 改动了其它 filter 或旧 state object。
  - UI 直接写 active memory，而不是生成 proposal。

输出：

- `SharedAtlasState`
- `SharedAtlasSelectionState`
- `SharedAtlasFilterState`
- `SharedAtlasFocusState`
- `sync.revision`、`sync.updatedBy`、`sync.lastAction`
- Home、Galaxy、Timeline、Inspector 的 `data-shared-*` contract。

迭代规则：

- Stage 6 整体复审已确认 shared-state schema、sync actions、filter clearing
  和 cross-view focus contract 均通过；后续变更必须继续跑
  `validate:stage6`。
- Stage 6.2 可以从 shared state 读取 Inspector explanation/proposal
  所需焦点，但不得直接写长期记忆。
- 新增 filter 时先进入 `SharedAtlasFilterState` 和 validator，再接 UI。
- 如果后续出现跨板块循环更新，优先收紧 reducer action，而不是增加组件内
  effect 同步。

## 9. 情绪分模型

状态：当前未实现。

原因：

- 当前 Memory Atlas 已有活动强度、ROI、记忆层级、重要性、置信度、错误/中断等信号，但没有真实情绪标注、情感词典校准、人工样本、跨语种语义校验，也没有把情绪分写入数据 schema。
- 因此不能声称已经有 emotion score。

未来可行输入：

- 用户消息语气信号。
- 重复纠错/不满表达。
- 中断、返工、否定反馈。
- 高压任务词。
- 明确满意/不满意反馈。

未来建议公式草案：

- 先做 `friction_score`，不要直接做情绪判断。
- `friction_score = correction_count * 3 + repeated_requirement_count * 2 + abort_count * 2 + error_event_count + explicit_negative_feedback * 4`
- 需要人工验证样本后才能进入正式模型参数。

## 10. 质量门槛模型

模型假设：

- Memory Atlas 是决策与记忆平台，质量不能只靠 build 成功。
- 需要同时检查数据安全、视觉密度、中文界面、运行缓存、Cloudflare readiness、本地 app runtime。

输入：

- 源码
- `memory_atlas.json`
- docs
- build output
- local app bundle

处理方法：

- `audit_memory_atlas_release.py` 检查发布目录安全。
- `audit_memory_atlas_visual_acceptance.py` 检查视觉和交互契约。
- `audit_memory_atlas_acceptance.py` 汇总数据、源码、文档、Cloudflare、本地 app。

参数与阈值：

- 所有导航板块默认可视化程度目标：80%+。
- GitHub 不允许 raw exports、明文 secrets、cookies、sessions、auth files。
- 本地 runtime manifest 必须匹配当前 git HEAD。
- 关闭 tab 后本地 runtime 必须支持 release/shutdown，减少后台线程和缓存占用。

输出：

- PASS/FAIL JSON。
- 失败时停止发布或同步。

迭代规则：

- 每次新增视觉要求都要同步到 audit，防止下一轮退化。
- 每次新增数据源都要先增加 registry/source contract，再增加 UI 选择。

## 11. Inspector 解释与 Proposal 安全模型

review_status: `stage_6_whole_stage_review_passed`

模型假设：

- Inspector 默认层应该先帮助人理解“为什么这条记忆重要、怎么算出来、有哪些脱敏证据”，而不是暴露 agent 内部字段。
- 写回长期记忆是高风险动作；前端只能生成 proposal JSON，不能直接修改 active memory。
- Debug 信息有用，但默认展示会增加认知负担和误用风险，因此必须手动开启。

输入：

- `AtlasNode`
- `edgeCount`
- `SharedAtlasState`
- `source_contract.writeback_policy`
- 用户在写回面板输入的 `action`、`proposed_text`、`reason`

处理方法：

- 默认解释面板只读取派生字段：层级、分类、日期、时效、连接数、来源、ROI、共享焦点。
- `node.statement` 低敏数据库摘要只放入 Debug / Agent Inspector，默认关闭。
- proposal preview 和保存逻辑共用 `buildWritebackProposalDraft`，避免 preview 与真实本地提案结构漂移。
- 保存提案只写入浏览器本地 proposal queue，不写 active memory 文件。

参数与公式：

- `memory_weight = tier_score * 0.5 + importance_score * 0.3 + confidence_score * 0.2`
- `TIER_WEIGHT = {"核心画像": 1.0, "一般": 0.66, "临时": 0.28}`
- `IMPORTANCE_WEIGHT = {"高": 1.0, "中": 0.62, "低": 0.32}`
- `CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.72, "low": 0.45}`
- `decision_impact = 1` 当 `category == "decision"`，否则 `0`
- `sensitivity_penalty = 0.35` 当 `visual.sensitive == true` 或分类属于 `temporary_or_sensitive` / `security_boundary`，否则 `0.1`
- `leverage_score = max(0, memory_weight + decision_impact * 0.15 - sensitivity_penalty)`
- proposal safety 必须保持：
  - `direct_frontend_mutation_of_active_memory = false`
  - `requires_conflict_check = true`
  - `requires_agent_or_human_apply = true`

输出：

- Inspector explanation panel：人类解释、公式、参数、脱敏证据、安全说明。
- Debug / Agent Inspector：agent memory/meta 字段、低敏数据库摘要、结构化字段。
- Writeback proposal JSON：`schema_version`、`proposal_id`、`target_ref`、`payload`、`diff`、`version`、`review`、`safety`。

失败条件：

- 默认 Inspector 展示 raw transcript、secret、cookie、session 或本地绝对路径。
- Debug / Agent Inspector 默认打开。
- 前端直接修改 active memory 或 proposal safety 字段不是 fail-closed。
- proposal preview 和保存的 proposal 结构不一致。

迭代规则：

- Stage 6 整体复审已确认 Inspector explanation、Debug separation、proposal
  JSON preview 和 fail-closed writeback safety 均通过。
- Stage 6 整体复审必须同时跑 `validate:shared-state` 和 `validate:inspector-proposal`。
- 后续 agent apply CLI 必须重新读库、做冲突检查、写 history、生成 git 回滚点；不能复用前端状态直接写库。
- 如果默认解释面板过密，优先折叠公式细节，不把 raw 摘要移回默认层。

## 12. Stage 7.1 视觉验收模型

状态：Stage 7.1 已实现，Stage 7 整体复审已完成。

模型假设：

- Memory Atlas 的关键视觉面板不能只靠源码字符串验收；Galaxy 和 Memory River
  必须在真实浏览器中渲染、截图，并通过非空或结构质量 gate。
- Galaxy 是 WebGL canvas，适合用 bounded pixel signal 验证不是空白、纯黑、
  fallback-only 或静态点云。
- Memory River 是 SVG 视觉系统，适合用截图文件和 DOM 结构验证 Macro / Meso /
  Micro 河道、证据层、marker 和密度上下文没有退化成静态列表。

输入：

- Vite production preview output: `apps/memory-atlas/dist`
- Playwright Chromium 页面
- `window.__memoryAtlasGalaxySignal()`
- `.memory-river-canvas` DOM contract
- Browser screenshots

处理方法：

- `validate:stage7-visual` 启动 `vite preview --host 127.0.0.1 --port 4177
  --strictPort`。
- 使用 Playwright 打开页面，等待 `networkidle` 后依次切换到 Galaxy 和 Timeline。
- Galaxy：读取 bounded pixel signal，捕获 `stage7-galaxy-desktop.png`。
- Memory River：检查 SVG contract，捕获 `stage7-memory-river-desktop.png`。
- 验证结束后关闭 preview server，并确认 4177 不再响应。

参数与阈值：

- Galaxy canvas signal:
  - `lit > 100`
  - `alpha > 100`
  - `max > 42`
  - `width > 100`
  - `height > 100`
  - `rendererMode == "memory-starfield"`
  - `fallbackMode != "legacy"`
  - `points > 0`
  - `triangles > 0`
  - `terrainFeatureCount > 0`
  - `flowFieldStrength > 0`
- Screenshot file:
  - `stage7-galaxy-desktop.png` size `> 20000` bytes
  - `stage7-memory-river-desktop.png` size `> 20000` bytes
- Memory River structure:
  - `data-utc-time-scale == "true"`
  - Macro / Meso / Micro level labels all present
  - `laneFlows >= 3`
  - `laneLabels >= 3`
  - evidence layers include `black-hole-lifecycle`, `proto-star-lifecycle`,
    `stale-deprecated`
  - `evidenceSegments > 0`
  - black-hole lifecycle band contract is present through `black-hole-lifecycle`
  - `protoStarMarkers > 0`
  - `totalMarkers >= 3`
  - `densityBands >= 24`

输出：

- PASS/FAIL JSON
- `outputDir`
- Galaxy screenshot path and signal object
- Memory River screenshot path and structure object
- server cleanup result through 4177 port close assertion

失败条件：

- Browser console/page error appears during visual validation.
- Galaxy pixel signal is blank, too dark, legacy fallback, or missing terrain /
  flow-field evidence.
- Memory River lacks Macro / Meso / Micro, evidence layers, opportunity markers, density
  context, or screenshot proof.
- Preview server remains alive on 4177 after validation.

迭代规则：

- Stage 7.2 may add FPS and adaptive quality metrics, but must not weaken
  Stage 7.1 non-empty visual gates.
- Stage 7.3 may add privacy/accessibility checks, but must keep screenshots
  redacted and avoid browser profile/cookie/session capture.

## 13. Stage 7.2 性能验收模型

状态：Stage 7.2 已实现，Stage 7 整体复审已完成。

模型假设：

- FPS 验收必须来自真实浏览器 production preview，不用静态源码推断。
- 高质量和中质量需要明确阈值；低质量的核心验收是不空白、不退回 legacy。
- 自适应质量不能剥夺人工回滚路径；手动选择 `high` / `mid` / `low`
  会关闭自动质量，`Auto` toggle 可重新启用。
- 资源清理验收不只看 preview server 退出，还要看 Galaxy unmount 的 RAF、
  WebGL renderer、Worker 和 AudioContext lifecycle contract。

输入：

- `window.__memoryAtlasGalaxySignal()`
- `window.__memoryAtlasGalaxyLifecycle`
- `.galaxy-performance-overlay`
- Vite production preview output: `apps/memory-atlas/dist`
- Playwright Chromium 页面

处理方法：

- `validate:stage7-performance` 启动 `vite preview --host 127.0.0.1
  --port 4177 --strictPort`。
- 进入 Galaxy 并切到 Analysis mode，等待 `.galaxy-performance-overlay` 和
  `__memoryAtlasGalaxySignal()` 的 FPS sample。
- 分别切换 `high`、`mid`、`low` quality；manual quality selection 作为
  fallback/rollback path。
- 重新启用 `Auto`，确认 adaptive quality 可以恢复。
- 切到 Timeline 触发 Galaxy unmount，读取 lifecycle signal。
- 关闭 preview server 并确认 4177 不再响应。

参数与阈值：

- FPS:
  - high quality: `fps >= 45`
  - mid quality: `fps >= 30`
  - sample window: `>= 0.8s`
  - `renderTicks > 8`
- Quality:
  - default adaptive quality starts at `mid`
  - low quality `fallbackMode == "low-quality"`
  - low quality still requires `lit > 100`, `alpha > 100`, `points > 0`,
    `triangles > 0`
- Adaptive quality:
  - warmup `2400ms`
  - cooldown `4200ms`
  - high below `45 FPS` may downgrade to `mid`
  - mid below `30 FPS` may downgrade to `low`
  - low at or above `45 FPS` may upgrade to `mid`
  - mid at or above `52 FPS` may upgrade to `high`
- Cleanup:
  - `activeRaf == false`
  - `rafCancelled == true`
  - `rendererDisposed == true`
  - `webglContextLost == true`
  - `workersClosed == true`
  - `audioContextClosed == true`
  - `__memoryAtlasGalaxySignal` removed after unmount

输出：

- PASS/FAIL JSON
- `stage7-performance-report.json`
- high/mid/low signal snapshots
- adaptive overlay contract snapshot
- cleanup lifecycle snapshot
- server cleanup result through 4177 port close assertion

失败条件：

- high or mid quality FPS is below threshold.
- FPS overlay or adaptive data contract is missing.
- low quality is blank, missing render stats, or does not expose low-quality fallback.
- Auto quality cannot resume after manual quality selection.
- Galaxy unmount leaves RAF signal, renderer, WebGL context, Worker/Audio contract,
  or `__memoryAtlasGalaxySignal` active.
- Browser console/page errors appear during performance validation.
- Preview server remains alive on 4177 after validation.

迭代规则：

- Stage 7.2 must keep Stage 7.1 visual gates passing.
- Stage 7.3 may add privacy/accessibility checks but must not relax the FPS,
  adaptive quality or cleanup lifecycle thresholds.

## 14. Stage 7.3 隐私与无障碍验收模型

状态：Stage 7.3 已实现，Stage 7 整体复审已完成。

模型假设：

- 发布产物只能作为 public redacted read-only visualization 使用；不能把
  raw/private/cookie/session/secret 或本机绝对路径带入 `dist`。
- reduced motion 必须使用浏览器偏好验证，不能只靠 UI 文案判断。
- 伪触感和音频是用户显式 opt-in 的反馈；默认必须保持安静，不调用
  `navigator.vibrate` 或 `AudioContext`。
- Stage 7.3 只增加验收 gate 和安全 DOM contract，不改变写回、数据摄取或
  Cloudflare 发布边界。

输入：

- `apps/memory-atlas/dist`
- `apps/memory-atlas/dist/memory_atlas.json`
- `scripts/audit_memory_atlas_release.py`
- Playwright Chromium 页面
- `prefers-reduced-motion` browser media emulation
- Timeline feedback DOM contract

处理方法：

- `validate:stage7-privacy-accessibility` 先运行 release privacy audit。
- 扫描 publish artifact，确认无 sourcemap，且 `memory_atlas.json` 的
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 启动 Vite production preview。
- 用 `reducedMotion: "reduce"` 的 browser context 打开 Timeline，确认
  Reduced Motion 默认开启、播放按钮禁用、Memory River transition 被关闭。
- 用 `reducedMotion: "no-preference"` 的 browser context 清空本地反馈偏好，
  确认伪触感和音频默认关闭。
- 安装 vibration / AudioContext spy，点击 Memory River marker，确认默认
  不调用 vibration 或 AudioContext。
- 关闭 preview server 并确认 4177 不再响应。

参数与阈值：

- Privacy artifact:
  - `memory_atlas.json` exists
  - `schema_version == "memory_atlas.v1"`
  - `source_contract.mode == "public_redacted_read_only_visualization"`
  - `direct_frontend_mutation_of_active_memory == false`
  - no `.map` files in `dist`
  - forbidden text patterns absent:
    - `PRIVATE CORE DETAIL`
    - `SECRET DETAIL`
    - `sk-*`
    - private key headers
    - `OpenAI-export.zip`
    - `chatgpt_memory_vault`
    - `.local_keys`
    - `/Users/<name>/`
- Reduced motion:
  - browser `matchMedia("(prefers-reduced-motion: reduce)").matches == true`
  - Reduced Motion checkbox checked
  - `data-reduced-motion == "true"`
  - `data-feedback-reduced-motion == "true"`
  - play button disabled
  - Memory River lane/marker transition duration `0s`
- Feedback defaults:
  - pseudo-haptic checkbox unchecked
  - audio checkbox unchecked
  - `data-feedback-pseudo-haptic == "disabled"`
  - `data-feedback-audio == "disabled"`
  - `data-feedback-defaults == "silent-by-default"`
  - marker click leaves vibration spy count `0`
  - marker click leaves AudioContext spy count `0`

输出：

- PASS/FAIL JSON
- `stage7-privacy-accessibility-report.json`
- release privacy audit result
- publish artifact privacy summary
- reduced-motion browser contract snapshot
- silent feedback default probe snapshot
- server cleanup result through 4177 port close assertion

失败条件：

- Release privacy audit fails.
- Publish artifact contains sourcemaps or forbidden private/secret patterns.
- `memory_atlas.json` does not advertise public redacted read-only mode.
- Browser reduced-motion preference does not enable Reduced Motion behavior.
- Playback remains available under reduced motion.
- Pseudo-haptic or audio feedback defaults on.
- Default marker interaction calls vibration or AudioContext.
- Browser console/page errors appear during validation.
- Preview server remains alive on 4177 after validation.

迭代规则：

- Stage 7.3 must keep Stage 7.1 visual gates and Stage 7.2 performance gates
  passing.
- Stage 7 whole-stage review may start only after 7.1, 7.2 and 7.3 validators
  all pass on the same current branch base.

## 15. Stage 7 整体复审状态

状态：`stage_7_whole_stage_review_passed`。

Stage 7 整体复审已确认：

- 7.1 Visual Acceptance 已通过真实浏览器截图、Galaxy canvas pixel signal 和
  Memory River DOM/screenshot gate。
- 7.2 Performance Acceptance 已通过 FPS overlay、high/mid FPS threshold、
  low-quality non-blank fallback、adaptive quality 和 cleanup lifecycle gate。
- 7.3 Privacy and Accessibility 已通过 release artifact privacy scan、
  reduced motion browser behavior 和 silent feedback default gate。
- `validate:stage7` 会同时检查 phase review docs、package validators、
  visual acceptance hooks、模型参数、changelog 和 delivery record 是否一致。
- 发布产物必须继续满足
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 前端写回边界保持
  `direct_frontend_mutation_of_active_memory == false`。
- Stage 7 整体复审不包含 Cloudflare live deploy、Access policy change、
  raw/private data read、direct active-memory writeback 或 Stage 8 packaging。

下一阶段：

- Stage 8: 打包、部署、回滚。

## 16. Stage 8.1 本地 App 打包验收模型

状态：`stage_8_1_local_app_packaging_passed`。

范围：

- 8.1.1 local build。
- 8.1.2 launcher check。
- 8.1.3 default route check。

验收门槛：

- `validate:stage8-local-app` 必须通过。
- Production build 必须生成 `dist/index.html` 与 `dist/memory_atlas.json`。
- Installer 必须能在临时目录创建 executable `Memory Atlas.app` bundle，
  `Info.plist`、`MemoryAtlas.icns` 和 `PkgInfo` 必须存在。
- 无 Pillow 环境下必须使用标准库 `.icns` fallback，不得阻塞
  `python3 scripts/install_memory_atlas_app.py`。
- Launcher 必须只打开 `launching.html` 状态页，不直接打开第二个 `$URL`
  窗口；状态页在 ready 后跳转到本地 app。
- Launcher 必须支持 npm-first / pnpm-fallback dependency install and build，
  并在 Finder 启动环境中注入 Codex bundled runtime PATH（存在时）。
- pnpm `.pnpm/.../node_modules/lightningcss` dependency layout 必须被视为
  ready。
- 本地 runtime 必须写入 `memory_atlas_build.json`，且 `git_commit` 匹配当前
  git HEAD。
- Managed server 必须支持 `MEMORY_ATLAS_PID_FILE`，在 release、idle 或 TTL
  正常退出时清理自己的 pid file。
- 默认 production route 必须打开 `记忆总览`，`data-view="home"` 且
  `.home-overview-view` 可见。
- 关闭验证后 4177 不得留下 listener。

已验证：

- `python3 -m unittest OpenAIDatabase.tests.test_memory_atlas_launcher -q` PASS。
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:stage8-local-app`
  PASS，默认首页 screenshot `504546` bytes。
- `python3 OpenAIDatabase/scripts/install_memory_atlas_app.py --repo-root OpenAIDatabase`
  PASS，已安装 Downloads 与 `/Applications` app bundle。
- `python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --repo-root OpenAIDatabase --publish-dir "$HOME/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime" --require-local-apps`
  PASS。
- Runtime manifest 的具体 `git_commit` 不在模型参数中硬编码；exact
  commit is validated by audit, not hard-coded。以
  `audit_memory_atlas_acceptance.py --require-local-apps` 与
  `memory_atlas_build.json` 对当前 git HEAD 的实时比对为准。

边界：

- Stage 8.1 不包含 Stage 8.2 Release Safety。
- Stage 8.1 不包含 Cloudflare live deploy 或 Access policy change。
- Stage 8.1 不读取 raw/private/cookie/session/secret 数据。
- Stage 8.1 不新增 direct active-memory writeback。

下一阶段：

- Stage 8.2 Release Safety。

## 17. Stage 8.2 Release Safety 验收模型

状态：`stage_8_2_release_safety_passed`。

范围：

- 8.2.1 Feature Flag Rollback。
- 8.2.2 Acceptance Audit。
- 8.2.3 Release Notes。

验收门槛：

- `validate:stage8-release-safety` 必须通过。
- Production build 必须生成 `dist/index.html` 与 `dist/memory_atlas.json`。
- `audit_memory_atlas_release.py` 与 `audit_memory_atlas_acceptance.py` 必须
  对同一 production dist 通过。
- Galaxy 默认 renderer 必须保持 `memory-starfield`，回滚 renderer 必须保持
  `legacy`。
- Timeline 默认 renderer 必须保持 `memory-river`，回滚 renderer 必须保持
  `legacy`。
- URL rollback 必须支持 `?galaxyRenderer=legacy` 与
  `?timelineRenderer=legacy`。
- localStorage rollback/restore 必须使用
  `memory-atlas.galaxy-renderer` 与 `memory-atlas.timeline-renderer`。
- 环境变量 rollback contract 必须保留
  `VITE_MEMORY_ATLAS_GALAXY_RENDERER` 与
  `VITE_MEMORY_ATLAS_TIMELINE_RENDERER`。
- 真实浏览器必须验证 legacy rollback、新 renderer restore、localStorage
  persistence、screenshot 非空、console/network 无 actionable error。
- 验证结束后 4177 不得留下 listener。

边界：

- Stage 8.2 不包含 Stage 8 whole-stage review。
- Stage 8.2 不包含 Cloudflare live deploy 或 Access policy change。
- Stage 8.2 不读取 raw/private/cookie/session/secret 数据。
- Stage 8.2 不新增 direct active-memory writeback；前端写回仍为
  proposal-only。
- Stage 8.2 不上传 GitHub main。

下一阶段：

- Stage 8 整体复审。

## 18. Stage 8 整体复审状态

状态：`stage_8_whole_stage_review_passed`。

Stage 8 整体复审已确认：

- 8.1 Local App Packaging 已通过 production build、临时 app bundle、
  launcher single-window contract、default `记忆总览` route 和 pid cleanup
  gate。
- 8.2 Release Safety 已通过 Galaxy/Timeline legacy rollback、new renderer
  restore、localStorage persistence、release audit、overall acceptance audit
  和 release notes gate。
- `validate:stage8` 会同时运行 `validate:stage8-local-app`、
  `validate:stage8-release-safety`、offline Cloudflare Pages + Access
  preflight、Stage 8 文档一致性检查和 4177 cleanup assertion。
- offline Cloudflare Pages + Access preflight 只验证 templates、runbook、
  wrangler config 和 release-safe dist，不执行 live deploy。
- 发布产物必须继续满足
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 前端写回边界保持
  `direct_frontend_mutation_of_active_memory == false`。

边界：

- Stage 8 整体复审不包含 Cloudflare live deploy 或 Access policy change。
- Stage 8 整体复审不读取 raw/private/cookie/session/secret 数据。
- Stage 8 整体复审不新增 direct active-memory writeback。
- GitHub main 上传必须在复审通过后再做 final fast-forward 检查。

下一阶段：

- GitHub main 上传后进入 Stage 9 后续增强迭代。

## 19. Stage 9.1 Obsidian Graph E Iteration 验收模型

状态：`stage_9_1_obsidian_graph_iteration_passed`。

范围：

- 9.1.1 局部图谱优化。
- 9.1.2 标签阈值优化。
- 9.1.3 与记忆星系同步。

验收门槛：

- `validate:stage9-obsidian` 必须通过。
- Obsidian Graph 默认仍可进入 global graph，且默认 label density 不得挤满
  全图。
- Local graph 必须有 bounded neighborhood budget，当前阈值为
  `LOCAL_GRAPH_PRIMARY_NODE_LIMIT = 34`、
  `LOCAL_GRAPH_SECONDARY_NODE_LIMIT = 52`、
  `LOCAL_GRAPH_CLUSTER_MEMBER_LIMIT = 42`、
  `LOCAL_GRAPH_MAX_NODES = 96`。
- Local Graph Budget 必须暴露 primary、secondary、hidden local neighbor 和
  label budget evidence。
- 标签规则必须区分 selected、hover、local-neighbor、zoom-priority、hub 和
  hidden。
- Galaxy shared focus 必须通过 `sharedState.focus` 传入 Obsidian Graph；
  `sourceView == "galaxy"` 且存在 cluster 时，Obsidian 必须显示 bounded local
  cluster graph。
- 验证结束后 4177 不得留下 listener。

边界：

- Stage 9.1 不包含 Stage 9.2 Visual Semantics Enrichment。
- Stage 9.1 不包含 Stage 9 whole-stage review。
- Stage 9.1 不读取 raw/private/cookie/session/secret 数据。
- Stage 9.1 不新增 direct active-memory writeback。
- Stage 9.1 不上传 GitHub main。

下一阶段：

- Stage 9.2 Visual Semantics Enrichment。

## 20. Stage 9.2 Visual Semantics Enrichment 验收模型

状态：`stage_9_2_visual_semantics_enrichment_passed`。

范围：

- 9.2.1 Memory Terrain v2。
- 9.2.2 Memory Weather v2。
- 9.2.3 ROI Visual Gradient。

验收门槛：

- `validate:stage9-visual-semantics` 必须通过。
- Home 必须显示 Memory Weather v2，并暴露 stability、momentum、risk、
  opportunity、confidence 和 signal list；状态判断只能来自现有
  `DeltaStats`、topic rows、black-hole/proto-star 节点和 redacted derived
  nodes。
- Galaxy `memory-starfield` 的 Analysis Mode 必须显示
  `data-memory-terrain-v2="analysis-only"`、terrain semantic role、coverage、
  intensity、sample evidence 和 ROI Capability Gradient；Presentation Mode
  不承载这些分析面板。
- Memory River 必须显示 `data-roi-gradient="capability-growth"`，并把
  `leverage_score` 与 capability-growth event 合成 12 段 ROI gradient band。
- 浏览器验证必须覆盖 Home、Galaxy、Timeline 三面，且 actionable
  console/network error 为 0；`/__memory_atlas_heartbeat` 本地运行探针 404
  不计入资源失败。
- 验证结束后 4177 不得留下 listener。

边界：

- Stage 9.2 不包含 Stage 9 whole-stage review。
- Stage 9.2 不上传 GitHub main。
- Stage 9.2 不部署 Cloudflare，不修改 Access policy。
- Stage 9.2 不读取 raw/private/cookie/session/secret 数据。
- Stage 9.2 不新增 direct active-memory writeback。

下一阶段：

- Stage 9 整体复审与修复；通过后再做 GitHub main 上传。

## 21. Stage 9 整体复审状态

状态：`stage_9_whole_stage_review_passed`。

Stage 9 整体复审已确认：

- 9.1 Obsidian Graph E Iteration 已通过 `validate:stage9-obsidian`：
  bounded local graph、label rules、Galaxy shared-focus sync 和 4177 cleanup
  均通过。
- 9.2 Visual Semantics Enrichment 已通过
  `validate:stage9-visual-semantics`：Memory Weather v2、Memory Terrain v2、
  Galaxy ROI gradient、Memory River ROI/capability gradient、browser
  console/network 和 4177 cleanup 均通过。
- `validate:stage9` 会同时运行 Stage 9.1 validator、Stage 9.2 validator、
  visual acceptance、release audit、overall acceptance、Stage 9 文档一致性检查
  和 4177 cleanup assertion。
- `audit_memory_atlas_visual_acceptance.py` 必须继续包含
  `stage9_1_obsidian_graph_iteration_ready` 和
  `stage9_2_visual_semantics_enrichment_ready`。
- 发布产物必须继续满足
  `source_contract.mode == "public_redacted_read_only_visualization"`。
- 前端写回边界保持
  `direct_frontend_mutation_of_active_memory == false`。

边界：

- Stage 9 整体复审不包含 Cloudflare live deploy 或 Access policy change。
- Stage 9 整体复审不读取 raw/private/cookie/session/secret 数据。
- Stage 9 整体复审不新增 direct active-memory writeback。
- Stage 9 整体复审不进入 Stage 10。
- Stage 9 整体复审通过后必须先进入整项目复审与修复。
- GitHub main 上传必须在整项目复审通过后再做 final fast-forward 检查。

下一阶段：

- 整项目复审与修复；通过后再做 GitHub main 上传并关闭 Stage 9 交付。

## 22. Part 1 Stage 0 复审门槛

状态：`part_1_stage_0_review_passed`。

范围：

- Phase 0.1 Scope & Naming Freeze。
- Phase 0.2 Memory Overview / Memory Starfield / Memory River / Universe State
  contracts。
- Phase 0.3 isolated spike scaffold continuity。

验收门槛：

- `validate:part1-stage0` 必须通过。
- Phase 0.1 必须同时包含首批模块、中文命名、默认入口、隐私边界、不改
  route/production UI 和 rollback。
- Phase 0.2 必须同时覆盖 Memory Weather、Black Hole、Proto-Star、Next
  Actions、Mini Starfield、River Pulse、Presentation / Analysis mode、zoom、
  brush、theme lanes、pseudo-haptic 和 reduced motion。
- Phase 0.3 scaffold continuity 必须保留 isolated directory、README
  contract、redacted fixture boundary、acceptance criteria、rollback，以及
  production source 不引用 spike 目录的证据。
- 参数文件必须保留 `product_target: Memory Atlas v1.1.5`、schema marker、
  validation hints、`raw_private_data_allowed: false`、
  `plaintext_secrets_allowed: false`、`local_absolute_paths_allowed: false` 和
  `writeback_allowed: false`。

边界：

- 本 Part 1 复审不进入 Part 2。
- 本 Part 1 复审不执行整项目复审。
- 本 Part 1 复审不上传 GitHub main。
- 本 Part 1 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 1 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 1 复审不新增 direct active-memory writeback。

下一阶段：

- 单独执行 Part 2 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 23. Part 2 Stage 1 复审门槛

状态：`part_2_stage_1_review_passed`。

范围：

- Phase 1.1 Memory Starfield Spike。
- Phase 1.2 Memory River Spike。
- Phase 1.3 Universe State Generator Spike。

验收门槛：

- `validate:part2-stage1` 必须通过。
- Phase 1.1 必须保留 isolated runnable Memory Starfield workspace、Three.js
  canvas、默认 10k particle path、LOD、Flow Field、gravitational disk、Black
  Hole、Proto-Star、Memory Terrain、reduced motion、hover card、smoke
  instrumentation 和 false safety flags。
- Phase 1.2 必须保留 isolated runnable Memory River workspace、D3 UTC scale、
  zoom、brush、macro/meso/micro lanes、Black Hole band、Proto-Star marker、
  pseudo-haptic visual feedback、reduced motion、hover card、smoke
  instrumentation 和 false safety/writeback flags。
- Phase 1.3 必须保留 Universe State adapter、score functions、schema/sample
  gate、parameter drift check、`dominant/rising/declining/conflict/black_hole/
  proto_star/stale` 输出、consumer map、proposal-only next actions 和 all-false
  privacy/writeback diagnostics。
- TypeScript/Vite build 必须通过。
- Production source 不得引用 isolated Stage 1 spike/generator workspaces。

参数边界：

- Universe State score weights 必须继续从
  `config/visualization/model_parameters.universe_state.yaml` 镜像并通过 drift
  check。
- `black_hole`、`proto_star`、`stale` weight groups 必须各自保持 sum `1.0`。
- `recommended_next_actions[*].proposal_only == true`。

边界：

- 本 Part 2 复审不进入 Part 3。
- 本 Part 2 复审不执行整项目复审。
- 本 Part 2 复审不上传 GitHub main。
- 本 Part 2 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 2 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 2 复审不新增 direct active-memory writeback。
- 本 Part 2 复审不把 Stage 1 spike/generator 接入 production UI。

下一阶段：

- 单独执行 Part 3 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 24. Part 3 Stage 2 复审门槛

状态：`part_3_stage_2_review_passed`。

范围：

- Phase 2.1 Default Home Integration Plan。
- Phase 2.2 Galaxy Replacement Plan。
- Phase 2.3 Timeline Replacement Plan。

验收门槛：

- `validate:part3-stage2` 必须通过。
- Phase 2.1 必须保留默认首页目标、`记忆总览` 首屏 UX、Memory Weather、
  Black Hole、Proto-Star、Next Actions、Mini Starfield、River Pulse、Stage 3
  implementation sequence、rollback、validation 和 stop conditions。
- Phase 2.2 必须保留 Galaxy replacement wrapper strategy、legacy/new
  feature flag strategy、MemoryStarfieldScene 生产组件边界、data mapping、
  screenshot/FPS/privacy validation、one-flag rollback 和 Stage 4 deferral。
- Phase 2.3 必须保留 Timeline replacement wrapper strategy、legacy/new river
  feature flag strategy、D3 UTC scale、zoom、brush、theme lanes、Black Hole
  band、Proto-Star marker、reduced motion、data mapping、one-flag rollback 和
  Stage 5 deferral。
- Stage 2 historical runtime note 必须存在：Stage 2 review 的 runtime
  assertions 是 2026-06-30 历史状态，不是当前 Stage 3-9 runtime truth。
- TypeScript/Vite build、visual acceptance、overall acceptance 必须通过。

边界：

- 本 Part 3 复审不进入 Part 4。
- 本 Part 3 复审不执行整项目复审。
- 本 Part 3 复审不上传 GitHub main。
- 本 Part 3 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 3 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 3 复审不新增 direct active-memory writeback。
- 本 Part 3 复审不新增 production runtime feature work。

下一阶段：

- 单独执行 Part 4 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 25. Part 4 Stage 3 复审门槛

状态：`part_4_stage_3_review_passed`。

范围：

- Stage 3.1 Home Information Architecture。
- Stage 3.2 Preview Widgets。
- Stage 3 overall review。

验收门槛：

- `validate:part4-stage3` 必须通过。
- Stage 3.1 必须保留 `home` default entry、`记忆总览` nav label、
  HomeOverviewView、Memory Weather、Universe State status cards、Black Hole、
  Proto-Star 和 proposal-only next actions。
- Stage 3.2 必须保留 Mini Starfield、River Pulse、Inspector Deep Link、
  focus-preserving navigation、static SVG/non-WebGL Home preview boundary 和
  visual acceptance hook。
- Stage 3 overall review 必须继续证明 Stage 3.1 / 3.2 均通过、Home 默认页
  验收通过、安全边界通过、4177 cleanup 已验证。
- TypeScript/Vite build、visual acceptance、overall acceptance 必须通过。

边界：

- 本 Part 4 复审不进入 Part 5。
- 本 Part 4 复审不执行整项目复审。
- 本 Part 4 复审不上传 GitHub main。
- 本 Part 4 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 4 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 4 复审不新增 direct active-memory writeback。
- 本 Part 4 复审不新增 production runtime feature work。

下一阶段：

- 单独执行 Part 5 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 26. Part 5 Stage 4 复审门槛

状态：`part_5_stage_4_review_passed`。

范围：

- Stage 4.1 Rendering Integration。
- Stage 4.2 Data Mapping。
- Stage 4.3 Starfield Interaction。
- Stage 4 overall review。

验收门槛：

- `validate:part5-stage4` 必须通过。
- Stage 4.1 必须保留 `memory-starfield` default Galaxy renderer、legacy
  rollback flag、Flow Field trajectories、semantic signal markers、quality
  selector 和 low-quality fallback。
- Stage 4.2 必须保留
  `config/visualization/model_parameters.memory_starfield.yaml` 参数源、
  `memoryStarfieldMass`、`memoryStarfieldParticleAttributes`、
  `memoryTerrainType`、Memory Terrain rendering layer 和 Analysis explanation
  panel。
- Stage 4.3 必须保留 transient hover preview、click focus、capped focused
  neighborhood、Freeze/Resume Flow、Presentation/Analysis mode、formula summary、
  terrain legend 和 Inspector context。
- Stage 4 overall review 必须继续证明 Stage 4.1 / 4.2 / 4.3 均通过、
  desktop/mobile browser evidence 已记录、安全边界通过、4177 cleanup 已验证。
- Starfield mapping validator、Starfield interaction validator、
  TypeScript/Vite build、visual acceptance、overall acceptance 必须通过。

边界：

- 本 Part 5 复审不进入 Part 6。
- 本 Part 5 复审不进入 Stage 5。
- 本 Part 5 复审不执行整项目复审。
- 本 Part 5 复审不上传 GitHub main。
- 本 Part 5 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 5 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 5 复审不新增 direct active-memory writeback。
- 本 Part 5 复审不新增 production runtime feature work。

下一阶段：

- 单独执行 Part 6 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 27. Part 6 Stage 5 复审门槛

状态：`part_6_stage_5_review_passed`。

范围：

- Stage 5.1 River Rendering。
- Stage 5.2 River Interaction。
- Stage 5.3 Evidence Layers。
- Stage 5 overall review。

验收门槛：

- `validate:part6-stage5` 必须通过。
- Stage 5.1 必须保留 `memory-river` default Timeline renderer、legacy
  rollback flag、UTC time scale、Macro/Meso/Micro river lanes、theme/project/
  category lane grouping、black-hole/proto-star/event markers。
- Stage 5.2 必须保留 Pan/Brush interaction、selected range overlay、Home /
  Galaxy / Interaction Lens selected-range sync、hover/click redacted event
  card、click lock、Inspector sync、Reduced Motion、pseudo-haptic/audio off by
  default 的安全反馈边界。
- Stage 5.3 必须保留 black-hole lifecycle band、proto-star lifecycle growth
  path、stale/deprecated cooling fade layer，并继续只使用 redacted derived
  signals。
- Stage 5 overall review 必须继续证明 Stage 5.1 / 5.2 / 5.3 均通过、
  release audit、visual acceptance、overall acceptance、安全边界和 4177 cleanup
  已验证。
- Memory River rendering、interaction、evidence、stage5 validators、
  TypeScript/Vite build、release audit、visual acceptance、overall acceptance
  必须通过。

边界：

- 本 Part 6 复审不进入 Part 7。
- 本 Part 6 复审不进入 Stage 6。
- 本 Part 6 复审不执行整项目复审。
- 本 Part 6 复审不上传 GitHub main。
- 本 Part 6 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 6 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 6 复审不新增 direct active-memory writeback。
- 本 Part 6 复审不新增 production runtime feature work。

下一阶段：

- 单独执行 Part 7 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 28. Part 7 Stage 6 复审门槛

状态：`part_7_stage_6_review_passed`。

范围：

- Stage 6.1 Shared State Store。
- Stage 6.2 Inspector and Proposal。
- Stage 6 overall review。

验收门槛：

- `validate:part7-stage6` 必须通过。
- Stage 6.1 必须保留 `SharedAtlasSelectionState`、
  `SharedAtlasFilterState`、`SharedAtlasFocusState`、`sharedAtlasReducer`、
  `clearSharedAtlasFilter`、single-dispatch loop guard、cross-view shared focus
  和 `data-shared-*` runtime markers。
- Stage 6.2 必须保留 `InspectorExplanationPanel`、
  `buildWritebackProposalDraft`、formula/evidence explanation、`data-raw-display=false`、
  proposal-only JSON、`data-proposal-only=true`、
  `data-active-memory-mutation=false`、default-closed Debug separation 和
  agent/human apply safety fields。
- Stage 6 overall review 必须继续证明 Stage 6.1 / 6.2 均通过、release audit、
  visual acceptance、overall acceptance、data boundary、writeback boundary 和
  4177 cleanup 已验证。
- Shared-state、Inspector/Proposal、stage6 validators、TypeScript/Vite build、
  release audit、visual acceptance、overall acceptance 必须通过。

边界：

- 本 Part 7 复审不进入 Part 8。
- 本 Part 7 复审不进入 Stage 7。
- 本 Part 7 复审不执行整项目复审。
- 本 Part 7 复审不上传 GitHub main。
- 本 Part 7 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 7 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 7 复审不新增 direct active-memory writeback。
- 本 Part 7 复审不新增 production runtime feature work。

下一阶段：

- 单独执行 Part 8 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 29. Part 8 Stage 7 复审门槛

状态：`part_8_stage_7_review_passed`。

范围：

- Stage 7.1 Visual Acceptance。
- Stage 7.2 Performance Acceptance。
- Stage 7.3 Privacy and Accessibility。
- Stage 7 overall review。

验收门槛：

- `validate:part8-stage7` 必须通过。
- Stage 7.1 必须保留真实浏览器截图、Galaxy non-empty pixel signal、
  Memory River 结构验收和 4177 cleanup。
- Stage 7.2 必须保留 FPS overlay、high/mid FPS thresholds、low-quality
  non-blank fallback、adaptive quality resume 和 cleanup lifecycle。
- Stage 7.3 必须保留 release artifact scan、
  `public_redacted_read_only_visualization`、无 sourcemap、reduced motion 和
  silent feedback defaults。
- Stage 7 model parameters must not contain stale whole-stage-incomplete
  status text。
- Stage 7 validators、build、visual acceptance、release audit 和 overall
  acceptance 必须通过。

边界：

- 本 Part 8 复审不进入 Part 9。
- 本 Part 8 复审不进入 Stage 8。
- 本 Part 8 复审不执行整项目复审。
- 本 Part 8 复审不上传 GitHub main。
- 本 Part 8 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 8 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 8 复审不新增 direct active-memory writeback。
- 本 Part 8 复审不新增 production runtime feature work。

下一阶段：

- 单独执行 Part 9 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 30. Part 9 Stage 8 复审门槛

状态：`part_9_stage_8_review_passed`。

范围：

- Stage 8.1 Local App Packaging。
- Stage 8.2 Release Safety。
- Stage 8 overall review。

验收门槛：

- `validate:part9-stage8` 必须通过。
- Stage 8.1 必须保留 production build、临时 app bundle、launcher
  single-window contract、default `记忆总览` route、pid cleanup 和 runtime
  manifest gate。
- Stage 8.2 必须保留 Galaxy / Timeline legacy rollback、new renderer
  restore、localStorage persistence、release audit、overall acceptance audit
  和 release notes gate。
- Stage 8 overall 必须保留 `validate:stage8-local-app`、
  `validate:stage8-release-safety`、`validate:stage8`、offline Cloudflare
  Pages + Access preflight 和 4177 cleanup assertion。
- 本地 `~/Downloads/Memory Atlas.app` 与 `/Applications/Memory Atlas.app`
  必须存在且通过 `--require-local-apps` audit。
- Application Support runtime 的 `memory_atlas_build.json` 必须匹配当前
  git HEAD。
- Stage 8 model parameters must not hard-code an old runtime git commit。
- Stage 8 validators、release audit、overall acceptance 和 local app audit
  必须通过。

边界：

- 本 Part 9 复审不进入 Part 10。
- 本 Part 9 复审不进入 Stage 9。
- 本 Part 9 复审不执行整项目复审。
- 本 Part 9 复审不上传 GitHub main。
- 本 Part 9 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 9 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 9 复审不新增 direct active-memory writeback。
- 本 Part 9 复审不新增 production runtime feature work。

下一阶段：

- 单独执行 Part 10 复审与修复；所有 part-level 复审完成后再进入整项目复审。

## 31. Part 10 Stage 9 复审门槛

状态：`part_10_stage_9_review_passed`。

范围：

- Stage 9.1 Obsidian Graph E Iteration。
- Stage 9.2 Visual Semantics Enrichment。
- Stage 9 overall review。

验收门槛：

- `validate:part10-stage9` 必须通过。
- Stage 9.1 必须保留 bounded local graph、label rules、Galaxy
  shared-focus sync、visual acceptance hooks 和 4177 cleanup。
- Stage 9.2 必须保留 Memory Weather v2、Memory Terrain v2、Galaxy ROI
  gradient、Memory River ROI/capability gradient、browser console/network gate
  和 4177 cleanup。
- Stage 9 overall 必须保留 `validate:stage9-obsidian`、
  `validate:stage9-visual-semantics`、`validate:stage9`、visual acceptance、
  release audit、overall acceptance 和 Stage 9 文档一致性检查。
- Stage 9 review、model parameters、delivery record 和 changelog 必须明确：
  part-level 复审完成后先进入整项目复审，通过后才可 GitHub main 上传。
- Stage 9 validators、release audit、overall acceptance 和 visual acceptance
  必须通过。

边界：

- 本 Part 10 复审不执行整项目复审。
- 本 Part 10 复审不上传 GitHub main。
- 本 Part 10 复审不部署 Cloudflare，不修改 Access policy。
- 本 Part 10 复审不读取 raw/private/cookie/session/secret 数据。
- 本 Part 10 复审不新增 direct active-memory writeback。
- 本 Part 10 复审不新增 production runtime feature work。

下一阶段：

- 进入整项目复审与修复；通过后再做 final remote checks 和 GitHub main 上传。

## 32. Whole-Project 整项目复审门槛

状态：`whole_project_review_passed`。

范围：

- Part 1-10 全部复审 gate。
- Roadmap v2 final acceptance：默认记忆总览、板块说明、建议动作、层级资产、主题分类、proposal-only 调整、搜索/复盘/总结、数据导图、Memory River、Memory Starfield、视觉反退化、raw/private 边界、feature flag rollback。
- Production build、visual acceptance、release audit、overall acceptance、offline Cloudflare Pages + Access preflight。
- OpenAIDatabase Python compile、unittest discover、diff-driven governance sync。
- Canonical remote、GitHub main upload boundary、4177 cleanup。

验收门槛：

- `validate:whole-project` 必须通过。
- Part 1-10 对应 validator 必须全部返回 PASS。
- Production `dist/index.html` 与 `dist/memory_atlas.json` 必须重新生成并通过 release audit。
- Visual acceptance 必须覆盖 roadmap v2 final acceptance 的核心视觉和交互面。
- Overall acceptance 必须确认 redacted derived snapshot、proposal-only writeback、no raw/private data、local app launcher contract、Cloudflare offline preflight 和 CI acceptance gate。
- Full OpenAIDatabase unittest discovery 必须在 Python 3.12 runtime 下通过；系统 Python 3.9 缺 `tomllib` 不能作为 personalization architecture 测试 runtime。
- Diff-driven governance sync 必须对 `origin/main` 变更范围返回 0 errors。
- Application Support runtime 的 `memory_atlas_build.json` 必须在整项目复审 commit 后刷新，并通过 `audit_memory_atlas_acceptance.py --require-local-apps`。
- GitHub main 上传前必须确认 clean tree、final remote ancestry、fast-forward/merge 策略、push target 和 canonical remote。

边界：

- 本整项目复审不上传 GitHub main。
- 本整项目复审不部署 Cloudflare，不修改 Access policy。
- 本整项目复审不读取 raw/private/cookie/session/secret 数据。
- 本整项目复审不新增 direct active-memory writeback。
- 本整项目复审不新增 production runtime feature work。
- 本整项目复审不把 sparse checkout 的 root 全仓治理缺文件当作 Memory Atlas 产品失败；上传前只使用 diff-driven governance sync 作为本项目变更同步证据。

下一阶段：

- 提交整项目复审后刷新本地 app/runtime，并重新运行 `MEMORY_ATLAS_REQUIRE_LOCAL_APPS=1 validate:whole-project`。
- 通过后执行 final remote checks；若分支仍落后 `origin/main`，先处理 rebase/merge，再上传 GitHub main。

## 33. v1.1.6 Stage 0 Phase 0.1 中文文本质量门槛

状态：`phase_0_1_contract_created`。

模型假设：

- 中文可读性是 Memory Atlas 的基础可用性门槛；如果用户看不懂标签、说明、证据或 proposal 边界，后续视觉增强不能证明系统可用。
- 文本质量问题可能来自文件编码、前端渲染、CSS/字体、旧文案或数据快照；不能把不可读问题归因于用户操作。
- 长摘要和解释性内容必须进入展开层或 Inspector，表格和按钮只承载短标签、状态和动作。

输入：

- Markdown 合同与验收文档。
- UI 标签、按钮、卡片标题、状态标签、Inspector 标签。
- 后续浏览器截图与 redacted derived snapshot。

处理方法：

- 先用静态扫描排除替换字符和典型 mojibake。
- 再用产品合同固定中文主标签、状态标签和 proposal-only 文案。
- 后续实现阶段使用桌面、平板和移动视口截图验证重叠、截断、横向撑破和表格长句问题。

参数与门槛：

- 文件编码：`UTF-8`。
- 阻断字符：replacement character `U+FFFD`、Latin-1 残留 `U+00C2/U+00C3`、以及 UTF-8 被错误解码后形成的连续乱码片段。
- 卡片标题建议长度：`<= 18` 个中文字符。
- 卡片摘要建议高度：`<= 2` 行；超过后进入展开层或 Inspector。
- 表格允许内容：短标签、数字、状态、日期、低长度摘要。
- 表格禁止内容：长段落、公式解释、证据全文、多句行动建议、多层级原因。
- 建议截图视口：`1440x900`、`768x1024`、`390x844`。
- proposal-only 提示必须明确：前端只生成调整草案，不直接写入长期记忆。

输出：

- `docs/product/chinese_ui_quality_contract.md`
- `docs/acceptance/chinese_text_audit.md`
- 后续实现 phase 的浏览器截图验收记录。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private 数据。
- 本 phase 不修改核心前端实现或 CSS。

## 34. v1.1.6 Stage 0 Phase 0.2 视觉密度基线门槛

状态：`phase_0_2_contract_created_stage_0_review_passed_pending_upload`。

模型假设：

- Memory Atlas 的核心价值来自可解释视觉结构，不来自列表、表格或普通卡片堆叠。
- 视觉密度是人工验收门槛，用于阻断明显退化；它不替代后续浏览器截图、交互测试和用户判断。
- 视觉主区必须承载状态、结构、时间或行动关系；纯装饰背景不能计入视觉化程度。

输入：

- Roadmap v2 Stage 0 Phase 0.2。
- 记忆总览、记忆星系、记忆时间河、数据导图的产品合同。
- 后续实现 phase 的桌面、平板和移动截图。

处理方法：

- 对四个核心板块分别定义最低视觉化程度。
- 为每个板块定义必备视觉主区、失败条件和后续截图矩阵。
- 使用反退化规则阻断空白画布、列表化、表格化、普通卡片化和无语义装饰化。

参数与门槛：

- `memory_overview_visualization_min = 0.70`
- `memory_starfield_visualization_min = 0.90`
- `memory_river_visualization_min = 0.85`
- `data_map_visualization_min = 0.80`
- `screenshot_viewports = 1440x900;768x1024;390x844`
- `required_pages = 记忆总览;记忆星系;记忆时间河;数据导图`

输出：

- `docs/acceptance/visual_density_baseline.md`
- 后续实现 phase 的截图证据和复审记录。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private 数据。
- 本 phase 不修改核心前端实现、CSS 或 feature flag。

## 35. v1.1.6 Stage 0 整体复审门槛

状态：`stage_0_review_passed_pending_upload`。

模型假设：

- Stage 0 不能只依赖人工描述；上传前必须有固定 review artifact 和 deterministic validator 证明 Phase 0.1 / 0.2 合同、记录和边界一致。
- 本复审只验证 C2 合同层，不证明后续浏览器截图、运行时 UI 或最终视觉实现已完成。

输入：

- `docs/product/chinese_ui_quality_contract.md`
- `docs/acceptance/chinese_text_audit.md`
- `docs/acceptance/visual_density_baseline.md`
- `docs/reviews/memory_atlas_v1_1_6_stage0_review.md`
- Memory Atlas 交付记录、模型参数记录、三文件和 changelog。

处理方法：

- 使用 `validate:v1.1.6-stage0` 检查 Phase 0.1 / 0.2 marker、记录一致性、review 文档、package script 和改动范围。
- 保持 no runtime UI、no CSS、no raw/private、no direct writeback、no Stage 1、no GitHub main upload in review commit。

参数与门槛：

- `stage0_required_validator = validate:v1.1.6-stage0`
- `stage0_required_review_doc = docs/reviews/memory_atlas_v1_1_6_stage0_review.md`
- `stage0_review_status = stage_0_review_passed_pending_upload`
- `stage0_allowed_change_scope = contracts;acceptance;review;records;validator;package_script`

输出：

- Stage 0 review artifact。
- Stage 0 validator。
- 上传前 final remote checks 和 post-integration validation。

边界：

- 本复审不上传 GitHub main。
- 本复审不部署 Cloudflare，不修改 Access policy。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不新增 direct active-memory writeback。
- 本复审不新增 production runtime feature work。

## 36. v1.1.6 Stage 1 Phase 1 记忆总览使用说明门槛

状态：`phase_1_1_contract_created_pending_stage_review`。

模型假设：

- 用户打开 Memory Atlas 后首先需要可理解的系统状态和下一步行动，而不是内部字段或普通 dashboard。
- 记忆总览的可用性取决于“状态、原因、行动、深入入口”能否在同一入口形成闭环。
- 使用说明必须降低理解成本，但不能绕过 Inspector、proposal-only 和隐私边界。

输入：

- `docs/product/memory_overview_usage_contract.md`
- `docs/acceptance/memory_overview_usage_acceptance.md`
- Stage 0 中文 UI 质量合同和视觉密度基线。
- 后续实现 phase 的浏览器截图与 redacted derived snapshot。

处理方法：

- 固定记忆总览作为系统操作中枢的说明结构。
- 将首页信息拆成今日状态、Memory Weather、建议动作、低价值循环、新生机会、层级资产摘要、主题分类摘要、Mini 记忆星系和记忆时间河脉冲。
- 将 Presentation / Analysis、Inspector、Proposal 和后续搜索复盘路径写成用户可执行说明。
- 使用 `validate:v1.1.6-stage1-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S1P01-001 overview_required_role = system_entry_not_welcome_page`
- `PARAM-MA-V116-S1P01-002 required_overview_modules = 今日状态;Memory Weather;建议动作;低价值循环;新生机会;层级资产摘要;主题分类摘要;Mini 记忆星系;记忆时间河脉冲;系统使用说明`
- `PARAM-MA-V116-S1P01-003 required_mode_explanations = Presentation;Analysis`
- `PARAM-MA-V116-S1P01-004 required_explanation_surfaces = Inspector;Proposal`
- `PARAM-MA-V116-S1P01-005 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S1P01-006 stage1_phase1_required_validator = validate:v1.1.6-stage1-phase1`
- `screenshot_viewports = 1440x900;768x1024;390x844`

输出：

- Stage 1 Phase 1 产品合同。
- Stage 1 Phase 1 验收文件。
- Stage 1 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- Stage 2-5 未进入。

## 37. v1.1.6 Stage 1 Phase 2 建议动作明细门槛

状态：`phase_1_2_contract_created_pending_stage_review`。

模型假设：

- 建议动作只有在能够解释原因、收益、成本、紧急度、证据和下一步时才适合用于真实决策。
- 建议动作是 proposal-ready action candidate，不是直接写长期记忆的命令。
- 首页摘要应该短，完整判断应交给展开层和 Inspector。

输入：

- `docs/product/suggested_action_detail_contract.md`
- `docs/acceptance/suggested_action_detail_acceptance.md`
- Stage 1 Phase 1 记忆总览使用说明合同。
- 后续实现 phase 的 redacted evidence、Universe State 和浏览器截图。

处理方法：

- 固定建议动作的必备字段。
- 固定五类动作语义：continue、review、consolidate、explore、defer。
- 固定 Inspector 交接内容和 proposal-only 安全边界。
- 使用 `validate:v1.1.6-stage1-phase2` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S1P02-001 suggested_action_required_fields = action_id;title;action_type;reason;roi_score;effort_cost;urgency;confidence;evidence_count;evidence_refs;source_scope;linked_theme_ids;next_step;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S1P02-002 suggested_action_types = continue;review;consolidate;explore;defer`
- `PARAM-MA-V116-S1P02-003 effort_cost_values = low;medium;high`
- `PARAM-MA-V116-S1P02-004 urgency_values = now;this_week;later;watch`
- `PARAM-MA-V116-S1P02-005 confidence_values = high;medium;low`
- `PARAM-MA-V116-S1P02-006 required_explanation_surface = Inspector`
- `PARAM-MA-V116-S1P02-007 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S1P02-008 stage1_phase2_required_validator = validate:v1.1.6-stage1-phase2`

输出：

- Stage 1 Phase 2 产品合同。
- Stage 1 Phase 2 验收文件。
- Stage 1 Phase 2 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 层级资产和主题分类完整模型未进入。
- Search 2.0、Review / Summary / Iteration 和 Data Map 2.0 未进入。

## 38. v1.1.6 Stage 1 Phase 3 层级资产明细门槛

状态：`phase_1_3_contract_created_pending_stage_review`。

模型假设：

- 层级资产只有在能够说明层级、重要性、优先级、置信度、有效性、证据和下一步时才适合用于真实复盘和行动。
- 层级资产是结构化资产视图，不是原始记录列表，也不是数据库字段直出。
- 层级资产可以提示 proposal-only 调整，但不能由前端直接写长期记忆。

输入：

- `docs/product/tier_asset_detail_contract.md`
- `docs/acceptance/tier_asset_detail_acceptance.md`
- Stage 1 Phase 1 记忆总览使用说明合同。
- Stage 1 Phase 2 建议动作明细合同。
- 后续实现 phase 的 redacted evidence、Universe State 和浏览器截图。

处理方法：

- 固定七类层级资产：core_profile、project、decision、workflow、knowledge、opportunity、stale。
- 固定层级资产的必备字段。
- 固定 Inspector 交接内容和 proposal-only 安全边界。
- 使用 `validate:v1.1.6-stage1-phase3` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S1P03-001 tier_asset_types = core_profile;project;decision;workflow;knowledge;opportunity;stale`
- `PARAM-MA-V116-S1P03-002 tier_asset_required_fields = asset_id;asset_tier;title;summary;importance;priority;confidence;staleness_status;evidence_count;evidence_refs;source_scope;linked_action_ids;recommended_asset_action;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S1P03-003 importance_values = high;medium;low`
- `PARAM-MA-V116-S1P03-004 priority_values = p0;p1;p2;p3;watch`
- `PARAM-MA-V116-S1P03-005 staleness_status_values = current;needs_review;stale;unknown`
- `PARAM-MA-V116-S1P03-006 recommended_asset_actions = keep;review;consolidate;lower_priority;validate;defer`
- `PARAM-MA-V116-S1P03-007 required_explanation_surface = Inspector`
- `PARAM-MA-V116-S1P03-008 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S1P03-009 stage1_phase3_required_validator = validate:v1.1.6-stage1-phase3`

输出：

- Stage 1 Phase 3 产品合同。
- Stage 1 Phase 3 验收文件。
- Stage 1 Phase 3 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 主题分类完整模型未进入。
- Search 2.0、Review / Summary / Iteration 和 Data Map 2.0 未进入。

## 39. v1.1.6 Stage 1 Phase 4 主题分类明细门槛

状态：`phase_1_4_contract_created_pending_stage_review`。

模型假设：

- 主题分类只有在能够说明强度、趋势、置信度、记录数、证据、关联资产、关联动作和下一步时才适合用于真实复盘和行动。
- 主题分类是语义聚合视图，不是 tag 列表，也不是数据库字段直出。
- 主题分类可以提示 proposal-only 调整，但不能由前端直接写长期记忆。

输入：

- `docs/product/topic_classification_detail_contract.md`
- `docs/acceptance/topic_classification_detail_acceptance.md`
- Stage 1 Phase 1 记忆总览使用说明合同。
- Stage 1 Phase 2 建议动作明细合同。
- Stage 1 Phase 3 层级资产明细合同。
- 后续实现 phase 的 redacted evidence、Universe State 和浏览器截图。

处理方法：

- 固定七类主题状态：dominant、rising、declining、emerging、conflict、black_hole、stale。
- 固定主题分类的必备字段。
- 固定跨板块链接、Inspector 交接内容和 proposal-only 安全边界。
- 使用 `validate:v1.1.6-stage1-phase4` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S1P04-001 topic_states = dominant;rising;declining;emerging;conflict;black_hole;stale`
- `PARAM-MA-V116-S1P04-002 topic_required_fields = topic_id;topic_label;topic_state;topic_strength;trend;confidence;record_count;evidence_count;evidence_refs;source_scope;linked_asset_ids;linked_action_ids;matched_reason;recommended_topic_action;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S1P04-003 trend_values = up;down;flat;new;volatile`
- `PARAM-MA-V116-S1P04-004 confidence_values = high;medium;low`
- `PARAM-MA-V116-S1P04-005 recommended_topic_actions = continue;review;consolidate;validate;defer;watch`
- `PARAM-MA-V116-S1P04-006 required_cross_board_links = linked_asset_ids;linked_action_ids;linked_starfield_cluster_id;linked_river_range`
- `PARAM-MA-V116-S1P04-007 required_explanation_surface = Inspector`
- `PARAM-MA-V116-S1P04-008 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S1P04-009 stage1_phase4_required_validator = validate:v1.1.6-stage1-phase4`

输出：

- Stage 1 Phase 4 产品合同。
- Stage 1 Phase 4 验收文件。
- Stage 1 Phase 4 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- Proposal 编辑工作区、Search 2.0、Review / Summary / Iteration 和 Data Map 2.0 未进入。

## 40. v1.1.6 Stage 1 Phase 5 proposal-only 调整入口门槛

状态：`phase_1_5_contract_created_pending_stage_review`。

模型假设：

- 用户看懂总览、建议动作、层级资产和主题分类后，需要安全提出修正，而不是直接写长期记忆。
- proposal-only 调整入口只生成 draft，不是完整 proposal 编辑工作区，也不是 agent apply。
- 每个 draft 必须保留来源、目标、字段、旧值引用、建议值、理由、证据、冲突检查要求和 rollback hint。

输入：

- `docs/product/proposal_only_adjustment_entry_contract.md`
- `docs/acceptance/proposal_only_adjustment_entry_acceptance.md`
- Stage 1 Phase 1 记忆总览使用说明合同。
- Stage 1 Phase 2 建议动作明细合同。
- Stage 1 Phase 3 层级资产明细合同。
- Stage 1 Phase 4 主题分类明细合同。
- 后续实现 phase 的 redacted evidence、Inspector focus 和浏览器截图。

处理方法：

- 固定五类入口：memory_overview、suggested_action_detail、tier_asset_detail、topic_classification_detail、inspector。
- 固定四类目标：overview_signal、suggested_action、tier_asset、topic_classification。
- 固定八类允许字段：importance、priority、topic_category、action_status、due_window、hidden_until、stale_override、confidence_note。
- 固定 proposal draft 最小 schema 和 no-direct-writeback 安全说明。
- 使用 `validate:v1.1.6-stage1-phase5` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S1P05-001 proposal_entry_surfaces = memory_overview;suggested_action_detail;tier_asset_detail;topic_classification_detail;inspector`
- `PARAM-MA-V116-S1P05-002 proposal_target_types = overview_signal;suggested_action;tier_asset;topic_classification`
- `PARAM-MA-V116-S1P05-003 proposal_allowed_fields = importance;priority;topic_category;action_status;due_window;hidden_until;stale_override;confidence_note`
- `PARAM-MA-V116-S1P05-004 proposal_required_schema_fields = proposal_id;proposal_schema_version;parent_snapshot_id;entry_surface;target_type;target_id;field;old_value_ref;proposed_value;reason;evidence_refs;confidence;created_at;created_by;requires_conflict_check;requires_agent_or_human_apply;rollback_hint`
- `PARAM-MA-V116-S1P05-005 proposal_schema_version = memory_atlas_proposal_entry.v1`
- `PARAM-MA-V116-S1P05-006 requires_conflict_check = true`
- `PARAM-MA-V116-S1P05-007 requires_agent_or_human_apply = true`
- `PARAM-MA-V116-S1P05-008 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S1P05-009 forbidden_payload_scope = raw_private_cookie_session_secret_local_absolute_path`
- `PARAM-MA-V116-S1P05-010 stage1_phase5_required_validator = validate:v1.1.6-stage1-phase5`

输出：

- Stage 1 Phase 5 产品合同。
- Stage 1 Phase 5 验收文件。
- Stage 1 Phase 5 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 完整 proposal 编辑工作区、agent apply、Search 2.0、Review / Summary / Iteration 和 Data Map 2.0 未进入。
- Stage 1 phase 本地完成后仍需整体复审，复审通过前不得进入 Stage 2 或上传 GitHub main。

## 41. v1.1.6 Stage 1 整体复审门槛

状态：`stage_1_review_passed_pending_stage2`。

模型假设：

- Stage 1 只有在 Phase 1.1 到 Phase 1.5 的合同、验收、validator 和记录均一致时，才允许进入 Stage 2。
- Stage 1 复审通过不等于运行时 UI、浏览器截图、完整 proposal editor、Search 2.0、Review / Summary / Iteration 或 Data Map 已完成。
- GitHub main 上传必须等 Stage 1-5 全部完成并通过最终上传 gate。

输入：

- `docs/product/memory_overview_usage_contract.md`
- `docs/product/suggested_action_detail_contract.md`
- `docs/product/tier_asset_detail_contract.md`
- `docs/product/topic_classification_detail_contract.md`
- `docs/product/proposal_only_adjustment_entry_contract.md`
- `docs/reviews/memory_atlas_v1_1_6_stage1_review.md`
- Stage 1 Phase 1-5 validator。

处理方法：

- 固定 Stage 1 五个 phase 的合同和验收边界。
- 固定 Stage 1 review artifact。
- 固定 `validate:v1.1.6-stage1` 为进入 Stage 2 前的必跑 gate。
- 确认 changed paths 仅限 Stage 1 contracts、acceptance、records、review、validators 和 package script。

参数与门槛：

- `PARAM-MA-V116-S1-REVIEW-001 stage1_required_validator = validate:v1.1.6-stage1`
- `PARAM-MA-V116-S1-REVIEW-002 stage1_review_status = stage_1_review_passed_pending_stage2`
- `PARAM-MA-V116-S1-REVIEW-003 stage1_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage1_review.md`
- `PARAM-MA-V116-S1-REVIEW-004 stage1_allowed_change_scope = contracts;acceptance;review;records;validators;package_script`
- `PARAM-MA-V116-S1-REVIEW-005 stage1_next_gate = Stage 2 bounded run`
- `PARAM-MA-V116-S1-REVIEW-006 upload_boundary = no_github_main_upload_until_stage1_to_stage5_complete`

输出：

- Stage 1 review artifact。
- Stage 1 validator。
- Stage 1 记录状态：`stage_1_review_passed_pending_stage2`。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由或 feature flag。
- 本复审不进入 Stage 2-5，不执行 GitHub main 上传。

## 42. v1.1.6 Stage 2 Phase 1 明细可见性工作台门槛

状态：`phase_2_1_contract_created_pending_stage_review`。

模型假设：

- Stage 2 的第一步是建立统一明细工作台 IA，而不是直接实现 React/CSS。
- 建议动作、层级资产和主题分类三类明细必须能在同一个工作台模式下展开、筛选、排序并交接 Inspector。
- 工作台内筛选不是 Search 2.0，不能把搜索工作流冒充为本 phase 已完成。

输入：

- `docs/product/detail_visibility_workbench_contract.md`
- `docs/acceptance/detail_visibility_workbench_acceptance.md`
- Stage 1 记忆总览、建议动作、层级资产、主题分类和 proposal-only 调整入口合同。
- 后续实现 phase 的 redacted evidence、Universe State、Inspector focus 和浏览器截图。

处理方法：

- 固定工作台区域：workbench_header、scope_controls、density_mode、suggested_action_lane、tier_asset_lane、topic_classification_lane、inspector_handoff、proposal_entry_hint、empty_state、error_state。
- 固定三类 lane 的最小字段和默认排序。
- 固定展开交互：collapsed summary、expanded detail、open_inspector、jump_to_related、proposal_only_entry。
- 固定筛选：source_scope、confidence、evidence_count、proposal_hint、urgency、effort_cost、action_type、asset_tier、importance、priority、staleness_status、topic_state、trend、clear_filters。
- 使用 `validate:v1.1.6-stage2-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S2P01-001 workbench_regions = workbench_header;scope_controls;density_mode;suggested_action_lane;tier_asset_lane;topic_classification_lane;inspector_handoff;proposal_entry_hint;empty_state;error_state`
- `PARAM-MA-V116-S2P01-002 required_lanes = suggested_action_lane;tier_asset_lane;topic_classification_lane`
- `PARAM-MA-V116-S2P01-003 expansion_primitives = collapsed_summary;expanded_detail;open_inspector;jump_to_related;proposal_only_entry`
- `PARAM-MA-V116-S2P01-004 suggested_action_lane_fields = action_id;title;action_type;reason;roi_score;effort_cost;urgency;confidence;evidence_count;next_step;proposal_hint;open_inspector`
- `PARAM-MA-V116-S2P01-005 tier_asset_lane_fields = asset_id;asset_tier;title;summary;importance;priority;confidence;staleness_status;evidence_count;linked_action_ids;recommended_asset_action;proposal_hint;open_inspector`
- `PARAM-MA-V116-S2P01-006 topic_classification_lane_fields = topic_id;topic_label;topic_state;topic_strength;trend;confidence;record_count;evidence_count;linked_asset_ids;linked_action_ids;recommended_topic_action;proposal_hint;open_inspector`
- `PARAM-MA-V116-S2P01-007 required_filters = source_scope;confidence;evidence_count;proposal_hint;urgency;effort_cost;action_type;asset_tier;importance;priority;staleness_status;topic_state;trend;clear_filters`
- `PARAM-MA-V116-S2P01-008 required_explanation_surface = Inspector`
- `PARAM-MA-V116-S2P01-009 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S2P01-010 stage2_phase1_required_validator = validate:v1.1.6-stage2-phase1`

输出：

- Stage 2 Phase 1 产品合同。
- Stage 2 Phase 1 验收文件。
- Stage 2 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 proposal editor 和 agent apply 未进入。
- Stage 2 整体复审未执行。

## 43. v1.1.6 Stage 2 Phase 2 suggested action lane 可见性门槛

状态：`phase_2_2_contract_created_pending_stage_review`。

模型假设：

- Stage 2 Phase 2 只细化 suggested_action_lane，不实现运行时 React/CSS。
- 建议动作必须能被快速扫描、比较、展开证据，并交接 Inspector。
- 建议动作可引导 proposal-only 调整，但不得直接写 active memory 或长期记忆。

输入：

- `docs/product/suggested_action_lane_visibility_contract.md`
- `docs/acceptance/suggested_action_lane_visibility_acceptance.md`
- Stage 2 Phase 1 明细可见性工作台合同。
- Stage 1 建议动作明细合同和 proposal-only 调整入口合同。

处理方法：

- 固定 suggested_action_lane 三层信息：scan_row、decision_row、evidence_drawer。
- 固定建议动作最小字段、分组、排序、badge 和交互。
- 固定 Inspector handoff 字段与 proposal-only 边界。
- 使用 `validate:v1.1.6-stage2-phase2` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S2P02-001 action_lane_layers = scan_row;decision_row;evidence_drawer`
- `PARAM-MA-V116-S2P02-002 suggested_action_required_fields = action_id;title;action_type;reason;roi_score;effort_cost;urgency;confidence;evidence_count;evidence_refs;source_scope;linked_theme_ids;linked_asset_ids;next_step;recommended_time_window;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S2P02-003 action_groups = now;this_week;later;watch`
- `PARAM-MA-V116-S2P02-004 action_sort_keys = roi_score;urgency;effort_cost;confidence;evidence_count;selection_focus`
- `PARAM-MA-V116-S2P02-005 action_badges = high_roi;medium_roi;low_roi;low_effort;medium_effort;high_effort;urgent_now;this_week;later;watch;evidence_ready;evidence_thin;missing_evidence;proposal_recommended;proposal_not_needed`
- `PARAM-MA-V116-S2P02-006 action_interactions = expand_action;compare_actions;pin_action;mark_reviewed;clear_temporary_state`
- `PARAM-MA-V116-S2P02-007 inspector_handoff_fields = source_lane;target_type;action_id;title;action_type;reason;roi_score;effort_cost;urgency;confidence;evidence_refs;linked_theme_ids;linked_asset_ids;next_step;recommended_time_window;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S2P02-008 action_states = empty_state;low_evidence_state;error_state;loading_state`
- `PARAM-MA-V116-S2P02-009 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S2P02-010 stage2_phase2_required_validator = validate:v1.1.6-stage2-phase2`

输出：

- Stage 2 Phase 2 产品合同。
- Stage 2 Phase 2 验收文件。
- Stage 2 Phase 2 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 proposal editor 和 agent apply 未进入。
- Stage 2 整体复审未执行。

## 44. v1.1.6 Stage 2 Phase 3 tier asset lane 可见性门槛

状态：`phase_2_3_contract_created_pending_stage_review`。

模型假设：

- Stage 2 Phase 3 只细化 tier_asset_lane，不实现运行时 React/CSS。
- 层级资产必须能被快速扫描、比较、展开证据，并交接 Inspector。
- 层级资产可引导 proposal-only 调整，但不得直接写 active memory 或长期记忆。

输入：

- `docs/product/tier_asset_lane_visibility_contract.md`
- `docs/acceptance/tier_asset_lane_visibility_acceptance.md`
- Stage 2 Phase 1 明细可见性工作台合同。
- Stage 1 层级资产明细合同和 proposal-only 调整入口合同。

处理方法：

- 固定 tier_asset_lane 三层信息：asset_scan_row、asset_decision_row、asset_evidence_drawer。
- 固定层级资产最小字段、七类资产分组、排序、badge 和交互。
- 固定 Inspector handoff 字段与 proposal-only 边界。
- 使用 `validate:v1.1.6-stage2-phase3` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S2P03-001 asset_lane_layers = asset_scan_row;asset_decision_row;asset_evidence_drawer`
- `PARAM-MA-V116-S2P03-002 tier_asset_required_fields = asset_id;asset_tier;title;summary;importance;priority;confidence;staleness_status;evidence_count;evidence_refs;source_scope;linked_action_ids;linked_theme_ids;linked_time_range;recommended_asset_action;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S2P03-003 asset_groups = core_profile;project;decision;workflow;knowledge;opportunity;stale`
- `PARAM-MA-V116-S2P03-004 asset_sort_keys = importance;priority;staleness_status;confidence;evidence_count;selection_focus`
- `PARAM-MA-V116-S2P03-005 asset_badges = core_profile;project;decision;workflow;knowledge;opportunity;stale;high_importance;medium_importance;low_importance;p0;p1;p2;p3;watch;current;needs_review;stale;unknown;evidence_ready;evidence_thin;missing_evidence;proposal_recommended;proposal_not_needed`
- `PARAM-MA-V116-S2P03-006 asset_interactions = expand_asset;compare_assets;pin_asset;mark_reviewed;jump_to_linked_action;clear_temporary_state`
- `PARAM-MA-V116-S2P03-007 inspector_handoff_fields = source_lane;target_type;asset_id;asset_tier;title;summary;importance;priority;confidence;staleness_status;evidence_refs;source_scope;linked_action_ids;linked_theme_ids;linked_time_range;recommended_asset_action;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S2P03-008 asset_states = empty_state;low_evidence_state;stale_conflict_state;error_state;loading_state`
- `PARAM-MA-V116-S2P03-009 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S2P03-010 stage2_phase3_required_validator = validate:v1.1.6-stage2-phase3`

输出：

- Stage 2 Phase 3 产品合同。
- Stage 2 Phase 3 验收文件。
- Stage 2 Phase 3 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 proposal editor 和 agent apply 未进入。
- Stage 2 整体复审未执行。

## 45. v1.1.6 Stage 2 Phase 4 topic classification lane 可见性门槛

状态：`phase_2_4_contract_created_pending_stage_review`。

模型假设：

- Stage 2 Phase 4 只细化 topic_classification_lane，不实现运行时 React/CSS。
- 主题分类必须能被快速扫描、比较、展开证据，并交接 Inspector。
- 主题分类可引导 proposal-only 调整，但不得直接写 active memory 或长期记忆。

输入：

- `docs/product/topic_classification_lane_visibility_contract.md`
- `docs/acceptance/topic_classification_lane_visibility_acceptance.md`
- Stage 2 Phase 1 明细可见性工作台合同。
- Stage 1 主题分类明细合同和 proposal-only 调整入口合同。

处理方法：

- 固定 topic_classification_lane 三层信息：topic_scan_row、topic_decision_row、topic_evidence_drawer。
- 固定主题分类最小字段、七类主题状态分组、排序、badge 和交互。
- 固定 Inspector handoff 字段与 proposal-only 边界。
- 使用 `validate:v1.1.6-stage2-phase4` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S2P04-001 topic_lane_layers = topic_scan_row;topic_decision_row;topic_evidence_drawer`
- `PARAM-MA-V116-S2P04-002 topic_classification_required_fields = topic_id;topic_label;topic_state;topic_strength;trend;confidence;record_count;evidence_count;evidence_refs;source_scope;linked_asset_ids;linked_action_ids;linked_starfield_cluster_id;linked_river_range;related_topic_ids;matched_reason;recommended_topic_action;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S2P04-003 topic_groups = dominant;rising;emerging;conflict;black_hole;declining;stale`
- `PARAM-MA-V116-S2P04-004 topic_sort_keys = topic_strength;trend;confidence;record_count;evidence_count;selection_focus`
- `PARAM-MA-V116-S2P04-005 topic_badges = dominant;rising;declining;emerging;conflict;black_hole;stale;high_strength;medium_strength;low_strength;trend_up;trend_down;trend_flat;trend_new;trend_volatile;high_confidence;medium_confidence;low_confidence;evidence_ready;evidence_thin;missing_evidence;proposal_recommended;proposal_not_needed`
- `PARAM-MA-V116-S2P04-006 topic_interactions = expand_topic;compare_topics;pin_topic;mark_reviewed;jump_to_linked_asset;jump_to_linked_action;jump_to_starfield;jump_to_river;clear_temporary_state`
- `PARAM-MA-V116-S2P04-007 inspector_handoff_fields = source_lane;target_type;topic_id;topic_label;topic_state;topic_strength;trend;confidence;record_count;evidence_count;evidence_refs;source_scope;linked_asset_ids;linked_action_ids;linked_starfield_cluster_id;linked_river_range;related_topic_ids;matched_reason;recommended_topic_action;proposal_hint;rollback_hint`
- `PARAM-MA-V116-S2P04-008 topic_states = empty_state;low_evidence_state;conflict_state;black_hole_state;stale_state;error_state;loading_state`
- `PARAM-MA-V116-S2P04-009 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S2P04-010 stage2_phase4_required_validator = validate:v1.1.6-stage2-phase4`

输出：

- Stage 2 Phase 4 产品合同。
- Stage 2 Phase 4 验收文件。
- Stage 2 Phase 4 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- Search 2.0、Review / Summary / Iteration、Data Map 2.0、完整 proposal editor 和 agent apply 未进入。
- Stage 2 整体复审未执行。

## 46. v1.1.6 Stage 2 整体复审门槛

状态：`stage_2_review_passed_pending_stage3`。

模型假设：

- Stage 2 只有在 Phase 2.1 到 Phase 2.4 的合同、验收、validator 和记录均一致时，才允许进入 Stage 3。
- Stage 2 复审通过不等于运行时 UI、浏览器截图、完整 proposal editor、Search 2.0、Review / Summary / Iteration 或 Data Map 已完成。
- GitHub main 上传必须等 Stage 1-5 全部完成并通过最终上传 gate。

输入：

- `docs/product/detail_visibility_workbench_contract.md`
- `docs/product/suggested_action_lane_visibility_contract.md`
- `docs/product/tier_asset_lane_visibility_contract.md`
- `docs/product/topic_classification_lane_visibility_contract.md`
- `docs/reviews/memory_atlas_v1_1_6_stage2_review.md`
- Stage 2 Phase 1-4 validator。

处理方法：

- 固定 Stage 2 四个 phase 的合同和验收边界。
- 固定 Stage 2 review artifact。
- 固定 `validate:v1.1.6-stage2` 为进入 Stage 3 前的必跑 gate。
- 确认 changed paths 仅限 Stage 1 和 Stage 2 contracts、acceptance、records、review、validators 和 package script。

参数与门槛：

- `PARAM-MA-V116-S2-REVIEW-001 stage2_required_validator = validate:v1.1.6-stage2`
- `PARAM-MA-V116-S2-REVIEW-002 stage2_review_status = stage_2_review_passed_pending_stage3`
- `PARAM-MA-V116-S2-REVIEW-003 stage2_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage2_review.md`
- `PARAM-MA-V116-S2-REVIEW-004 stage2_allowed_change_scope = contracts;acceptance;review;records;validators;package_script`
- `PARAM-MA-V116-S2-REVIEW-005 stage2_next_gate = Stage 3 bounded run`
- `PARAM-MA-V116-S2-REVIEW-006 upload_boundary = no_github_main_upload_until_stage1_to_stage5_complete`

输出：

- Stage 2 review artifact。
- Stage 2 validator。
- Stage 2 记录状态：`stage_2_review_passed_pending_stage3`。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由或 feature flag。
- 本复审不进入 Stage 3-5，不执行 GitHub main 上传。

## 47. v1.1.6 Stage 3 Phase 1 proposal-only 调整工作区门槛

状态：`phase_3_1_contract_created_pending_stage_review`。

模型假设：

- 用户调整重要性、优先级、主题、状态或隐藏窗口时，需要完整 proposal-only adjustment workspace，而不是只有入口提示。
- proposal-only 工作区必须让 old_value、proposed_value、reason、evidence_refs、confidence、冲突检查要求和 rollback_hint 同时可见。
- 工作区可以把 proposal 标记为 ready_for_agent_apply，但不能执行 agent apply，也不能直接写 active memory。

输入：

- `docs/product/proposal_only_adjustment_workspace_contract.md`
- `docs/acceptance/proposal_only_adjustment_workspace_acceptance.md`
- Stage 1 proposal-only 调整入口合同。
- Stage 2 明细可见性工作台和三类 lane 合同。
- 后续实现 phase 的 redacted snapshot、Inspector focus 和浏览器截图。

处理方法：

- 固定工作区区域：proposal_queue、target_context_panel、field_editor_panel、proposal_diff_preview、safety_review_panel、rollback_panel。
- 固定允许字段：importance、priority、topic_category、action_status、due_window、hidden_until、stale_override、confidence_note。
- 固定四类目标：overview_signal、suggested_action、tier_asset、topic_classification。
- 固定 proposal draft schema、proposal 状态、Inspector 交接和 no-direct-writeback 安全说明。
- 使用 `validate:v1.1.6-stage3-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S3P01-001 workspace_regions = proposal_queue;target_context_panel;field_editor_panel;proposal_diff_preview;safety_review_panel;rollback_panel`
- `PARAM-MA-V116-S3P01-002 allowed_fields = importance;priority;topic_category;action_status;due_window;hidden_until;stale_override;confidence_note`
- `PARAM-MA-V116-S3P01-003 proposal_target_types = overview_signal;suggested_action;tier_asset;topic_classification`
- `PARAM-MA-V116-S3P01-004 proposal_required_schema_fields = proposal_id;proposal_schema_version;parent_snapshot_id;source_surface;entry_surface;target_type;target_id;field;old_value;old_value_ref;proposed_value;reason;evidence_refs;confidence;status;created_at;created_by;requires_conflict_check;requires_agent_or_human_apply;rollback_hint`
- `PARAM-MA-V116-S3P01-005 proposal_statuses = draft;needs_review;ready_for_agent_apply;rejected;superseded`
- `PARAM-MA-V116-S3P01-006 proposal_boundary = proposal_only_no_direct_active_memory_write`
- `PARAM-MA-V116-S3P01-007 stage3_phase1_required_validator = validate:v1.1.6-stage3-phase1`

输出：

- Stage 3 Phase 1 产品合同。
- Stage 3 Phase 1 验收文件。
- Stage 3 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不实现 agent apply，不进入 Search 2.0、Review / Summary / Iteration 或 Data Map 2.0。
- Stage 3 整体复审未执行。

## 48. v1.1.6 Stage 3 Phase 2 proposal queue 持久化与版本链门槛

状态：`phase_3_2_contract_created_pending_stage_review`。

模型假设：

- proposal-only 工作区只有在 proposal queue 可追溯、可复核、可回滚时，才适合支持用户调整重要性、优先级和主题。
- 本地 queue 可以保存 draft metadata，但不能保存 raw/private 内容，不能直接写 active memory，也不能代替 agent/human apply。
- 版本链必须 append-only；修改、替代和回滚都必须生成新记录而不是覆盖旧记录。

输入：

- `docs/product/proposal_queue_persistence_contract.md`
- `docs/acceptance/proposal_queue_persistence_acceptance.md`
- Stage 3 Phase 1 proposal-only 调整工作区合同。
- 现有写回提案版本控制模型。
- 后续实现 phase 的 redacted snapshot、Inspector focus 和浏览器截图。

处理方法：

- 固定 storage key：`memory-atlas.writeback.proposals.v1`。
- 固定 storage_scope：`browser_local_only`。
- 固定 queue_mutation_policy：`append_only`。
- 固定 proposal_record、proposal_revision、proposal_history 和 rollback_proposal。
- 固定 stale_snapshot、schema_mismatch 和 forbidden_payload 阻断状态。
- 使用 `validate:v1.1.6-stage3-phase2` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S3P02-001 storage_key = memory-atlas.writeback.proposals.v1`
- `PARAM-MA-V116-S3P02-002 storage_scope = browser_local_only`
- `PARAM-MA-V116-S3P02-003 queue_mutation_policy = append_only`
- `PARAM-MA-V116-S3P02-004 required_record_fields = proposal_id;proposal_schema_version;revision;parent_proposal_id;supersedes_proposal_id;rollback_to_proposal_id;parent_snapshot_id;target_ref;target_type;target_id;field;old_value_ref;proposed_value;diff_summary;reason;evidence_refs;status;created_at;updated_at;created_by;requires_conflict_check;requires_agent_or_human_apply;rollback_hint`
- `PARAM-MA-V116-S3P02-005 proposal_statuses = draft;needs_review;ready_for_agent_apply;rejected;superseded`
- `PARAM-MA-V116-S3P02-006 failure_states = stale_snapshot;schema_mismatch;forbidden_payload`
- `PARAM-MA-V116-S3P02-007 stage3_phase2_required_validator = validate:v1.1.6-stage3-phase2`

输出：

- Stage 3 Phase 2 产品合同。
- Stage 3 Phase 2 验收文件。
- Stage 3 Phase 2 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不写 localStorage，不实现 agent apply，不进入 Search 2.0、Review / Summary / Iteration 或 Data Map 2.0。
- Stage 3 整体复审未执行。

## 49. v1.1.6 Stage 3 整体复审门槛

状态：`stage_3_review_passed_pending_stage4`。

模型假设：

- Stage 3 只有在 Phase 3.1 和 Phase 3.2 的合同、验收、validator 和记录均一致时，才允许进入 Stage 4。
- Stage 3 复审通过不等于运行时 UI、浏览器截图、真实 localStorage queue、agent apply、Search 2.0、Review / Summary / Iteration 或 Data Map 已完成。
- GitHub main 上传必须等 Stage 1-5 全部完成并通过最终上传 gate。

输入：

- `docs/product/proposal_only_adjustment_workspace_contract.md`
- `docs/product/proposal_queue_persistence_contract.md`
- `docs/reviews/memory_atlas_v1_1_6_stage3_review.md`
- Stage 3 Phase 1-2 validator。

处理方法：

- 固定 Stage 3 两个 phase 的合同和验收边界。
- 固定 Stage 3 review artifact。
- 固定 `validate:v1.1.6-stage3` 为进入 Stage 4 前的必跑 gate。
- 确认 changed paths 仅限 Stage 1、Stage 2 和 Stage 3 contracts、acceptance、records、reviews、validators 和 package script。

参数与门槛：

- `PARAM-MA-V116-S3-REVIEW-001 stage3_required_validator = validate:v1.1.6-stage3`
- `PARAM-MA-V116-S3-REVIEW-002 stage3_review_status = stage_3_review_passed_pending_stage4`
- `PARAM-MA-V116-S3-REVIEW-003 stage3_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage3_review.md`
- `PARAM-MA-V116-S3-REVIEW-004 stage3_allowed_change_scope = contracts;acceptance;review;records;validators;package_script`
- `PARAM-MA-V116-S3-REVIEW-005 stage3_next_gate = Stage 4 bounded run`
- `PARAM-MA-V116-S3-REVIEW-006 upload_boundary = no_github_main_upload_until_stage1_to_stage5_complete`

输出：

- Stage 3 review artifact。
- Stage 3 validator。
- Stage 3 记录状态：`stage_3_review_passed_pending_stage4`。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由、feature flag 或 localStorage。
- 本复审不进入 Stage 4-5，不执行 GitHub main 上传。

## 50. v1.1.6 Stage 4 Phase 1 Search 2.0 工作流参数

状态：`phase_4_1_contract_created_pending_stage_review`。

模型假设：

- Search 2.0 必须是搜索、解释、跳转和下一步行动的工作流，不是普通数据库列表。
- 搜索结果只有在能解释 `matched_reason`、显示 title/summary/source/tier/topic/recency/importance，并提供 Starfield/River/Inspector 跳转时，才适合进入真实使用。
- Search 2.0 只能使用 redacted summary 和 evidence_refs，不读取 raw/private/cookie/session/secret。
- 本 phase 不实现运行时搜索、不进入 Review / Summary / Iteration、不进入 Data Map 2.0。

输入：

- `docs/product/search_2_0_workflow_contract.md`
- `docs/acceptance/search_2_0_workflow_acceptance.md`
- Stage 1-3 已建立的 overview、detail、proposal-only 合同。

处理方法：

- 固定 `search_2_0_workflow` 区域：`query_input`、`filter_state`、`result_list`、`result_action_bar`、`search_session_summary`、`zero_result_recovery`。
- 固定结果字段：title、summary、source、tier、topic、recency、importance、matched_reason、evidence_refs、jump_to_starfield、jump_to_river、open_inspector、proposal_candidate。
- 固定安全边界：No runtime UI、No raw/private data read、No direct writeback、No GitHub main upload。
- 使用 `validate:v1.1.6-stage4-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S4P01-001 stage4_phase1_contract_id = search_2_0_workflow`
- `PARAM-MA-V116-S4P01-002 stage4_phase1_required_regions = query_input;filter_state;result_list;result_action_bar;search_session_summary;zero_result_recovery`
- `PARAM-MA-V116-S4P01-003 stage4_phase1_required_result_fields = title;summary;source;tier;topic;recency;importance;matched_reason;evidence_refs;jump_to_starfield;jump_to_river;open_inspector;proposal_candidate`
- `PARAM-MA-V116-S4P01-004 stage4_phase1_navigation_actions = jump_to_starfield;jump_to_river;open_inspector`
- `PARAM-MA-V116-S4P01-005 stage4_phase1_safety = redacted_summary_only;no_raw_private;no_direct_writeback`
- `PARAM-MA-V116-S4P01-006 stage4_phase1_status = phase_4_1_contract_created_pending_stage_review`
- `PARAM-MA-V116-S4P01-007 stage4_phase1_required_validator = validate:v1.1.6-stage4-phase1`

输出：

- Stage 4 Phase 1 产品合同。
- Stage 4 Phase 1 验收文件。
- Stage 4 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不进入 Review / Summary / Iteration、Data Map 2.0、Stage 5 或 GitHub main 上传。

## 51. v1.1.6 Stage 4 Phase 2 Review / Summary / Iteration 工作流参数

状态：`phase_4_2_contract_created_pending_stage_review`。

模型假设：

- Review / Summary / Iteration 必须回答八个复盘问题，不能只给摘要。
- 复盘结论必须包含 evidence_refs、confidence、next_actions 和 proposal_candidate 判断。
- 如果需要调整重要性、优先级、主题、动作状态或隐藏策略，必须进入 Stage 3 proposal-only 工作区。
- 本 phase 不实现运行时复盘、不读取 raw/private/cookie/session/secret、不进入 Data Map 2.0。

输入：

- `docs/product/review_summary_iteration_workflow_contract.md`
- `docs/acceptance/review_summary_iteration_workflow_acceptance.md`
- Stage 4 Phase 1 Search 2.0 工作流合同。
- Stage 3 proposal-only 工作区和 queue 合同。

处理方法：

- 固定 `review_summary_iteration_workflow` 区域：`review_period_selector`、`theme_change_panel`、`opportunity_panel`、`low_value_loop_panel`、`decision_change_panel`、`next_action_panel`、`proposal_decision_panel`、`iteration_backlog`。
- 固定八个复盘问题：本期主导主题是什么、哪些主题增强、哪些主题衰退、哪些新机会出现、哪些低价值循环出现、哪些决策变化、下一步动作是什么、是否需要生成 proposal。
- 固定输出字段：dominant_topics、strengthening_topics、declining_topics、new_opportunities、low_value_loops、decision_changes、next_actions、proposal_candidate、evidence_refs、confidence、iteration。
- 固定安全边界：No runtime UI、No raw/private data read、No direct writeback、No GitHub main upload。
- 使用 `validate:v1.1.6-stage4-phase2` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S4P02-001 stage4_phase2_contract_id = review_summary_iteration_workflow`
- `PARAM-MA-V116-S4P02-002 stage4_phase2_required_regions = review_period_selector;theme_change_panel;opportunity_panel;low_value_loop_panel;decision_change_panel;next_action_panel;proposal_decision_panel;iteration_backlog`
- `PARAM-MA-V116-S4P02-003 stage4_phase2_required_questions = dominant_topics;strengthening_topics;declining_topics;new_opportunities;low_value_loops;decision_changes;next_actions;proposal_candidate`
- `PARAM-MA-V116-S4P02-004 stage4_phase2_required_outputs = evidence_refs;confidence;iteration;acceptance_hint;blocked_reason;review_again_at`
- `PARAM-MA-V116-S4P02-005 stage4_phase2_safety = redacted_summary_only;no_raw_private;no_direct_writeback`
- `PARAM-MA-V116-S4P02-006 stage4_phase2_status = phase_4_2_contract_created_pending_stage_review`
- `PARAM-MA-V116-S4P02-007 stage4_phase2_required_validator = validate:v1.1.6-stage4-phase2`

输出：

- Stage 4 Phase 2 产品合同。
- Stage 4 Phase 2 验收文件。
- Stage 4 Phase 2 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不进入 Data Map 2.0、Stage 5 或 GitHub main 上传。

## 52. v1.1.6 Stage 4 整体复审门槛

状态：`stage_4_review_passed_pending_stage5`。

模型假设：

- Stage 4 只有在 Phase 4.1 和 Phase 4.2 的合同、验收、validator 和记录均一致时，才允许进入 Stage 5。
- Stage 4 复审通过不等于运行时 UI、浏览器截图、runtime Search 2.0、runtime Review / Summary / Iteration 或 Data Map 2.0 已完成。
- 本复审不实现运行时搜索、不实现复盘 runtime、不读取 raw/private/cookie/session/secret、不执行 direct writeback。

输入：

- `docs/product/search_2_0_workflow_contract.md`
- `docs/acceptance/search_2_0_workflow_acceptance.md`
- `docs/product/review_summary_iteration_workflow_contract.md`
- `docs/acceptance/review_summary_iteration_workflow_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_6_stage4_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage4.cjs`

处理方法：

- 固定 `validate:v1.1.6-stage4` 为进入 Stage 5 前的必跑 gate。
- 固定 Stage 4 review artifact 为 `docs/reviews/memory_atlas_v1_1_6_stage4_review.md`。
- 固定允许改动范围为 contracts、acceptance、review、records、validators、package_script。
- 固定上传边界：Stage 1-5 完成并通过最终上传 gate 前不上传 GitHub main。

参数与门槛：

- `PARAM-MA-V116-S4-REVIEW-001 stage4_required_validator = validate:v1.1.6-stage4`
- `PARAM-MA-V116-S4-REVIEW-002 stage4_review_status = stage_4_review_passed_pending_stage5`
- `PARAM-MA-V116-S4-REVIEW-003 stage4_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage4_review.md`
- `PARAM-MA-V116-S4-REVIEW-004 stage4_allowed_change_scope = contracts;acceptance;review;records;validators;package_script`
- `PARAM-MA-V116-S4-REVIEW-005 stage4_next_gate = Stage 5 bounded run`
- `PARAM-MA-V116-S4-REVIEW-006 upload_boundary = no_github_main_upload_until_stage1_to_stage5_complete`

输出：

- Stage 4 复审 artifact。
- Stage 4 stage-level validator。
- Stage 4 记录状态：`stage_4_review_passed_pending_stage5`。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由、feature flag 或 localStorage。
- 本复审不进入 Stage 5，不执行 GitHub main 上传。

## 53. v1.1.6 Stage 5 Phase 1 Data Map 2.0 工作流参数

状态：`phase_5_1_contract_created_pending_stage_review`。

模型假设：

- Data Map 2.0 必须解释数据如何变成行动建议，不能只是 static structure diagram。
- Data Map 2.0 必须至少包含来源层、主题层、资产层和行动层。
- 每张 map card 必须包含 label、type、strength、trend、evidence_count、action_count 和 inspector_link。
- 本 phase 不实现运行时 Data Map、不读取 raw/private/cookie/session/secret、不执行 direct writeback。

输入：

- `docs/product/data_map_2_0_workflow_contract.md`
- `docs/acceptance/data_map_2_0_workflow_acceptance.md`
- Stage 4 Search 2.0 工作流合同。
- Stage 4 Review / Summary / Iteration 工作流合同。

处理方法：

- 固定 `data_map_2_0_workflow` 四层结构：`source_layer`、`topic_layer`、`asset_layer`、`action_layer`。
- 固定数据到行动路径：`source_to_topic_edges`、`topic_to_asset_edges`、`asset_to_action_edges`、`data_to_action_flow`。
- 固定 map card 字段：label、type、strength、trend、evidence_count、action_count、inspector_link。
- 固定跨工作流 handoff：open_inspector、jump_to_search、jump_to_review、proposal_candidate。
- 固定安全边界：No runtime UI、No raw/private data read、No direct writeback、No GitHub main upload。
- 使用 `validate:v1.1.6-stage5-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S5P01-001 stage5_phase1_contract_id = data_map_2_0_workflow`
- `PARAM-MA-V116-S5P01-002 stage5_phase1_required_layers = source_layer;topic_layer;asset_layer;action_layer`
- `PARAM-MA-V116-S5P01-003 stage5_phase1_required_edges = source_to_topic_edges;topic_to_asset_edges;asset_to_action_edges;data_to_action_flow`
- `PARAM-MA-V116-S5P01-004 stage5_phase1_required_card_fields = label;type;strength;trend;evidence_count;action_count;inspector_link`
- `PARAM-MA-V116-S5P01-005 stage5_phase1_handoffs = open_inspector;jump_to_search;jump_to_review;proposal_candidate`
- `PARAM-MA-V116-S5P01-006 stage5_phase1_status = phase_5_1_contract_created_pending_stage_review`
- `PARAM-MA-V116-S5P01-007 stage5_phase1_required_validator = validate:v1.1.6-stage5-phase1`

输出：

- Stage 5 Phase 1 产品合同。
- Stage 5 Phase 1 验收文件。
- Stage 5 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不进入 Stage 5 整体复审，不执行 GitHub main 上传。

## 54. v1.1.6 Stage 5 整体复审门槛

状态：`stage_5_review_passed_pending_stage1_5_final_upload`。

模型假设：

- Stage 5 只有在 Phase 5.1 的合同、验收、validator 和记录均一致时，才允许进入 Stage 1-5 final upload gate。
- Stage 5 复审通过不等于运行时 UI、浏览器截图、runtime Data Map 2.0 或 agent apply 已完成。
- Stage 5 复审不得读取 raw/private/cookie/session/secret，不得执行 direct writeback，不得上传 GitHub main。

输入：

- `docs/product/data_map_2_0_workflow_contract.md`
- `docs/acceptance/data_map_2_0_workflow_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_6_stage5_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage5_phase1.cjs`

处理方法：

- 先运行 Stage 5 Phase 1 validator。
- 检查 Stage 5 review artifact 是否覆盖 Phase 5.1、边界、风险和 Stage 1-5 final upload gate。
- 检查 delivery、feature、development、model parameter、changelog 和 package script 是否一致。
- 固定 `validate:v1.1.6-stage5` 为 Stage 1-5 final upload 前的必跑 gate。

参数与门槛：

- `PARAM-MA-V116-S5-REVIEW-001 stage5_required_validator = validate:v1.1.6-stage5`
- `PARAM-MA-V116-S5-REVIEW-002 stage5_review_status = stage_5_review_passed_pending_stage1_5_final_upload`
- `PARAM-MA-V116-S5-REVIEW-003 stage5_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage5_review.md`
- `PARAM-MA-V116-S5-REVIEW-004 stage5_allowed_change_scope = contracts;acceptance;records;reviews;validators;package_script`
- `PARAM-MA-V116-S5-REVIEW-005 stage5_next_gate = Stage 1-5 final upload`
- `PARAM-MA-V116-S5-REVIEW-006 upload_boundary = no_github_main_upload_until_final_upload_gate_passes`

输出：

- Stage 5 review artifact。
- Stage 5 stage-level validator。
- Stage 5 review records。

边界：

- 本复审不实现运行时 Data Map 2.0。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由或 feature flag。
- 本复审不进入 Stage 6，不执行 GitHub main 上传。

## 55. v1.1.6 Stage 6 Phase 1 记忆时间河重做参数

状态：`phase_6_1_contract_created_pending_stage_review`。

模型假设：

- 旧 Timeline 不能继续作为默认可用性答案；Stage 6 必须将它按 0 分处理并重做为记忆时间河。
- 记忆时间河必须让用户看见时间、主题、事件、决策、black-hole 风险和 proto-star 机会如何共同形成下一步行动。
- 本 phase 只定义合同和验收，不实现 runtime Memory River，不读取 raw/private/cookie/session/secret，不执行 direct writeback。

输入：

- `docs/product/memory_river_rebuild_contract.md`
- `docs/acceptance/memory_river_rebuild_acceptance.md`
- Roadmap v2 记忆时间河要求：时间河、主题带、事件脉冲、决策节点、black hole band、proto-star marker、zoom、brush、hover card、click Inspector、reduced motion。

处理方法：

- 固定 Memory River rebuild 的视觉层和交互层。
- 固定 river item 必备字段和 Inspector/proposal handoff。
- 固定 date list、static table、dots-and-lines-only、缺少生命周期 marker、缺少 Inspector 交接、raw/private hover card 和 ignored reduced motion 为失败条件。
- 使用 `validate:v1.1.6-stage6-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S6P01-001 stage6_phase1_contract_id = memory_river_rebuild_contract`
- `PARAM-MA-V116-S6P01-002 stage6_phase1_required_layers = time_river;theme_bands;event_pulses;decision_nodes;black_hole_band;proto_star_marker;evidence_density_lane`
- `PARAM-MA-V116-S6P01-003 stage6_phase1_required_interactions = zoom;brush;hover_card;click_inspector;keyboard_navigation;reduced_motion`
- `PARAM-MA-V116-S6P01-004 stage6_phase1_required_item_fields = river_item_id;item_type;occurred_at;theme_id;theme_label;topic_state;importance;confidence;evidence_count;evidence_refs;source_scope;linked_asset_ids;linked_action_ids;inspector_link;proposal_hint`
- `PARAM-MA-V116-S6P01-005 stage6_phase1_failure_conditions = date_list;static_table;dots_and_lines_only;missing_theme_bands;missing_lifecycle_markers;missing_inspector_handoff;raw_private_hover_card;reduced_motion_ignored`
- `PARAM-MA-V116-S6P01-006 stage6_phase1_status = phase_6_1_contract_created_pending_stage_review`
- `PARAM-MA-V116-S6P01-007 stage6_phase1_required_validator = validate:v1.1.6-stage6-phase1`

输出：

- Stage 6 Phase 1 产品合同。
- Stage 6 Phase 1 验收文件。
- Stage 6 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不进入 Stage 6 整体复审，不进入 Stage 7-10，不执行 GitHub main 上传。

## 56. v1.1.6 Stage 6 整体复审门槛

状态：`stage_6_review_passed_pending_github_main_upload`。

模型假设：

- Stage 6 只有在 Phase 6.1 的合同、验收、validator 和记录均一致时，才允许进入 GitHub main upload gate。
- Stage 6 复审通过不等于运行时 UI、浏览器截图、runtime Memory River、真实 zoom/brush 或 agent apply 已完成。
- Stage 6 复审不得读取 raw/private/cookie/session/secret，不得执行 direct writeback，不得进入 Stage 7。

输入：

- `docs/product/memory_river_rebuild_contract.md`
- `docs/acceptance/memory_river_rebuild_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_6_stage6_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage6_phase1.cjs`

处理方法：

- 检查 Stage 6 Phase 1 合同、验收和 validator 是否覆盖记忆时间河重做所需视觉层、交互、字段和失败条件。
- 检查 Stage 6 review artifact 是否覆盖 Phase 6.1、边界、风险和 Stage 7 前上传 gate。
- 检查 delivery、feature、development、model parameter、changelog 和 package script 是否一致。
- 固定 `validate:v1.1.6-stage6` 为 Stage 7 前的必跑 gate。

参数与门槛：

- `PARAM-MA-V116-S6-REVIEW-001 stage6_required_validator = validate:v1.1.6-stage6`
- `PARAM-MA-V116-S6-REVIEW-002 stage6_review_status = stage_6_review_passed_pending_github_main_upload`
- `PARAM-MA-V116-S6-REVIEW-003 stage6_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage6_review.md`
- `PARAM-MA-V116-S6-REVIEW-004 stage6_allowed_change_scope = contracts;acceptance;records;reviews;validators;package_script`
- `PARAM-MA-V116-S6-REVIEW-005 stage6_next_gate = GitHub main upload before Stage 7`
- `PARAM-MA-V116-S6-REVIEW-006 upload_boundary = no_stage7_until_stage6_upload_verified`

输出：

- Stage 6 review artifact。
- Stage 6 stage-level validator。
- Stage 6 review records。

边界：

- 本复审不实现运行时 Memory River。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由或 feature flag。
- 本复审不进入 Stage 7；GitHub main upload 只在 final remote checks 通过后执行。

## 57. v1.1.6 Stage 7 Phase 1 记忆星系重做参数

状态：`phase_7_1_contract_created_pending_stage_review`。

模型假设：

- 现有 Galaxy 不能继续作为 v1.1.6 记忆星系的最终可用性答案；Stage 7 必须将普通 node-link graph、dots-and-lines 和 Obsidian-like graph 设为失败条件。
- 记忆星系必须让用户看见主题引力、星云、流场、轨迹、黑洞风险、新生机会和记忆地形层如何共同解释当前记忆状态。
- 本 phase 只定义合同和验收，不实现 runtime Memory Starfield，不导入 experiment 目录，不切换 feature flag，不读取 raw/private/cookie/session/secret，不执行 direct writeback。

输入：

- `docs/product/memory_starfield_rebuild_contract.md`
- `docs/acceptance/memory_starfield_rebuild_acceptance.md`
- Roadmap v2 记忆星系要求：星云、流场、轨迹、引力源、黑洞、新生星云、记忆地形层、非普通 Obsidian Graph、Search/River/Inspector 交接和 reduced motion。

处理方法：

- 固定 Memory Starfield rebuild 的视觉层和交互层。
- 固定 starfield item 必备字段和 Inspector/proposal handoff。
- 固定 dots-only、nodes-and-edges-only、Obsidian-like、chart-like、missing nebula、missing flow field、missing trajectories、missing gravity、missing lifecycle markers、blank fallback、raw/private hover card 和 ignored reduced motion 为失败条件。
- 使用 `validate:v1.1.6-stage7-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S7P01-001 stage7_phase1_contract_id = memory_starfield_rebuild_contract`
- `PARAM-MA-V116-S7P01-002 stage7_phase1_required_layers = memory_starfield;nebula_field;flow_field;trajectory_trails;gravity_sources;black_hole_core;proto_star_cloud;memory_terrain_layer;cluster_constellations;ambient_depth_particles`
- `PARAM-MA-V116-S7P01-003 stage7_phase1_required_interactions = orbit_pan_zoom;hover_card;click_inspector;focus_cluster;jump_from_search;jump_from_river;presentation_analysis_toggle;keyboard_navigation;reduced_motion`
- `PARAM-MA-V116-S7P01-004 stage7_phase1_required_item_fields = starfield_item_id;item_type;theme_id;theme_label;topic_state;gravity_mass;orbit_radius;trajectory_refs;terrain_value;importance;confidence;evidence_count;evidence_refs;source_scope;linked_river_range;linked_asset_ids;linked_action_ids;inspector_link;proposal_hint`
- `PARAM-MA-V116-S7P01-005 stage7_phase1_failure_conditions = dots_only;nodes_and_edges_only;obsidian_like_graph;chart_like_network;missing_nebula;missing_flow_field;missing_trajectories;missing_gravity_sources;missing_black_hole;missing_proto_star;missing_memory_terrain;missing_inspector_handoff;blank_fallback;raw_private_hover_card;reduced_motion_ignored`
- `PARAM-MA-V116-S7P01-006 stage7_phase1_status = phase_7_1_contract_created_pending_stage_review`
- `PARAM-MA-V116-S7P01-007 stage7_phase1_required_validator = validate:v1.1.6-stage7-phase1`

输出：

- Stage 7 Phase 1 产品合同。
- Stage 7 Phase 1 验收文件。
- Stage 7 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback 或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不导入 experiment 目录，不切换 feature flag default。
- 本 phase 不进入 Stage 7 整体复审，不进入 Stage 8-10，不执行 GitHub main 上传。

## 58. v1.1.6 Stage 7 整体复审门槛

状态：`stage_7_review_passed_pending_github_main_upload`。

模型假设：

- Stage 7 只有在 Phase 7.1 的合同、验收、validator 和记录均一致时，才允许进入 GitHub main upload gate。
- Stage 7 复审通过不等于运行时 UI、浏览器截图、runtime Memory Starfield、真实 WebGL/fallback canvas、Search/River focus handoff 或 agent apply 已完成。
- Stage 7 复审不得读取 raw/private/cookie/session/secret，不得执行 direct writeback，不得进入 Stage 8。

输入：

- `docs/product/memory_starfield_rebuild_contract.md`
- `docs/acceptance/memory_starfield_rebuild_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_6_stage7_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage7_phase1.cjs`

处理方法：

- 检查 Stage 7 Phase 1 合同、验收和 validator 是否覆盖记忆星系重做所需视觉层、交互、字段和失败条件。
- 检查 Stage 7 review artifact 是否覆盖 Phase 7.1、边界、风险和 Stage 8 前上传 gate。
- 检查 delivery、feature、development、model parameter、changelog 和 package script 是否一致。
- 固定 `validate:v1.1.6-stage7` 为 Stage 8 前的必跑 gate。

参数与门槛：

- `PARAM-MA-V116-S7-REVIEW-001 stage7_required_validator = validate:v1.1.6-stage7`
- `PARAM-MA-V116-S7-REVIEW-002 stage7_review_status = stage_7_review_passed_pending_github_main_upload`
- `PARAM-MA-V116-S7-REVIEW-003 stage7_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage7_review.md`
- `PARAM-MA-V116-S7-REVIEW-004 stage7_allowed_change_scope = contracts;acceptance;records;reviews;validators;package_script`
- `PARAM-MA-V116-S7-REVIEW-005 stage7_next_gate = GitHub main upload before Stage 8`
- `PARAM-MA-V116-S7-REVIEW-006 upload_boundary = no_stage8_until_stage7_upload_verified`

输出：

- Stage 7 review artifact。
- Stage 7 stage-level validator。
- Stage 7 review records。

边界：

- 本复审不实现运行时 Memory Starfield。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由或 feature flag。
- 本复审不导入 experiment 目录，不切换 feature flag default。
- 本复审不进入 Stage 8；GitHub main upload 只在 final remote checks 通过后执行。

## 59. v1.1.6 Stage 8 Phase 1 发布、本地 App 与回滚安全参数

状态：`phase_8_1_contract_created_pending_stage_review`。

模型假设：

- Stage 8 必须先冻结发布、本地 App 和回滚安全合同，再允许任何 production build、installer、browser、Cloudflare 或 Access 操作。
- 发布安全必须区分 local pass、offline preflight pass 和 live deploy complete，不能把外部授权缺失包装成完成。
- 本 phase 只定义合同和验收，不运行 installer，不 build，不部署 Cloudflare，不修改 Access policy，不读取 raw/private/cookie/session/secret，不执行 direct writeback。

输入：

- `docs/product/memory_atlas_release_rollback_contract.md`
- `docs/acceptance/memory_atlas_release_rollback_acceptance.md`
- v1.1.5 Stage 8 经验：Local App Packaging、Release Safety、offline Cloudflare Pages + Access preflight、rollback matrix、runtime manifest 和 cleanup guard。

处理方法：

- 固定 local app、runtime manifest、redacted release artifact、Cloudflare preflight、live deploy authorization、rollback matrix、proposal-only writeback 和 cleanup guard。
- 固定 release item 必备字段和 owner gate。
- 固定 stale runtime manifest、stale local app、raw/private release artifact、unauthorized Cloudflare deploy、unauthorized Access policy change、missing rollback path、weakened proposal-only boundary、unclean transient output 和 premature GitHub upload 为失败条件。
- 使用 `validate:v1.1.6-stage8-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S8P01-001 stage8_phase1_contract_id = memory_atlas_release_rollback_contract`
- `PARAM-MA-V116-S8P01-002 stage8_phase1_required_surfaces = local_app_bundle;runtime_manifest;redacted_static_artifact;cloudflare_preflight;live_deploy_authorization_gate;rollback_matrix;proposal_only_writeback_gate;cleanup_guard`
- `PARAM-MA-V116-S8P01-003 stage8_phase1_rollback_matrix = memory_starfield;memory_river;data_map_2_0;search_review_workflows;proposal_queue;local_app_runtime;cloudflare_release`
- `PARAM-MA-V116-S8P01-004 stage8_phase1_required_item_fields = release_item_id;surface;artifact_path;git_commit;snapshot_generated_at;source_scope;build_mode;audit_status;rollback_path;fallback_mode;owner_gate;evidence_refs;risk_level;inspector_link;proposal_hint`
- `PARAM-MA-V116-S8P01-005 stage8_phase1_failure_conditions = stale_runtime_manifest;stale_local_app;raw_private_release_artifact;unauthorized_cloudflare_deploy;unauthorized_access_policy_change;missing_rollback_path;weakened_proposal_only_boundary;unclean_transient_output;premature_github_upload`
- `PARAM-MA-V116-S8P01-006 stage8_phase1_status = phase_8_1_contract_created_pending_stage_review`
- `PARAM-MA-V116-S8P01-007 stage8_phase1_required_validator = validate:v1.1.6-stage8-phase1`

输出：

- Stage 8 Phase 1 产品合同。
- Stage 8 Phase 1 验收文件。
- Stage 8 Phase 1 validator。

边界：

- 本参数段不新增运行时公式，不改变 Memory Atlas scoring、ROI、writeback、部署脚本或数据生成。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不修改核心前端实现、CSS、路由或 feature flag。
- 本 phase 不运行 installer，不执行 production build，不部署 Cloudflare，不修改 Access policy。
- 本 phase 不进入 Stage 8 整体复审，不进入 Stage 9-10，不执行 GitHub main 上传。

## 60. v1.1.6 Stage 8 整体复审门槛

状态：`stage_8_review_passed_pending_github_main_upload`。

模型假设：

- Stage 8 只有在 Phase 8.1 的合同、验收、validator 和记录均一致时，才允许进入 GitHub main upload gate。
- Stage 8 复审通过不等于 production build、本地 App 安装、runtime manifest、release artifact audit、Cloudflare preflight 或 live deploy 已完成。
- Stage 8 复审不得读取 raw/private/cookie/session/secret，不得执行 direct writeback，不得运行 installer/build/deploy，不得进入 Stage 9。

输入：

- `docs/product/memory_atlas_release_rollback_contract.md`
- `docs/acceptance/memory_atlas_release_rollback_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_6_stage8_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage8_phase1.cjs`

处理方法：

- 检查 Stage 8 Phase 1 合同、验收和 validator 是否覆盖本地 App、runtime manifest、redacted static artifact、Cloudflare preflight、授权门槛、rollback matrix、proposal-only gate 和 cleanup guard。
- 检查 Stage 8 review artifact 是否覆盖 Phase 8.1、边界、风险和 Stage 9 前上传 gate。
- 检查 delivery、feature、development、model parameter、changelog 和 package script 是否一致。
- 固定 `validate:v1.1.6-stage8` 为 Stage 9 前的必跑 gate。

参数与门槛：

- `PARAM-MA-V116-S8-REVIEW-001 stage8_required_validator = validate:v1.1.6-stage8`
- `PARAM-MA-V116-S8-REVIEW-002 stage8_review_status = stage_8_review_passed_pending_github_main_upload`
- `PARAM-MA-V116-S8-REVIEW-003 stage8_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage8_review.md`
- `PARAM-MA-V116-S8-REVIEW-004 stage8_allowed_change_scope = contracts;acceptance;records;reviews;validators;package_script`
- `PARAM-MA-V116-S8-REVIEW-005 stage8_next_gate = GitHub main upload before Stage 9`
- `PARAM-MA-V116-S8-REVIEW-006 upload_boundary = no_stage9_until_stage8_upload_verified`

输出：

- Stage 8 review artifact。
- Stage 8 stage-level validator。
- Stage 8 review records。

边界：

- 本复审不实现运行时发布流程。
- 本复审不读取 raw/private/cookie/session/secret 数据。
- 本复审不修改核心前端实现、CSS、路由或 feature flag。
- 本复审不运行 installer，不执行 production build，不部署 Cloudflare，不修改 Access policy。
- 本复审不进入 Stage 9；GitHub main upload 只在 final remote checks 通过后执行。

## 61. v1.1.6 Stage 9 Phase 1 记忆星系 C3 隔离原型参数

状态：`phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review`。

模型假设：

- Stage 9 是 C3 isolated prototype pass，不等于 production integration。
- Phase 9.1 只固定 `memory-starfield-spike` 的独立原型证据、fixture 安全、production isolation 和治理记录。
- 既有 v1.1.5 spike 可作为 v1.1.6 修补包原型基础，但必须补 v1.1.6 continuity、validator 和 no-production-import gate。

输入：

- `apps/memory-atlas/src/experiments/memory-starfield-spike/README.md`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/index.html`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/main.ts`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/fixture.ts`
- `docs/product/memory_starfield_c3_spike_contract.md`
- `docs/acceptance/memory_starfield_c3_spike_acceptance.md`

处理方法：

- 检查 spike 文件是否齐全。
- 检查 main source 是否保留 Three.js、particle LOD、nebula dust、Flow Field、gravity disk、Black Hole、Proto-Star、hover card、reduced motion 和 smoke hook。
- 检查 fixture 是否保持 raw/private、plaintext secrets 和 local absolute paths 标志为 false。
- 检查 production `src` 是否没有引用 `memory-starfield-spike`。
- 使用 `validate:v1.1.6-stage9-phase1` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S9P01-001 stage9_phase1_contract_id = memory_starfield_c3_spike_contract`
- `PARAM-MA-V116-S9P01-002 stage9_phase1_spike_path = apps/memory-atlas/src/experiments/memory-starfield-spike`
- `PARAM-MA-V116-S9P01-003 stage9_phase1_required_features = three_js_canvas;particle_lod;nebula_dust;flow_field;gravity_disk;black_hole_marker;proto_star_marker;memory_terrain_signal;hover_card;smoke_status_hook`
- `PARAM-MA-V116-S9P01-004 stage9_phase1_fixture_safety = rawPrivateDataIncluded:false;plaintextSecretsIncluded:false;localAbsolutePathsIncluded:false`
- `PARAM-MA-V116-S9P01-005 stage9_phase1_isolation_boundary = no_production_import;no_route;no_navigation;no_feature_flag_default;no_direct_writeback`
- `PARAM-MA-V116-S9P01-006 stage9_phase1_required_validator = validate:v1.1.6-stage9-phase1`

输出：

- Stage 9 Phase 1 产品合同。
- Stage 9 Phase 1 验收文件。
- Stage 9 Phase 1 validator。
- Memory Starfield spike README v1.1.6 continuity note。

边界：

- 本 phase 不修改 production Galaxy、路由、导航、feature flag 或 app shell。
- 本 phase 不运行 production build、installer、本地 app install、browser screenshot 或 Cloudflare deploy。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不执行 agent apply。
- 本 phase 不进入 Stage 9 整体复审，不进入 Stage 10，不执行 GitHub main 上传。

## 62. v1.1.6 Stage 9 Phase 2 记忆时间河 C3 隔离原型参数

状态：`phase_9_2_memory_river_c3_spike_ready_pending_stage_review`。

模型假设：

- Stage 9 是 C3 isolated prototype pass，不等于 production integration。
- Phase 9.2 只固定 `memory-river-spike` 的独立原型证据、fixture 安全、production isolation 和治理记录。
- 既有 v1.1.5 spike 可作为 v1.1.6 修补包原型基础，但必须补 v1.1.6 continuity、validator 和 no-production-import gate。

输入：

- `apps/memory-atlas/src/experiments/memory-river-spike/README.md`
- `apps/memory-atlas/src/experiments/memory-river-spike/index.html`
- `apps/memory-atlas/src/experiments/memory-river-spike/main.ts`
- `apps/memory-atlas/src/experiments/memory-river-spike/fixture.ts`
- `docs/product/memory_river_c3_spike_contract.md`
- `docs/acceptance/memory_river_c3_spike_acceptance.md`

处理方法：

- 检查 spike 文件是否齐全。
- 检查 main source 是否保留 D3 UTC scale、zoom、brush、theme lanes、event pulses、Black Hole band、Proto-Star marker、hover card、reduced motion 和 smoke hook。
- 检查 fixture 是否保持 raw/private、plaintext secrets、local absolute paths 和 writeback 标志为 false。
- 检查 production `src` 是否没有引用 `memory-river-spike`。
- 使用 `validate:v1.1.6-stage9-phase2` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S9P02-001 stage9_phase2_contract_id = memory_river_c3_spike_contract`
- `PARAM-MA-V116-S9P02-002 stage9_phase2_spike_path = apps/memory-atlas/src/experiments/memory-river-spike`
- `PARAM-MA-V116-S9P02-003 stage9_phase2_required_features = d3_time_scale;zoom_pan;brush_selection;theme_lanes;black_hole_band;proto_star_marker;event_pulses;hover_card;reduced_motion;smoke_status_hook`
- `PARAM-MA-V116-S9P02-004 stage9_phase2_fixture_safety = rawPrivateDataIncluded:false;plaintextSecretsIncluded:false;localAbsolutePathsIncluded:false;writebackAllowed:false`
- `PARAM-MA-V116-S9P02-005 stage9_phase2_isolation_boundary = no_production_import;no_route;no_navigation;no_feature_flag_default;no_direct_writeback;no_proposal_write`
- `PARAM-MA-V116-S9P02-006 stage9_phase2_required_validator = validate:v1.1.6-stage9-phase2`

输出：

- Stage 9 Phase 2 产品合同。
- Stage 9 Phase 2 验收文件。
- Stage 9 Phase 2 validator。
- Memory River spike README v1.1.6 continuity note。

边界：

- 本 phase 不修改 production Timeline、路由、导航、feature flag 或 app shell。
- 本 phase 不运行 production build、installer、本地 app install、browser screenshot 或 Cloudflare deploy。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 phase 不进入 Stage 9 整体复审，不进入 Stage 10，不执行 GitHub main 上传。

## 68. v1.1.7 Pre Stage 0 Gap Remediation Upgrade Package

状态：`pre_stage_0_review_passed_pending_github_main_upload`。

模型假设：

- v1.1.6 Stage 10 review 是 v1.1.7 的 baseline，不在本 pre-stage 重写。
- v1.1.7 必须先把 Roadmap v2 gap remediation 转成 Stage 0-10 执行映射、
  验收矩阵、no-runtime/no-raw-private/no-direct-writeback 边界和一次性 GitHub
  main 上传 gate。
- Roadmap v2 Stage 11 release/rollback 在用户指定的 Stage 0-10 体系下并入
  Stage 10 final hardening/upload gate，除非后续 owner decision 重新拆分。

输入：

- `docs/product/memory_atlas_v1_1_7_gap_remediation_upgrade_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_pre_stage0_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_7_pre_stage0_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_pre_stage0.cjs`
- `docs/reviews/memory_atlas_v1_1_6_stage10_review.md`

处理方法：

- 检查 v1.1.7 pre-stage 合同是否覆盖 Roadmap v2 gap remediation source、Stage
  0-10 stage map、required acceptance matrix、non-goals、rollback 和 one-time
  upload gate。
- 检查 acceptance 文件是否明确 deferred proof 和 no-runtime/no-raw-private 边界。
- 检查 review artifact、delivery、feature、development、model parameter、
  changelog 和 package script 是否登记 `MA-V117-PRESTAGE0` 与
  `ACC-MA-V117-PRESTAGE0`。
- 检查当前改动范围是否只包含 pre-stage 合同、验收、review、validator、package
  script 和记录。
- 使用 `validate:v1.1.7-pre-stage0` 固定本 pre-stage 边界。

参数与门槛：

- `PARAM-MA-V117-PRESTAGE0-001 pre_stage0_contract_id = memory_atlas_v1_1_7_gap_remediation_upgrade_contract`
- `PARAM-MA-V117-PRESTAGE0-002 pre_stage0_status = pre_stage_0_review_passed_pending_github_main_upload`
- `PARAM-MA-V117-PRESTAGE0-003 pre_stage0_required_surfaces = Chinese readability;Usage path;Suggested actions;Tier assets;Topic categories;Proposal-only editing;Search 2.0;Review workflow;Summary iteration;Data Map 2.0;Memory River;Memory Starfield;Safety;Performance;Rollback`
- `PARAM-MA-V117-PRESTAGE0-004 pre_stage0_stage_map = Pre Stage 0;Stage 0;Stage 1;Stage 2;Stage 3;Stage 4;Stage 5;Stage 6;Stage 7;Stage 8;Stage 9;Stage 10`
- `PARAM-MA-V117-PRESTAGE0-005 pre_stage0_allowed_change_scope = product_contract;acceptance;review;validator;package_script;records`
- `PARAM-MA-V117-PRESTAGE0-006 pre_stage0_required_validator = validate:v1.1.7-pre-stage0`
- `PARAM-MA-V117-PRESTAGE0-007 pre_stage0_upload_boundary = one_time_github_main_upload_after_validation_clean_tree_fetch_and_canonical_remote`

输出：

- v1.1.7 pre-stage product contract。
- v1.1.7 pre-stage acceptance checklist。
- v1.1.7 pre-stage review artifact。
- v1.1.7 pre-stage deterministic validator。
- v1.1.7 pre-stage governance records。

边界：

- 本 pre-stage 不修改 production UI、CSS、路由、导航、feature flag 或 app shell。
- 本 pre-stage 不运行 production build、installer、本地 app install、browser
  screenshot 或 Cloudflare deploy。
- 本 pre-stage 不修改 Access policy。
- 本 pre-stage 不读取 raw/private/cookie/session/secret 数据。
- 本 pre-stage 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 pre-stage 不执行 Stage 0 implementation。
- 本 pre-stage review artifact 不执行 GitHub main 上传。

## 69. v1.1.7 Stage 0 Phase 0.1 Chinese Display Foundation

状态：`phase_0_1_chinese_display_foundation_completed_pending_stage0_review`。

验收 ID：`ACC-MA-V117-S0P01`。

模型假设：

- Stage 0 Phase 0.1 只建立中文显示基础，不证明截图验收、Help 面板、空状态工作流或 Stage 0 整体复审。
- 中文 copy registry 先覆盖 app shell、navigation、filters、states、overview、Inspector 和 proposal 的关键路径，后续 phase 可继续迁移其余硬编码文案。
- UTF-8 scan 是静态 gate，不替代浏览器截图。

输入：

- `apps/memory-atlas/src/i18n/types.ts`
- `apps/memory-atlas/src/i18n/zh-CN.ts`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_atlas_v1_1_7_stage0_phase1_chinese_display_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage0_phase1_chinese_display_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase1.cjs`

处理方法：

- 扫描 selected Memory Atlas text surfaces，确认无 U+FFFD、common mojibake、null bytes、trailing whitespace 和 invalid JSON。
- 检查 `ChineseUiCopy` 类型和 `zhCNCopy` registry 是否覆盖必备组。
- 检查 `App.tsx` 是否在 navigation、filters、load state、overview、Inspector 和 proposal 关键路径使用 registry。
- 检查 `styles.css` 是否包含中文字体 fallback 和长文本布局容错。
- 使用 `validate:v1.1.7-stage0-phase1` 固定本 phase 边界。

参数与门槛：

- `PARAM-MA-V117-S0P01-001 stage0_phase1_contract_id = memory_atlas_v1_1_7_stage0_phase1_chinese_display_contract`
- `PARAM-MA-V117-S0P01-002 stage0_phase1_status = phase_0_1_chinese_display_foundation_completed_pending_stage0_review`
- `PARAM-MA-V117-S0P01-003 stage0_phase1_registry_groups = app;navigation;metrics;filters;states;overview;inspector;proposal`
- `PARAM-MA-V117-S0P01-004 stage0_phase1_text_scan_scope = apps/memory-atlas/src;docs/product;docs/acceptance;config/visualization;data/derived/visualization/memory_atlas.json;records`
- `PARAM-MA-V117-S0P01-005 stage0_phase1_layout_tolerance = Chinese font fallback;overflow-wrap:anywhere;word-break:normal;line-break:loose;min-width:0`
- `PARAM-MA-V117-S0P01-006 stage0_phase1_required_validator = validate:v1.1.7-stage0-phase1`

输出：

- Stage 0 Phase 0.1 product contract。
- Stage 0 Phase 0.1 acceptance checklist。
- Chinese UI copy registry。
- Stage 0 Phase 0.1 deterministic validator。

## 70. v1.1.7 Stage 0 Phase 0.2 Usage Help And Empty/Error States

状态：`phase_0_2_usage_help_completed_pending_stage0_review`。

验收 ID：`ACC-MA-V117-S0P02`。

模型假设：

- Stage 0 Phase 0.2 只解决系统使用说明和关键空错态，不证明截图验收、真实
  WebGL 失败模拟、Stage 0.3 明细字段合同或 Stage 0 整体复审。
- Help 面板先覆盖 3 分钟使用路径、Presentation / Analysis、Inspector、
  Proposal-only 和 Search Review 关键读法。
- 空错态覆盖 empty-atlas、no-filtered-results、load-failed、webgl-unavailable
  和 proposal-not-writable；它们解释下一步，但不自动写 memory 或 proposal。

输入：

- `apps/memory-atlas/src/components/help/MemoryAtlasHelpPanel.tsx`
- `apps/memory-atlas/src/components/EmptyState.tsx`
- `apps/memory-atlas/src/components/ErrorState.tsx`
- `apps/memory-atlas/src/i18n/types.ts`
- `apps/memory-atlas/src/i18n/zh-CN.ts`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/GalaxyScene.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/product/memory_atlas_v1_1_7_stage0_phase2_usage_help_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage0_phase2_usage_help_acceptance.md`
- `docs/product/memory_atlas_usage_guide.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase2.cjs`

处理方法：

- 检查 Help panel 是否含 3-minute path、读法说明和 workflow notes。
- 检查 ViewRouter 是否覆盖 empty atlas、no filtered results 和 load failed。
- 检查 GalaxyScene 是否给 WebGL unavailable 中文恢复路径。
- 检查 proposal 不可写时是否解释 writeback policy 不满足安全条件。
- 使用 `validate:v1.1.7-stage0-phase2` 固定本 phase 边界。

参数与门槛：

- `PARAM-MA-V117-S0P02-001 stage0_phase2_contract_id = memory_atlas_v1_1_7_stage0_phase2_usage_help_contract`
- `PARAM-MA-V117-S0P02-002 stage0_phase2_status = phase_0_2_usage_help_completed_pending_stage0_review`
- `PARAM-MA-V117-S0P02-003 stage0_phase2_usage_path = 看状态;看建议;看证据;调整 proposal;搜索复盘;导出或回滚`
- `PARAM-MA-V117-S0P02-004 stage0_phase2_state_cases = empty-atlas;no-filtered-results;load-failed;webgl-unavailable;proposal-not-writable`
- `PARAM-MA-V117-S0P02-005 stage0_phase2_help_modes = Presentation;Analysis;Inspector;Proposal-only;Search Review`
- `PARAM-MA-V117-S0P02-006 stage0_phase2_text_scan_scope = apps/memory-atlas/src;docs/product;docs/acceptance;package.json;records`
- `PARAM-MA-V117-S0P02-007 stage0_phase2_required_validator = validate:v1.1.7-stage0-phase2`

输出：

- Stage 0 Phase 0.2 product contract。
- Stage 0 Phase 0.2 acceptance checklist。
- Memory Atlas usage guide。
- Help panel and empty/error state components。
- Stage 0 Phase 0.2 deterministic validator。

边界：

- 本 phase 不实现 Stage 0.3 明细字段合同、Stage 1 schema 或运行时数据模型。
- 本 phase 不运行 production build、本地 app install、browser screenshot 或 Cloudflare deploy。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 phase 不执行 GitHub main 上传。

## 71. v1.1.7 Stage 0 Phase 0.3 Detail Visibility Field Contract

状态：`phase_0_3_detail_visibility_contract_completed_pending_stage0_review`。

验收 ID：`ACC-MA-V117-S0P03`。

模型假设：

- Stage 0 Phase 0.3 只定义字段合同，不实现运行时明细工作台、生成器、数据
  schema、Search 2.0、Review workflow 或截图验收。
- 三类明细对象必须统一说明 required field、source、display surface 和 edit
  permission，避免后续实现阶段猜字段含义。
- 可修改字段只能进入 proposal-only 层；合同不得允许前端直接修改 active memory、
  source snapshot、模型参数或证据引用。

输入：

- `docs/product/detail_visibility_contract.md`
- `docs/acceptance/memory_atlas_v1_1_7_stage0_phase3_detail_visibility_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase3.cjs`

处理方法：

- 检查 `suggested_action_detail` 是否覆盖 reason、ROI、effort、urgency、
  evidence、next step、linked topics/assets、proposal hint 和 rollback hint。
- 检查 `tier_asset_detail` 是否覆盖 core profile、project、decision、workflow、
  knowledge、opportunity、stale 资产层级，以及 importance、priority、confidence、
  staleness、evidence 和 recommended action。
- 检查 `topic_classification_detail` 是否覆盖 strength、trend、confidence、
  record_count、evidence_count、linked assets/actions、starfield/river handoff 和
  recommended action。
- 检查字段表是否包含 source、display surface 和 edit permission。
- 使用 `validate:v1.1.7-stage0-phase3` 固定本 phase 边界。

参数与门槛：

- `PARAM-MA-V117-S0P03-001 stage0_phase3_contract_id = memory_atlas_v1_1_7_stage0_phase3_detail_visibility_contract`
- `PARAM-MA-V117-S0P03-002 stage0_phase3_status = phase_0_3_detail_visibility_contract_completed_pending_stage0_review`
- `PARAM-MA-V117-S0P03-003 stage0_phase3_detail_objects = suggested_action_detail;tier_asset_detail;topic_classification_detail`
- `PARAM-MA-V117-S0P03-004 stage0_phase3_field_dimensions = field;required;source;display_surface;edit_permission;fallback_policy;evidence_policy`
- `PARAM-MA-V117-S0P03-005 stage0_phase3_edit_permissions = read_only;proposal_only;system_generated;no_direct_writeback`
- `PARAM-MA-V117-S0P03-006 stage0_phase3_required_validator = validate:v1.1.7-stage0-phase3`

输出：

- Stage 0 Phase 0.3 detail visibility field contract。
- Stage 0 Phase 0.3 acceptance checklist。
- Stage 0 Phase 0.3 deterministic validator。

边界：

- 本 phase 不实现运行时 UI、CSS、数据生成、Search 2.0、Review workflow、Data Map
  2.0、Memory River 或 Memory Starfield。
- 本 phase 不运行 production build、本地 app install、browser screenshot 或 Cloudflare deploy。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 phase 不执行 GitHub main 上传。

## 72. v1.1.7 Stage 0 Review

状态：`stage_0_review_passed_pending_stage1_no_github_main_upload`。

验收 ID：`ACC-MA-V117-S0-REVIEW`。

模型假设：

- Stage 0 review 只证明 Phase 0.1/0.2/0.3 的合同、运行时轻量修复、validator 和
  记录链一致，不证明 Stage 1-8。
- Stage 0 review 不执行 GitHub main 上传；上传必须等整个 Stage 0-8 项目完成后走最终 gate。
- Stage 0 review 不进入 Stage 1，不读取 raw/private，不写 proposal，不执行 agent apply。

输入：

- `docs/reviews/memory_atlas_v1_1_7_stage0_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase1.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase2.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage0_phase3.cjs`

处理方法：

- 执行 Phase 0.1/0.2/0.3 validator chain。
- 检查 Stage 0 review artifact 是否包含 phase coverage、validation、boundaries、
  remaining risks 和 next gate。
- 检查 records 是否登记 `MA-V117-S0-REVIEW`、`ACC-MA-V117-S0-REVIEW`、
  `stage_0_review_passed_pending_stage1_no_github_main_upload` 和
  `validate:v1.1.7-stage0`。
- 检查 canonical remote 和 sparse checkout boundary。

参数与门槛：

- `PARAM-MA-V117-S0-REVIEW-001 stage0_review_status = stage_0_review_passed_pending_stage1_no_github_main_upload`
- `PARAM-MA-V117-S0-REVIEW-002 stage0_review_required_validator = validate:v1.1.7-stage0`
- `PARAM-MA-V117-S0-REVIEW-003 stage0_review_phase_validators = validate:v1.1.7-stage0-phase1;validate:v1.1.7-stage0-phase2;validate:v1.1.7-stage0-phase3`
- `PARAM-MA-V117-S0-REVIEW-004 stage0_review_next_gate = Stage 1 one phase per run`
- `PARAM-MA-V117-S0-REVIEW-005 stage0_review_upload_boundary = no_github_main_upload_before_whole_stage_0_to_8_completion`

输出：

- Stage 0 review artifact。
- Stage 0 deterministic validator。
- Stage 0 review package script。

边界：

- 本 review 不进入 Stage 1。
- 本 review 不实现运行时 UI、CSS、数据生成、Search 2.0、Review workflow、Data Map
  2.0、Memory River 或 Memory Starfield。
- 本 review 不运行 production build、本地 app install、browser screenshot 或 Cloudflare deploy。
- 本 review 不读取 raw/private/cookie/session/secret 数据。
- 本 review 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 review 不执行 GitHub main 上传。

## 73. v1.1.7 Stage 1 Phase 1.1 Universe State Schema

状态：`phase_1_1_universe_state_schema_completed_pending_stage1_review`。

验收 ID：`ACC-MA-V117-S1P01`。

模型假设：

- `universe_state_snapshot.v1` 可以继续作为 v1.1.7 Stage 1 的共享状态版本；
  本 phase 只扩展 consumer_map，不改评分公式。
- Roadmap v2 后续 Data Map、Search、Review/Summary/Iteration 必须从同一份
  Universe State 派生，避免每个页面各自计算事实。
- 所有 recommended next actions 仍是 proposal-only，不表示前端或 agent 可以直接写
  active memory。

输入：

- `docs/architecture/universe_state_snapshot.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/src/models/universeState.ts`
- `apps/memory-atlas/src/fixtures/universe_state.schema.json`
- `apps/memory-atlas/src/fixtures/universe_state.sample.json`
- `docs/acceptance/memory_atlas_v1_1_7_stage1_phase1_universe_state_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase1.cjs`

处理方法：

- 扩展 Universe State `consumer_map`，新增 `data_map_2_0`、`search_2_0` 和
  `review_summary_iteration`。
- 保留既有 `memory_overview`、`memory_starfield`、`memory_river`、`inspector`
  和 `roi_dashboard` 映射。
- 使用 `validate:universe-state-spike` 证明 deterministic sample 与 generator 输出一致。
- 使用 `validate:v1.1.7-stage1-phase1` 检查 schema、sample、model、参数模板、
  acceptance、records、proposal-only 和 privacy false gate。

参数与门槛：

- `PARAM-MA-V117-S1P01-001 stage1_phase1_status = phase_1_1_universe_state_schema_completed_pending_stage1_review`
- `PARAM-MA-V117-S1P01-002 stage1_phase1_required_validator = validate:v1.1.7-stage1-phase1`
- `PARAM-MA-V117-S1P01-003 stage1_phase1_state_fields = memory_weather;dominant_clusters;rising_clusters;declining_clusters;conflict_zones;black_holes;proto_stars;stale_orbits;memory_terrain;river_pulse;mini_starfield;recommended_next_actions`
- `PARAM-MA-V117-S1P01-004 stage1_phase1_consumer_map = memory_overview;memory_starfield;memory_river;data_map_2_0;search_2_0;review_summary_iteration;inspector;roi_dashboard`
- `PARAM-MA-V117-S1P01-005 stage1_phase1_proposal_boundary = recommended_next_actions.proposal_only=true;no_direct_writeback`
- `PARAM-MA-V117-S1P01-006 stage1_phase1_deferred_work = Phase 1.2 suggested_action_detail;Phase 1.3 tier_asset_detail;Phase 1.4 topic_classification_detail;Stage 2 proposal editor;Stage 7 Search 2.0 UI;Stage 8 summary proposal export`

输出：

- v1.1.7 Universe State architecture addendum。
- v1.1.7 Universe State parameter gate。
- Updated deterministic Universe State sample and schema.
- Stage 1 Phase 1.1 acceptance and validator。

边界：

- 本 phase 不进入 Phase 1.2，不实现 Action Detail Drawer。
- 本 phase 不实现 tier asset、topic classification、proposal editor、Search 2.0
  runtime UI、Review workflow、Data Map production UI 或 Summary proposal export。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 phase 不运行 browser screenshot、production build、本地 app install、deploy 或
  GitHub main 上传。

## 74. v1.1.7 Stage 1 Phase 1.2 Next Action Detail

状态：`phase_1_2_next_action_detail_completed_pending_stage1_review`。

验收 ID：`ACC-MA-V117-S1P02`。

模型假设：

- Next Action 只从已筛选的 redacted atlas nodes、graph edges 和 delta stats 派生；
  本 phase 不读取 raw/private/cookie/session/secret。
- `nextActionSortScore` 是展示排序启发式，不是长期记忆写回公式。
- Action Detail Drawer 是只读解释层；任何重要性、优先级或状态调整仍必须进入后续
  proposal-only 工作区。

输入：

- `docs/architecture/next_action_model.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/ActionDetailDrawer.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/acceptance/memory_atlas_v1_1_7_stage1_phase2_next_action_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase2.cjs`

处理方法：

- 使用 `buildNextActionDetails` 生成最多 Top 5 Next Action。
- 使用 `nextActionSortScore = roi_score * 0.40 + urgency_score * 0.25 +
  confidence * 0.25 - effort_penalty * 0.10` 排序。
- 在 Home Overview card 上显示 priority、title、reason、`roi_score`、effort
  cost、`urgency`、evidence count 和 next step。
- 点击 card 后打开 Action Detail Drawer，展示 source、status、evidence_refs、
  matched_reason、linked_topic_ids、linked_asset_ids、proposal_hint、rollback_hint
  和 `proposal_only`。
- 使用 `validate:v1.1.7-stage1-phase2` 检查模型、实现、样式、记录和改动范围。

参数与门槛：

- `PARAM-MA-V117-S1P02-001 stage1_phase2_status = phase_1_2_next_action_detail_completed_pending_stage1_review`
- `PARAM-MA-V117-S1P02-002 stage1_phase2_required_validator = validate:v1.1.7-stage1-phase2`
- `PARAM-MA-V117-S1P02-003 next_action_required_fields = action_id;title;action_type;reason;roi_score;effort_cost;urgency;confidence;source;status;evidence_count;evidence_refs;matched_reason;linked_topic_ids;linked_asset_ids;next_step;recommended_time_window;proposal_hint;rollback_hint;proposal_only`
- `PARAM-MA-V117-S1P02-004 next_action_sort_weights = roi_weight=0.40;urgency_weight=0.25;confidence_weight=0.25;effort_penalty_weight=0.10`
- `PARAM-MA-V117-S1P02-005 next_action_top_limit = Top 5`
- `PARAM-MA-V117-S1P02-006 action_detail_drawer_fields = reason;roi_score;effort_cost;urgency;source;evidence_refs;status;linked_topic_ids;linked_asset_ids;next_step;proposal_hint;rollback_hint;proposal_only`
- `PARAM-MA-V117-S1P02-007 stage1_phase2_deferred_work = Phase 1.3 tier_asset_detail;Phase 1.4 topic_classification_detail;Stage 2 proposal editor;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

输出：

- Next Action model contract。
- Action Detail Drawer runtime component。
- Home Overview Top 5 Next Action cards。
- Stage 1 Phase 1.2 acceptance and validator。

边界：

- 本 phase 不进入 Phase 1.3，不实现 tier asset detail。
- 本 phase 不进入 Phase 1.4，不实现 topic classification detail。
- 本 phase 不写 proposal，不直接写 active memory，不执行 agent apply。
- 本 phase 不运行 browser screenshot、production build、本地 app install、deploy 或
  GitHub main 上传。

## 75. v1.1.7 Stage 1 Phase 1.3 Level Asset Detail

状态：`phase_1_3_tier_asset_detail_completed_pending_stage1_review`。

验收 ID：`ACC-MA-V117-S1P03`。

模型假设：

- Level Asset 只从已筛选的 redacted atlas nodes、graph edges、Next Action map
  和 Universe State 派生；本 phase 不读取 raw/private/cookie/session/secret。
- `tierAssetSortScore` 是展示排序启发式，不是长期记忆写回公式。
- AssetDetailPanel 是只读解释层；任何资产层级、重要性、优先级或状态调整仍必须进入后续
  proposal-only 工作区。

输入：

- `docs/architecture/level_asset_model.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/AssetDetailPanel.tsx`
- `apps/memory-atlas/src/styles.css`
- `docs/acceptance/memory_atlas_v1_1_7_stage1_phase3_tier_asset_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_stage1_phase3.cjs`

处理方法：

- 使用 `buildTierAssetDetails` 生成最多 Top 7 Level Asset。
- 使用 `tierAssetSortScore = value_score * 0.35 + importance_score * 0.25 +
  confidence * 0.25 - staleness_penalty * 0.15` 排序。
- 在 Home Overview card 上显示 asset_tier、title、theme、`value_score`、
  importance、`staleness_status`、evidence count 和 recommended asset action。
- 点击 card 后打开 AssetDetailPanel，展示 summary、source_scope、linked_action_ids、
  linked_topic_ids、last_seen_range、updated_at、evidence_refs、proposal_hint、
  rollback_hint 和 `proposal_only`。
- 使用 `validate:v1.1.7-stage1-phase3` 检查模型、实现、样式、记录和改动范围。

参数与门槛：

- `PARAM-MA-V117-S1P03-001 stage1_phase3_status = phase_1_3_tier_asset_detail_completed_pending_stage1_review`
- `PARAM-MA-V117-S1P03-002 stage1_phase3_required_validator = validate:v1.1.7-stage1-phase3`
- `PARAM-MA-V117-S1P03-003 level_asset_required_fields = asset_id;asset_tier;title;summary;theme;value_score;updated_at;importance;priority;confidence;staleness_status;last_seen_range;evidence_count;evidence_refs;source_scope;linked_action_ids;linked_topic_ids;recommended_asset_action;proposal_hint;rollback_hint;proposal_only`
- `PARAM-MA-V117-S1P03-004 tier_asset_sort_weights = value_weight=0.35;importance_weight=0.25;confidence_weight=0.25;staleness_penalty_weight=0.15`
- `PARAM-MA-V117-S1P03-005 tier_asset_top_limit = Top 7`
- `PARAM-MA-V117-S1P03-006 asset_detail_panel_fields = summary;theme;value_score;updated_at;importance;priority;confidence;staleness_status;last_seen_range;evidence_refs;source_scope;linked_action_ids;linked_topic_ids;recommended_asset_action;proposal_hint;rollback_hint;proposal_only`
- `PARAM-MA-V117-S1P03-007 stage1_phase3_deferred_work = Phase 1.4 topic_classification_detail;Stage 2 proposal editor;Search 2.0;Review workflow;Data Map 2.0;browser screenshot;final app reinstall;GitHub main upload`

输出：

- Level Asset model contract。
- AssetDetailPanel runtime component。
- Home Overview Level Asset cards。
- Stage 1 Phase 1.3 acceptance and validator。

边界：

- 本 phase 不进入 Phase 1.4，不实现 topic classification detail。
- 本 phase 不写 proposal，不直接写 active memory，不执行 agent apply。
- 本 phase 不运行 browser screenshot、production build、本地 app install、deploy 或
  GitHub main 上传。

## 64. v1.1.6 Stage 9 Phase 4 Universe State Fixture Continuity 参数

状态：`phase_9_4_universe_state_fixture_continuity_ready_pending_stage_review`。

模型假设：

- Stage 9 是 C3 isolated prototype pass，不等于 production integration。
- Phase 9.4 固定既有 Universe State generator spike 的 fixture continuity，不改 score formula、parameter YAML、input fixture、sample 或 schema。
- Universe State fixture 必须继续为 Overview、Starfield、River、Data Map、Inspector 和 ROI 提供 redacted shared semantic state。

输入：

- `apps/memory-atlas/src/experiments/universe-state-generator-spike/README.md`
- `apps/memory-atlas/src/models/universeState.ts`
- `apps/memory-atlas/src/utils/universeStateScores.ts`
- `apps/memory-atlas/src/fixtures/universe_state.input.fixture.json`
- `apps/memory-atlas/src/fixtures/universe_state.sample.json`
- `apps/memory-atlas/src/fixtures/universe_state.schema.json`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/scripts/validate_universe_state_spike.mjs`
- `docs/product/universe_state_fixture_continuity_contract.md`
- `docs/acceptance/universe_state_fixture_continuity_acceptance.md`

处理方法：

- 检查 Universe State 文件是否齐全。
- 运行 `validate:universe-state-spike` 验证 deterministic sample、schema、score functions、parameter drift 和 privacy scan。
- 检查 input fixture 和 sample 是否保持 raw/private、plaintext secrets、local absolute paths 和 writeback 标志为 false。
- 检查 sample 是否保留 memory_weather、dominant/rising/declining/conflict、black_holes、proto_stars、stale_orbits、memory_terrain、river_pulse、mini_starfield、recommended_next_actions、consumer_map 和 diagnostics。
- 检查 generated next actions 是否保持 `proposal_only=true`。
- 检查 production `src` 是否没有引用 `experiments/universe-state-generator-spike`。
- 使用 `validate:v1.1.6-stage9-phase4` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S9P04-001 stage9_phase4_contract_id = universe_state_fixture_continuity_contract`
- `PARAM-MA-V116-S9P04-002 stage9_phase4_fixture_surface = universeState.ts;universeStateScores.ts;universe_state.input.fixture.json;universe_state.sample.json;universe_state.schema.json;model_parameters.universe_state.yaml;validate_universe_state_spike.mjs`
- `PARAM-MA-V116-S9P04-003 stage9_phase4_required_features = redacted_fixture_adapter;deterministic_sample_generation;schema_validation;parameter_drift_gate;black_hole_score;proto_star_score;stale_score;memory_weather;memory_terrain;river_pulse;mini_starfield;consumer_map;proposal_only_actions;privacy_status`
- `PARAM-MA-V116-S9P04-004 stage9_phase4_fixture_safety = rawPrivateDataIncluded:false;plaintextSecretsIncluded:false;localAbsolutePathsIncluded:false;writebackAllowed:false;proposalOnly:true`
- `PARAM-MA-V116-S9P04-005 stage9_phase4_isolation_boundary = no_production_experiment_import;no_route;no_navigation;no_feature_flag_default;no_direct_writeback;no_proposal_write`
- `PARAM-MA-V116-S9P04-006 stage9_phase4_required_validator = validate:v1.1.6-stage9-phase4;validate:universe-state-spike`

输出：

- Stage 9 Phase 4 产品合同。
- Stage 9 Phase 4 验收文件。
- Stage 9 Phase 4 validator。
- Universe State generator spike README v1.1.6 continuity note。

边界：

- 本 phase 不修改 production app shell、路由、导航、feature flag 或 runtime UI。
- 本 phase 不修改 Universe State score formula、parameter YAML、input fixture、sample 或 schema。
- 本 phase 不运行 production build、installer、本地 app install、browser screenshot 或 Cloudflare deploy。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 phase 不进入 Stage 9 整体复审，不进入 Stage 10，不执行 GitHub main 上传。

## 65. v1.1.6 Stage 9 整体复审门槛

状态：`stage_9_review_passed_pending_github_main_upload`。

模型假设：

- Stage 9 是 C3 isolated prototype pass，不等于 production integration。
- Stage 9 复审通过只表示四个 C3 原型 phase 与 Universe State fixture
  continuity 已被 deterministic validator 和 review artifact 固定。
- Stage 9 复审不替换 production Galaxy、Timeline、Data Map 或 shared-state
  runtime integration。

输入：

- `docs/product/memory_starfield_c3_spike_contract.md`
- `docs/product/memory_river_c3_spike_contract.md`
- `docs/product/data_map_c3_spike_contract.md`
- `docs/product/universe_state_fixture_continuity_contract.md`
- `docs/reviews/memory_atlas_v1_1_6_stage9_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage9.cjs`

处理方法：

- 检查 Stage 9 Phase 1-4 合同、验收和 validator 是否齐全。
- 检查 production `src` 是否没有引用 Stage 9 isolated experiments。
- 检查 review artifact、delivery、feature、development、model parameter、
  changelog 和 package script 是否一致。
- 使用 `validate:v1.1.6-stage9` 固定 review artifact、记录、改动范围和
  GitHub main 上传前边界。

参数与门槛：

- `PARAM-MA-V116-S9-REVIEW-001 stage9_required_validator = validate:v1.1.6-stage9`
- `PARAM-MA-V116-S9-REVIEW-002 stage9_review_status = stage_9_review_passed_pending_github_main_upload`
- `PARAM-MA-V116-S9-REVIEW-003 stage9_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage9_review.md`
- `PARAM-MA-V116-S9-REVIEW-004 stage9_allowed_change_scope = records;reviews;validators;package_script`
- `PARAM-MA-V116-S9-REVIEW-005 stage9_next_gate = GitHub main upload before Stage 10`
- `PARAM-MA-V116-S9-REVIEW-006 upload_boundary = no_stage10_until_stage9_upload_verified`

输出：

- Stage 9 review artifact。
- Stage 9 stage-level validator。
- Stage 9 review package script。
- Stage 9 review governance records。

边界：

- 本 review 不修改 production UI、CSS、路由、导航、feature flag 或 app shell。
- 本 review 不导入 experiment 到 app shell。
- 本 review 不修改 Universe State score formula、parameter YAML、input fixture、
  sample 或 schema。
- 本 review 不运行 production build、installer、本地 app install、browser screenshot
  或 Cloudflare deploy。
- 本 review 不读取 raw/private/cookie/session/secret 数据。
- 本 review 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 review 不进入 Stage 10，不执行 GitHub main 上传。

## 66. v1.1.6 Stage 10 Phase 1 Final Acceptance Readiness 参数

状态：`phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review`。

模型假设：

- Stage 10 必须在 Stage 9 上传验证完成后开始。
- Phase 10.1 只建立最终验收 readiness 合同，不执行 Stage 10 整体复审。
- 最终验收必须把 Roadmap v2 的可用性、解释性、可修改性、中文可读性、搜索复盘、Data Map、Memory River、Memory Starfield、隐私和上传边界收束到同一 evidence matrix。

输入：

- `docs/product/memory_atlas_final_acceptance_readiness_contract.md`
- `docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10_phase1.cjs`
- Stage 0-9 validators and records

处理方法：

- 检查最终验收 readiness 合同是否覆盖 roadmap v2 final acceptance、validator chain、visual evidence、release safety、privacy/writeback、upload readiness 和 governance sync。
- 检查 acceptance 文件是否说明本 phase 只证明合同与记录一致，不证明最终视觉、浏览器截图、local app packaging、production build、Cloudflare preflight 或 Stage 10 review 完成。
- 检查 package script、delivery、feature、development、model parameter 和 changelog 是否登记 `MA-V116-S10P01`。
- 检查当前改动范围是否只包含 Stage 10 Phase 1 合同、验收、validator、package script 和记录。
- 使用 `validate:v1.1.6-stage10-phase1` 固定本 phase 边界。

参数与门槛：

- `PARAM-MA-V116-S10P01-001 stage10_phase1_contract_id = memory_atlas_final_acceptance_readiness_contract`
- `PARAM-MA-V116-S10P01-002 stage10_phase1_status = phase_10_1_final_acceptance_readiness_contract_created_pending_stage_review`
- `PARAM-MA-V116-S10P01-003 stage10_phase1_required_surfaces = roadmap_v2_final_acceptance_matrix;validator_chain;visual_evidence_matrix;release_safety_matrix;privacy_writeback_matrix;upload_readiness_matrix;governance_sync_matrix`
- `PARAM-MA-V116-S10P01-004 stage10_phase1_required_validator = validate:v1.1.6-stage10-phase1`
- `PARAM-MA-V116-S10P01-005 stage10_phase1_allowed_change_scope = records;product_contract;acceptance_contract;validator;package_script`
- `PARAM-MA-V116-S10P01-006 stage10_phase1_entry_condition = stage9_upload_verified_and_origin_main_included`
- `PARAM-MA-V116-S10P01-007 stage10_phase1_next_gate = Stage 10 review`

输出：

- Stage 10 Phase 1 final acceptance readiness contract。
- Stage 10 Phase 1 acceptance file。
- Stage 10 Phase 1 deterministic validator。
- Stage 10 Phase 1 governance records。

边界：

- 本 phase 不修改 production UI、CSS、路由、导航、feature flag 或 app shell。
- 本 phase 不运行 production build、installer、本地 app install、browser screenshot
  或 Cloudflare deploy。
- 本 phase 不修改 Access policy。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 phase 不执行 Stage 10 整体复审，不执行 GitHub main 上传。

## 67. v1.1.6 Stage 10 整体复审门槛

状态：`stage_10_review_passed_pending_github_main_upload`。

模型假设：

- Stage 10 Phase 1 readiness 合同已经完成。
- Stage 10 整体复审必须复跑 `validate:whole-project`，把最终验收 readiness 的七类 surface 转化为可验证 evidence gate。
- Stage 10 review 通过不等于 GitHub main 上传已经执行。

输入：

- `docs/product/memory_atlas_final_acceptance_readiness_contract.md`
- `docs/acceptance/memory_atlas_final_acceptance_readiness_acceptance.md`
- `docs/reviews/memory_atlas_v1_1_6_stage10_review.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10_phase1.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_1_6_stage10.cjs`
- `apps/memory-atlas/scripts/validate_memory_atlas_whole_project.cjs`

处理方法：

- 检查 Stage 10 Phase 1 readiness 合同、验收、validator 和记录是否一致。
- 执行 `validate:whole-project`，确认 production build、unittest、visual acceptance、release audit、overall acceptance、offline Cloudflare preflight、roadmap final acceptance coverage、canonical remote 和 upload boundary 均通过。
- 检查 Stage 10 review artifact、delivery、feature、development、model parameter、changelog 和 package script 是否登记 `MA-V116-S10-REVIEW`。
- 检查当前改动范围是否只包含 Stage 10 review artifact、validator、package script 和记录。
- 使用 `validate:v1.1.6-stage10` 固定本 review 边界。

参数与门槛：

- `PARAM-MA-V116-S10-REVIEW-001 stage10_required_validator = validate:v1.1.6-stage10`
- `PARAM-MA-V116-S10-REVIEW-002 stage10_review_status = stage_10_review_passed_pending_github_main_upload`
- `PARAM-MA-V116-S10-REVIEW-003 stage10_review_artifact = docs/reviews/memory_atlas_v1_1_6_stage10_review.md`
- `PARAM-MA-V116-S10-REVIEW-004 stage10_required_whole_project_gate = validate:whole-project`
- `PARAM-MA-V116-S10-REVIEW-005 stage10_allowed_change_scope = records;reviews;validators;package_script`
- `PARAM-MA-V116-S10-REVIEW-006 stage10_next_gate = final GitHub main upload gate`
- `PARAM-MA-V116-S10-REVIEW-007 upload_boundary = no_github_main_upload_in_stage10_review`

输出：

- Stage 10 review artifact。
- Stage 10 stage-level validator。
- Stage 10 review package script。
- Stage 10 review governance records。

边界：

- 本 review 不新增 production runtime feature work。
- 本 review 不修改 production UI、CSS、路由、导航、feature flag 或 app shell。
- 本 review 不安装本地 app，不部署 Cloudflare，不修改 Access policy。
- 本 review 不读取 raw/private/cookie/session/secret 数据。
- 本 review 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 review 不执行 GitHub main 上传。

## 63. v1.1.6 Stage 9 Phase 3 Data Map C3 隔离原型参数

状态：`phase_9_3_data_map_c3_spike_ready_pending_stage_review`。

模型假设：

- Stage 9 是 C3 isolated prototype pass，不等于 production integration。
- Phase 9.3 创建 `data-map-spike` 的独立原型证据、fixture 安全、production isolation 和治理记录。
- Data Map 2.0 必须解释 source -> topic -> asset -> action，不得退化为 static structure diagram、plain table 或不可解释 node-link graph。

输入：

- `apps/memory-atlas/src/experiments/data-map-spike/README.md`
- `apps/memory-atlas/src/experiments/data-map-spike/index.html`
- `apps/memory-atlas/src/experiments/data-map-spike/main.ts`
- `apps/memory-atlas/src/experiments/data-map-spike/fixture.ts`
- `docs/product/data_map_c3_spike_contract.md`
- `docs/acceptance/data_map_c3_spike_acceptance.md`

处理方法：

- 检查 spike 文件是否齐全。
- 检查 main source 是否保留 source/topic/asset/action 四层、三类 edge、data_to_action_flow、map_card 字段、Inspector/Search/Review handoff、proposal-only 状态、reduced motion 和 smoke hook。
- 检查 fixture 是否保持 raw/private、plaintext secrets、local absolute paths 和 writeback 标志为 false，`proposalOnly` 为 true。
- 检查 production `src` 是否没有引用 `data-map-spike`。
- 使用 `validate:v1.1.6-stage9-phase3` 固定合同、验收、记录和改动范围。

参数与门槛：

- `PARAM-MA-V116-S9P03-001 stage9_phase3_contract_id = data_map_c3_spike_contract`
- `PARAM-MA-V116-S9P03-002 stage9_phase3_spike_path = apps/memory-atlas/src/experiments/data-map-spike`
- `PARAM-MA-V116-S9P03-003 stage9_phase3_required_features = source_layer;topic_layer;asset_layer;action_layer;source_to_topic_edges;topic_to_asset_edges;asset_to_action_edges;data_to_action_flow;map_card;open_inspector;jump_to_search;jump_to_review;proposal_candidate;reduced_motion;smoke_status_hook`
- `PARAM-MA-V116-S9P03-004 stage9_phase3_fixture_safety = rawPrivateDataIncluded:false;plaintextSecretsIncluded:false;localAbsolutePathsIncluded:false;writebackAllowed:false;proposalOnly:true`
- `PARAM-MA-V116-S9P03-005 stage9_phase3_isolation_boundary = no_production_import;no_route;no_navigation;no_feature_flag_default;no_direct_writeback;no_proposal_write`
- `PARAM-MA-V116-S9P03-006 stage9_phase3_required_validator = validate:v1.1.6-stage9-phase3`

输出：

- Stage 9 Phase 3 Data Map spike 原型文件。
- Stage 9 Phase 3 产品合同。
- Stage 9 Phase 3 验收文件。
- Stage 9 Phase 3 validator。

边界：

- 本 phase 不修改 production Data Guide / Data Map、路由、导航、feature flag 或 app shell。
- 本 phase 不运行 production build、installer、本地 app install、browser screenshot 或 Cloudflare deploy。
- 本 phase 不读取 raw/private/cookie/session/secret 数据。
- 本 phase 不直接写长期记忆，不写 proposal，不执行 agent apply。
- 本 phase 不进入 Stage 9 整体复审，不进入 Stage 10，不执行 GitHub main 上传。
