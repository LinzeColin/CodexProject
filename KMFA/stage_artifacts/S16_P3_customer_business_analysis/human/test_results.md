# S16-P3 Test Results

更新时间: 2026-07-01

## TDD Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_customer_business_analysis -q` before implementation | FAIL: `ModuleNotFoundError: No module named 'KMFA.tools.customer_business_analysis'` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_customer_business_analysis -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/customer_business_analysis.py --generated-at 2026-07-01T23:40:00+10:00` | PASS: generated S16-P3 public-safe artifacts |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s16_p3_customer_business_analysis.py` | PASS: source_lanes=5, customer_summaries=4, exception_items=4, report_grade_visible=D, formal_report_allowed=false, business_decision_basis=false, collection_action=false, legal_collection_decision=false, stage16_review=false, github_upload=false |

## Final Verification

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_customer_business_analysis -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s16_p3_customer_business_analysis.py` | PASS: source_lanes=5, customer_summaries=4, exception_items=4, report_grade_visible=D, gates false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 226 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=498, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0, warnings=0 |
| JSON/JSONL/CSV parse checks | PASS: JSON=2, JSONL=6, parameter_csv_rows=220, csv_width=34 |
| `git diff --check -- KMFA` | PASS: no whitespace errors |
| raw/private file path scan over KMFA diff | PASS: no matches |
| S16-P3 machine artifact credential/raw/private leakage scan | PASS: no matches |
| KMFA high-signal secret pattern scan | PASS: no matches |

## Non-Blocking Validator Note

Semantic governance sync with `--semantic` may continue to expose pre-existing planned traceability/root manifest issues, as recorded in prior phase evidence. The binding gate for this phase is the non-semantic changed-only sync plus direct S16-P3 validator, raw/private scan, parse checks and full KMFA test suite.
