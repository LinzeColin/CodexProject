# KMFA v0.1.4 S05-P1 Test Results

- status: `pass_final_validation_local_only`
- task_id: `KMFA-V014-S05-P1-A0-FILE-REGISTRATION-20260704`
- raw_inbox_read_by_this_phase: `true`
- raw_inbox_hashed_by_this_phase: `true`
- raw_inbox_mutated_by_this_phase: `false`
- github_upload_performed: `false`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s05_p1_a0_file_registration.py KMFA/tools/check_v014_s05_p1_a0_file_registration.py KMFA/tests/test_v014_s05_p1_a0_file_registration.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s05_p1_a0_file_registration.py` | PASS: generated public-safe evidence before governance sync |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_stage_review.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s05_p1_a0_file_registration.py --require-private-diagnostic` | PASS: files=9, pdf=8, excel=1, private_hashes=9, q3=9, q4=0, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s05_p1_a0_file_registration -q` | PASS: 1 test |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_a0_file_registration.py` | PASS: legacy A0 file registration check remains compatible |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS |
| structured JSON/JSONL/CSV parse and CSV width check | PASS |
| Ruby YAML parse check | PASS |
| changed/untracked raw-private path scan | PASS |
| changed/untracked high-signal secret scan | PASS |
| public S05-P1 evidence raw leak token scan | PASS |
| `git diff --check -- KMFA scripts` | PASS |

## Boundary Evidence

- public_raw_hash_committed_count: `0`
- public_raw_member_name_committed_count: `0`
- private_business_member_hash_record_count: `9`
- private_diagnostic_ignored_by_git: `true`
- s05_p2_performed: `false`
- s05_p3_performed: `false`
- stage5_review_performed: `false`
- raw_value_matching_performed: `false`
- formal_report_performed: `false`
