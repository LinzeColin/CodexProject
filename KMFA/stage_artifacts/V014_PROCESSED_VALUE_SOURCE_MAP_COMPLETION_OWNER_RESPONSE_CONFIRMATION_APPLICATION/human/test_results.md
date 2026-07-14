# Test Results

Generated at: `2026-07-06T00:00:00+10:00`

## Commands

- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_confirmation_application.py --require-private-confirmation`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_response_confirmation_application -q`

## Result

- `decision=NO_GO`
- `primary_confirmation_code=KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL`
- `follow_up_confirmation_code=KMFA_ORR_OPTION_REVIEW_GROUPS`
- `supplemental_diagnostic_request_row_count=113`
- `review_group_follow_up_ready=true`
- `active_owner_authorized_fill_record_ready=false`
- `source_map_completion_reapplication_ready=false`
- `raw_to_processed_value_comparison_performed=false`
- `business_value_consistency_verified=false`
- `github_upload_performed=false`

## Boundary

This phase did not read, list, stat, fingerprint, modify, copy, normalize, move, rename, overwrite or delete the raw inbox. Private confirmation and diagnostic details remain under ignored runtime only.
