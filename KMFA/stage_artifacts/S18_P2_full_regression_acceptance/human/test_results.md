# KMFA S18-P2 Full Regression Acceptance Test Results

generated_at: 2026-07-01T23:59:59+10:00

## TDD Red Evidence

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_full_regression_acceptance.py
ModuleNotFoundError: No module named 'KMFA.tools.full_regression_acceptance'
```

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_full_regression_acceptance.py
FAIL: test_cli_validator_accepts_generated_public_safe_artifacts
can't open file '.../KMFA/tools/check_s18_p2_full_regression_acceptance.py': [Errno 2] No such file or directory
```

## Green Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_full_regression_acceptance.py` | PASS: 7 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/full_regression_acceptance.py --generated-at 2026-07-01T23:59:59+10:00` | PASS: checks=5, stages=18, decision=NO_GO, delivery_allowed=false, s18_p3=false, stage18_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p2_full_regression_acceptance.py` | PASS: checks=5, stages=18, decision=NO_GO, delivery_allowed=false, s18_p3=false, stage18_review=false, github_upload=false |

## Final Local Gate

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_full_regression_acceptance.py` | PASS: 7 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p2_full_regression_acceptance.py` | PASS: checks=5, stages=18, decision=NO_GO |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p1_precision_stress.py` | PASS: scenarios=5, runs=3, large_batch_files=1200 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=531, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` | PASS: Ran 260 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s06_p3_validation_evidence.py` | PASS: metadata_quality_records=3+ |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s12_p3_manual_rerun_mechanism.py` | PASS: eligible=2, blocked_previews=3, invalidations=2, rerun_steps=8 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0, warnings=0 |
| `git diff --check` | PASS: no whitespace errors |
| `raw/private path scan` | PASS: no forbidden raw/private file paths in current diff |
| `high-signal secret scan` | PASS: no high-signal credentials in KMFA |

## Boundary Result

- `decision=NO_GO`
- `delivery_allowed=false`
- `business_decision_basis_allowed=false`
- `official_report_release_allowed=false`
- `github_upload_allowed=false`
- `s18_p3=false`
- `stage18_review=false`
- `raw_business_data=false`
