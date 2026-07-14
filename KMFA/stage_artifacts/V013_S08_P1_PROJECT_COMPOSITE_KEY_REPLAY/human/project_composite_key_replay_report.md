# KMFA v0.1.3 S08-P1 Project Composite Key Replay

- task_id: `KMFA-V013-S08-P1-PROJECT-COMPOSITE-KEY-REPLAY-20260703`
- status: `completed_validated_local_only_no_go_upload_deferred_project_composite_key_replayed`
- phase_scope: `v013_s08_p1_project_composite_key_replay_only`
- dependency: `v0.1.3 Stage 7 review PASS`
- legacy_s08_p1_dependency_validated: `true`
- required_component_count: `8`
- profile_count: `4`
- match_result_count: `3`
- manual_review_queue_count: `2`
- strong_auto_match_count: `1`
- human_review_required_count: `2`
- hash_only_profile_count: `4`
- matching_weights_sum_bps: `10000`
- strong_threshold_bps: `8500`
- human_review_threshold_bps: `7000`
- weak_candidate_threshold_bps: `5000`
- missing_single_component_blocks_all_matching: `false`
- below_strong_threshold_enters_manual_review: `true`
- auto_merge_allowed_for_review_queue_count: `0`

## Boundary

- s08_p1_scope_included: `true`
- s08_p2_entity_model_scope_included: `false`
- s08_p3_matching_quality_scope_included: `false`
- stage8_review_scope_included: `false`
- github_upload_deferred_until_stage10_batch: `true`
- github_upload_performed: `false`
- formal_report_allowed: `false`
- business_decision_basis_allowed: `false`
- business_execution_allowed: `false`

## Raw Data Boundary

- local_raw_data_dir: `/Users/linzezhang/Downloads/KMFA_MetaData`
- local_raw_data_dir_role: `user_finance_raw_private_inbox`
- codex_read_required_by_this_phase: `false`
- codex_read_performed_by_this_phase: `false`
- codex_list_performed_by_this_phase: `false`
- codex_modify_allowed: `false`
- codex_delete_allowed: `false`
- codex_move_allowed: `false`
- codex_rename_allowed: `false`
- codex_generate_inside_allowed: `false`
- codex_create_extra_files_inside_allowed: `false`
- github_commit_allowed: `false`

This phase did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox. It only replayed public-safe aggregate and hash/ref evidence already present in the repository.

## Public Safety

Evidence contains only component names, counts, integer bps weights, thresholds, status gates, validator references, and governance paths.
It does not contain source filenames, source hashes from the private inbox, tab labels, ZIP member names, field/header plaintext, row values, business values, credentials, contracts, payroll, tax filings, or bank statements.

## Next Step

Proceed to v0.1.3 S08-P2 as a separate run. GitHub main upload remains deferred until v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; do not run S08-P3, Stage 8 review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, Redcircle automatic connector, or business execution in the S08-P1 run.
