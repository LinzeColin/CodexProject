# KMFA v0.1.3 S04-P3 Test Results

- status: `passed_local_only_no_go_upload_deferred`
- phase: `S04-P3`
- task_id: `KMFA-V013-S04-P3-BASIC-TOOL-REPORT-20260702`
- raw_data_inbox: `/Users/linzezhang/Downloads/KMFA_MetaData`
- raw_data_inbox_read_or_listed: `false`
- raw_data_inbox_modified_deleted_moved_renamed_overwritten_or_written: `false`
- github_upload_performed: `false`
- stage4_review_performed: `false`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s04_p3_basic_tool_report.py` | PASS: generated evidence with cases=22/22, raw_read=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p3_basic_tool_report.py` | PASS: S04-P3 validator passed with cases=22/22 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s04_p3_basic_tool_report -q` | PASS: 1 test |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q` | PASS: 4 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format json` | PASS: JSON report emitted, raw_business_data_used=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format markdown` | PASS: Markdown report emitted, 22 total / 22 passed / 0 failed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p1_amount_precision.py` | PASS: S04-P1 dependency passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p2_field_standardization.py` | PASS: S04-P2 dependency passed |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q` | PASS: 295 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=549, tasks=162, v1.2_html=45+ |
| `structured changed-file parse check` | PASS: files=4 |
| `changed/untracked public-safe path scan` | PASS: no forbidden raw/private path candidates |
| `high-signal secret scan` | PASS: no key-shaped secrets |
| `git diff --check -- KMFA scripts` | PASS |

## Boundary Result

S04-P3 only replays synthetic public-safe boundary cases and generates public-safe JSON/Markdown tool test reports. It does not perform Stage 4 review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, OpMe deep coupling, or business execution.
