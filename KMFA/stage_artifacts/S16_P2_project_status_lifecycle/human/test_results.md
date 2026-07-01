# S16-P2 Test Results

更新时间: 2026-07-01

## TDD Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_status_lifecycle -q` before implementation | FAIL: `ModuleNotFoundError: No module named 'KMFA.tools.project_status_lifecycle'` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_status_lifecycle -q` | PASS: 7 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_status_lifecycle.py --generated-at 2026-07-01T23:30:00+10:00` | PASS: generated S16-P2 public-safe artifacts |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s16_p2_project_status_lifecycle.py` | PASS: source_lanes=6, lifecycle_records=4, exception_items=3, handoff_guards=3, report_grade_visible=D, formal_report_allowed=false, site_construction=false, safety_signature=false, technical_signature=false, invoice_issuance=false, collection_action=false, s16_p3_scope=false, github_upload=false |

## Final Verification

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_status_lifecycle -q` | PASS: 7 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s16_p2_project_status_lifecycle.py` | PASS: source_lanes=6, lifecycle_records=4, exception_items=3, handoff_guards=3, report_grade_visible=D, formal_report_allowed=false, site_construction=false, safety_signature=false, technical_signature=false, invoice_issuance=false, collection_action=false, s16_p3_scope=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 220 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=493, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0, warnings=0 |
| JSON/JSONL parse checks | PASS: S16-P2 JSON/JSONL and parameter CSV parse checks passed |
| `git diff --check -- KMFA` | PASS |
| raw/private file path scan over KMFA diff | PASS: no matches |
| S16-P2 machine artifact credential/raw/private leakage scan | PASS: no matches |
| KMFA secret pattern scan | PASS: no matches |

## Non-Blocking Validator Note

Semantic governance sync with `--semantic` may continue to expose pre-existing planned traceability/root manifest issues, as recorded in prior phase evidence. The binding gate for this phase is the non-semantic changed-only sync plus direct S16-P2 validator, raw/private scan, parse checks and full KMFA test suite.
