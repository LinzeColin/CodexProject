# S16-P1 Test Results

更新时间: 2026-07-01

## TDD Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_subcontract_procurement_aggregation -q` before implementation | FAIL: `ModuleNotFoundError: No module named 'KMFA.tools.subcontract_procurement_aggregation'` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_subcontract_procurement_aggregation -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/subcontract_procurement_aggregation.py --generated-at 2026-07-01T23:00:00+10:00` | PASS: generated S16-P1 public-safe artifacts |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s16_p1_subcontract_procurement.py` | PASS: source_lanes=4, project_matches=5, unallocated_pool=2, duplicate_payment_candidates=2, cross_project_candidates=2, report_grade_visible=D, formal_report_allowed=false, payment_execution=false, bank_operation=false, s16_p2_scope=false, s16_p3_scope=false, github_upload=false |

## Final Verification

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_subcontract_procurement_aggregation -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s16_p1_subcontract_procurement.py` | PASS: source_lanes=4, project_matches=5, unallocated_pool=2, duplicate_payment_candidates=2, cross_project_candidates=2, report_grade_visible=D |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 213 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=488, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m json.tool ...` and JSONL parser | PASS: S16-P1 JSON/JSONL plus governance event JSONL parsed |
| `git diff --check -- KMFA` | PASS |
| raw/private file path scan over KMFA diff | PASS: no raw business files, zips, Excel/PDF, db/sqlite or private/raw CSV paths |
| S16-P1 machine artifact credential/raw/private leakage scan | PASS: no credential/raw/private leakage markers |
| S16-P1 machine artifact sensitive filename/business marker scan | PASS: no sensitive source filename or business plaintext markers |

## Non-Blocking Validator Note

`PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync --semantic` exposed pre-existing semantic reference issues in old planned traceability rows and unrelated root run manifest bindings. The non-semantic changed-only sync gate for this S16-P1 diff passed with errors=0 and warnings=0.
