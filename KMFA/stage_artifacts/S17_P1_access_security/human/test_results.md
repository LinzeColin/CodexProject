# S17-P1 Test Results

更新时间: 2026-07-01

## TDD Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_access_security_policy.py` before implementation | FAIL: `ModuleNotFoundError: No module named 'KMFA.tools.access_security_policy'` |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_access_security_policy.py` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/access_security_policy.py --generated-at 2026-07-01T23:55:00+10:00` | PASS: generated S17-P1 public-safe access/security artifacts |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_p1_access_security.py` | PASS: roles=4, sensitive_categories=15, audit_actions=5, notification_delivery=false, github_upload=false |

## Final Verification

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_access_security_policy.py` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_p1_access_security.py` | PASS: roles=4, sensitive_categories=15, audit_actions=5, gates false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` | PASS: 233 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=507, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0, warnings=0 |
| Ruby JSON/JSONL/YAML/CSV parse checks | PASS: json=0, jsonl=3, yaml=9, csv=2 |
| `git diff --check -- KMFA scripts` | PASS |
| raw/private file path scan over changed paths | PASS: no forbidden raw/private files found |
| KMFA high-signal secret pattern scan | PASS: no matches |
| stale S17-P1 next-step scan | PASS: no stale S17-P1 next-step text found |

## Scope Boundaries

- Stage 17 review was not executed.
- GitHub upload was not executed.
- S17-P2 notification delivery was not implemented.
- S17-P3 SOP/backup/restore rehearsal was not implemented.
