# Test Results

Generated at: `2026-07-06T00:00:00+10:00`

## Commands

- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_review_groups_path.py --require-private-groups`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_review_groups_path -q`

## Result

- `decision=NO_GO`
- `review_group_count=22`
- `review_group_response_row_count=113`
- `candidate_catalog_record_count=366`
- `ambiguous_review_group_count=19`
- `non_numeric_review_group_count=2`
- `unmatched_review_group_count=1`
- `review_groups_path_prepared=true`
- `owner_group_decision_applied=false`
- `active_owner_authorized_fill_record_ready=false`
- `source_map_completion_reapplication_ready=false`
- `raw_to_processed_value_comparison_performed=false`
- `business_value_consistency_verified=false`
- `github_upload_performed=false`

## Boundary

This phase did not read, list, stat, fingerprint, modify, copy, normalize, move, rename, overwrite or delete the raw inbox. Private group routing and row-level drafts remain under ignored runtime only.
