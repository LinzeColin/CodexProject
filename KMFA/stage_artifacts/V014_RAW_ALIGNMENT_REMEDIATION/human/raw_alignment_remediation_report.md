# KMFA v0.1.4 Raw Alignment Remediation

- status: `raw_alignment_remediation_reported_no_go_owner_source_identity_required`
- task_id: `KMFA-V014-RAW-ALIGNMENT-REMEDIATION-20260705`
- phase_id: `V014_RAW_ALIGNMENT_REMEDIATION`
- raw_root_file_count: `5`
- raw_root_archive_count: `3`
- raw_root_spreadsheet_count: `2`
- selected_candidate_count: `1`
- selected_archive_openable: `true`
- business_member_count: `9`
- business_document_member_count: `8`
- business_spreadsheet_member_count: `1`
- hidden_or_system_member_count: `13`
- business_shape_matches_expected_a0: `true`
- package_hash_matches_registered: `false`
- package_size_matches_registered: `false`
- private_member_hashes_recorded: `true`
- public_member_hash_backfill_allowed: `false`
- raw_alignment_complete: `false`
- decision: `NO_GO`

## Boundary

- This phase read, listed, stat-checked and hashed the configured raw inbox because the active goal explicitly requires raw evidence alignment diagnostics.
- No raw inbox mutation, deletion, move, rename, overwrite or generated file creation was performed.
- Public evidence is aggregate-only and does not include raw names, raw hashes, archive member names, sheet names, field/header text, row/cell values or business values.
- public_safe_aggregate_only: `true`

## Decision

- The local container does not match the registered source package by hash/size, even though the public-safe business shape matches the expected A0 package shape.
- The correct stop line is owner source identity confirmation before public hash backfill, lineage closure, report release, GitHub upload or app reinstall.
