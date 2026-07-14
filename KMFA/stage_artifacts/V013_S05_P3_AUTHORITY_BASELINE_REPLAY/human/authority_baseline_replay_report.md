# KMFA v0.1.3 S05-P3 Authority Baseline Replay

- status: `completed_validated_local_only_no_go_upload_deferred_authority_baseline_replayed`
- phase_scope: `v013_s05_p3_authority_baseline_replay_only`
- baseline_version: `KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK`
- baseline_content_hash: `sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670`
- authority_records: `45`
- total_fixture_fields: `45`
- q5_locked_field_count: `40`
- excluded_field_count: `5`
- q4_human_confirmed_count: `40`
- q5_calculation_baseline_allowed_count: `40`
- formal_report_allowed: `false`
- stage5_review_completed: `false`
- github_upload_allowed: `false`
- s05_p2_dependency_validated: `true`
- legacy_s05_p3_dependency_validated: `true`
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
- s05_p3_performed: `true`
- stage5_review_performed: `false`
- github_upload_performed: `false`
- github_upload_deferred_until_stage10_batch: `true`
- current_data_quality_grade: `Q2`
- current_report_grade: `D`
- release_permission: `blocked`

## Boundary Note

This replay uses only existing public-safe S05-P3 aggregate authority baseline metadata and validator results. It does not read the local raw inbox and does not publish raw values, normalized values, source filenames, sheet names, ZIP member names, row values, business values, or field/header plaintext.

`/Users/linzezhang/Downloads/KMFA_MetaData` is the user finance raw business data inbox. Codex must not modify, delete, move, rename, overwrite, or write generated/extra files inside that directory. Private diagnostics or scratch outputs must use `KMFA/.codex_private_runtime/` or another project-controlled gitignored work directory.

## Next

Stage 5 whole review in a separate run. Do not perform GitHub upload in S05-P3; GitHub main upload remains deferred until Stage 1-10 are complete, whole review passes, and findings are fixed.
