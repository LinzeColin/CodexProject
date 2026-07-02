# KMFA v0.1.3 S05-P2 Field Candidate Replay

- status: `completed_validated_local_only_no_go_upload_deferred_owner_downgrade_replayed`
- phase_scope: `v013_s05_p2_field_candidate_replay_only`
- a0_project_candidates: `9`
- required_fields_per_candidate: `5`
- fixture_candidate_count: `45`
- private_value_hash_recorded_count: `40`
- private_value_pending_count: `5`
- source_anchor_recorded_count: `40`
- source_anchor_pending_count: `5`
- pending_source_candidate_count: `1`
- q3_field_candidate_count: `45`
- q4_human_confirmed_count: `0`
- q5_calculation_baseline_allowed_count: `0`
- owner_allowed_decision_count: `3`
- owner_template_count: `3`
- active_decision_code: `downgrade_to_cross_source_support`
- active_preview_status: `ready`
- completion_gate_ready: `true`
- completion_gate_mode: `owner_downgrade_to_cross_source_support`
- raw_dir_read_required: `false`
- raw_dir_read_performed: `false`
- raw_dir_mutation_performed: `false`
- local_raw_data_dir: `/Users/linzezhang/Downloads/KMFA_MetaData`
- raw_filename_publication_allowed: `false`
- field_plaintext_publication_allowed: `false`
- sheet_name_publication_allowed: `false`
- zip_member_name_publication_allowed: `false`
- row_value_publication_allowed: `false`
- business_value_publication_allowed: `false`
- s05_p3_performed: `false`
- stage5_review_performed: `false`
- github_upload_performed: `false`
- github_upload_deferred_until_stage10_batch: `true`
- current_data_quality_grade: `Q2`
- current_report_grade: `D`
- release_permission: `blocked`

## Boundary Note

This replay uses only existing public-safe S05-P2 metadata and owner/authorized decision records. It does not read the local raw inbox, does not publish raw or normalized business values, and does not promote Q4/Q5 authority baseline status.

`/Users/linzezhang/Downloads/KMFA_MetaData` is the user finance raw business data inbox. Codex must not modify, delete, move, rename, overwrite, or write generated/extra files inside that directory. Private diagnostics or scratch outputs must use `KMFA/.codex_private_runtime/` or another project-controlled gitignored work directory.

## Next

S05-P3 authority baseline lock in a separate run. Do not perform Stage 5 review or GitHub upload in S05-P2; GitHub main upload remains deferred until Stage 1-10 are complete, whole review passes, and findings are fixed.
