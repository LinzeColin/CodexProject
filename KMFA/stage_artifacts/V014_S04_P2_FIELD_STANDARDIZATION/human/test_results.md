# KMFA v0.1.4 S04-P2 Test Results

- task_id: `KMFA-V014-S04-P2-FIELD-STANDARDIZATION-20260704`
- status: `passed_local_only_no_go_upload_deferred`
- validation_time: `2026-07-04T03:40:00+10:00`
- scope: `S04-P2 field standardization only`
- raw_boundary: `raw root not read/listed/hashed/mutated; raw value matching not performed`
- github_upload_performed: `false`
- next_required_step: `v0.1.4 S04-P3 basic tool report as a separate run`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s04_p2_field_standardization.py KMFA/tools/check_v014_s04_p2_field_standardization.py KMFA/tests/test_v014_s04_p2_field_standardization.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s04_p2_field_standardization.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p1_amount_precision.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p2_field_standardization.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p2_field_standardization -q` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_field_standardization -q` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS |
| `structured JSONL/CSV parse check` | PASS |
| `Ruby YAML parse check` | PASS |
| `changed/untracked raw-private artifact path scan` | PASS |
| `public raw leak scan` | PASS |
| `high-signal secret scan` | PASS |
| `git diff --check -- KMFA scripts` | PASS |

## Evidence Summary

- `canonical_field_count=6`
- `alias_dictionary_row_count=32`
- `mapping_record_count=6`
- `standardization_case_passed_count=6`
- `quality_status_count=5`
- `current_go_no_go=NO_GO`
- `delivery_allowed=false`
- `formal_report_allowed=false`
- `github_upload_performed=false`
- `s04_p3_started=false`
- `stage4_review_performed=false`
